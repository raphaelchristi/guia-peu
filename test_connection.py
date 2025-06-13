#!/usr/bin/env python3
"""
Script de teste de conexão com Supabase
Valida se as credenciais e URL estão corretas
"""
import os
import sys
import asyncio
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

async def test_supabase_connection():
    """Testa conexão com Supabase"""
    print("🔍 TESTE DE CONEXÃO SUPABASE")
    print("=" * 40)
    
    # Verificar variáveis de ambiente
    url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_KEY")
    access_token = os.environ.get("SUPABASE_ACCESS_TOKEN")
    
    print(f"URL: {url}")
    print(f"Service Key: {'✅ Configurada' if service_key else '❌ Não configurada'}")
    print(f"Access Token: {'✅ Configurada' if access_token else '❌ Não configurada'}")
    
    if not all([url, service_key, access_token]):
        print("❌ Configuração incompleta!")
        return False
    
    # Testar conexão com supabase-py
    try:
        from supabase import create_client
        
        print("\n🔗 Testando conexão...")
        client = create_client(url, service_key)
        
        # Testar conexão básica
        result = client.table("guia").select("*").limit(1).execute()
        
        print("✅ Conexão com Supabase OK!")
        print(f"📊 Teste na tabela 'guia': {len(result.data)} registro(s) encontrado(s)")
        
        if result.data:
            print("📝 Exemplo de estrutura:")
            first_record = result.data[0]
            for key, value in first_record.items():
                value_preview = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                print(f"   {key}: {value_preview}")
        
        return True
        
    except ImportError:
        print("❌ Biblioteca supabase não instalada")
        print("Execute: pip install supabase")
        return False
        
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        
        # Diagnóstico detalhado
        if "Name or service not known" in str(e):
            print("\n🔍 DIAGNÓSTICO:")
            print("- Erro de DNS/rede detectado")
            print("- Verifique se a URL está correta")
            print("- Teste conectividade de rede")
            
        elif "Invalid API key" in str(e) or "unauthorized" in str(e).lower():
            print("\n🔍 DIAGNÓSTICO:")
            print("- Erro de autenticação detectado")
            print("- Verifique se as chaves estão corretas")
            print("- Confirme se o projeto está ativo")
            
        elif "table" in str(e).lower() and "does not exist" in str(e).lower():
            print("\n🔍 DIAGNÓSTICO:")
            print("- Tabela 'guia' não encontrada")
            print("- Verifique se a tabela existe no projeto")
            print("- Confirme permissões de acesso")
            
        return False

async def test_mcp_server():
    """Testa o servidor MCP"""
    print("\n🔧 TESTE DO SERVIDOR MCP")
    print("=" * 40)
    
    try:
        # Testar se o script do servidor existe
        server_path = "supabase_mcp_server.py"
        if os.path.exists(server_path):
            print(f"✅ Servidor MCP encontrado: {server_path}")
        else:
            print(f"❌ Servidor MCP não encontrado: {server_path}")
            return False
            
        # Testar importações necessárias
        try:
            from mcp import types as mcp_types
            from mcp.server.lowlevel import Server
            print("✅ Bibliotecas MCP OK")
        except ImportError as e:
            print(f"❌ Erro de import MCP: {e}")
            print("Execute: pip install mcp")
            return False
            
        print("✅ Servidor MCP configurado corretamente")
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste MCP: {e}")
        return False

async def test_network_connectivity():
    """Testa conectividade de rede"""
    print("\n🌐 TESTE DE CONECTIVIDADE")
    print("=" * 40)
    
    import socket
    import urllib.parse
    
    url = os.environ.get("SUPABASE_URL", "")
    if not url:
        print("❌ URL não configurada")
        return False
        
    try:
        # Extrair hostname da URL
        parsed = urllib.parse.urlparse(url)
        hostname = parsed.hostname
        port = parsed.port or 443
        
        print(f"🔍 Testando: {hostname}:{port}")
        
        # Teste de DNS
        try:
            ip = socket.gethostbyname(hostname)
            print(f"✅ DNS OK: {hostname} → {ip}")
        except socket.gaierror:
            print(f"❌ Erro de DNS: {hostname} não resolvido")
            return False
            
        # Teste de conectividade TCP
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((hostname, port))
            sock.close()
            
            if result == 0:
                print(f"✅ Conectividade TCP OK: {hostname}:{port}")
                return True
            else:
                print(f"❌ Falha na conectividade TCP: {hostname}:{port}")
                return False
                
        except Exception as e:
            print(f"❌ Erro no teste TCP: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste de rede: {e}")
        return False

async def main():
    """Função principal de teste"""
    print("🚀 DIAGNÓSTICO COMPLETO DO SISTEMA")
    print("=" * 50)
    
    # Executar todos os testes
    tests = [
        ("Conectividade de Rede", test_network_connectivity),
        ("Conexão Supabase", test_supabase_connection),
        ("Servidor MCP", test_mcp_server),
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        results[test_name] = await test_func()
    
    # Resumo final
    print(f"\n{'='*20} RESUMO FINAL {'='*20}")
    all_passed = True
    
    for test_name, passed in results.items():
        status = "✅ PASSOU" if passed else "❌ FALHOU"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print(f"\n🎉 TODOS OS TESTES PASSARAM!")
        print("O sistema está pronto para uso.")
        print("\n💡 Próximos passos:")
        print("1. Execute: adk web")
        print("2. Acesse a interface web")
        print("3. Selecione o agente 'tabela_guia_specialist'")
        print("4. Pergunte: 'Qual é a estrutura da tabela guia?'")
    else:
        print(f"\n⚠️ ALGUNS TESTES FALHARAM")
        print("Revise os erros acima e corrija antes de continuar.")
    
    return all_passed

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n👋 Teste interrompido pelo utilizador")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        sys.exit(1)