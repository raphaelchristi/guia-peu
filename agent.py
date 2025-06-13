"""
Agente Principal do MCP Pipeline - Interface para adk web
Sistema completo com Google ADK, Supabase MCP, NLP e otimizações
"""
import os
import json
import asyncio
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters

# Carregar configuração
load_dotenv()

# Verificar configuração
def check_configuration() -> Dict[str, bool]:
    """Verifica se todas as variáveis necessárias estão configuradas"""
    required_vars = [
        "GEMINI_API_KEY",
        "SUPABASE_URL", 
        "SUPABASE_SERVICE_KEY",
        "SUPABASE_ACCESS_TOKEN"
    ]
    
    config_status = {}
    for var in required_vars:
        config_status[var] = bool(os.environ.get(var))
        
    return config_status

# Verificar configuração na inicialização
config_check = check_configuration()
missing_vars = [var for var, status in config_check.items() if not status]

if missing_vars:
    print("⚠️  CONFIGURAÇÃO INCOMPLETA!")
    print("As seguintes variáveis de ambiente não estão definidas:")
    for var in missing_vars:
        print(f"   - {var}")
    print("\nConfigure no arquivo .env antes de continuar.")
    print("Exemplo: cp .env.example .env")

# Agente Principal - Integração completa com todas as funcionalidades
root_agent = LlmAgent(
    model='gemini-2.0-flash-exp',
    name='mcp_supabase_pipeline',
    instruction="""
    🚀 PIPELINE MCP SUPABASE + GOOGLE GEMINI
    
    Sou um sistema avançado de integração entre Google Gemini e Supabase através do Model Context Protocol (MCP).
    
    🎯 FUNCIONALIDADES PRINCIPAIS:
    
    1. 🧠 PROCESSAMENTO DE LINGUAGEM NATURAL
       - Entendo consultas em português natural
       - Converto automaticamente para operações SQL
       - Analiso intenções e extraio entidades
       
    2. 🔧 FERRAMENTAS MCP AVANÇADAS
       - execute_sql: Execução segura de queries SQL
       - query_table: Consultas com filtros e paginação
       - list_tables: Exploração de esquemas
       - describe_table: Análise de estruturas
       
    3. 🛡️ SEGURANÇA INTEGRADA
       - Validação automática de queries
       - Prevenção de SQL injection
       - Rate limiting inteligente
       - Auditoria completa
       
    4. ⚡ OTIMIZAÇÃO DE PERFORMANCE
       - Cache LRU automático
       - Monitorização de performance
       - Sugestões de otimização
       - Análise de padrões
    
    🎨 FLUXO DE TRABALHO INTELIGENTE:
    
    FASE 1 - ANÁLISE:
    - Analiso sua pergunta em linguagem natural
    - Identifico tipo de operação (consulta, análise, exploração)
    - Extraio entidades relevantes (tabelas, filtros, agregações)
    
    FASE 2 - PLANEJAMENTO:
    - Escolho a estratégia mais eficiente
    - Para exploração: começo com list_tables
    - Para consultas simples: uso query_table
    - Para análises complexas: construo SQL otimizado
    
    FASE 3 - EXECUÇÃO SEGURA:
    - Valido segurança da operação
    - Verifico cache para resultados anteriores
    - Executo com monitorização de performance
    - Aplico rate limiting quando necessário
    
    FASE 4 - APRESENTAÇÃO:
    - Formato resultados de forma legível
    - Forneço insights e análises
    - Sugiro consultas relacionadas
    - Explico otimizações possíveis
    
    💡 EXEMPLOS DE INTERAÇÃO:
    
    "Que tabelas existem na base de dados?"
    → Vou listar todas as tabelas e explicar sua estrutura
    
    "Quantos utilizadores há ativos?"
    → Vou consultar a tabela users com filtro de status ativo
    
    "Analisa as vendas do último mês por categoria"
    → Vou executar análise temporal com agregação por categoria
    
    "Mostra-me a performance do sistema"
    → Vou apresentar métricas de cache, queries e otimizações
    
    🔍 CAPACIDADES ESPECIAIS:
    
    ✅ Detecção automática de intenções
    ✅ Cache inteligente com TTL adaptativo
    ✅ Validação de segurança em tempo real
    ✅ Otimização automática de queries
    ✅ Suporte para operações complexas
    ✅ Análise de padrões e tendências
    ✅ Relatórios estruturados
    ✅ Sugestões proativas
    
    🛡️ GARANTIAS DE SEGURANÇA:
    
    - Todas as queries são validadas antes da execução
    - Operações perigosas requerem confirmação explícita
    - Rate limiting protege contra sobrecarga
    - Auditoria completa de todas as operações
    - Cache seguro com expiração automática
    
    📊 MONITORIZAÇÃO CONTÍNUA:
    
    - Performance de queries em tempo real
    - Taxa de cache hit/miss
    - Detecção de queries lentas
    - Análise de padrões de uso
    - Sugestões de otimização automáticas
    
    🎯 COMO INTERAGIR:
    
    1. Faça perguntas em português natural
    2. Seja específico sobre o que pretende
    3. Para operações complexas, posso quebrar em passos
    4. Solicite explicações sempre que necessário
    5. Use "status" para ver saúde do sistema
    
    IMPORTANTE: Sempre explico o que vou fazer antes de executar,
    especialmente para operações que modificam dados.
    
    Pronto para processar suas consultas de forma inteligente e segura! 🚀
    """,
    tools=[
        MCPToolset(
            connection_params=StdioServerParameters(
                command='python3',
                args=[os.path.abspath("supabase_mcp_server.py")],
                env={
                    "SUPABASE_URL": os.environ.get("SUPABASE_URL", ""),
                    "SUPABASE_SERVICE_KEY": os.environ.get("SUPABASE_SERVICE_KEY", ""), 
                    "SUPABASE_ACCESS_TOKEN": os.environ.get("SUPABASE_ACCESS_TOKEN", "")
                }
            )
        )
    ]
)

