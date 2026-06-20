"""
Brain file system.
Generates, versions, writes, and reads server/project brain markdown files.
Brain files live at:  ~/.qwerty/brains/{server_name}/SERVER.md
                      ~/.qwerty/brains/{server_name}/{project_name}.md
"""
import difflib
from datetime import datetime
from pathlib import Path
from typing import Optional
from sqlmodel import Session, select
from cli.db.models import get_engine, BrainVersionTable, ProjectTable, TrackedFileTable
from cli.db.memory import list_memories
from cli.env import get_base_dir

BRAINS_DIR = get_base_dir() / "brains"


# ── Directory helpers ─────────────────────────────────────────────────────────

def _brain_dir(server_name: str) -> Path:
    d = BRAINS_DIR / server_name
    d.mkdir(parents=True, exist_ok=True)
    return d

def _brain_path(server_name: str, project_name: Optional[str] = None) -> Path:
    filename = f"{project_name}.md" if project_name else "SERVER.md"
    return _brain_dir(server_name) / filename


# ── File I/O ──────────────────────────────────────────────────────────────────

def write_brain_file(server_name: str, content: str, project_name: Optional[str] = None):
    path = _brain_path(server_name, project_name)
    path.write_text(content, encoding="utf-8")

def read_brain_file(server_name: str, project_name: Optional[str] = None) -> Optional[str]:
    path = _brain_path(server_name, project_name)
    if path.exists():
        return path.read_text(encoding="utf-8")
    return None


# ── Versioning ────────────────────────────────────────────────────────────────

def _next_version(server_name: str, project_name: Optional[str]) -> int:
    engine = get_engine()
    with Session(engine) as session:
        stmt = select(BrainVersionTable).where(
            BrainVersionTable.server_name == server_name,
            BrainVersionTable.project_name == project_name
        )
        rows = session.exec(stmt).all()
        return (max((r.version_number for r in rows), default=0)) + 1

def save_brain_version(
    server_name: str,
    content: str,
    project_name: Optional[str] = None,
    trigger: str = "sync",
    summary: Optional[str] = None
) -> int:
    """Store a new versioned snapshot of a brain file. Returns the version number."""
    version = _next_version(server_name, project_name)
    engine = get_engine()
    with Session(engine) as session:
        row = BrainVersionTable(
            server_name=server_name,
            project_name=project_name,
            version_number=version,
            trigger=trigger,
            content=content,
            summary_of_changes=summary,
            created_at=datetime.utcnow()
        )
        session.add(row)
        session.commit()
    return version

def list_brain_versions(server_name: str, project_name: Optional[str] = None) -> list[BrainVersionTable]:
    engine = get_engine()
    with Session(engine) as session:
        stmt = select(BrainVersionTable).where(
            BrainVersionTable.server_name == server_name,
            BrainVersionTable.project_name == project_name
        )
        return list(session.exec(stmt).all())

def get_brain_version(server_name: str, version_number: int, project_name: Optional[str] = None) -> Optional[BrainVersionTable]:
    engine = get_engine()
    with Session(engine) as session:
        stmt = select(BrainVersionTable).where(
            BrainVersionTable.server_name == server_name,
            BrainVersionTable.project_name == project_name,
            BrainVersionTable.version_number == version_number
        )
        return session.exec(stmt).first()

def diff_brain_versions(
    server_name: str,
    v1: int,
    v2: int,
    project_name: Optional[str] = None
) -> str:
    """Return unified diff between two brain versions."""
    bv1 = get_brain_version(server_name, v1, project_name)
    bv2 = get_brain_version(server_name, v2, project_name)
    if not bv1 or not bv2:
        return "One or both versions not found."
    lines1 = bv1.content.splitlines(keepends=True)
    lines2 = bv2.content.splitlines(keepends=True)
    label = project_name or "SERVER"
    diff = difflib.unified_diff(lines1, lines2, fromfile=f"{label} v{v1}", tofile=f"{label} v{v2}")
    return "".join(diff) or "No differences."


# ── Generation ────────────────────────────────────────────────────────────────

