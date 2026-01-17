"""
Encryption Utilities for Sensitive Data
AES-256-GCM encryption for PII (Personally Identifiable Information)

Protected fields:
- Genzai: birth_date, hourly_wage
- Ukeoi: birth_date, hourly_wage
- Staff: birth_date, address, postal_code, visa_type

Usage:
    from services.crypto_utils import encrypt_data, decrypt_data

    encrypted = encrypt_data("1985-05-15")
    decrypted = decrypt_data(encrypted)
"""

import os
import base64
import logging
from typing import Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


class EncryptionManager:
    """Manages AES-256-GCM encryption for sensitive data"""

    def __init__(self, master_key: Optional[str] = None):
        """
        Initialize encryption manager

        Args:
            master_key: 32-byte hex string or None (reads from DATABASE_ENCRYPTION_KEY env var)
        """
        if master_key is None:
            master_key = os.getenv("DATABASE_ENCRYPTION_KEY", "")

        if not master_key:
            logger.warning("No DATABASE_ENCRYPTION_KEY set - encryption disabled")
            self.enabled = False
            self.key = None
            return

        try:
            # Convert hex string to bytes (should be 32 bytes for AES-256)
            self.key = bytes.fromhex(master_key)
            if len(self.key) != 32:
                raise ValueError(f"Key must be 32 bytes (256 bits), got {len(self.key)}")
            self.enabled = True
        except ValueError as e:
            logger.error(f"Invalid encryption key: {e}")
            self.enabled = False
            self.key = None

    def encrypt(self, plaintext: Optional[str]) -> Optional[str]:
        """
        Encrypt plaintext using AES-256-GCM

        Args:
            plaintext: String to encrypt

        Returns:
            Base64-encoded ciphertext with nonce (format: nonce:ciphertext) or None
        """
        if not plaintext:
            return None

        if not self.enabled or not self.key:
            logger.warning(f"Encryption disabled - returning plaintext")
            return plaintext

        try:
            # Generate random 96-bit nonce
            nonce = os.urandom(12)

            # Create cipher
            cipher = AESGCM(self.key)

            # Encrypt
            ciphertext = cipher.encrypt(
                nonce,
                plaintext.encode('utf-8'),
                None  # No associated data
            )

            # Combine nonce:ciphertext and encode
            encrypted_data = nonce + ciphertext
            encoded = base64.b64encode(encrypted_data).decode('ascii')

            return encoded
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            return plaintext

    def decrypt(self, encrypted_data: Optional[str]) -> Optional[str]:
        """
        Decrypt AES-256-GCM ciphertext

        Args:
            encrypted_data: Base64-encoded ciphertext (nonce:ciphertext format)

        Returns:
            Decrypted plaintext or None
        """
        if not encrypted_data:
            return None

        if not self.enabled or not self.key:
            return encrypted_data  # Return as-is if encryption disabled

        try:
            # Decode from base64
            encrypted_bytes = base64.b64decode(encrypted_data)

            # Extract nonce (first 12 bytes) and ciphertext
            nonce = encrypted_bytes[:12]
            ciphertext = encrypted_bytes[12:]

            # Create cipher
            cipher = AESGCM(self.key)

            # Decrypt
            plaintext = cipher.decrypt(nonce, ciphertext, None)

            return plaintext.decode('utf-8')
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            return encrypted_data  # Return encrypted if decryption fails

    def hash_password(self, password: str, salt: Optional[bytes] = None) -> tuple[str, str]:
        """
        Hash password using PBKDF2 with SHA-256

        Args:
            password: Password to hash
            salt: Optional salt (generated if None)

        Returns:
            Tuple of (hashed_password, salt_hex)
        """
        if not salt:
            salt = os.urandom(16)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )

        hashed = kdf.derive(password.encode('utf-8'))

        return base64.b64encode(hashed).decode('ascii'), salt.hex()

    def verify_password(self, password: str, hashed: str, salt_hex: str) -> bool:
        """
        Verify password against hash

        Args:
            password: Password to verify
            hashed: Base64-encoded hash
            salt_hex: Hex-encoded salt

        Returns:
            True if password matches
        """
        try:
            salt = bytes.fromhex(salt_hex)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            kdf.verify(password.encode('utf-8'), base64.b64decode(hashed))
            return True
        except Exception:
            return False


# Global encryption manager
_encryption_manager = None


def get_encryption_manager() -> EncryptionManager:
    """Get or create global encryption manager"""
    global _encryption_manager
    if _encryption_manager is None:
        _encryption_manager = EncryptionManager()
    return _encryption_manager


def encrypt_field(value: Optional[str]) -> Optional[str]:
    """Encrypt a single field value"""
    if not value:
        return None
    manager = get_encryption_manager()
    return manager.encrypt(value)


def decrypt_field(value: Optional[str]) -> Optional[str]:
    """Decrypt a single field value"""
    if not value:
        return None
    manager = get_encryption_manager()
    return manager.decrypt(value)


def generate_encryption_key() -> str:
    """Generate a new 32-byte (256-bit) encryption key"""
    key = os.urandom(32)
    return key.hex()
