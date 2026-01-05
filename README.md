# Banco Ágil - Sistema Multi-Agente Inteligente

Sistema de atendimento bancário automatizado utilizando arquitetura multi-agente baseada em LangGraph e LLMs, desenvolvido para gerenciar processos de autenticação, crédito, câmbio e entrevistas de forma conversacional e inteligente.

---

## Visão Geral do Projeto

O **Banco Ágil** é uma solução completa de atendimento bancário que utiliza múltiplos agentes especializados coordenados por um grafo de estados para fornecer uma experiência conversacional natural e eficiente. O sistema integra validação de dados, consultas de informações financeiras e processos de tomada de decisão automatizados.

### Principais Características

- **Arquitetura Multi-Agente**: 4 agentes especializados que trabalham de forma coordenada
- **Fluxo Conversacional Natural**: Interação em linguagem natural utilizando GPT-4
- **Gestão de Estado Persistente**: Mantém contexto completo da conversa através do LangGraph
- **Autenticação Segura**: Sistema de validação com controle de tentativas
- **Processamento Inteligente de Crédito**: Análise automatizada baseada em score
- **Interface Web Interativa**: Interface Streamlit moderna e responsiva
- **Cobertura de Testes**: 99 testes automatizados com pytest

---

## Arquitetura do Sistema

### Diagrama do Grafo de Fluxo

```mermaid
---
config:
  flowchart:
    curve: linear
---
graph TD;
        __start__([<p>__start__</p>]):::first
        router(router)
        triagem(triagem)
        credito(credito)
        entrevista(entrevista)
        cambio(cambio)
        __end__([<p>__end__</p>]):::last
        __start__ --> router;
        cambio -. &nbsp;end&nbsp; .-> __end__;
        credito -. &nbsp;end&nbsp; .-> __end__;
        credito -.-> entrevista;
        entrevista -. &nbsp;end&nbsp; .-> __end__;
        entrevista -.-> credito;
        router -.-> entrevista;
        router -.-> triagem;
        triagem -. &nbsp;end&nbsp; .-> __end__;
        triagem -.-> cambio;
        triagem -.-> credito;
        classDef default fill:#f2f0ff,line-height:1.2
        classDef first fill-opacity:0
        classDef last fill:#bfb6fc
```

### Componentes Principais

#### 1. **Router (Roteador)**
- **Função**: Ponto de entrada do sistema que direciona para o agente apropriado
- **Responsabilidades**:
  - Verifica se há processo de entrevista ativa
  - Direciona novos usuários para triagem
  - Mantém usuários em entrevista no fluxo correto

#### 2. **Agente de Triagem** ([src/agents/triagem.py](src/agents/triagem.py))
- **Função**: Autenticação e direcionamento de clientes
- **Responsabilidades**:
  - Coleta e valida CPF (11 dígitos)
  - Valida data de nascimento (formato AAAA-MM-DD)
  - Controla tentativas de autenticação (máximo 3)
  - Identifica intenção do cliente através de NLU
  - Redireciona para agente especializado (crédito ou câmbio)
- **Ferramentas**: `autenticar_cliente`, `encerrar_atendimento`
- **Fluxos de Saída**: `credito`, `cambio`, `end`

#### 3. **Agente de Crédito** ([src/agents/credito.py](src/agents/credito.py))
- **Função**: Gestão de limite de crédito
- **Responsabilidades**:
  - Consulta limite atual do cliente
  - Processa solicitações de aumento de limite
  - Avalia pedidos baseado em score e regras de negócio
  - Oferece entrevista em caso de rejeição
- **Regras de Negócio**:
  - Score 0-299: Limite máximo R$ 1.000
  - Score 300-599: Limite máximo R$ 5.000
  - Score 600-799: Limite máximo R$ 15.000
  - Score 800-1000: Limite máximo R$ 50.000
- **Ferramentas**: `consultar_limite_credito`, `solicitar_aumento_limite`, `encerrar_atendimento`
- **Fluxos de Saída**: `entrevista`, `end`

