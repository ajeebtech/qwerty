"""
File tracker — track every file vibe-server reads or writes.
Stores content hash for external-change detection.
Records before/after versions for /undo.
"""
import hashlib
import difflib
from datetime import datetime, timedelta
from typing import Optional
from sqlmodel import Session, select
from cli.db.models import get_engine, TrackedFileTable, FileVersionTable

CONTENT_CAP = 50_000   # max bytes stored as snapshot
STALE_MINUTES = 10     # re-read file if not read in this many minutes


# ── Helpers ───────────────────────────────────────────────────────────────────

def _sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8", errors="replace")).hexdigest()

def _unified_diff(before: str, after: str, path: str) -> str:
    lines_before = before.splitlines(keepends=True)
    lines_after = after.splitlines(keepends=True)
    diff = difflib.unified_diff(lines_before, lines_after, fromfile=f"a{path}", tofile=f"b{path}")
    return "".join(diff)


# ── Track ─────────────────────────────────────────────────────────────────────

def track_file(
    server_name: str,
    path: str,
    content: str,
    category: Optional[str] = None,
    project_name: Optional[str] = None,
    is_sensitive: bool = False
) -> TrackedFileTable:
    """Create or update a tracked file record."""
    engine = get_engine()
    with Session(engine) as session:
        stmt = select(TrackedFileTable).where(
            TrackedFileTable.server_name == server_name,
            TrackedFileTable.path == path
        )
        tf = session.exec(stmt).first()
        capped = content[:CONTENT_CAP]
        h = _sha256(content)
        now = datetime.utcnow()
        if tf:
            tf.content_hash = h
            tf.content_snapshot = capped if not is_sensitive else None
            tf.last_read_at = now
            tf.category = category or tf.category
            tf.project_name = project_name or tf.project_name
            tf.is_sensitive = is_sensitive
        else:
            tf = TrackedFileTable(
                server_name=server_name,
                path=path,
                category=category,
                project_name=project_name,
                content_hash=h,
                content_snapshot=capped if not is_sensitive else None,
                last_read_at=now,
                is_sensitive=is_sensitive,
                created_at=now
            )
        session.add(tf)
        session.commit()
        session.refresh(tf)
        return tf


def get_tracked_file(server_name: str, path: str) -> Optional[TrackedFileTable]:
    engine = get_engine()
    with Session(engine) as session:
        stmt = select(TrackedFileTable).where(
            TrackedFileTable.server_name == server_name,
            TrackedFileTable.path == path
        )
        return session.exec(stmt).first()


def is_stale(tf: TrackedFileTable) -> bool:
    """Return True if the file hasn't been re-read in STALE_MINUTES."""
    if not tf.last_read_at:
        return True
    return datetime.utcnow() - tf.last_read_at > timedelta(minutes=STALE_MINUTES)


def check_freshness(server_name: str, path: str, ssh) -> dict:
    """
    Re-read the file from the server if stale or not tracked.
    Returns a dict:
      { "changed": bool, "diff": str|None, "current_content": str, "tracked_file": TrackedFileTable }
    """
    tf = get_tracked_file(server_name, path)
    # Read current content from server
    current_content, exit_code, _ = ssh.run(f"cat {path}", was_dry_run=False, confirm_all=False, disable_hooks=True)
    if exit_code != 0:
        return {"changed": False, "diff": None, "current_content": "", "tracked_file": tf}

    current_hash = _sha256(current_content)

    if tf is None:
        # First time seeing this file — just track it
        tf = track_file(server_name, path, current_content)
        return {"changed": False, "diff": None, "current_content": current_content, "tracked_file": tf}

    if tf.content_hash != current_hash:
        # File changed externally
        old_content = tf.content_snapshot or ""
        diff = _unified_diff(old_content, current_content, path)
        # Update tracking
        track_file(server_name, path, current_content, category=tf.category, project_name=tf.project_name, is_sensitive=tf.is_sensitive)
        return {"changed": True, "diff": diff, "current_content": current_content, "tracked_file": tf}

    return {"changed": False, "diff": None, "current_content": current_content, "tracked_file": tf}


