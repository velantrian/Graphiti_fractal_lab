"""
Embedding Service with LRU Cache and TTL

Provides cached embeddings with automatic expiration and size limits.
"""

import asyncio
import json
import logging
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from openai import AsyncOpenAI
from dotenv import load_dotenv

from core.text_utils import fingerprint
from core.config import get_config

load_dotenv()
logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with creation timestamp for TTL."""
    embedding: List[float]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def is_expired(self, ttl_hours: int) -> bool:
        """Check if entry has expired."""
        now = datetime.now(timezone.utc)
        return (now - self.created_at) > timedelta(hours=ttl_hours)


class EmbeddingCache:
    """
    LRU Cache with TTL for embeddings.
    
    Features:
    - Maximum size limit (LRU eviction)
    - TTL-based expiration
    - Persistent storage to disk
    - Thread-safe async operations
    """
    
    def __init__(
        self,
        max_size: int = 10000,
        ttl_hours: int = 168,  # 7 days
        cache_file: Optional[Path] = None
    ):
        self.max_size = max_size
        self.ttl_hours = ttl_hours
        self.cache_file = cache_file or Path(__file__).parent.parent / ".embedding_cache.json"
        
        # OrderedDict for LRU behavior
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = asyncio.Lock()
        self._loaded = False
        self._dirty = False
        self._save_counter = 0
        
        # Stats
        self.hits = 0
        self.misses = 0
    
    async def _ensure_loaded(self):
        """Load cache from disk if not already loaded."""
        if self._loaded:
            return
        
        async with self._lock:
            if self._loaded:
                return
            
            if self.cache_file.exists():
                try:
                    with open(self.cache_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Convert to CacheEntry objects
                    now = datetime.now(timezone.utc)
                    loaded_count = 0
                    expired_count = 0
                    
                    for key, value in data.items():
                        # Handle old format (just embedding list)
                        if isinstance(value, list):
                            entry = CacheEntry(embedding=value)
                        # Handle new format (dict with embedding and created_at)
                        elif isinstance(value, dict):
                            created_at = datetime.fromisoformat(value.get('created_at', now.isoformat()))
                            entry = CacheEntry(
                                embedding=value['embedding'],
                                created_at=created_at
                            )
                        else:
                            continue
                        
                        # Skip expired entries
                        if entry.is_expired(self.ttl_hours):
                            expired_count += 1
                            continue
                        
                        self._cache[key] = entry
                        loaded_count += 1
                        
                        # Enforce max size during load
                        if len(self._cache) >= self.max_size:
                            break
                    
                    logger.info(
                        f"Loaded {loaded_count} embeddings from cache "
                        f"(expired: {expired_count}, max: {self.max_size})"
                    )
                except Exception as e:
                    logger.warning(f"Failed to load embedding cache: {e}")
            
            self._loaded = True
    
    async def get(self, key: str) -> Optional[List[float]]:
        """
        Get embedding from cache.
        
        Args:
            key: Cache key (fingerprint|model)
            
        Returns:
            Embedding list or None if not found/expired
        """
        await self._ensure_loaded()
        
        async with self._lock:
            if key not in self._cache:
                self.misses += 1
                return None
            
            entry = self._cache[key]
            
            # Check TTL
            if entry.is_expired(self.ttl_hours):
                del self._cache[key]
                self.misses += 1
                self._dirty = True
                return None
            
            # Move to end for LRU
            self._cache.move_to_end(key)
            self.hits += 1
            return entry.embedding
    
    async def set(self, key: str, embedding: List[float]):
        """
        Store embedding in cache.
        
        Args:
            key: Cache key
            embedding: Embedding vector
        """
        await self._ensure_loaded()
        
        async with self._lock:
            # Evict oldest if at capacity
            while len(self._cache) >= self.max_size:
                self._cache.popitem(last=False)
            
            self._cache[key] = CacheEntry(embedding=embedding)
            self._dirty = True
            self._save_counter += 1
            
            # Auto-save every 10 additions
            if self._save_counter >= 10:
                await self._save_unlocked()
                self._save_counter = 0
    
    async def _save_unlocked(self):
        """Save cache to disk (must hold lock)."""
        if not self._dirty:
            return
        
        try:
            # Convert to serializable format
            data = {}
            for key, entry in self._cache.items():
                data[key] = {
                    'embedding': entry.embedding,
                    'created_at': entry.created_at.isoformat()
                }
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
            
            self._dirty = False
            logger.debug(f"Saved {len(self._cache)} embeddings to cache")
        except Exception as e:
            logger.warning(f"Failed to save embedding cache: {e}")
    
    async def save(self):
        """Save cache to disk."""
        async with self._lock:
            await self._save_unlocked()
    
    async def clear(self):
        """Clear all cache entries."""
        async with self._lock:
            self._cache.clear()
            self._dirty = True
            await self._save_unlocked()
    
    async def cleanup_expired(self) -> int:
        """
        Remove expired entries.
        
        Returns:
            Number of entries removed
        """
        async with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired(self.ttl_hours)
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                self._dirty = True
                await self._save_unlocked()
            
            return len(expired_keys)
    
    def stats(self) -> Dict:
        """Get cache statistics."""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{hit_rate:.1f}%",
            "ttl_hours": self.ttl_hours
        }


# Global instances
_aclient: Optional[AsyncOpenAI] = None
_cache: Optional[EmbeddingCache] = None


def _get_cache() -> EmbeddingCache:
    """Get or create cache instance."""
    global _cache
    if _cache is None:
        config = get_config()
        _cache = EmbeddingCache(
            max_size=config.cache.embedding_cache_max_size,
            ttl_hours=config.cache.embedding_cache_ttl_hours
        )
    return _cache


def get_async_client() -> Optional[AsyncOpenAI]:
    """Get or create OpenAI async client."""
    global _aclient
    if _aclient is None:
        config = get_config()
        api_key = config.llm.openai_api_key
        if not api_key:
            logger.warning("OPENAI_API_KEY not set, embeddings will fail.")
            return None
        _aclient = AsyncOpenAI(api_key=api_key)
    return _aclient


async def get_embedding(
    text: str,
    model: Optional[str] = None
) -> Optional[List[float]]:
    """
    Get embedding for text using OpenAI API with caching.
    
    Args:
        text: Text to embed
        model: Embedding model (default from config)
        
    Returns:
        Embedding vector or None on error
    """
    config = get_config()
    model = model or config.llm.embedding_model
    cache = _get_cache()
    client = get_async_client()
    
    if not client:
        return None
    
    # Normalize whitespace
    text = text.replace("\n", " ").strip()
    if not text:
        return None
    
    # Create cache key
    fp = fingerprint(text)
    cache_key = f"{fp}|{model}"
    
    # Check cache
    cached = await cache.get(cache_key)
    if cached is not None:
        logger.debug(f"[embed] cache hit model={model} len={len(text)} fp={fp[:8]}")
        return cached
    
    # Call OpenAI API
    start_time = time.time()
    try:
        logger.info(f"[embed] API call model={model} len={len(text)} fp={fp[:8]}")
        resp = await client.embeddings.create(input=[text], model=model)
        embedding = resp.data[0].embedding
        took_ms = int((time.time() - start_time) * 1000)
        
        logger.info(f"[embed] success model={model} len={len(text)} took={took_ms}ms")
        
        # Cache result
        await cache.set(cache_key, embedding)
        
        return embedding
        
    except Exception as e:
        took_ms = int((time.time() - start_time) * 1000)
        error_type = type(e).__name__
        
        # Extract HTTP status if available
        status_code = "unknown"
        if hasattr(e, 'status_code'):
            status_code = str(e.status_code)
        elif hasattr(e, 'response') and hasattr(e.response, 'status_code'):
            status_code = str(e.response.status_code)
        elif "429" in str(e):
            status_code = "429"
        elif "402" in str(e):
            status_code = "402"
        
        logger.error(
            f"[embed] failed model={model} len={len(text)} "
            f"took={took_ms}ms status={status_code} error={error_type}: {str(e)[:100]}"
        )
        return None


async def get_embedding_batch(
    texts: List[str],
    model: Optional[str] = None
) -> List[Optional[List[float]]]:
    """
    Get embeddings for multiple texts.
    
    Args:
        texts: List of texts to embed
        model: Embedding model
        
    Returns:
        List of embeddings (None for failed items)
    """
    results = []
    for text in texts:
        embedding = await get_embedding(text, model)
        results.append(embedding)
    return results


def get_cache_stats() -> Dict:
    """Get embedding cache statistics."""
    cache = _get_cache()
    return cache.stats()


async def cleanup_cache() -> int:
    """
    Cleanup expired cache entries.
    
    Returns:
        Number of entries removed
    """
    cache = _get_cache()
    return await cache.cleanup_expired()


async def save_cache():
    """Force save cache to disk."""
    cache = _get_cache()
    await cache.save()