#### 4. **Agente de Entrevista** ([src/agents/entrevista.py](src/agents/entrevista.py))
- **Função**: Coleta de dados socioeconômicos para recálculo de score
- **Responsabilidades**:
  - Conduz entrevista conversacional natural
  - Coleta 5 informações essenciais:
    - Renda mensal (em reais)
    - Tipo de emprego (formal/autonomo/desempregado)
    - Despesas fixas mensais (em reais)
    - Número de dependentes (0-3+)
    - Existência de dívidas ativas (sim/não)
  - Processa linguagem natural (ex: "5 mil" = 5000)
  - Recalcula score baseado em algoritmo ponderado
- **Ferramentas**: `calcular_novo_score`, `encerrar_atendimento`
- **Fluxos de Saída**: `credito`, `end`

#### 5. **Agente de Câmbio** ([src/agents/cambio.py](src/agents/cambio.py))
- **Função**: Consulta de cotações de moedas
- **Responsabilidades**:
  - Identifica moeda solicitada (USD, EUR, GBP, etc.)
  - Consulta cotação em tempo real
  - Apresenta informações de compra e venda
  - Permite consultas múltiplas
- **Ferramentas**: `consultar_cotacao_moeda`, `encerrar_atendimento`
- **Fluxos de Saída**: `end`

### Manipulação de Dados

#### Estado Compartilhado (AgentState)
O sistema utiliza um estado centralizado definido em [src/core/state.py](src/core/state.py) que persiste através de todos os agentes:

```python
{
    "messages": List[BaseMessage],          # Histórico de mensagens
    "current_agent": str,                   # Agente ativo
    "authenticated": bool,                  # Status de autenticação
    "cpf": str,                            # CPF do cliente
    "nome_cliente": str,                    # Nome do cliente
    "limite_credito": float,                # Limite atual
    "score": int,                          # Score de crédito
    "authentication_attempts": int,         # Tentativas de login
    "pending_redirect": str,                # Redirecionamento pendente
    "should_end": bool,                     # Flag de encerramento
    "temp_cpf": str,                       # CPF temporário (pré-auth)
    "temp_data_nascimento": str            # Data temp (pré-auth)
}
```

#### Persistência de Dados
- **Formato**: CSV para simplicidade e portabilidade
- **Localização**: Diretório `data/`
- **Arquivos**:
  - `clientes.csv`: Dados cadastrais e score
  - `score_limite.csv`: Tabela de limites por faixa de score
  - `solicitacoes_aumento_limite.csv`: Histórico de solicitações
- **Gerenciamento**: Classe `Database` em [src/data_models/database.py](src/data_models/database.py)

#### Fluxo de Dados
1. **Entrada**: Mensagem do usuário (HumanMessage)
2. **Processamento**: Router → Agente Especializado → Atualização de Estado
3. **Ferramentas**: Executadas conforme necessidade (ex: autenticação, consultas)
4. **Saída**: Resposta do agente (AIMessage) + Estado atualizado
5. **Redirecionamento**: Conditional edges determinam próximo agente ou fim

---

## Funcionalidades Implementadas

### 1. Autenticação de Clientes
- Validação por CPF (11 dígitos) e data de nascimento (AAAA-MM-DD)
- Extração inteligente de dados da mensagem usando regex
- Sistema de controle de tentativas (máximo 3)
- Bloqueio automático após falhas sucessivas

### 2. Gestão de Crédito
- Consulta de limite atual
- Solicitação de aumento de limite
- Aprovação/rejeição automática baseada em score
- Sistema de escalonamento para entrevista em caso de rejeição

### 3. Entrevista de Crédito
- Coleta conversacional de 5 parâmetros socioeconômicos
- Processamento de linguagem natural para valores numéricos
- Algoritmo de recálculo de score:
  ```
  score = 300 (base) +
          min(renda_mensal / 100, 200) +
          (150 se emprego formal, 100 se autônomo, 0 se desempregado) +
          max(-despesas_fixas / 50, -150) +
          (-50 * num_dependentes) +
          (-100 se tem_dividas else 0)
  ```
