# FIAP AI Lab - Troubleshooting

## Problemas Comuns

### 1. Gateway não responde

**Sintoma**: Erro de conexão ao acessar o gateway

**Verificações**:
```bash
# Verificar status do serviço
railway status --service fiap-ai-gateway

# Verificar logs
railway logs --service fiap-ai-gateway

# Testar health check
curl https://fiap-ai-gateway-production.up.railway.app/health
```

**Soluções**:
- Verificar se o serviço está rodando no Railway
- Verificar se as variáveis `OPENAI_API_KEY` e `LITELLM_MASTER_KEY` estão configuradas
- Verificar se o `DATABASE_URL` está correto
- Reiniciar o serviço: `railway restart --service fiap-ai-gateway`

---

### 2. Dashboard não carrega

**Sintoma**: Página em branco ou erro 502

**Verificações**:
```bash
# Verificar status
railway status --service fiap-dashboard

# Verificar logs
railway logs --service fiap-dashboard

# Testar health check
curl https://fiap-dashboard-production.up.railway.app/api/health
```

**Soluções**:
- Verificar se `LITELLM_BASE_URL` aponta para o gateway correto
- Verificar se `LITELLM_MASTER_KEY` está correta
- Verificar se `ADMIN_USERNAME` e `ADMIN_PASSWORD` estão configurados
- Reiniciar o serviço

---

### 3. Login do dashboard falha

**Sintoma**: Erro "Usuário ou senha inválidos"

**Verificações**:
- Verificar `ADMIN_USERNAME` e `ADMIN_PASSWORD` nas variáveis do Railway
- Verificar se não há espaços extras nas variáveis

**Soluções**:
- Redefinir as variáveis:
  ```bash
  railway variables set ADMIN_USERNAME="professor"
  railway variables set ADMIN_PASSWORD="nova-senha-forte"
  ```
- Reiniciar o dashboard

---

### 4. Virtual keys não funcionam

**Sintoma**: Erro 401 ao usar chave de grupo

**Verificações**:
```bash
# Listar chaves existentes
python scripts/provision_groups.py --list

# Verificar se a chave está no formato correto
```

**Soluções**:
- Verificar se a chave foi copiada corretamente (sem espaços)
- Verificar se o gateway está rodando
- Re-provisionar as chaves:
  ```bash
  python scripts/provision_groups.py
  ```

---

### 5. n8n não conecta ao gateway

**Sintoma**: Erro de conexão ao usar OpenAI no n8n

**Verificações**:
- Verificar se a URL do gateway está correta no n8n
- Verificar se a virtual key está correta

**Soluções**:
- No n8n, configure o OpenAI node com:
  - Base URL: `https://fiap-ai-gateway-production.up.railway.app/v1`
  - API Key: Virtual key do grupo
- Testar com curl:
  ```bash
  curl -X POST https://fiap-ai-gateway-production.up.railway.app/v1/chat/completions \
    -H "Authorization: Bearer sk-fiap-grupo-01-..." \
    -H "Content-Type: application/json" \
    -d '{"model": "fiap-fast", "messages": [{"role": "user", "content": "Teste"}]}'
  ```

---

### 6. Dashboard não atualiza dados

**Sintoma**: Dados desatualizados no dashboard

**Verificações**:
- Verificar se auto-refresh está ativado
- Verificar intervalo de refresh

**Soluções**:
- Ativar auto-refresh no painel de filtros
- Clicar em atualizar manualmente
- Verificar se `DASHBOARD_REFRESH_SECONDS` está configurado

---

### 7. Erro "LITELLM_MASTER_KEY is missing"

**Sintoma**: Erro ao executar `provision_groups.py`

**Soluções**:
- Verificar se a variável está definida:
  ```bash
  echo $LITELLM_MASTER_KEY
  ```
- Se estiver usando `.env`, verificar se o arquivo existe
- Se estiver usando Railway, copiar a chave das variáveis

---

### 8. Budget não é respeitado

**Sintoma**: Grupo continua funcionando após atingir budget

**Verificações**:
- Verificar se o budget está configurado corretamente
- Verificar se o `budget_duration` está correto

**Soluções**:
- Verificar no dashboard se o budget está correto
- Atualizar o budget via dashboard se necessário
- Verificar se o LiteLLM está processando budgets

---

### 9. Railway CLI não encontrado

**Sintoma**: `command not found: railway`

**Soluções**:
```bash
# Instalar Railway CLI
curl -fsSL https://railway.com/install.sh | sh

# Configurar PATH
source "$HOME/.railway/env"

# Verificar instalação
railway --version
```

---

### 10. Erro de permissão ao provisionar

**Sintoma**: Erro 403 ao criar chaves

**Soluções**:
- Verificar se `LITELLM_MASTER_KEY` está correta
- Verificar se a chave tem permissões de admin
- Gerar nova chave mestra se necessário

---

## Comandos de Diagnóstico

```bash
# Status geral
railway status

# Logs de um serviço
railway logs --service fiap-ai-gateway --tail 100

# Variáveis de um serviço
railway variables --service fiap-dashboard

# Testar gateway
curl https://fiap-ai-gateway-production.up.railway.app/health

# Testar dashboard
curl https://fiap-dashboard-production.up.railway.app/api/health

# Listar chaves
python scripts/provision_groups.py --list

# Provisionar chaves
python scripts/provision_groups.py

# Smoke test
export FIAP_GROUP_KEY="sk-fiap-grupo-01-..."
export GATEWAY_PUBLIC_URL="https://fiap-ai-gateway-production.up.railway.app"
python scripts/smoke_test.py
```

## Contato

Se o problema persistir, entre em contato com o professor responsável.
