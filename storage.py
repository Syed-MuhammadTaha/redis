from typing import Dict, Optional, Any
from datetime import datetime
import threading
import json
import os
import logging

logger = logging.getLogger(__name__)

class Storage:
    def __init__(self):
        self._store: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self._start_time = datetime.now()
        self._node_id = os.environ.get("NODE_ID", "node_1")
        self._storage_file = f"data/{self._node_id}_storage.json"
        
        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)
        
        # Load existing data if available
        self._load_from_disk()
            
    def _load_from_disk(self) -> None:
        """Load data from disk if it exists."""
        try:
            if os.path.exists(self._storage_file):
                with open(self._storage_file, 'r') as f:
                    self._store = json.load(f)
                logger.info(f"Loaded {len(self._store)} keys from {self._storage_file}")
        except Exception as e:
            logger.error(f"Error loading data from disk: {e}")
            
    def _save_to_disk(self) -> None:
        """Save current data to disk."""
        try:
            with open(self._storage_file, 'w') as f:
                json.dump(self._store, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving data to disk: {e}")
        
    def put(self, key: str, value: Any) -> None:
        """Store a key-value pair."""
        with self._lock:
            self._store[key] = value
            self._save_to_disk()
            
    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value by key."""
        with self._lock:
            return self._store.get(key)
            
    def delete(self, key: str) -> bool:
        """Delete a key-value pair."""
        with self._lock:
            if key in self._store:
                del self._store[key]
                self._save_to_disk()
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