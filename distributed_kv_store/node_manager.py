import json
import hashlib
from typing import List, Dict, Optional
import aiohttp
import asyncio
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Node:
    def __init__(self, id: str, host: str, port: int):
        self.id = id
        self.host = host
        self.port = port
        self.url = f"http://{host}:{port}"
        self.last_heartbeat = datetime.now()
        self.failed_attempts = 0
        self.max_failures = 3

    def mark_failed(self):
        self.failed_attempts += 1
        logger.warning(f"Node {self.id} failed attempt {self.failed_attempts}")

    def mark_healthy(self):
        if self.failed_attempts > 0:
            logger.info(f"Node {self.id} recovered")
        self.failed_attempts = 0
        self.last_heartbeat = datetime.now()

    @property
    def is_healthy(self):
        return self.failed_attempts < self.max_failures

class NodeManager:
    def __init__(self, config_path: str, current_node_id: str):
        self.config_path = config_path
        self.current_node_id = current_node_id
        self.nodes: Dict[str, Node] = {}
        self.load_config()
        
    def load_config(self) -> None:
        """Load node configuration from config file."""
        try:
            with open(self.config_path) as f:
                config = json.load(f)
                for node_config in config["nodes"]:
                    node = Node(
                        id=node_config["id"],
                        host=node_config["host"],
                        port=node_config["port"]
                    )
                    self.nodes[node.id] = node
            self.replication_factor = config.get("replication_factor", 1)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise
        
    def get_node_for_key(self, key: str) -> Node:
        """Determine which node should handle a given key."""
        hash_value = int(hashlib.md5(key.encode()).hexdigest(), 16)
        healthy_nodes = [n for n in self.nodes.values() if n.is_healthy]
        if not healthy_nodes:
            raise Exception("No healthy nodes available")
        node_index = hash_value % len(healthy_nodes)
        return healthy_nodes[node_index]
        
    def get_replica_nodes(self, primary_node: Node) -> List[Node]:
        """Get replica nodes for a given primary node."""
        healthy_nodes = [n for n in self.nodes.values() if n.is_healthy and n.id != primary_node.id]
        replicas = []
        
        for i in range(min(self.replication_factor - 1, len(healthy_nodes))):
            replicas.append(healthy_nodes[i])
            
        return replicas
        
    async def forward_request(self, node: Node, method: str, path: str, **kwargs) -> Optional[dict]:
        """Forward a request to another node with retry logic."""
        max_retries = 2
        retry_delay = 1  # seconds
        
        for attempt in range(max_retries + 1):
            if not node.is_healthy:
                logger.warning(f"Node {node.id} is unhealthy, skipping request")
                return None
                
            try:
                timeout = aiohttp.ClientTimeout(total=5)  # 5 seconds timeout
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.request(method, f"{node.url}{path}", **kwargs) as response:
                        if response.status == 404:
                            return None
                        if response.status >= 500:
                            raise aiohttp.ClientError(f"Server error: {response.status}")
                        node.mark_healthy()
                        return await response.json()
                        
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                node.mark_failed()
                logger.error(f"Request to node {node.id} failed: {e}")
                if attempt < max_retries:
                    await asyncio.sleep(retry_delay)
                    continue
                return None
                
    def get_all_nodes(self) -> List[Node]:
        """Get all registered nodes."""
        return list(self.nodes.values())
        
    def get_current_node(self) -> Node:
        """Get the current node instance."""
        return self.nodes[self.current_node_id]

    async def check_node_health(self, node: Node) -> bool:
        """Check if a node is healthy by pinging its status endpoint."""
        try:
            result = await self.forward_request(node, "GET", "/status")
            return result is not None
        except Exception:
            return False 