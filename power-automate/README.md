# Power Automate - FIAP AI Gateway

O arquivo `fiap-ai-gateway.swagger.template.json` é uma definição OpenAPI 2.0 para criar um Custom Connector.

## Gerar o arquivo final

Com o gateway publicado em HTTPS:

```bash
python scripts/render_power_automate_swagger.py https://seu-gateway.exemplo.com
```

Isso gera `power-automate/fiap-ai-gateway.swagger.json` com o host correto.

## Importar no Power Automate

1. Acesse **Custom connectors**.
2. Escolha **New custom connector > Import an OpenAPI file**.
3. Importe `fiap-ai-gateway.swagger.json`.
4. Crie uma conexão.
5. Quando o campo da API key for solicitado, informe:

`Bearer SUA-CHAVE-VIRTUAL-DO-GRUPO`

6. Use a ação **Gerar resposta com IA** no fluxo.

> Importante: disponibilidade de Custom Connectors depende do licenciamento e das políticas do tenant Microsoft da instituição.
