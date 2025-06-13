#!/usr/bin/env python3
"""
Servidor MCP Corrigido para Supabase
Implementa protocolo MCP correto com campos obrigatórios
"""
import json
import sys
import os
import asyncio
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def handle_initialize(request_id):
    """Handler correto para initialize - FIX PRINCIPAL"""
    response = {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "supabase-mcp-server",
                "version": "1.0.0"
            }
        }
    }
    return response

def handle_list_tools(request_id):
    """Handler para list_tools"""
    response = {
        "jsonrpc": "2.0", 
        "id": request_id,
        "result": {
            "tools": [
                {
                    "name": "query_guia",
                    "description": "Consulta a tabela guia com filtros",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "operation": {
                                "type": "string",
                                "description": "Tipo de operação: count, samples, structure, search",
                                "enum": ["count", "samples", "structure", "search"]
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Limite de resultados",
                                "default": 10
                            },
                            "filters": {
                                "type": "object",
                                "description": "Filtros para aplicar"
                            }
                        },
                        "required": ["operation"]
                    }
                },
                {
                    "name": "analyze_bairros",
                    "description": "Analisa distribuição por bairros na tabela guia",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "limit": {
                                "type": "integer",
                                "description": "Número de bairros no ranking",
                                "default": 10
                            }
                        }
                    }
                }
            ]
        }
    }
    return response

def handle_call_tool(request_id, tool_name, arguments):
    """Handler para call_tool"""
    try:
        # Conectar ao Supabase
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        
        if not supabase_url or not supabase_key:
            raise Exception("Credenciais Supabase não configuradas")
        
        supabase = create_client(supabase_url, supabase_key)
        
        if tool_name == "query_guia":
            operation = arguments.get("operation", "count")
            limit = arguments.get("limit", 10)
            filters = arguments.get("filters", {})
            
            if operation == "count":
                result = supabase.table('guia').select('*', count='exact').execute()
                data = {
                    "operation": "count",
                    "total_registros": result.count,
                    "message": f"Total de {result.count:,} registros na tabela guia"
                }
                
            elif operation == "samples":
                query = supabase.table('guia').select('*').limit(limit)
                if filters:
                    for key, value in filters.items():
                        query = query.ilike(key, f"%{value}%")
                result = query.execute()
                data = {
                    "operation": "samples",
                    "data": result.data,
                    "count": len(result.data)
                }
                
            elif operation == "structure":
                result = supabase.table('guia').select('*').limit(1).execute()
                if result.data:
                    sample = result.data[0]
                    structure = []
                    for column, value in sample.items():
                        structure.append({
                            "column": column,
                            "type": type(value).__name__,
                            "sample": str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                        })
                    data = {
                        "operation": "structure",
                        "total_columns": len(structure),
                        "structure": structure
                    }
                else:
                    data = {"operation": "structure", "error": "Tabela vazia"}
                    
            elif operation == "search":
                query = supabase.table('guia').select('*').limit(limit)
                if filters:
                    for key, value in filters.items():
                        query = query.ilike(key, f"%{value}%")
                result = query.execute()
                data = {
                    "operation": "search",
                    "filters": filters,
                    "data": result.data,
                    "count": len(result.data)
                }
            else:
                data = {"error": f"Operação '{operation}' não suportada"}
                
        elif tool_name == "analyze_bairros":
            limit = arguments.get("limit", 10)
            result = supabase.table('guia').select('Bairro').execute()
            
            bairros = {}
            for item in result.data:
                bairro = item.get("Bairro", "").strip()
                if bairro:
                    bairros[bairro] = bairros.get(bairro, 0) + 1
            
            top_bairros = sorted(bairros.items(), key=lambda x: x[1], reverse=True)[:limit]
            
            data = {
                "operation": "analyze_bairros",
                "total_bairros_unicos": len(bairros),
                "top_bairros": [{"bairro": b, "quantidade": q} for b, q in top_bairros]
            }
        else:
            raise Exception(f"Ferramenta '{tool_name}' não encontrada")
        
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(data, indent=2, ensure_ascii=False)
                    }
                ]
            }
        }
            
    except Exception as e:
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32000,
                "message": str(e)
            }
        }
    
    return response

def main():
    """Loop principal do servidor MCP"""
    print("🚀 Servidor MCP Corrigido iniciado", file=sys.stderr)
    
    try:
        while True:
            # Ler request do stdin
            line = sys.stdin.readline()
            if not line:
                break
            
            try:
                request = json.loads(line.strip())
            except json.JSONDecodeError:
                continue
            
            # Processar request
            method = request.get("method")
            request_id = request.get("id")
            params = request.get("params", {})
            
            response = None
            
            if method == "initialize":
                response = handle_initialize(request_id)
                print(f"✅ Initialize processado", file=sys.stderr)
                
            elif method == "initialized":
                # Notification - não precisa resposta
                print(f"✅ Initialized notification recebida", file=sys.stderr)
                continue
                
            elif method == "tools/list":
                response = handle_list_tools(request_id)
                print(f"✅ Tools list processado", file=sys.stderr)
                
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                response = handle_call_tool(request_id, tool_name, arguments)
                print(f"✅ Tool call '{tool_name}' processado", file=sys.stderr)
                
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Método '{method}' não encontrado"
                    }
                }
            
            # Enviar response
            if response:
                print(json.dumps(response), flush=True)
                
    except KeyboardInterrupt:
        print("🛑 Servidor interrompido", file=sys.stderr)
    except Exception as e:
        print(f"❌ Erro no servidor: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()