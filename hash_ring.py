import hashlib
from typing import List, Dict, Any
from bisect import bisect

class HashRing:
    """Consistent Hashing Ring implementation"""
    
    def __init__(self, nodes: Dict[str, Dict[str, Any]], replicas: int = 100):
        """
        Initialize the hash ring with nodes and virtual node replicas
        
        Args:
            nodes: Dictionary of node IDs to node info
            replicas: Number of virtual nodes per real node
        """
        self.replicas = replicas
        self.ring = {}  # Hash value -> node mapping
        self.sorted_keys = []  # Sorted list of hash values
        
        for node_id in nodes.keys():
            self.add_node(node_id)
    
    def get_hash(self, key: str) -> int:
        """Generate a hash value for a key"""
        big_hash = hashlib.md5(key.encode()).hexdigest()
        return int(big_hash, 16)
    
    def add_node(self, node_id: str) -> None:
        """Add a node to the hash ring"""
        for i in range(self.replicas):
            hash_key = self.get_hash(f"{node_id}:{i}")
            self.ring[hash_key] = node_id
            self.sorted_keys.append(hash_key)
        
        self.sorted_keys.sort()
    
    def remove_node(self, node_id: str) -> None:
        """Remove a node from the hash ring"""
        for i in range(self.replicas):
            hash_key = self.get_hash(f"{node_id}:{i}")
            del self.ring[hash_key]
            self.sorted_keys.remove(hash_key)
    
    def get_node(self, key: str) -> str:
        """Get the node responsible for a key"""
        if not self.ring:
            raise ValueError("Hash ring is empty")
        
        hash_key = self.get_hash(key)
        
        # Find the first point in the ring after hash_key
        idx = bisect(self.sorted_keys, hash_key)
        if idx == len(self.sorted_keys):
            idx = 0
        
        return self.ring[self.sorted_keys[idx]]
    
    def get_nodes(self, key: str, count: int) -> List[str]:
        """Get multiple nodes for replication"""
        if count > len(self.ring) // self.replicas:
            raise ValueError("Not enough nodes for requested replication")
        
        nodes = []
        hash_key = self.get_hash(key)
        
        # Start from the first point after hash_key
        idx = bisect(self.sorted_keys, hash_key)
        if idx == len(self.sorted_keys):
            idx = 0
        
        # Collect unique nodes
        seen = set()
        while len(nodes) < count:
            node = self.ring[self.sorted_keys[idx]]
            if node not in seen:
                nodes.append(node)
                seen.add(node)
            idx = (idx + 1) % len(self.sorted_keys)
        
        return nodes 