- Atualização automática do score no banco de dados

### 4. Consulta de Câmbio
- Suporte a múltiplas moedas (USD, EUR, GBP, JPY, etc.)
- Integração com API de câmbio real
- Apresentação de cotações de compra e venda
- Permite consultas sequenciais

### 5. Interface Conversacional
- Chat em linguagem natural via Streamlit
- Barra lateral com informações do cliente
- Exibição dinâmica de limite e score
- Botão de "Nova Conversa" para reset de sessão

### 6. Controle de Fluxo
- Redirecionamento inteligente entre agentes
- Detecção de intenção do usuário (NLU)
- Sistema de flags para controle de estado
- Encerramento gracioso de atendimento

---

## Desafios Enfrentados e Soluções

### 1. Coordenação entre Agentes
**Desafio**: Garantir que múltiplos agentes compartilhem estado de forma consistente sem duplicação ou perda de dados.

**Solução**: Implementação de um estado centralizado (`AgentState`) usando TypedDict do LangGraph, com sistema de `pending_redirect` para controlar transições entre agentes. Cada nó atualiza apenas seus campos específicos e preserva os demais através de merge de dicionários.

### 2. Autenticação em Múltiplas Etapas
**Desafio**: Coletar CPF e data de nascimento de forma natural sem forçar formato rígido, enquanto mantém controle de tentativas.

**Solução**: Sistema de estado temporário (`temp_cpf`, `temp_data_nascimento`) que persiste dados parciais. Regex para extração automática de padrões (11 dígitos para CPF, AAAA-MM-DD para data). Contador de tentativas com reset após sucesso.

### 3. Processamento de Linguagem Natural em Entrevista
**Desafio**: Interpretar valores como "5 mil", "3.5k", "CLT", "autônomo" de forma robusta.

**Solução**: Prompts detalhados no System Message orientando o LLM a normalizar valores. Exemplos explícitos de conversões no prompt (ex: "5 mil = 5000"). Validação dos argumentos antes de invocar ferramentas.

### 4. Prevenção de Loops Infinitos
**Desafio**: Evitar ciclos entre agentes (ex: credito → entrevista → credito → entrevista...).

**Solução**: Regras claras de redirecionamento nos conditional edges. Flag `pending_redirect` que é consumida e limpa após cada transição. Condições de saída definidas em cada agente.

### 5. Sincronização de Estado com Interface
**Desafio**: Manter UI do Streamlit sincronizada com estado interno do grafo LangGraph.

**Solução**: Sistema de detecção de mudanças de estado (`state_changed`) que aciona `st.rerun()` automaticamente. Session state do Streamlit armazena cópia do `agent_state` que é atualizado após cada invoke do grafo.

### 6. Testes de Fluxo Completo
**Desafio**: Testar interações multi-agente end-to-end com mocks adequados.

**Solução**: Uso de `pytest-mock` e `responses` para mockar chamadas de LLM e APIs externas. Fixtures reutilizáveis em [tests/conftest.py](tests/conftest.py). Testes de integração que validam transições entre agentes em [tests/integration/test_graph.py](tests/integration/test_graph.py).

### 7. Gerenciamento de Dependências do LangGraph
**Desafio**: Integrar LangGraph CLI para desenvolvimento local sem conflitos de versão.

**Solução**: Uso de `langgraph-cli[inmem]` no requirements.txt para incluir servidor de desenvolvimento em memória. Configuração via `langgraph.json` apontando para o grafo principal. Variáveis de ambiente gerenciadas por `python-dotenv`.

---

## Escolhas Técnicas e Justificativas

### Stack Principal

#### **LangGraph** (Orquestração de Agentes)
**Por quê?**
- Suporta nativamente grafos de estado cíclicos (essencial para fluxos como credito ↔ entrevista)
- Conditional edges permitem lógica de roteamento complexa sem código imperativo
- Integração nativa com LangChain para gerenciamento de LLMs
- Permite debugging visual através do LangSmith
- StateGraph garante persistência automática de estado entre nós

