import os
import re
import sys
import json
import time
from datetime import datetime
from pathlib import Path
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory

from cli import display, config, ai
from cli.ssh import SSHManager
from cli.db import session_log, memory
from cli.modes import loader as mode_loader
from cli.plugins import loader as plugin_loader
from cli.auth import keychain
from cli.context import assemble_context, generate_session_summary
from cli.sync import run_sync
from cli.db.brain import read_brain_file, list_brain_versions, diff_brain_versions, save_brain_version, write_brain_file, generate_server_brain, generate_project_brain
from cli.db.file_tracker import get_last_version, list_versions, restore_version

def capture_snapshot(ssh, server_name: str) -> dict:
    snapshot_data = {
        "os_info": "Unknown",
        "memory_total_mb": 0,
        "memory_used_mb": 0,
        "disk_total_gb": 0.0,
        "disk_used_gb": 0.0,
        "cpu_count": 1,
        "load_avg": [],
        "running_services": [],
        "open_ports": [],
        "raw_context": ""
    }
    
    # 1. OS info
    out, _, _ = ssh.run("uname -sr", was_dry_run=False)
    if out.strip():
        snapshot_data["os_info"] = out.strip()
    
    # 2. Memory
    out, _, _ = ssh.run("free -m 2>/dev/null", was_dry_run=False)
    mem_match = re.search(r"Mem:\s+(\d+)\s+(\d+)", out)
    if mem_match:
        snapshot_data["memory_total_mb"] = int(mem_match.group(1))
        snapshot_data["memory_used_mb"] = int(mem_match.group(2))
        
    # 3. Disk
    out, _, _ = ssh.run("df -m / 2>/dev/null", was_dry_run=False)
    lines = out.strip().split("\n")
    if len(lines) >= 2:
        parts = lines[1].split()
        if len(parts) >= 3:
            try:
                snapshot_data["disk_total_gb"] = round(float(parts[1]) / 1024.0, 2)
                snapshot_data["disk_used_gb"] = round(float(parts[2]) / 1024.0, 2)
            except Exception:
                pass
                
    # 4. CPU count
    out, _, _ = ssh.run("nproc 2>/dev/null", was_dry_run=False)
    try:
        snapshot_data["cpu_count"] = int(out.strip())
    except Exception:
        pass
        
    # 5. Load average
    out, _, _ = ssh.run("cat /proc/loadavg 2>/dev/null", was_dry_run=False)
    parts = out.strip().split()
    if len(parts) >= 3:
        snapshot_data["load_avg"] = parts[:3]
        
    # 6. Running services
    out, _, _ = ssh.run("systemctl list-units --type=service --state=running --no-legend --no-pager 2>/dev/null", was_dry_run=False)
    services = []
    for line in out.strip().split("\n"):
        parts = line.split()
        if parts:
            services.append(parts[0])
    snapshot_data["running_services"] = services
    
    # 7. Open ports
    out, _, _ = ssh.run("ss -tunl | grep LISTEN 2>/dev/null", was_dry_run=False)
    ports = []
    for line in out.strip().split("\n"):
        port_matches = re.findall(r":(\d+)\s+", line)
        if port_matches:
            ports.extend(port_matches)
    snapshot_data["open_ports"] = sorted(list(set(ports)))
    
    # 8. Raw Context
    raw_context = (
        f"OS: {snapshot_data['os_info']}\n"
        f"CPU: {snapshot_data['cpu_count']} cores\n"
        f"RAM: {snapshot_data['memory_used_mb']} / {snapshot_data['memory_total_mb']} MB used\n"
        f"Disk: {snapshot_data['disk_used_gb']} / {snapshot_data['disk_total_gb']} GB used\n"
        f"Load Avg: {snapshot_data['load_avg']}\n"
        f"Running Services: {', '.join(services[:15])}\n"
        f"Open Ports: {', '.join(snapshot_data['open_ports'])}"
    )
    snapshot_data["raw_context"] = raw_context
    return snapshot_data

