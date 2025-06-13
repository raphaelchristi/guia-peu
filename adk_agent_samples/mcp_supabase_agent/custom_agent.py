"""
Agente ADK que utiliza o servidor MCP Supabase customizado
Este agente conecta ao nosso servidor MCP personalizado para operações avançadas
"""
import os
import asyncio
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# Carregar variáveis de ambiente
load_dotenv()

class SupabaseDatabaseAgent:
    """Agente especializado em operações de base de dados Supabase"""
    
    def __init__(self):
        self.session_service = InMemorySessionService()
        
    async def create_agent(self) -> tuple[LlmAgent, MCPToolset]:
        """Cria o agente ADK com MCPToolset personalizado"""
        
        # Caminho absoluto para o servidor MCP customizado
        server_script_path = os.path.abspath("fixed_mcp_server.py")
        
        # Configurar MCPToolset para usar nosso servidor customizado
        toolset = MCPToolset(
            connection_params=StdioServerParameters(
                command='python3',
                args=[server_script_path],
                # Passar variáveis de ambiente necessárias
                env={
                    "SUPABASE_URL": os.environ.get("SUPABASE_URL", ""),
                    "SUPABASE_SERVICE_KEY": os.environ.get("SUPABASE_SERVICE_KEY", ""),
                    "SUPABASE_ACCESS_TOKEN": os.environ.get("SUPABASE_ACCESS_TOKEN", "")
                }
            ),
            # Filtrar ferramentas específicas se necessário
            tool_filter=['execute_sql', 'query_table', 'list_tables', 'describe_table']
        )

        # Criar agente com instruções detalhadas
        agent = LlmAgent(
            model='gemini-2.0-flash',
            name='supabase_expert_agent',
            instruction="""
            Você é um especialista em bases de dados Supabase com capacidades avançadas de análise.
            
            SUAS FERRAMENTAS:
            1. execute_sql: Executa queries SQL com validação de segurança
            2. query_table: Consulta tabelas com filtros avançados e paginação
            3. list_tables: Lista todas as tabelas disponíveis
            4. describe_table: Mostra a estrutura detalhada de uma tabela
            
            FLUXO DE TRABALHO RECOMENDADO:
            1. Para novas bases de dados: comece com list_tables
            2. Para explorar estrutura: use describe_table
            3. Para consultas simples: use query_table
            4. Para análises complexas: use execute_sql
            
            DIRETRIZES DE SEGURANÇA:
            - Sempre explique que operação vai realizar antes de executar
            - Use safe_mode=true por defeito em execute_sql
            - Para operações de escrita, solicite confirmação explícita
            - Limite resultados grandes com LIMIT nas queries
            
            COMUNICAÇÃO:
            - Forneça explicações claras sobre os dados obtidos
            - Sugira melhorias ou insights baseados nos resultados
            - Se houver erros, explique o problema e sugira soluções
            - Formate resultados de forma legível
            
            EXEMPLOS DE USO:
            - "Liste todas as tabelas" → list_tables
            - "Mostre a estrutura da tabela users" → describe_table
            - "Quantos utilizadores há na tabela users?" → query_table ou execute_sql
            - "Encontre utilizadores criados na última semana" → execute_sql com filtro temporal
            """,
            tools=[toolset]
        )
        
        return agent, toolset

    async def run_query(self, query: str) -> None:
        """Executa uma consulta através do agente"""
        try:
            # Criar sessão
            session = await self.session_service.create_session(
                state={}, 
                app_name='supabase_mcp_app', 
                user_id='database_user'
            )

            # Criar agente
            agent, toolset = await self.create_agent()
            
            # Criar runner
            runner = Runner(
                app_name='supabase_mcp_app',
                agent=agent,
                session_service=self.session_service,
            )

            # Preparar mensagem
            content = types.Content(
                role='user', 
                parts=[types.Part(text=query)]
            )

            print(f"🤖 Processando consulta: '{query}'")
            print("=" * 50)

            # Executar consulta
            events_async = runner.run_async(
                session_id=session.id,
                user_id=session.user_id,
                new_message=content
            )

            # Processar eventos
            async for event in events_async:
                if hasattr(event, 'content') and event.content:
                    print(f"📊 Resposta: {event.content}")
                elif hasattr(event, 'text') and event.text:
                    print(f"📝 Resultado: {event.text}")
                else:
                    print(f"📋 Evento: {event}")

            # Limpeza
            await toolset.close()
            print("\n✅ Consulta processada com sucesso")

        except Exception as e:
            print(f"❌ Erro na execução: {e}")

# Agente principal para usar com adk web
root_agent = LlmAgent(
    model='gemini-2.0-flash',
    name='supabase_database_expert',
    instruction="""
    Sou um especialista em bases de dados Supabase com acesso a ferramentas avançadas.
    
    Posso ajudar com:
    - Exploração de esquemas de base de dados
    - Consultas SQL complexas e análises
    - Relatórios e métricas de dados
    - Optimização de queries
    - Análise de performance
    
    Como funciono:
    1. Analiso a sua solicitação
    2. Escolho a ferramenta mais adequada
    3. Executo a operação de forma segura
    4. Apresento os resultados de forma clara
    5. Sugiro melhorias ou próximos passos
    
    Experimente perguntar:
    - "Que tabelas existem na base de dados?"
    - "Mostra-me a estrutura da tabela X"
    - "Quantos registos há na tabela Y?"
    - "Análise os dados de vendas do último mês"
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
    ]
)

# Função principal para teste direto
async def main():
    """Função principal para teste do agente"""
    agent_manager = SupabaseDatabaseAgent()
    
    # Exemplos de consultas
    test_queries = [
        "Liste todas as tabelas disponíveis na base de dados",
        "Quantas tabelas existem no total?",
        # "Descreva a estrutura da tabela 'users' se existir",
        # "Mostre-me os primeiros 5 registos de qualquer tabela disponível"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Testando: {query}")
        await agent_manager.run_query(query)
        print("\n" + "="*60)

if __name__ == "__main__":
    print("🚀 Iniciando teste do agente Supabase MCP...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Teste interrompido pelo utilizador")
    except Exception as e:
        print(f"\n❌ Erro no teste: {e}")