**Como facilita?**
- Cada agente é um nó isolado, facilitando manutenção e testes
- Adição de novos agentes requer apenas criar nó e definir edges
- Estado compartilhado elimina necessidade de gerenciamento manual de contexto

#### **LangChain** (Interface com LLMs)
**Por quê?**
- Abstração de alto nível para diferentes providers de LLM
- Sistema de mensagens (HumanMessage, AIMessage, SystemMessage) padroniza comunicação
- Tool binding facilita integração de ferramentas customizadas
- Chain of thought e prompts estruturados melhoram qualidade das respostas

**Como se encaixa?**
- `llm_with_tools` permite que agentes chamem funções Python de forma declarativa
- System prompts definem personalidade e regras de cada agente
- Histórico de mensagens mantém contexto conversacional

#### **OpenAI GPT-4** (Modelo de Linguagem)
**Por quê?**
- Melhor desempenho em NLU para português brasileiro
- Capacidade de tool calling confiável e determinística
- Compreensão de contexto conversacional multi-turno
- Raciocínio complexo para decidir entre ferramentas

**Como se encaixa?**
- Cada agente usa instância separada com prompts especializados
- Tool definitions são automaticamente convertidas para schema OpenAI
- Responses incluem tanto texto quanto tool calls estruturados

#### **Streamlit** (Interface Web)
**Por quê?**
- Desenvolvimento rápido de interfaces sem frontend complexo
- Session state nativo para gerenciar estado da aplicação
- Componentes de chat prontos (`st.chat_message`, `st.chat_input`)
- Deploy simples (Streamlit Cloud, Docker)

**Como se encaixa?**
- Session state armazena grafo LangGraph e estado do agente
- Cada mensagem do usuário invoca o grafo e atualiza UI
- Sidebar exibe informações de autenticação em tempo real

#### **Pytest** (Framework de Testes)
**Por quê?**
- Fixtures permitem reutilização de mocks (database, LLM)
- Parametrize facilita testes de múltiplos cenários
- Plugins (pytest-cov, pytest-mock) estendem funcionalidades
- Sintaxe clara e mensagens de erro informativas

**Como se encaixa?**
- 99 testes cobrindo unidade, integração e E2E
- Mocks de LLM garantem testes determinísticos e rápidos
- Fixtures em `conftest.py` compartilhadas entre módulos

#### **CSV + Dataclasses** (Persistência)
**Por quê?**
- Simplicidade adequada ao escopo do projeto
- Facilita inspeção manual de dados
- Portabilidade sem dependências de banco de dados
- Performance suficiente para volume esperado

**Como se encaixa?**
- Classe `Database` abstrai leitura/escrita de CSVs
- Dataclasses (`Cliente`, `SolicitacaoAumento`, `ScoreLimite`) tipam dados
- Pandas facilita operações de busca e atualização

---

## Tutorial de Execução e Testes

### Pré-requisitos

- Python 3.11 ou superior
- pip (gerenciador de pacotes Python)
- Git (opcional, para clonar repositório)
- Chave de API da OpenAI
- Docker e Docker Compose (para execução em container)

### Instalação Local

#### 1. Clone o repositório
```bash
git clone <url-do-repositorio>
cd teste-banco-agil
```

