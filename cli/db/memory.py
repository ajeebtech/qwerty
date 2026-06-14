from datetime import datetime
from typing import Optional
from sqlmodel import Session, select, delete
from cli.db.models import get_engine, AIMemoryTable

def set_memory(
    server_name: str,
    key: str,
    value: str,
    source: str = "ai_inferred",
    expires_at: Optional[datetime] = None
) -> AIMemoryTable:
    engine = get_engine()
    with Session(engine) as session:
        statement = select(AIMemoryTable).where(
            AIMemoryTable.server_name == server_name,
            AIMemoryTable.key == key
        )
        db_memory = session.exec(statement).first()
        if db_memory:
            db_memory.value = value
            db_memory.source = source
            db_memory.updated_at = datetime.utcnow()
            db_memory.expires_at = expires_at
        else:
            db_memory = AIMemoryTable(
                server_name=server_name,
                key=key,
                value=value,
                source=source,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                expires_at=expires_at
            )
        session.add(db_memory)
        session.commit()
        session.refresh(db_memory)
        return db_memory

def forget_memory(server_name: str, key: str) -> bool:
    engine = get_engine()
    with Session(engine) as session:
        statement = select(AIMemoryTable).where(
            AIMemoryTable.server_name == server_name,
            AIMemoryTable.key == key
        )
        db_memory = session.exec(statement).first()
        if db_memory:
            session.delete(db_memory)
            session.commit()
            return True
        return False

def get_memory(server_name: str, key: str) -> Optional[AIMemoryTable]:
    engine = get_engine()
    with Session(engine) as session:
        statement = select(AIMemoryTable).where(
            AIMemoryTable.server_name == server_name,
            AIMemoryTable.key == key
        )
        memory = session.exec(statement).first()
        # Check TTL expiration
        if memory and memory.expires_at and memory.expires_at < datetime.utcnow():
            session.delete(memory)
            session.commit()
            return None
        return memory

def list_memories(server_name: str) -> list[AIMemoryTable]:
    engine = get_engine()
    with Session(engine) as session:
        statement = select(AIMemoryTable).where(AIMemoryTable.server_name == server_name)
        memories = session.exec(statement).all()
        # Filter expired memories
        active_memories = []
        now = datetime.utcnow()
        for mem in memories:
            if mem.expires_at and mem.expires_at < now:
                session.delete(mem)
                session.commit()
            else:
                active_memories.append(mem)
        return active_memories

def clear_memories(server_name: str):
    engine = get_engine()
    with Session(engine) as session:
        statement = delete(AIMemoryTable).where(AIMemoryTable.server_name == server_name)
        session.exec(statement)
        session.commit()
