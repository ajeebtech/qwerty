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

    def run(self, command: str, was_dry_run: bool = False, confirm_all: bool = False) -> tuple[str, int, int]:
        """Runs a command, streams output, and returns (output_text, exit_code, duration_ms)"""
        if was_dry_run:
            display.status_dry_run(command)
            return "", 0, 0

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
        return full_output, exit_code, duration_ms

    def close(self):
        if self.client:
            self.client.close()
            self.client = None
