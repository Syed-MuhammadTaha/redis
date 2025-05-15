import hashlib
import aiohttp
from typing import Dict, Any, Optional, List
import json
from hash_ring import HashRing

class NodeManager:
    def __init__(self, nodes: Dict[str, Dict[str, Any]], current_node: str, replicas: int = 100):
        self.nodes = nodes
        self.current_node = current_node
        self.hash_ring = HashRing(nodes, replicas)
        
        # For replication
        self.replication_factor = 2  # Store on primary + 1 backup
    
    def get_node_for_key(self, key: str) -> str:
        """Determine which node should handle a given key"""
        return self.hash_ring.get_node(key)
    
    def get_replica_nodes(self, key: str) -> List[str]:
        """Get all nodes that should store this key (primary + replicas)"""
        return self.hash_ring.get_nodes(key, self.replication_factor)
    
    async def forward_request(self, method: str, path: str, target_node: str, data: Optional[Dict] = None) -> Dict:
        """Forward a request to the appropriate node"""
        target_host = self.nodes[target_node]["host"]
        target_port = self.nodes[target_node]["port"]
        url = f"http://{target_host}:{target_port}{path}"
        
        async with aiohttp.ClientSession() as session:
            try:
                if method == "GET":
                    async with session.get(url) as response:
                        return await response.json()
                elif method == "PUT":
                    # For PUT requests, we need to replicate to backup nodes
                    if path.startswith("/store/"):
                        key = path.split("/")[-1]
                        replica_nodes = self.get_replica_nodes(key)
                        
                        # Store on all replica nodes
                        results = []
                        for node in replica_nodes:
                            if node != target_node:  # Skip if we've already stored on this node
                                replica_url = f"http://{self.nodes[node]['host']}:{self.nodes[node]['port']}{path}"
                                async with session.put(replica_url, json=data) as response:
                                    results.append(await response.json())
                        
                        # Return success if at least one replica succeeded
                        return {"message": "Value stored successfully", "replicas": len(results) + 1}
                    else:
                        async with session.put(url, json=data) as response:
                            return await response.json()
                elif method == "DELETE":
                    # For DELETE requests, we need to remove from all replicas
                    if path.startswith("/store/"):
                        key = path.split("/")[-1]
                        replica_nodes = self.get_replica_nodes(key)
                        
                        # Delete from all replica nodes
                        results = []
                        for node in replica_nodes:
                            if node != target_node:  # Skip if we've already deleted from this node
                                replica_url = f"http://{self.nodes[node]['host']}:{self.nodes[node]['port']}{path}"
                                async with session.delete(replica_url) as response:
                                    results.append(await response.json())
                        
                        return {"message": "Key deleted successfully", "replicas": len(results) + 1}
                    else:
                        async with session.delete(url) as response:
                            return await response.json()
                else:
                    raise ValueError(f"Unsupported method: {method}")
            except aiohttp.ClientError as e:
                return {"error": f"Failed to forward request: {str(e)}"}
    
    def get_all_nodes(self) -> Dict[str, Dict[str, Any]]:
        """Return information about all nodes"""
        return self.nodes 