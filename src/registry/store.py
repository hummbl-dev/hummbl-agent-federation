"""
Persistent storage for the provider registry.

Supports SQLite (local/single-node) and Redis (distributed) backends.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from contextlib import contextmanager

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from .models import Provider, ProviderHealth, ProviderStatus


class RegistryStore:
    """
    Abstract base class for registry storage backends.
    """
    
    def save_provider(self, provider: Provider) -> None:
        """Save or update a provider."""
        raise NotImplementedError
    
    def get_provider(self, provider_id: str) -> Optional[Provider]:
        """Retrieve a provider by ID."""
        raise NotImplementedError
    
    def get_all_providers(self) -> Dict[str, Provider]:
        """Retrieve all providers."""
        raise NotImplementedError
    
    def save_health(self, provider_id: str, health: ProviderHealth) -> None:
        """Save health metrics for a provider."""
        raise NotImplementedError
    
    def get_health_history(self, provider_id: str, limit: int = 100) -> List[dict]:
        """Get health check history for a provider."""
        raise NotImplementedError


class SQLiteStore(RegistryStore):
    """
    SQLite-backed registry store for local or single-node deployments.
    
    Schema:
    - providers: Static provider configuration
    - health_checks: Time-series health metrics
    - routing_outcomes: Learning data for optimization
    """
    
    def __init__(self, db_path: str = "federation.db"):
        self.db_path = Path(db_path)
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema."""
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS providers (
                    id TEXT PRIMARY KEY,
                    config JSON NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS health_checks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provider_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    latency_ms REAL,
                    error_rate REAL,
                    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (provider_id) REFERENCES providers(id)
                );
                
                CREATE TABLE IF NOT EXISTS routing_outcomes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provider_id TEXT NOT NULL,
                    task_type TEXT,
                    success BOOLEAN,
                    quality_score REAL,
                    cost REAL,
                    latency_ms INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (provider_id) REFERENCES providers(id)
                );
                
                CREATE INDEX IF NOT EXISTS idx_health_provider 
                    ON health_checks(provider_id, checked_at);
                
                CREATE INDEX IF NOT EXISTS idx_outcomes_provider 
                    ON routing_outcomes(provider_id, created_at);
            """)
    
    @contextmanager
    def _connect(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()
    
    def save_provider(self, provider: Provider) -> None:
        """Save or update a provider."""
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO providers (id, config, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    config = excluded.config,
                    updated_at = excluded.updated_at
                """,
                (provider.id, json.dumps(provider.to_dict()), datetime.utcnow())
            )
    
    def get_provider(self, provider_id: str) -> Optional[Provider]:
        """Retrieve a provider by ID."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT config FROM providers WHERE id = ?",
                (provider_id,)
            ).fetchone()
            
            if row:
                # Note: Full reconstruction would need loader logic
                # For now, return simplified version
                config = json.loads(row['config'])
                return self._reconstruct_provider(config)
            return None
    
    def get_all_providers(self) -> Dict[str, Provider]:
        """Retrieve all providers."""
        with self._connect() as conn:
            rows = conn.execute("SELECT id, config FROM providers").fetchall()
            
            providers = {}
            for row in rows:
                config = json.loads(row['config'])
                provider = self._reconstruct_provider(config)
                providers[provider.id] = provider
            
            return providers
    
    def save_health(self, provider_id: str, health: ProviderHealth) -> None:
        """Save health check result."""
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO health_checks 
                    (provider_id, status, latency_ms, error_rate, checked_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    provider_id,
                    health.status.name,
                    health.avg_latency_ms,
                    health.error_rate_24h,
                    health.last_checked or datetime.utcnow()
                )
            )
    
    def get_health_history(self, provider_id: str, limit: int = 100) -> List[dict]:
        """Get recent health checks for a provider."""
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT status, latency_ms, error_rate, checked_at
                FROM health_checks
                WHERE provider_id = ?
                ORDER BY checked_at DESC
                LIMIT ?
                """,
                (provider_id, limit)
            ).fetchall()
            
            return [dict(row) for row in rows]
    
    def save_routing_outcome(self, provider_id: str, task_type: str, 
                            success: bool, quality_score: float,
                            cost: float, latency_ms: int) -> None:
        """Save routing outcome for learning."""
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO routing_outcomes
                    (provider_id, task_type, success, quality_score, cost, latency_ms)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (provider_id, task_type, success, quality_score, cost, latency_ms)
            )
    
    def get_routing_stats(self, provider_id: str, 
                         days: int = 7) -> Optional[dict]:
        """Get aggregate routing statistics for a provider."""
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT 
                    COUNT(*) as total_requests,
                    SUM(CASE WHEN success THEN 1 ELSE 0 END) as success_count,
                    AVG(quality_score) as avg_quality,
                    AVG(cost) as avg_cost,
                    AVG(latency_ms) as avg_latency
                FROM routing_outcomes
                WHERE provider_id = ?
                    AND created_at >= datetime('now', '-' || ? || ' days')
                """,
                (provider_id, days)
            ).fetchone()
            
            if row and row['total_requests']:
                return {
                    'total_requests': row['total_requests'],
                    'success_rate': row['success_count'] / row['total_requests'],
                    'avg_quality': row['avg_quality'],
                    'avg_cost': row['avg_cost'],
                    'avg_latency_ms': row['avg_latency'],
                }
            return None
    
    def _reconstruct_provider(self, config: dict) -> Provider:
        """Reconstruct a Provider from stored config."""
        # Simplified reconstruction - full impl would need all fields
        from .loader import RegistryLoader
        loader = RegistryLoader()
        return loader._create_provider(config)


class RedisStore(RegistryStore):
    """
    Redis-backed registry store for distributed deployments.
    
    Uses Redis hashes for provider data and sorted sets for time-series.
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        if not REDIS_AVAILABLE:
            raise ImportError("Redis support requires 'redis' package: pip install redis")
        
        self.client = redis.from_url(redis_url, decode_responses=True)
        self.key_prefix = "federation"
    
    def _key(self, *parts) -> str:
        """Build a Redis key with prefix."""
        return f"{self.key_prefix}:{':'.join(parts)}"
    
    def save_provider(self, provider: Provider) -> None:
        """Save or update a provider."""
        key = self._key("provider", provider.id)
        self.client.hset(key, mapping={
            "config": json.dumps(provider.to_dict()),
            "updated_at": datetime.utcnow().isoformat(),
        })
        # Add to provider index
        self.client.sadd(self._key("providers"), provider.id)
    
    def get_provider(self, provider_id: str) -> Optional[Provider]:
        """Retrieve a provider by ID."""
        key = self._key("provider", provider_id)
        data = self.client.hget(key, "config")
        
        if data:
            config = json.loads(data)
            from .loader import RegistryLoader
            loader = RegistryLoader()
            return loader._create_provider(config)
        return None
    
    def get_all_providers(self) -> Dict[str, Provider]:
        """Retrieve all providers."""
        provider_ids = self.client.smembers(self._key("providers"))
        providers = {}
        
        for pid in provider_ids:
            provider = self.get_provider(pid)
            if provider:
                providers[pid] = provider
        
        return providers
    
    def save_health(self, provider_id: str, health: ProviderHealth) -> None:
        """Save health check result."""
        # Add to sorted set by timestamp
        key = self._key("health", provider_id)
        timestamp = datetime.utcnow().timestamp()
        
        data = json.dumps({
            "status": health.status.name,
            "latency_ms": health.avg_latency_ms,
            "error_rate": health.error_rate_24h,
            "timestamp": timestamp,
        })
        
        self.client.zadd(key, {data: timestamp})
        
        # Trim to last 10,000 entries
        self.client.zremrangebyrank(key, 0, -10001)
    
    def get_health_history(self, provider_id: str, limit: int = 100) -> List[dict]:
        """Get recent health checks for a provider."""
        key = self._key("health", provider_id)
        entries = self.client.zrevrange(key, 0, limit - 1)
        
        return [json.loads(e) for e in entries]


def create_store(backend: str = "sqlite", **kwargs) -> RegistryStore:
    """
    Factory function to create the appropriate store backend.
    
    Args:
        backend: "sqlite" or "redis"
        **kwargs: Backend-specific configuration
        
    Returns:
        Configured RegistryStore instance
    """
    if backend == "sqlite":
        return SQLiteStore(db_path=kwargs.get("db_path", "federation.db"))
    elif backend == "redis":
        return RedisStore(redis_url=kwargs.get("redis_url", "redis://localhost:6379/0"))
    else:
        raise ValueError(f"Unknown backend: {backend}")
