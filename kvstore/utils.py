import logging
import json
from typing import Dict, Any
import os

def setup_logging(name: str) -> logging.Logger:
    """Set up logging for a component."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from a JSON file."""
    with open(config_path, 'r') as f:
        return json.load(f)

def get_node_address(host: str, port: int) -> str:
    """Get the full node address."""
    return f"{host}:{port}"

def ensure_directory(path: str):
    """Ensure a directory exists."""
    os.makedirs(path, exist_ok=True) 