import json
from datetime import datetime
from typing import Optional, Any
from sqlmodel import Session, select, desc, or_
from cli.db.models import (
    get_engine,
    SessionTable,
    CommandTable,
    ServerSnapshotTable,
    SettingTable
)

def create_session(server_name: str, host: str, user: str, mode: str) -> SessionTable:
    engine = get_engine()
    with Session(engine) as session:
        db_session = SessionTable(
            server_name=server_name,
            host=host,
            user=user,
            mode=mode,
            started_at=datetime.utcnow()
        )
        session.add(db_session)
        session.commit()
        session.refresh(db_session)
        return db_session

def end_session(session_id: int, command_count: int, notes: Optional[str] = None):
    engine = get_engine()
    with Session(engine) as session:
        statement = select(SessionTable).where(SessionTable.id == session_id)
        db_session = session.exec(statement).first()
        if db_session:
            db_session.ended_at = datetime.utcnow()
            db_session.command_count = command_count
            if notes is not None:
                db_session.notes = notes
            session.add(db_session)
            session.commit()

def log_command(
    session_id: int,
    server_name: str,
    command: str,
    description: Optional[str] = None,
    output: Optional[str] = None,
    exit_code: Optional[int] = None,
    duration_ms: Optional[int] = None,
    was_dry_run: bool = False,
    user_prompt: Optional[str] = None
) -> CommandTable:
    engine = get_engine()
    with Session(engine) as session:
        db_cmd = CommandTable(
            session_id=session_id,
            server_name=server_name,
            command=command,
            description=description,
            output=output,
            exit_code=exit_code,
            duration_ms=duration_ms,
            was_dry_run=was_dry_run,
            user_prompt=user_prompt,
            ran_at=datetime.utcnow()
        )
        session.add(db_cmd)
        session.commit()
        session.refresh(db_cmd)
        return db_cmd

def get_session_history(server_name: Optional[str] = None, limit: int = 20) -> list[SessionTable]:
    engine = get_engine()
    with Session(engine) as session:
        statement = select(SessionTable)
        if server_name:
            statement = statement.where(SessionTable.server_name == server_name)
        statement = statement.order_by(desc(SessionTable.started_at)).limit(limit)
        return list(session.exec(statement).all())

def get_commands_for_session(session_id: int) -> list[CommandTable]:
    engine = get_engine()
    with Session(engine) as session:
        statement = select(CommandTable).where(CommandTable.session_id == session_id).order_by(CommandTable.ran_at)
        return list(session.exec(statement).all())

def search_command_history(query: str, limit: int = 50) -> list[CommandTable]:
    engine = get_engine()
    with Session(engine) as session:
        statement = select(CommandTable).where(
            or_(
                CommandTable.command.like(f"%{query}%"),
                CommandTable.description.like(f"%{query}%"),
                CommandTable.user_prompt.like(f"%{query}%")
            )
        ).order_by(desc(CommandTable.ran_at)).limit(limit)
        return list(session.exec(statement).all())

def get_command_by_id(command_id: int) -> Optional[CommandTable]:
    engine = get_engine()
    with Session(engine) as session:
        statement = select(CommandTable).where(CommandTable.id == command_id)
        return session.exec(statement).first()

def save_snapshot(server_name: str, snapshot_data: dict) -> ServerSnapshotTable:
    engine = get_engine()
    with Session(engine) as session:
        snapshot = ServerSnapshotTable(
            server_name=server_name,
            captured_at=datetime.utcnow(),
            os_info=snapshot_data.get("os_info"),
            memory_total_mb=snapshot_data.get("memory_total_mb"),
            memory_used_mb=snapshot_data.get("memory_used_mb"),
            disk_total_gb=snapshot_data.get("disk_total_gb"),
            disk_used_gb=snapshot_data.get("disk_used_gb"),
            cpu_count=snapshot_data.get("cpu_count"),
            load_avg=json.dumps(snapshot_data.get("load_avg")),
            running_services=json.dumps(snapshot_data.get("running_services")),
            open_ports=json.dumps(snapshot_data.get("open_ports")),
            raw_context=snapshot_data.get("raw_context")
        )
        session.add(snapshot)
        session.commit()
        session.refresh(snapshot)
        return snapshot

def get_latest_snapshot(server_name: str) -> Optional[ServerSnapshotTable]:
    engine = get_engine()
    with Session(engine) as session:
        statement = select(ServerSnapshotTable).where(ServerSnapshotTable.server_name == server_name).order_by(desc(ServerSnapshotTable.captured_at))
        return session.exec(statement).first()

def get_snapshots(server_name: str, limit: int = 20) -> list[ServerSnapshotTable]:
    engine = get_engine()
    with Session(engine) as session:
        statement = select(ServerSnapshotTable).where(ServerSnapshotTable.server_name == server_name).order_by(desc(ServerSnapshotTable.captured_at)).limit(limit)
        return list(session.exec(statement).all())

def get_setting(key: str, server_name: Optional[str] = None, default: Any = None) -> Any:
    engine = get_engine()
    with Session(engine) as session:
        # Check server-scoped first
        if server_name:
            stmt = select(SettingTable).where(SettingTable.server_name == server_name, SettingTable.key == key)
            db_setting = session.exec(stmt).first()
            if db_setting:
                try:
                    return json.loads(db_setting.value)
                except Exception:
                    return db_setting.value

        # Fallback to global
        stmt = select(SettingTable).where(SettingTable.server_name == None, SettingTable.key == key)
        db_setting = session.exec(stmt).first()
        if db_setting:
            try:
                return json.loads(db_setting.value)
            except Exception:
                return db_setting.value

        return default

def set_setting(key: str, value: Any, server_name: Optional[str] = None):
    engine = get_engine()
    serialized = json.dumps(value)
    with Session(engine) as session:
        if server_name:
            stmt = select(SettingTable).where(SettingTable.server_name == server_name, SettingTable.key == key)
        else:
            stmt = select(SettingTable).where(SettingTable.server_name == None, SettingTable.key == key)
        
        db_setting = session.exec(stmt).first()
        if db_setting:
            db_setting.value = serialized
            db_setting.updated_at = datetime.utcnow()
        else:
            db_setting = SettingTable(
                server_name=server_name,
                key=key,
                value=serialized,
                updated_at=datetime.utcnow()
            )
        session.add(db_setting)
        session.commit()

def get_all_settings(server_name: Optional[str] = None) -> dict[str, Any]:
    engine = get_engine()
    settings = {}
    with Session(engine) as session:
        # Load global first
        stmt = select(SettingTable).where(SettingTable.server_name == None)
        for row in session.exec(stmt).all():
            try:
                settings[row.key] = json.loads(row.value)
            except Exception:
                settings[row.key] = row.value
        
        # Override with server-scoped if specified
        if server_name:
            stmt = select(SettingTable).where(SettingTable.server_name == server_name)
            for row in session.exec(stmt).all():
                try:
                    settings[row.key] = json.loads(row.value)
                except Exception:
                    settings[row.key] = row.value
    return settings
