# Checklist de instalação - FIAP AI Lab

- [ ] Criar um projeto OpenAI exclusivo para a disciplina.
- [ ] Criar uma chave API exclusiva para esse projeto.
- [ ] Copiar `.env.example` para `.env`.
- [ ] Rodar `python scripts/generate_secrets.py`.
- [ ] Colar a chave OpenAI em `.env`.
- [ ] Definir `GATEWAY_PUBLIC_URL` se o gateway for público.
- [ ] Rodar `docker compose up -d`.
- [ ] Verificar `http://localhost:4000/health` ou o domínio público.
- [ ] Rodar `python scripts/provision_groups.py`.
- [ ] Distribuir apenas `secrets/grupo-XX.txt` para cada grupo.
- [ ] Importar o workflow de teste no n8n.
- [ ] Configurar provider OpenAI-compatible no Dify.
- [ ] Se usar Power Automate, gerar Swagger com host HTTPS correto.
- [ ] Executar smoke test com uma chave virtual.
- [ ] Definir procedimento de revogação ao final da turma.
