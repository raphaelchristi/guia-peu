#!/usr/bin/env python3
"""
Servidor MCP Customizado para Supabase
Expõe ferramentas específicas de base de dados através do protocolo MCP
"""
import asyncio
import json
import os
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# MCP Server Imports
from mcp import types as mcp_types
from mcp.server.lowlevel import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio

# Supabase Imports
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions

# Validation
from pydantic import BaseModel, ValidationError

# Logging Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load Environment Variables
load_dotenv()

class SupabaseConfig:
    """Configuração do Supabase"""
    def __init__(self):
        self.url = os.environ.get("SUPABASE_URL")
        self.service_key = os.environ.get("SUPABASE_SERVICE_KEY")
        self.access_token = os.environ.get("SUPABASE_ACCESS_TOKEN")
        
        if not self.url or not self.service_key:
            raise ValueError("SUPABASE_URL e SUPABASE_SERVICE_KEY são obrigatórios")

class QueryParams(BaseModel):
    """Parâmetros para queries SQL"""
    query: str
    params: Optional[List[Any]] = None
    safe_mode: bool = True

class TableQueryParams(BaseModel):
    """Parâmetros para consultas de tabela"""
    table: str
    select: str = "*"
    filters: Optional[Dict[str, Any]] = None
    limit: Optional[int] = None
    offset: Optional[int] = None
    order_by: Optional[str] = None

class SupabaseMCPServer:
    """Servidor MCP para Supabase"""
    
    def __init__(self):
        self.config = SupabaseConfig()
        self.supabase: Client = create_client(
            self.config.url,
            self.config.service_key,
            options=ClientOptions(
                auto_refresh_token=False,
                persist_session=False
            )
        )
        logger.info("Supabase client inicializado")

    async def execute_sql_query(self, params: QueryParams) -> Dict[str, Any]:
        """Executa query SQL com validação de segurança"""
        try:
            # Validação básica de segurança
            if params.safe_mode:
                dangerous_keywords = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE']
                query_upper = params.query.upper()
                
                for keyword in dangerous_keywords:
                    if keyword in query_upper and not query_upper.strip().startswith('SELECT'):
                        raise ValueError(f"Operação perigosa detectada: {keyword}")

            # Executar query usando RPC se necessário
            if params.params:
                result = self.supabase.rpc('execute_query', {
                    'query_text': params.query,
                    'query_params': params.params
                }).execute()
            else:
                # Para queries SELECT simples
                if params.query.strip().upper().startswith('SELECT'):
                    # Tentar executar como query direta
                    result = self.supabase.postgrest.rpc('query', {
                        'query': params.query
                    }).execute()
                else:
                    result = self.supabase.rpc('execute_query', {
                        'query_text': params.query
                    }).execute()

            return {
                "success": True,
                "data": result.data,
                "count": len(result.data) if result.data else 0
            }

        except Exception as e:
            logger.error(f"Erro na execução da query: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": None
            }

    async def query_table(self, params: TableQueryParams) -> Dict[str, Any]:
        """Consulta tabela específica com filtros"""
        try:
            query = self.supabase.table(params.table).select(params.select)
            
            # Aplicar filtros
            if params.filters:
                for key, value in params.filters.items():
                    if isinstance(value, dict) and 'operator' in value:
                        # Filtro avançado: {"operator": "gte", "value": 100}
                        op = value['operator']
                        val = value['value']
                        if op == 'gte':
                            query = query.gte(key, val)
                        elif op == 'lte':
                            query = query.lte(key, val)
                        elif op == 'like':
                            query = query.like(key, val)
                        elif op == 'in':
                            query = query.in_(key, val)
                        else:
                            query = query.eq(key, val)
                    else:
                        # Filtro simples de igualdade
                        query = query.eq(key, value)
            
            # Aplicar ordenação
            if params.order_by:
                if params.order_by.startswith('-'):
                    query = query.order(params.order_by[1:], desc=True)
                else:
                    query = query.order(params.order_by)
            
            # Aplicar paginação
            if params.limit:
                query = query.limit(params.limit)
                if params.offset:
                    query = query.offset(params.offset)

            result = query.execute()

            return {
                "success": True,
                "data": result.data,
                "count": len(result.data) if result.data else 0,
                "table": params.table
            }

        except Exception as e:
            logger.error(f"Erro na consulta da tabela {params.table}: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": None
            }

    async def list_tables(self) -> Dict[str, Any]:
        """Lista todas as tabelas disponíveis"""
        try:
            # Query para listar tabelas do esquema público
            query = """
            SELECT table_name, table_type 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
            """
            
            result = self.supabase.rpc('execute_query', {
                'query_text': query
            }).execute()

            return {
                "success": True,
                "data": result.data,
                "count": len(result.data) if result.data else 0
            }

        except Exception as e:
            logger.error(f"Erro ao listar tabelas: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": None
            }

    async def describe_table(self, table_name: str) -> Dict[str, Any]:
        """Descreve a estrutura de uma tabela"""
        try:
            # Query para obter informações das colunas
            query = """
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default,
                character_maximum_length
            FROM information_schema.columns 
            WHERE table_name = %s AND table_schema = 'public'
            ORDER BY ordinal_position;
            """
            
            result = self.supabase.rpc('execute_query', {
                'query_text': query,
                'query_params': [table_name]
            }).execute()

            return {
                "success": True,
                "data": result.data,
                "table": table_name,
                "count": len(result.data) if result.data else 0
            }

        except Exception as e:
            logger.error(f"Erro ao descrever tabela {table_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": None
            }

