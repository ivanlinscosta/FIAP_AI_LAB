# FIAP AI Lab - Railway Deploy Guide

## Pré-requisitos

- Railway CLI instalado (`curl -fsSL https://railway.com/install.sh | sh`)
- Conta no Railway (https://railway.app)
- Chave de API OpenAI dedicada para o laboratório

## Passo 1: Login no Railway

```bash
railway login
```

## Passo 2: Criar Projeto

```bash
railway init FIAP-AI-Lab
```

## Passo 3: Criar Serviço PostgreSQL

```bash
railway add --database postgres
```

Anote a variável `DATABASE_URL` fornecida automaticamente.

## Passo 4: Criar Serviço Gateway (LiteLLM)

```bash
railway add --name fiap-ai-gateway
```

Configure o Dockerfile:
```bash
railway variables set RAILWAY_DOCKERFILE_PATH=railway/Dockerfile.gateway
```

Variáveis do gateway:
```bash
railway variables set OPENAI_API_KEY="sua-chave-openai-aqui"
railway variables set LITELLM_MASTER_KEY="sk-fiap-admin-$(openssl rand -base64 32)"
railway variables set DATABASE_URL="${DATABASE_URL}"
```

Gere o domínio público:
```bash
railway domain
```

Anote a URL (ex: `https://fiap-ai-gateway-production.up.railway.app`).

## Passo 5: Criar Serviço n8n

```bash
railway add --name fiap-n8n
```

Use a imagem oficial do n8n:
```bash
railway variables set RAILWAY_DOCKERFILE_PATH=""
railway variables set N8N_IMAGE=n8nio/n8n:latest
```

Variáveis do n8n:
```bash
railway variables set N8N_ENCRYPTION_KEY="$(openssl rand -base64 48)"
railway variables set GENERIC_TIMEZONE="America/Sao_Paulo"
railway variables set TZ="America/Sao_Paulo"
railway variables set N8N_PROTOCOL="https"
railway variables set WEBHOOK_URL="https://fiap-n8n-production.up.railway.app/"
railway variables set N8N_SECURE_COOKIE="true"
```

Gere o domínio público:
```bash
railway domain
```

## Passo 6: Criar Serviço Dashboard

```bash
railway add --name fiap-dashboard
```

Configure o Dockerfile:
```bash
railway variables set RAILWAY_DOCKERFILE_PATH=dashboard/Dockerfile
```

Variáveis do dashboard:
```bash
railway variables set LITELLM_BASE_URL="https://fiap-ai-gateway-production.up.railway.app"
railway variables set LITELLM_MASTER_KEY="sk-fiap-admin-..."
railway variables set ADMIN_USERNAME="professor"
railway variables set ADMIN_PASSWORD="$(openssl rand -base64 16)"
railway variables set DASHBOARD_REFRESH_SECONDS="30"
```

Gere o domínio público:
```bash
railway domain
```

## Passo 7: Provisionar Grupos

Localmente, com as variáveis configuradas no `.env`:

```bash
python scripts/provision_groups.py
```

Ou diretamente com variáveis de ambiente:

```bash
export GATEWAY_PUBLIC_URL="https://fiap-ai-gateway-production.up.railway.app"
export LITELLM_MASTER_KEY="sk-fiap-admin-..."
python scripts/provision_groups.py --count 10
```

## Passo 8: Testar

```bash
# Listar chaves criadas
python scripts/provision_groups.py --list

# Testar smoke test
export FIAP_GROUP_KEY="sk-fiap-grupo-01-..."
export GATEWAY_PUBLIC_URL="https://fiap-ai-gateway-production.up.railway.app"
python scripts/smoke_test.py
```

## Variáveis de Ambiente

### Gateway (fiap-ai-gateway)

| Variável | Obrigatória | Descrição |
|----------|-------------|-----------|
| `OPENAI_API_KEY` | Sim | Chave da API OpenAI |
| `LITELLM_MASTER_KEY` | Sim | Chave mestra do LiteLLM |
| `DATABASE_URL` | Sim | URL do PostgreSQL |

### Dashboard (fiap-dashboard)

| Variável | Obrigatória | Descrição |
|----------|-------------|-----------|
| `LITELLM_BASE_URL` | Sim | URL do gateway LiteLLM |
| `LITELLM_MASTER_KEY` | Sim | Chave mestra do LiteLLM |
| `ADMIN_USERNAME` | Sim | Usuário do dashboard |
| `ADMIN_PASSWORD` | Sim | Senha do dashboard |
| `DASHBOARD_REFRESH_SECONDS` | Não | Intervalo de refresh (default: 30) |

### n8n (fiap-n8n)

| Variável | Obrigatória | Descrição |
|----------|-------------|-----------|
| `N8N_ENCRYPTION_KEY` | Sim | Chave de criptografia do n8n |
| `GENERIC_TIMEZONE` | Sim | Fuso horário |
| `N8N_PROTOCOL` | Sim | Protocolo (https) |
| `WEBHOOK_URL` | Sim | URL pública do n8n |

### Provisionamento

| Variável | Default | Descrição |
|----------|---------|-----------|
| `GROUP_COUNT` | 10 | Número de grupos |
| `GROUP_BUDGET_USD` | 5 | Budget por grupo (US$) |
| `GROUP_BUDGET_DURATION` | 30d | Duração do budget |
| `GROUP_RPM_LIMIT` | 30 | Limite de requests/minuto |
| `GROUP_TPM_LIMIT` | 100000 | Limite de tokens/minuto |
| `GROUP_KEY_DURATION` | 45d | Duração da chave virtual |

## URLs Finais

Após o deploy, as URLs serão:

- **Gateway**: `https://fiap-ai-gateway-production.up.railway.app`
- **Dashboard**: `https://fiap-dashboard-production.up.railway.app`
- **n8n**: `https://fiap-n8n-production.up.railway.app`

## Comandos Úteis

```bash
# Ver logs de um serviço
railway logs --service fiap-ai-gateway

# Ver variáveis
railway variables --service fiap-dashboard

# Reiniciar um serviço
railway restart --service fiap-n8n

# Status do projeto
railway status
```

## Segurança

- Nunca commite `.env` ou chaves no Git
- Use variáveis de ambiente do Railway para todas as credenciais
- O dashboard deve ter senha forte
- Revogue chaves ao final de cada turma
- Não exponha o PostgreSQL publicamente
