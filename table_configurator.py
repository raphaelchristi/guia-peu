"""
Configurador de Tabelas Específicas para o Pipeline MCP
Permite configurar e otimizar o acesso a tabelas específicas
"""
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class TableConfig:
    """Configuração de uma tabela específica"""
    name: str
    alias: str
    description: str
    primary_key: str
    columns: Dict[str, str]  # nome_coluna: tipo_dados
    indexes: List[str]
    common_queries: List[str]
    business_rules: Dict[str, Any]

class TableManager:
    """Gerenciador de configurações de tabelas"""
    
    def __init__(self):
        self.tables = {}
        self.load_default_configs()
    
    def load_default_configs(self):
        """Carrega configurações padrão de tabelas comuns"""
        
        # Exemplo: Tabela de Utilizadores
        self.add_table_config(TableConfig(
            name="users",
            alias="utilizadores",
            description="Tabela de utilizadores do sistema",
            primary_key="id",
            columns={
                "id": "uuid",
                "email": "varchar",
                "name": "varchar", 
                "created_at": "timestamp",
                "updated_at": "timestamp",
                "is_active": "boolean",
                "last_login": "timestamp"
            },
            indexes=["email", "created_at", "is_active"],
            common_queries=[
                "SELECT COUNT(*) FROM users WHERE is_active = true",
                "SELECT * FROM users ORDER BY created_at DESC LIMIT 10",
                "SELECT COUNT(*) as total_users, COUNT(CASE WHEN is_active THEN 1 END) as active_users FROM users"
            ],
            business_rules={
                "max_results_default": 100,
                "sensitive_columns": ["email"],
                "public_columns": ["name", "created_at"],
                "date_filters": ["created_at", "updated_at", "last_login"]
            }
        ))
        
        # Exemplo: Tabela de Produtos
        self.add_table_config(TableConfig(
            name="products",
            alias="produtos",
            description="Catálogo de produtos",
            primary_key="id",
            columns={
                "id": "uuid",
                "name": "varchar",
                "description": "text",
                "price": "decimal",
                "category_id": "uuid",
                "stock_quantity": "integer",
                "is_available": "boolean",
                "created_at": "timestamp"
            },
            indexes=["category_id", "is_available", "price"],
            common_queries=[
                "SELECT * FROM products WHERE is_available = true ORDER BY name",
                "SELECT category_id, COUNT(*) as product_count, AVG(price) as avg_price FROM products GROUP BY category_id",
                "SELECT * FROM products WHERE stock_quantity < 10 AND is_available = true"
            ],
            business_rules={
                "max_results_default": 50,
                "price_format": "currency",
                "stock_alerts": {"low_stock": 10, "out_of_stock": 0}
            }
        ))
        
        # Configuração específica para tabela "guia"
        self.add_table_config(TableConfig(
            name="guia",
            alias="guia",
            description="Tabela principal 'guia' do projeto",
            primary_key="id",  # Será descoberto automaticamente
            columns={},  # Será preenchido após análise
            indexes=[],  # Será descoberto automaticamente
            common_queries=[
                "SELECT COUNT(*) FROM guia",
                "SELECT * FROM guia ORDER BY id DESC LIMIT 10",
                "SELECT * FROM guia LIMIT 5",
                "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'guia'"
            ],
            business_rules={
                "max_results_default": 25,
                "table_priority": "high",
                "auto_analyze": True,
                "cache_duration": 300,
                "sensitive_data_protection": True
            }
        ))
    
    def add_table_config(self, config: TableConfig):
        """Adiciona configuração de tabela"""
        self.tables[config.name] = config
        if config.alias:
            self.tables[config.alias] = config
    
    def get_table_config(self, table_name: str) -> Optional[TableConfig]:
        """Obtém configuração de uma tabela"""
        return self.tables.get(table_name.lower())
    
    def suggest_queries_for_table(self, table_name: str) -> List[str]:
        """Sugere queries comuns para uma tabela"""
        config = self.get_table_config(table_name)
        if not config:
            return [
                f"SELECT COUNT(*) FROM {table_name}",
                f"SELECT * FROM {table_name} LIMIT 10",
                f"DESCRIBE {table_name}"
            ]
        
        suggestions = config.common_queries.copy()
        
        # Adicionar queries baseadas em regras de negócio
        if "date_filters" in config.business_rules:
            for date_col in config.business_rules["date_filters"]:
                suggestions.extend([
                    f"SELECT COUNT(*) FROM {config.name} WHERE {date_col} >= CURRENT_DATE - INTERVAL '7 days'",
                    f"SELECT COUNT(*) FROM {config.name} WHERE {date_col} >= CURRENT_DATE - INTERVAL '30 days'"
                ])
        
        return suggestions
    
    def optimize_query_for_table(self, table_name: str, user_query: str) -> str:
        """Otimiza query para uma tabela específica"""
        config = self.get_table_config(table_name)
        if not config:
            return user_query
        
        optimized = user_query
        
        # Aplicar limite padrão se não especificado
        if "LIMIT" not in optimized.upper() and "SELECT" in optimized.upper():
            max_results = config.business_rules.get("max_results_default", 100)
            optimized += f" LIMIT {max_results}"
        
        # Adicionar índices sugeridos em WHERE clauses
        # (implementação mais complexa seria necessária para análise real de query)
        
        return optimized
    
    def get_table_insights(self, table_name: str) -> Dict[str, Any]:
        """Obtém insights sobre uma tabela"""
        config = self.get_table_config(table_name)
        if not config:
            return {"error": f"Tabela {table_name} não configurada"}
        
        return {
            "name": config.name,
            "alias": config.alias,
            "description": config.description,
            "column_count": len(config.columns),
            "indexed_columns": config.indexes,
            "suggested_queries": self.suggest_queries_for_table(table_name),
            "business_rules": config.business_rules,
            "optimization_tips": [
                f"Use filtros nas colunas indexadas: {', '.join(config.indexes)}",
                f"Limite resultados para melhor performance (padrão: {config.business_rules.get('max_results_default', 100)})",
                "Use agregações para análises de grandes volumes"
            ]
        }