# Criar instância do servidor MCP
logger.info("Criando servidor MCP para Supabase...")
app = Server("supabase-mcp-server")
supabase_server = SupabaseMCPServer()

@app.list_tools()
async def list_tools() -> List[mcp_types.Tool]:
    """Lista as ferramentas disponíveis do servidor MCP"""
    logger.info("MCP Server: Recebida solicitação list_tools")
    
    return [
        mcp_types.Tool(
            name="execute_sql",
            description="Executa query SQL na base de dados Supabase com validação de segurança",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Query SQL para executar"
                    },
                    "params": {
                        "type": "array",
                        "description": "Parâmetros para a query (opcional)",
                        "items": {"type": "string"}
                    },
                    "safe_mode": {
                        "type": "boolean",
                        "description": "Ativar validação de segurança (default: true)",
                        "default": True
                    }
                },
                "required": ["query"]
            }
        ),
        mcp_types.Tool(
            name="query_table",
            description="Consulta tabela específica com filtros e paginação",
            inputSchema={
                "type": "object",
                "properties": {
                    "table": {
                        "type": "string",
                        "description": "Nome da tabela"
                    },
                    "select": {
                        "type": "string",
                        "description": "Colunas a seleccionar (default: '*')",
                        "default": "*"
                    },
                    "filters": {
                        "type": "object",
                        "description": "Filtros para aplicar à consulta"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Limite de resultados"
                    },
                    "offset": {
                        "type": "integer",
                        "description": "Offset para paginação"
                    },
                    "order_by": {
                        "type": "string",
                        "description": "Campo para ordenação (use '-' para desc)"
                    }
                },
                "required": ["table"]
            }
        ),
        mcp_types.Tool(
            name="list_tables",
            description="Lista todas as tabelas disponíveis na base de dados",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        mcp_types.Tool(
            name="describe_table",
            description="Descreve a estrutura de uma tabela específica",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Nome da tabela para descrever"
                    }
                },
                "required": ["table_name"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> List[mcp_types.Content]:
    """Executa ferramenta solicitada pelo cliente MCP"""
    logger.info(f"MCP Server: Recebida chamada para ferramenta '{name}' com argumentos: {arguments}")
    
    try:
        if name == "execute_sql":
            params = QueryParams(**arguments)
            result = await supabase_server.execute_sql_query(params)
            
        elif name == "query_table":
            params = TableQueryParams(**arguments)
            result = await supabase_server.query_table(params)
            
        elif name == "list_tables":
            result = await supabase_server.list_tables()
            
        elif name == "describe_table":
            table_name = arguments.get("table_name")
            if not table_name:
                raise ValueError("table_name é obrigatório")
            result = await supabase_server.describe_table(table_name)
            
        else:
            result = {
                "success": False,
                "error": f"Ferramenta '{name}' não implementada"
            }

        # Formatear resposta para MCP
        response_text = json.dumps(result, indent=2, ensure_ascii=False)
        return [mcp_types.TextContent(type="text", text=response_text)]

    except ValidationError as e:
        logger.error(f"Erro de validação para ferramenta '{name}': {e}")
        error_response = {
            "success": False,
            "error": f"Erro de validação: {str(e)}"
        }
        return [mcp_types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
    
    except Exception as e:
        logger.error(f"Erro na execução da ferramenta '{name}': {e}")
        error_response = {
            "success": False,
            "error": f"Erro na execução: {str(e)}"
        }
        return [mcp_types.TextContent(type="text", text=json.dumps(error_response, indent=2))]

async def run_stdio_server():
    """Executa o servidor MCP via stdio"""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        logger.info("MCP Stdio Server: Iniciando handshake com cliente...")
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name=app.name,
                server_version="1.0.0",
                capabilities=app.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )
        logger.info("MCP Stdio Server: Loop de execução terminado")

if __name__ == "__main__":
    logger.info("Iniciando servidor MCP Supabase via stdio...")
    try:
        asyncio.run(run_stdio_server())
    except KeyboardInterrupt:
        logger.info("Servidor MCP Supabase interrompido pelo utilizador")
    except Exception as e:
        logger.error(f"Erro no servidor MCP Supabase: {e}")
    finally:
        logger.info("Processo do servidor MCP Supabase terminado")