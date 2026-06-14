from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, create_engine, Session
from cli.env import get_base_dir

DB_DIR = get_base_dir()
DB_PATH = DB_DIR / "data.db"

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
    source: str  # 'ai_inferred' or 'user_set'
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
    load_avg: Optional[str] = Field(default=None)  # JSON
    running_services: Optional[str] = Field(default=None)  # JSON
    open_ports: Optional[str] = Field(default=None)  # JSON
    raw_context: Optional[str] = Field(default=None)

# Database Engine
engine = None

def get_engine():
    global engine
    if engine is None:
        DB_DIR.mkdir(parents=True, exist_ok=True)
        db_url = f"sqlite:///{DB_PATH}"
        engine = create_engine(db_url, connect_args={"check_same_thread": False})
    return engine

def init_db():
    SQLModel.metadata.create_all(get_engine())
