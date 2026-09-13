# Deploy do Gateway no Railway

O pacote principal funciona com Docker Compose. Se preferir Railway, crie:

1. Um serviço PostgreSQL gerenciado.
2. Um serviço `fiap-ai-gateway` usando `railway/Dockerfile.gateway`.
3. Variáveis do gateway:
   - `OPENAI_API_KEY`
   - `LITELLM_MASTER_KEY`
   - `DATABASE_URL` (fornecida pelo PostgreSQL)
4. Porta do serviço: `4000`.
5. Gere um domínio HTTPS público para o serviço.
6. Atualize `GATEWAY_PUBLIC_URL` no seu arquivo `.env` local para esse domínio.
7. Execute `python scripts/provision_groups.py` para criar as chaves virtuais.

Observação: a chave OpenAI deve existir somente nas variáveis privadas do serviço, nunca no workflow dos alunos.
