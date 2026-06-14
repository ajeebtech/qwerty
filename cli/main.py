import click
import json
import sys
import os
from datetime import datetime

from cli import display, config
from cli.db.models import init_db
from cli.db import session_log, memory
from cli.auth import vault, keychain
from cli.repl import REPLSession, capture_snapshot, diff_snapshots
from cli.ssh import SSHManager
from cli.env import get_cmd_name

@click.group()
def cli():
    """vps: AI-Powered Conversational VPS Manager"""
    init_db()

@cli.command("init")
def init():
    """Interactive first-time setup for config and vault"""
    display.status_info("Initializing qwerty configuration...")
    cfg = config.load_config()
    
    # 1. Ask for Anthropic API Key
    api_key = config.get_api_key()
    if not api_key:
        api_key = click.prompt("Enter your ANTHROPIC_API_KEY", default="", show_default=False).strip()
        if api_key:
            cfg["anthropic_api_key"] = api_key
            config.save_config(cfg)
            display.status_success("Saved Anthropic API Key.")
        else:
            display.status_warning("No API key entered. You can set it in ANTHROPIC_API_KEY env var later.")
            
    # 2. Ask to initialize credential vault
    if not vault.is_vault_initialized():
        if click.confirm("Would you like to setup the encrypted credential vault now?", default=True):
            pwd = click.prompt("Choose a master password for the vault", hide_input=True, confirmation_prompt=True)
            if pwd:
                vault.setup_vault(pwd)
                display.status_success(f"Encrypted vault initialized successfully at {vault.VAULT_PATH}")
            else:
                display.status_error("Invalid master password. Vault setup skipped.")
    else:
        display.status_info("Credential vault is already initialized.")
        
    display.status_success(f"qwerty setup completed! Run '{get_cmd_name()} add-server' to add your first VPS.")

@cli.command("add-server")
def add_server_cmd():
    """Add or update a server profile"""
    name = click.prompt("Server profile name (e.g., prod, staging)").strip().lower()
    host = click.prompt("Server IP or hostname").strip()
    user = click.prompt("SSH username", default="root").strip()
    port = click.prompt("SSH port", default=22, type=int)
    key_path = click.prompt("Path to SSH private key (optional)", default="", show_default=False).strip()
    hoster = click.prompt("Hoster profile (optional, e.g., hetzner, aws)", default="", show_default=False).strip()
    
    key_path = key_path if key_path else None
    hoster = hoster if hoster else None
    
    config.add_server(name, host, user, port, key_path, hoster)
    display.status_success(f"Server profile '{name}' added/updated successfully.")

@cli.command("servers")
def servers_cmd():
    """List all servers with status"""
    cfg = config.load_config()
    servers = cfg.get("servers", {})
    default = cfg.get("default_server")
    if not servers:
        display.status_warning(f"No servers configured. Use '{get_cmd_name()} add-server' first.")
        return
        
    display.status_info("Configured VPS Server Profiles:")
    for name, details in servers.items():
        marker = "*" if name == default else " "
        display.status_active_server(f"{marker} {name}", f"{details['user']}@{details['host']}:{details.get('port', 22)}")

@cli.command("remove-server")
@click.argument("name")
def remove_server_cmd(name):
    """Delete a server profile"""
    try:
        config.remove_server(name)
        display.status_success(f"Server profile '{name}' deleted.")
    except Exception as e:
        display.status_error(str(e))

@cli.command("set-default")
@click.argument("name")
def set_default_cmd(name):
    """Change default server"""
    try:
        config.set_default_server(name)
        display.status_success(f"Default server set to '{name}'.")
    except Exception as e:
        display.status_error(str(e))

