#!/usr/bin/env python3
import os
import sys
import json
import time
import signal
import subprocess
from typing import List, Dict
import argparse

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kvstore.utils import setup_logging, load_config

class ClusterManager:
    def __init__(self, config_path: str):
        self.logger = setup_logging("cluster-manager")
        self.config = load_config(config_path)
        self.nodes: List[subprocess.Popen] = []

    def start_nodes(self):
        """Start all nodes defined in the configuration."""
        for node_config in self.config["nodes"]:
            node_id = node_config["id"]
            host = node_config["host"]
            port = node_config["port"]
            peers = [f"{p['host']}:{p['port']}" for p in self.config["nodes"] 
                    if p["id"] != node_id]

            # Start node process
            cmd = [
                sys.executable,
                "-m", "kvstore.node",
                "--node-id", node_id,
                "--host", host,
                "--port", str(port),
                "--peers", ",".join(peers)
            ]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.nodes.append(process)
            self.logger.info(f"Started node {node_id} on {host}:{port}")

    def stop_nodes(self):
        """Stop all running nodes."""
        for process in self.nodes:
            process.terminate()
            process.wait()
        self.logger.info("All nodes stopped")

def main():
    parser = argparse.ArgumentParser(description="Start a cluster of KV store nodes")
    parser.add_argument("--config", default="config/nodes.json",
                      help="Path to the cluster configuration file")
    args = parser.parse_args()

    manager = ClusterManager(args.config)
    
    def signal_handler(signum, frame):
        manager.logger.info("Received shutdown signal")
        manager.stop_nodes()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        manager.start_nodes()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        manager.stop_nodes()

if __name__ == "__main__":
    main() 