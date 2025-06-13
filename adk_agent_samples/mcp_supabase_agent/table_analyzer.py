"""
Analisador de Tabelas Específicas do Supabase
Conecta automaticamente ao projeto e analisa estruturas de tabelas
"""
import os
import asyncio
from typing import Dict, Any, List
from dotenv import load_dotenv

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# Carregar configuração
load_dotenv()

class TableAnalyzer:
    """Analisador automático de tabelas Supabase"""
    
    def __init__(self):
        self.session_service = InMemorySessionService()
        
    async def create_analyzer_agent(self):
        """Cria agente especializado em análise de tabelas"""
        
        toolset = MCPToolset(
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

        agent = LlmAgent(
            model='gemini-2.0-flash-exp',
            name='table_structure_analyzer',
            instruction="""
            Sou um especialista em análise de estruturas de tabelas Supabase.
            
            MINHA FUNÇÃO:
            1. Analisar estruturas completas de tabelas
            2. Identificar relacionamentos e chaves
            3. Sugerir otimizações e índices
            4. Gerar queries de exemplo
            5. Criar configurações personalizadas
            
            PROCESSO DE ANÁLISE:
            
            PASSO 1 - EXPLORAÇÃO INICIAL:
            - Listar todas as tabelas disponíveis
            - Identificar tabela principal de interesse
            - Verificar permissões de acesso
            
            PASSO 2 - ANÁLISE ESTRUTURAL:
            - Descrever estrutura completa da tabela
            - Identificar tipos de dados de todas as colunas
            - Mapear chaves primárias e estrangeiras
            - Analisar constraints e validações
            
            PASSO 3 - ANÁLISE DE DADOS:
            - Verificar quantidade total de registos
            - Analisar distribuição de dados
            - Identificar padrões e anomalias
            - Verificar valores nulos e únicos
            
            PASSO 4 - OTIMIZAÇÃO:
            - Sugerir índices para performance
            - Identificar queries comuns úteis
            - Propor estratégias de cache
            - Recomendar boas práticas
            
            PASSO 5 - CONFIGURAÇÃO:
            - Gerar configuração personalizada
            - Criar queries de exemplo
            - Definir regras de negócio
            - Estabelecer limites de segurança
            
            FORMATO DE RESPOSTA:
            - Estruturado e detalhado
            - Inclui exemplos práticos
            - Foco em usabilidade
            - Sugestões acionáveis
            """,
            tools=[toolset]
        )
        
        return agent, toolset

    async def analyze_table(self, table_name: str = None) -> Dict[str, Any]:
        """Analisa uma tabela específica ou descobre tabelas disponíveis"""
        
        try:
            session = await self.session_service.create_session(
                state={}, 
                app_name='table_analyzer_app', 
                user_id='analyzer_user'
            )

            agent, toolset = await self.create_analyzer_agent()
            
            runner = Runner(
                app_name='table_analyzer_app',
                agent=agent,
                session_service=self.session_service,
            )

            if table_name:
                # Analisar tabela específica
                prompt = f"""
                ANÁLISE COMPLETA DA TABELA: {table_name}
                
                Execute uma análise completa seguindo este processo:
                
                1. VERIFICAR EXISTÊNCIA:
                   - Confirme se a tabela '{table_name}' existe
                   - Se não existir, liste todas as tabelas disponíveis
                
                2. ESTRUTURA DETALHADA:
                   - Use describe_table para obter estrutura completa
                   - Identifique tipos de dados, chaves, constraints
                   - Analise relacionamentos possíveis
                
                3. ANÁLISE DE DADOS:
                   - Conte total de registos
                   - Mostre 3-5 exemplos de dados (sem informações sensíveis)
                   - Identifique padrões nos dados
                
                4. OTIMIZAÇÕES:
                   - Sugira índices para melhor performance
                   - Identifique colunas mais consultadas
                   - Proponha queries comuns úteis
                
                5. CONFIGURAÇÃO RECOMENDADA:
                   - Gere configuração personalizada para esta tabela
                   - Inclua regras de negócio relevantes
                   - Defina limites de segurança apropriados
                
                IMPORTANTE: 
                - Seja detalhado mas objetivo
                - Foque em informações práticas
                - Sugira melhorias acionáveis
                - Mantenha segurança de dados
                """
            else:
                # Descobrir tabelas disponíveis
                prompt = """
                DESCOBERTA DE TABELAS DISPONÍVEIS
                
                Execute uma análise exploratória completa:
                
                1. LISTAR TODAS AS TABELAS:
                   - Use list_tables para obter lista completa
                   - Identifique tabelas principais vs auxiliares
                   - Estime tamanho e importância de cada uma
                
                2. ANÁLISE PRELIMINAR:
                   - Para cada tabela principal, execute describe_table
                   - Identifique possíveis relacionamentos
                   - Categorize por tipo de dados (users, products, orders, etc.)
                
                3. RECOMENDAÇÕES:
                   - Sugira qual tabela seria mais interessante analisar primeiro
                   - Identifique tabelas que podem ter dados sensíveis
                   - Proponha estratégia de exploração
                
                4. PRÓXIMOS PASSOS:
                   - Liste queries úteis para cada tabela
                   - Sugira análises que podem ser feitas
                   - Identifique oportunidades de otimização
                
                Forneça uma visão geral organizada e acionável do banco de dados.
                """

            content = types.Content(
                role='user', 
                parts=[types.Part(text=prompt)]
            )

            response_parts = []
            events_async = runner.run_async(
                session_id=session.id,
                user_id=session.user_id,
                new_message=content
            )

            async for event in events_async:
                if hasattr(event, 'content') and event.content:
                    response_parts.append(str(event.content))
                elif hasattr(event, 'text') and event.text:
                    response_parts.append(str(event.text))

            await toolset.close()

            return {
                "success": True,
                "table_name": table_name,
                "analysis": " ".join(response_parts),
                "timestamp": asyncio.get_event_loop().time()
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "table_name": table_name
            }

    async def interactive_analysis(self):
        """Sessão interativa de análise de tabelas"""
        print("🔍 ANALISADOR DE TABELAS SUPABASE")
        print("=" * 50)
        print("Conectando ao seu projeto Supabase...")
        
        # Verificar configuração
        required_vars = ["SUPABASE_URL", "SUPABASE_SERVICE_KEY", "SUPABASE_ACCESS_TOKEN"]
        missing = [var for var in required_vars if not os.environ.get(var)]
        
        if missing:
            print("❌ Configuração incompleta!")
            print(f"Configure: {', '.join(missing)}")
            return
            
        print("✅ Configuração OK")
        
        # Descobrir tabelas disponíveis primeiro
        print("\n🔍 Descobrindo tabelas disponíveis...")
        discovery_result = await self.analyze_table()
        
        if discovery_result["success"]:
            print("📊 TABELAS ENCONTRADAS:")
            print(discovery_result["analysis"])
        else:
            print(f"❌ Erro na descoberta: {discovery_result['error']}")
            return
        
        # Análise interativa
        print("\n" + "="*60)
        print("💡 Agora você pode analisar tabelas específicas")
        print("Digite o nome da tabela ou 'sair' para terminar")
        
        while True:
            try:
                table_name = input("\n🔍 Tabela para analisar: ").strip()
                
                if table_name.lower() in ['sair', 'exit', 'quit']:
                    print("👋 Análise terminada!")
                    break
                    
                if not table_name:
                    continue
                    
                print(f"\n⏳ Analisando tabela '{table_name}'...")
                
                result = await self.analyze_table(table_name)
                
                if result["success"]:
                    print(f"\n📊 ANÁLISE COMPLETA - {table_name.upper()}")
                    print("=" * 60)
                    print(result["analysis"])
                    
                    # Perguntar se quer salvar configuração
                    save = input(f"\n💾 Salvar configuração para '{table_name}'? (y/N): ")
                    if save.lower() == 'y':
                        await self.save_table_config(table_name, result["analysis"])
                        
                else:
                    print(f"❌ Erro na análise: {result['error']}")
                    
                print("\n" + "-"*60)
                
            except KeyboardInterrupt:
                print("\n👋 Análise interrompida!")
                break
            except Exception as e:
                print(f"❌ Erro inesperado: {e}")

    async def save_table_config(self, table_name: str, analysis: str):
        """Salva configuração da tabela analisada"""
        try:
            config_file = f"table_config_{table_name}.json"
            
            config_data = {
                "table_name": table_name,
                "analysis_date": asyncio.get_event_loop().time(),
                "full_analysis": analysis,
                "project_id": os.environ.get("SUPABASE_URL", "").split("//")[1].split(".")[0] if os.environ.get("SUPABASE_URL") else "unknown"
            }
            
            import json
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
                
            print(f"✅ Configuração salva em: {config_file}")
            
        except Exception as e:
            print(f"❌ Erro ao salvar: {e}")

# Agente específico para análise de tabelas para uso com adk web
table_analyzer_agent = LlmAgent(
    model='gemini-2.0-flash-exp',
    name='supabase_table_analyzer',
    instruction="""
    🔍 ANALISADOR ESPECIALIZADO DE TABELAS SUPABASE
    
    Sou um especialista em análise profunda de estruturas de tabelas Supabase.
    
    🎯 FUNCIONALIDADES:
    
    1. 📋 DESCOBERTA AUTOMÁTICA:
       - Listo todas as tabelas do projeto
       - Identifico tabelas principais vs auxiliares
       - Analiso relacionamentos entre tabelas
    
    2. 🔬 ANÁLISE ESTRUTURAL:
       - Estrutura completa de colunas
       - Tipos de dados e constraints
       - Chaves primárias e estrangeiras
       - Índices existentes
    
    3. 📊 ANÁLISE DE DADOS:
       - Volume de dados por tabela
       - Distribuição e padrões
       - Qualidade dos dados
       - Valores únicos e nulos
    
    4. ⚡ OTIMIZAÇÕES:
       - Sugestões de índices
       - Queries comuns úteis
       - Estratégias de cache
       - Boas práticas
    
    💡 COMO USAR:
    
    "Que tabelas existem no projeto?"
    → Lista e categoriza todas as tabelas
    
    "Analisa a estrutura da tabela X"
    → Análise completa de uma tabela específica
    
    "Sugere otimizações para a tabela Y"
    → Recomendações de performance e índices
    
    "Mostra dados de exemplo da tabela Z"
    → Exemplos de dados (sem informações sensíveis)
    
    🛡️ SEGURANÇA:
    - Não exponho dados sensíveis
    - Uso apenas queries de leitura
    - Respeito limites de privacidade
    - Aplico boas práticas de segurança
    
    Especializado no seu projeto Supabase específico!
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

async def main():
    """Função principal para análise de tabelas"""
    analyzer = TableAnalyzer()
    await analyzer.interactive_analysis()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Análise terminada pelo utilizador")