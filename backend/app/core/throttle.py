"""Login brute-force guard (in memory, per process): too many failures lock the username+address for a while."""
import time
from collections import defaultdict

LIMIT, WINDOW, LOCK = 5, 300, 300
_fails: dict[str, list[float]] = defaultdict(list)
_locked: dict[str, float] = {}


def blocked(key: str) -> int:
    """Seconds left on the lock, or 0."""
    until = _locked.get(key, 0)
    if until > time.time():
        return int(until - time.time()) + 1
    _locked.pop(key, None)
    return 0


def failed(key: str) -> None:
    now = time.time()
    f = [t for t in _fails[key] if now - t < WINDOW] + [now]
    _fails[key] = f
    if len(f) >= LIMIT:
        _locked[key] = now + LOCK
        _fails.pop(key, None)


def ok(key: str) -> None:
    _fails.pop(key, None)
    _locked.pop(key, None)


def reset() -> None:
    _fails.clear()
    _locked.clear()