#### 2. Crie um ambiente virtual
```bash
# Linux/Mac
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

#### 3. Instale as dependências
```bash
pip install -r requirements.txt
```

#### 4. Configure as variáveis de ambiente
Crie um arquivo `.env` na raiz do projeto:
```bash
OPENAI_API_KEY=sk-...sua-chave-aqui...
```

#### 5. Verifique a estrutura de dados
Os arquivos CSV devem estar em `data/`:
- `data/clientes.csv`
- `data/score_limite.csv`
- `data/solicitacoes_aumento_limite.csv`

### Executando a Aplicação

#### Interface Streamlit (Recomendado)
```bash
streamlit run app_streamlit.py
```
Acesse: http://localhost:8501

#### LangGraph Studio (Desenvolvimento)
```bash
langgraph dev
```
Acesse: http://localhost:8123

### Executando Testes

#### Todos os testes
```bash
pytest -v
```

#### Com cobertura de código
```bash
pytest --cov=src --cov-report=html -v
```
Relatório em: `htmlcov/index.html`

#### Apenas testes unitários
```bash
pytest tests/unit/ -v
```

#### Apenas testes de integração
```bash
pytest tests/integration/ -v
```

#### Teste específico
```bash
pytest tests/unit/test_tools_autenticacao.py::test_autenticar_cliente_sucesso -v
```

### Resultados Esperados

```
======================== test session starts =========================
collected 99 items

tests/unit/test_database.py::test_buscar_cliente_existente PASSED
tests/unit/test_database.py::test_buscar_cliente_inexistente PASSED
tests/unit/test_tools_autenticacao.py::test_autenticar_cliente_sucesso PASSED
tests/unit/test_tools_credito.py::test_consultar_limite_sucesso PASSED
tests/integration/test_agents.py::test_triagem_autenticacao_completa PASSED
tests/integration/test_graph.py::test_fluxo_completo_credito PASSED
[...]

====================== 99 passed, 1 skipped in 12.45s ===============
```

---

## Execução com Docker

### Por que Docker?

- **Consistência**: Ambiente idêntico em desenvolvimento e produção
- **Isolamento**: Não interfere com pacotes do sistema
- **Portabilidade**: Funciona em qualquer SO com Docker
- **Reprodutibilidade**: Garante mesmas versões de dependências

### Dockerfile

Crie um arquivo `Dockerfile` na raiz do projeto:

```dockerfile
# Imagem base Python
FROM python:3.11-slim

# Define diretório de trabalho
WORKDIR /app

# Instala dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copia arquivos de dependências
COPY requirements.txt .

# Instala dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia código da aplicação
COPY . .

# Expõe porta do Streamlit
EXPOSE 8501

# Comando padrão: inicia Streamlit
CMD ["streamlit", "run", "app_streamlit.py", "--server.address", "0.0.0.0"]
```

### Docker Compose

Crie um arquivo `docker-compose.yml`:

```yaml
version: '3.8'

services:
  banco-agil:
    build: .
    container_name: banco-agil-app
    ports:
      - "8501:8501"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./data:/app/data
      - ./src:/app/src
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### Construindo e Executando

#### 1. Crie o arquivo .env
```bash
echo "OPENAI_API_KEY=sk-sua-chave-aqui" > .env
```

#### 2. Construa a imagem
```bash
docker-compose build
```

#### 3. Inicie o container
```bash
docker-compose up -d
```

#### 4. Verifique os logs
```bash
docker-compose logs -f banco-agil
```

#### 5. Acesse a aplicação
```
http://localhost:8501
```

### Comandos Úteis

#### Parar o container
```bash
docker-compose down
```

#### Reiniciar
```bash
docker-compose restart
```

#### Ver status
```bash
docker-compose ps
```

#### Executar testes no container
```bash
docker-compose exec banco-agil pytest -v
```

#### Acessar shell do container
```bash
docker-compose exec banco-agil /bin/bash
```

#### Reconstruir após mudanças
```bash
docker-compose up -d --build
```

### Variações de Deploy

#### Apenas build da imagem
```bash
docker build -t banco-agil:latest .
docker run -p 8501:8501 --env-file .env banco-agil:latest
```

#### Com volume para desenvolvimento
```bash
docker run -p 8501:8501 \
  -v $(pwd)/src:/app/src \
  -v $(pwd)/data:/app/data \
  --env-file .env \
  banco-agil:latest
```

---

## Configuração e Uso do LangSmith

### O que é LangSmith?

