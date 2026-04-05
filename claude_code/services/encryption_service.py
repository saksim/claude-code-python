"""
Claude Code Python - Session Encryption Service
Provides encryption for session data at rest.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- Dataclass patterns (frozen/slots)
- pathlib.Path for file operations
- Proper error handling
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass


try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE: bool = True
except ImportError:
    CRYPTO_AVAILABLE = False


# Default constants
DEFAULT_SALT: bytes = b"claude-code-default-salt"
DEFAULT_PBKDF2_ITERATIONS: int = 480000


@dataclass(frozen=True, slots=True)
class EncryptedData:
    """Encrypted data container.
    
    Using frozen=True, slots=True for immutability and memory efficiency.
    
    Attributes:
        ciphertext: Base64-encoded encrypted data
        salt: Key derivation method used (e.g., "pbkdf2", "none")
        nonce: Nonce/IV used for encryption (e.g., "fernet", None)
    """
    ciphertext: str
    salt: str
    nonce: Optional[str] = None


class SessionEncryption:
    """Service for encrypting/decrypting session data.
    
    Uses Fernet symmetric encryption with PBKDF2 key derivation.
    Falls back to base64 encoding if cryptography is not available.
    
    Attributes:
        is_enabled: Whether encryption is currently active
    
    Example:
        >>> encryption = SessionEncryption(master_password="secret")
        >>> if encryption.is_enabled:
        ...     encrypted = encryption.encrypt({"key": "value"})
        ...     decrypted = encryption.decrypt(encrypted)
    """
    
    def __init__(self, master_password: Optional[str] = None):
        self._fernet: Optional[Fernet] = None
        self._has_crypto = CRYPTO_AVAILABLE
        
        if master_password:
            self._derive_key(master_password)
        elif CRYPTO_AVAILABLE:
            env_key = os.environ.get("CLAUDE_SESSION_KEY")
            if env_key:
                self._derive_key(env_key)
    
    def _derive_key(self, password: str) -> None:
        """Derive encryption key from password.
        
        Args:
            password: Master password for key derivation
        """
        if not CRYPTO_AVAILABLE:
            return
        
        salt_env = os.environ.get("CLAUDE_SESSION_SALT")
        salt = salt_env.encode() if isinstance(salt_env, str) else DEFAULT_SALT
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=DEFAULT_PBKDF2_ITERATIONS,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        self._fernet = Fernet(key)
    
    @property
    def is_enabled(self) -> bool:
        """Check if encryption is enabled.
        
        Returns:
            True if encryption key has been derived.
        """
        return self._fernet is not None
    
    def encrypt(self, data: Any) -> EncryptedData:
        """Encrypt data.
        
        Args:
            data: Any JSON-serializable data to encrypt
            
        Returns:
            EncryptedData containing ciphertext and metadata.
        """
        json_data = json.dumps(data, default=str)
        
        if self._fernet:
            ciphertext = self._fernet.encrypt(json_data.encode())
            return EncryptedData(
                ciphertext=base64.b64encode(ciphertext).decode(),
                salt="pbkdf2",
                nonce="fernet"
            )
        else:
            encoded = base64.b64encode(json_data.encode()).decode()
            return EncryptedData(
                ciphertext=encoded,
                salt="none",
                nonce=None
            )
    
    def decrypt(self, encrypted: EncryptedData) -> Any:
        """Decrypt data.
        
        Args:
            encrypted: EncryptedData to decrypt
            
        Returns:
            Original decrypted data.
        """
        if self._fernet and encrypted.salt != "none":
            ciphertext = base64.b64decode(encrypted.ciphertext.encode())
            decrypted = self._fernet.decrypt(ciphertext)
            return json.loads(decrypted.decode())
        else:
            decoded = base64.b64decode(encrypted.ciphertext.encode())
            return json.loads(decoded.decode())
    
    def encrypt_str(self, data: str) -> str:
        """Encrypt a string.
        
        Args:
            data: String to encrypt
            
        Returns:
            JSON string containing encrypted data.
        """
        encrypted = self.encrypt(data)
        return json.dumps({
            "ciphertext": encrypted.ciphertext,
            "salt": encrypted.salt,
            "nonce": encrypted.nonce
        })
    
    def decrypt_str(self, encrypted_str: str) -> str:
        """Decrypt a string.
        
        Args:
            encrypted_str: JSON string with encrypted data
            
        Returns:
            Decrypted string.
        """
        data = json.loads(encrypted_str)
        encrypted = EncryptedData(
            ciphertext=data["ciphertext"],
            salt=data.get("salt", "none"),
            nonce=data.get("nonce")
        )
        result = self.decrypt(encrypted)
        return result if isinstance(result, str) else json.dumps(result)
    
    @staticmethod
    def generate_key() -> str:
        """Generate a new encryption key.
        
        Returns:
            Base64-encoded encryption key string.
        """
        if CRYPTO_AVAILABLE:
            return Fernet.generate_key().decode()
        else:
            return base64.b64encode(os.urandom(32)).decode()


class SessionStorage:
    """Encrypted session storage.
    
    Provides secure storage for session data with encryption at rest.
    Uses asyncio.Lock for thread-safe operations.
    
    Attributes:
        storage_dir: Directory for storing encrypted session files
    
    Example:
        >>> storage = SessionStorage("./sessions")
        >>> await storage.save("session-123", {"key": "value"})
        >>> data = await storage.load("session-123")
    """
    
    def __init__(
        self,
        storage_dir: str | Path,
        encryption: Optional[SessionEncryption] = None
    ):
        self._storage_dir = Path(storage_dir)
        self._encryption = encryption or SessionEncryption()
        self._lock = asyncio.Lock()
        
        self._storage_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_file_path(self, session_id: str) -> Path:
        """Get file path for a session.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Path to the session file.
        """
        return self._storage_dir / f"{session_id}.enc"
    
    async def save(
        self,
        session_id: str,
        data: dict[str, Any],
        encrypt: bool = True,
    ) -> None:
        """Save session data.
        
        Args:
            session_id: Unique session identifier
            data: Session data to save
            encrypt: Whether to encrypt the data before saving
        """
        async with self._lock:
            file_path = self._get_file_path(session_id)
            
            if encrypt and self._encryption.is_enabled:
                encrypted = self._encryption.encrypt(data)
                save_data: dict[str, Any] = {
                    "encrypted": True,
                    "data": {
                        "ciphertext": encrypted.ciphertext,
                        "salt": encrypted.salt,
                        "nonce": encrypted.nonce,
                    }
                }
            else:
                save_data = {
                    "encrypted": False,
                    "data": data
                }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f)
    
    async def load(
        self,
        session_id: str,
        decrypt: bool = True,
    ) -> Optional[dict[str, Any]]:
        """Load session data.
        
        Args:
            session_id: Unique session identifier
            decrypt: Whether to decrypt the data after loading
            
        Returns:
            Session data dictionary or None if not found.
        """
        async with self._lock:
            file_path = self._get_file_path(session_id)
            
            if not file_path.exists():
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                save_data = json.load(f)
            
            if save_data.get("encrypted") and decrypt:
                encrypted = EncryptedData(**save_data["data"])
                return self._encryption.decrypt(encrypted)
            else:
                return save_data.get("data")
    
    async def delete(self, session_id: str) -> bool:
        """Delete session data.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            True if deleted, False if not found.
        """
        async with self._lock:
            file_path = self._get_file_path(session_id)
            if file_path.exists():
                file_path.unlink()
                return True
            return False
    
    async def exists(self, session_id: str) -> bool:
        """Check if session exists.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            True if session file exists.
        """
        file_path = self._get_file_path(session_id)
        return file_path.exists()
    
    async def list_sessions(self) -> list[str]:
        """List all session IDs.
        
        Returns:
            Sorted list of session IDs (without .enc extension).
        """
        sessions: list[str] = []
        for filename in self._storage_dir.glob("*.enc"):
            session_id = filename.stem
            sessions.append(session_id)
        return sorted(sessions)


# Global encryption instance
_encryption: Optional[SessionEncryption] = None


def get_encryption() -> SessionEncryption:
    """Get global encryption instance."""
    global _encryption
    if _encryption is None:
        _encryption = SessionEncryption()
    return _encryption
