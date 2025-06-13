"""
Sistema de Segurança e Monitorização para MCP Pipeline
Implementa validação de segurança, auditoria e monitorização de performance
"""
import os
import re
import json
import time
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import threading
from collections import defaultdict, deque

class SecurityLevel(Enum):
    """Níveis de segurança"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertType(Enum):
    """Tipos de alerta"""
    SQL_INJECTION = "sql_injection"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_QUERY = "suspicious_query"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    CONNECTION_FAILURE = "connection_failure"

@dataclass
class SecurityEvent:
    """Evento de segurança"""
    timestamp: datetime
    event_type: AlertType
    severity: SecurityLevel
    user_id: str
    query: str
    source_ip: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    
class QueryValidator:
    """Validador de queries SQL para segurança"""
    
    def __init__(self):
        # Palavras-chave perigosas
        self.dangerous_keywords = {
            'DROP': SecurityLevel.CRITICAL,
            'DELETE': SecurityLevel.HIGH,
            'TRUNCATE': SecurityLevel.CRITICAL,
            'ALTER': SecurityLevel.HIGH,
            'CREATE': SecurityLevel.MEDIUM,
            'INSERT': SecurityLevel.MEDIUM,
            'UPDATE': SecurityLevel.MEDIUM,
            'EXEC': SecurityLevel.CRITICAL,
            'EXECUTE': SecurityLevel.CRITICAL,
            'UNION': SecurityLevel.MEDIUM,
            'INFORMATION_SCHEMA': SecurityLevel.LOW,
            'pg_': SecurityLevel.MEDIUM  # PostgreSQL system functions
        }
        
        # Padrões de SQL injection
        self.injection_patterns = [
            r"'.*OR.*'.*'",  # ' OR '1'='1
            r"'.*UNION.*SELECT",  # UNION injection
            r"';.*--",  # SQL comment injection
            r"'.*AND.*'.*'",  # ' AND '1'='1
            r"\\x[0-9a-fA-F]+",  # Hex encoding
            r"CHAR\s*\(",  # CHAR function
            r"ASCII\s*\(",  # ASCII function
            r"/\*.*\*/",  # SQL comments
            r"--.*",  # Line comments
            r"xp_cmdshell",  # System command execution
            r"sp_executesql"  # Dynamic SQL execution
        ]
        
        # Limites de query
        self.max_query_length = 10000
        self.max_result_limit = 10000
        
    def validate_query(self, query: str, user_id: str = "unknown") -> Tuple[bool, List[SecurityEvent]]:
        """Valida uma query SQL"""
        events = []
        query_upper = query.upper()
        
        # Verificar comprimento
        if len(query) > self.max_query_length:
            events.append(SecurityEvent(
                timestamp=datetime.now(),
                event_type=AlertType.SUSPICIOUS_QUERY,
                severity=SecurityLevel.MEDIUM,
                user_id=user_id,
                query=query[:100] + "...",
                details={"reason": "Query muito longa", "length": len(query)}
            ))
            
        # Verificar palavras-chave perigosas
        for keyword, severity in self.dangerous_keywords.items():
            if keyword in query_upper:
                # Verificar se é uma operação de leitura legítima
                if keyword in ['INFORMATION_SCHEMA'] and query_upper.strip().startswith('SELECT'):
                    continue
                    
                events.append(SecurityEvent(
                    timestamp=datetime.now(),
                    event_type=AlertType.SUSPICIOUS_QUERY,
                    severity=severity,
                    user_id=user_id,
                    query=query,
                    details={"dangerous_keyword": keyword}
                ))
                
        # Verificar padrões de injection
        for pattern in self.injection_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                events.append(SecurityEvent(
                    timestamp=datetime.now(),
                    event_type=AlertType.SQL_INJECTION,
                    severity=SecurityLevel.CRITICAL,
                    user_id=user_id,
                    query=query,
                    details={"injection_pattern": pattern}
                ))
                
        # Verificar LIMIT excessivo
        limit_match = re.search(r'LIMIT\s+(\d+)', query_upper)
        if limit_match:
            limit_value = int(limit_match.group(1))
            if limit_value > self.max_result_limit:
                events.append(SecurityEvent(
                    timestamp=datetime.now(),
                    event_type=AlertType.SUSPICIOUS_QUERY,
                    severity=SecurityLevel.MEDIUM,
                    user_id=user_id,
                    query=query,
                    details={"excessive_limit": limit_value}
                ))
        
        # Query aprovada se não houver eventos críticos
        critical_events = [e for e in events if e.severity == SecurityLevel.CRITICAL]
        is_safe = len(critical_events) == 0
        
        return is_safe, events

class RateLimiter:
    """Limitador de taxa de requisições"""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(deque)
        self.lock = threading.Lock()
        
    def is_allowed(self, user_id: str) -> bool:
        """Verifica se o utilizador pode fazer uma requisição"""
        with self.lock:
            now = time.time()
            user_requests = self.requests[user_id]
            
            # Remover requisições antigas
            while user_requests and user_requests[0] < now - self.window_seconds:
                user_requests.popleft()
                
            # Verificar limite
            if len(user_requests) >= self.max_requests:
                return False
                
            # Adicionar nova requisição
            user_requests.append(now)
            return True

class PerformanceMonitor:
    """Monitor de performance do sistema"""
    
    def __init__(self):
        self.query_times = deque(maxlen=1000)  # Últimos 1000 queries
        self.error_count = defaultdict(int)
        self.connection_stats = {
            'active_connections': 0,
            'total_connections': 0,
            'failed_connections': 0
        }
        self.lock = threading.Lock()
        
    def record_query_time(self, duration: float, query_type: str = "unknown"):
        """Registra tempo de execução de query"""
        with self.lock:
            self.query_times.append({
                'timestamp': datetime.now(),
                'duration': duration,
                'query_type': query_type
            })
            
    def record_error(self, error_type: str):
        """Registra erro"""
        with self.lock:
            self.error_count[error_type] += 1
            
    def get_performance_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas de performance"""
        with self.lock:
            if not self.query_times:
                return {"status": "no_data"}
                
            durations = [q['duration'] for q in self.query_times]
            recent_queries = [q for q in self.query_times 
                            if q['timestamp'] > datetime.now() - timedelta(minutes=5)]
            
            return {
                "avg_query_time": sum(durations) / len(durations),
                "max_query_time": max(durations),
                "min_query_time": min(durations),
                "total_queries": len(self.query_times),
                "recent_queries": len(recent_queries),
                "error_count": dict(self.error_count),
                "connection_stats": self.connection_stats.copy()
            }