@cli.command("connect")
@click.argument("server", required=False)
@click.option("--dry-run", is_flag=True, help="Preview commands without executing them")
@click.option("--mode", help="Specific mode to launch on connect (general/deploy/debug/monitor)")
def connect_cmd(server, dry_run, mode):
    """Connect to server and start the conversational REPL"""
    cfg = config.load_config()
    if not server:
        server = cfg.get("default_server")
        if not server:
            display.status_error(f"No server specified and no default server is set. Run '{get_cmd_name()} connect <server>'")
            return
            
    # Try unlocking vault if set up
    if vault.is_vault_initialized():
        display.status_info("Encrypted credential vault detected.")
        unlocked = False
        for i in range(3):
            pwd = click.prompt("Enter master password to unlock vault", hide_input=True)
            if vault.unlock_vault(pwd):
                display.status_success("Vault unlocked.")
                unlocked = True
                break
            else:
                display.status_error("Incorrect master password.")
        if not unlocked:
            display.status_warning("Proceeding with vault locked. Encrypted credentials will not be available.")

    try:
        session = REPLSession(server, initial_mode=mode, dry_run=dry_run)
        session.connect()
        session.run_loop()
    except Exception as e:
        display.status_error(f"Failed to start session: {e}")

@cli.command("ping")
@click.argument("server", required=False)
def ping_cmd(server):
    """Test SSH connection only"""
    cfg = config.load_config()
    if not server:
        server = cfg.get("default_server")
        if not server:
            display.status_error("No server specified and no default server set.")
            return

    # Unlock vault if possible
    if vault.is_vault_initialized():
        pwd = click.prompt("Enter master password to unlock vault", hide_input=True)
        vault.unlock_vault(pwd)
        
    try:
        profile = config.get_server_profile(server)
        host = profile["host"]
        user = profile["user"]
        port = profile.get("port", 22)
        key_path = profile.get("key_path")
        password = keychain.get_server_password(server)
        passphrase = keychain.get_key_passphrase(server)
        
        display.status_info(f"Pinging {user}@{host}:{port}...")
        ssh = SSHManager(host, user, port, key_path, passphrase or password)
        ssh.connect()
        display.status_success(f"Successfully reached server '{server}' via SSH!")
        ssh.close()
    except Exception as e:
        display.status_error(f"Failed to reach server: {e}")

@cli.group("auth")
def auth_group():
    """Manage SSH keys and passwords in the encrypted vault"""
    pass

@auth_group.command("setup")
def auth_setup():
    """Initialize credential vault with master password"""
    if vault.is_vault_initialized():
        if not click.confirm("Vault is already setup. Overwriting it will ERASE all saved secrets. Continue?", default=False):
            return
    pwd = click.prompt("Enter master password for the vault", hide_input=True, confirmation_prompt=True)
    vault.setup_vault(pwd)
    display.status_success("Credential vault setup completed.")

@auth_group.command("add-key")
@click.argument("server")
def auth_add_key(server):
    """Associate a key passphrase or login password with a server"""
    try:
        profile = config.get_server_profile(server)
    except Exception as e:
        display.status_error(str(e))
        return

    if not vault.is_vault_initialized():
        display.status_error(f"Vault is not initialized. Run '{get_cmd_name()} auth setup' first.")
        return

    # Unlock vault
    pwd = click.prompt("Enter vault master password to unlock", hide_input=True)
    if not vault.unlock_vault(pwd):
        display.status_error("Unlock failed. Cannot add credentials.")
        return

    choice = click.prompt(
        "Select credential type to add",
        type=click.Choice(["password", "passphrase", "cancel"], case_sensitive=False)
    )
    if choice == "password":
        passwd = click.prompt("Enter login password for VPS", hide_input=True)
        keychain.set_server_password(server, passwd)
        display.status_success(f"Saved SSH password for '{server}' to vault.")
    elif choice == "passphrase":
        passphrase = click.prompt("Enter passphrase for SSH private key", hide_input=True)
        keychain.set_key_passphrase(server, passphrase)
        display.status_success(f"Saved private key passphrase for '{server}' to vault.")

