"""
Encryption utilities for Moulya College Management System
Handles password encryption/decryption for management access
"""

from cryptography.fernet import Fernet
import base64
import os

class PasswordEncryption:
    """Handle password encryption and decryption"""
    
    def __init__(self):
        # Get encryption key from environment or use a fixed key for development
        key = os.environ.get('ENCRYPTION_KEY')
        if not key:
            # Use a fixed key for development (in production, this should be set as env var)
            key = 'RBITlQDqlZsPZhjKIVlVvH2nbTLo1jQLPCIok5Gm_XQ='  # Fixed key from migration
            print("Using fixed development encryption key")
            print("Set ENCRYPTION_KEY environment variable in production")
        
        if isinstance(key, str):
            key = key.encode()
        
        self.cipher_suite = Fernet(key)
    
    def encrypt_password(self, password):
        """Encrypt a password for storage"""
        try:
            encrypted_password = self.cipher_suite.encrypt(password.encode())
            return base64.urlsafe_b64encode(encrypted_password).decode()
        except Exception as e:
            print(f"Error encrypting password: {e}")
            return None
    
    def decrypt_password(self, encrypted_password):
        """Decrypt a password for display"""
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_password.encode())
            decrypted_password = self.cipher_suite.decrypt(encrypted_bytes)
            return decrypted_password.decode()
        except Exception as e:
            print(f"Error decrypting password: {e}")
            return None

# Global instance
password_encryptor = PasswordEncryption()