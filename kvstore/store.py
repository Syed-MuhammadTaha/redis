import threading
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Value:
    data: str
    timestamp: datetime
    version: int

class KVStore:
    def __init__(self):
        self._store: Dict[str, Value] = {}
        self._lock = threading.RLock()
        self._version_counter = 0

    def get(self, key: str) -> Tuple[Optional[str], bool]:
        """Get a value from the store."""
        with self._lock:
            if key in self._store:
                return self._store[key].data, True
            return None, False

    def put(self, key: str, value: str) -> bool:
        """Put a value into the store."""
        with self._lock:
            self._version_counter += 1
            self._store[key] = Value(
                data=value,
                timestamp=datetime.utcnow(),
                version=self._version_counter
            )
            return True

    def delete(self, key: str) -> bool:
        """Delete a value from the store."""
        with self._lock:
            if key in self._store:
                del self._store[key]
                return True
            return False

    def get_all(self) -> Dict[str, str]:
        """Get all key-value pairs."""
        with self._lock:
            return {k: v.data for k, v in self._store.items()}

    def get_version(self, key: str) -> Optional[int]:
        """Get the version of a key."""
        with self._lock:
            if key in self._store:
                return self._store[key].version
            return None 