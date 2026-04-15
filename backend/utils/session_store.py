"""
Thread-safe in-memory session store.

Each session holds:
- language         : "es" | "en"
- topic            : original research topic
- sources          : list of {title, url, snippet, citation_apa, citation_ieee}
- summary          : markdown summary of findings
- structured_data  : dict ready for file generation (sections, tables, charts...)
- status           : "idle" | "researching" | "awaiting_format" | "generating" | "done" | "error"
- error            : optional error message
"""

import asyncio
import time
import uuid
from typing import Any

from cachetools import TTLCache

# TTL is read from env at import time; default 1 h
import os
_TTL = int(os.getenv("SESSION_TTL_SECONDS", 3600))

# TTLCache is not async-safe, so we guard every access with a lock.
_cache: TTLCache = TTLCache(maxsize=512, ttl=_TTL)
_lock = asyncio.Lock()


async def create_session(language: str, topic: str) -> str:
    session_id = str(uuid.uuid4())
    async with _lock:
        _cache[session_id] = {
            "language": language,
            "topic": topic,
            "sources": [],
            "summary": "",
            "structured_data": {},
            "status": "idle",
            "error": None,
            "created_at": time.time(),
        }
    return session_id


async def get_session(session_id: str) -> dict[str, Any] | None:
    async with _lock:
        return _cache.get(session_id)


async def update_session(session_id: str, **kwargs: Any) -> None:
    async with _lock:
        session = _cache.get(session_id)
        if session is None:
            raise KeyError(f"Session {session_id} not found or expired")
        session.update(kwargs)
        _cache[session_id] = session


async def delete_session(session_id: str) -> None:
    async with _lock:
        _cache.pop(session_id, None)