class SecurityLogger:
    """Logger especializado para eventos de segurança"""
    
    def __init__(self, log_file: str = "security.log"):
        self.log_file = log_file
        self.setup_logger()
        
    def setup_logger(self):
        """Configura o logger"""
        self.logger = logging.getLogger("SecurityLogger")
        self.logger.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # File handler
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Console handler para eventos críticos
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
    def log_event(self, event: SecurityEvent):
        """Registra evento de segurança"""
        event_data = {
            "timestamp": event.timestamp.isoformat(),
            "type": event.event_type.value,
            "severity": event.severity.value,
            "user_id": event.user_id,
            "query_hash": hashlib.md5(event.query.encode()).hexdigest(),
            "details": event.details
        }
        
        message = f"SECURITY_EVENT: {json.dumps(event_data)}"
        
        if event.severity == SecurityLevel.CRITICAL:
            self.logger.critical(message)
        elif event.severity == SecurityLevel.HIGH:
            self.logger.error(message)
        elif event.severity == SecurityLevel.MEDIUM:
            self.logger.warning(message)
        else:
            self.logger.info(message)

class SecurityMonitor:
    """Monitor principal de segurança"""
    
    def __init__(self, 
                 max_requests: int = 100, 
                 window_seconds: int = 60,
                 log_file: str = "security.log"):
        self.validator = QueryValidator()
        self.rate_limiter = RateLimiter(max_requests, window_seconds)
        self.performance_monitor = PerformanceMonitor()
        self.security_logger = SecurityLogger(log_file)
        self.blocked_users = set()
        
    def validate_request(self, query: str, user_id: str, source_ip: str = None) -> Tuple[bool, List[SecurityEvent]]:
        """Valida uma requisição completa"""
        events = []
        
        # Verificar rate limiting
        if not self.rate_limiter.is_allowed(user_id):
            event = SecurityEvent(
                timestamp=datetime.now(),
                event_type=AlertType.RATE_LIMIT_EXCEEDED,
                severity=SecurityLevel.HIGH,
                user_id=user_id,
                query="",
                source_ip=source_ip,
                details={"max_requests": self.rate_limiter.max_requests}
            )
            events.append(event)
            self.security_logger.log_event(event)
            return False, events
            
        # Verificar se utilizador está bloqueado
        if user_id in self.blocked_users:
            event = SecurityEvent(
                timestamp=datetime.now(),
                event_type=AlertType.UNAUTHORIZED_ACCESS,
                severity=SecurityLevel.CRITICAL,
                user_id=user_id,
                query=query,
                source_ip=source_ip,
                details={"reason": "User blocked"}
            )
            events.append(event)
            self.security_logger.log_event(event)
            return False, events
            
        # Validar query
        is_safe, query_events = self.validator.validate_query(query, user_id)
        events.extend(query_events)
        
        # Log eventos
        for event in query_events:
            self.security_logger.log_event(event)
            
        # Bloquear utilizador se houver muitos eventos críticos
        critical_events = [e for e in events if e.severity == SecurityLevel.CRITICAL]
        if len(critical_events) > 0:
            self.blocked_users.add(user_id)
            
        return is_safe, events
        
    def record_query_performance(self, duration: float, query_type: str = "unknown"):
        """Registra performance de query"""
        self.performance_monitor.record_query_time(duration, query_type)
        
        # Alertar se performance degradou
        stats = self.performance_monitor.get_performance_stats()
        if stats.get("avg_query_time", 0) > 5.0:  # Mais de 5 segundos
            event = SecurityEvent(
                timestamp=datetime.now(),
                event_type=AlertType.PERFORMANCE_DEGRADATION,
                severity=SecurityLevel.MEDIUM,
                user_id="system",
                query="",
                details=stats
            )
            self.security_logger.log_event(event)
            
    def get_security_status(self) -> Dict[str, Any]:
        """Obtém status de segurança do sistema"""
        performance_stats = self.performance_monitor.get_performance_stats()
        
        return {
            "blocked_users": len(self.blocked_users),
            "performance": performance_stats,
            "rate_limiter": {
                "max_requests": self.rate_limiter.max_requests,
                "window_seconds": self.rate_limiter.window_seconds
            },
            "system_status": "healthy" if performance_stats.get("avg_query_time", 0) < 2.0 else "degraded"
        }
        
    def unblock_user(self, user_id: str):
        """Desbloqueia utilizador (para administradores)"""
        self.blocked_users.discard(user_id)
        
        event = SecurityEvent(
            timestamp=datetime.now(),
            event_type=AlertType.UNAUTHORIZED_ACCESS,
            severity=SecurityLevel.LOW,
            user_id="admin",
            query="",
            details={"action": "unblock_user", "target_user": user_id}
        )
        self.security_logger.log_event(event)

