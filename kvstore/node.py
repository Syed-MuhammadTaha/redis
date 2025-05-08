import grpc
from concurrent import futures
import logging
from typing import List, Dict, Optional
import time

from .store import KVStore
from .utils import setup_logging

# Import generated gRPC code
import proto.kvstore_pb2 as kvstore_pb2
import proto.kvstore_pb2_grpc as kvstore_pb2_grpc

class KVStoreServicer(kvstore_pb2_grpc.KVStoreServicer):
    def __init__(self, node_id: str, peers: List[str]):
        self.node_id = node_id
        self.peers = peers
        self.store = KVStore()
        self.logger = setup_logging(f"node-{node_id}")

    def Get(self, request, context):
        value, found = self.store.get(request.key)
        return kvstore_pb2.GetResponse(value=value if value else "", found=found)

    def Put(self, request, context):
        success = self.store.put(request.key, request.value)
        # Replicate to peers
        self._replicate_to_peers(request.key, request.value, "PUT")
        return kvstore_pb2.PutResponse(success=success)

    def Delete(self, request, context):
        success = self.store.delete(request.key)
        # Replicate to peers
        self._replicate_to_peers(request.key, "", "DELETE")
        return kvstore_pb2.DeleteResponse(success=success)

    def Replicate(self, request, context):
        if request.operation == "PUT":
            success = self.store.put(request.key, request.value)
        else:  # DELETE
            success = self.store.delete(request.key)
        return kvstore_pb2.ReplicateResponse(success=success)

    def HealthCheck(self, request, context):
        return kvstore_pb2.HealthResponse(healthy=True, status="OK")

    def _replicate_to_peers(self, key: str, value: str, operation: str):
        """Replicate changes to peer nodes."""
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

    def start(self):
        """Start the gRPC server."""
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        servicer = KVStoreServicer(self.node_id, self.peers)
        kvstore_pb2_grpc.add_KVStoreServicer_to_server(servicer, self.server)
        self.server.add_insecure_port(self.address)
        self.server.start()
        self.logger.info(f"Node {self.node_id} started on {self.address}")

    def stop(self):
        """Stop the gRPC server."""
        if self.server:
            self.server.stop(0)
            self.logger.info(f"Node {self.node_id} stopped") 