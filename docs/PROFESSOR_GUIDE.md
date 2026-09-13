# FIAP AI Lab - Guia do Professor

## Visão Geral

Este guia explica como usar o FIAP AI Lab para gerenciar o laboratório de IA durante a disciplina Tools, Automations and Workflows.

## Primeiros Passos

### 1. Acessar o Dashboard

1. Acesse a URL do dashboard (ex: `https://fiap-dashboard-production.up.railway.app`)
2. Faça login com as credenciais de administrador
3. Você verá o painel de monitoramento

### 2. Entender o Dashboard

#### Cards de Resumo

- **TOTAL DE REQUISIÇÕES**: Número total de chamadas à API
- **TOTAL DE TOKENS**: Tokens consumidos (formato compacto: 8.4M)
- **CUSTO TOTAL**: Custo total em US$
- **GRUPOS ATIVOS**: Grupos ativos / Total

#### Tabela de Grupos

Cada linha mostra:
- Nome do grupo (ex: grupo-01)
- Número de requisições
- Tokens (input/output/total)
- Custo
- Budget definido e restante
- Percentual utilizado com barra de progresso
- Última chamada
- Status

#### Cores da Barra de Progresso

| Cor | Significado |
|-----|-------------|
| Verde (0-69%) | Normal |
| Amarelo (70-84%) | Atenção |
| Laranja (85-99%) | Alerta |
| Vermelho (≥100%) | Bloqueado |

## Gerenciando Grupos

### Ver Detalhes de um Grupo

1. Clique no nome do grupo na tabela
2. Um modal será aberto com:
   - Informações de budget
   - Uso de tokens
   - Controles administrativos
   - Distribuição de modelos
   - Chamadas recentes

### Bloquear um Grupo

1. Clique no grupo
2. Clique em "Block"
3. Confirme a ação

**Quando bloquear:**
- Grupo terminou a atividade
- Uso anômalo detectado
- Solicitação do aluno

### Desbloquear um Grupo

1. Clique no grupo
2. Clique em "Unblock"

### Atualizar Budget

1. Clique no grupo
2. Digite o novo valor em US$
3. Clique em "Atualizar budget"

**Exemplo:** Se o grupo está usando muito, aumente de US$ 5 para US$ 10.

### Regenerar Chave

1. Clique no grupo
2. Clique em "Regenerate key"
3. Confirme a ação
4. **Importante:** A nova chave só será exibida uma vez!

**Quando regenerar:**
- Chave pode ter vazado
- Grupo solicitou nova chave
- Suspeita de uso não autorizado

## Monitoramento

### Alertas

O dashboard exibe alertas automaticamente:

| Tipo | Significado |
|------|-------------|
| Budget 70% | Grupo atingiu 70% do orçamento |
| Budget 85% | Grupo atingiu 85% do orçamento |
| Budget 100% | Grupo esgotou o orçamento |
| Anomalia | Mais de 100 chamadas em 5 minutos |

### Filtros

Use os filtros para analisar dados:

- **Período**: Última hora, Hoje, Últimas 24h, 7 dias, 30 dias
- **Grupo**: Todos ou grupo específico
- **Modelo**: Todos, fiap-fast, fiap-standard, fiap-embedding

### Exportação CSV

Clique em "Exportar CSV" para baixar um relatório com todos os dados dos grupos.

## Distribuindo Chaves para Alunos

### O que enviar para cada grupo

Envie apenas o arquivo `secrets/grupo-XX.txt` que contém:

```
FIAP AI Lab - grupo-01
Gateway: https://fiap-ai-gateway-production.up.railway.app
OpenAI-compatible Base URL: https://fiap-ai-gateway-production.up.railway.app/v1
API Key: sk-fiap-grupo-01-...
Modelo padrão: fiap-fast
Modelo avançado: fiap-standard
Embedding: fiap-embedding
```

### O que NÃO enviar

- `.env` (contém chaves sensíveis)
- `LITELLM_MASTER_KEY`
- `OPENAI_API_KEY`
- `secrets/group_keys.csv` (contém todas as chaves)
- Acesso ao Railway Dashboard

## Configurando n8n

### Para o Professor

1. Acesse o n8n (ex: `https://fiap-n8n-production.up.railway.app`)
2. Crie um workflow de teste
3. Configure um node OpenAI com:
   - Base URL: `https://fiap-ai-gateway-production.up.railway.app/v1`
   - API Key: Chave de teste ou de um grupo
   - Model: `fiap-fast`

### Para os Alunos

Oriente os alunos a:

1. Criar uma conta no n8n (se necessário)
2. Configurar o provider OpenAI com a chave do grupo
3. Criar workflows usando os modelos disponíveis

## Configurando Dify

### Para o Professor

1. Acesse o Dify
2. Crie um provider OpenAI-compatible
3. Configure:
   - Base URL: `https://fiap-ai-gateway-production.up.railway.app/v1`
   - API Key: Chave de teste

### Para os Alunos

Oriente os alunos a:

1. Criar uma conta no Dify
2. Configurar o provider com a chave do grupo
3. Criar aplicações usando os modelos disponíveis

## Boas Práticas

### Antes da Aula

1. Verifique se todos os serviços estão rodando
2. Teste a conexão com uma Virtual Key
3. Verifique se os budgets estão adequados

### Durante a Aula

1. Monitore o dashboard periodicamente
2. Fique atento a alertas de anomalia
3. Tenha chaves reserva para emergências

### Após a Aula

1. Anote qual grupo usou quanto
2. Considere aumentar budgets se necessário
3. Bloqueie grupos que terminaram

## Solução de Problemas

### Grupo não consegue usar a API

1. Verifique se a chave está correta
2. Verifique se o gateway está rodando
3. Verifique se o budget não foi atingido
4. Verifique se a chave não foi bloqueada

### Dashboard não mostra dados

1. Verifique se o dashboard está rodando
2. Verifique as credenciais de login
3. Verifique se o gateway está enviando dados

### n8n não conecta

1. Verifique a URL do gateway
2. Verifique a Virtual Key
3. Teste com curl primeiro

## Comandos Úteis

```bash
# Ver status dos serviços
railway status

# Ver logs do gateway
railway logs --service fiap-ai-gateway

# Listar chaves
python3 scripts/provision_groups.py --list

# Re-provisionar grupos
python3 scripts/provision_groups.py

# Testar conexão
export FIAP_GROUP_KEY="sk-fiap-grupo-01-..."
python3 scripts/smoke_test.py
```

## Contato

Em caso de problemas, entre em contato com o suporte de TI da FIAP.
