#!/usr/bin/env python3
import os
import sys
import time
import grpc
import argparse
from typing import List
from rich.console import Console
from rich.table import Table

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

    def _create_stubs(self) -> List[kvstore_pb2_grpc.KVStoreStub]:
        """Create gRPC stubs for all nodes."""
        stubs = []
        for node in self.config["nodes"]:
            channel = grpc.insecure_channel(f"{node['host']}:{node['port']}")
            stub = kvstore_pb2_grpc.KVStoreStub(channel)
            stubs.append(stub)
        return stubs

    def demo_crud_operations(self):
        """Demonstrate CRUD operations across nodes."""
        self.console.print("\n[bold blue]Starting CRUD Operations Demo[/bold blue]")
        
        # Test data
        test_data = [
            ("key1", "value1"),
            ("key2", "value2"),
            ("key3", "value3")
        ]

        # PUT operations
        self.console.print("\n[bold green]PUT Operations:[/bold green]")
        for key, value in test_data:
            self.console.print(f"\nPutting {key}={value} on node 1")
            response = self.stubs[0].Put(kvstore_pb2.PutRequest(key=key, value=value))
            if response.success:
                self.console.print(f"[green]Successfully put {key}={value}[/green]")
            time.sleep(1)  # Small delay for visibility

        # GET operations from all nodes
        self.console.print("\n[bold green]GET Operations:[/bold green]")
        for i, stub in enumerate(self.stubs):
            self.console.print(f"\nReading from node {i+1}:")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Key")
            table.add_column("Value")
            table.add_column("Found")

            for key, _ in test_data:
                response = stub.Get(kvstore_pb2.GetRequest(key=key))
                table.add_row(key, response.value, str(response.found))
            
            self.console.print(table)

        # DELETE operation
        key_to_delete = "key2"
        self.console.print(f"\n[bold green]DELETE Operation:[/bold green]")
        self.console.print(f"\nDeleting {key_to_delete} from node 1")
        response = self.stubs[0].Delete(kvstore_pb2.DeleteRequest(key=key_to_delete))
        if response.success:
            self.console.print(f"[green]Successfully deleted {key_to_delete}[/green]")
        time.sleep(1)

        # Verify deletion across nodes
        self.console.print("\n[bold green]Verifying Deletion:[/bold green]")
        for i, stub in enumerate(self.stubs):
            self.console.print(f"\nChecking node {i+1}:")
            response = stub.Get(kvstore_pb2.GetRequest(key=key_to_delete))
            self.console.print(f"Key {key_to_delete}: {'Found' if response.found else 'Not Found'}")

def main():
    parser = argparse.ArgumentParser(description="Demo CRUD operations across KV store nodes")
    parser.add_argument("--config", default="config/nodes.json",
                      help="Path to the cluster configuration file")
    args = parser.parse_args()

    client = DemoClient(args.config)
    client.demo_crud_operations()

if __name__ == "__main__":
    main() 