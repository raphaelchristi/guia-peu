"""
MCP Supabase Agent - Pipeline de integração entre Google Gemini e Supabase via MCP
Este agente utiliza o Google ADK com MCPToolset para conectar ao servidor MCP do Supabase
"""
import os
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters

# Carregar variáveis de ambiente
load_dotenv()

# Obter Personal Access Token do Supabase
supabase_access_token = os.environ.get("SUPABASE_ACCESS_TOKEN")

if not supabase_access_token:
    print("AVISO: SUPABASE_ACCESS_TOKEN não está definido. Configure no arquivo .env")
    supabase_access_token = "your_supabase_access_token_here"

# Definir o agente ADK com ferramentas MCP do Supabase
root_agent = LlmAgent(
    model='gemini-2.0-flash',
    name='supabase_database_assistant',
    instruction="""
    Você é um assistente especializado em bases de dados Supabase.
    
    Suas capacidades incluem:
    - Executar queries SQL em bases de dados Supabase
    - Consultar tabelas específicas com filtros
    - Analisar estruturas de bases de dados
    - Gerar relatórios e análises de dados
    - Traduzir linguagem natural para operações de base de dados
    
    Sempre explique que operações está a realizar e porquê.
    Forneça respostas claras e estruturadas sobre os dados obtidos.
    Se encontrar erros, explique o que aconteceu e sugira soluções.
    
    Use as ferramentas disponíveis para:
    1. Listar tabelas e esquemas disponíveis
    2. Executar queries SQL seguras
    3. Consultar dados específicos
    4. Gerar análises e relatórios
    """,
    tools=[
        MCPToolset(
            connection_params=StdioServerParameters(
                command='npx',
                args=[
                    "-y",  # Auto-confirmar instalação do pacote
                    "@supabase/mcp-server-supabase@latest",
                ],
                # Passar o token de acesso como variável de ambiente
                env={
                    "SUPABASE_ACCESS_TOKEN": supabase_access_token
                }
            ),
            # Filtros opcionais para ferramentas específicas
            # tool_filter=['execute_sql', 'list_tables', 'describe_table']
        )
    ],
)

# Agente adicional para operações somente leitura (mais seguro)
readonly_agent = LlmAgent(
    model='gemini-2.0-flash',
    name='supabase_readonly_assistant',
    instruction="""
    Você é um assistente de leitura para bases de dados Supabase (modo somente leitura).
    
    Foque em:
    - Consultas seguras de dados
    - Análises e relatórios
    - Exploração de esquemas
    - Geração de insights
    
    IMPORTANTE: Opere apenas em modo de leitura. Não execute operações de escrita, 
    atualização ou eliminação de dados.
    """,
    tools=[
        MCPToolset(
            connection_params=StdioServerParameters(
                command='npx',
                args=[
                    "-y",
                    "@supabase/mcp-server-supabase@latest",
                    "--read-only",  # Modo somente leitura
                ],
                env={
                    "SUPABASE_ACCESS_TOKEN": supabase_access_token
                }
            ),
        )
    ],
)