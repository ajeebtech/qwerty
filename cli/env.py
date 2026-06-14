import os
import sys
from pathlib import Path

def is_dev_env() -> bool:
    return "vps-dev" in sys.argv[0] or os.environ.get("VIBE_ENV") == "dev"

def get_base_dir() -> Path:
    dir_name = ".vibe-server-dev" if is_dev_env() else ".vibe-server"
    return Path.home() / dir_name

def get_cmd_name() -> str:
    return "vps-dev" if is_dev_env() else "vps"
