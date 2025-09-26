import hashlib
import base64
from django.conf import settings

class URLEncryptor:
    def __init__(self):
        self.secret_key = getattr(settings, 'URL_SECRET_KEY', 'your-secret-key-change-this')
    
    def encrypt_id(self, property_id):
        """Encrypt property ID to create a non-predictable URL"""
        # Create a hash of the ID with secret key
        hash_input = f"{property_id}{self.secret_key}".encode('utf-8')
        hash_result = hashlib.sha256(hash_input).digest()
        
        # Encode to base64 for URL safety
        encoded = base64.urlsafe_b64encode(hash_result[:12]).decode('utf-8').rstrip('=')
        
        # Combine ID with hash for verification
        return f"{property_id}_{encoded}"
    
    def decrypt_id(self, encrypted_string):
        """Decrypt the URL back to property ID and verify integrity"""
        try:
            parts = encrypted_string.split('_')
            if len(parts) != 2:
                return None
                
            property_id = int(parts[0])
            provided_hash = parts[1]
            
            # Recreate the hash to verify (using the same method as encryption)
            hash_input = f"{property_id}{self.secret_key}".encode('utf-8')
            hash_result = hashlib.sha256(hash_input).digest()
            expected_hash = base64.urlsafe_b64encode(hash_result[:12]).decode('utf-8').rstrip('=')
            
            # Compare the provided hash with the expected hash
            if provided_hash == expected_hash:
                return property_id
            return None
        except (ValueError, IndexError, AttributeError):
            return None

# Create a global instance
url_encryptor = URLEncryptor()