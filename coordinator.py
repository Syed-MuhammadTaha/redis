import time
import json
import threading
import hashlib
from concurrent import futures

import grpc
import kv_store_pb2
import kv_store_pb2_grpc

class ConsistentHashing:
    def __init__(self, num_virtual_nodes=1024):
        self.num_virtual_nodes = num_virtual_nodes
        self.nodes = {}  # node_id -> address
        self.ring = {}  # position -> node_id
        self.lock = threading.RLock()
    
    def add_node(self, node_id, address):
        """Add a node to the hash ring"""
        with self.lock:
            self.nodes[node_id] = address
            
            for i in range(self.num_virtual_nodes):
                key = f"{node_id}:{i}"
                position = self._hash(key)
                self.ring[position] = node_id
    
    def remove_node(self, node_id):
        """Remove a node from the hash ring"""
        with self.lock:
            if node_id in self.nodes:
                address = self.nodes[node_id]
                del self.nodes[node_id]
                
                # Remove all virtual nodes
                positions_to_remove = []
                for position, n_id in self.ring.items():
                    if n_id == node_id:
                        positions_to_remove.append(position)
                
                for position in positions_to_remove:
                    del self.ring[position]
                
                return address
            return None
    
    def get_node(self, key):
        """Get the node responsible for a key"""
        with self.lock:
            if not self.ring:
                return None
            
            position = self._hash(key)
            
            # Find the first position >= hash
            for p in sorted(self.ring.keys()):
                if p >= position:
                    return self.nodes[self.ring[p]]
            
            # If we reached here, it means we need to wrap around to the first node
            return self.nodes[self.ring[sorted(self.ring.keys())[0]]]
    
    def get_nodes(self):
        """Get all nodes in the cluster"""
        with self.lock:
            return self.nodes.copy()
    
    def _hash(self, key):
        """Hash a key to a position on the ring"""
        return int(hashlib.md5(key.encode()).hexdigest(), 16) % (2**32)

class CoordinatorService(kv_store_pb2_grpc.KVStoreServicer):
    def __init__(self):
        self.consistent_hash = ConsistentHashing()
        self.node_health = {}  # node_id -> last_heartbeat_time
        self.master_nodes = set()  # Set of master node IDs
        
        # Start health check thread
        self.health_check_thread = threading.Thread(target=self._health_check_worker, daemon=True)
        self.health_check_thread.start()
    
    def _health_check_worker(self):
        """Background worker to check node health"""
        while True:
            current_time = time.time()
            nodes_to_remove = []
            
            for node_id, last_heartbeat in self.node_health.items():
                if current_time - last_heartbeat > 10:  # 10 seconds timeout
                    nodes_to_remove.append(node_id)
            
            for node_id in nodes_to_remove:
                print(f"Node {node_id} seems down, removing from cluster")
                self.consistent_hash.remove_node(node_id)
                del self.node_health[node_id]
                if node_id in self.master_nodes:
                    self.master_nodes.remove(node_id)
            
            time.sleep(5)  # Check every 5 seconds
    
    def RegisterNode(self, request, context):
        """Register a new node in the cluster"""
        self.consistent_hash.add_node(request.node_id, request.address)
        self.node_health[request.node_id] = time.time()
        
        if request.is_master:
            self.master_nodes.add(request.node_id)
        
        return kv_store_pb2_grpc.RegisterNodeResponse(
            success=True,
            cluster_info=json.dumps({
                "nodes": self.consistent_hash.get_nodes(),
                "masters": list(self.master_nodes)
            })
        )
    
    def Heartbeat(self, request, context):
        """Update node health status"""
        if request.node_id in self.node_health:
            self.node_health[request.node_id] = time.time()
            return kv_store_pb2_grpc.HeartbeatResponse(
                status="OK", 
                node_id=request.node_id,
                is_master=request.node_id in self.master_nodes
            )
        else:
            return kv_store_pb2_grpc.HeartbeatResponse(
                status="UNKNOWN_NODE", 
                node_id=request.node_id,
                is_master=False
            )
    
    def GetNodeForKey(self, request, context):
        """Find which node should handle a given key"""
        node_address = self.consistent_hash.get_node(request.key)
        if not node_address:
            return kv_store_pb2_grpc.GetNodeForKeyResponse(found=False)
        
        return kv_store_pb2_grpc.GetNodeForKeyResponse(
            found=True,
            node_address=node_address
        )
    
    def GetClusterInfo(self, request, context):
        """Get information about the current cluster state"""
        return kv_store_pb2_grpc.GetClusterInfoResponse(
            nodes=self.consistent_hash.get_nodes(),
            masters=list(self.master_nodes)
        )

def run_coordinator(port):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    coordinator = CoordinatorService()
    kv_store_pb2_grpc.add_CoordinatorServicer_to_server(coordinator, server)
    
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    
    print(f"Coordinator started on port {port}")
    
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        server.stop(0)

# Example usage:
# run_coordinator(5000)