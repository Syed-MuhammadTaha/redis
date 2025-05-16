from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uvicorn
import os
import sys
import logging
from fastapi.responses import JSONResponse

from storage import storage
from node_manager import NodeManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KeyValue(BaseModel):
    value: Any

class NodeStatus(BaseModel):
    node_id: str
    status: str
    uptime: str
    key_count: int
    host: str
    port: int

app = FastAPI(title="Distributed Key-Value Store")

# Enable CORS with more specific settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Explicitly allow OPTIONS
    allow_headers=["*"],
    max_age=86400,  # Cache preflight requests for 24 hours
)

# Initialize node manager
node_id = os.environ.get("NODE_ID", "node_1")
try:
    node_manager = NodeManager("config.json", node_id)
except Exception as e:
    logger.error(f"Failed to initialize node manager: {e}")
    sys.exit(1)

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception handler caught: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )

@app.get("/store/{key}")
async def get_value(key: str):
    try:
        # Determine which node should handle this key
        target_node = node_manager.get_node_for_key(key)
        logger.info(f"Get request for key '{key}' routed to node {target_node.id}")
        
        # If this is the target node, handle locally
        if target_node.id == node_id:
            value = storage.get(key)
            if value is None:
                raise HTTPException(status_code=404, detail="Key not found")
            return {"key": key, "value": value}
        
        # Forward request to target node
        response = await node_manager.forward_request(target_node, "GET", f"/store/{key}")
        if response is None:
            # Try replicas if primary node fails
            replicas = node_manager.get_replica_nodes(target_node)
            logger.info(f"Primary node failed, trying {len(replicas)} replicas")
            for replica in replicas:
                response = await node_manager.forward_request(replica, "GET", f"/store/{key}")
                if response is not None:
                    return response
            raise HTTPException(status_code=404, detail="Key not found")
        return response
    except Exception as e:
        logger.error(f"Error in get_value: {e}")
        raise

@app.put("/store/{key}")
async def put_value(key: str, item: KeyValue):
    try:
        # Determine which node should handle this key
        target_node = node_manager.get_node_for_key(key)
        logger.info(f"Put request for key '{key}' routed to node {target_node.id}")
        
        # Store on primary node
        if target_node.id == node_id:
            storage.put(key, item.value)
            logger.info(f"Stored key '{key}' locally")
        else:
            response = await node_manager.forward_request(
                target_node, "PUT", f"/store/{key}", 
                json={"value": item.value}
            )
            if response is None:
                raise HTTPException(status_code=503, detail="Failed to store value")
        
        # Replicate to backup nodes
        replicas = node_manager.get_replica_nodes(target_node)
        logger.info(f"Replicating to {len(replicas)} nodes")
        for replica in replicas:
            await node_manager.forward_request(
                replica, "PUT", f"/store/{key}",
                json={"value": item.value}
            )
        
        return {"status": "success", "node": target_node.id}
    except Exception as e:
        logger.error(f"Error in put_value: {e}")
        raise

@app.delete("/store/{key}")
async def delete_value(key: str):
    try:
        target_node = node_manager.get_node_for_key(key)
        logger.info(f"Delete request for key '{key}' routed to node {target_node.id}")
        
        if target_node.id == node_id:
            if not storage.delete(key):
                raise HTTPException(status_code=404, detail="Key not found")
        else:
            response = await node_manager.forward_request(target_node, "DELETE", f"/store/{key}")
            if response is None:
                raise HTTPException(status_code=404, detail="Key not found")
        
        # Delete from replicas
        replicas = node_manager.get_replica_nodes(target_node)
        logger.info(f"Deleting from {len(replicas)} replicas")
        for replica in replicas:
            await node_manager.forward_request(replica, "DELETE", f"/store/{key}")
        
        return {"status": "success", "node": target_node.id}
    except Exception as e:
        logger.error(f"Error in delete_value: {e}")
        raise

@app.get("/status")
async def get_status():
    try:
        current_node = node_manager.get_current_node()
        return NodeStatus(
            node_id=current_node.id,
            status="healthy",
            uptime=storage.get_uptime(),
            key_count=storage.get_key_count(),
            host=current_node.host,
            port=current_node.port
        )
    except Exception as e:
        logger.error(f"Error in get_status: {e}")
        raise

@app.get("/keys")
async def get_keys():
    try:
        return {"keys": storage.get_all_keys()}
    except Exception as e:
        logger.error(f"Error in get_keys: {e}")
        raise

@app.get("/node-info")
async def get_node_info():
    try:
        return {
            "nodes": [
                {
                    "id": node.id,
                    "url": node.url,
                    "last_heartbeat": node.last_heartbeat.isoformat(),
                    "is_healthy": node.is_healthy,
                    "failed_attempts": node.failed_attempts
                }
                for node in node_manager.get_all_nodes()
            ]
        }
    except Exception as e:
        logger.error(f"Error in get_node_info: {e}")
        raise

if __name__ == "__main__":
    if len(sys.argv) > 1:
        node_id = sys.argv[1]
    port = node_manager.nodes[node_id].port
    logger.info(f"Starting node {node_id} on port {port}")
    uvicorn.run(app, host="127.0.0.1", port=port) 