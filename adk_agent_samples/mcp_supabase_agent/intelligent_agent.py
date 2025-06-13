"""
Agente Inteligente com Processamento de Linguagem Natural
Combina o processador NLP com ferramentas MCP para interações mais naturais
"""
import os
import json
import asyncio
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from .nlp_processor import process_natural_language_query, QueryType

# Carregar variáveis de ambiente
load_dotenv()

class IntelligentSupabaseAgent:
    """Agente inteligente com processamento de linguagem natural"""
    
    def __init__(self):
        self.session_service = InMemorySessionService()
        
    async def create_enhanced_agent(self) -> tuple[LlmAgent, MCPToolset]:
        """Cria agente com capacidades de NLP melhoradas"""
        
        server_script_path = os.path.abspath("fixed_mcp_server.py")
        
        toolset = MCPToolset(
            connection_params=StdioServerParameters(
                command='python3',
                args=[server_script_path],
                env={
                    "SUPABASE_URL": os.environ.get("SUPABASE_URL", ""),
                    "SUPABASE_SERVICE_KEY": os.environ.get("SUPABASE_SERVICE_KEY", ""),
                    "SUPABASE_ACCESS_TOKEN": os.environ.get("SUPABASE_ACCESS_TOKEN", "")
                }
            )
        )

        agent = LlmAgent(
            model='gemini-2.0-flash',
            name='intelligent_supabase_agent',
            instruction="""
            Você é um agente inteligente especializado em bases de dados Supabase com processamento de linguagem natural avançado.
            
            FLUXO DE TRABALHO INTELIGENTE:
            
            1. ANÁLISE DA CONSULTA:
               - Analise cuidadosamente a pergunta do utilizador
               - Identifique o tipo de operação desejada
               - Extraia entidades relevantes (tabelas, campos, filtros)
               
            2. ESTRATÉGIA DE EXECUÇÃO:
               - Para consultas simples: use query_table com filtros
               - Para análises complexas: use execute_sql
               - Para exploração: comece com list_tables ou describe_table
               - Para agregações: construa queries SQL optimizadas
               
            3. VALIDAÇÃO E SEGURANÇA:
               - Sempre use safe_mode=true em execute_sql
               - Limite resultados grandes com LIMIT
               - Valide nomes de tabelas antes de usar
               - Explique operações perigosas antes de executar
               
            4. COMUNICAÇÃO INTELIGENTE:
               - Explique sua estratégia antes de executar
               - Formate resultados de forma legível
               - Forneça insights e sugestões baseados nos dados
               - Sugira optimizações ou consultas relacionadas
               
            CAPACIDADES ESPECIAIS:
            - Entende consultas em português natural
            - Converte automaticamente para operações SQL
            - Sugere melhores práticas de consulta
            - Identifica padrões nos dados
            - Gera relatórios estruturados
            
            EXEMPLOS DE INTERAÇÕES:
            
            Utilizador: "Quantos utilizadores há?"
            Você: "Vou consultar o número total de utilizadores. Primeiro vou verificar se a tabela 'users' existe, depois contar os registos."
            
            Utilizador: "Mostra-me vendas do último mês"
            Você: "Vou analisar as vendas recentes. Vou filtrar a tabela 'sales' para registos do último mês e apresentar um resumo."
            
            Utilizador: "Que tabelas posso consultar?"
            Você: "Vou listar todas as tabelas disponíveis na base de dados e explicar o que cada uma contém."
            
            REGRAS IMPORTANTES:
            - Sempre confirme a operação antes de executar modificações
            - Explique resultados complexos de forma simples
            - Sugira consultas de follow-up relevantes
            - Mantenha foco na utilidade e clareza
            """,
            tools=[toolset]
        )
        
        return agent, toolset

    async def process_intelligent_query(self, user_query: str) -> Dict[str, Any]:
        """Processa consulta usando NLP e executa via MCP"""
        try:
            # Processar linguagem natural
            nlp_result = process_natural_language_query(user_query)
            
            if not nlp_result["success"]:
                return {
                    "success": False,
                    "error": "Não consegui entender a consulta",
                    "details": nlp_result["error"]
                }
            
            intent = nlp_result["intent"]
            mcp_call = nlp_result["mcp_call"]
            
            # Criar sessão e agente
            session = await self.session_service.create_session(
                state={}, 
                app_name='intelligent_supabase_app', 
                user_id='smart_user'
            )

            agent, toolset = await self.create_enhanced_agent()
            
            runner = Runner(
                app_name='intelligent_supabase_app',
                agent=agent,
                session_service=self.session_service,
            )

            # Construir prompt inteligente que inclui a análise NLP
            intelligent_prompt = f"""
            CONSULTA DO UTILIZADOR: "{user_query}"
            
            ANÁLISE AUTOMÁTICA:
            - Tipo de operação: {intent['query_type']}
            - Tabela identificada: {intent['table_name'] or 'não especificada'}
            - Confiança da análise: {intent['confidence']:.2f}
            
            OPERAÇÃO SUGERIDA:
            - Ferramenta: {mcp_call['tool']}
            - Argumentos: {json.dumps(mcp_call['arguments'], indent=2)}
            
            INSTRUÇÕES:
            1. Execute a operação sugerida usando as ferramentas disponíveis
            2. Se a tabela não foi identificada, liste as tabelas primeiro
            3. Explique o que está a fazer e porquê
            4. Formate os resultados de forma clara e legível
            5. Sugira consultas relacionadas se relevante
            
            EXECUTE A OPERAÇÃO AGORA:
            """

            content = types.Content(
                role='user', 
                parts=[types.Part(text=intelligent_prompt)]
            )

            # Executar através do agente
            response_parts = []
            events_async = runner.run_async(
                session_id=session.id,
                user_id=session.user_id,
                new_message=content
            )

            async for event in events_async:
                if hasattr(event, 'content') and event.content:
                    response_parts.append(event.content)
                elif hasattr(event, 'text') and event.text:
                    response_parts.append(event.text)

            # Limpeza
            await toolset.close()

            return {
                "success": True,
                "user_query": user_query,
                "nlp_analysis": intent,
                "mcp_operation": mcp_call,
                "response": " ".join(str(part) for part in response_parts),
                "confidence": intent['confidence']
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "user_query": user_query
            }

    async def chat_session(self):
        """Sessão de chat interativa"""
        print("🤖 Agente Inteligente Supabase Iniciado!")
        print("💡 Pode fazer perguntas em português natural sobre a base de dados")
        print("📝 Exemplos: 'Quantos utilizadores há?', 'Lista as tabelas', 'Vendas do último mês'")
        print("🔄 Digite 'sair' para terminar\n")
        
        while True:
            try:
                user_input = input("🔍 Sua pergunta: ").strip()
                
                if user_input.lower() in ['sair', 'exit', 'quit']:
                    print("👋 Sessão terminada!")
                    break
                    
                if not user_input:
                    continue
                    
                print(f"\n🧠 Processando: '{user_input}'...")
                print("⏳ Aguarde...\n")
                
                result = await self.process_intelligent_query(user_input)
                
                if result["success"]:
                    print("📊 ANÁLISE NLP:")
                    print(f"   Tipo: {result['nlp_analysis']['query_type']}")
                    print(f"   Tabela: {result['nlp_analysis']['table_name'] or 'não identificada'}")
                    print(f"   Confiança: {result['confidence']:.1%}")
                    
                    print("\n🔧 OPERAÇÃO MCP:")
                    print(f"   Ferramenta: {result['mcp_operation']['tool']}")
                    
                    print("\n💬 RESPOSTA:")
                    print(result["response"])
                    
                else:
                    print(f"❌ Erro: {result['error']}")
                    
                print("\n" + "="*60 + "\n")
                
            except KeyboardInterrupt:
                print("\n👋 Sessão interrompida!")
                break
            except Exception as e:
                print(f"❌ Erro inesperado: {e}")

