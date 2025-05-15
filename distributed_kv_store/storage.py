from typing import Dict, Optional, Any
from datetime import datetime
import threading

class Storage:
    def __init__(self):
        self._store: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self._start_time = datetime.now()
        
    def put(self, key: str, value: Any) -> None:
        """Store a key-value pair."""
        with self._lock:
            self._store[key] = value
            
    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value by key."""
        with self._lock:
            return self._store.get(key)
            
    def delete(self, key: str) -> bool:
        """Delete a key-value pair."""
        with self._lock:
            if key in self._store:
                del self._store[key]
                return True
            return False
            
    def get_all_keys(self) -> list[str]:
        """Get all stored keys."""
        with self._lock:
            return list(self._store.keys())
            
    def get_key_count(self) -> int:
        """Get the total number of stored keys."""
        with self._lock:
            return len(self._store)
            
    def get_uptime(self) -> str:
        """Get the storage uptime in seconds."""
        uptime = datetime.now() - self._start_time
        return f"{int(uptime.total_seconds())}s"

# Global storage instance
storage = Storage() 