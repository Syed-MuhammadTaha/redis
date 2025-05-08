import hashlib
from typing import Dict, List, Set, Optional
import logging

class ShardManager:
    def __init__(self, node_id: str, num_shards: int = 10):
        self.node_id = node_id
        self.num_shards = num_shards
        self.shard_allocation: Dict[int, str] = {}  # shard_id -> node_id
        self.owned_shards: Set[int] = set()
        self.logger = logging.getLogger(f"shard-manager-{node_id}")

    def calculate_shard(self, key: str) -> int:
        """Calculate which shard a key belongs to."""
        hash_value = int(hashlib.md5(key.encode()).hexdigest(), 16)
        return hash_value % self.num_shards

    def assign_initial_shards(self, nodes: List[str]):
        """Assign shards to nodes using consistent hashing."""
        for shard_id in range(self.num_shards):
            # Simple round-robin assignment for now
            node_idx = shard_id % len(nodes)
            assigned_node = nodes[node_idx]
            self.shard_allocation[shard_id] = assigned_node
            if assigned_node == self.node_id:
                self.owned_shards.add(shard_id)
        
        self.logger.info(f"Node {self.node_id} owns shards: {self.owned_shards}")

    def owns_key(self, key: str) -> bool:
        """Check if this node owns the shard containing the key."""
        shard_id = self.calculate_shard(key)
        return shard_id in self.owned_shards

    def get_owner(self, key: str) -> Optional[str]:
        """Get the node that owns the shard containing the key."""
        shard_id = self.calculate_shard(key)
        return self.shard_allocation.get(shard_id)

    def add_shard(self, shard_id: int):
        """Add a shard to this node's ownership."""
        self.owned_shards.add(shard_id)
        self.shard_allocation[shard_id] = self.node_id
        self.logger.info(f"Node {self.node_id} now owns shard {shard_id}")

    def remove_shard(self, shard_id: int):
        """Remove a shard from this node's ownership."""
        self.owned_shards.discard(shard_id)
        if self.shard_allocation.get(shard_id) == self.node_id:
            del self.shard_allocation[shard_id]
        self.logger.info(f"Node {self.node_id} no longer owns shard {shard_id}")

    def rebalance_shards(self, nodes: List[str]):
        """Rebalance shards across nodes."""
        target_shards_per_node = self.num_shards // len(nodes)
        
        # Find overloaded and underloaded nodes
        node_shards = {node: [] for node in nodes}
        for shard_id, node in self.shard_allocation.items():
            node_shards[node].append(shard_id)
        
        # Move shards from overloaded to underloaded nodes
        for source_node, shards in node_shards.items():
            while len(shards) > target_shards_per_node:
                for target_node, target_shards in node_shards.items():
                    if len(target_shards) < target_shards_per_node:
                        shard_to_move = shards.pop()
                        target_shards.append(shard_to_move)
                        self.shard_allocation[shard_to_move] = target_node
                        
                        if source_node == self.node_id:
                            self.owned_shards.discard(shard_to_move)
                        if target_node == self.node_id:
                            self.owned_shards.add(shard_to_move)
                        
                        self.logger.info(f"Moving shard {shard_to_move} from {source_node} to {target_node}")
                        break 