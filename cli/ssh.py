import time
import sys
import os
import re
from pathlib import Path
import paramiko
from cli import display

# Simple list of common destructive command patterns
DESTRUCTIVE_PATTERNS = [
    r"\brm\b",
    r"\bmkfs\b",
    r"\bdd\s+if=",
    r"\bshutdown\b",
    r"\breboot\b",
    r"\bpoweroff\b",
    r"\bhalt\b",
    r"\bsystemctl\s+stop\b",
    r"\binit\s+[06]\b"
]

COLOR_MAP = {
    "green": "\033[32m",
    "dim": "\033[2m",
    "grey": "\033[90m",
    "gray": "\033[90m",
    "cyan": "\033[36m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "red": "\033[31m",
    "white": "\033[37m",
    "reset": "\033[0m"
}

def is_destructive(command: str) -> bool:
    # Split by common shell execution delimiters: &&, ||, ;, |
    sub_commands = re.split(r'(&&|\|\||;|\|)', command)
    for sub in sub_commands:
        sub = sub.strip()
        if not sub or sub in ("&&", "||", ";", "|"):
            continue
        # Find first word
        words = sub.split()
        if not words:
            continue
        # Strip quotes from the first word
        first_word = words[0].lower().strip("'\"")
        # If it's a display/read-only command wrapper, it's not destructive
        if first_word in ("echo", "cat", "printf", "grep", "egrep", "fgrep", "stat", "less", "more", "tail", "head"):
            continue
        
        # Check against destructive patterns
        for pattern in DESTRUCTIVE_PATTERNS:
            if re.search(pattern, sub):
                return True
    return False

def _extract_written_file(command: str, server_name: str) -> str | None:
    # Match redirects: > /path or >> /path or > "/path"
    m = re.search(r"(?:>|>>)\s*(['\"]?)(/[^\s;&|'\"]+)\1", command)
    if m:
        path = m.group(2)
        if "/dev/null" not in path:
            return path
    # Match tee: tee /path or tee -a /path
    m = re.search(r"\btee\b(?:\s+-[a-zA-Z]+)*\s+(['\"]?)(/[^\s;&|'\"]+)\1", command)
    if m:
        path = m.group(2)
        if "/dev/null" not in path:
            return path
    # Match sed -i: sed -i ... /path
    m = re.search(r"\bsed\b\s+.*-i.*\s+(['\"]?)(/[^\s;&|'\"]+)\1", command)
    if m:
        path = m.group(2)
        if "/dev/null" not in path:
            return path
            
    # Check if a tracked file path is mentioned in a write command
    write_keywords = ["echo", "cat", "tee", "sed", "cp", "mv", "rm", "printf", "write", "nano", "vim", "vi"]
    words = command.split()
    is_write = any(kw in words or (kw in command) for kw in write_keywords) or ">" in command or ">>" in command
    if is_write:
        from sqlmodel import Session, select
        from cli.db.models import get_engine, TrackedFileTable
        try:
            engine = get_engine()
            with Session(engine) as session:
                tracked = session.exec(select(TrackedFileTable).where(TrackedFileTable.server_name == server_name)).all()
            for tf in tracked:
                if tf.path in command:
                    return tf.path
        except Exception:
            pass
            
    return None

class SSHManager:
    def __init__(self, host: str, user: str, port: int = 22, key_path: str | None = None, password: str | None = None, log_color: str = "dim"):
        self.host = host
        self.user = user
        self.port = port
        self.key_path = key_path
        self.password = password
        self.client = None
        self.log_color = log_color

    def connect(self) -> bool:
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Try authentication in priority order:
        # 1. Key file (if provided)
        # 2. SSH agent
        # 3. Password
        
        pkey = None
        if self.key_path:
            expanded_path = os.path.expanduser(self.key_path)
            if os.path.exists(expanded_path):
                # Try reading as RSA, DSS, ECDSA, Ed25519
                key_classes = []
                for name in ["Ed25519Key", "RSAKey", "ECDSAKey", "DSSKey"]:
                    if hasattr(paramiko, name):
                        key_classes.append(getattr(paramiko, name))
                for key_class in key_classes:
                    try:
                        # If the key has a passphrase, we can pass it (password or prompted later)
                        pkey = key_class.from_private_key_file(expanded_path, password=self.password)
                        break
                    except paramiko.PasswordRequiredException:
                        # Needs passphrase
                        raise
                    except Exception:
                        continue
                if not pkey:
                    raise ValueError(f"Could not load private key from {expanded_path}")

        try:
            # Let's check SSH agent fallback first if no key path
            if not pkey:
                agent = paramiko.Agent()
                keys = agent.get_keys()
                if keys:
                    # SSH Agent has keys, paramiko connect will automatically use them if we let look_for_keys=True
                    pass

            # Connect
            connect_kwargs = {
                "hostname": self.host,
                "port": self.port,
                "username": self.user,
                "timeout": 15,
                "look_for_keys": True,
                "allow_agent": True
            }
            if pkey:
                connect_kwargs["pkey"] = pkey
            elif self.password:
                connect_kwargs["password"] = self.password
                
            self.client.connect(**connect_kwargs)
            return True
        except Exception as e:
            self.client = None
            raise e

    def run(self, command: str, was_dry_run: bool = False, confirm_all: bool = False, disable_hooks: bool = False) -> tuple[str, int, int]:
        """Runs a command, streams output, and returns (output_text, exit_code, duration_ms)"""
        if was_dry_run:
            display.status_dry_run(command)
            return "", 0, 0

        # Check if we should execute file tracking / change checks
        file_path = None
        res = None
        server_name = getattr(self, "server_name", None)
        
        if not disable_hooks and server_name:
            try:
                file_path = _extract_written_file(command, server_name)
                if file_path:
                    from cli.db.file_tracker import check_freshness
                    res = check_freshness(server_name, file_path, self)
                    if res and res.get("changed"):
                        # Show conflict UX
                        print(f"\n\033[33m⚠ {file_path} changed externally since last read\033[0m")
                        if res.get("diff"):
                            print("diff from my last read:")
                            print(res["diff"])
                        print("looks like the file was modified. do you want to:")
                        print("  [1] re-read the file and proceed anyway")
                        print("  [2] skip this command execution")
                        print("  [3] show the full current config first")
                        
                        while True:
                            choice = input("Select an option [1-3]: ").strip()
                            if choice == "1":
                                break
                            elif choice == "2":
                                display.status_warning("Command execution skipped by user.")
                                return "Command execution skipped due to file change conflict.", 0, 0
                            elif choice == "3":
                                print("\n--- Current File Content ---")
                                print(res.get("current_content", ""))
                                print("----------------------------")
                                print("Select an option:")
                                print("  [1] re-read the file and proceed anyway")
                                print("  [2] skip this command execution")
                            else:
                                print("Invalid option. Please choose 1, 2, or 3.")
            except Exception as e:
                display.status_warning(f"Error in pre-edit hook: {e}")

        # Destructive detection
        destructive = is_destructive(command)
        if destructive or confirm_all:
            prompt_msg = f"Destructive command detected: '{command}'" if destructive else f"Run command: '{command}'"
            if not display.status_destructive_prompt(prompt_msg):
                display.status_warning("Command cancelled by user.")
                return "Command cancelled by user.", -1, 0

        display.status_command(command)
        
        start_time = time.time()
        output_chunks = []
        exit_code = -1
        
        try:
            # We use get_pty=True to merge stdout and stderr and avoid blocking
            stdin, stdout, stderr = self.client.exec_command(command, get_pty=True)
            
            # Start custom colored output tag
            color_esc = COLOR_MAP.get(self.log_color.lower(), "\033[2m")
            sys.stdout.write(color_esc)
            sys.stdout.flush()
            
            # Read in real-time
            while not stdout.channel.exit_status_ready():
                if stdout.channel.recv_ready():
                    chunk = stdout.channel.recv(4096).decode('utf-8', errors='replace')
                    sys.stdout.write(chunk)
                    sys.stdout.flush()
                    output_chunks.append(chunk)
                time.sleep(0.01)
                
            # Read leftovers
            while stdout.channel.recv_ready():
                chunk = stdout.channel.recv(4096).decode('utf-8', errors='replace')
                sys.stdout.write(chunk)
                sys.stdout.flush()
                output_chunks.append(chunk)
                
            # End custom colored output tag
            sys.stdout.write("\033[0m")
            sys.stdout.flush()
                
            exit_code = stdout.channel.recv_exit_status()
        except Exception as e:
            display.status_error(f"Command execution error: {e}")
            output_chunks.append(f"\n[Error executing command: {e}]")
            exit_code = -1
            
        duration_ms = int((time.time() - start_time) * 1000)
        full_output = "".join(output_chunks)

        # Post-edit hook: record file version if write succeeded
        if not disable_hooks and server_name and file_path and exit_code == 0:
            try:
                # Read the new content after write
                # We must use disable_hooks=True to avoid recursion
                after_content, after_code, _ = self.run(f"cat {file_path}", was_dry_run=False, disable_hooks=True)
                if after_code == 0:
                    from cli.db.file_tracker import record_file_version, track_file
                    # Track the new file state
                    tf = track_file(
                        server_name=server_name,
                        path=file_path,
                        content=after_content,
                        category=res["tracked_file"].category if (res and res.get("tracked_file")) else None,
                        project_name=res["tracked_file"].project_name if (res and res.get("tracked_file")) else None,
                        is_sensitive=res["tracked_file"].is_sensitive if (res and res.get("tracked_file")) else False
                    )
                    
                    content_before = ""
                    if res and res.get("current_content") is not None:
                        content_before = res["current_content"]
                    elif res and res.get("tracked_file") and res["tracked_file"].content_snapshot is not None:
                        content_before = res["tracked_file"].content_snapshot
                        
                    record_file_version(
                        tracked_file_id=tf.id,
                        server_name=server_name,
                        file_path=file_path,
                        content_before=content_before,
                        content_after=after_content,
                        session_id=getattr(self, "session_id", None),
                        reason=getattr(self, "current_user_prompt", "Write command executed"),
                        user_prompt=getattr(self, "current_user_prompt", None)
                    )
            except Exception as e:
                display.status_warning(f"Failed to record file version in hook: {e}")

        return full_output, exit_code, duration_ms

    def close(self):
        if self.client:
            self.client.close()
            self.client = None
