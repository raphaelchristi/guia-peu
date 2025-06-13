#!/usr/bin/env python3
"""
Analisador Direto da Tabela Guia
Conecta diretamente ao Supabase sem MCP
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def main():
    print("🏠 ANALISADOR DA TABELA GUIA")
    print("=" * 40)
    
    try:
        # Conectar ao Supabase
        supabase = create_client(
            os.environ.get("SUPABASE_URL"),
            os.environ.get("SUPABASE_SERVICE_KEY")
        )
        print("✅ Conectado ao Supabase")
        
        # Analisar estrutura
        print("\n📋 ESTRUTURA DA TABELA:")
        result = supabase.table("guia").select("*").limit(1).execute()
        
        if result.data:
            sample = result.data[0]
            print(f"📊 Total de colunas: {len(sample)}")
            print("\n🔍 Principais colunas:")
            for i, (column, value) in enumerate(sample.items()):
                if i < 10:  # Mostrar apenas primeiras 10
                    valor_exemplo = str(value)[:30] + "..." if len(str(value)) > 30 else str(value)
                    print(f"   • {column}: {valor_exemplo}")
        
        # Contar registros
        print("\n📊 VOLUME DE DADOS:")
        count_result = supabase.table("guia").select("*", count="exact").execute()
        print(f"📈 Total de registros: {count_result.count:,}")
        
        # Análise de bairros
        print("\n🏘️ ANÁLISE POR BAIRROS:")
        bairros_result = supabase.table("guia").select("Bairro").execute()
        
        if bairros_result.data:
            bairros = {}
            for item in bairros_result.data:
                bairro = item.get("Bairro", "").strip()
                if bairro:
                    bairros[bairro] = bairros.get(bairro, 0) + 1
            
            print(f"🏙️ Total de bairros únicos: {len(bairros)}")
            top_bairros = sorted(bairros.items(), key=lambda x: x[1], reverse=True)[:5]
            
            print("\n🔝 Top 5 bairros:")
            for bairro, quantidade in top_bairros:
                print(f"   • {bairro}: {quantidade} imóveis")
        
        print("\n" + "="*40)
        print("✅ Análise concluída!")
        print("\n💡 Sua tabela 'guia' contém dados imobiliários ricos!")
        print("Agora você pode usar o sistema MCP para consultas avançadas.")
        
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    main()