def diff_snapshots(snap_old, snap_new) -> list[str]:
    changes = []
    if snap_old.os_info != snap_new.os_info:
        changes.append(f"OS: {snap_old.os_info} -> {snap_new.os_info}")
    if snap_old.memory_used_mb != snap_new.memory_used_mb:
        changes.append(f"RAM Used: {snap_old.memory_used_mb}MB -> {snap_new.memory_used_mb}MB (Total: {snap_new.memory_total_mb}MB)")
    if snap_old.disk_used_gb != snap_new.disk_used_gb:
        changes.append(f"Disk Used: {snap_old.disk_used_gb}GB -> {snap_new.disk_used_gb}GB (Total: {snap_new.disk_total_gb}GB)")
    
    try:
        old_services = set(json.loads(snap_old.running_services))
        new_services = set(json.loads(snap_new.running_services))
        added_services = new_services - old_services
        removed_services = old_services - new_services
        if added_services:
            changes.append(f"Started Services: {', '.join(added_services)}")
        if removed_services:
            changes.append(f"Stopped Services: {', '.join(removed_services)}")
    except Exception:
        pass
        
    try:
        old_ports = set(json.loads(snap_old.open_ports))
        new_ports = set(json.loads(snap_new.open_ports))
        added_ports = new_ports - old_ports
        removed_ports = old_ports - new_ports
        if added_ports:
            changes.append(f"Opened Ports: {', '.join(added_ports)}")
        if removed_ports:
            changes.append(f"Closed Ports: {', '.join(removed_ports)}")
    except Exception:
        pass
        
    return changes

