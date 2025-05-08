#!/bin/bash

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Generate gRPC code
echo "Generating gRPC code..."
python -m grpc_tools.protoc -I./proto --python_out=. --grpc_python_out=. ./proto/kvstore.proto

# Start the cluster
echo "Starting the cluster..."
python scripts/start_cluster.py 