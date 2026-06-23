# encryption.py
from cryptography.fernet import Fernet
import os
import streamlit as st
import base64

class EncryptionManager:
    def __init__(self):
        self.key = self._get_encryption_key()
        self.cipher_suite = Fernet(self.key)
    
    def _get_encryption_key(self):
        """
        Get encryption key from Streamlit secrets or environment variable.

        IMPORTANT: a Fernet key (from Fernet.generate_key()) is already a
        base64-encoded string. It should be passed to Fernet() as-is
        (encoded to bytes), NOT decoded again with base64.urlsafe_b64decode.
        Decoding it again either raises a padding error or, worse, silently
        produces a different (wrong-length) key.
        """
        # 1. Streamlit Cloud secrets (.streamlit/secrets.toml in the cloud dashboard)
        try:
            if hasattr(st, 'secrets') and 'ENCRYPTION_KEY' in st.secrets:
                return st.secrets['ENCRYPTION_KEY'].encode()
        except Exception:
            pass

        # 2. Environment variable (local/.env or any other host)
        key_env = os.environ.get('PASSWORD_MANAGER_ENCRYPTION_KEY') or os.environ.get('ENCRYPTION_KEY')
        if key_env:
            return key_env.encode()

        # No key configured anywhere — stop here rather than silently using a
        # fixed fallback key. A fallback baked into source code defeats the
        # purpose of encryption once the code is on GitHub.
        st.error(
            "No encryption key configured. Set ENCRYPTION_KEY in "
            ".streamlit/secrets.toml (or the Streamlit Cloud Secrets panel), or set the "
            "PASSWORD_MANAGER_ENCRYPTION_KEY environment variable. "
            "Generate one locally with:\n"
            "python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
        st.stop()
    
    def encrypt_password(self, password):
        """Encrypt a password"""
        if not password or self.key is None:
            return None
        try:
            return self.cipher_suite.encrypt(password.encode()).decode()
        except Exception as e:
            st.error(f"Encryption error: {str(e)}")
            return None
    
    def decrypt_password(self, encrypted_password):
        """Decrypt a password"""
        if not encrypted_password or self.key is None:
            return None
        try:
            return self.cipher_suite.decrypt(encrypted_password.encode()).decode()
        except Exception as e:
            st.error(f"Decryption error: {str(e)}")
            return None

# Global encryption manager instance
encryption_manager = EncryptionManager()