# FIAP AI Lab - Architecture

## Visão Geral

O FIAP AI Lab é um ambiente de laboratório compartilhado para a disciplina Tools, Automations and Workflows da FIAP. A arquitetura permite que múltiplos grupos de alunos utilizem modelos de IA sem terem acesso à chave real da OpenAI.

## Diagrama de Arquitetura

```
                    ┌─────────────────────────────────────┐
                    │           OpenAI API                │
                    │      (Chave real do professor)      │
                    └──────────────┬──────────────────────┘
                                   │
                                   │ API Key
                                   │
                    ┌──────────────▼──────────────────────┐
                    │        LiteLLM Gateway              │
                    │    (AI Gateway central)             │
                    │                                      │
                    │  • OpenAI-compatible API             │
                    │  • Virtual Keys por grupo           │
                    │  • Rate limiting (RPM/TPM)          │
                    │  • Budget control                   │
                    │  • Usage tracking                   │
                    └──────────────┬──────────────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
              │                    │                    │
    ┌─────────▼─────────┐ ┌───────▼────────┐ ┌────────▼────────┐
    │       n8n         │ │    Dashboard   │ │   Power         │
    │  (Automações)     │ │  (Professor)   │ │   Automate      │
    │                   │ │                │ │  (Futuro)       │
    │  • Workflows      │ │  • Métricas    │ │  • Custom       │
    │  • HTTP Request   │ │  • Alertas     │ │    Connector    │
    │  • OpenAI Node    │ │  • Controles   │ │  • OpenAPI      │
    └───────────────────┘ └────────────────┘ └─────────────────┘
              │                    │                    │
              │                    │                    │
              └────────────────────┼────────────────────┘
                                   │
                          Virtual Keys
                    (sk-fiap-grupo-XX-...)
                                   │
                    ┌──────────────▼──────────────────────┐
                    │           PostgreSQL                │
                    │    (Dados de usage e keys)          │
                    └─────────────────────────────────────┘
```

## Serviços

### 1. LiteLLM Gateway (fiap-ai-gateway)

**Função**: AI Gateway central que roteia chamadas para a OpenAI

**Stack**:
- Imagem: `docker.litellm.ai/berriai/litellm:main-latest`
- Configuração: `litellm/config.yaml`
- Porta: 4000

**Endpoints**:
- `GET /v1/models` - Lista modelos disponíveis
- `POST /v1/chat/completions` - Chat completions (OpenAI-compatible)
- `GET /health` - Health check
- `POST /key/generate` - Criar virtual key (admin)
- `POST /key/list` - Listar virtual keys (admin)
- `GET /spend/logs` - Logs de uso (admin)

**Aliases de Modelo**:
| Alias | Modelo Real | Uso |
|-------|-------------|-----|
| `fiap-fast` | `gpt-5-mini` | Modelo econômico para laboratório |
| `fiap-standard` | `gpt-5.1` | Modelo de capacidade superior |
| `fiap-embedding` | `text-embedding-3-small` | Embeddings |

**Variáveis**:
- `OPENAI_API_KEY` - Chave da OpenAI
- `LITELLM_MASTER_KEY` - Chave mestra do LiteLLM
- `DATABASE_URL` - URL do PostgreSQL

---

### 2. PostgreSQL (fiap-postgres)

**Função**: Banco de dados para armazenar keys, usage e configurações

**Stack**:
- Imagem: `postgres:16-alpine`
- Database: `litellm`
- Usuário: `litellm`

**Variáveis**:
- `POSTGRES_USER` - Usuário do banco
- `POSTGRES_PASSWORD` - Senha do banco
- `POSTGRES_DB` - Nome do banco

**Acesso**: Apenas via rede interna do Railway

---

### 3. n8n (fiap-n8n)

**Função**: Plataforma de automação de workflows para os alunos

**Stack**:
- Imagem: `n8nio/n8n:latest`
- Porta: 5678

**Configuração**:
- Base URL do gateway: `https://fiap-ai-gateway-production.up.railway.app/v1`
- Virtual Key: Chave do grupo

**Variáveis**:
- `N8N_ENCRYPTION_KEY` - Chave de criptografia
- `GENERIC_TIMEZONE` - Fuso horário
- `N8N_PROTOCOL` - Protocolo (https)
- `WEBHOOK_URL` - URL pública

---

### 4. Dashboard (fiap-dashboard)

**Função**: Console do professor para monitorar e gerenciar o laboratório

**Stack**:
- Backend: FastAPI (Python)
- Frontend: HTML + CSS + JavaScript
- Gráficos: Chart.js
- Porta: 8080

**Funcionalidades**:
- Cards de resumo (requests, tokens, custo, grupos ativos)
- Gráficos de consumo por grupo e modelo
- Tabela de grupos com budget e status
- Alertas de budget e anomalias
- Controles administrativos (bloquear, desbloquear, budget, regenerar chave)
- Exportação CSV
- Auto-refresh configurável

**Variáveis**:
- `LITELLM_BASE_URL` - URL do gateway
- `LITELLM_MASTER_KEY` - Chave mestra do LiteLLM
- `ADMIN_USERNAME` - Usuário do dashboard
- `ADMIN_PASSWORD` - Senha do dashboard

---

## Fluxo de Dados

### 1. Chamada de Aluno

```
Aluno → n8n/Dify/Power Automate
  ↓
Virtual Key (sk-fiap-grupo-XX-...)
  ↓
LiteLLM Gateway
  ↓
Verifica:
  • Key válida?
  • Budget disponível?
  • RPM/TPM ok?
  • Modelo permitido?
  ↓
OpenAI API (com chave real)
  ↓
Resposta → Aluno
```

### 2. Registro de Uso

```
LiteLLM Gateway
  ↓
Registra em PostgreSQL:
  • Key usada
  • Modelo
  • Tokens
  • Custo
  • Timestamp
  ↓
Dashboard lê via API
  ↓
Professor vê métricas
```

## Segurança

### Camadas de Proteção

1. **Chave OpenAI**: Apenas no gateway (Railway)
2. **Virtual Keys**: Por grupo, com limites
3. **Rate Limiting**: RPM e TPM por grupo
4. **Budget Control**: Limite de gasto por grupo
5. **Dashboard Auth**: Credenciais via env vars
6. **Network**: Comunicação interna via rede privada

### O que cada ator acessa

| Ator | Acesso |
|------|--------|
| Professor | Dashboard, Railway CLI |
| Aluno | n8n, Virtual Key do grupo |
| Gateway | OpenAI API |
| Dashboard | LiteLLM Admin API |

## Deploy

### Railway

```
FIAP-AI-Lab (projeto)
├── fiap-postgres (PostgreSQL gerenciado)
├── fiap-ai-gateway (LiteLLM)
├── fiap-n8n (n8n)
└── fiap-dashboard (Dashboard)
```

### Variáveis Compartilhadas

- `LITELLM_MASTER_KEY`: Gateway + Dashboard + Provisionamento
- `DATABASE_URL`: Apenas Gateway
- `OPENAI_API_KEY`: Apenas Gateway

## Escalabilidade

### Limites Atuais

- 10 grupos (configurável)
- 5 US$ budget por grupo (configurável)
- 30 RPM por grupo (configurável)
- 100K TPM por grupo (configurável)

### Possíveis Melhorias

- Multi-tenant com organizações
- Dashboard para alunos (read-only)
- Integração com LMS da FIAP
- Alertas via email/Slack
- Métricas avançadas (latência, erros)
