"""
Sistema de Cache e Otimização de Performance para MCP Pipeline
Implementa cache LRU, connection pooling e otimizações de performance
"""
import os
import json
import time
import hashlib
import asyncio
import threading
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import OrderedDict
from functools import wraps
import logging

# Cache LRU Implementation
class LRUCache:
    """Cache LRU thread-safe para resultados de queries"""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 300):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache = OrderedDict()
        self.access_times = {}
        self.lock = threading.RLock()
        
    def _generate_key(self, query: str, params: Dict = None) -> str:
        """Gera chave única para cache"""
        cache_data = f"{query}:{json.dumps(params or {}, sort_keys=True)}"
        return hashlib.md5(cache_data.encode()).hexdigest()
        
    def _is_expired(self, key: str) -> bool:
        """Verifica se item do cache expirou"""
        if key not in self.access_times:
            return True
        return time.time() - self.access_times[key] > self.ttl_seconds
        
    def _cleanup_expired(self):
        """Remove itens expirados do cache"""
        current_time = time.time()
        expired_keys = [
            key for key, access_time in self.access_times.items()
            if current_time - access_time > self.ttl_seconds
        ]
        
        for key in expired_keys:
            self.cache.pop(key, None)
            self.access_times.pop(key, None)
            
    def get(self, query: str, params: Dict = None) -> Optional[Any]:
        """Obtém item do cache"""
        with self.lock:
            key = self._generate_key(query, params)
            
            if key not in self.cache or self._is_expired(key):
                return None
                
            # Move para o final (mais recente)
            value = self.cache.pop(key)
            self.cache[key] = value
            self.access_times[key] = time.time()
            
            return value
            
    def put(self, query: str, result: Any, params: Dict = None):
        """Armazena item no cache"""
        with self.lock:
            key = self._generate_key(query, params)
            
            # Remove item se já existe
            if key in self.cache:
                self.cache.pop(key)
                
            # Adiciona novo item
            self.cache[key] = result
            self.access_times[key] = time.time()
            
            # Remove itens mais antigos se necessário
            while len(self.cache) > self.max_size:
                oldest_key = next(iter(self.cache))
                self.cache.pop(oldest_key)
                self.access_times.pop(oldest_key, None)
                
            # Limpeza periódica
            if len(self.cache) % 100 == 0:
                self._cleanup_expired()
                
    def clear(self):
        """Limpa todo o cache"""
        with self.lock:
            self.cache.clear()
            self.access_times.clear()
            
    def stats(self) -> Dict[str, Any]:
        """Estatísticas do cache"""
        with self.lock:
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "ttl_seconds": self.ttl_seconds,
                "hit_ratio": getattr(self, '_hit_count', 0) / max(getattr(self, '_request_count', 1), 1)
            }

@dataclass
class QueryMetrics:
    """Métricas de performance de queries"""
    query_hash: str
    execution_time: float
    result_size: int
    timestamp: datetime
    cache_hit: bool
    query_type: str
    
