import time
import json
import threading
import os
import hashlib
from concurrent import futures

import grpc
import kv_store_pb2
import kv_store_pb2_grpc

class KeyValueStore:
    def __init__(self, persistence_file=None):
        self.store = {}
        self.ttl_map = {}  # For keys with expiration
        self.lock = threading.RLock()  # Reentrant lock for thread safety
        self.persistence_file = persistence_file
        
        # Load data from persistence file if available
        if persistence_file and os.path.exists(persistence_file):
            try:
                with open(persistence_file, 'r') as f:
                    data = json.load(f)
                    self.store = data.get('store', {})
                    self.ttl_map = {k: v for k, v in data.get('ttl_map', {}).items() 
                                   if v > time.time()}  # Only load non-expired keys
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading persistence file: {e}")
        
        # Start TTL cleanup thread
        self.cleanup_thread = threading.Thread(target=self._ttl_cleanup_worker, daemon=True)
        self.cleanup_thread.start()
    
    def _ttl_cleanup_worker(self):
        """Background worker to clean up expired keys"""
        while True:
            current_time = time.time()
            keys_to_delete = []
            
            with self.lock:
                for key, expiry_time in self.ttl_map.items():
                    if expiry_time <= current_time and key in self.store:
                        keys_to_delete.append(key)
                
                for key in keys_to_delete:
                    del self.store[key]
                    del self.ttl_map[key]
            
            self._persist_if_needed()
            time.sleep(1)  # Check every second
    
    def _persist_if_needed(self):
        """Save the current state to disk if persistence is enabled"""
        if not self.persistence_file:
            return
            
        try:
            with open(self.persistence_file, 'w') as f:
                json.dump({
                    'store': self.store,
                    'ttl_map': self.ttl_map
                }, f)
        except IOError as e:
            print(f"Error persisting data: {e}")
    
    def get(self, key):
        """Get a value by key, return None if not found or expired"""
        with self.lock:
            if key in self.ttl_map and self.ttl_map[key] <= time.time():
                # Key has expired
                del self.store[key]
                del self.ttl_map[key]
                self._persist_if_needed()
                return None
                
            return self.store.get(key)
    
    def set(self, key, value, ttl=None):
        """Set a key-value pair with optional TTL in seconds"""
        with self.lock:
            self.store[key] = value
            
            if ttl:
                self.ttl_map[key] = time.time() + ttl
            elif key in self.ttl_map:
                # Remove TTL if previously set
                del self.ttl_map[key]
                
        self._persist_if_needed()
        return True
    
    def delete(self, key):
        """Delete a key, return True if deleted, False if not found"""
        with self.lock:
            if key in self.store:
                del self.store[key]
                if key in self.ttl_map:
                    del self.ttl_map[key]
                self._persist_if_needed()
                return True
            return False
    
    def exists(self, key):
        """Check if a key exists and is not expired"""
        with self.lock:
            if key in self.ttl_map and self.ttl_map[key] <= time.time():
                # Key has expired
                del self.store[key]
                del self.ttl_map[key]
                self._persist_if_needed()
                return False
                
            return key in self.store
    
    def get_keys(self, pattern=None):
        """Get all keys, optionally filtered by a simple pattern"""
        with self.lock:
            # Clean up expired keys before returning
            current_time = time.time()
            keys_to_delete = [k for k, exp in self.ttl_map.items() 
                             if exp <= current_time and k in self.store]
            
            for key in keys_to_delete:
                del self.store[key]
                del self.ttl_map[key]
            
            if not pattern:
                return list(self.store.keys())
            
            # Simple pattern matching (supports prefix* only)
            if pattern.endswith('*'):
                prefix = pattern[:-1]
                return [k for k in self.store.keys() if k.startswith(prefix)]
            
            # Exact match
            return [k for k in self.store.keys() if k == pattern]

    def get_all(self):
        """Get all keys and values as a dictionary (for replication)"""
        with self.lock:
            # Clean up expired keys first
            current_time = time.time()
            keys_to_delete = [k for k, exp in self.ttl_map.items() 
                             if exp <= current_time and k in self.store]
            
            for key in keys_to_delete:
                del self.store[key]
                del self.ttl_map[key]
            
            # Return a copy of the store
            return self.store.copy(), {k: v - time.time() for k, v in self.ttl_map.items()}

