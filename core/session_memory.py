from __future__ import annotations

from typing import List, Tuple, Dict
from collections import defaultdict

_mem: Dict[str, List[Tuple[str, str]]] = defaultdict(list)


def append(session_id: str, role: str, content: str) -> None:
    _mem[session_id].append((role, content))


def recent(session_id: str, limit: int = 8) -> List[Tuple[str, str]]:
    msgs = _mem.get(session_id, [])
    return msgs[-limit:]


def clear(session_id: str) -> None:
    _mem.pop(session_id, None)
