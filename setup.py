#!/usr/bin/env python3
"""
Script de Setup para MCP Pipeline Supabase + Google Gemini
Configura automaticamente o ambiente e dependências
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_python_version():
    """Verifica versão do Python"""
    if sys.version_info < (3, 9):
        print("❌ Python 3.9+ é necessário")
        print(f"Versão atual: {sys.version}")
        return False
    print(f"✅ Python {sys.version.split()[0]} OK")
    return True

def check_node_npm():
    """Verifica se Node.js e npm estão instalados"""
    try:
        node_version = subprocess.check_output(['node', '--version'], text=True).strip()
        npm_version = subprocess.check_output(['npm', '--version'], text=True).strip()
        print(f"✅ Node.js {node_version} OK")
        print(f"✅ npm {npm_version} OK")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Node.js e npm são necessários")
        print("Instale em: https://nodejs.org/")
        return False

def install_python_dependencies():
    """Instala dependências Python"""
    print("\n📦 Instalando dependências Python...")
    
    dependencies = [
        "google-adk",
        "python-dotenv",
        "supabase",
        "mcp",
        "pydantic",
        "asyncio-throttle"
    ]
    
    for dep in dependencies:
        try:
            print(f"   Instalando {dep}...")
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", dep
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"   ✅ {dep} instalado")
        except subprocess.CalledProcessError:
            print(f"   ❌ Erro ao instalar {dep}")
            return False
    
    print("✅ Dependências Python instaladas")
    return True

def setup_environment_file():
    """Configura arquivo .env"""
    print("\n🔧 Configurando arquivo .env...")
    
    env_example = Path(".env.example")
    env_file = Path(".env")
    
    if not env_example.exists():
        print("❌ Arquivo .env.example não encontrado")
        return False
        
    if env_file.exists():
        response = input("Arquivo .env já existe. Sobrescrever? (y/N): ")
        if response.lower() != 'y':
            print("⏭️  Mantendo .env existente")
            return True
    
    # Copiar exemplo
    shutil.copy(env_example, env_file)
    
    print("✅ Arquivo .env criado")
    print("⚠️  IMPORTANTE: Configure suas chaves de API no arquivo .env")
    print("   - GEMINI_API_KEY")
    print("   - SUPABASE_URL")
    print("   - SUPABASE_SERVICE_KEY") 
    print("   - SUPABASE_ACCESS_TOKEN")
    
    return True

def create_directories():
    """Cria diretórios necessários"""
    print("\n📁 Criando diretórios...")
    
    directories = [
        "logs",
        "cache", 
        "reports",
        "backups"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"   ✅ {directory}/")
    
    print("✅ Diretórios criados")
    return True

def test_installation():
    """Testa a instalação"""
    print("\n🧪 Testando instalação...")
    
    try:
        # Testar imports
        import google.adk
        import supabase
        import mcp
        print("   ✅ Imports Python OK")
        
        # Testar servidor MCP
        if Path("supabase_mcp_server.py").exists():
            print("   ✅ Servidor MCP encontrado")
        else:
            print("   ❌ Servidor MCP não encontrado")
            return False
            
        # Testar agentes
        if Path("agent.py").exists():
            print("   ✅ Agente principal encontrado")
        else:
            print("   ❌ Agente principal não encontrado")
            return False
            
        print("✅ Instalação testada com sucesso")
        return True
        
    except ImportError as e:
        print(f"   ❌ Erro de import: {e}")
        return False

def show_next_steps():
    """Mostra próximos passos"""
    print("\n🎉 SETUP CONCLUÍDO!")
    print("=" * 50)
    
    print("\n📋 PRÓXIMOS PASSOS:")
    print("\n1. Configure suas chaves de API no arquivo .env:")
    print("   - Obtenha GEMINI_API_KEY em: https://aistudio.google.com/")
    print("   - Configure Supabase em: https://supabase.com/")
    
    print("\n2. Teste a configuração:")
    print("   python agent.py")
    
    print("\n3. Inicie a interface web:")
    print("   adk web")
    
    print("\n4. Acesse no navegador e selecione um agente")
    
    print("\n💡 AGENTES DISPONÍVEIS:")
    print("   - mcp_supabase_pipeline (completo)")
    print("   - supabase_analytics_specialist (análises)")
    print("   - database_explorer (exploração segura)")
    
    print("\n📚 DOCUMENTAÇÃO:")
    print("   - README.md (guia completo)")
    print("   - .env.example (configuração)")
    print("   - logs/ (logs do sistema)")

def main():
    """Função principal do setup"""
    print("🚀 MCP Pipeline Supabase + Google Gemini - Setup")
    print("=" * 60)
    
    # Verificações
    if not check_python_version():
        return 1
        
    if not check_node_npm():
        return 1
    
    # Instalação
    if not install_python_dependencies():
        return 1
        
    if not setup_environment_file():
        return 1
        
    if not create_directories():
        return 1
        
    if not test_installation():
        return 1
    
    # Finalização
    show_next_steps()
    return 0

if __name__ == "__main__":
    sys.exit(main())