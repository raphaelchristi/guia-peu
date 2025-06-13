#!/usr/bin/env python3
"""
Teste do servidor MCP corrigido
Valida se os campos obrigatórios estão presentes
"""
import subprocess
import json
import sys
import time

def test_mcp_server():
    """Testar servidor MCP corrigido"""
    print("🧪 TESTANDO SERVIDOR MCP CORRIGIDO")
    print("=" * 50)
    
    # Iniciar servidor
    print("🚀 Iniciando servidor...")
    process = subprocess.Popen(
        ["python3", "fixed_mcp_server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Aguardar inicialização
    time.sleep(1)
    
    try:
        # 1. Testar Initialize
        print("\n1️⃣ Testando Initialize...")
        initialize_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
                "capabilities": {}
            }
        }
        
        process.stdin.write(json.dumps(initialize_request) + "\n")
        process.stdin.flush()
        
        response_line = process.stdout.readline()
        response = json.loads(response_line)
        
        # Verificar campos obrigatórios
        result = response.get("result", {})
        required_fields = ["protocolVersion", "capabilities", "serverInfo"]
        
        print("📋 Verificando campos obrigatórios:")
        all_present = True
        for field in required_fields:
            if field in result:
                print(f"   ✅ {field}: {result[field]}")
            else:
                print(f"   ❌ {field}: AUSENTE")
                all_present = False
        
        if all_present:
            print("✅ Initialize: SUCESSO - Todos os campos obrigatórios presentes")
        else:
            print("❌ Initialize: FALHOU - Campos obrigatórios ausentes")
            return False
        
        # 2. Testar List Tools
        print("\n2️⃣ Testando List Tools...")
        list_tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        process.stdin.write(json.dumps(list_tools_request) + "\n")
        process.stdin.flush()
        
        tools_response_line = process.stdout.readline()
        tools_response = json.loads(tools_response_line)
        tools = tools_response.get('result', {}).get('tools', [])
        
        print(f"🔧 Ferramentas disponíveis: {len(tools)}")
        for tool in tools:
            print(f"   • {tool['name']}: {tool['description']}")
        
        if len(tools) > 0:
            print("✅ List Tools: SUCESSO")
        else:
            print("❌ List Tools: FALHOU - Nenhuma ferramenta encontrada")
            return False
        
        # 3. Testar Call Tool
        print("\n3️⃣ Testando Call Tool...")
        call_tool_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "query_guia",
                "arguments": {
                    "operation": "count"
                }
            }
        }
        
        process.stdin.write(json.dumps(call_tool_request) + "\n")
        process.stdin.flush()
        
        call_response_line = process.stdout.readline()
        call_response = json.loads(call_response_line)
        
        if "result" in call_response:
            content = call_response["result"].get("content", [])
            if content:
                data = json.loads(content[0]["text"])
                print(f"📊 Resultado: {data.get('message', 'Sem mensagem')}")
                print("✅ Call Tool: SUCESSO")
            else:
                print("❌ Call Tool: FALHOU - Sem conteúdo na resposta")
                return False
        else:
            print(f"❌ Call Tool: FALHOU - {call_response.get('error', 'Erro desconhecido')}")
            return False
        
        print(f"\n{'='*50}")
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("✅ Servidor MCP está funcionando corretamente")
        print("✅ Protocolo MCP implementado adequadamente")
        print("✅ Pronto para integração com ADK")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False
    
    finally:
        process.terminate()
        
        # Aguardar stderr
        time.sleep(0.5)
        stderr_output = process.stderr.read()
        if stderr_output:
            print(f"\n📋 Log do servidor:")
            print(stderr_output)

if __name__ == "__main__":
    success = test_mcp_server()
    sys.exit(0 if success else 1)