LangSmith é uma plataforma de observabilidade e debugging para aplicações LangChain/LangGraph, permitindo:
- Rastreamento detalhado de execuções
- Visualização de fluxo entre agentes
- Análise de custos de API
- Debugging de prompts e respostas
- Monitoramento de performance

### Tutorial de Configuração

#### 1. Criar Conta no LangSmith

1. Acesse: https://smith.langchain.com/
2. Clique em "Sign Up"
3. Crie conta com email ou GitHub
4. Confirme email e faça login

#### 2. Obter API Key

1. No dashboard, clique no ícone de usuário (canto superior direito)
2. Selecione "Settings"
3. Navegue até "API Keys"
4. Clique em "Create API Key"
5. Dê um nome (ex: "Banco Ágil Dev")
6. Copie a chave gerada (ex: `ls__...`)

#### 3. Configurar Variáveis de Ambiente

Adicione ao seu arquivo `.env`:

```bash
# OpenAI
OPENAI_API_KEY=sk-...

# LangSmith
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=ls__...
LANGCHAIN_PROJECT=banco-agil
```

**Explicação das variáveis:**
- `LANGCHAIN_TRACING_V2=true`: Ativa rastreamento
- `LANGCHAIN_ENDPOINT`: URL da API do LangSmith
- `LANGCHAIN_API_KEY`: Sua chave de API
- `LANGCHAIN_PROJECT`: Nome do projeto (organiza traces)

#### 4. Atualizar Código (Opcional)

O LangGraph já envia traces automaticamente quando as variáveis estão configuradas. Mas você pode adicionar metadados customizados:

```python
# src/core/graph.py
import os
from langsmith import Client

# Inicializar cliente (opcional, para metadados)
ls_client = Client() if os.getenv("LANGCHAIN_TRACING_V2") == "true" else None

def create_graph(openai_api_key: str):
    # ... código existente ...

    workflow = StateGraph(AgentState)
    # ... adicionar nós e edges ...

    graph = workflow.compile()

    # Adicionar metadados ao grafo
    if ls_client:
        graph.metadata = {
            "project": "banco-agil",
            "version": "1.0.0",
            "description": "Sistema Multi-Agente Bancário"
        }

    return graph
```

#### 5. Executar Aplicação com Rastreamento

```bash
# Certifique-se de que o .env está configurado
streamlit run app_streamlit.py
```

Todas as execuções serão automaticamente enviadas ao LangSmith.

### Usando o LangSmith

#### Visualizar Traces

1. Acesse: https://smith.langchain.com/
2. No menu lateral, clique em "Projects"
3. Selecione "banco-agil"
4. Você verá lista de todas as execuções (runs)

#### Analisar uma Execução

Clique em qualquer run para ver:

**Timeline:**
- Sequência de chamadas aos agentes
- Tempo de cada etapa
- Transições entre nós do grafo

**Input/Output:**
- Mensagem do usuário (input)
- Resposta final (output)
- Estado intermediário

**LLM Calls:**
- Prompts enviados ao GPT-4
- Respostas geradas
- Tokens utilizados
- Custo estimado

**Tools:**
- Ferramentas invocadas
- Argumentos passados
- Resultados retornados

#### Debugging de Fluxo

**Cenário**: Usuário não foi redirecionado corretamente para agente de crédito.

1. Encontre o run problemático na lista
2. Abra a visualização em árvore
3. Localize o nó "triagem"
4. Verifique:
   - System prompt enviado
   - Resposta do LLM
   - Valor de `pending_redirect` no estado
5. Identifique se o problema é:
   - Prompt ambíguo
   - LLM não detectou intenção
   - Conditional edge não funcionou

#### Analisar Custos

1. Na página do projeto, veja gráfico de custos
2. Filtre por período (última hora, dia, semana)
3. Identifique agentes mais caros
4. Otimize prompts longos ou chamadas redundantes

#### Comparar Versões de Prompt

