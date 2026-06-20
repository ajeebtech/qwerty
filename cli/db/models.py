from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, create_engine, Session
from cli.env import get_base_dir

DB_DIR = get_base_dir()
DB_PATH = DB_DIR / "data.db"

# ── Core tables ──────────────────────────────────────────────────────────────

class SessionTable(SQLModel, table=True):
    __tablename__ = "sessions"
    id: Optional[int] = Field(default=None, primary_key=True)
    server_name: str
    host: str
    user: str
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = Field(default=None)
    mode: str
    command_count: int = Field(default=0)
    notes: Optional[str] = Field(default=None)
    summary: Optional[str] = Field(default=None)   # AI-generated end-of-session summary

class CommandTable(SQLModel, table=True):
    __tablename__ = "commands"
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="sessions.id")
    server_name: str
    command: str
    description: Optional[str] = Field(default=None)
    output: Optional[str] = Field(default=None)
    exit_code: Optional[int] = Field(default=None)
    duration_ms: Optional[int] = Field(default=None)
    ran_at: datetime = Field(default_factory=datetime.utcnow)
    was_dry_run: bool = Field(default=False)
    user_prompt: Optional[str] = Field(default=None)

class AIMemoryTable(SQLModel, table=True):
    __tablename__ = "ai_memory"
    id: Optional[int] = Field(default=None, primary_key=True)
    server_name: str
    key: str
    value: str
    source: str = Field(default="ai_inferred")   # ai_inferred | user_set | sync_discovered
    category: Optional[str] = Field(default=None) # config | deployment | incident | preference | discovery
    confidence: float = Field(default=0.8)         # 0.0–1.0
    times_accessed: int = Field(default=0)
    last_accessed_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = Field(default=None)

class SettingTable(SQLModel, table=True):
    __tablename__ = "settings"
    id: Optional[int] = Field(default=None, primary_key=True)
    server_name: Optional[str] = Field(default=None)  # NULL = global
    key: str
    value: str  # JSON-encoded value
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ServerSnapshotTable(SQLModel, table=True):
    __tablename__ = "server_snapshots"
    id: Optional[int] = Field(default=None, primary_key=True)
    server_name: str
    captured_at: datetime = Field(default_factory=datetime.utcnow)
    os_info: Optional[str] = Field(default=None)
    memory_total_mb: Optional[int] = Field(default=None)
    memory_used_mb: Optional[int] = Field(default=None)
    disk_total_gb: Optional[float] = Field(default=None)
    disk_used_gb: Optional[float] = Field(default=None)
    cpu_count: Optional[int] = Field(default=None)
    load_avg: Optional[str] = Field(default=None)       # JSON
    running_services: Optional[str] = Field(default=None)  # JSON
    open_ports: Optional[str] = Field(default=None)     # JSON
    raw_context: Optional[str] = Field(default=None)

# ── Memory system tables ──────────────────────────────────────────────────────

class ProjectTable(SQLModel, table=True):
    """A discrete app/service discovered on the server."""
    __tablename__ = "projects"
    id: Optional[int] = Field(default=None, primary_key=True)
    server_name: str
    name: str                                            # e.g. 'api', 'frontend'
    path: Optional[str] = Field(default=None)           # /var/www/api
    type: Optional[str] = Field(default=None)           # node/python/docker/static/unknown
    process_manager: Optional[str] = Field(default=None)  # pm2/systemd/docker/none
    process_name: Optional[str] = Field(default=None)
    port: Optional[int] = Field(default=None)
    domain: Optional[str] = Field(default=None)
    runtime_version: Optional[str] = Field(default=None)  # Node 20.11 / Python 3.11
    package_manager: Optional[str] = Field(default=None)  # npm/yarn/pip/poetry
    git_remote: Optional[str] = Field(default=None)
    git_branch: Optional[str] = Field(default=None)
    last_deploy_at: Optional[datetime] = Field(default=None)
    brain_file_path: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class TrackedFileTable(SQLModel, table=True):
    """Every file vibe-server has read or touched."""
    __tablename__ = "tracked_files"
    id: Optional[int] = Field(default=None, primary_key=True)
    server_name: str
    project_name: Optional[str] = Field(default=None)   # nullable = server-wide file
    path: str                                            # absolute path on server
    category: Optional[str] = Field(default=None)       # nginx/systemd/env/cron/app-config/docker/other
    content_hash: Optional[str] = Field(default=None)   # SHA256
    content_snapshot: Optional[str] = Field(default=None)  # full content, capped 50KB
    last_read_at: Optional[datetime] = Field(default=None)
    last_modified_at: Optional[datetime] = Field(default=None)
    is_sensitive: bool = Field(default=False)            # .env, keys — redact in brain files
    created_at: datetime = Field(default_factory=datetime.utcnow)

