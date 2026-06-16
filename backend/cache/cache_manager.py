"""
MarketMind AI Dashboard - Cache Manager
Two-tier cache: in-memory (fast) + JSON file (persistent across restarts).
TTL-based expiration with stale fallback.
"""
from __future__ import annotations
import hashlib
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any, Optional

from config import settings

logger = logging.getLogger(__name__)


class CacheEntry:
    """A single cache entry with TTL tracking."""
    def __init__(self, key: str, value: Any, ttl_seconds: int):
        self.key = key
        self.value = value
        self.ttl = ttl_seconds
        self.created_at = time.time()
        self.accessed_at = self.created_at

    def is_expired(self) -> bool:
        return time.time() > self.created_at + self.ttl

    def age_seconds(self) -> float:
        return time.time() - self.created_at

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "value": self.value,
            "ttl": self.ttl,
            "created_at": self.created_at,
            "created_iso": datetime.fromtimestamp(self.created_at).isoformat(),
        }


class CacheManager:
    """
    In-memory + file-persisted cache with TTL.
    On API failure, serves stale cached data as fallback.
    """

    def __init__(self, cache_dir: Optional[Path] = None):
        self._cache_dir = cache_dir or settings.CACHE_DIR
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._memory: dict[str, CacheEntry] = {}
        self._lock = Lock()
        self._load_from_disk()

    def _build_filepath(self, key: str) -> Path:
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return self._cache_dir / f"{digest}.json"

    def _build_legacy_filepath(self, key: str) -> Path:
        safe_key = key.replace("/", "_").replace("\\", "_").replace(":", "_")
        return self._cache_dir / f"{safe_key}.json"

    def _load_from_disk(self):
        """Load all cached files from disk into memory on startup."""
        if not self._cache_dir.exists():
            return
        loaded = 0
        expired = 0
        for filepath in self._cache_dir.glob("*.json"):
            try:
                data = json.loads(filepath.read_text(encoding="utf-8"))
                entry = CacheEntry(
                    key=data["key"],
                    value=data["value"],
                    ttl_seconds=data.get("ttl", 3600),
                )
                entry.created_at = data.get("created_at", time.time())
                if not entry.is_expired():
                    self._memory[entry.key] = entry
                    loaded += 1
                else:
                    expired += 1
            except Exception as e:
                logger.warning(f"Failed to load cache file {filepath}: {e}")
        logger.info(f"Cache loaded: {loaded} active, {expired} expired")

    def get(self, key: str) -> Optional[Any]:
        """Get a cached value, returns None if missing or expired."""
        with self._lock:
            entry = self._memory.get(key)
            if entry is None:
                return None
            if entry.is_expired():
                # Keep on disk but remove from memory
                del self._memory[key]
                return None
            entry.accessed_at = time.time()
            return entry.value

    def get_with_meta(self, key: str) -> tuple[Optional[Any], bool]:
        """
        Get cached value with a stale flag.
        Returns (value, is_stale).
        value is None only if no cache exists at all.
        """
        with self._lock:
            entry = self._memory.get(key)
            if entry is None:
                # Try disk
                filepath = self._build_filepath(key)
                if not filepath.exists():
                    filepath = self._build_legacy_filepath(key)
                if filepath.exists():
                    try:
                        data = json.loads(filepath.read_text(encoding="utf-8"))
                        return data.get("value"), True  # stale
                    except Exception:
                        return None, False
                return None, False
            if entry.is_expired():
                return entry.value, True  # stale
            return entry.value, False  # fresh

    def set(self, key: str, value: Any, ttl_seconds: int = 3600):
        """Set a cache entry with TTL."""
        entry = CacheEntry(key=key, value=value, ttl_seconds=ttl_seconds)
        with self._lock:
            self._memory[key] = entry
        # Persist to disk
        try:
            filepath = self._build_filepath(key)
            filepath.write_text(json.dumps(entry.to_dict(), default=str), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to persist cache key '{key}': {e}")

    def prune_expired(self):
        """Remove all expired entries from memory and disk."""
        with self._lock:
            expired_keys = [k for k, e in self._memory.items() if e.is_expired()]
            for key in expired_keys:
                del self._memory[key]
                filepath = self._build_filepath(key)
                try:
                    filepath.unlink(missing_ok=True)
                except Exception:
                    pass
        if expired_keys:
            logger.info(f"Pruned {len(expired_keys)} expired cache entries")

    @property
    def size(self) -> int:
        return len(self._memory)

    def stats(self) -> dict:
        now = time.time()
        fresh = sum(1 for e in self._memory.values() if not e.is_expired())
        stale = self.size - fresh
        return {
            "total_entries": self.size,
            "fresh_entries": fresh,
            "stale_entries": stale,
        }


# Global singleton
cache = CacheManager()
