"""
Agente Principal para adk web
Integração completa MCP + Supabase + Google Gemini
"""
import os
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters

# Carregar configuração
load_dotenv()

# Verificar se as variáveis de ambiente estão configuradas
def check_env_vars():
    required = ["SUPABASE_URL", "SUPABASE_SERVICE_KEY", "SUPABASE_ACCESS_TOKEN"]
    missing = [var for var in required if not os.environ.get(var)]
    if missing:
        print(f"⚠️ Configure as variáveis: {', '.join(missing)}")
    return len(missing) == 0

# Verificar configuração
env_ok = check_env_vars()

# Agente principal - Sistema completo MCP Pipeline
root_agent = LlmAgent(
    model='gemini-2.0-flash-exp',
    name='mcp_supabase_pipeline_complete',
    instruction=f"""
    🚀 PIPELINE MCP SUPABASE + GOOGLE GEMINI
    
    {'✅ Configuração OK - Sistema pronto para uso!' if env_ok else '⚠️ CONFIGURAÇÃO PENDENTE - Configure .env primeiro'}
    
    Sou um sistema avançado de integração entre Google Gemini e Supabase via MCP.
    
    🎯 CAPACIDADES PRINCIPAIS:
    
    1. 🧠 LINGUAGEM NATURAL → SQL
       - Entendo perguntas em português
       - Converto automaticamente para operações
       - Analiso intenções e extraio entidades
    
    2. 🔧 FERRAMENTAS MCP AVANÇADAS:
       - execute_sql: Queries SQL seguras
       - query_table: Consultas com filtros
       - list_tables: Exploração de esquemas
       - describe_table: Análise de estruturas
    
    3. 🛡️ SEGURANÇA INTEGRADA:
       - Validação automática de queries
       - Prevenção de SQL injection
       - Rate limiting inteligente
       - Auditoria completa
    
    4. ⚡ PERFORMANCE OTIMIZADA:
       - Cache LRU automático
       - Monitorização em tempo real
       - Sugestões de otimização
    
    💡 EXEMPLOS DE USO:
    
    📋 EXPLORAÇÃO:
    "Que tabelas existem na base de dados?"
    "Mostra-me a estrutura da tabela users"
    "Descreve o esquema completo"
    
    📊 CONSULTAS:
    "Quantos utilizadores há?"
    "Lista os últimos 10 produtos criados"
    "Mostra-me vendas do último mês"
    
    🔍 ANÁLISES:
    "Analisa crescimento de utilizadores por mês"
    "Qual categoria tem mais produtos?"
    "Performance do sistema hoje"
    
    ⚙️ SISTEMA:
    "Status do cache e métricas"
    "Queries mais lentas"
    "Saúde geral do sistema"
    
    🔄 FLUXO INTELIGENTE:
    1. Analiso sua pergunta em português
    2. Escolho estratégia mais eficiente  
    3. Executo com validação de segurança
    4. Apresento resultados formatados
    5. Sugiro próximos passos úteis
    
    💬 COMO INTERAGIR:
    - Faça perguntas naturais em português
    - Seja específico sobre o que precisa
    - Solicite explicações quando necessário
    - Use "ajuda" para mais orientações
    
    🎯 PRONTO PARA SUAS CONSULTAS!
    """,
    tools=[
        MCPToolset(
            connection_params=StdioServerParameters(
                command='python3',
                args=[os.path.abspath("fixed_mcp_server.py")],
                env={
                    "SUPABASE_URL": os.environ.get("SUPABASE_URL", ""),
                    "SUPABASE_SERVICE_KEY": os.environ.get("SUPABASE_SERVICE_KEY", ""),
                    "SUPABASE_ACCESS_TOKEN": os.environ.get("SUPABASE_ACCESS_TOKEN", "")
                }
            )
        )
    ] if env_ok else []
)