1. Crie dois runs com prompts diferentes
2. Selecione ambos (Ctrl+Click)
3. Clique em "Compare"
4. Analise diferenças em:
   - Taxa de sucesso
   - Tempo de resposta
   - Custo
   - Qualidade das respostas

### Filtros Úteis

#### Por Agente
```
metadata.agent_name = "triagem"
```

#### Por Status
```
status = "success"
status = "error"
```

#### Por Duração
```
latency > 5s
```

#### Por Usuário (se adicionar ao metadata)
```
metadata.user_id = "12345"
```

### Monitoramento em Produção

#### 1. Criar Projeto de Produção

No LangSmith, crie projeto separado "banco-agil-prod":

```bash
# .env.production
LANGCHAIN_PROJECT=banco-agil-prod
```

#### 2. Configurar Alertas

1. Vá em "Settings" do projeto
2. Ative "Alerts"
3. Configure notificações para:
   - Taxa de erro > 5%
   - Latência média > 10s
   - Custo diário > $X

#### 3. Dashboard Personalizado

1. Crie dataset de teste
2. Configure avaliações automáticas
3. Monitore métricas customizadas

### Integração com Docker

Adicione variáveis ao `docker-compose.yml`:

```yaml
services:
  banco-agil:
    # ... configurações existentes ...
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - LANGCHAIN_TRACING_V2=${LANGCHAIN_TRACING_V2}
      - LANGCHAIN_ENDPOINT=${LANGCHAIN_ENDPOINT}
      - LANGCHAIN_API_KEY=${LANGCHAIN_API_KEY}
      - LANGCHAIN_PROJECT=${LANGCHAIN_PROJECT}
```

E no `.env`:
```bash
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=ls__...
LANGCHAIN_PROJECT=banco-agil
```

### Troubleshooting

#### Traces não aparecem
```bash
# Verifique se variáveis estão carregadas
python -c "import os; print(os.getenv('LANGCHAIN_TRACING_V2'))"

# Deve retornar: true
```

#### Erro de autenticação
```bash
# Valide API key
curl -H "x-api-key: ls__..." https://api.smith.langchain.com/info

# Deve retornar JSON com informações da conta
```

#### Desativar temporariamente
```bash
# No .env, comente ou mude para false
LANGCHAIN_TRACING_V2=false
```

---

## Estrutura do Projeto

```
teste-banco-agil/
├── src/                           # Código fonte principal
│   ├── agents/                    # Agentes especializados
│   │   ├── base.py               # Classe base com configuração de LLM
│   │   ├── triagem.py            # Agente de autenticação e triagem
│   │   ├── credito.py            # Agente de gestão de crédito
│   │   ├── entrevista.py         # Agente de entrevista socioeconômica
│   │   └── cambio.py             # Agente de consulta de câmbio
│   ├── tools/                     # Ferramentas (functions) dos agentes
│   │   ├── autenticacao.py       # Ferramenta de autenticação
│   │   ├── credito.py            # Ferramentas de crédito
│   │   ├── cambio.py             # Ferramenta de cotação
│   │   ├── score.py              # Ferramenta de recálculo de score
│   │   └── atendimento.py        # Ferramenta de encerramento
│   ├── core/                      # Núcleo do sistema
│   │   ├── graph.py              # Definição do grafo LangGraph
│   │   └── state.py              # Definição do estado compartilhado
│   ├── data_models/               # Modelos de dados
│   │   ├── models.py             # Dataclasses (Cliente, Solicitacao, etc)
│   │   └── database.py           # Classe de acesso a dados CSV
│   └── config/                    # Configurações
│       └── settings.py           # Carregamento de variáveis de ambiente
├── tests/                         # Suíte de testes
│   ├── unit/                      # Testes unitários
│   │   ├── test_database.py
│   │   ├── test_models.py
│   │   ├── test_tools_autenticacao.py
│   │   ├── test_tools_credito.py
│   │   └── test_tools_cambio.py
│   ├── integration/               # Testes de integração
│   │   ├── test_agents.py        # Testa agentes isoladamente
│   │   └── test_graph.py         # Testa fluxos completos
│   ├── fixtures/                  # Dados de teste reutilizáveis
│   │   ├── clientes.py           # Fixtures de clientes
│   │   └── responses.py          # Fixtures de respostas de API
│   └── conftest.py               # Configuração global de testes
├── data/                          # Dados persistidos
│   ├── clientes.csv              # Base de clientes
│   ├── score_limite.csv          # Tabela score → limite
│   └── solicitacoes_aumento_limite.csv  # Histórico de solicitações
├── app_streamlit.py              # Interface web principal
├── langgraph.json                # Configuração LangGraph CLI
├── requirements.txt              # Dependências Python
├── pytest.ini                    # Configuração pytest
├── Dockerfile                    # Container Docker
├── docker-compose.yml            # Orquestração Docker
├── .env                          # Variáveis de ambiente (não versionado)
├── .gitignore
├── README.md                     # Esta documentação
└── MIGRATION_GUIDE.md            # Guia de migração de estrutura
```