# ── Version Recording ─────────────────────────────────────────────────────────

def record_file_version(
    tracked_file_id: int,
    server_name: str,
    file_path: str,
    content_before: str,
    content_after: str,
    session_id: Optional[int] = None,
    reason: Optional[str] = None,
    user_prompt: Optional[str] = None
) -> FileVersionTable:
    """Log a before/after version of a file write."""
    engine = get_engine()
    with Session(engine) as db_session:
        # Get next version number for this file
        stmt = select(FileVersionTable).where(
            FileVersionTable.tracked_file_id == tracked_file_id
        )
        existing = db_session.exec(stmt).all()
        version_num = (max((v.version_number for v in existing), default=0)) + 1

        diff = _unified_diff(content_before, content_after, file_path)
        fv = FileVersionTable(
            tracked_file_id=tracked_file_id,
            session_id=session_id,
            server_name=server_name,
            file_path=file_path,
            version_number=version_num,
            content_before=content_before,
            content_after=content_after,
            diff=diff,
            change_reason=reason,
            user_prompt=user_prompt,
            changed_at=datetime.utcnow()
        )
        db_session.add(fv)
        db_session.commit()
        db_session.refresh(fv)
        return fv


def get_last_version(server_name: str, path: str) -> Optional[FileVersionTable]:
    """Return the most recent file version for a given path."""
    engine = get_engine()
    with Session(engine) as session:
        stmt = select(FileVersionTable).where(
            FileVersionTable.server_name == server_name,
            FileVersionTable.file_path == path
        )
        versions = session.exec(stmt).all()
        if not versions:
            return None
        return max(versions, key=lambda v: v.version_number)


def get_version(server_name: str, path: str, version_number: int) -> Optional[FileVersionTable]:
    engine = get_engine()
    with Session(engine) as session:
        stmt = select(FileVersionTable).where(
            FileVersionTable.server_name == server_name,
            FileVersionTable.file_path == path,
            FileVersionTable.version_number == version_number
        )
        return session.exec(stmt).first()


def list_versions(server_name: str, path: Optional[str] = None) -> list[FileVersionTable]:
    engine = get_engine()
    with Session(engine) as session:
        stmt = select(FileVersionTable).where(FileVersionTable.server_name == server_name)
        if path:
            stmt = stmt.where(FileVersionTable.file_path == path)
        return list(session.exec(stmt).all())


def restore_version(
    server_name: str,
    path: str,
    version_number: int,
    ssh,
    session_id: Optional[int] = None
) -> tuple[bool, str]:
    """
    Restore a file to a specific version by writing content_before of that version.
    Returns (success: bool, message: str).
    """
    fv = get_version(server_name, path, version_number)
    if not fv:
        return False, f"Version {version_number} not found for {path}"

    restore_content = fv.content_before
    if not restore_content:
        return False, "No content_before stored for this version — cannot restore."

    # Write via SSH using heredoc
    escaped = restore_content.replace("'", "'\\''")
    write_cmd = f"cat > {path} << 'VIBE_RESTORE_EOF'\n{restore_content}\nVIBE_RESTORE_EOF"
    _, exit_code, _ = ssh.run(write_cmd, was_dry_run=False, confirm_all=True, disable_hooks=True)

    if exit_code != 0:
        return False, f"Failed to write restored content to {path}"

    # Re-track the restored content
    tf = get_tracked_file(server_name, path)
    if tf:
        track_file(server_name, path, restore_content, category=tf.category, project_name=tf.project_name, is_sensitive=tf.is_sensitive)

    # Mark the version as reverted
    engine = get_engine()
    with Session(engine) as db_session:
        stmt = select(FileVersionTable).where(
            FileVersionTable.server_name == server_name,
            FileVersionTable.file_path == path,
            FileVersionTable.version_number == version_number
        )
        row = db_session.exec(stmt).first()
        if row:
            row.reverted_at = datetime.utcnow()
            db_session.add(row)
            db_session.commit()

    return True, f"Restored {path} to version {version_number}"