# Instância global do monitor de segurança
security_monitor = SecurityMonitor()

def validate_database_request(query: str, user_id: str = "unknown", source_ip: str = None) -> Tuple[bool, List[Dict]]:
    """Função principal para validar requisições de base de dados"""
    is_safe, events = security_monitor.validate_request(query, user_id, source_ip)
    
    # Converter eventos para dict para serialização
    events_dict = [asdict(event) for event in events]
    for event_dict in events_dict:
        event_dict['timestamp'] = event_dict['timestamp'].isoformat()
        event_dict['event_type'] = event_dict['event_type'].value
        event_dict['severity'] = event_dict['severity'].value
    
    return is_safe, events_dict

# Exemplo de uso
if __name__ == "__main__":
    # Testes de segurança
    test_queries = [
        "SELECT * FROM users LIMIT 10",  # Segura
        "DROP TABLE users",  # Perigosa
        "' OR '1'='1",  # SQL Injection
        "SELECT * FROM information_schema.tables",  # Potencialmente suspeita
        "UPDATE users SET password = 'hacked' WHERE id = 1"  # Operação de escrita
    ]
    
    print("🛡️ Testando Sistema de Segurança...")
    print("=" * 50)
    
    for query in test_queries:
        print(f"\n🔍 Query: {query}")
        is_safe, events = validate_database_request(query, "test_user")
        
        print(f"✅ Segura: {is_safe}")
        if events:
            print("⚠️ Eventos de segurança:")
            for event in events:
                print(f"   - {event['event_type']}: {event['severity']}")
        print("-" * 30)
    
    # Status do sistema
    print(f"\n📊 Status do Sistema:")
    status = security_monitor.get_security_status()
    print(json.dumps(status, indent=2))