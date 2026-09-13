# FIAP AI Lab

Ambiente de laboratório compartilhado para a disciplina **Tools, Automations and Workflows** da FIAP.

Permite que grupos de alunos utilizem n8n, Dify e Power Automate consumindo modelos OpenAI sem terem acesso à chave real do professor.

## Comece por aqui

> **Novo no laboratório?** Leia o **[Guia Completo](docs/GUIA_COMPLETO.md)** — documenta o funcionamento de todo o projeto, com passo a passo didático para alunos usando as ferramentas pela primeira vez e guia completo para o professor.

- **Aluno**: [docs/GUIA_COMPLETO.md](docs/GUIA_COMPLETO.md#parte-a--guia-do-aluno-primeira-vez) (ou [docs/STUDENT_GUIDE.md](docs/STUDENT_GUIDE.md))
- **Professor**: [docs/GUIA_COMPLETO.md](docs/GUIA_COMPLETO.md#parte-b--guia-do-professor) (ou [docs/PROFESSOR_GUIDE.md](docs/PROFESSOR_GUIDE.md))

## Arquitetura

```
OpenAI (chave real do professor)
        │
        ▼
LiteLLM Gateway (AI Gateway central)
        │
   Virtual Keys por grupo
        │
   ┌────┼────┐
   │    │    │
 n8n  Dashboard  Power Automate
```

## Componentes

| Serviço | Função | URL |
|---------|--------|-----|
| **fiap-ai-gateway** | LiteLLM Gateway | `https://fiap-ai-gateway-production.up.railway.app` |
| **fiap-dashboard** | Professor Console | `https://fiap-dashboard-production.up.railway.app` |
| **fiap-n8n** | Automações | `https://fiap-n8n-production.up.railway.app` |
| **fiap-postgres** | Banco de dados | (interno) |

## Modelos Disponíveis

| Alias | Modelo | Uso |
|-------|--------|-----|
| `fiap-fast` | `gpt-5-mini` | Econômico para laboratório |
| `fiap-standard` | `gpt-5.1` | Capacidade superior |
| `fiap-embedding` | `text-embedding-3-small` | Embeddings |

## Instalação Local

### Pré-requisitos

- Python 3.10+
- Docker e Docker Compose
- Chave de API OpenAI

### Passo 1: Configurar ambiente

```bash
cp .env.example .env
python3 scripts/generate_secrets.py
```

Edite `.env` e adicione sua `OPENAI_API_KEY`.

### Passo 2: Subir serviços

```bash
docker compose up -d
```

### Passo 3: Provisionar grupos

```bash
python3 scripts/provision_groups.py
```

### Passo 4: Testar

```bash
export FIAP_GROUP_KEY='sk-fiap-grupo-01-...'
python3 scripts/smoke_test.py
```

## Deploy no Railway

Veja o guia completo em [docs/RAILWAY_DEPLOY.md](docs/RAILWAY_DEPLOY.md).

### Resumo

```bash
# Instalar Railway CLI
curl -fsSL https://railway.com/install.sh | sh

# Login
railway login

# Criar projeto
railway init FIAP-AI-Lab

# Criar PostgreSQL
railway add --database postgres

# Criar Gateway
railway add --name fiap-ai-gateway
railway variables set RAILWAY_DOCKERFILE_PATH=railway/Dockerfile.gateway
railway variables set OPENAI_API_KEY="sua-chave"
railway variables set LITELLM_MASTER_KEY="sk-fiap-admin-..."
railway domain

# Criar Dashboard
railway add --name fiap-dashboard
railway variables set RAILWAY_DOCKERFILE_PATH=dashboard/Dockerfile
railway variables set LITELLM_BASE_URL="https://fiap-ai-gateway-production.up.railway.app"
railway variables set LITELLM_MASTER_KEY="sk-fiap-admin-..."
railway variables set ADMIN_USERNAME="professor"
railway variables set ADMIN_PASSWORD="senha-forte"
railway domain

# Criar n8n
railway add --name fiap-n8n
railway variables set N8N_IMAGE=n8nio/n8n:latest
railway variables set N8N_ENCRYPTION_KEY="..."
railway variables set GENERIC_TIMEZONE="America/Sao_Paulo"
railway domain

# Provisionar grupos
export GATEWAY_PUBLIC_URL="https://fiap-ai-gateway-production.up.railway.app"
export LITELLM_MASTER_KEY="sk-fiap-admin-..."
python3 scripts/provision_groups.py
```

## Dashboard

O Dashboard Professor Console permite:

- Monitorar uso da API por grupo
- Visualizar métricas de tokens e custo
- Gerenciar budgets e limites
- Bloquear/desbloquear grupos
- Regenerar virtual keys
- Exportar dados em CSV

Veja a documentação completa em [docs/DASHBOARD.md](docs/DASHBOARD.md).

## Scripts

| Script | Função |
|--------|--------|
| `generate_secrets.py` | Gera segredos locais |
| `provision_groups.py` | Cria virtual keys para grupos |
| `smoke_test.py` | Testa conexão com o gateway |
| `render_power_automate_swagger.py` | Gera OpenAPI para Power Automate |

### Uso do provision_groups.py

```bash
# Criar todos os grupos
python3 scripts/provision_groups.py

# Listar chaves existentes
python3 scripts/provision_groups.py --list

# Preview sem criar
python3 scripts/provision_groups.py --dry-run

# Override de parâmetros
python3 scripts/provision_groups.py --count 15 --budget 10
```

## Conectando Clientes

### n8n

1. Adicione um node OpenAI ou HTTP Request
2. Configure:
   - Base URL: `https://fiap-ai-gateway-production.up.railway.app/v1`
   - API Key: Virtual Key do grupo
   - Model: `fiap-fast`

### Dify

1. Crie um provider OpenAI-compatible
2. Configure:
   - Base URL: `https://fiap-ai-gateway-production.up.railway.app/v1`
   - API Key: Virtual Key do grupo
3. Use o modelo `fiap-fast`

### Power Automate

1. Importe o Custom Connector do arquivo `power-automate/fiap-ai-gateway.swagger.template.json`
2. Configure a URL do gateway
3. Use a Virtual Key do grupo como API Key

## Segurança

- `OPENAI_API_KEY` nunca é exposta aos alunos
- Cada grupo recebe apenas sua Virtual Key
- Budget e rate limits por grupo
- Dashboard protegido por senha
- Veja [docs/SECURITY.md](docs/SECURITY.md)

## Documentação

| Documento | Descrição |
|-----------|-----------|
| [GUIA_COMPLETO.md](docs/GUIA_COMPLETO.md) | **Guia completo do projeto** — alunos e professor, passo a passo didático |
| [RAILWAY_DEPLOY.md](docs/RAILWAY_DEPLOY.md) | Guia de deploy no Railway |
| [DASHBOARD.md](docs/DASHBOARD.md) | Documentação do Dashboard |
| [SECURITY.md](docs/SECURITY.md) | Guia de segurança |
| [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | Solução de problemas |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Arquitetura do sistema |
| [PROFESSOR_GUIDE.md](docs/PROFESSOR_GUIDE.md) | Guia do professor |
| [STUDENT_GUIDE.md](docs/STUDENT_GUIDE.md) | Guia do aluno |

## Variáveis de Ambiente

Veja a lista completa em [docs/RAILWAY_DEPLOY.md](docs/RAILWAY_DEPLOY.md#variáveis-de-ambiente).

## Licença

Uso educacional - FIAP