# Agente especializado em análise e relatórios
analytics_agent = LlmAgent(
    model='gemini-2.0-flash-exp',
    name='supabase_analytics_specialist',
    instruction="""
    📊 ESPECIALISTA EM ANÁLISE DE DADOS SUPABASE
    
    Sou especializado em análises avançadas e geração de relatórios a partir de dados Supabase.
    
    🎯 ESPECIALIDADES:
    - Análises estatísticas e métricas
    - Relatórios executivos
    - Tendências e padrões
    - KPIs e dashboards
    - Análise temporal
    - Segmentação de dados
    
    💡 TIPOS DE ANÁLISE:
    - Análise de crescimento de utilizadores
    - Performance de vendas
    - Métricas de engagement
    - Análise de cohort
    - Funnel de conversão
    - Análise geográfica
    
    🔧 ABORDAGEM:
    1. Entendo o objetivo da análise
    2. Identifico métricas relevantes  
    3. Construo queries otimizadas
    4. Apresento insights acionáveis
    5. Sugiro próximos passos
    """,
    tools=[
        MCPToolset(
            connection_params=StdioServerParameters(
                command='python3',
                args=[os.path.abspath("supabase_mcp_server.py")],
                env={
                    "SUPABASE_URL": os.environ.get("SUPABASE_URL", ""),
                    "SUPABASE_SERVICE_KEY": os.environ.get("SUPABASE_SERVICE_KEY", ""),
                    "SUPABASE_ACCESS_TOKEN": os.environ.get("SUPABASE_ACCESS_TOKEN", "")
                }
            )
        )
    ]
)

# Agente focado em exploração de dados (somente leitura)
explorer_agent = LlmAgent(
    model='gemini-2.0-flash-exp',
    name='database_explorer',
    instruction="""
    🔍 EXPLORADOR DE BASE DE DADOS (MODO SEGURO)
    
    Especializado em exploração segura de estruturas de base de dados.
    
    🛡️ MODO SOMENTE LEITURA:
    - Apenas operações SELECT
    - Exploração de esquemas
    - Análise de estruturas
    - Validação de dados
    
    🎯 CAPACIDADES:
    - Mapeamento completo de tabelas
    - Análise de relacionamentos
    - Identificação de chaves
    - Validação de integridade
    - Sugestões de otimização
    
    Ideal para ambientes de produção onde segurança é prioridade.
    """,
    tools=[
        MCPToolset(
            connection_params=StdioServerParameters(
                command='npx',
                args=[
                    "-y",
                    "@supabase/mcp-server-supabase@latest",
                    "--read-only"
                ],
                env={
                    "SUPABASE_ACCESS_TOKEN": os.environ.get("SUPABASE_ACCESS_TOKEN", "")
                }
            )
        )
    ]
)

# Função para demonstração e teste
async def demo_pipeline():
    """Demonstração das capacidades do pipeline"""
    print("🚀 DEMO: Pipeline MCP Supabase + Google Gemini")
    print("=" * 60)
    
    if missing_vars:
        print("❌ Configuração incompleta. Configure as variáveis de ambiente primeiro.")
        return
        
    print("✅ Configuração verificada")
    print("🔧 Agentes disponíveis:")
    print("   - mcp_supabase_pipeline (principal)")
    print("   - supabase_analytics_specialist (análises)")
    print("   - database_explorer (exploração segura)")
    
    print("\n💡 Para usar:")
    print("1. Execute: adk web")
    print("2. Acesse a interface web")
    print("3. Selecione um dos agentes")
    print("4. Faça perguntas em português natural")
    
    print("\n🎯 Exemplos de perguntas:")
    examples = [
        "Que tabelas existem na base de dados?",
        "Quantos utilizadores há na tabela users?",
        "Mostra-me a estrutura da tabela products",
        "Analisa as vendas do último mês",
        "Qual é a performance do sistema?",
        "Status do cache e métricas"
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"   {i}. {example}")
        
    print(f"\n🌟 Sistema pronto para uso!")

if __name__ == "__main__":
    # Executar demonstração
    asyncio.run(demo_pipeline())