# MCP Pipeline com Supabase e Google Gemini

Sistema completo de integração entre Google Gemini e Supabase através do Model Context Protocol (MCP), implementado com Google ADK.

## 🚀 Visão Geral

Este projeto implementa um pipeline avançado que permite interações naturais em português com bases de dados Supabase através do Google Gemini, utilizando o protocolo MCP para comunicação padronizada.

### ✨ Funcionalidades Principais

- 🧠 **Processamento de Linguagem Natural** - Consultas em português convertidas automaticamente para SQL
- 🔧 **Ferramentas MCP Avançadas** - Operações seguras e otimizadas na base de dados
- 🛡️ **Segurança Integrada** - Validação automática, prevenção de SQL injection e auditoria
- ⚡ **Cache Inteligente** - Sistema LRU com TTL adaptativo para otimização de performance
- 📊 **Monitorização em Tempo Real** - Métricas de performance e sugestões de otimização

## 🏗️ Arquitetura

```
Utilizador → Google Gemini → ADK Agent → MCP Client → MCP Server → Supabase → PostgreSQL
                ↑                          ↓
         Processamento NLP          Cache + Segurança + Monitorização
```

### Componentes Principais

1. **Agentes ADK** - Interfaces inteligentes com capacidades especializadas
2. **Servidor MCP Customizado** - Ferramentas específicas para Supabase
3. **Processador NLP** - Conversão de linguagem natural para operações SQL
4. **Sistema de Segurança** - Validação e auditoria completa
5. **Otimizador de Performance** - Cache e métricas em tempo real

## 🛠️ Instalação Rápida

### Pré-requisitos

- Python 3.9+
- Node.js 16+
- Google ADK
- Conta Supabase
- API Key do Google Gemini

### Setup Automático

```bash
# 1. Clone o repositório
git clone <repo-url>
cd mcp-supabase-gemini-pipeline

# 2. Execute o setup automático
python setup.py

# 3. Configure suas chaves de API no .env
cp .env.example .env
# Edite .env com suas chaves

# 4. Teste a instalação
python agent.py

# 5. Inicie a interface web
adk web
```

### Configuração Manual

```bash
# Instalar dependências Python
pip install google-adk python-dotenv supabase mcp pydantic

# Instalar dependências Node.js (para servidores MCP)
npm install -g @supabase/mcp-server-supabase
```

## ⚙️ Configuração

### Variáveis de Ambiente (.env)

```bash
# Google Gemini
GEMINI_API_KEY=your_gemini_api_key_here

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_service_role_key
SUPABASE_ACCESS_TOKEN=your_personal_access_token

# Otimização
CACHE_TTL=300
MAX_CACHE_SIZE=1000
RATE_LIMIT_REQUESTS=100
```

### Obter Chaves de API