@auth_group.command("test")
@click.argument("server")
def auth_test(server):
    """Test SSH connection without launching REPL"""
    ctx = click.get_current_context()
    ctx.invoke(ping_cmd, server=server)

@auth_group.command("list")
def auth_list():
    """List configured auth methods per server"""
    if vault.is_vault_initialized():
        pwd = click.prompt("Enter master password to unlock vault", hide_input=True)
        vault.unlock_vault(pwd)
        
    cfg = config.load_config()
    servers = cfg.get("servers", {})
    if not servers:
        display.status_warning("No servers configured.")
        return
        
    for name, details in servers.items():
        methods = keychain.list_auth_methods(name, details)
        display.status_info(f"Server '{name}' ({details['user']}@{details['host']}):")
        for m in methods:
            print(f"  - {m}")

@cli.command("history")
@click.argument("server", required=False)
@click.option("--session", "session_id", type=int, help="Show commands from a specific session ID")
@click.option("--search", "search_term", help="Search through execution log text")
@click.option("--export", "export_file", help="Export session history to JSON file")
def history_cmd(server, session_id, search_term, export_file):
    """Show and search session and command history logs"""
    if search_term:
        results = session_log.search_command_history(search_term)
        display.status_info(f"Search results for '{search_term}':")
        for cmd in results:
            print(f"[{cmd.id}] {cmd.ran_at} (server: {cmd.server_name}): {cmd.command}")
        return

    if session_id:
        cmds = session_log.get_commands_for_session(session_id)
        if not cmds:
            display.status_warning(f"No commands found for Session ID {session_id}.")
            return
        display.status_info(f"Commands from Session ID {session_id}:")
        for c in cmds:
            print(f"[{c.id}] exit:{c.exit_code} ({c.duration_ms}ms) | {c.command}")
            
        if export_file:
            data = []
            for c in cmds:
                data.append({
                    "id": c.id,
                    "command": c.command,
                    "description": c.description,
                    "output": c.output,
                    "exit_code": c.exit_code,
                    "duration_ms": c.duration_ms,
                    "ran_at": c.ran_at.isoformat() if c.ran_at else None,
                    "was_dry_run": c.was_dry_run
                })
            try:
                with open(export_file, "w") as f:
                    json.dump(data, f, indent=2)
                display.status_success(f"Exported session {session_id} to '{export_file}'.")
            except Exception as e:
                display.status_error(f"Failed to export: {e}")
        return

    # Default show sessions
    sessions = session_log.get_session_history(server)
    if not sessions:
        display.status_warning("No session history found.")
        return
        
    display.status_info("Recent qwerty sessions:")
    for s in sessions:
        ended = s.ended_at.strftime('%Y-%m-%d %H:%M:%S') if s.ended_at else "Active/Interrupted"
        print(f"Session #{s.id} | Server: {s.server_name} | Started: {s.started_at.strftime('%Y-%m-%d %H:%M:%S')} | Ended: {ended} | Commands: {s.command_count} | Notes: {s.notes or 'None'}")

@cli.command("memory")
@click.argument("server")
@click.option("--set-key", "set_k", help="Setting key")
@click.option("--set-val", "set_v", help="Setting value")
@click.option("--forget", "forget_k", help="Forget key name")
@click.option("--clear", "clear_all", is_flag=True, help="Clear all memory for this server")
def memory_cmd(server, set_k, set_v, forget_k, clear_all):
    """View and manage persistent AI memory keys for servers"""
    if clear_all:
        memory.clear_memories(server)
        display.status_success(f"Wiped all memories for server '{server}'.")
        return
        
    if forget_k:
        if memory.forget_memory(server, forget_k):
            display.status_success(f"Forgot fact key '{forget_k}'.")
        else:
            display.status_warning(f"Key '{forget_k}' not found in memory.")
        return
        
    if set_k and set_v:
        memory.set_memory(server, set_k, set_v, source="user_set")
        display.status_success(f"Saved memory fact: {set_k} = {set_v}")
        return

    # List memories
    mems = memory.list_memories(server)
    if not mems:
        display.status_warning(f"No memories recorded for server '{server}'.")
        return
    display.status_info(f"AI Memories for '{server}':")
    for m in mems:
        print(f"  - {m.key}: {m.value} (source: {m.source})")

