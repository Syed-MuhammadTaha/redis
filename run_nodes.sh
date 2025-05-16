#!/bin/bash

# Function to cleanup processes
cleanup() {
    echo -e "\nShutting down nodes..."
    pkill -f "/usr/local/bin/python3 main.py"
    exit 0
}

# Set up trap for Ctrl+C
trap cleanup SIGINT

# Kill any existing Python processes
pkill -f "/usr/local/bin/python3 main.py" || true
sleep 2

# Function to start a node
start_node() {
    local node_id=$1
    local port=$2
    echo "Starting $node_id on port $port..."
    NODE_ID=$node_id /usr/local/bin/python3 main.py $node_id &
    sleep 1
    
    # Check if node is running
    if curl -s "http://127.0.0.1:$port/status" > /dev/null; then
        echo "$node_id started successfully"
    else
        echo "Warning: $node_id may not have started properly"
    fi
}

# Start nodes sequentially with health checks
cd "$(dirname "$0")"  # Ensure we're in the right directory
start_node "node_1" 8000
start_node "node_2" 8001
start_node "node_3" 8002

echo -e "\nAll nodes started. Use the following endpoints:"
echo "Node 1: http://127.0.0.1:8000"
echo "Node 2: http://127.0.0.1:8001"
echo "Node 3: http://127.0.0.1:8002"
echo
echo "Access Swagger UI at: http://127.0.0.1:8000/docs"
echo
echo "Monitor node status:"
echo "curl http://127.0.0.1:8000/status"
echo -e "\nPress Ctrl+C to terminate all nodes\n"

# Keep the script running
while true; do
    sleep 1
done 