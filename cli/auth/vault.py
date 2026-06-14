import os
import json
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cli.env import get_base_dir

VAULT_DIR = get_base_dir()
SALT_PATH = VAULT_DIR / "vault.salt"
VAULT_PATH = VAULT_DIR / "vault.enc"

_unlocked_fernet = None

def is_vault_initialized() -> bool:
    return SALT_PATH.exists() and VAULT_PATH.exists()

def setup_vault(master_password: str):
    VAULT_DIR.mkdir(parents=True, exist_ok=True)
    salt = os.urandom(16)
    with open(SALT_PATH, "wb") as f:
        f.write(salt)
    
    # Derive key and write empty encrypted dict
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000
    )
    key = base64.urlsafe_b64encode(kdf.derive(master_password.encode()))
    f_client = Fernet(key)
    
    empty_data = json.dumps({}).encode()
    encrypted = f_client.encrypt(empty_data)
    with open(VAULT_PATH, "wb") as f:
        f.write(encrypted)

def unlock_vault(master_password: str) -> bool:
    global _unlocked_fernet
    if not is_vault_initialized():
        return False
    try:
        with open(SALT_PATH, "rb") as f:
            salt = f.read()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_password.encode()))
        f_client = Fernet(key)
        
        with open(VAULT_PATH, "rb") as f:
            encrypted_data = f.read()
            
        # Try decrypting to verify
        f_client.decrypt(encrypted_data)
        _unlocked_fernet = f_client
        return True
    except Exception:
        return False

def _get_fernet() -> Fernet:
    global _unlocked_fernet
    if _unlocked_fernet is None:
        raise ValueError("Vault is locked. Please unlock it first.")
    return _unlocked_fernet

def read_vault() -> dict:
    f_client = _get_fernet()
    with open(VAULT_PATH, "rb") as f:
        encrypted_data = f.read()
    decrypted_data = f_client.decrypt(encrypted_data)
    return json.loads(decrypted_data.decode())

def write_vault(data: dict):
    f_client = _get_fernet()
    serialized = json.dumps(data).encode()
    encrypted = f_client.encrypt(serialized)
    with open(VAULT_PATH, "wb") as f:
        f.write(encrypted)

def get_vault_value(key: str) -> str | None:
    try:
        data = read_vault()
        return data.get(key)
    except Exception:
        return None

def set_vault_value(key: str, value: str):
    data = read_vault()
    data[key] = value
    write_vault(data)

def delete_vault_value(key: str) -> bool:
    data = read_vault()
    if key in data:
        del data[key]
        write_vault(data)
        return True
    return False

def list_vault_keys() -> list[str]:
    try:
        data = read_vault()
        return list(data.keys())
    except Exception:
        return []
