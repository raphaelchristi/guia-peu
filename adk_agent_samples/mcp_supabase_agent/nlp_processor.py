"""
Processador de Linguagem Natural para Consultas de Base de Dados
Sistema avançado que converte perguntas em português para operações SQL
"""
import re
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class QueryType(Enum):
    """Tipos de queries suportadas"""
    LIST_TABLES = "list_tables"
    DESCRIBE_TABLE = "describe_table"
    SELECT_DATA = "select_data"
    COUNT_RECORDS = "count_records"
    AGGREGATE = "aggregate"
    FILTER_DATA = "filter_data"
    RECENT_DATA = "recent_data"
    ANALYTICS = "analytics"

@dataclass
class QueryIntent:
    """Representação da intenção da query"""
    query_type: QueryType
    table_name: Optional[str] = None
    columns: List[str] = None
    filters: Dict[str, any] = None
    aggregation: Optional[str] = None
    limit: Optional[int] = None
    time_filter: Optional[str] = None
    confidence: float = 0.0

class NLPQueryProcessor:
    """Processador de linguagem natural para queries de base de dados"""
    
    def __init__(self):
        self.patterns = self._initialize_patterns()
        self.table_keywords = {
            'utilizadores': 'users',
            'usuarios': 'users',
            'clientes': 'customers',
            'produtos': 'products',
            'vendas': 'sales',
            'encomendas': 'orders',
            'pedidos': 'orders',
            'pagamentos': 'payments',
            'transacoes': 'transactions',
            'transações': 'transactions',
            'categorias': 'categories',
            'avaliacoes': 'reviews',
            'avaliações': 'reviews'
        }
        
    def _initialize_patterns(self) -> Dict[QueryType, List[str]]:
        """Inicializa padrões de reconhecimento de intenções"""
        return {
            QueryType.LIST_TABLES: [
                r'.*(?:lista|mostra|que).*tabelas?.*',
                r'.*que.*tabelas?.*(?:existem|há|tem).*',
                r'.*quais.*tabelas?.*',
                r'.*todas.*tabelas?.*'
            ],
            QueryType.DESCRIBE_TABLE: [
                r'.*(?:estrutura|esquema|colunas?).*(?:da|de).*tabela.*(\w+).*',
                r'.*descreve?.*tabela.*(\w+).*',
                r'.*(?:campos|atributos).*tabela.*(\w+).*',
                r'.*como.*(?:é|está).*tabela.*(\w+).*'
            ],
            QueryType.COUNT_RECORDS: [
                r'.*quantos?.*(?:registos?|linhas?|entradas?).*',
                r'.*(?:número|total).*(?:de|dos?).*(?:registos?|linhas?).*',
                r'.*conta.*(?:registos?|linhas?).*',
                r'.*(?:há|existem).*quantos?.*'
            ],
            QueryType.SELECT_DATA: [
                r'.*(?:mostra|lista|busca).*(?:dados?|registos?|informações?).*',
                r'.*(?:selecciona|seleciona).*(?:de|da|dos?).*',
                r'.*(?:primeiros?|últimos?).*(\d+).*(?:registos?|linhas?).*',
                r'.*(?:todos?|todas?).*(?:os?|as?).*(?:dados?|registos?).*'
            ],
            QueryType.AGGREGATE: [
                r'.*(?:total|soma|média|máximo|mínimo).*',
                r'.*(?:sum|avg|max|min|count).*',
                r'.*(?:maior|menor|mais alto|mais baixo).*',
                r'.*(?:média|mediana).*'
            ],
            QueryType.RECENT_DATA: [
                r'.*(?:últimos?|recentes?).*(?:dias?|semanas?|meses?).*',
                r'.*(?:hoje|ontem|esta semana|este mês).*',
                r'.*(?:desde|a partir de).*',
                r'.*(?:criados?|adicionados?).*(?:recentemente|hoje|ontem).*'
            ],
            QueryType.FILTER_DATA: [
                r'.*(?:onde|com|que).*(?:=|igual|maior|menor).*',
                r'.*(?:filtrar|filtro).*(?:por|onde).*',
                r'.*(?:apenas|só|somente).*(?:os?|as?).*que.*',
                r'.*(?:contém|inclui|tem).*'
            ]
        }

    def extract_table_name(self, text: str) -> Optional[str]:
        """Extrai nome da tabela do texto"""
        text_lower = text.lower()
        
        # Procurar por nomes de tabela explícitos
        table_patterns = [
            r'(?:tabela|table)\s+[\'"]?(\w+)[\'"]?',
            r'(?:da|de|dos?|nas?)\s+(?:tabela\s+)?[\'"]?(\w+)[\'"]?',
            r'(?:em|na|no)\s+[\'"]?(\w+)[\'"]?'
        ]
        
        for pattern in table_patterns:
            match = re.search(pattern, text_lower)
            if match:
                table_candidate = match.group(1)
                # Verificar se é um nome de tabela válido
                if len(table_candidate) > 2 and table_candidate.isalnum():
                    return self.table_keywords.get(table_candidate, table_candidate)
        
        # Procurar por palavras-chave de tabela
        for keyword, table_name in self.table_keywords.items():
            if keyword in text_lower:
                return table_name
                
        return None

    def extract_number(self, text: str) -> Optional[int]:
        """Extrai números do texto (para LIMIT, etc.)"""
        numbers = re.findall(r'\d+', text)
        if numbers:
            return int(numbers[0])
        return None

    def extract_time_filter(self, text: str) -> Optional[str]:
        """Extrai filtros temporais do texto"""
        text_lower = text.lower()
        
        time_patterns = {
            r'(?:hoje|today)': "DATE(created_at) = CURRENT_DATE",
            r'(?:ontem|yesterday)': "DATE(created_at) = CURRENT_DATE - INTERVAL '1 day'",
            r'(?:esta semana|this week)': "created_at >= DATE_TRUNC('week', CURRENT_DATE)",
            r'(?:este mês|this month)': "created_at >= DATE_TRUNC('month', CURRENT_DATE)",
            r'(?:últimos?|last)\s+(\d+)\s+(?:dias?|days?)': "created_at >= CURRENT_DATE - INTERVAL '{} days'",
            r'(?:últimas?|last)\s+(\d+)\s+(?:semanas?|weeks?)': "created_at >= CURRENT_DATE - INTERVAL '{} weeks'",
            r'(?:últimos?|last)\s+(\d+)\s+(?:meses?|months?)': "created_at >= CURRENT_DATE - INTERVAL '{} months'"
        }
        
        for pattern, sql_filter in time_patterns.items():
            match = re.search(pattern, text_lower)
            if match:
                if '{}' in sql_filter:
                    number = match.group(1)
                    return sql_filter.format(number)
                return sql_filter
                
        return None

    def extract_aggregation(self, text: str) -> Optional[str]:
        """Extrai tipo de agregação do texto"""
        text_lower = text.lower()
        
        agg_patterns = {
            r'(?:total|soma|sum)': 'SUM',
            r'(?:média|average|avg)': 'AVG',
            r'(?:máximo|maximum|max|maior)': 'MAX',
            r'(?:mínimo|minimum|min|menor)': 'MIN',
            r'(?:conta|count|número|quantos?)': 'COUNT'
        }
        
        for pattern, agg_type in agg_patterns.items():
            if re.search(pattern, text_lower):
                return agg_type
                
        return None

    def classify_query(self, text: str) -> QueryIntent:
        """Classifica a intenção da query baseada no texto"""
        text_lower = text.lower()
        best_match = None
        highest_confidence = 0.0
        
        for query_type, patterns in self.patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    # Calcular confiança baseada na especificidade do padrão
                    confidence = len(pattern) / 100.0  # Padrões mais específicos = maior confiança
                    if confidence > highest_confidence:
                        highest_confidence = confidence
                        best_match = query_type
        
        if not best_match:
            # Fallback para SELECT_DATA se não conseguir classificar
            best_match = QueryType.SELECT_DATA
            highest_confidence = 0.3
            
        return QueryIntent(
            query_type=best_match,
            confidence=highest_confidence
        )

    def process_query(self, text: str) -> QueryIntent:
        """Processa uma query em linguagem natural"""
        # Classificar tipo de query
        intent = self.classify_query(text)
        
        # Extrair componentes adicionais
        intent.table_name = self.extract_table_name(text)
        intent.limit = self.extract_number(text)
        intent.time_filter = self.extract_time_filter(text)
        intent.aggregation = self.extract_aggregation(text)
        
        # Extrair filtros específicos baseados no tipo de query
        if intent.query_type == QueryType.FILTER_DATA:
            intent.filters = self._extract_filters(text)
            
        return intent

    def _extract_filters(self, text: str) -> Dict[str, any]:
        """Extrai filtros específicos do texto"""
        filters = {}
        text_lower = text.lower()
        
        # Padrões comuns de filtro
        filter_patterns = [
            r'(?:nome|name)\s*(?:=|igual|é)\s*[\'"]?(\w+)[\'"]?',
            r'(?:idade|age)\s*(?:>|maior|acima)\s*(\d+)',
            r'(?:status|estado)\s*(?:=|igual|é)\s*[\'"]?(\w+)[\'"]?',
            r'(?:ativo|active)\s*(?:=|igual|é)\s*(true|false|sim|não)',
        ]
        
        for pattern in filter_patterns:
            match = re.search(pattern, text_lower)
            if match:
                # Extrair nome do campo e valor
                field_value = match.groups()
                if len(field_value) >= 2:
                    field, value = field_value[0], field_value[1]
                    filters[field] = value
                    
        return filters

    def generate_mcp_call(self, intent: QueryIntent) -> Dict[str, any]:
        """Gera chamada MCP baseada na intenção"""
        if intent.query_type == QueryType.LIST_TABLES:
            return {
                "tool": "list_tables",
                "arguments": {}
            }
            
        elif intent.query_type == QueryType.DESCRIBE_TABLE:
            if not intent.table_name:
                raise ValueError("Nome da tabela é obrigatório para descrever estrutura")
            return {
                "tool": "describe_table",
                "arguments": {"table_name": intent.table_name}
            }
            
        elif intent.query_type in [QueryType.SELECT_DATA, QueryType.COUNT_RECORDS]:
            if not intent.table_name:
                raise ValueError("Nome da tabela é obrigatório para consultar dados")
                
            args = {"table": intent.table_name}
            
            if intent.query_type == QueryType.COUNT_RECORDS:
                args["select"] = "COUNT(*) as total"
            elif intent.columns:
                args["select"] = ", ".join(intent.columns)
                
            if intent.limit:
                args["limit"] = intent.limit
                
            if intent.filters:
                args["filters"] = intent.filters
                
            return {
                "tool": "query_table",
                "arguments": args
            }
            
        elif intent.query_type == QueryType.AGGREGATE:
            if not intent.table_name or not intent.aggregation:
                raise ValueError("Tabela e tipo de agregação são obrigatórios")
                
            # Construir query SQL para agregação
            agg_column = "*" if intent.aggregation == "COUNT" else "value"  # Assumir coluna 'value'
            sql_query = f"SELECT {intent.aggregation}({agg_column}) as result FROM {intent.table_name}"
            
            if intent.time_filter:
                sql_query += f" WHERE {intent.time_filter}"
                
            return {
                "tool": "execute_sql",
                "arguments": {
                    "query": sql_query,
                    "safe_mode": True
                }
            }
            
        else:
            # Fallback para execute_sql
            return {
                "tool": "execute_sql",
                "arguments": {
                    "query": f"SELECT * FROM {intent.table_name or 'information_schema.tables'} LIMIT 10",
                    "safe_mode": True
                }
            }