class PerformanceOptimizer:
    """Otimizador de performance do sistema"""
    
    def __init__(self, cache_size: int = 1000, cache_ttl: int = 300):
        self.cache = LRUCache(cache_size, cache_ttl)
        self.metrics = []
        self.query_patterns = {}
        self.slow_queries = []
        self.lock = threading.Lock()
        
        # Configurar logging
        self.logger = logging.getLogger("PerformanceOptimizer")
        
    def cached_query(self, func):
        """Decorator para cache de queries"""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extrair query dos argumentos
            query = kwargs.get('query') or (args[0] if args else "")
            params = kwargs.get('params', {})
            
            start_time = time.time()
            
            # Tentar obter do cache
            cached_result = self.cache.get(query, params)
            if cached_result is not None:
                execution_time = time.time() - start_time
                
                # Registrar métricas de cache hit
                self._record_metrics(
                    query, execution_time, len(str(cached_result)), 
                    cache_hit=True, query_type="cached"
                )
                
                return cached_result
                
            # Executar query
            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Armazenar no cache
                self.cache.put(query, result, params)
                
                # Registrar métricas
                self._record_metrics(
                    query, execution_time, len(str(result)),
                    cache_hit=False, query_type="database"
                )
                
                # Verificar se é query lenta
                if execution_time > 2.0:  # Mais de 2 segundos
                    self._record_slow_query(query, execution_time)
                    
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                self._record_metrics(
                    query, execution_time, 0,
                    cache_hit=False, query_type="error"
                )
                raise
                
        return wrapper
        
    def _record_metrics(self, query: str, execution_time: float, result_size: int, 
                       cache_hit: bool, query_type: str):
        """Registra métricas de performance"""
        with self.lock:
            query_hash = hashlib.md5(query.encode()).hexdigest()[:8]
            
            metric = QueryMetrics(
                query_hash=query_hash,
                execution_time=execution_time,
                result_size=result_size,
                timestamp=datetime.now(),
                cache_hit=cache_hit,
                query_type=query_type
            )
            
            self.metrics.append(metric)
            
            # Manter apenas últimas 1000 métricas
            if len(self.metrics) > 1000:
                self.metrics = self.metrics[-1000:]
                
    def _record_slow_query(self, query: str, execution_time: float):
        """Registra query lenta para análise"""
        with self.lock:
            slow_query = {
                "query": query[:200] + "..." if len(query) > 200 else query,
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat()
            }
            
            self.slow_queries.append(slow_query)
            
            # Manter apenas últimas 100 queries lentas
            if len(self.slow_queries) > 100:
                self.slow_queries = self.slow_queries[-100:]
                
            self.logger.warning(f"Slow query detected: {execution_time:.2f}s - {query[:100]}")
            
    def analyze_patterns(self) -> Dict[str, Any]:
        """Analisa padrões de performance"""
        with self.lock:
            if not self.metrics:
                return {"status": "no_data"}
                
            recent_metrics = [
                m for m in self.metrics 
                if m.timestamp > datetime.now() - timedelta(hours=1)
            ]
            
            if not recent_metrics:
                return {"status": "no_recent_data"}
                
            # Calcular estatísticas
            execution_times = [m.execution_time for m in recent_metrics]
            cache_hits = sum(1 for m in recent_metrics if m.cache_hit)
            
            # Agrupar por tipo de query
            query_types = {}
            for metric in recent_metrics:
                if metric.query_type not in query_types:
                    query_types[metric.query_type] = []
                query_types[metric.query_type].append(metric.execution_time)
                
            type_stats = {}
            for query_type, times in query_types.items():
                type_stats[query_type] = {
                    "count": len(times),
                    "avg_time": sum(times) / len(times),
                    "max_time": max(times),
                    "min_time": min(times)
                }
                
            return {
                "total_queries": len(recent_metrics),
                "cache_hit_ratio": cache_hits / len(recent_metrics),
                "avg_execution_time": sum(execution_times) / len(execution_times),
                "max_execution_time": max(execution_times),
                "min_execution_time": min(execution_times),
                "slow_queries_count": len([t for t in execution_times if t > 2.0]),
                "query_type_stats": type_stats,
                "cache_stats": self.cache.stats()
            }
            
    def get_optimization_suggestions(self) -> List[str]:
        """Gera sugestões de otimização"""
        analysis = self.analyze_patterns()
        suggestions = []
        
        if analysis.get("status") in ["no_data", "no_recent_data"]:
            return ["Sistema sem dados suficientes para análise"]
            
        # Sugestões baseadas em cache hit ratio
        cache_hit_ratio = analysis.get("cache_hit_ratio", 0)
        if cache_hit_ratio < 0.3:
            suggestions.append("Cache hit ratio baixo (<30%). Considere aumentar TTL do cache.")
        elif cache_hit_ratio > 0.8:
            suggestions.append("Excelente cache hit ratio (>80%). Sistema bem otimizado.")
            
        # Sugestões baseadas em tempo de execução
        avg_time = analysis.get("avg_execution_time", 0)
        if avg_time > 1.0:
            suggestions.append("Tempo médio de execução alto (>1s). Revisar índices da base de dados.")
            
        # Sugestões baseadas em queries lentas
        slow_count = analysis.get("slow_queries_count", 0)
        if slow_count > 5:
            suggestions.append(f"{slow_count} queries lentas detectadas. Otimizar queries mais frequentes.")
            
        # Sugestões baseadas no cache
        cache_stats = analysis.get("cache_stats", {})
        cache_size = cache_stats.get("size", 0)
        max_cache_size = cache_stats.get("max_size", 1000)
        
        if cache_size / max_cache_size > 0.9:
            suggestions.append("Cache quase cheio. Considere aumentar tamanho do cache.")
            
        return suggestions or ["Sistema funcionando dentro dos parâmetros normais"]
        
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Dados para dashboard de monitorização"""
        analysis = self.analyze_patterns()
        suggestions = self.get_optimization_suggestions()
        
        return {
            "performance_analysis": analysis,
            "optimization_suggestions": suggestions,
            "slow_queries": self.slow_queries[-10:],  # Últimas 10 queries lentas
            "system_health": self._calculate_health_score(analysis),
            "timestamp": datetime.now().isoformat()
        }
        
    def _calculate_health_score(self, analysis: Dict) -> Dict[str, Any]:
        """Calcula score de saúde do sistema"""
        if analysis.get("status") in ["no_data", "no_recent_data"]:
            return {"score": 0, "status": "unknown"}
            
        score = 100
        status = "excellent"
        
        # Penalizar por tempo de execução alto
        avg_time = analysis.get("avg_execution_time", 0)
        if avg_time > 2.0:
            score -= 30
            status = "poor"
        elif avg_time > 1.0:
            score -= 15
            status = "fair"
            
        # Penalizar por cache hit ratio baixo
        cache_hit_ratio = analysis.get("cache_hit_ratio", 0)
        if cache_hit_ratio < 0.3:
            score -= 20
            status = "poor" if status == "excellent" else status
        elif cache_hit_ratio < 0.6:
            score -= 10
            status = "fair" if status == "excellent" else status
            
        # Penalizar por queries lentas
        slow_count = analysis.get("slow_queries_count", 0)
        if slow_count > 10:
            score -= 25
            status = "poor"
        elif slow_count > 5:
            score -= 10
            status = "fair" if status == "excellent" else status
            
        return {
            "score": max(0, score),
            "status": status,
            "factors": {
                "avg_execution_time": avg_time,
                "cache_hit_ratio": cache_hit_ratio,
                "slow_queries": slow_count
            }
        }

# Instância global do otimizador
performance_optimizer = PerformanceOptimizer()

# Decorator para cache automático
def cached_database_operation(func):
    """Decorator para operações de base de dados com cache automático"""
    return performance_optimizer.cached_query(func)

# Função para obter estatísticas de performance
def get_performance_stats() -> Dict[str, Any]:
    """Obtém estatísticas de performance do sistema"""
    return performance_optimizer.get_dashboard_data()

# Exemplo de uso
if __name__ == "__main__":
    import asyncio
    
    # Simular operações de base de dados
    @cached_database_operation
    async def simulate_query(query: str, delay: float = 0.1):
        """Simula execução de query"""
        await asyncio.sleep(delay)
        return {"result": f"Resultado para: {query}", "rows": 100}
        
    async def test_performance():
        """Teste do sistema de performance"""
        print("🚀 Testando Sistema de Performance...")
        
        # Simular várias queries
        queries = [
            ("SELECT * FROM users", 0.1),
            ("SELECT * FROM products", 0.2),
            ("SELECT * FROM users", 0.1),  # Cache hit
            ("SELECT COUNT(*) FROM orders", 0.5),
            ("SELECT * FROM users", 0.1),  # Cache hit
            ("COMPLEX QUERY...", 2.5),  # Query lenta
        ]
        
        for query, delay in queries:
            result = await simulate_query(query, delay)
            print(f"✅ Query executada: {query[:30]}...")
            
        # Obter estatísticas
        stats = get_performance_stats()
        print("\n📊 Estatísticas de Performance:")
        print(json.dumps(stats, indent=2, default=str))
        
    # Executar teste
    asyncio.run(test_performance())