#!/usr/bin/env python3
import os
import sys
import time
import grpc
import argparse
from typing import List, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import proto.kvstore_pb2 as kvstore_pb2
import proto.kvstore_pb2_grpc as kvstore_pb2_grpc
from kvstore.utils import setup_logging, load_config

class DemoClient:
    def __init__(self, config_path: str):
        self.logger = setup_logging("demo-client")
        self.config = load_config(config_path)
        self.console = Console()
        self.stubs = self._create_stubs()
        self.auth_token = None

    def _create_stubs(self) -> List[kvstore_pb2_grpc.KVStoreStub]:
        """Create gRPC stubs for all nodes."""
        stubs = []
        for node in self.config["nodes"]:
            channel = grpc.insecure_channel(f"{node['host']}:{node['port']}")
            stub = kvstore_pb2_grpc.KVStoreStub(channel)
            stubs.append(stub)
        return stubs

    def authenticate(self):
        """Authenticate with the cluster."""
        self.console.print("\n[bold blue]Authentication Demo[/bold blue]")
        
        # Try to authenticate with the demo key
        response = self.stubs[0].Authenticate(
            kvstore_pb2.AuthRequest(api_key="demo-key")
        )
        
        if response.success:
            self.auth_token = response.token
            self.console.print("[green]Successfully authenticated with demo key[/green]")
        else:
            self.console.print(f"[red]Authentication failed: {response.error}[/red]")
            sys.exit(1)

    def find_leader(self) -> Optional[int]:
        """Find the current leader node."""
        for i, stub in enumerate(self.stubs):
            try:
                response = stub.GetMetadata(kvstore_pb2.MetadataRequest())
                if response.role == "leader":
                    return i
            except Exception:
                continue
        return None

    def demo_crud_operations(self):
        """Demonstrate CRUD operations across nodes."""
        # First authenticate
        self.authenticate()
        
        self.console.print("\n[bold blue]Starting CRUD Operations Demo[/bold blue]")
        
        # Find leader
        leader_idx = self.find_leader()
        if leader_idx is not None:
            self.console.print(f"\n[green]Found leader: Node {leader_idx + 1}[/green]")
        else:
            self.console.print("\n[yellow]Warning: No leader found, cluster may be in election[/yellow]")
        
        # Test data for different shards
        test_data = [
            ("key1", "value1"),
            ("key2", "value2"),
            ("key3", "value3"),
            ("key4", "value4"),
            ("key5", "value5")
        ]

        # PUT operations
        self.console.print("\n[bold green]PUT Operations:[/bold green]")
        versions = {}
        for key, value in test_data:
            self.console.print(f"\nPutting {key}={value}")
            
            # Try all nodes until we find the one that owns the shard
            success = False
            for i, stub in enumerate(self.stubs):
                try:
                    response = stub.Put(kvstore_pb2.PutRequest(
                        key=key,
                        value=value,
                        auth_token=self.auth_token
                    ))
                    if response.success:
                        success = True
                        versions[key] = response.new_version
                        self.console.print(f"[green]Successfully put {key}={value} on node {i+1} (version: {response.new_version})[/green]")
                        break
                    elif "belongs to node" in response.error:
                        continue
                    else:
                        self.console.print(f"[red]Failed to put on node {i+1}: {response.error}[/red]")
                except Exception as e:
                    self.console.print(f"[red]Error on node {i+1}: {e}[/red]")
            
            if not success:
                self.console.print(f"[red]Failed to put {key}={value} on any node[/red]")
            
            time.sleep(1)  # Small delay for visibility

        # GET operations from all nodes
        self.console.print("\n[bold green]GET Operations:[/bold green]")
        for i, stub in enumerate(self.stubs):
            self.console.print(f"\nReading from node {i+1}:")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Key")
            table.add_column("Value")
            table.add_column("Found")
            table.add_column("Version")
            table.add_column("Error")

            for key, _ in test_data:
                try:
                    response = stub.Get(kvstore_pb2.GetRequest(
                        key=key,
                        auth_token=self.auth_token
                    ))
                    table.add_row(
                        key,
                        response.value,
                        str(response.found),
                        str(response.version),
                        response.error or ""
                    )
                except Exception as e:
                    table.add_row(key, "", "False", "0", str(e))
            
            self.console.print(table)

        # Demonstrate version conflict
        if test_data:
            key, _ = test_data[0]
            if key in versions:
                self.console.print("\n[bold yellow]Demonstrating Version Conflict:[/bold yellow]")
                old_version = versions[key] - 1
                response = self.stubs[0].Put(kvstore_pb2.PutRequest(
                    key=key,
                    value="conflict_value",
                    auth_token=self.auth_token,
                    version=old_version
                ))
                if not response.success and "conflict" in response.error:
                    self.console.print("[green]Successfully detected version conflict[/green]")
                else:
                    self.console.print("[red]Version conflict test failed[/red]")

        # DELETE operation
        key_to_delete = "key2"
        self.console.print(f"\n[bold green]DELETE Operation:[/bold green]")
        success = False
        for i, stub in enumerate(self.stubs):
            try:
                response = stub.Delete(kvstore_pb2.DeleteRequest(
                    key=key_to_delete,
                    auth_token=self.auth_token
                ))
                if response.success:
                    success = True
                    self.console.print(f"[green]Successfully deleted {key_to_delete} on node {i+1}[/green]")
                    break
                elif "belongs to node" in response.error:
                    continue
                else:
                    self.console.print(f"[red]Failed to delete on node {i+1}: {response.error}[/red]")
            except Exception as e:
                self.console.print(f"[red]Error on node {i+1}: {e}[/red]")
        
        if not success:
            self.console.print(f"[red]Failed to delete {key_to_delete} on any node[/red]")

        time.sleep(1)

        # Verify deletion across nodes
        self.console.print("\n[bold green]Verifying Deletion:[/bold green]")
        for i, stub in enumerate(self.stubs):
            try:
                response = stub.Get(kvstore_pb2.GetRequest(
                    key=key_to_delete,
                    auth_token=self.auth_token
                ))
                status = "Not Found" if not response.found else f"Found (Error: {response.error})"
                self.console.print(f"Node {i+1}: {status}")
            except Exception as e:
                self.console.print(f"[red]Error on node {i+1}: {e}[/red]")

def main():
    parser = argparse.ArgumentParser(description="Demo CRUD operations across KV store nodes")
    parser.add_argument("--config", default="config/nodes.json",
                      help="Path to the cluster configuration file")
    args = parser.parse_args()

    client = DemoClient(args.config)
    client.demo_crud_operations()

if __name__ == "__main__":
    main() 