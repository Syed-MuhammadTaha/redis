# Distributed Key-Value Store

A simple distributed key-value store implementation using gRPC for communication between nodes. This project demonstrates basic CRUD operations across multiple nodes with replication.

## Features

- Distributed key-value storage across multiple nodes
- gRPC-based communication
- Automatic replication of changes across nodes
- Thread-safe operations
- Simple CLI-based demo

## Prerequisites

- Python 3.8+
- pip (Python package manager)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd distributed_kv_store
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Generate gRPC code:
```bash
python -m grpc_tools.protoc -I./proto --python_out=. --grpc_python_out=. ./proto/kvstore.proto
```

## Running the Demo

1. Start the cluster (3 nodes):
```bash
python scripts/start_cluster.py
```

2. In a new terminal, run the CRUD demo:
```bash
python scripts/demo_crud.py
```

The demo will:
- Put some test data on node 1
- Show that the data is replicated to all nodes
- Delete a key and verify deletion across nodes

## Project Structure

```
distributed_kv_store/
│
├── README.md
├── requirements.txt
├── config/
│   └── nodes.json              # Node configuration
│
├── proto/
│   └── kvstore.proto          # gRPC definitions
│
├── kvstore/
│   ├── __init__.py
│   ├── node.py                # Node implementation
│   ├── store.py               # Key-value store logic
│   └── utils.py               # Utilities
│
└── scripts/
    ├── start_cluster.py       # Cluster bootstrap
    └── demo_crud.py           # CRUD demo
```

## Design Decisions

- Using gRPC for efficient RPC communication
- Simple replication strategy: all nodes are peers
- Thread-safe operations using RLock
- Version tracking for values
- Rich console output for demo visualization

## Limitations

- No persistence (in-memory only)
- No leader election
- No sharding
- Basic replication without conflict resolution
- No authentication/authorization

## Future Improvements

- Add persistence layer
- Implement leader election
- Add sharding support
- Implement conflict resolution
- Add authentication and authorization
- Add monitoring and metrics
- Implement proper error handling and recovery
- Add load balancing 