# Instância global
table_manager = TableManager()

def configure_your_table(
    table_name: str,
    description: str,
    columns: Dict[str, str],
    primary_key: str = "id",
    alias: str = None,
    indexes: List[str] = None,
    business_rules: Dict[str, Any] = None
) -> TableConfig:
    """Função helper para configurar sua tabela específica"""
    
    config = TableConfig(
        name=table_name,
        alias=alias or table_name,
        description=description,
        primary_key=primary_key,
        columns=columns,
        indexes=indexes or [primary_key],
        common_queries=[
            f"SELECT COUNT(*) FROM {table_name}",
            f"SELECT * FROM {table_name} ORDER BY {primary_key} DESC LIMIT 10",
            f"SELECT * FROM {table_name} LIMIT 5"
        ],
        business_rules=business_rules or {"max_results_default": 100}
    )
    
    table_manager.add_table_config(config)
    return config

def analyze_table_structure(table_name: str) -> str:
    """Gera prompt para analisar estrutura de uma tabela"""
    return f"""
    Analise a estrutura da tabela '{table_name}' e forneça as seguintes informações:
    
    1. Listar todas as colunas com seus tipos de dados
    2. Identificar a chave primária
    3. Identificar possíveis chaves estrangeiras
    4. Sugerir índices para otimização
    5. Propor queries comuns para esta tabela
    6. Identificar padrões de dados
    
    Use a ferramenta describe_table para obter informações detalhadas.
    """

def generate_table_queries(table_name: str, query_type: str = "exploration") -> List[str]:
    """Gera queries específicas para uma tabela"""
    
    query_templates = {
        "exploration": [
            f"SELECT COUNT(*) as total_records FROM {table_name}",
            f"SELECT * FROM {table_name} LIMIT 5",
            f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table_name}'"
        ],
        "analysis": [
            f"SELECT COUNT(*) as total, COUNT(DISTINCT *) as unique_records FROM {table_name}",
            f"SELECT * FROM {table_name} ORDER BY random() LIMIT 10",
        ],
        "quality": [
            f"SELECT COUNT(*) as total_nulls FROM {table_name} WHERE {table_name}.* IS NULL",
            f"SELECT COUNT(DISTINCT *) as unique_count, COUNT(*) as total_count FROM {table_name}"
        ]
    }
    
    return query_templates.get(query_type, query_templates["exploration"])

# Exemplo de uso para sua tabela específica
def setup_my_table_example():
    """Exemplo de como configurar sua tabela"""
    
    # Substitua pelos dados reais da sua tabela
    my_table = configure_your_table(
        table_name="minha_tabela",
        description="Descrição da minha tabela específica",
        columns={
            "id": "integer",
            "nome": "varchar",
            "email": "varchar", 
            "data_criacao": "timestamp",
            "status": "varchar"
        },
        primary_key="id",
        alias="tabela_principal",
        indexes=["email", "data_criacao", "status"],
        business_rules={
            "max_results_default": 50,
            "sensitive_columns": ["email"],
            "date_filters": ["data_criacao"],
            "status_values": ["ativo", "inativo", "pendente"]
        }
    )
    
    print("✅ Tabela configurada:")
    print(f"   Nome: {my_table.name}")
    print(f"   Colunas: {len(my_table.columns)}")
    print(f"   Índices: {my_table.indexes}")
    
    # Obter insights
    insights = table_manager.get_table_insights("minha_tabela")
    print("\n📊 Insights da tabela:")
    print(json.dumps(insights, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    print("🔧 Configurador de Tabelas - Pipeline MCP")
    print("=" * 50)
    
    # Exemplo de configuração
    setup_my_table_example()
    
    # Mostrar tabelas configuradas
    print(f"\n📋 Tabelas configuradas: {list(table_manager.tables.keys())}")
    
    # Exemplo de análise
    print(f"\n🔍 Queries sugeridas para 'users':")
    for query in table_manager.suggest_queries_for_table("users"):
        print(f"   - {query}")