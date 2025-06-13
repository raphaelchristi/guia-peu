"""
Agente Direto para Tabela Guia (Sem MCP)
Conecta diretamente ao Supabase usando FunctionTool
"""
import os
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.tools.function_tool import FunctionTool
from supabase import create_client

load_dotenv()

# Cliente Supabase global
supabase = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_SERVICE_KEY")
)

def query_guia_table(query_type: str = "count", filters: dict = None, limit: int = 10) -> dict:
    """
    Consulta a tabela guia com diferentes tipos de operações
    
    Args:
        query_type: Tipo de consulta ("count", "samples", "bairros", "search")
        filters: Filtros a aplicar (ex: {"Bairro": "IBIRAPUERA"})
        limit: Limite de resultados
    """
    try:
        if query_type == "count":
            # Contar total de registros
            result = supabase.table("guia").select("*", count="exact").execute()
            return {
                "success": True,
                "type": "count",
                "total_registros": result.count,
                "message": f"Total de {result.count:,} registros na tabela guia"
            }
            
        elif query_type == "samples":
            # Obter amostras de dados
            query = supabase.table("guia").select("*").limit(limit)
            if filters:
                for key, value in filters.items():
                    query = query.ilike(key, f"%{value}%")
            
            result = query.execute()
            return {
                "success": True,
                "type": "samples",
                "data": result.data,
                "count": len(result.data),
                "message": f"Retornando {len(result.data)} amostras"
            }
            
        elif query_type == "bairros":
            # Análise por bairros
            result = supabase.table("guia").select("Bairro").execute()
            
            bairros = {}
            for item in result.data:
                bairro = item.get("Bairro", "").strip()
                if bairro:
                    bairros[bairro] = bairros.get(bairro, 0) + 1
            
            top_bairros = sorted(bairros.items(), key=lambda x: x[1], reverse=True)[:limit]
            
            return {
                "success": True,
                "type": "bairros",
                "total_bairros": len(bairros),
                "top_bairros": [{"bairro": b, "quantidade": q} for b, q in top_bairros],
                "message": f"Análise de {len(bairros)} bairros únicos"
            }
            
        elif query_type == "search":
            # Busca personalizada
            query = supabase.table("guia").select("*").limit(limit)
            
            if filters:
                for key, value in filters.items():
                    if key in ["Bairro", "Nome do Logradouro"]:
                        query = query.ilike(key, f"%{value}%")
                    else:
                        query = query.eq(key, value)
            
            result = query.execute()
            return {
                "success": True,
                "type": "search",
                "data": result.data,
                "count": len(result.data),
                "filters_applied": filters,
                "message": f"Busca retornou {len(result.data)} resultados"
            }
            
        else:
            return {
                "success": False,
                "error": f"Tipo de consulta '{query_type}' não suportado",
                "supported_types": ["count", "samples", "bairros", "search"]
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "type": query_type
        }

def analyze_guia_structure() -> dict:
    """Analisa a estrutura da tabela guia"""
    try:
        result = supabase.table("guia").select("*").limit(1).execute()
        
        if not result.data:
            return {"success": False, "error": "Tabela vazia"}
        
        sample = result.data[0]
        structure = []
        
        for column, value in sample.items():
            # Inferir tipo
            if value is None:
                data_type = "NULL"
            elif isinstance(value, bool):
                data_type = "BOOLEAN"
            elif isinstance(value, int):
                data_type = "INTEGER"
            elif isinstance(value, float):
                data_type = "DECIMAL"
            elif isinstance(value, str):
                data_type = "TEXT" if len(value) > 100 else "VARCHAR"
            else:
                data_type = "UNKNOWN"
            
            structure.append({
                "column": column,
                "type": data_type,
                "sample": str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
            })
        
        return {
            "success": True,
            "total_columns": len(structure),
            "structure": structure,
            "message": f"Tabela guia tem {len(structure)} colunas"
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# Agente especializado na tabela guia (sem MCP)
root_agent = LlmAgent(
    model='gemini-2.0-flash-exp',
    name='guia_direct_agent',
    instruction="""
    🏠 ESPECIALISTA DIRETO NA TABELA GUIA
    
    Sou um especialista na tabela "guia" de dados imobiliários do seu projeto Supabase.
    
    📊 DADOS DISPONÍVEIS:
    - **14.456 registros** de transações imobiliárias
    - **28 colunas** com informações completas
    - **158 bairros únicos** em São Paulo
    - Dados de endereço, valores, datas, características
    
    🔧 FERRAMENTAS DISPONÍVEIS:
    
    1. **query_guia_table**: Consulta principal da tabela
       - count: Conta registros
       - samples: Obtém amostras
       - bairros: Análise por bairros
       - search: Busca personalizada
    
    2. **analyze_guia_structure**: Analisa estrutura da tabela
    
    💡 EXEMPLOS DE USO:
    
    "Quantos registros há?"
    → Uso query_guia_table com type="count"
    
    "Mostra-me alguns exemplos"
    → Uso query_guia_table com type="samples"
    
    "Análise por bairros"
    → Uso query_guia_table com type="bairros"
    
    "Buscar imóveis no Ibirapuera"
    → Uso query_guia_table com type="search" e filters={"Bairro": "IBIRAPUERA"}
    
    "Qual é a estrutura da tabela?"
    → Uso analyze_guia_structure
    
    🎯 PRINCIPAIS COLUNAS DISPONÍVEIS:
    - N° do Cadastro (SQL)
    - Nome do Logradouro, Número, Complemento, Bairro, CEP
    - Natureza de Transação
    - Valor de Transação (declarado pelo contribuinte)
    - Data de Transação
    - Valor Venal de Referência
    - Tipo de Financiamento
    - Área do Terreno, Área Construída
    - Uso (IPTU), Padrão (IPTU)
    
    🔍 ESTRATÉGIA DE RESPOSTA:
    1. Analiso sua pergunta
    2. Escolho a ferramenta apropriada
    3. Configuro filtros se necessário
    4. Executo consulta
    5. Apresento resultados formatados
    6. Sugiro consultas relacionadas
    
    💬 COMUNICAÇÃO:
    - Sempre explico que dados estou buscando
    - Formato resultados de forma legível
    - Sugiro próximas análises úteis
    - Foco em insights acionáveis
    
    Pronto para analisar seus dados imobiliários! 🚀
    """,
    tools=[
        FunctionTool(query_guia_table),
        FunctionTool(analyze_guia_structure)
    ]
)