class KVStoreServicer(kv_store_pb2_grpc.KVStoreServicer):
    def __init__(self, kv_store, node_id, is_master=False, master_address=None):
        self.kv_store = kv_store
        self.node_id = node_id
        self.is_master = is_master
        self.master_address = master_address
        self.replica_addresses = []  # List of replica addresses if master
    
    def Get(self, request, context):
        value = self.kv_store.get(request.key)
        if value is None:
            return kv_store_pb2.GetResponse(found=False)
        return kv_store_pb2.GetResponse(found=True, value=value)
    
    def Set(self, request, context):
        # If not master, forward to master
        if not self.is_master and self.master_address:
            with grpc.insecure_channel(self.master_address) as channel:
                stub = kv_store_pb2_grpc.KVStoreStub(channel)
                return stub.Set(request)
        
        # Process the set operation
        success = self.kv_store.set(request.key, request.value, 
                                   request.ttl if request.ttl > 0 else None)
        
        # If master, replicate to all replicas
        if self.is_master and success:
            for replica in self.replica_addresses:
                try:
                    with grpc.insecure_channel(replica) as channel:
                        stub = kv_store_pb2_grpc.KVStoreStub(channel)
                        replication_request = kv_store_pb2.ReplicateRequest(
                            operation="SET",
                            key=request.key,
                            value=request.value,
                            ttl=request.ttl
                        )
                        stub.Replicate(replication_request)
                except Exception as e:
                    print(f"Replication failed to {replica}: {e}")
        
        return kv_store_pb2.SetResponse(success=success)
    
    def Delete(self, request, context):
        # If not master, forward to master
        if not self.is_master and self.master_address:
            with grpc.insecure_channel(self.master_address) as channel:
                stub = kv_store_pb2_grpc.KVStoreStub(channel)
                return stub.Delete(request)
        
        # Process the delete operation
        success = self.kv_store.delete(request.key)
        
        # If master, replicate to all replicas
        if self.is_master and success:
            for replica in self.replica_addresses:
                try:
                    with grpc.insecure_channel(replica) as channel:
                        stub = kv_store_pb2_grpc.KVStoreStub(channel)
                        replication_request = kv_store_pb2.ReplicateRequest(
                            operation="DELETE",
                            key=request.key
                        )
                        stub.Replicate(replication_request)
                except Exception as e:
                    print(f"Replication failed to {replica}: {e}")
        
        return kv_store_pb2.DeleteResponse(success=success)
    
    def Exists(self, request, context):
        exists = self.kv_store.exists(request.key)
        return kv_store_pb2.ExistsResponse(exists=exists)
    
    def Keys(self, request, context):
        keys = self.kv_store.get_keys(request.pattern if request.pattern else None)
        return kv_store_pb2.KeysResponse(keys=keys)
    
    def Replicate(self, request, context):
        """Handle replication requests from the master node"""
        if request.operation == "SET":
            self.kv_store.set(request.key, request.value, 
                             request.ttl if request.ttl > 0 else None)
        elif request.operation == "DELETE":
            self.kv_store.delete(request.key)
        
        return kv_store_pb2.ReplicateResponse(success=True)
    
    def SyncData(self, request, context):
        """Full data sync for a new replica"""
        store_data, ttl_data = self.kv_store.get_all()
        return kv_store_pb2.SyncDataResponse(
            data={k: v for k, v in store_data.items()},
            ttls={k: v for k, v in ttl_data.items()}
        )
    
    def RegisterReplica(self, request, context):
        """Register a new replica with the master"""
        if not self.is_master:
            return kv_store_pb2.RegisterReplicaResponse(success=False, 
                                                      error="Not a master node")
        
        # Add to replica list if not already there
        if request.address not in self.replica_addresses:
            self.replica_addresses.append(request.address)
            print(f"New replica registered: {request.address}")
        
        return kv_store_pb2.RegisterReplicaResponse(success=True)
    
    def Heartbeat(self, request, context):
        """Simple heartbeat to check if server is alive"""
        return kv_store_pb2.HeartbeatResponse(
            status="OK", 
            node_id=self.node_id,
            is_master=self.is_master
        )

def hash_key(key):
    """Hash a key to determine which node should store it"""
    return int(hashlib.md5(key.encode()).hexdigest(), 16) % 1024  # 1024 virtual nodes

def run_server(port, node_id, is_master=False, master_address=None, persistence_file=None):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    kv_store = KeyValueStore(persistence_file)
    servicer = KVStoreServicer(kv_store, node_id, is_master, master_address)
    kv_store_pb2_grpc.add_KVStoreServicer_to_server(servicer, server)
    
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    
    print(f"Server started on port {port}, Node ID: {node_id}, "
          f"{'Master' if is_master else 'Replica'}")
    
    # If replica, register with master and sync data
    if not is_master and master_address:
        try:
            with grpc.insecure_channel(master_address) as channel:
                stub = kv_store_pb2_grpc.KVStoreStub(channel)
                
                # Register with master
                register_response = stub.RegisterReplica(
                    kv_store_pb2.RegisterReplicaRequest(address=f"localhost:{port}")
                )
                if not register_response.success:
                    print(f"Failed to register with master: {register_response.error}")
                else:
                    print(f"Successfully registered with master at {master_address}")
                
                # Sync data from master
                sync_response = stub.SyncData(kv_store_pb2.SyncDataRequest())
                
                # Apply synced data
                for key, value in sync_response.data.items():
                    ttl = sync_response.ttls.get(key, None)
                    kv_store.set(key, value, ttl)
                
                print(f"Synced {len(sync_response.data)} keys from master")
        except Exception as e:
            print(f"Failed to connect to master: {e}")
    
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        server.stop(0)

# Example usage:
# run_server(5000, "node1", is_master=True, persistence_file="master.json")
# run_server(5001, "node2", is_master=False, master_address="localhost:5000", persistence_file="replica1.json")