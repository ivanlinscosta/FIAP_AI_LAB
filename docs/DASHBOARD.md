# FIAP AI Lab - Dashboard Documentation

## Visão Geral

O Dashboard FIAP AI Lab Professor Console é uma ferramenta de monitoramento e gerenciamento para acompanhar o uso da API de IA pelos grupos de alunos durante a disciplina.

## Acesso

1. Acesse a URL do dashboard (ex: `https://fiap-dashboard-production.up.railway.app`)
2. Faça login com as credenciais de administrador
3. O dashboard será exibido com os dados atualizados

## Layout

### Header

- **FIAP AI Lab** - Identificação do projeto
- **Professor Console** - Nome do dashboard
- **Tools, Automations and Workflows** - Disciplina
- **Exportar CSV** - Botão para exportar dados
- **Logout** - Botão para sair

### Cards de Resumo

No topo do dashboard, quatro cards mostram os totais:

| Card | Descrição |
|------|-----------|
| TOTAL DE REQUISIÇÕES | Número total de chamadas à API |
| TOTAL DE TOKENS | Total de tokens consumidos (formato compacto: 8.4M) |
| CUSTO TOTAL | Custo total em US$ |
| GRUPOS ATIVOS | Grupos ativos / Total de grupos |

### Filtros

O painel de filtros permite:

| Filtro | Opções |
|--------|--------|
| Período | Última hora, Hoje, Últimas 24h, 7 dias, 30 dias, Customizado |
| Grupo | Todos, ou grupo específico |
| Modelo | Todos, fiap-fast, fiap-standard, fiap-embedding |
| Auto-refresh | Toggle + intervalo (10s, 30s, 60s, Manual) |

### Gráficos

| Gráfico | Tipo | Descrição |
|---------|------|-----------|
| Cost per group | Barras | Custo por grupo |
| Tokens per group | Barras | Tokens por grupo |
| Consumption over time | Linha | Consumo ao longo do tempo |
| Model distribution | Donut | Distribuição por modelo |

### Tabela de Grupos

Colunas:

| Coluna | Descrição |
|--------|-----------|
| Grupo | Nome do grupo (ex: grupo-01) |
| Requests | Número de requisições |
| Input Tokens | Tokens de entrada |
| Output Tokens | Tokens de saída |
| Total Tokens | Total de tokens |
| Custo | Custo em US$ |
| Budget | Budget definido |
| Budget Restante | Budget disponível |
| % Utilizado | Percentual utilizado com barra de progresso |
| Última Chamada | Data/hora da última chamada |
| Status | Status atual (Ativo, Atenção, Crítico, Bloqueado) |

### Indicadores de Budget

Cores da barra de progresso:

| Faixa | Cor | Significado |
|-------|-----|-------------|
| 0-69% | Verde | Normal |
| 70-84% | Amarelo | Atenção |
| 85-99% | Laranja | Alerta |
| >=100% | Vermelho | Bloqueado/Esgotado |

### Alertas

O dashboard exige alertas para:

- **Budget**: Quando um grupo atinge 70%, 85% ou 100% do orçamento
- **Anomalia**: Quando um grupo realiza mais de 100 chamadas em 5 minutos (possível loop de automação)

## Detalhe do Grupo

Ao clicar em um grupo na tabela, um modal é aberto com:

### Informações Budget
- Budget definido
- Budget restante
- Percentual utilizado
- Status
- Limite RPM
- Limite TPM

### Uso de Tokens
- Requests
- Input tokens
- Output tokens
- Total tokens
- Custo atual
- Última chamada

### Controles Administrativos

| Ação | Descrição |
|------|-----------|
| Block | Bloqueia o acesso do grupo |
| Unblock | Desbloqueia o acesso do grupo |
| Atualizar budget | Altera o budget do grupo |
| Regenerate key | Gera uma nova chave virtual (com confirmação) |

### Distribuição de Modelos

Gráfico donut mostrando a distribuição de uso entre:
- fiap-fast
- fiap-standard
- fiap-embedding

### Chamadas Recentes

Tabela com as últimas chamadas do grupo:

| Coluna | Descrição |
|--------|-----------|
| Timestamp | Data/hora da chamada |
| Modelo | Modelo utilizado |
| Input Tokens | Tokens de entrada |
| Output Tokens | Tokens de saída |
| Total Tokens | Total de tokens |
| Cost | Custo da chamada |
| Latency | Latência em ms |
| HTTP Status | Código de resposta |

## Exportação CSV

O botão "Exportar CSV" gera um arquivo com os seguintes campos:

```
group,requests,input_tokens,output_tokens,total_tokens,cost_usd,budget_usd,budget_remaining,budget_usage_pct,last_request
```

## Auto-Refresh

O dashboard atualiza automaticamente a cada:
- 10 segundos
- 30 segundos (padrão)
- 60 segundos
- Manual (só ao clicar em atualizar)

## Autenticação

- Credenciais via variáveis de ambiente: `ADMIN_USERNAME` e `ADMIN_PASSWORD`
- Sessão segura com cookie HttpOnly, Secure, SameSite=strict
- TTL da sessão: 12 horas (configurável via `ADMIN_SESSION_TTL_SECONDS`)
- Logout limpa a sessão e redireciona para o login

## Segurança

- O dashboard NÃO expõe a `OPENAI_API_KEY`
- O dashboard NÃO expõe a `LITELLM_MASTER_KEY` completa
- Chaves virtuais são mascaradas (ex: `sk-...3A92`)
- Prompts dos alunos NÃO são exibidos
- Todas as ações administrativas passam pelo backend

## Arquitetura

```
Browser → Dashboard Backend → LiteLLM Admin API
                ↓
           PostgreSQL
```

- **Backend**: FastAPI (Python)
- **Frontend**: HTML + CSS + JavaScript vanilla
- **Gráficos**: Chart.js
- **Comunicação**: HTTP com LiteLLM API

## Variáveis de Ambiente

| Variável | Obrigatória | Default | Descrição |
|----------|-------------|---------|-----------|
| `LITELLM_BASE_URL` | Sim | - | URL do gateway LiteLLM |
| `LITELLM_MASTER_KEY` | Sim | - | Chave mestra do LiteLLM |
| `ADMIN_USERNAME` | Sim | - | Usuário do dashboard |
| `ADMIN_PASSWORD` | Sim | - | Senha do dashboard |
| `DASHBOARD_REFRESH_SECONDS` | Não | 30 | Intervalo de refresh |
| `ADMIN_SESSION_TTL_SECONDS` | Não | 43200 | TTL da sessão (12h) |
| `DASHBOARD_LOOKBACK_DAYS` | Não | 90 | Dias para buscar dados |
| `LITELLM_TIMEOUT_SECONDS` | Não | 30 | Timeout da API LiteLLM |
