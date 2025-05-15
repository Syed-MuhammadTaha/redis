# Distributed Key-Value Store

A lightweight distributed key-value store with a RESTful API and monitoring dashboard, built with FastAPI.

## Features

- Distributed key-value storage across multiple nodes
- Key-based sharding using consistent hashing
- Data replication for fault tolerance
- RESTful API with FastAPI
- Basic monitoring dashboard
- Swagger UI documentation

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start the nodes:
```bash
chmod +x run_nodes.sh
./run_nodes.sh
```

This will start three nodes on ports 8000, 8001, and 8002.

## Running the Dashboard

To run the frontend monitoring dashboard:

1. Navigate to the dashboard directory:
```bash
cd dashboard
```

2. Install Node.js dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm start
```

The dashboard will be available at http://localhost:3000

## API Endpoints

### Key-Value Operations

- `PUT /store/{key}` - Create or update a value
- `GET /store/{key}` - Retrieve a value
- `DELETE /store/{key}` - Delete a key-value pair

### Monitoring

- `GET /status` - Get node status (uptime, key count)
- `GET /keys` - List all keys on the node
- `GET /node-info` - Get detailed node information

## Architecture

The system uses a distributed architecture with the following components:

1. **Storage Layer**: In-memory key-value store
2. **Node Manager**: Handles node discovery and request forwarding
3. **FastAPI Server**: RESTful API interface
4. **Replication**: Data is replicated across multiple nodes for fault tolerance

## Testing the API

You can test the API using the Swagger UI at:
http://localhost:8000/docs

Or using curl:

```bash
# Store a value
curl -X PUT "http://localhost:8000/store/mykey" -H "Content-Type: application/json" -d '{"value": "test"}'

# Retrieve a value
curl "http://localhost:8000/store/mykey"

# Delete a value
curl -X DELETE "http://localhost:8000/store/mykey"
```

## Monitoring

Each node exposes monitoring endpoints that provide:
- Node status and health
- Key distribution
- Uptime statistics
- Replication status

## License

MIT 