# Instância global do processador
nlp_processor = NLPQueryProcessor()

def process_natural_language_query(text: str) -> Dict[str, any]:
    """Função principal para processar queries em linguagem natural"""
    try:
        intent = nlp_processor.process_query(text)
        mcp_call = nlp_processor.generate_mcp_call(intent)
        
        return {
            "success": True,
            "intent": {
                "query_type": intent.query_type.value,
                "table_name": intent.table_name,
                "confidence": intent.confidence,
                "filters": intent.filters,
                "aggregation": intent.aggregation,
                "limit": intent.limit,
                "time_filter": intent.time_filter
            },
            "mcp_call": mcp_call
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "intent": None,
            "mcp_call": None
        }

# Exemplos de teste
if __name__ == "__main__":
    test_queries = [
        "Que tabelas existem na base de dados?",
        "Mostra-me a estrutura da tabela users",
        "Quantos utilizadores há na tabela users?",
        "Lista os primeiros 10 produtos",
        "Qual é o total de vendas do último mês?",
        "Mostra-me os clientes criados hoje",
        "Filtrar utilizadores onde idade maior que 25"
    ]
    
    print("🧠 Testando processador de linguagem natural...")
    print("=" * 60)
    
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        result = process_natural_language_query(query)
        print(f"🎯 Resultado: {json.dumps(result, indent=2, ensure_ascii=False)}")
        print("-" * 40)