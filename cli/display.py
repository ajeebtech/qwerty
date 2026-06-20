import sys
from rich.console import Console
from rich.theme import Theme
from rich.panel import Panel
from rich.text import Text

# Define a minimal, modern theme
custom_theme = Theme({
    "success": "bold green",
    "error": "bold red",
    "warning": "bold yellow",
    "info": "dim italic",
    "command": "bold cyan",
    "dry_run": "bold white",
    "active": "bold green",
    "banner": "bold blue"
})

console = Console(theme=custom_theme)

def status_success(msg: str):
    console.print(f"[success]✓[/success] {msg}")

def status_error(msg: str):
    console.print(f"[error]✗[/error] {msg}")

def status_warning(msg: str):
    console.print(f"[warning]⚠[/warning] {msg}")

def status_info(msg: str):
    console.print(f"[info]* {msg}[/info]")

def status_command(cmd: str):
    console.print(f"❯ [bold white]{cmd}[/bold white]")

def status_ai_response(msg: str):
    console.print(f"\n● {msg}\n")

def status_active_server(server_name: str, connection_str: str):
    console.print(f"[active]●[/active] {server_name}  {connection_str}")

def status_dry_run(cmd: str):
    console.print(f"[dry_run]  [dry-run] would run:[/dry_run] [bold white]{cmd}[/bold white]")

def status_destructive_prompt(msg: str) -> bool:
    console.print(f"[warning][y/N][/warning] {msg} [y/N]: ", end="")
    sys.stdout.flush()
    try:
        ans = sys.stdin.readline().strip().lower()
        return ans in ("y", "yes")
    except (KeyboardInterrupt, IOError):
        console.print()
        return False

def show_banner(server_name: str, host: str, user: str, mode: str, plugins_loaded: int = 0):
    console.print()
    console.print(f" vibe-server v2.0", style="banner")
    console.print(f" Target: {user}@{host} ({server_name}) | Mode: {mode}", style="dim")
    if plugins_loaded > 0:
        console.print(f" Plugins: + {plugins_loaded} loaded", style="dim green")
    console.print(" Type your request or /help", style="dim")
    console.print()
