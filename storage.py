from typing import Dict, Optional, List
from threading import Lock

class KeyValueStore:
    def __init__(self):
        self._store: Dict[str, str] = {}
        self._lock = Lock()
    
    def put(self, key: str, value: str) -> None:
        """Store a key-value pair"""
        with self._lock:
            self._store[key] = value
    
    def get(self, key: str) -> Optional[str]:
        """Retrieve a value by key"""
        return self._store.get(key)
    
    def delete(self, key: str) -> bool:
        """Delete a key-value pair"""
        with self._lock:
            if key in self._store:
                del self._store[key]
                return True
            return False
    
    def count(self) -> int:
        """Return the number of stored keys"""
        return len(self._store)
    
    def get_all_keys(self) -> List[str]:
        """Return all stored keys"""
        return list(self._store.keys()) 