---

## Dados de Teste

Para facilitar testes, o sistema inclui clientes pré-cadastrados em `data/clientes.csv`:

| CPF | Nome | Data Nascimento | Limite Inicial | Score |
|-----|------|----------------|---------------|-------|
| 12345678901 | João Silva | 1990-05-15 | 5000.00 | 650 |
| 98765432100 | Maria Santos | 1985-08-20 | 1000.00 | 250 |
| 11122233344 | Carlos Souza | 1992-03-10 | 15000.00 | 750 |

### Exemplos de Interação

#### Fluxo de Autenticação e Crédito
```
Usuário: Olá
Sistema: Bem-vindo ao Banco Ágil! Para continuar, informe seu CPF.

Usuário: 12345678901
Sistema: Obrigado! Agora, por favor, informe sua data de nascimento (AAAA-MM-DD).

Usuário: 1990-05-15
Sistema: Autenticação realizada com sucesso! Bem-vindo, João Silva. Como posso ajudá-lo?

Usuário: Qual meu limite?
Sistema: Seu limite atual é de R$ 5.000,00.

Usuário: Quero aumentar para 10000
Sistema: Sua solicitação de aumento para R$ 10.000,00 foi aprovada! Seu novo limite já está ativo.
```

#### Fluxo com Entrevista
```
Usuário: Quero aumentar meu limite para 20000
Sistema: Infelizmente não foi possível aprovar o limite de R$ 20.000,00 no momento (seu score é 650, máximo permitido: R$ 15.000,00). Posso encaminhá-lo para uma entrevista de crédito que pode melhorar seu score. Deseja fazer a entrevista?

Usuário: Sim
Sistema: Ótimo! Para recalcular seu score, preciso de algumas informações. Qual é sua renda mensal?

Usuário: 8000
Sistema: Entendi. Qual é seu tipo de emprego: formal, autônomo ou desempregado?

Usuário: CLT
Sistema: Certo. Quais são suas despesas fixas mensais?

Usuário: 3000
Sistema: Quantos dependentes você possui?

Usuário: 2
Sistema: Por fim, você possui alguma dívida ativa?

Usuário: Não
Sistema: Seu score foi recalculado! Novo score: 720. Vou redirecioná-lo de volta ao atendimento de crédito.

Sistema: Agora que seu score melhorou, posso reanalizar sua solicitação. O que gostaria de fazer?
```

---

## Contribuindo

1. Fork o repositório
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

### Padrões de Código
- Use type hints em todas as funções
- Docstrings no formato Google Style
- Testes para toda nova funcionalidade
- Coverage mínimo de 80%

---

## Licença

Este projeto foi desenvolvido como demonstração técnica para o desafio Banco Ágil.

---

## Contato e Suporte

Para dúvidas, sugestões ou problemas:
- Abra uma issue no repositório
- Entre em contato via email: [levifreire7@gmail.com]

---

**Desenvolvido com LangGraph, LangChain e OpenAI GPT-4**
