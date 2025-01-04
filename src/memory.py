from typing import Dict, Any
import weakref

class MemoryManager:
    _cache: Dict[str, Any] = {}
    _refs = weakref.WeakValueDictionary()

    @classmethod
    def clear_cache(cls):
        """Clear memory cache"""
        cls._cache.clear()
        cls._refs.clear()

    @classmethod
    def cache_size(cls) -> int:
        """Get current cache size"""
        return len(cls._cache)
