from datetime import datetime
from typing import Optional
from sqlmodel import Session, select, delete
from cli.db.models import get_engine, AIMemoryTable

def set_memory(
    server_name: str,
    key: str,
    value: str,
    source: str = "ai_inferred",
    category: Optional[str] = None,
    confidence: float = 0.8,
    expires_at: Optional[datetime] = None
) -> AIMemoryTable:
    """Upsert a memory. user_set memories are never overwritten by ai_inferred."""
    engine = get_engine()
    with Session(engine) as session:
        statement = select(AIMemoryTable).where(
            AIMemoryTable.server_name == server_name,
            AIMemoryTable.key == key
        )
        db_memory = session.exec(statement).first()
        if db_memory:
            # Never overwrite a user_set memory with an AI-inferred one
            if db_memory.source == "user_set" and source == "ai_inferred":
                return db_memory
            db_memory.value = value
            db_memory.source = source
            db_memory.category = category or db_memory.category
            db_memory.confidence = confidence
            db_memory.updated_at = datetime.utcnow()
            db_memory.expires_at = expires_at
        else:
            db_memory = AIMemoryTable(
                server_name=server_name,
                key=key,
                value=value,
                source=source,
                category=category,
                confidence=confidence,
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
        if memory and memory.expires_at and memory.expires_at < datetime.utcnow():
            session.delete(memory)
            session.commit()
            return None
        return memory

def bump_access(server_name: str, key: str):
    """Increment times_accessed and update last_accessed_at for a memory."""
    engine = get_engine()
    with Session(engine) as session:
        statement = select(AIMemoryTable).where(
            AIMemoryTable.server_name == server_name,
            AIMemoryTable.key == key
        )
        mem = session.exec(statement).first()
        if mem:
            mem.times_accessed = (mem.times_accessed or 0) + 1
            mem.last_accessed_at = datetime.utcnow()
            session.add(mem)
            session.commit()

def list_memories(server_name: str, category: Optional[str] = None) -> list[AIMemoryTable]:
    """Return all active memories, optionally filtered by category."""
    engine = get_engine()
    with Session(engine) as session:
        statement = select(AIMemoryTable).where(AIMemoryTable.server_name == server_name)
        if category:
            statement = statement.where(AIMemoryTable.category == category)
        memories = session.exec(statement).all()
        active = []
        now = datetime.utcnow()
        for mem in memories:
            if mem.expires_at and mem.expires_at < now:
                session.delete(mem)
                session.commit()
            else:
                active.append(mem)
        return active

def list_memories_top(server_name: str, limit: int = 30) -> list[AIMemoryTable]:
    """Return the top N memories sorted by times_accessed descending."""
    mems = list_memories(server_name)
    return sorted(mems, key=lambda m: m.times_accessed or 0, reverse=True)[:limit]

def search_memories(server_name: str, query: str) -> list[AIMemoryTable]:
    """Keyword search across key and value fields (case-insensitive)."""
    q = query.lower()
    return [
        m for m in list_memories(server_name)
        if q in m.key.lower() or q in m.value.lower()
    ]

def clear_memories(server_name: str):
    engine = get_engine()
    with Session(engine) as session:
        statement = delete(AIMemoryTable).where(AIMemoryTable.server_name == server_name)
        session.exec(statement)
        session.commit()
