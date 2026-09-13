# Configuração do Dify com o FIAP AI Gateway

A forma recomendada é usar o provider **OpenAI-API-compatible** do Dify.

Para cada grupo:

- Endpoint URL: `https://SEU-GATEWAY` (sem `/v1` no final)
- API Key: chave virtual do grupo
- Model name: `fiap-fast`
- Model type: LLM / Chat

Para RAG/Knowledge Base, adicione outro modelo:

- Model name: `fiap-embedding`
- Model type: Text Embedding
- Endpoint URL: o mesmo gateway
- API Key: a mesma chave virtual do grupo

O plugin OpenAI-compatible do Dify acrescenta `/v1` ao endpoint configurado, por isso o endereço informado deve ser a raiz do gateway.

## Teste rápido

Crie uma aplicação Workflow com:

`Start -> LLM -> End`

Prompt de teste:

`Explique em uma frase o que é um workflow automatizado.`

Se a execução retornar uma resposta, a integração está pronta.