class FileVersionTable(SQLModel, table=True):
    """Before/after content on every write — the undo log."""
    __tablename__ = "file_versions"
    id: Optional[int] = Field(default=None, primary_key=True)
    tracked_file_id: int = Field(foreign_key="tracked_files.id")
    session_id: Optional[int] = Field(default=None, foreign_key="sessions.id")
    server_name: str
    file_path: str                                       # denormalised for easy lookup
    version_number: int = Field(default=1)
    content_before: Optional[str] = Field(default=None)
    content_after: Optional[str] = Field(default=None)
    diff: Optional[str] = Field(default=None)            # unified diff string
    change_reason: Optional[str] = Field(default=None)  # AI one-liner
    user_prompt: Optional[str] = Field(default=None)    # message that triggered the edit
    changed_at: datetime = Field(default_factory=datetime.utcnow)
    reverted_at: Optional[datetime] = Field(default=None)

class BrainVersionTable(SQLModel, table=True):
    """Versioned copies of brain markdown files (git-like)."""
    __tablename__ = "brain_versions"
    id: Optional[int] = Field(default=None, primary_key=True)
    server_name: str
    project_name: Optional[str] = Field(default=None)  # null = SERVER.md
    version_number: int = Field(default=1)
    trigger: str = Field(default="sync")                # sync | edit | manual
    content: str                                        # full markdown content
    summary_of_changes: Optional[str] = Field(default=None)  # AI changelog entry
    created_at: datetime = Field(default_factory=datetime.utcnow)

# ── Engine ───────────────────────────────────────────────────────────────────

engine = None

def get_engine():
    global engine
    if engine is None:
        DB_DIR.mkdir(parents=True, exist_ok=True)
        db_url = f"sqlite:///{DB_PATH}"
        engine = create_engine(db_url, connect_args={"check_same_thread": False})
    return engine

def init_db():
    engine = get_engine()
    SQLModel.metadata.create_all(engine)
    
    # Simple SQLite migration for new columns added to existing tables
    from sqlalchemy import text
    with engine.begin() as conn:
        # Add summary to sessions
        try:
            conn.execute(text("ALTER TABLE sessions ADD COLUMN summary TEXT"))
        except Exception:
            pass
            
        # Add category to ai_memory
        try:
            conn.execute(text("ALTER TABLE ai_memory ADD COLUMN category TEXT"))
        except Exception:
            pass
            
        # Add confidence to ai_memory
        try:
            conn.execute(text("ALTER TABLE ai_memory ADD COLUMN confidence REAL DEFAULT 0.8"))
        except Exception:
            pass
            
        # Add times_accessed to ai_memory
        try:
            conn.execute(text("ALTER TABLE ai_memory ADD COLUMN times_accessed INTEGER DEFAULT 0"))
        except Exception:
            pass
            
        # Add last_accessed_at to ai_memory
        try:
            conn.execute(text("ALTER TABLE ai_memory ADD COLUMN last_accessed_at TIMESTAMP"))
        except Exception:
            pass
