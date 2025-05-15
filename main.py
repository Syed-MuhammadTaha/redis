from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import time
import os
from typing import Dict, Optional
from datetime import datetime

# Import our custom modules
from storage import KeyValueStore
from node_manager import NodeManager
from status import NodeStatus

app = FastAPI(title="Distributed Key-Value Store")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
start_time = time.time()
store = KeyValueStore()
node_status = NodeStatus()

# Load config and setup node manager
with open("config.json") as f:
    config = json.load(f)
    current_node = os.environ.get("NODE_ID", "node_1")
    node_manager = NodeManager(config["nodes"], current_node)

# Mount static files for dashboard
app.mount("/dashboard", StaticFiles(directory="dashboard", html=True), name="dashboard")

@app.get("/")
async def read_root():
    return {"message": "Distributed Key-Value Store", "node_id": current_node}

@app.put("/store/{key}")
async def put_value(key: str, value: str):
    target_node = node_manager.get_node_for_key(key)
    
    if target_node == current_node:
        store.put(key, value)
        return {"message": "Value stored successfully"}
    else:
        # Forward request to correct node
        return await node_manager.forward_request("PUT", f"/store/{key}?value={value}", target_node)

@app.get("/store/{key}")
async def get_value(key: str):
    target_node = node_manager.get_node_for_key(key)
    
    if target_node == current_node:
        value = store.get(key)
        if value is None:
            raise HTTPException(status_code=404, detail="Key not found")
        return {"key": key, "value": value}
    else:
        # Forward request to correct node
        return await node_manager.forward_request("GET", f"/store/{key}", target_node)

@app.delete("/store/{key}")
async def delete_value(key: str):
    target_node = node_manager.get_node_for_key(key)
    
    if target_node == current_node:
        if store.delete(key):
            return {"message": "Key deleted successfully"}
        raise HTTPException(status_code=404, detail="Key not found")
    else:
        # Forward request to correct node
        return await node_manager.forward_request("DELETE", f"/store/{key}", target_node)

@app.get("/status")
async def get_status():
    uptime = int(time.time() - start_time)
    return {
        "node_id": current_node,
        "status": "healthy",
        "uptime": f"{uptime}s",
        "key_count": store.count(),
        "host": config["nodes"][current_node]["host"],
        "port": config["nodes"][current_node]["port"]
    }

@app.get("/keys")
async def get_keys():
    return {"keys": store.get_all_keys()}

@app.get("/node-info")
async def get_node_info():
    return {
        "memory_usage": node_status.get_memory_usage(),
        "cpu_usage": node_status.get_cpu_usage(),
        "last_operation_time": node_status.get_last_operation_time()
    }

if __name__ == "__main__":
    import uvicorn
    port = config["nodes"][current_node]["port"]
    uvicorn.run(app, host="0.0.0.0", port=port) 