# FIAP AI Lab

Ambiente de laboratório compartilhado para a disciplina **Tools, Automations and Workflows** da FIAP. Permite que grupos de alunos utilizem n8n, Dify e Power Automate consumindo modelos OpenAI sem terem acesso à chave real do professor.

## Comece por aqui

> **Novo no laboratório?** Este guia documenta o funcionamento de todo o projeto, com passo a passo didático para alunos usando as ferramentas pela primeira vez e guia completo para o professor.

- **Aluno**: [Guia do Aluno (primeira vez)](#parte-a-guia-do-aluno-primeira-vez)
- **Professor**: [Guia do Professor](#parte-b-guia-do-professor)

## 1. O que é o FIAP AI Lab

O **FIAP AI Lab** é um ambiente compartilhado de laboratório para a disciplina *Tools, Automations and Workflows*. Ele permite que grupos de alunos usem modelos de IA (OpenAI) em ferramentas como **n8n**, **Dify**, **Power Automate** e **Python**, sem ter acesso à chave real da OpenAI.

Cada grupo recebe uma **chave virtual (Virtual Key)** com limite de gasto, de requisições e de tokens. Isso garante que:

- A chave real do professor nunca é exposta.
- O custo é controlado por grupo (budget em US$).
- O professor consegue monitorar e bloquear qualquer grupo a qualquer momento.
- Todos usam os mesmos modelos, com a mesma qualidade e padronização.

## 2. Por que um gateway de IA?

Para entender o laboratório, primeiro entenda o problema que ele resolve.

### O problema

Se o professor entregasse a chave da OpenAI para cada grupo:

- Um grupo poderia gastar o orçamento inteiro em minutos.
- Não haveria como saber qual grupo gastou quanto.
- Um grupo poderia compartilhar a chave com pessoas de fora.
- Se a chave vazasse, ela precisaria ser trocada para todos.

### A solução

O **LiteLLM Gateway** funciona como um porteiro entre os grupos e a OpenAI:

```
Aluno → Virtual Key do grupo → GATEWAY (valida chave, limite e modelo) → OpenAI
                                   ↑
                            Professor controla tudo aqui
```

- O aluno chama o gateway com a chave do grupo.
- O gateway verifica: a chave existe? O budget ainda tem saldo? O modelo é permitido?
- Só então ele repassa a chamada para a OpenAI.
- O gateway registra tudo: quantas requisições, quantos tokens, quanto custou, por grupo.

É por isso que o gateway é chamado de proxy ou intermediário.

## 3. Arquitetura do sistema

```
                        OpenAI (chave real do professor)
                                   │
                                   ▼
                        LiteLLM Gateway (porteiro)
                                   │
                    Virtual Keys de cada grupo
                                   │
              ┌──────────────┬─────┴──────┬──────────────┐
              │              │            │              │
              ▼              ▼            ▼              ▼
            Dashboard      n8n         Dify        Power Automate
         (professor)   (automações)  (apps de IA)     (Microsoft)
```

| Componente | O que é | Para quem |
|------------|---------|-----------|
| **LiteLLM Gateway** | Porteiro que valida chaves e encaminha para a OpenAI | Todos |
| **Dashboard** | Painel do professor: monitoramento e controle | Professor |
| **n8n** | Ferramenta visual de automações (workflows) | Professor e alunos |
| **Dify** | Plataforma para criar apps de IA (chatbots, agentes) | Professor e alunos |
| **Power Automate** | Automações dentro do ecossistema Microsoft | Professor e alunos |
| **PostgreSQL** | Banco de dados onde o gateway guarda chaves e consumo | Sistema |

## 4. URLs de acesso

Estes são os endereços públicos (produção, hospedados no Railway):

| Serviço | URL |
|---------|-----|
| **Gateway (LiteLLM)** | `https://fiap-ai-gateway-production.up.railway.app` |
| **API compatível com OpenAI** | `https://fiap-ai-gateway-production.up.railway.app/v1` |
| **Dashboard (Professor)** | `https://fiap-dashboard-production.up.railway.app` |
| **n8n** | `https://fiap-n8n-production.up.railway.app` |

> **Dica:** copie estas URLs, elas serão usadas em todos os exemplos deste guia.

## 5. Modelos de IA disponíveis

O laboratório expõe 3 modelos com nomes próprios. Sempre use estes nomes (aliases), nunca os nomes internos da OpenAI:

| Alias (use este) | Modelo real | Para que serve | Custo |
|------------------|-------------|----------------|-------|
| `fiap-fast` | GPT-5 mini | Testes, atividades do dia a dia, protótipos | Baixo |
| `fiap-standard` | GPT-5.1 | Tarefas que exigem mais qualidade de resposta | Médio |
| `fiap-embedding` | text-embedding-3-small | Transformar texto em vetores (busca semântica) | Baixo |

**Regras:**
- Para conversas e textos: `fiap-fast` (e `fiap-standard` quando precisar de mais qualidade).
- Para busca semântica / similaridade: `fiap-embedding`.
- Não existe outros modelos. Se você tentar usar outro nome, o gateway rejeita.

# PARTE A: Guia do Aluno (primeira vez)

Esta parte foi escrita para quem nunca usou uma API de IA. Se você já conhece, pode pular para a ferramenta que precisar.

## A.1 O que você recebeu do professor

No início da aula, o professor entrega para o seu grupo um cartão de credenciais. Ele se parece com isto:

```
FIAP AI Lab - grupo-01
Gateway: https://fiap-ai-gateway-production.up.railway.app
OpenAI-compatible Base URL: https://fiap-ai-gateway-production.up.railway.app/v1
API Key: sk-6G8r0B-_SGyVG6Uy90p8sQ
Modelo padrão: fiap-fast
Modelo avançado: fiap-standard
Embedding: fiap-embedding
```

Você precisa de quatro informações para começar:

| Informação | No cartão | Para que serve |
|------------|-----------|----------------|
| **Base URL** | `https://fiap-ai-gateway-production.up.railway.app/v1` | Diz onde a API mora |
| **API Key** | `sk-...` | Diz quem você é (identificação do grupo) |
| **Modelo** | `fiap-fast` | Diz qual IA você quer usar |
| **Endpoint** | `/v1/chat/completions` | Diz qual operação fazer (conversar) |

> **IMPORTANTE:** Sua API Key é pessoal do grupo. Não compartilhe. Se ela for usada por outro grupo, todos perdem o orçamento.

## A.2 Primeiro contato: teste no navegador

O jeito mais rápido de confirmar que tudo funciona é abrir este link no navegador:

```
https://fiap-ai-gateway-production.up.railway.app/health
```

Você deve ver uma mensagem parecida com:

```json
{"status": "ok"}
```

O gateway está no ar. Agora vamos falar com a IA de verdade.

## A.3 Teste rápido com o terminal (curl)

O `curl` é um comando que envia requisições HTTP pelo terminal. É a forma mais direta de testar uma API.

**Passo 1: Abra o terminal** (no macOS: aplicativo Terminal).

**Passo 2: Copie e cole este comando**, substituindo `SUA_API_KEY` pela chave do seu grupo:

```bash
curl -X POST https://fiap-ai-gateway-production.up.railway.app/v1/chat/completions \
  -H "Authorization: Bearer SUA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "fiap-fast",
    "messages": [
      {"role": "user", "content": "Diga apenas: FIAP LAB OK"}
    ],
    "max_tokens": 50
  }'
```

**Passo 3: Tecle ENTER.** Em poucos segundos você verá uma resposta em JSON parecida com:

```json
{
  "id": "chatcmpl-...",
  "choices": [
    {
      "message": {
        "content": "FIAP LAB OK",
        "role": "assistant"
      }
    }
  ],
  "usage": {
    "prompt_tokens": 15,
    "completion_tokens": 4,
    "total_tokens": 19
  }
}
```

Pronto! Você acabou de usar a IA. A resposta está em `choices[0].message.content`.

### Erro comum neste passo

| Erro | Causa | Solução |
|------|-------|---------|
| `401 Unauthorized` | A chave está errada ou incompleta | Copie a chave do cartão exatamente como está, incluindo o prefixo `sk-` |
| `403 key not allowed to access model` | Modelo não permitido | Use `fiap-fast`, `fiap-standard` ou `fiap-embedding` |
| `429` / budget esgotado | Limite do grupo atingido | Avise o professor |

## A.4 Usando com Python

Python é a linguagem mais usada para consumir essas APIs. Vamos do zero.

### Passo 1: Instale a biblioteca oficial da OpenAI

Abra o terminal e execute:

```bash
pip install openai
```

### Passo 2: Crie um arquivo `teste_lab.py`

Crie um arquivo com este conteúdo:

```python
import openai

# Configura o cliente apontando para o gateway do laboratório
client = openai.OpenAI(
    api_key="SUA_API_KEY",                                        # chave do seu grupo
    base_url="https://fiap-ai-gateway-production.up.railway.app/v1"
)

# Faz uma pergunta para a IA
resposta = client.chat.completions.create(
    model="fiap-fast",
    messages=[
        {"role": "user", "content": "Explique o que é automação em uma frase."}
    ]
)

# Mostra a resposta
print(resposta.choices[0].message.content)

# Mostra quantos tokens foram usados
print(f"\nTokens usados: {resposta.usage.total_tokens}")
```

### Passo 3: Execute

```bash
python3 teste_lab.py
```

Se tudo deu certo, você verá uma frase explicando automação.

> **Para embeddings** (busca semântica), use este exemplo:
>
> ```python
> import openai
>
> client = openai.OpenAI(
>     api_key="SUA_API_KEY",
>     base_url="https://fiap-ai-gateway-production.up.railway.app/v1"
> )
>
> resposta = client.embeddings.create(
>     model="fiap-embedding",
>     input=["FIAP é uma faculdade de tecnologia"]
> )
>
> vetor = resposta.data[0].embedding
> print(f"Vetor com {len(vetor)} dimensões gerado!")
> ```

## A.5 Usando com o n8n

O **n8n** é uma ferramenta visual de automação. Você monta fluxos arrastando blocos (chamados de nodes) e conectando-os, sem escrever código.

### Passo 1: Acesse o n8n

Abra no navegador: `https://fiap-n8n-production.up.railway.app`

Na primeira vez, crie sua conta ou entre com a conta que o professor indicar.

### Passo 2: Cadastre a credencial da OpenAI

1. No menu lateral esquerdo, clique em **Credentials**.
2. Clique em **Add Credential**.
3. Na busca, digite **OpenAI** e selecione o tipo **OpenAI API**.
4. Preencha:
   - **API Key**: a chave do seu grupo (a partir de `sk-`).
   - **Base URL**: `https://fiap-ai-gateway-production.up.railway.app/v1`.
5. Clique em **Save**.

### Passo 3: Crie seu primeiro workflow

1. Clique em **New Workflow** ou no ícone **+**.
2. Adicione um node de **Manual Trigger**. É o ponto de partida, o botão que você vai clicar para rodar.
3. Clique no **+** embaixo e adicione um node do tipo **OpenAI → Chat Model**:
   - **Credential**: selecione a que você criou no Passo 2.
   - **Model**: `fiap-fast`.
   - **Messages**: adicione uma mensagem com role `User` e content, por exemplo: `Me diga uma curiosidade sobre automação`.
4. Execute o workflow clicando no botão **Execute Workflow** ou **Test Workflow**.
5. Veja o resultado no painel do node.

Pronto, você automatizou uma chamada de IA. A partir daqui, você pode ligar esse node a triggers de e-mail, webhook, planilha, etc.

## A.6 Usando com o Dify

O **Dify** é uma plataforma para construir aplicações de IA (chatbots, agentes) com uma interface amigável.

### Passo 1: Acesse o Dify

Abra a URL do Dify que o professor indicar. Crie sua conta se necessário.

### Passo 2: Configure o provider

1. Vá em **Settings** (engrenagem) → **Model Provider**.
2. Adicione um provider do tipo **OpenAI-API-compatible**.
3. Preencha:
   - **Base URL**: `https://fiap-ai-gateway-production.up.railway.app/v1`.
   - **API Key**: a chave do seu grupo.
4. Salve. Na lista de modelos, selecione `fiap-fast` como modelo de conversa.

### Passo 3: Crie uma aplicação

1. Clique em **Create APP**.
2. Escolha, por exemplo, **Chatbot**.
3. Configure o LLM com o modelo `fiap-fast`.
4. Teste pelo chat embutido.

## A.7 Usando com o Power Automate

O **Power Automate** é a ferramenta de automação da Microsoft. Para usá-la com o laboratório:

1. O professor disponibiliza um **Custom Connector**. O arquivo de template fica em `power-automate/`.
2. Na plataforma, importe esse connector.
3. Configure a **Base URL** do gateway.
4. Use a **API Key** do seu grupo.
5. Monte fluxos usando as ações do connector (Chat Completion, etc.).

## A.8 Limites do seu grupo

Cada grupo possui os seguintes limites:

| Limite | Valor | O que acontece se estourar |
|--------|-------|----------------------------|
| **Budget** | US$ 5,00 por período | As chamadas são bloqueadas até o professor liberar mais |
| **RPM** | 30 requisições por minuto | Chamadas extras retornam erro `429` |
| **TPM** | 100.000 tokens por minuto | Chamadas que excedem retornam erro `429` |
| **Validade** | 45 dias | A chave expira e precisa ser regenerada |

### Como economizar seu budget

- Use `fiap-fast` para testes e `fiap-standard` apenas quando precisar.
- Use `max_tokens` pequenos quando a resposta não precisa ser longa.
- Evite loops que chamam a API repetidamente sem necessidade. Isso é muito comum no n8n.
- Teste com poucos dados antes de rodar em escala.

## A.9 Erros comuns e como resolver

| Mensagem de erro | Significado | O que fazer |
|------------------|-------------|-------------|
| `401 Unauthorized` | Chave inválida | Verifique se copiou a chave inteira (`sk-...`) |
| `403 key not allowed to access model` | Modelo não permitido | Use apenas `fiap-fast`, `fiap-standard`, `fiap-embedding` |
| `429` | Muitas requisições ou budget esgotado | Aguarde 1 minuto (RPM) ou fale com o professor (budget) |
| `400 Invalid model name` | Nome do modelo errado | Confira a grafia: `fiap-fast` (hífen, minúsculo) |
| Connection timeout | Rede ou gateway indisponível | Verifique sua internet. Teste `https://fiap-ai-gateway-production.up.railway.app/health` |
| `404` virou `401/403/429` inesperado | Chave bloqueada pelo professor | Pergunte ao professor |

## A.10 Perguntas frequentes (FAQ)

**Posso usar minha própria chave da OpenAI?**
Não. Use somente a chave do laboratório. Chaves pessoais quebram o controle de custo e a regra da disciplina.

**Posso compartilhar minha chave com outro grupo?**
Não. Chave por grupo. Compartilhar pode causar bloqueio do grupo.

**Como sei quanto já gastei?**
O professor vê o consumo de todos os grupos no Dashboard. Se quiser saber o seu, pergunte a ele.

**Minha chave parou de funcionar do nada.**
Causas possíveis: budget atingido, chave expirada, ou chave bloqueada pelo professor. Fale com ele.

**Posso usar `gpt-4` ou `gpt-4o`?**
Não. O laboratório expõe apenas `fiap-fast`, `fiap-standard` e `fiap-embedding`.

**Qual é a diferença entre "Gateway" e "Base URL"?**
- **Gateway** é o endereço raiz do serviço: `https://fiap-ai-gateway-production.up.railway.app`
- **Base URL** da API é o mesmo endereço + `/v1`: `https://fiap-ai-gateway-production.up.railway.app/v1`
- Nas ferramentas (n8n, Dify, Python), use sempre a **Base URL**.

# PARTE B: Guia do Professor

Esta parte explica como gerenciar o laboratório durante toda a disciplina.

## B.1 Acessar o Dashboard

1. Abra no navegador: `https://fiap-dashboard-production.up.railway.app`.
2. Faça login com as credenciais de administrador. O usuário é `professor` e a senha é definida no Railway.
3. Você verá o painel principal com o monitoramento em tempo real.

> Se você não lembra a senha, ela é a variável de ambiente `ADMIN_PASSWORD` do serviço `fiap-dashboard` no Railway.

## B.2 Entender o Dashboard

### Cards de resumo (topo)

- **Total de requisições**: todas as chamadas feitas pelos grupos.
- **Total de tokens**: soma de tokens de entrada e saída.
- **Custo total**: gasto acumulado em US$.
- **Grupos ativos**: quantos grupos estão destravados / total.

### Tabela de grupos

Cada linha representa um grupo e mostra:

- Nome do grupo (grupo-01, grupo-02, ...).
- Número de requisições.
- Tokens (entrada / saída / total).
- Custo.
- Budget definido e restante.
- **Barra de progresso** do uso do budget.
- Última chamada (timestamp).
- Status (bloqueado ou ativo).

### Semáforo da barra de progresso

| Cor | Faixa | Ação sugerida |
|-----|-------|---------------|
| Verde | 0% – 69% | Tudo normal |
| Amarelo | 70% – 84% | Observe. Avise o grupo se continuar subindo |
| Laranja | 85% – 99% | Considere aumentar o budget |
| Vermelho | 100%+ | Grupo bloqueado por orçamento. Aumente ou renove o período |

## B.3 Gerenciar um grupo

Clique no nome do grupo para abrir o modal de detalhes. Nele você pode:

### Bloquear / Desbloquear

- **Block**: interrompe imediatamente o acesso do grupo. Use ao final da atividade, em suspeita de uso anômalo, ou a pedido do grupo.
- **Unblock**: volta a liberar o acesso.

### Atualizar budget

1. No modal do grupo, digite o novo valor em US$.
2. Clique em **Atualizar budget**.

Exemplo: o grupo está realizando uma entrega final, aumente de US$ 5 para US$ 10.

### Regenerar chave

1. Clique em **Regenerate key**.
2. Confirme. A **nova chave aparece apenas uma vez**, salve-a e entregue ao grupo.

Use quando houver vazamento, suspeita de mau uso, ou solicitação do grupo.

## B.4 Distribuir chaves para os grupos

### O que ENVIAR para cada grupo

Somente o conteúdo do arquivo **`secrets/grupo-XX.txt`** do grupo correspondente:

```
FIAP AI Lab - grupo-XX
Gateway: https://fiap-ai-gateway-production.up.railway.app
OpenAI-compatible Base URL: https://fiap-ai-gateway-production.up.railway.app/v1
API Key: sk-...
Modelo padrão: fiap-fast
Modelo avançado: fiap-standard
Embedding: fiap-embedding
```

### O que NUNCA enviar

- O arquivo `.env`. Ele contém chaves sensíveis.
- `OPENAI_API_KEY`. É a chave real da OpenAI.
- `LITELLM_MASTER_KEY`. É a chave mestre do gateway.
- `secrets/group_keys.csv`. Contém as chaves de todos os grupos.
- Credenciais de acesso ao painel do Railway.

## B.5 Provisionar novos grupos (linha de comando)

Quando precisar criar novos grupos, reprovisionar ou listar chaves, use o script:

```bash
# Listar grupos existentes
python3 scripts/provision_groups.py --list

# Simular a criação (sem criar de verdade)
python3 scripts/provision_groups.py --dry-run

# Criar 5 grupos novos com budget de US$ 10
python3 scripts/provision_groups.py --count 5 --budget 10
```

Antes de executar, defina as variáveis apontando para o gateway de produção:

```bash
export GATEWAY_PUBLIC_URL="https://fiap-ai-gateway-production.up.railway.app"
export LITELLM_MASTER_KEY="sk-fiap-admin-..."
```

As chaves geradas são salvas em `secrets/grupo-XX.txt` e `secrets/group_keys.csv`.

## B.6 Monitorar o uso

### Alertas automáticos

O dashboard sinaliza automaticamente:

| Alerta | Significado |
|--------|-------------|
| Budget em 70% | Grupo usou 70% do orçamento. Acompanhe |
| Budget em 85% | Grupo usou 85%. Considere aumentar |
| Budget em 100% | Grupo esgotou. Bloqueado automaticamente |
| Anomalia | Mais de 100 chamadas em 5 minutos. Possível loop |

### Filtros

Use os filtros para analisar: **período** (última hora, hoje, 7 dias, 30 dias), **grupo** ou **modelo**.

### Exportar CSV

Clique em **Exportar CSV** para baixar um relatório completo para planilha ou relatório de aula.

### Testar o gateway manualmente

```bash
curl https://fiap-ai-gateway-production.up.railway.app/health
```

Deve retornar algo como `{"status": "ok"}` ou documento de health check válido.

## B.7 Preparar o ambiente para a turma

### Antes da aula

1. Confirme que os serviços estão no ar: gateway, dashboard e n8n.
2. Teste uma chamada com a chave de um grupo. Exemplo: `python3 scripts/smoke_test.py` com `FIAP_GROUP_KEY` definida.
3. Confira os budgets de cada grupo.
4. Garanta que `secrets/grupo-XX.txt` está separado por grupo para distribuir.

### Durante a aula

1. Monitore o dashboard periodicamente.
2. Fique atento a alertas de anomalia. Loops acidentais de alunos são comuns.
3. Tenha um grupo reserva para emergências.

### Depois da aula

1. Exporte o CSV com o consumo da aula.
2. Bloqueie os grupos que não usarão mais.
3. Anote o que precisará ser ajustado para a próxima aula.

## B.8 Comandos úteis (Railway CLI)

```bash
# Ver status dos serviços
railway status

# Ver logs do gateway
railway logs --service fiap-ai-gateway

# Ver logs do dashboard
railway logs --service fiap-dashboard

# Ver logs do n8n
railway logs --service fiap-n8n

# Listar chaves de grupos
python3 scripts/provision_groups.py --list

# Testar uma chave
export FIAP_GROUP_KEY="sk-do-grupo"
python3 scripts/smoke_test.py
```

## 8. Solução de problemas (Troubleshooting)

### 8.1 O gateway está fora do ar?

1. Teste o health check:
   ```bash
   curl https://fiap-ai-gateway-production.up.railway.app/health
   ```
2. Se não responder, verifique o status no Railway:
   ```bash
   railway status
   railway logs --service fiap-ai-gateway --tail 50
   ```
3. Confirme que as variáveis `OPENAI_API_KEY`, `LITELLM_MASTER_KEY` e `DATABASE_URL` estão configuradas no serviço.

### 8.2 O dashboard não carrega ou não mostra dados

1. Teste o health check do dashboard:
   ```bash
   curl https://fiap-dashboard-production.up.railway.app/api/health
   ```
2. Verifique se as variáveis `LITELLM_BASE_URL` e `LITELLM_MASTER_KEY` estão apontando para o gateway correto.
3. Verifique se o gateway está rodando. O dashboard busca os dados dele.

### 8.3 Aluno não consegue chamar a API

Siga a ordem de verificação:

1. **Chave correta?** Teste com `curl` usando exatamente a chave do cartão.
2. **Modelo correto?** Use `fiap-fast` / `fiap-standard` / `fiap-embedding`.
3. **Budget com saldo?** Veja no dashboard a barra de progresso do grupo.
4. **Grupo bloqueado?** Verifique o status na tabela do dashboard.
5. **Chave expirada?** A validade padrão é 45 dias. Regenere se necessário.

### 8.4 n8n não conecta ao gateway

1. No n8n, confira se a credencial OpenAI está com:
   - **Base URL**: `https://fiap-ai-gateway-production.up.railway.app/v1`.
   - **API Key**: chave do grupo.
2. Teste a mesma chave com `curl`. Se o curl funciona, o problema está na configuração do n8n.
3. Verifique se a regra de **RPM (30/min)** não está sendo estourada por workflows em loop.

### 8.5 Orçamento estourou no meio da aula

1. No dashboard, localize o grupo.
2. Aumente o budget. Exemplo: de US$ 5 para US$ 10.
3. Se o grupo está em entrega final, considere um valor maior.
4. Avise o grupo que o saldo foi renovado.

### 8.6 Suspeita de vazamento de chave

1. No dashboard, abra o grupo.
2. Clique em **Regenerate key**.
3. Salve a nova chave. Ela aparece uma única vez.
4. Entregue a nova chave apenas ao grupo correto.
5. Se necessário, bloqueie o grupo enquanto a troca acontece.

## 9. Segurança

Boas práticas obrigatórias:

1. **Nunca** exponha `OPENAI_API_KEY` ou `LITELLM_MASTER_KEY` em mensagens, commits, código do frontend ou arquivos públicos.
2. **Nunca** faça commit de `.env`, `secrets/`, chaves ou senhas. O `.gitignore` já protege por padrão.
3. Toda credencial deve ser **variável de ambiente** no Railway.
4. O `secrets/group_keys.csv` contém todas as chaves. Guarde em local seguro.
5. O dashboard deve ter **senha forte**. Use a variável `ADMIN_PASSWORD`.
6. Revogue qualquer chave que vaze.

## 10. Referência rápida

### URLs

| Serviço | URL |
|---------|-----|
| Gateway | `https://fiap-ai-gateway-production.up.railway.app` |
| Base URL da API | `https://fiap-ai-gateway-production.up.railway.app/v1` |
| Dashboard | `https://fiap-dashboard-production.up.railway.app` |
| n8n | `https://fiap-n8n-production.up.railway.app` |

### Modelos

| Alias | Uso |
|-------|-----|
| `fiap-fast` | Chat padrão |
| `fiap-standard` | Chat de alta qualidade |
| `fiap-embedding` | Vetores / busca semântica |

### Exemplo mínimo (Python)

```python
import openai

client = openai.OpenAI(
    api_key="SUA_API_KEY",
    base_url="https://fiap-ai-gateway-production.up.railway.app/v1"
)

resposta = client.chat.completions.create(
    model="fiap-fast",
    messages=[{"role": "user", "content": "Olá!"}]
)
print(resposta.choices[0].message.content)
```

### Exemplo mínimo (curl)

```bash
curl -X POST https://fiap-ai-gateway-production.up.railway.app/v1/chat/completions \
  -H "Authorization: Bearer SUA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "fiap-fast", "messages": [{"role": "user", "content": "Olá!"}]}'
```

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

1. Adicione um node OpenAI ou HTTP Request.
2. Configure:
   - Base URL: `https://fiap-ai-gateway-production.up.railway.app/v1`
   - API Key: Virtual Key do grupo.
   - Model: `fiap-fast`

### Dify

1. Crie um provider OpenAI-compatible.
2. Configure:
   - Base URL: `https://fiap-ai-gateway-production.up.railway.app/v1`
   - API Key: Virtual Key do grupo.
3. Use o modelo `fiap-fast`.

### Power Automate

1. Importe o Custom Connector do arquivo `power-automate/fiap-ai-gateway.swagger.template.json`.
2. Configure a URL do gateway.
3. Use a Virtual Key do grupo como API Key.

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
