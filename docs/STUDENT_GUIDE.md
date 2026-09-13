# FIAP AI Lab - Guia do Aluno

## Visão Geral

O FIAP AI Lab é um ambiente compartilado para a disciplina Tools, Automations and Workflows. Você terá acesso a uma chave Virtual Key que permite usar modelos de IA sem expor a chave real do professor.

## Suas Credenciais

O professor fornecerá um cartão com suas credenciais:

```
FIAP AI Lab - grupo-01
Gateway: https://fiap-ai-gateway-production.up.railway.app
OpenAI-compatible Base URL: https://fiap-ai-gateway-production.up.railway.app/v1
API Key: sk-fiap-grupo-01-...
Modelo padrão: fiap-fast
Modelo avançado: fiap-standard
Embedding: fiap-embedding
```

**Importante:** Suas credenciais são pessoais e intransferíveis. Não as compartilhe com outros grupos.

## Modelos Disponíveis

| Modelo | Uso | Quando usar |
|--------|-----|-------------|
| `fiap-fast` | GPT-5 Mini | Atividades do dia a dia, testes |
| `fiap-standard` | GPT-5.1 | Tarefas que precisam de mais qualidade |
| `fiap-embedding` | Text Embedding 3 Small | Análise de semelhança, busca semântica |

## Como Usar

### Opção 1: n8n

#### Configurar o Provider

1. Abra o n8n (URL fornecida pelo professor)
2. Vá em **Credentials** → **Add Credential**
3. Busque por **OpenAI**
4. Configure:
   - **API Key**: Sua Virtual Key
   - **Base URL**: `https://fiap-ai-gateway-production.up.railway.app/v1`
5. Salve

#### Criar um Workflow

1. Clique em **New Workflow**
2. Adicione um **Manual Trigger**
3. Adicione um **OpenAI Chat Model** ou **HTTP Request**
4. Configure o modelo (ex: `fiap-fast`)
5. Teste com uma mensagem simples

### Opção 2: Dify

#### Configurar o Provider

1. Acesse o Dify (URL fornecida pelo professor)
2. Vá em **Settings** → **Model Provider**
3. Adicione um provider **OpenAI-compatible**
4. Configure:
   - **Base URL**: `https://fiap-ai-gateway-production.up.railway.app/v1`
   - **API Key**: Sua Virtual Key
5. Salve

#### Criar uma Aplicação

1. Clique em **Create App**
2. Escolha o tipo (Chatbot, Agent, etc.)
3. Configure o LLM com o modelo `fiap-fast`
4. Teste com uma mensagem simples

### Opção 3: API Direta

Se preferir usar a API diretamente:

```bash
curl -X POST https://fiap-ai-gateway-production.up.railway.app/v1/chat/completions \
  -H "Authorization: Bearer sk-fiap-grupo-01-..." \
  -H "Content-Type: application/json" \
  -d '{
    "model": "fiap-fast",
    "messages": [
      {
        "role": "user",
        "content": "Olá, tudo bem?"
      }
    ]
  }'
```

### Opção 4: Python

```python
import openai

client = openai.OpenAI(
    api_key="sk-fiap-grupo-01-...",
    base_url="https://fiap-ai-gateway-production.up.railway.app/v1"
)

response = client.chat.completions.create(
    model="fiap-fast",
    messages=[
        {"role": "user", "content": "Explique automação em uma frase."}
    ]
)

print(response.choices[0].message.content)
```

### Opção 5: Power Automate

1. Importe o Custom Connector fornecido pelo professor
2. Configure a URL do gateway
3. Use sua Virtual Key como API Key
4. Crie fluxos usando o connector

## Limites

Cada grupo possui:

| Limite | Valor | O que significa |
|--------|-------|-----------------|
| Budget | US$ 5 | Limite de gasto total |
| RPM | 30 | Máximo de requisições por minuto |
| TPM | 100.000 | Máximo de tokens por minuto |
| Duração | 45 dias | Tempo de validade da chave |

**O que acontece ao atingir o limite:**
- Budget: As chamadas são bloqueadas até o próximo período
- RPM/TPM: Chamadas extras são rejeitadas

## Perguntas Frequentes

### Posso usar qualquer modelo?

Não. Apenas os modelos `fiap-fast`, `fiap-standard` e `fiap-embedding` estão disponíveis.

### Posso compartilhar minha chave?

Não. Sua chave é pessoal. Compartilhar resultará em bloqueio.

### Como saber quanto usei?

O professor pode ver seu uso no Dashboard. Pergunte a ele.

### Minha chave parou de funcionar

Possíveis causas:
- Budget atingido
- Chave expirada
- Chave bloqueada pelo professor

Entre em contato com o professor.

### Posso criar minha própria conta na OpenAI?

Não use sua chave pessoal. Use apenas a chave fornecida pelo professor.

## Boas Práticas

1. **Use o modelo apropriado**: `fiap-fast` para testes, `fiap-standard` para produção
2. **Economize tokens**: Requests desnecessários consomem budget
3. **Teste antes de escalar**: Valide seu workflow com poucos dados
4. **Documente seu trabalho**: Anote as configurações que funcionaram

## Suporte

Em caso de problemas, entre em contato com o professor responsável.

**Não** abra tickets no suporte de TI da FIAP para problemas com o laboratório.