@cli.command("snapshot")
@click.argument("server", required=False)
def snapshot_cmd(server):
    """Capture snapshot of server state immediately"""
    cfg = config.load_config()
    if not server:
        server = cfg.get("default_server")
        if not server:
            display.status_error("No server specified and no default server set.")
            return

    if vault.is_vault_initialized():
        pwd = click.prompt("Enter master password to unlock vault", hide_input=True)
        vault.unlock_vault(pwd)
        
    try:
        profile = config.get_server_profile(server)
        host = profile["host"]
        user = profile["user"]
        port = profile.get("port", 22)
        key_path = profile.get("key_path")
        password = keychain.get_server_password(server)
        passphrase = keychain.get_key_passphrase(server)
        
        display.status_info(f"Connecting to {server}...")
        ssh = SSHManager(host, user, port, key_path, passphrase or password)
        ssh.connect()
        
        display.status_info("Capturing snapshot...")
        snap_data = capture_snapshot(ssh, server)
        session_log.save_snapshot(server, snap_data)
        display.status_success("Snapshot successfully saved to database.")
        
        ssh.close()
    except Exception as e:
        display.status_error(f"Snapshot capture failed: {e}")

@cli.command("snapshots")
@click.argument("server")
def snapshots_cmd(server):
    """List all snapshots captured for a server"""
    snaps = session_log.get_snapshots(server)
    if not snaps:
        display.status_warning(f"No snapshots found for server '{server}'.")
        return
        
    display.status_info(f"Snapshots for '{server}':")
    for s in snaps:
        print(f"  Snapshot #{s.id} | Captured At: {s.captured_at.strftime('%Y-%m-%d %H:%M:%S')} | OS: {s.os_info} | RAM: {s.memory_used_mb}/{s.memory_total_mb} MB")

@cli.command("diff")
@click.argument("server")
def diff_cmd(server):
    """Diff the last two snapshots of a server"""
    snaps = session_log.get_snapshots(server, limit=2)
    if len(snaps) < 2:
        display.status_warning("At least two snapshots are needed to perform a diff.")
        return
    new_snap, old_snap = snaps[0], snaps[1]
    changes = diff_snapshots(old_snap, new_snap)
    if changes:
        display.status_info(f"Changes since snapshot on {old_snap.captured_at.strftime('%Y-%m-%d %H:%M:%S')}:")
        for c in changes:
            print(f"  {c}")
    else:
        display.status_success("No changes detected since last snapshot.")

@cli.command("settings")
@click.option("--server", help="Show settings scoped to a specific server")
def settings_cmd(server):
    """Show all current global and scoped settings"""
    settings = session_log.get_all_settings(server)
    display.status_info("qwerty Active Settings Configuration:")
    for k, v in settings.items():
        print(f"  {k} = {v}")

@cli.command("set")
@click.argument("key")
@click.argument("value")
@click.option("--server", help="Set settings scoped to a specific server")
def set_cmd(key, value, server):
    """Update global or server-scoped setting"""
    # Convert types
    if value.lower() == "true":
        val = True
    elif value.lower() == "false":
        val = False
    else:
        try:
            val = int(value)
        except ValueError:
            try:
                val = float(value)
            except ValueError:
                val = value

    session_log.set_setting(key, val, server_name=server)
    scope_str = f"server '{server}'" if server else "global"
    display.status_success(f"Updated settings key '{key}' to '{val}' ({scope_str} scope).")

def cli_dev():
    os.environ["VIBE_ENV"] = "dev"
    cli()

if __name__ == "__main__":
    if "vps-dev" in sys.argv[0]:
        cli_dev()
    else:
        cli()
