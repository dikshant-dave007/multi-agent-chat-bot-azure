"""
Cache service for Semantic Kernel orchestration.

This module provides caching capabilities for:
- Intent detection results
- Agent responses
- Semantic search results
"""

import hashlib
import json
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from abc import ABC, abstractmethod

from src.core.logging_config import LoggerMixin


class CacheEntry:
    """Represents a cache entry."""
    
    def __init__(
        self,
        key: str,
        value: Any,
        ttl_minutes: int = 30,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize cache entry.
        
        Args:
            key: Cache key
            value: Cached value
            ttl_minutes: Time to live in minutes
            metadata: Additional metadata
        """
        self.key = key
        self.value = value
        self.created_at = datetime.utcnow()
        self.expires_at = datetime.utcnow() + timedelta(minutes=ttl_minutes)
        self.metadata = metadata or {}
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        return datetime.utcnow() > self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "key": self.key,
            "value": self.value,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "metadata": self.metadata,
        }


class CacheProvider(ABC, LoggerMixin):
    """Abstract base class for cache providers."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl_minutes: int = 30) -> None:
        """Set value in cache."""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete value from cache."""
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """Clear all cache entries."""
        pass


class InMemoryCacheProvider(CacheProvider):
    """In-memory cache provider (suitable for development)."""
    
    def __init__(self):
        """Initialize in-memory cache."""
        self._cache: Dict[str, CacheEntry] = {}
        self.logger.info("in_memory_cache_initialized")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        
        if entry.is_expired():
            await self.delete(key)
            return None
        
        self.logger.debug("cache_hit", key=key)
        return entry.value
    
    async def set(self, key: str, value: Any, ttl_minutes: int = 30) -> None:
        """Set value in cache."""
        entry = CacheEntry(key, value, ttl_minutes)
        self._cache[key] = entry
        self.logger.debug("cache_set", key=key, ttl_minutes=ttl_minutes)
    
    async def delete(self, key: str) -> None:
        """Delete value from cache."""
        if key in self._cache:
            del self._cache[key]
            self.logger.debug("cache_deleted", key=key)
    
    async def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        self.logger.info("cache_cleared")


class CacheService(LoggerMixin):
    """
    Caching service for multi-agent orchestration.
    
    Handles caching of:
    - Intent detection results
    - Agent responses
    - Semantic search results
    """
    
    def __init__(self, provider: Optional[CacheProvider] = None):
        """
        Initialize cache service.
        
        Args:
            provider: Cache provider (defaults to InMemoryCacheProvider)
        """
        self._provider = provider or InMemoryCacheProvider()
        self.logger.info("cache_service_initialized", provider=type(self._provider).__name__)
    
    @staticmethod
    def _generate_key(prefix: str, data: Dict[str, Any]) -> str:
        """
        Generate cache key from data.
        
        Args:
            prefix: Cache key prefix
            data: Data to hash
            
        Returns:
            Cache key
        """
        # Sort keys for consistent hashing
        json_str = json.dumps(data, sort_keys=True, default=str)
        hash_obj = hashlib.sha256(json_str.encode())
        return f"{prefix}:{hash_obj.hexdigest()}"
    
    async def get_intent(self, query: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get cached intent detection result.
        
        Args:
            query: User query
            user_id: Optional user ID for personalization
            
        Returns:
            Cached intent result or None
        """
        data = {"query": query, "user_id": user_id}
        key = self._generate_key("intent", data)
        result = await self._provider.get(key)
        
        if result:
            self.logger.debug("intent_cache_hit", query=query[:50])
        return result
    
    async def set_intent(
        self,
        query: str,
        intent: str,
        confidence: float,
        user_id: Optional[str] = None,
        ttl_minutes: int = 60
    ) -> None:
        """
        Cache intent detection result.
        
        Args:
            query: User query
            intent: Detected intent
            confidence: Confidence score
            user_id: Optional user ID
            ttl_minutes: Time to live
        """
        data = {"query": query, "user_id": user_id}
        key = self._generate_key("intent", data)
        
        value = {
            "intent": intent,
            "confidence": confidence,
            "detected_at": datetime.utcnow().isoformat(),
        }
        
        await self._provider.set(key, value, ttl_minutes)
        self.logger.debug("intent_cached", intent=intent, confidence=confidence)
    
    async def get_response(
        self,
        agent_type: str,
        query: str,
        user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached agent response.
        
        Args:
            agent_type: Type of agent
            query: User query
            user_id: Optional user ID
            
        Returns:
            Cached response or None
        """
        data = {"agent_type": agent_type, "query": query, "user_id": user_id}
        key = self._generate_key("response", data)
        result = await self._provider.get(key)
        
        if result:
            self.logger.debug("response_cache_hit", agent_type=agent_type)
        return result
    
    async def set_response(
        self,
        agent_type: str,
        query: str,
        response: str,
        user_id: Optional[str] = None,
        ttl_minutes: int = 30
    ) -> None:
        """
        Cache agent response.
        
        Args:
            agent_type: Type of agent
            query: User query
            response: Agent response
            user_id: Optional user ID
            ttl_minutes: Time to live
        """
        data = {"agent_type": agent_type, "query": query, "user_id": user_id}
        key = self._generate_key("response", data)
        
        value = {
            "response": response,
            "cached_at": datetime.utcnow().isoformat(),
        }
        
        await self._provider.set(key, value, ttl_minutes)
        self.logger.debug("response_cached", agent_type=agent_type)
    
    async def invalidate_user_cache(self, user_id: str) -> None:
        """
        Invalidate all cache entries for a user.
        
        Args:
            user_id: User ID to invalidate cache for
        """
        # For now, just clear all cache
        # In production, you'd track per-user cache keys
        await self._provider.clear()
        self.logger.info("user_cache_invalidated", user_id=user_id)
    
    async def clear_all(self) -> None:
        """Clear all cache entries."""
        await self._provider.clear()
        self.logger.info("all_cache_cleared")


# Global cache service instance
_cache_service: Optional[CacheService] = None


def get_cache_service(provider: Optional[CacheProvider] = None) -> CacheService:
    """
    Get or create the global cache service instance.
    
    Args:
        provider: Optional cache provider
        
    Returns:
        CacheService instance
    """
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService(provider)
    return _cache_service
