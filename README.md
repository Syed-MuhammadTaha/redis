# Distributed Key-Value Store with Dashboard

A lightweight distributed key-value store implementation with a monitoring dashboard, built using FastAPI and modern web technologies.

## Features

- Distributed key-value store with multiple nodes
- Key-based sharding using consistent hashing
- RESTful API for CRUD operations
- Real-time monitoring dashboard
- Node health monitoring
- Key distribution visualization

## Prerequisites

- Python 3.8+
- Node.js 14+ (for development)
- Modern web browser

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd distributed-kv-store
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

## Running the System

1. Make the run script executable:
```bash
chmod +x run_nodes.sh
```

2. Start the nodes:
```bash
./run_nodes.sh
```

This will start three nodes on ports 8001, 8002, and 8003.

## Accessing the Dashboard

Open your web browser and navigate to:
- Node 1: http://localhost:8001/dashboard
- Node 2: http://localhost:8002/dashboard
- Node 3: http://localhost:8003/dashboard

## API Endpoints

### Key-Value Operations

- `PUT /store/{key}` - Create or update a value
- `GET /store/{key}` - Retrieve a value
- `DELETE /store/{key}` - Delete a key-value pair

### Monitoring

- `GET /status` - Get node status
- `GET /keys` - Get all keys stored on the node
- `GET /node-info` - Get node system information

## Architecture

The system consists of the following components:

1. **Node Manager**: Handles node discovery and request forwarding
2. **Storage Engine**: In-memory key-value store
3. **Status Monitor**: Tracks node health and metrics
4. **Dashboard**: Real-time monitoring UI

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License 