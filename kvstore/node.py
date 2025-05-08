import grpc
from concurrent import futures
import logging
from typing import List, Dict, Optional, Tuple
import time

from .store import KVStore
from .utils import setup_logging
from .consensus import ConsensusModule
from .sharding import ShardManager
from .auth import AuthManager

# Import generated gRPC code
import proto.kvstore_pb2 as kvstore_pb2
import proto.kvstore_pb2_grpc as kvstore_pb2_grpc

class KVStoreServicer(kvstore_pb2_grpc.KVStoreServicer):
    def __init__(self, node_id: str, peers: List[str]):
        self.node_id = node_id
        self.peers = peers
        self.store = KVStore()
        self.logger = setup_logging(f"node-{node_id}")
        
        # Initialize consensus module
        self.consensus = ConsensusModule(node_id, peers)
        
        # Initialize sharding manager
        self.shard_manager = ShardManager(node_id)
        self.shard_manager.assign_initial_shards([node_id] + peers)
        
        # Initialize auth manager
        self.auth_manager = AuthManager()
        # Add a default API key for demo purposes
        self.auth_manager.add_api_key("demo-key", "admin")

    def Authenticate(self, request, context):
        success, token, error = self.auth_manager.authenticate(request.api_key)
        return kvstore_pb2.AuthResponse(
            success=success,
            token=token if token else "",
            error=error if error else ""
        )

    def _validate_auth(self, auth_token: str) -> Tuple[bool, Optional[str]]:
        """Validate authentication token."""
        valid, error = self.auth_manager.validate_token(auth_token)
        if not valid:
            return False, error
        return True, None

    def Get(self, request, context):
        # Validate authentication
        valid, error = self._validate_auth(request.auth_token)
        if not valid:
            return kvstore_pb2.GetResponse(found=False, error=error)

        # Check if this node owns the key's shard
        if not self.shard_manager.owns_key(request.key):
            owner = self.shard_manager.get_owner(request.key)
            return kvstore_pb2.GetResponse(
                found=False,
                error=f"Key belongs to node {owner}"
            )

        value, found = self.store.get(request.key)
        version = self.store.get_version(request.key) if found else 0
        return kvstore_pb2.GetResponse(
            value=value if value else "",
            found=found,
            version=version
        )

    def Put(self, request, context):
        # Validate authentication
        valid, error = self._validate_auth(request.auth_token)
        if not valid:
            return kvstore_pb2.PutResponse(success=False, error=error)

        # Only leader can accept writes
        if not self.consensus.is_leader:
            return kvstore_pb2.PutResponse(
                success=False,
                error=f"Not leader. Current leader: {self.consensus.leader_id}"
            )

        # Check if this node owns the key's shard
        if not self.shard_manager.owns_key(request.key):
            owner = self.shard_manager.get_owner(request.key)
            return kvstore_pb2.PutResponse(
                success=False,
                error=f"Key belongs to node {owner}"
            )

        # Check version for conflicts
        current_version = self.store.get_version(request.key)
        if current_version and request.version and current_version != request.version:
            return kvstore_pb2.PutResponse(
                success=False,
                error="Version conflict",
                new_version=current_version
            )

        success = self.store.put(request.key, request.value)
        new_version = self.store.get_version(request.key)
        
        # Replicate to peers
        self._replicate_to_peers(request.key, request.value, "PUT")
        
        return kvstore_pb2.PutResponse(
            success=success,
            new_version=new_version
        )

    def Delete(self, request, context):
        # Validate authentication
        valid, error = self._validate_auth(request.auth_token)
        if not valid:
            return kvstore_pb2.DeleteResponse(success=False, error=error)

        # Only leader can accept writes
        if not self.consensus.is_leader:
            return kvstore_pb2.DeleteResponse(
                success=False,
                error=f"Not leader. Current leader: {self.consensus.leader_id}"
            )

        # Check if this node owns the key's shard
        if not self.shard_manager.owns_key(request.key):
            owner = self.shard_manager.get_owner(request.key)
            return kvstore_pb2.DeleteResponse(
                success=False,
                error=f"Key belongs to node {owner}"
            )

        success = self.store.delete(request.key)
        
        # Replicate to peers
        self._replicate_to_peers(request.key, "", "DELETE")
        
        return kvstore_pb2.DeleteResponse(success=success)

    def RequestVote(self, request, context):
        vote_granted = self.consensus.handle_request_vote(
            request.candidate_id,
            request.term
        )
        return kvstore_pb2.VoteResponse(
            vote_granted=vote_granted,
            term=self.consensus.current_term
        )

    def AppendEntries(self, request, context):
        success = self.consensus.handle_append_entries(
            request.term,
            request.leader_id
        )
        return kvstore_pb2.AppendEntriesResponse(
            success=success,
            term=self.consensus.current_term
        )

    def Replicate(self, request, context):
        if request.operation == "PUT":
            success = self.store.put(request.key, request.value)
        else:  # DELETE
            success = self.store.delete(request.key)
        return kvstore_pb2.ReplicateResponse(success=success)

    def HealthCheck(self, request, context):
        return kvstore_pb2.HealthResponse(healthy=True, status="OK")

    def _replicate_to_peers(self, key: str, value: str, operation: str):
        """Replicate changes to peer nodes that own the same shard."""
        shard_id = self.shard_manager.calculate_shard(key)
        for peer in self.peers:
            try:
                with grpc.insecure_channel(peer) as channel:
                    stub = kvstore_pb2_grpc.KVStoreStub(channel)
                    request = kvstore_pb2.ReplicateRequest(
                        key=key,
                        value=value,
                        operation=operation
                    )
                    stub.Replicate(request)
            except Exception as e:
                self.logger.error(f"Failed to replicate to peer {peer}: {e}")

class Node:
    def __init__(self, node_id: str, host: str, port: int, peers: List[str]):
        self.node_id = node_id
        self.address = f"{host}:{port}"
        self.peers = peers
        self.server = None
        self.logger = setup_logging(f"node-{node_id}")
        self.servicer = None

    def start(self):
        """Start the gRPC server and consensus module."""
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        self.servicer = KVStoreServicer(self.node_id, self.peers)
        kvstore_pb2_grpc.add_KVStoreServicer_to_server(self.servicer, self.server)
        self.server.add_insecure_port(self.address)
        self.server.start()
        
        # Start consensus module
        self.servicer.consensus.start()
        
        self.logger.info(f"Node {self.node_id} started on {self.address}")

    def stop(self):
        """Stop the gRPC server and consensus module."""
        if self.servicer:
            self.servicer.consensus.stop()
        if self.server:
            self.server.stop(0)
            self.logger.info(f"Node {self.node_id} stopped") 