# Agente para usar com adk web
root_agent = LlmAgent(
    model='gemini-2.0-flash',
    name='intelligent_database_assistant',
    instruction="""
    Sou um assistente inteligente de base de dados com processamento de linguagem natural.
    
    🧠 CAPACIDADES INTELIGENTES:
    - Entendo perguntas em português natural
    - Converto automaticamente para operações SQL
    - Analiso padrões e forneço insights
    - Sugiro optimizações e consultas relacionadas
    
    🔍 COMO FUNCIONO:
    1. Analiso sua pergunta em linguagem natural
    2. Identifico a melhor estratégia de consulta
    3. Executo operações na base de dados
    4. Apresento resultados de forma clara
    5. Sugiro próximos passos relevantes
    
    💡 EXPERIMENTE PERGUNTAR:
    - "Quantos registos há na tabela X?"
    - "Mostra-me as vendas do último mês"
    - "Que tabelas existem na base de dados?"
    - "Qual é a média de idade dos utilizadores?"
    - "Lista os produtos mais vendidos"
    
    🛡️ SEGURANÇA:
    - Uso apenas operações seguras de leitura por defeito
    - Valido todas as consultas antes de executar
    - Explico o que vou fazer antes de fazer
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

# Função principal para teste
async def main():
    """Função principal para teste do agente inteligente"""
    agent = IntelligentSupabaseAgent()
    
    # Teste com consultas automáticas
    test_queries = [
        "Que tabelas existem?",
        "Quantos registos há na base de dados?",
        "Mostra-me a estrutura de alguma tabela"
    ]
    
    print("🚀 Testando Agente Inteligente...")
    
    for query in test_queries:
        print(f"\n🔍 Teste: {query}")
        result = await agent.process_intelligent_query(query)
        
        if result["success"]:
            print(f"✅ Sucesso - Confiança: {result['confidence']:.1%}")
            print(f"📝 Resposta: {result['response'][:200]}...")
        else:
            print(f"❌ Erro: {result['error']}")
        
        print("-" * 50)
    
    # Iniciar sessão interativa
    print("\n🎉 Iniciando sessão de chat interativa...")
    await agent.chat_session()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Programa terminado pelo utilizador")