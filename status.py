import psutil
import time
from datetime import datetime

class NodeStatus:
    def __init__(self):
        self.last_operation_timestamp = time.time()
    
    def get_memory_usage(self) -> dict:
        """Get current memory usage statistics"""
        memory = psutil.virtual_memory()
        return {
            "total": memory.total,
            "available": memory.available,
            "percent": memory.percent,
            "used": memory.used
        }
    
    def get_cpu_usage(self) -> float:
        """Get current CPU usage percentage"""
        return psutil.cpu_percent(interval=1)
    
    def get_last_operation_time(self) -> str:
        """Get timestamp of last operation"""
        return datetime.fromtimestamp(self.last_operation_timestamp).isoformat()
    
    def update_last_operation(self):
        """Update the timestamp of the last operation"""
        self.last_operation_timestamp = time.time() 