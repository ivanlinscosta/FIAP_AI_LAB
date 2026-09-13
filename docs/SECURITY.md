# FIAP AI Lab - Security Guide

## Princípios de Segurança

1. **Chave OpenAI nunca exposta**: Apenas o gateway LiteLLM possui a chave real
2. **Virtual Keys por grupo**: Cada grupo recebe sua própria chave com limites
3. **Zero trust para alunos**: Nenhum aluno deve ter acesso a credenciais administrativas
4. **Defense in depth**: Múltiplas camadas de proteção

## Variáveis Sensíveis

### Nunca commit ou exponha:

| Variável | Risco | Onde deve estar |
|----------|-------|-----------------|
| `OPENAI_API_KEY` | Alto | Apenas no gateway (Railway) |
| `LITELLM_MASTER_KEY` | Alto | Gateway + Dashboard + Provisionamento |
| `DATABASE_URL` | Alto | Apenas no gateway (Railway) |
| `ADMIN_PASSWORD` | Médio | Apenas no dashboard (Railway) |
| `N8N_ENCRYPTION_KEY` | Médio | Apenas no n8n (Railway) |
| `POSTGRES_PASSWORD` | Alto | Apenas no gateway (Railway) |

### O que os alunos recebem:

- **Virtual Key** do grupo (ex: `sk-fiap-grupo-01-...`)
- **URL do gateway** (ex: `https://fiap-ai-gateway-production.up.railway.app`)
- **URL do n8n** (ex: `https://fiap-n8n-production.up.railway.app`)

### O que os alunos NÃO recebem:

- `OPENAI_API_KEY`
- `LITELLM_MASTER_KEY`
- `DATABASE_URL`
- Senhas de qualquer serviço
- Chaves de outros grupos
- Acesso ao Railway Dashboard

## Virtual Keys

Cada chave virtual possui:

| Parâmetro | Default | Descrição |
|-----------|---------|-----------|
| `max_budget` | US$ 5 | Limite de gasto |
| `budget_duration` | 30d | Duração do budget |
| `rpm_limit` | 30 | Requests por minuto |
| `tpm_limit` | 100000 | Tokens por minuto |
| `models` | fiap-fast, fiap-standard, fiap-embedding | Modelos permitidos |

## Dashboard

### Autenticação

- Credenciais via variáveis de ambiente
- Sessão server-side com cookie HttpOnly
- Cookie: `Secure=True`, `SameSite=strict`
- TTL: 12 horas (configurável)

### Controles Administrativos

Ações que exigem autenticação:

| Ação | Endpoint | Método |
|------|----------|--------|
| Bloquear grupo | `/api/groups/{group}/block` | POST |
| Desbloquear grupo | `/api/groups/{group}/unblock` | POST |
| Atualizar budget | `/api/groups/{group}/budget` | POST |
| Regenerar chave | `/api/groups/{group}/regenerate-key` | POST |

### Logs

- Chaves são mascaradas nos logs (ex: `sk-...3A92`)
- Prompts dos alunos NÃO são registrados
- Erros são logados sem expor dados sensíveis

## Railway

### Variáveis de Ambiente

- Use Railway Variables, nunca `.env` em produção
- Referências privadas entre serviços quando disponível
- Não exponha PostgreSQL publicamente

### Rede

- Comunicação interna via rede privada do Railway
- Apenas serviços públicos (gateway, dashboard, n8n) possuem domínio

## Checklist de Segurança

### Antes do Deploy

- [ ] `.env` está no `.gitignore`
- [ ] `secrets/` está no `.gitignore`
- [ ] Nenhuma chave está commitada no Git
- [ ] `OPENAI_API_KEY` está apenas nas variáveis do Railway
- [ ] `LITELLM_MASTER_KEY` está apenas nas variáveis do Railway
- [ ] Dashboard tem senha forte
- [ ] PostgreSQL não está público

### Durante o Uso

- [ ] Revogar chaves ao final de cada turma
- [ ] Monitorar uso anomálo no dashboard
- [ ] Verificar alertas de budget
- [ ] Manter chaves atualizadas

### Após o Uso

- [ ] Bloquear ou deletar todas as virtual keys
- [ ] Revogar `OPENAI_API_KEY` no OpenAI
- [ ] Remover variáveis do Railway (opcional)
- [ ] Arquivar dados de uso para referência

## Resposta a Incidentes

### Se uma virtual key vazar:

1. Bloqueie a chave imediatamente via dashboard
2. Registre uma nova chave para o grupo
3. Distribua a nova chave apenas para o grupo afetado
4. Verifique os logs de uso da chave comprometida

### Se a master key vazar:

1. Gere uma nova `LITELLM_MASTER_KEY`
2. Atualize todas as variáveis no Railway
3. Re-provisione todas as virtual keys
4. Revogue a chave antiga no OpenAI se necessário

### Se a `OPENAI_API_KEY` vazar:

1. Revogue a chave no OpenAI imediatamente
2. Gere uma nova chave
3. Atualize a variável no Railway
4. Verifique se houve uso não autorizado

## Contato

Para dúvidas sobre segurança, entre em contato com o professor responsável.