1. **Google Gemini API Key**
   - Acesse [Google AI Studio](https://aistudio.google.com/)
   - Crie um novo projeto
   - Gere uma API key

2. **Supabase Configuração**
   - Acesse [Supabase Dashboard](https://supabase.com/dashboard)
   - Crie um projeto
   - Obtenha URL e Service Key em Settings → API
   - Gere Personal Access Token em Account → Access Tokens

## 🎯 Uso

### Interface Web (Recomendado)

```bash
# Iniciar interface web
adk web

# Acessar no navegador: http://localhost:8000
```

Selecione um dos agentes disponíveis:
- **mcp_supabase_pipeline** - Sistema completo
- **supabase_analytics_specialist** - Especialista em análises
- **database_explorer** - Exploração segura (somente leitura)

### Exemplos de Consultas

```python
# Exploração básica
"Que tabelas existem na base de dados?"
"Mostra-me a estrutura da tabela users"

# Consultas de dados
"Quantos utilizadores há ativos?"
"Lista os produtos mais vendidos"
"Mostra-me as vendas do último mês"

# Análises avançadas
"Analisa o crescimento de utilizadores por mês"
"Qual é a performance do sistema?"
"Tendências de vendas por categoria"

# Monitorização
"Status do cache e métricas de performance"
"Queries mais lentas do sistema"
```

### Uso Programático

```python
from adk_agent_samples.mcp_supabase_agent.intelligent_agent import IntelligentSupabaseAgent

# Criar agente
agent = IntelligentSupabaseAgent()

# Processar consulta
result = await agent.process_intelligent_query(
    "Quantos utilizadores há na base de dados?"
)

print(result["response"])
```

## 🔧 Ferramentas MCP Disponíveis

### Ferramentas de Base de Dados

| Ferramenta | Descrição | Uso |
|------------|-----------|-----|
| `execute_sql` | Executa queries SQL com validação | Análises complexas |
| `query_table` | Consulta tabelas com filtros | Consultas estruturadas |
| `list_tables` | Lista todas as tabelas | Exploração de esquemas |
| `describe_table` | Descreve estrutura de tabela | Análise de campos |

### Funcionalidades de Segurança

- ✅ Validação automática de queries
- ✅ Prevenção de SQL injection
- ✅ Rate limiting por utilizador
- ✅ Auditoria completa de operações
- ✅ Modo somente leitura disponível

### Otimizações de Performance

- ⚡ Cache LRU com TTL configurável
- ⚡ Connection pooling otimizado
- ⚡ Detecção de queries lentas
- ⚡ Métricas em tempo real
- ⚡ Sugestões automáticas de otimização

## 📊 Monitorização

### Métricas Disponíveis

```python
# Obter estatísticas de performance
from cache_optimizer import get_performance_stats

stats = get_performance_stats()
print(f"Cache hit ratio: {stats['cache_hit_ratio']:.2%}")
print(f"Tempo médio: {stats['avg_execution_time']:.2f}s")
```

### Dashboard de Saúde

- 📈 Tempo de resposta médio
- 📈 Taxa de cache hit/miss
- 📈 Queries por minuto
- 📈 Detecção de anomalias
- 📈 Score de saúde do sistema

## 🛡️ Segurança

### Validações Implementadas

```python
# Palavras-chave perigosas bloqueadas
DANGEROUS_KEYWORDS = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER']

# Padrões de SQL injection detectados
INJECTION_PATTERNS = ["'.*OR.*'", "UNION.*SELECT", "';.*--"]

# Limites de segurança
MAX_QUERY_LENGTH = 10000
MAX_RESULT_LIMIT = 10000
```

### Auditoria

Todos os eventos são registados em `security.log`:
- Tentativas de SQL injection
- Queries bloqueadas por segurança
- Rate limiting ativado
- Performance degradada

## 🔄 Fluxo de Trabalho

### 1. Análise NLP
```
Consulta → Classificação de intenção → Extração de entidades → Validação
```

### 2. Execução Segura
```
Validação de segurança → Cache check → Execução MCP → Armazenamento cache
```

### 3. Monitorização
```
Métricas de performance → Detecção de anomalias → Sugestões de otimização
```

## 📁 Estrutura do Projeto

```
mcp-supabase-gemini-pipeline/
├── agent.py                          # Agente principal para adk web
├── supabase_mcp_server.py            # Servidor MCP customizado
├── security_monitor.py               # Sistema de segurança
├── cache_optimizer.py                # Cache e otimização
├── setup.py                          # Script de instalação
├── requirements.txt                  # Dependências Python
├── .env.example                      # Configuração exemplo
├── adk_agent_samples/                # Agentes ADK
│   └── mcp_supabase_agent/
│       ├── agent.py                  # Agente básico
│       ├── custom_agent.py           # Agente customizado
│       ├── intelligent_agent.py      # Agente com NLP
│       └── nlp_processor.py          # Processador NLP
├── logs/                             # Logs do sistema
├── cache/                            # Cache local
└── reports/                          # Relatórios gerados
```

## 🔍 Resolução de Problemas

### Problemas Comuns

**1. Erro de configuração**
```bash
# Verificar variáveis de ambiente
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print('GEMINI_API_KEY:', bool(os.getenv('GEMINI_API_KEY')))"
```

**2. Erro de conexão Supabase**
```bash
# Testar conexão
python -c "from supabase import create_client; client = create_client('URL', 'KEY'); print('Conexão OK')"
```

**3. Servidor MCP não inicia**
```bash
# Testar servidor manualmente
python supabase_mcp_server.py
```

### Logs de Debug

```bash
# Ativar logs detalhados
export ADK_DEBUG=true
export LOG_LEVEL=DEBUG

# Visualizar logs
tail -f logs/security.log
tail -f logs/performance.log
```

## 🤝 Contribuição

### Como Contribuir

1. Fork o repositório
2. Crie uma branch para sua feature
3. Implemente testes
4. Faça commit das mudanças
5. Abra um Pull Request

### Áreas de Melhoria

- [ ] Suporte para mais tipos de base de dados
- [ ] Interface gráfica avançada
- [ ] Integração com ferramentas de BI
- [ ] Análises de machine learning
- [ ] Deployment em cloud

## 📜 Licença

Este projeto está licenciado sob a MIT License - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 📞 Suporte

- 📧 Email: [seu-email@exemplo.com]
- 💬 Issues: [GitHub Issues](link-para-issues)
- 📚 Documentação: [Wiki do Projeto](link-para-wiki)

## 🙏 Agradecimentos

- [Google ADK](https://github.com/google/adk) - Framework de desenvolvimento
- [Supabase](https://supabase.com/) - Plataforma de base de dados
- [Model Context Protocol](https://github.com/anthropics/mcp) - Protocolo de comunicação
- [Google Gemini](https://gemini.google.com/) - Modelo de linguagem

---

**🌟 Se este projeto foi útil, considere dar uma estrela no GitHub!**