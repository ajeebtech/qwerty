import sys
import importlib.util
from cli.plugins import pm2, docker, nginx, certbot
from cli.env import get_base_dir

PLUGINS_DIR = get_base_dir() / "plugins"

class PluginRegistry:
    def __init__(self):
        self.commands = {}
        self.loaded_count = 0

    def slash_command(self, name: str):
        def decorator(func):
            self.commands[name] = func
            return func
        return decorator

def load_plugins() -> PluginRegistry:
    registry = PluginRegistry()
    
    # 1. Load built-in plugins
    builtins = [
        ("pm2", pm2),
        ("docker", docker),
        ("nginx", nginx),
        ("certbot", certbot)
    ]
    
    for name, module in builtins:
        try:
            if hasattr(module, "register"):
                module.register(registry)
                registry.loaded_count += 1
        except Exception:
            pass

    # 2. Load custom user plugins
    if not PLUGINS_DIR.exists():
        PLUGINS_DIR.mkdir(parents=True, exist_ok=True)
        
    for path in PLUGINS_DIR.glob("*.py"):
        if path.name.startswith("__"):
            continue
        try:
            module_name = f"cli.plugins.custom_{path.stem}"
            spec = importlib.util.spec_from_file_location(module_name, str(path))
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                if hasattr(module, "register"):
                    module.register(registry)
                    registry.loaded_count += 1
        except Exception:
            # Catch errors in plugins to report them but avoid crashing the REPL
            pass
            
    return registry
