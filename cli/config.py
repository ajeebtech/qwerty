import os
import yaml
from cli.env import get_base_dir

CONFIG_DIR = get_base_dir()
CONFIG_PATH = CONFIG_DIR / "config.yaml"

DEFAULT_CONFIG = {
    "default_server": None,
    "deepseek_api_key": None,
    "servers": {}
}

def ensure_config_dir():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

def load_config() -> dict:
    ensure_config_dir()
    if not CONFIG_PATH.exists():
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_PATH, "r") as f:
            config = yaml.safe_load(f)
            if not isinstance(config, dict):
                return DEFAULT_CONFIG.copy()
            # Merge defaults for missing top-level keys
            for key, val in DEFAULT_CONFIG.items():
                if key not in config:
                    config[key] = val
            return config
    except Exception:
        return DEFAULT_CONFIG.copy()

def save_config(config: dict):
    ensure_config_dir()
    with open(CONFIG_PATH, "w") as f:
        yaml.safe_dump(config, f, default_flow_style=False)

def get_server_profile(name: str) -> dict:
    config = load_config()
    servers = config.get("servers", {})
    if name not in servers:
        raise ValueError(f"Server profile '{name}' not found.")
    profile = servers[name]
    profile.setdefault("port", 22)
    return profile

def get_default_server() -> str | None:
    config = load_config()
    return config.get("default_server")

def set_default_server(name: str):
    config = load_config()
    if name not in config.get("servers", {}):
        raise ValueError(f"Server profile '{name}' does not exist.")
    config["default_server"] = name
    save_config(config)

def add_server(name: str, host: str, user: str, port: int = 22, key_path: str | None = None, hoster: str | None = None):
    config = load_config()
    servers = config.setdefault("servers", {})
    servers[name] = {
        "host": host,
        "user": user,
        "port": port,
        "key_path": key_path,
        "hoster": hoster
    }
    # If no default server is set, make this the default
    if not config.get("default_server"):
        config["default_server"] = name
    save_config(config)

def remove_server(name: str):
    config = load_config()
    servers = config.get("servers", {})
    if name in servers:
        del servers[name]
        if config.get("default_server") == name:
            config["default_server"] = list(servers.keys())[0] if servers else None
        save_config(config)
    else:
        raise ValueError(f"Server profile '{name}' not found.")

def get_api_key() -> str | None:
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if api_key:
        return api_key
    config = load_config()
    return config.get("deepseek_api_key")
