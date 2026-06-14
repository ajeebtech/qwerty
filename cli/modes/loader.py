import yaml
from cli.modes.base import BaseMode
from cli.modes.general import GeneralMode
from cli.modes.deploy import DeployMode
from cli.modes.debug import DebugMode
from cli.modes.monitor import MonitorMode
from cli.env import get_base_dir

CUSTOM_MODES_DIR = get_base_dir() / "modes"

class CustomMode(BaseMode):
    def __init__(self, name: str, description: str, overlay: str):
        self._name = name
        self._description = description
        self._overlay = overlay

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    def get_overlay(self) -> str:
        return self._overlay

def load_all_modes() -> dict[str, BaseMode]:
    # Standard modes
    modes: dict[str, BaseMode] = {
        "general": GeneralMode(),
        "deploy": DeployMode(),
        "debug": DebugMode(),
        "monitor": MonitorMode()
    }
    
    # Custom modes loader
    if not CUSTOM_MODES_DIR.exists():
        CUSTOM_MODES_DIR.mkdir(parents=True, exist_ok=True)
        # Create an example custom mode
        example_mode = {
            "name": "django",
            "description": "Django app management overlay",
            "overlay": "This server runs a Django app. Always use manage.py for migrations. Prefer gunicorn + nginx."
        }
        try:
            with open(CUSTOM_MODES_DIR / "django.yaml", "w") as f:
                yaml.safe_dump(example_mode, f)
        except Exception:
            pass

    for path in CUSTOM_MODES_DIR.glob("*.yaml"):
        try:
            with open(path, "r") as f:
                data = yaml.safe_load(f)
                if isinstance(data, dict) and "name" in data and "overlay" in data:
                    name = data["name"].strip().lower()
                    desc = data.get("description", f"Custom mode {name}")
                    overlay = data["overlay"]
                    modes[name] = CustomMode(name, desc, overlay)
        except Exception:
            # Silently ignore load errors for malformed custom modes
            continue

    return modes
