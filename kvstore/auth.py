import hashlib
import hmac
import time
import secrets
from typing import Dict, Optional, Tuple
import logging

class AuthManager:
    def __init__(self, secret_key: str = None):
        self.secret_key = secret_key or secrets.token_hex(32)
        self.api_keys: Dict[str, str] = {}  # api_key -> role
        self.tokens: Dict[str, Tuple[float, str]] = {}  # token -> (expiry, api_key)
        self.token_expiry = 3600  # 1 hour
        self.logger = logging.getLogger("auth-manager")

    def add_api_key(self, api_key: str, role: str = "user"):
        """Add a new API key with specified role."""
        self.api_keys[api_key] = role
        self.logger.info(f"Added new API key with role: {role}")

    def authenticate(self, api_key: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Authenticate an API key and return a token."""
        if api_key not in self.api_keys:
            return False, None, "Invalid API key"

        # Generate token
        token = self._generate_token()
        expiry = time.time() + self.token_expiry
        self.tokens[token] = (expiry, api_key)
        
        return True, token, None

    def validate_token(self, token: str) -> Tuple[bool, Optional[str]]:
        """Validate a token and return if it's valid."""
        if token not in self.tokens:
            return False, "Invalid token"

        expiry, api_key = self.tokens[token]
        if time.time() > expiry:
            del self.tokens[token]
            return False, "Token expired"

        return True, None

    def get_role(self, token: str) -> Optional[str]:
        """Get the role associated with a token."""
        if token in self.tokens:
            _, api_key = self.tokens[token]
            return self.api_keys.get(api_key)
        return None

    def _generate_token(self) -> str:
        """Generate a secure token."""
        random_bytes = secrets.token_bytes(32)
        timestamp = str(time.time()).encode()
        token_hash = hmac.new(
            self.secret_key.encode(),
            random_bytes + timestamp,
            hashlib.sha256
        ).hexdigest()
        return token_hash

    def cleanup_expired_tokens(self):
        """Remove expired tokens."""
        current_time = time.time()
        expired = [
            token for token, (expiry, _) in self.tokens.items()
            if current_time > expiry
        ]
        for token in expired:
            del self.tokens[token]
        
        if expired:
            self.logger.info(f"Cleaned up {len(expired)} expired tokens") 