def generate_server_brain(server_name: str, snapshot_context: Optional[str] = None) -> str:
    """
    Build the SERVER.md content from stored data.
    snapshot_context: raw text from the latest ServerSnapshotTable.raw_context
    """
    lines = [
        f"# SERVER BRAIN — {server_name}",
        f"Last synced: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')} | Brain version: {_next_version(server_name, None)}",
        "",
    ]

    # Server snapshot section
    if snapshot_context:
        lines += ["## System Info", "```", snapshot_context.strip(), "```", ""]

    # Projects
    engine = get_engine()
    with Session(engine) as session:
        projects = session.exec(
            select(ProjectTable).where(ProjectTable.server_name == server_name)
        ).all()

    if projects:
        lines.append("## Projects")
        for p in projects:
            parts = [f"[{p.name}]"]
            if p.type:
                parts.append(p.type)
            if p.path:
                parts.append(f"path: {p.path}")
            if p.port:
                parts.append(f"port: {p.port}")
            if p.process_manager:
                parts.append(f"via {p.process_manager}")
            if p.domain:
                parts.append(f"domain: {p.domain}")
            lines.append("- " + " · ".join(parts))
        lines.append("")

    # Tracked files summary
    with Session(engine) as session:
        tracked = session.exec(
            select(TrackedFileTable).where(
                TrackedFileTable.server_name == server_name,
                TrackedFileTable.project_name == None
            )
        ).all()

    if tracked:
        lines.append("## Tracked Server Files")
        for f in tracked:
            tag = " [sensitive]" if f.is_sensitive else ""
            lines.append(f"- {f.path} ({f.category or 'other'}){tag}")
        lines.append("")

    # Memories
    memories = list_memories(server_name)
    if memories:
        lines.append("## Known Facts")
        for m in sorted(memories, key=lambda x: x.category or ""):
            cat = f"[{m.category}] " if m.category else ""
            lines.append(f"- {cat}{m.key}: {m.value}")
        lines.append("")

    return "\n".join(lines)


def generate_project_brain(server_name: str, project_name: str) -> str:
    """Build the {project}.md content from stored data."""
    engine = get_engine()
    with Session(engine) as session:
        project = session.exec(
            select(ProjectTable).where(
                ProjectTable.server_name == server_name,
                ProjectTable.name == project_name
            )
        ).first()

        tracked = session.exec(
            select(TrackedFileTable).where(
                TrackedFileTable.server_name == server_name,
                TrackedFileTable.project_name == project_name
            )
        ).all()

    lines = [
        f"# PROJECT BRAIN — {project_name} ({server_name})",
        f"Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')} | Version: {_next_version(server_name, project_name)}",
        "",
    ]

    if project:
        lines.append("## Location")
        if project.path:
            lines.append(f"- Path: {project.path}")
        if project.git_remote:
            lines.append(f"- Git remote: {project.git_remote}")
        if project.git_branch:
            lines.append(f"- Branch: {project.git_branch}")
        lines.append("")

        lines.append("## Runtime")
        if project.type:
            lines.append(f"- Type: {project.type}")
        if project.runtime_version:
            lines.append(f"- Runtime: {project.runtime_version}")
        if project.process_manager:
            lines.append(f"- Process manager: {project.process_manager}" +
                         (f" | Process: {project.process_name}" if project.process_name else ""))
        if project.port:
            lines.append(f"- Port: {project.port}" + (f" | Domain: {project.domain}" if project.domain else ""))
        lines.append("")

    if tracked:
        lines.append("## Key Files")
        for f in tracked:
            tag = " [sensitive — keys only]" if f.is_sensitive else ""
            lines.append(f"- {f.path} ({f.category or 'other'}){tag}")
        lines.append("")

    # Project-scoped memories
    proj_memories = [m for m in list_memories(server_name) if True]  # all for now, could scope by key prefix
    if proj_memories:
        lines.append("## Known Facts")
        for m in proj_memories:
            cat = f"[{m.category}] " if m.category else ""
            lines.append(f"- {cat}{m.key}: {m.value}")
        lines.append("")

    return "\n".join(lines)
