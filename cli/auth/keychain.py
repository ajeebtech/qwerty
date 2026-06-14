from cli.auth import vault
from cli.env import get_cmd_name

def get_server_password(server_name: str) -> str | None:
    if not vault.is_vault_initialized():
        return None
    try:
        return vault.get_vault_value(f"pwd:{server_name}")
    except Exception:
        return None

def set_server_password(server_name: str, password: str):
    if not vault.is_vault_initialized():
        raise ValueError(f"Vault is not initialized. Please run '{get_cmd_name()} auth setup' first.")
    vault.set_vault_value(f"pwd:{server_name}", password)

def delete_server_password(server_name: str):
    if vault.is_vault_initialized():
        vault.delete_vault_value(f"pwd:{server_name}")

def get_key_passphrase(server_name: str) -> str | None:
    if not vault.is_vault_initialized():
        return None
    try:
        return vault.get_vault_value(f"passphrase:{server_name}")
    except Exception:
        return None

def set_key_passphrase(server_name: str, passphrase: str):
    if not vault.is_vault_initialized():
        raise ValueError(f"Vault is not initialized. Please run '{get_cmd_name()} auth setup' first.")
    vault.set_vault_value(f"passphrase:{server_name}", passphrase)

def delete_key_passphrase(server_name: str):
    if vault.is_vault_initialized():
        vault.delete_vault_value(f"passphrase:{server_name}")

def list_auth_methods(server_name: str, profile: dict) -> list[str]:
    methods = []
    if profile.get("key_path"):
        methods.append(f"Key file: {profile['key_path']}")
        if get_key_passphrase(server_name):
            methods.append("Key Passphrase: [stored in vault]")
    if get_server_password(server_name):
        methods.append("Password: [stored in vault]")
    if not methods:
        methods.append("SSH Agent / Default keys")
    return methods
