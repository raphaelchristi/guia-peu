#!/usr/bin/env python3
"""
Servidor MCP Simplificado para Supabase
Funciona com a biblioteca MCP disponível no sistema
"""
import os
import json
import asyncio
import logging
from typing import Dict, Any, List
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Carregar configuração
load_dotenv()

class SimpleSupabaseServer:
    """Servidor simplificado para Supabase"""
    
    def __init__(self):
        from supabase import create_client
        
        self.supabase = create_client(
            os.environ.get("SUPABASE_URL"),
            os.environ.get("SUPABASE_SERVICE_KEY")
        )
        logger.info("Cliente Supabase inicializado")
    
    async def execute_sql(self, query: str, params: List = None) -> Dict[str, Any]:
        """Executa query SQL"""
        try:
            logger.info(f"Executando SQL: {query[:100]}...")
            
            # Para queries simples SELECT, usar o cliente diretamente
            if query.strip().upper().startswith('SELECT'):
                # Executar query SQL bruta (se suportado)
                try:
                    result = self.supabase.postgrest.rpc('query', {'query_text': query}).execute()
                    return {
                        "success": True,
                        "data": result.data,
                        "count": len(result.data) if result.data else 0
                    }
                except:
                    # Fallback para queries específicas conhecidas
                    if 'FROM guia' in query.upper():
                        if 'COUNT(*)' in query.upper():
                            result = self.supabase.table('guia').select('*', count='exact').execute()
                            return {
                                "success": True,
                                "data": [{"count": result.count}],
                                "count": 1
                            }
                        else:
                            # Parse LIMIT se presente
                            limit = 10
                            if 'LIMIT' in query.upper():
                                import re
                                limit_match = re.search(r'LIMIT\s+(\d+)', query.upper())
                                if limit_match:
                                    limit = int(limit_match.group(1))
                            
                            result = self.supabase.table('guia').select('*').limit(limit).execute()
                            return {
                                "success": True,
                                "data": result.data,
                                "count": len(result.data) if result.data else 0
                            }
            
            return {
                "success": False,
                "error": "Query SQL não suportada por este servidor simplificado",
                "suggestion": "Use query_table para operações estruturadas"
            }
            
        except Exception as e:
            logger.error(f"Erro SQL: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def query_table(self, table: str, select: str = "*", filters: Dict = None, 
                         limit: int = None, order_by: str = None) -> Dict[str, Any]:
        """Consulta tabela específica"""
        try:
            logger.info(f"Consultando tabela: {table}")
            
            query = self.supabase.table(table).select(select)
            
            # Aplicar filtros
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            
            # Aplicar ordenação
            if order_by:
                if order_by.startswith('-'):
                    query = query.order(order_by[1:], desc=True)
                else:
                    query = query.order(order_by)
            
            # Aplicar limite
            if limit:
                query = query.limit(limit)
            
            result = query.execute()
            
            return {
                "success": True,
                "data": result.data,
                "count": len(result.data) if result.data else 0,
                "table": table
            }
            
        except Exception as e:
            logger.error(f"Erro na consulta: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def list_tables(self) -> Dict[str, Any]:
        """Lista tabelas disponíveis"""
        try:
            # Query para listar tabelas
            query = """
            SELECT table_name, table_type 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
            """
            
            # Como não temos RPC, vamos usar uma abordagem alternativa
            # Tentar acessar algumas tabelas conhecidas
            known_tables = ['guia']  # Sabemos que esta existe
            available_tables = []
            
            for table in known_tables:
                try:
                    result = self.supabase.table(table).select('*').limit(1).execute()
                    available_tables.append({
                        'table_name': table,
                        'table_type': 'BASE TABLE',
                        'record_count_sample': len(result.data)
                    })
                except:
                    pass
            
            return {
                "success": True,
                "data": available_tables,
                "count": len(available_tables)
            }
            
        except Exception as e:
            logger.error(f"Erro ao listar tabelas: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def describe_table(self, table_name: str) -> Dict[str, Any]:
        """Descreve estrutura de uma tabela"""
        try:
            logger.info(f"Descrevendo tabela: {table_name}")
            
            # Obter amostra de dados para inferir estrutura
            result = self.supabase.table(table_name).select('*').limit(1).execute()
            
            if not result.data:
                return {
                    "success": True,
                    "data": [],
                    "message": f"Tabela '{table_name}' está vazia",
                    "table": table_name
                }
            
            # Analisar estrutura baseada no primeiro registro
            sample_record = result.data[0]
            columns_info = []
            
            for column_name, value in sample_record.items():
                # Inferir tipo baseado no valor
                if value is None:
                    data_type = "unknown (null)"
                elif isinstance(value, bool):
                    data_type = "boolean"
                elif isinstance(value, int):
                    data_type = "integer"
                elif isinstance(value, float):
                    data_type = "numeric"
                elif isinstance(value, str):
                    if len(value) > 255:
                        data_type = "text"
                    else:
                        data_type = "varchar"
                else:
                    data_type = f"unknown ({type(value).__name__})"
                
                columns_info.append({
                    "column_name": column_name,
                    "data_type": data_type,
                    "sample_value": str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                })
            
            return {
                "success": True,
                "data": columns_info,
                "table": table_name,
                "count": len(columns_info),
                "note": "Estrutura inferida baseada em dados de amostra"
            }
            
        except Exception as e:
            logger.error(f"Erro ao descrever tabela: {e}")
            return {
                "success": False,
                "error": str(e)
            }

async def handle_stdio():
    """Simula protocolo MCP via stdio"""
    server = SimpleSupabaseServer()
    
    logger.info("Servidor MCP simplificado iniciado")
    
    try:
        while True:
            # Ler linha de entrada
            try:
                line = input()
                if not line.strip():
                    continue
                    
                # Parse comando JSON
                try:
                    command = json.loads(line)
                except json.JSONDecodeError:
                    # Comando simples de texto
                    command = {"method": "query_table", "params": {"table": "guia", "limit": 1}}
                
                method = command.get("method", "query_table")
                params = command.get("params", {})
                
                # Executar comando
                if method == "query_table":
                    result = await server.query_table(**params)
                elif method == "execute_sql":
                    result = await server.execute_sql(**params)
                elif method == "list_tables":
                    result = await server.list_tables()
                elif method == "describe_table":
                    result = await server.describe_table(**params)
                else:
                    result = {"success": False, "error": f"Método '{method}' não suportado"}
                
                # Responder
                response = {
                    "jsonrpc": "2.0",
                    "id": command.get("id", 1),
                    "result": result
                }
                
                print(json.dumps(response))
                
            except EOFError:
                break
            except KeyboardInterrupt:
                break
            except Exception as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": command.get("id", 1) if 'command' in locals() else 1,
                    "error": {"code": -1, "message": str(e)}
                }
                print(json.dumps(error_response))
                
    except Exception as e:
        logger.error(f"Erro no servidor: {e}")

async def test_server():
    """Testa o servidor simplificado"""
    server = SimpleSupabaseServer()
    
    print("🧪 TESTE DO SERVIDOR MCP SIMPLIFICADO")
    print("=" * 50)
    
    # Teste 1: Listar tabelas
    print("\n1️⃣ Testando list_tables...")
    result = await server.list_tables()
    print(f"✅ Resultado: {result}")
    
    # Teste 2: Descrever tabela guia
    print("\n2️⃣ Testando describe_table para 'guia'...")
    result = await server.describe_table("guia")
    print(f"✅ Resultado: {json.dumps(result, indent=2, ensure_ascii=False)[:500]}...")
    
    # Teste 3: Consultar tabela guia
    print("\n3️⃣ Testando query_table para 'guia'...")
    result = await server.query_table("guia", limit=1)
    print(f"✅ Resultado: {result['success']}, {result['count']} registos")
    
    # Teste 4: Executar SQL simples
    print("\n4️⃣ Testando execute_sql...")
    result = await server.execute_sql("SELECT COUNT(*) FROM guia")
    print(f"✅ Resultado: {result}")
    
    print("\n🎉 Todos os testes concluídos!")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Modo de teste
        asyncio.run(test_server())
    else:
        # Modo servidor
        asyncio.run(handle_stdio())