class REPLSession:
    def __init__(self, server_name: str, initial_mode: str | None = None, dry_run: bool = False):
        self.server_name = server_name
        self.dry_run = dry_run
        
        # Load configs
        self.profile = config.get_server_profile(server_name)
        
        # Determine mode
        self.modes = mode_loader.load_all_modes()
        
        # Determine initial mode: CLI flag -> server-scoped setting -> global setting -> "general"
        db_mode = session_log.get_setting("default_mode", server_name=server_name)
        self.active_mode_name = initial_mode or db_mode or "general"
        if self.active_mode_name not in self.modes:
            self.active_mode_name = "general"
            
        self.ssh = None
        self.db_session = None
        self.command_count = 0
        self.notes = []
        self.conversation_history = []  # List of message dicts: [{"role": "user"/"assistant", "content": "..."}]
        
        # Load Plugins
        self.plugin_registry = plugin_loader.load_plugins()

    def connect(self):
        host = self.profile["host"]
        user = self.profile["user"]
        port = self.profile.get("port", 22)
        key_path = self.profile.get("key_path")
        
        # Get credentials
        password = keychain.get_server_password(self.server_name)
        passphrase = keychain.get_key_passphrase(self.server_name)
        
        display.status_info(f"Connecting to {user}@{host}:{port}...")
        db_log_color = session_log.get_setting("log_color", server_name=self.server_name, default="dim")
        self.ssh = SSHManager(
            host=host,
            user=user,
            port=port,
            key_path=key_path,
            password=passphrase or password,
            log_color=db_log_color
        )
        
        try:
            self.ssh.connect()
            display.status_success(f"Connected to {self.server_name}")
        except Exception as e:
            display.status_error(f"SSH connection failed: {e}")
            raise e

        # Auto-detect hoster if not set manually
        hoster = self.profile.get("hoster")
        if not hoster:
            from cli.modes.hoster import detect_hoster
            display.status_info("Fingerprinting cloud provider...")
            detected = detect_hoster(self.ssh)
            if detected:
                display.status_success(f"Auto-detected provider: {detected}")
                self.profile["hoster"] = detected
                # Save back to config
                cfg = config.load_config()
                if self.server_name in cfg.get("servers", {}):
                    cfg["servers"][self.server_name]["hoster"] = detected
                    config.save_config(cfg)
            else:
                display.status_info("Hoster auto-detection yielded no match.")
        
        # Server snapshot (auto_snapshot setting)
        auto_snap = session_log.get_setting("auto_snapshot", server_name=self.server_name, default=True)
        if auto_snap:
            display.status_info("Capturing server state snapshot...")
            snap_data = capture_snapshot(self.ssh, self.server_name)
            session_log.save_snapshot(self.server_name, snap_data)
            display.status_success("Snapshot saved.")

        # Create session row in DB
        self.db_session = session_log.create_session(
            server_name=self.server_name,
            host=host,
            user=user,
            mode=self.active_mode_name
        )
        if self.ssh:
            self.ssh.session_id = self.db_session.id
            self.ssh.server_name = self.server_name

    def run_loop(self):
        # API Key validation
        api_key = config.get_api_key()
        if not api_key:
            display.status_warning("No DeepSeek API key found.")
            # Prompt user
            api_key = input("Please enter your DEEPSEEK_API_KEY: ").strip()
            if not api_key:
                display.status_error("API key is required to run the AI pipeline.")
                return
            # Save to config
            cfg = config.load_config()
            cfg["deepseek_api_key"] = api_key
            config.save_config(cfg)
            display.status_success("Saved DeepSeek API key to config.yaml.")
        
        self.api_key = api_key

        # Show banner
        display.show_banner(
            server_name=self.server_name,
            host=self.profile["host"],
            user=self.profile["user"],
            mode=self.active_mode_name,
            plugins_loaded=self.plugin_registry.loaded_count
        )
        
        # Setup prompt toolkit session with history file
        from cli.env import get_base_dir
        history_file = get_base_dir() / "prompt_history"
        prompt_session = PromptSession(history=FileHistory(str(history_file)))
        
        while True:
            try:
                # Prompt text
                dry_suffix = " [dry-run]" if self.dry_run else ""
                prompt_text = f"❯ "
                
                user_input = prompt_session.prompt(prompt_text).strip()
                if not user_input:
                    continue
                
                if user_input.startswith("/"):
                    # Process slash command
                    should_exit = self.handle_slash_command(user_input)
                    if should_exit:
                        break
                else:
                    # AI Conversational turn
                    self.execute_ai_turn(user_input, api_key)
                    
            except KeyboardInterrupt:
                print()
                display.status_warning("Session interrupted. Type /exit to disconnect.")
            except EOFError:
                print()
                break
            except Exception as e:
                display.status_error(f"REPL Error: {e}")

        # Disconnect
        self.disconnect()

    def handle_slash_command(self, cmd_str: str) -> bool:
        """Returns True if REPL should exit"""
        parts = cmd_str.split()
        cmd = parts[0].lower()
        args = parts[1:]
        
        # Check registered plugins first
        if cmd in self.plugin_registry.commands:
            try:
                self.plugin_registry.commands[cmd](args, self.ssh, ai, display)
            except Exception as e:
                display.status_error(f"Plugin command failed: {e}")
            return False

        if cmd == "/exit":
            # Generate and store session summary before exiting
            if self.db_session and self.conversation_history and getattr(self, "api_key", None):
                display.status_info("Generating session summary...")
                settings = session_log.get_all_settings(self.server_name)
                model_name = settings.get("ai_model", "deepseek-chat")
                summary = generate_session_summary(self.conversation_history, self.api_key, model_name)
                if summary:
                    session_log.update_session_summary(self.db_session.id, summary)
                    display.status_success("Session summary saved.")
            return True
            
        elif cmd == "/help":
            display.status_info("Available slash commands:")
            print("  /help                                 Show this help screen")
            print("  /servers                              List configured server profiles")
            print("  /switch <name>                        Switch active server mid-session")
            print("  /mode <name>                          Switch active mode")
            print("  /sync [--quick|--files|--memory]      Crawl server and update brain files")
            print("  /sync --project <name>                Sync one project only")
            print("  /sync --push                          Push current database data to the web dashboard")
            print("  /brain [<project>]                    Show SERVER.md or project brain file")
            print("  /brain diff [<v1> <v2>]               Diff brain versions")
            print("  /brain history                        List all brain versions")
            print("  /brain regen                          Force regenerate all brain files")
            print("  /memory                               Show all memories for this server")
            print("  /memory --category <cat>              Filter memories by category")
            print("  /memory set <key> <value>             Manually set a memory")
            print("  /memory forget <key>                  Forget a memory")
            print("  /memory search <query>                Search memories by keyword")
            print("  /memory clear                         Wipe all memories (destructive)")
            print("  /undo                                 Undo the last file write")
            print("  /undo --file <path> --version <n>     Restore a specific file version")
            print("  /history [n]                          Show last n commands (default 20)")
            print("  /history search <term>                Full-text search command history")
            print("  /replay <id>                          Re-run a command by database ID")
            print("  /snapshot                             Capture a server snapshot now")
            print("  /diff                                 Diff current state vs last snapshot")
            print("  /note <text>                          Attach a note to this session")
            print("  /settings                             Show current settings")
            print("  /set <key> <value>                    Update a setting")
            print("  /dry-run                              Toggle dry-run mode")
            print("  /clear                                Reset local conversation context")
            print("  /exit                                 Disconnect and exit")
            
            # Print plugin commands if any
            plugin_cmds = list(self.plugin_registry.commands.keys())
            if plugin_cmds:
                display.status_info("Plugin commands:")
                for pc in plugin_cmds:
                    print(f"  {pc}")
                    
        elif cmd == "/servers":
            cfg = config.load_config()
            servers = cfg.get("servers", {})
            default = cfg.get("default_server")
            for name, details in servers.items():
                marker = "*" if name == default else " "
                display.status_active_server(f"{marker} {name}", f"{details['user']}@{details['host']}")

        elif cmd == "/switch":
            if not args:
                display.status_warning("Usage: /switch <server_name>")
                return False
            target = args[0]
            try:
                # Save previous session ended info
                if self.ssh:
                    self.disconnect()
                # Connect to new
                self.server_name = target
                self.profile = config.get_server_profile(target)
                self.connect()
                # Reset conversation context
                self.conversation_history = []
                self.notes = []
                self.command_count = 0
                display.show_banner(
                    server_name=self.server_name,
                    host=self.profile["host"],
                    user=self.profile["user"],
                    mode=self.active_mode_name,
                    plugins_loaded=self.plugin_registry.loaded_count
                )
            except Exception as e:
                display.status_error(f"Failed to switch to {target}: {e}")
                
        elif cmd == "/mode":
            if not args:
                display.status_warning(f"Active mode: {self.active_mode_name}. Usage: /mode <mode_name>")
                print("Supported modes: " + ", ".join(self.modes.keys()))
                return False
            target_mode = args[0].lower()
            if target_mode in self.modes:
                self.active_mode_name = target_mode
                display.status_success(f"Switched to mode: {self.active_mode_name}")
            else:
                display.status_error(f"Unknown mode: {target_mode}. Supported: {list(self.modes.keys())}")
                
        elif cmd == "/history":
            if args and args[0] == "search":
                if len(args) < 2:
                    display.status_warning("Usage: /history search <term>")
                    return False
                term = " ".join(args[1:])
                results = session_log.search_command_history(term)
                display.status_info(f"Found {len(results)} matches for '{term}':")
                for cmd_obj in results:
                    print(f"[{cmd_obj.id}] {cmd_obj.ran_at} (server: {cmd_obj.server_name}): {cmd_obj.command}")
            else:
                limit = 20
                if args:
                    try:
                        limit = int(args[0])
                    except ValueError:
                        pass
                results = session_log.get_session_history(self.server_name, limit=limit)
                # Let's show commands for the current session or previous sessions
                if self.db_session:
                    cmds = session_log.get_commands_for_session(self.db_session.id)
                    display.status_info(f"Recent commands in this session:")
                    for c in cmds[-limit:]:
                        print(f"[{c.id}] exit:{c.exit_code} - {c.command}")
                else:
                    display.status_info("No active session rows.")
                    
        elif cmd == "/replay":
            if not args:
                display.status_warning("Usage: /replay <command_id>")
                return False
            try:
                cmd_id = int(args[0])
                cmd_obj = session_log.get_command_by_id(cmd_id)
                if not cmd_obj:
                    display.status_error(f"Command ID {cmd_id} not found in database.")
                    return False
                # Re-run
                confirm_all = session_log.get_setting("confirm_all", server_name=self.server_name, default=False)
                if self.ssh:
                    self.ssh.log_color = session_log.get_setting("log_color", server_name=self.server_name, default="dim")
                    self.ssh.current_user_prompt = f"/replay {cmd_id}"
                out, code, ms = self.ssh.run(cmd_obj.command, was_dry_run=self.dry_run, confirm_all=confirm_all)
                # Log to DB
                if self.db_session:
                    self.command_count += 1
                    session_log.log_command(
                        session_id=self.db_session.id,
                        server_name=self.server_name,
                        command=cmd_obj.command,
                        description=f"Replayed command #{cmd_id}",
                        output=out,
                        exit_code=code,
                        duration_ms=ms,
                        was_dry_run=self.dry_run,
                        user_prompt=f"/replay {cmd_id}"
                    )
            except ValueError:
                display.status_error("Command ID must be an integer.")
                
        elif cmd == "/memory":
            if args and args[0] == "set":
                if len(args) < 3:
                    display.status_warning("Usage: /memory set <key> <value>")
                    return False
                key = args[1]
                val = " ".join(args[2:])
                memory.set_memory(self.server_name, key, val, source="user_set")
                display.status_success(f"Set memory '{key}' = '{val}'  [user_set — protected]")
            elif args and args[0] == "forget":
                if len(args) < 2:
                    display.status_warning("Usage: /memory forget <key>")
                    return False
                key = args[1]
                if memory.forget_memory(self.server_name, key):
                    display.status_success(f"Forgot memory '{key}'")
                else:
                    display.status_warning(f"Memory key '{key}' not found.")
            elif args and args[0] == "search":
                if len(args) < 2:
                    display.status_warning("Usage: /memory search <query>")
                    return False
                query = " ".join(args[1:])
                results = memory.search_memories(self.server_name, query)
                display.status_info(f"Memory search results for '{query}':")
                for m in results:
                    cat = f"[{m.category}] " if m.category else ""
                    print(f"  {cat}{m.key} = {m.value}  (src:{m.source})")
            elif args and args[0] == "clear":
                confirm = input("  Wipe ALL memories for this server? [y/N]: ").strip().lower()
                if confirm == "y":
                    memory.clear_memories(self.server_name)
                    display.status_success("All memories cleared.")
                else:
                    display.status_warning("Cancelled.")
            elif args and args[0] == "--category":
                if len(args) < 2:
                    display.status_warning("Usage: /memory --category <category>")
                    return False
                cat = args[1]
                mems = memory.list_memories(self.server_name, category=cat)
                display.status_info(f"Memories [{cat}] for '{self.server_name}':")
                for m in mems:
                    print(f"  {m.key} = {m.value}  (conf:{m.confidence:.1f} src:{m.source})")
            else:
                mems = memory.list_memories(self.server_name)
                display.status_info(f"All memories for '{self.server_name}' ({len(mems)} total):")
                current_cat = None
                for m in sorted(mems, key=lambda x: (x.category or "", x.key)):
                    if m.category != current_cat:
                        current_cat = m.category
                        print(f"\n  [{current_cat or 'uncategorized'}]")
                    print(f"    {m.key} = {m.value}  (src:{m.source} conf:{m.confidence:.1f} accessed:{m.times_accessed}x)")
                    
        elif cmd == "/sync":
            if not self.ssh:
                display.status_error("Not connected to a server.")
                return False
            if "--push" in args:
                from cli.sync import push_to_cloud
                push_to_cloud(self.server_name)
                return True
            settings = session_log.get_all_settings(self.server_name)
            model_name = settings.get("ai_model", "deepseek-chat")
            quick = "--quick" in args
            only_files = "--files" in args
            only_memory = "--memory" in args
            only_project = None
            if "--project" in args:
                idx = args.index("--project")
                if idx + 1 < len(args):
                    only_project = args[idx + 1]
            run_sync(
                server_name=self.server_name,
                ssh=self.ssh,
                ai_api_key=self.api_key,
                model_name=model_name,
                quick=quick,
                only_project=only_project,
                only_files=only_files,
                only_memory=only_memory
            )

        elif cmd == "/brain":
            if not args or (len(args) == 1 and not args[0].startswith("-")):
                # Show brain file
                project_name = args[0] if args else None
                content = read_brain_file(self.server_name, project_name)
                if content:
                    print(content)
                else:
                    name = f"{project_name}.md" if project_name else "SERVER.md"
                    display.status_warning(f"No brain file found for {name}. Run /sync first.")
            elif args[0] == "diff":
                # /brain diff [v1 v2]
                project_name = None
                try:
                    v1 = int(args[1]) if len(args) > 1 else None
                    v2 = int(args[2]) if len(args) > 2 else None
                except (ValueError, IndexError):
                    v1 = v2 = None
                versions = list_brain_versions(self.server_name, project_name)
                if not versions:
                    display.status_warning("No brain versions found. Run /sync first.")
                elif v1 and v2:
                    print(diff_brain_versions(self.server_name, v1, v2, project_name))
                elif len(versions) >= 2:
                    sorted_v = sorted(versions, key=lambda v: v.version_number)
                    print(diff_brain_versions(self.server_name, sorted_v[-2].version_number, sorted_v[-1].version_number, project_name))
                else:
                    display.status_warning("Need at least 2 versions to diff.")
            elif args[0] == "history":
                versions = list_brain_versions(self.server_name)
                display.status_info(f"Brain versions for {self.server_name}:")
                for v in sorted(versions, key=lambda x: x.version_number, reverse=True):
                    proj = v.project_name or "SERVER"
                    print(f"  v{v.version_number}  [{proj}]  {v.trigger}  {v.created_at.strftime('%Y-%m-%d %H:%M')}")
            elif args[0] == "regen":
                display.status_info("Regenerating brain files from stored data...")
                content = generate_server_brain(self.server_name)
                v = save_brain_version(self.server_name, content, trigger="manual")
                write_brain_file(self.server_name, content)
                display.status_success(f"SERVER.md regenerated (v{v})")

        elif cmd == "/undo":
            if not self.ssh:
                display.status_error("Not connected to a server.")
                return False
            # Parse optional --file and --version flags
            undo_path = None
            undo_version = None
            if "--file" in args:
                idx = args.index("--file")
                if idx + 1 < len(args):
                    undo_path = args[idx + 1]
            if "--version" in args:
                idx = args.index("--version")
                if idx + 1 < len(args):
                    try:
                        undo_version = int(args[idx + 1])
                    except ValueError:
                        display.status_error("Version must be a number.")
                        return False
            # Find the version to restore
            if undo_path and undo_version:
                fv = None
                from cli.db.file_tracker import get_version
                fv = get_version(self.server_name, undo_path, undo_version)
            else:
                fv = get_last_version(self.server_name, undo_path)
            if not fv:
                display.status_warning("No file version found to undo.")
                return False
            # Show what will be restored
            print(f"  last change: {fv.file_path}")
            print(f"  changed: {fv.changed_at.strftime('%Y-%m-%d %H:%M')} | version {fv.version_number}")
            if fv.change_reason:
                print(f"  reason: {fv.change_reason}")
            confirm = input(f"  Restore version {fv.version_number - 1}? [y/N]: ").strip().lower()
            if confirm != "y":
                display.status_warning("Cancelled.")
                return False
            success, msg = restore_version(
                self.server_name, fv.file_path,
                fv.version_number, self.ssh,
                session_id=self.db_session.id if self.db_session else None
            )
            if success:
                display.status_success(msg)
            else:
                display.status_error(msg)

        elif cmd == "/snapshot":
            display.status_info("Capturing snapshot...")
            snap_data = capture_snapshot(self.ssh, self.server_name)
            session_log.save_snapshot(self.server_name, snap_data)
            display.status_success("Snapshot saved successfully.")
            
        elif cmd == "/diff":
            snaps = session_log.get_snapshots(self.server_name, limit=2)
            if len(snaps) < 2:
                display.status_warning("At least two snapshots are needed to perform a diff.")
                return False
            new_snap, old_snap = snaps[0], snaps[1]
            changes = diff_snapshots(old_snap, new_snap)
            if changes:
                display.status_info(f"Changes since snapshot on {old_snap.captured_at.strftime('%Y-%m-%d %H:%M:%S')}:")
                for c in changes:
                    print(f"  {c}")
            else:
                display.status_success("No changes detected since last snapshot.")
                
        elif cmd == "/note":
            if not args:
                display.status_warning("Usage: /note <session_note_text>")
                return False
            note_text = " ".join(args)
            self.notes.append(note_text)
            display.status_success("Note added to this session.")
            
        elif cmd == "/settings":
            settings = session_log.get_all_settings(self.server_name)
            display.status_info("Current settings configuration:")
            for k, v in settings.items():
                print(f"  {k} = {v}")
                
        elif cmd == "/set":
            if len(args) < 2:
                display.status_warning("Usage: /set <key> <value>")
                return False
            key = args[0]
            val_str = " ".join(args[1:])
            # Try to convert types
            if val_str.lower() == "true":
                val = True
            elif val_str.lower() == "false":
                val = False
            else:
                try:
                    val = int(val_str)
                except ValueError:
                    try:
                        val = float(val_str)
                    except ValueError:
                        val = val_str
            # Save server-scoped
            session_log.set_setting(key, val, server_name=self.server_name)
            display.status_success(f"Set settings key '{key}' to {val}")
            if key == "log_color" and self.ssh:
                self.ssh.log_color = str(val)
            
        elif cmd == "/dry-run":
            self.dry_run = not self.dry_run
            display.status_success(f"Dry-run mode toggled: {self.dry_run}")
            
        elif cmd == "/clear":
            self.conversation_history = []
            display.status_success("Local AI conversation context cleared.")
            
        else:
            display.status_error(f"Unknown slash command: {cmd}. Type /help for all options.")
            
        return False

    def execute_ai_turn(self, user_prompt: str, api_key: str):
        import time
        turn_start_time = time.time()
        # 1. Fetch relevant system settings and overlays
        settings = session_log.get_all_settings(self.server_name)
        if self.ssh:
            self.ssh.log_color = settings.get("log_color", "dim")
            self.ssh.current_user_prompt = user_prompt
        mode_overlay = self.modes[self.active_mode_name].get_overlay()
        
        hoster = self.profile.get("hoster")
        from cli.modes.hoster import get_hoster_overlay
        hoster_overlay = get_hoster_overlay(hoster)
        
        # Assemble brain context using the context assembler
        brain_ctx = assemble_context(self.server_name)
        
        # Assemble system prompt
        system_prompt = ai.assemble_system_prompt(
            mode_overlay=mode_overlay,
            hoster_overlay=hoster_overlay,
            settings=settings,
            brain_context=brain_ctx
        )
        
        # Format user prompt and add to context
        # We also inject the dry-run state if active so the AI doesn't get confused
        formatted_prompt = user_prompt
        if self.dry_run:
            formatted_prompt += " (NOTE: Running in dry-run connection mode, preview commands only)"
            
        self.conversation_history.append({"role": "user", "content": formatted_prompt})
        
        # 2. Loop for autonomous iteration
        max_iterations = 5
        for iteration in range(max_iterations):
            display.status_info("Thinking...")
            model_name = settings.get("ai_model", "deepseek-chat")
            try:
                parsed_response = ai.call_ai_pipeline(
                    api_key=api_key,
                    system_prompt=system_prompt,
                    messages=self.conversation_history,
                    show_stream=True,
                    model_name=model_name
                )
            except Exception as e:
                display.status_error(f"AI Pipeline failed: {e}")
                # Remove last user message since it failed
                self.conversation_history.pop()
                return
                
            # Parse output plan
            plan = parsed_response.get("plan", [])
            warnings = parsed_response.get("warnings", [])
            follow_up = parsed_response.get("follow_up")
            memories_to_process = parsed_response.get("memories", [])
            
            # Show warnings
            if warnings:
                for w in warnings:
                    display.status_warning(w)
                    
            if not plan:
                # No commands to execute, the AI is done with its autonomous loop
                break
                
            # 3. Execute plan commands
            outputs_context = []
            confirm_all = settings.get("confirm_all", False)
            
            for p in plan:
                desc = p.get("description", "Executing command")
                cmd = p.get("command", "").strip()
                if not cmd:
                    continue
                    
                display.status_info(f"Action: {desc}")
                out, code, ms = self.ssh.run(cmd, was_dry_run=self.dry_run, confirm_all=confirm_all)
                
                # Log executed command
                if self.db_session:
                    self.command_count += 1
                    session_log.log_command(
                        session_id=self.db_session.id,
                        server_name=self.server_name,
                        command=cmd,
                        description=desc,
                        output=out,
                        exit_code=code,
                        duration_ms=ms,
                        was_dry_run=self.dry_run,
                        user_prompt=user_prompt
                    )
                    
                # Cap command output inside context window management
                cap_limit = 3000
                if len(out) > cap_limit:
                    out_capped = out[:cap_limit] + f"\n... [Output truncated to {cap_limit} chars]"
                else:
                    out_capped = out
                    
                outputs_context.append(f"Command: {cmd}\nExit Code: {code}\nOutput:\n{out_capped}")
                
            # 4. Process AI memories
            for m in memories_to_process:
                action = m.get("action", "").lower()
                key = m.get("key")
                value = m.get("value", "")
                if key:
                    if action == "set":
                        memory.set_memory(self.server_name, key, value, source="ai_inferred")
                        display.status_info(f"AI auto-remembered: {key} = {value}")
                    elif action == "forget":
                        if memory.forget_memory(self.server_name, key):
                            display.status_info(f"AI auto-forgot: {key}")
                            
            # 5. Inject feedback of executions back into assistant response context
            assistant_plan_content = f"Plan: {json.dumps(plan, indent=2)}\nNarration: {parsed_response.get('narration', '')}"
            self.conversation_history.append({"role": "assistant", "content": assistant_plan_content})
            
            if outputs_context:
                user_feedback = "Executed planned commands. Outputs:\n" + "\n".join(outputs_context)
            else:
                user_feedback = "No commands were executed."
                
            if follow_up:
                user_feedback += f"\nFollow up suggestion: {follow_up}"
                display.status_info(f"Follow up: {follow_up}")
                
            # Check if we should iterate again
            if iteration < max_iterations - 1:
                user_feedback += "\n\nYou may now plan your next commands based on this output, or if you are done, provide an empty plan."
                
            self.conversation_history.append({"role": "user", "content": user_feedback})
        
        # 6. Stream final concise natural language answer to the user
        print() # Print space before final output
        display.status_info("Analyzing command results...")
        final_system_prompt = (
            "You are an expert Linux administrator. The user asked a question, commands were executed, and the outputs are provided. "
            "Provide a concise, direct, natural language answer to the user's question summarizing the findings. "
            "Do not include any JSON formatting, markdown blocks, or command plans. Just speak to the user directly."
        )
        try:
            final_summary = ai.call_final_response(
                api_key=api_key,
                system_prompt=final_system_prompt,
                messages=self.conversation_history,
                model_name=model_name
            )
            # Append final summary back to context with assistant role
            self.conversation_history.append({"role": "assistant", "content": final_summary})
        except Exception as e:
            display.status_error(f"Failed to fetch final summary: {e}")
            return f"Error getting final summary: {e}"
            
        elapsed = time.time() - turn_start_time
        display.status_info(f"Crunched for {elapsed:.1f}s")
        return final_summary

    def disconnect(self):
        # Save session logs
        if self.db_session:
            notes_str = "\n".join(self.notes) if self.notes else None
            session_log.end_session(self.db_session.id, self.command_count, notes=notes_str)
            self.db_session = None
            
        if self.ssh:
            display.status_info("Closing SSH connection...")
            self.ssh.close()
            self.ssh = None
            display.status_success("Disconnected.")
