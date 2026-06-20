"""
/sync — 5-phase server discovery and brain file generator.

Phase 1: Server inventory (OS, RAM, disk, ports, services, runtimes)
Phase 2: Project discovery (scan web roots, cross-ref process managers)
Phase 3: File tracking (hash key config files per project)
Phase 4: Memory extraction (AI extracts structured facts from collected data)
Phase 5: Brain file generation (SERVER.md + per-project .md files)
"""
import json
import time
from datetime import datetime
from typing import Optional
from sqlmodel import Session, select

from cli import display
from cli.db.models import get_engine, ProjectTable, TrackedFileTable, ServerSnapshotTable
from cli.db.memory import set_memory, list_memories
from cli.db.brain import (
    generate_server_brain,
    generate_project_brain,
    save_brain_version,
    write_brain_file,
    read_brain_file,
)
from cli.db.file_tracker import track_file


# ── Phase 1: Server Inventory ─────────────────────────────────────────────────

INVENTORY_COMMANDS = [
    ("os_info",         "cat /etc/os-release 2>/dev/null | head -5 || uname -a"),
    ("uptime",          "uptime"),
    ("memory",          "free -m 2>/dev/null || vm_stat 2>/dev/null | head -5"),
    ("disk",            "df -h / 2>/dev/null | tail -1"),
    ("cpu",             "nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null"),
    ("open_ports",      "ss -tlnp 2>/dev/null || netstat -tlnp 2>/dev/null | head -20"),
    ("services",        "systemctl list-units --type=service --state=running --no-legend --no-pager 2>/dev/null | head -20 || echo 'no systemd'"),
    ("runtimes",        "node --version 2>/dev/null; python3 --version 2>/dev/null; ruby --version 2>/dev/null; go version 2>/dev/null; php --version 2>/dev/null | head -1"),
    ("tools",           "nginx -v 2>&1 | head -1; docker --version 2>/dev/null; pm2 --version 2>/dev/null; ollama --version 2>/dev/null"),
    ("firewall",        "ufw status 2>/dev/null || nft list ruleset 2>/dev/null | head -10 || echo 'no firewall detected'"),
    ("cron",            "crontab -l 2>/dev/null || echo 'no cron'"),
]

def phase1_inventory(server_name: str, ssh) -> dict:
    display.status_info("phase 1: server inventory")
    results = {}
    for key, cmd in INVENTORY_COMMANDS:
        display.status_command(cmd)
        out, code, _ = ssh.run(cmd, was_dry_run=False, confirm_all=True)
        results[key] = out.strip()

    raw_context = "\n\n".join(f"[{k}]\n{v}" for k, v in results.items())

    # Save snapshot
    engine = get_engine()
    with Session(engine) as session:
        snap = ServerSnapshotTable(
            server_name=server_name,
            captured_at=datetime.utcnow(),
            os_info=results.get("os_info", "")[:500],
            raw_context=raw_context
        )
        session.add(snap)
        session.commit()

    display.status_success(f"inventory captured — {len(INVENTORY_COMMANDS)} checks")
    return results


# ── Phase 2: Project Discovery ────────────────────────────────────────────────

SCAN_PATHS = ["/var/www", "/opt", "/home", "/srv"]

DETECT_CMDS = [
    "pm2 list --no-color 2>/dev/null | grep -v '\\-\\-\\-' | tail -n +4 || echo 'no pm2'",
    "docker ps --format '{{.Names}} {{.Ports}}' 2>/dev/null || echo 'no docker'",
    "ls /var/www/ 2>/dev/null",
    "ls /opt/ 2>/dev/null",
    "ls /etc/nginx/sites-enabled/ 2>/dev/null || echo 'no nginx'",
]

def phase2_discovery(server_name: str, ssh) -> list[str]:
    display.status_info("phase 2: project discovery")
    engine = get_engine()

    # Collect raw data
    raw_data = {}
    for cmd in DETECT_CMDS:
        out, _, _ = ssh.run(cmd, was_dry_run=False, confirm_all=True)
        raw_data[cmd[:30]] = out.strip()

    # Scan web roots for directories
    found_names = set()
    for scan_path in SCAN_PATHS:
        out, code, _ = ssh.run(f"ls -d {scan_path}/*/ 2>/dev/null", was_dry_run=False, confirm_all=True)
        if code == 0 and out.strip():
            for line in out.strip().splitlines():
                dir_path = line.strip().rstrip("/")
                if not dir_path:
                    continue
                name = dir_path.split("/")[-1]
                if name in (".", "..", "html"):
                    continue

                # Detect project type
                proj_type = "unknown"
                for check_cmd, proj_t in [
                    (f"test -f {dir_path}/package.json && echo yes", "node"),
                    (f"test -f {dir_path}/requirements.txt && echo yes", "python"),
                    (f"test -f {dir_path}/pyproject.toml && echo yes", "python"),
                    (f"test -f {dir_path}/docker-compose.yml && echo yes", "docker"),
                    (f"test -f {dir_path}/index.html && echo yes", "static"),
                ]:
                    detect_out, _, _ = ssh.run(check_cmd, was_dry_run=False, confirm_all=True)
                    if "yes" in detect_out:
                        proj_type = proj_t
                        break

                # Check git remote
                git_out, _, _ = ssh.run(f"git -C {dir_path} remote get-url origin 2>/dev/null", was_dry_run=False, confirm_all=True)
                git_branch_out, _, _ = ssh.run(f"git -C {dir_path} rev-parse --abbrev-ref HEAD 2>/dev/null", was_dry_run=False, confirm_all=True)

                with Session(engine) as session:
                    stmt = select(ProjectTable).where(
                        ProjectTable.server_name == server_name,
                        ProjectTable.name == name
                    )
                    existing = session.exec(stmt).first()
                    if existing:
                        existing.path = dir_path
                        existing.type = proj_type
                        existing.git_remote = git_out.strip() or existing.git_remote
                        existing.git_branch = git_branch_out.strip() or existing.git_branch
                        existing.updated_at = datetime.utcnow()
                        session.add(existing)
                    else:
                        project = ProjectTable(
                            server_name=server_name,
                            name=name,
                            path=dir_path,
                            type=proj_type,
                            git_remote=git_out.strip() or None,
                            git_branch=git_branch_out.strip() or None,
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow()
                        )
                        session.add(project)
                    session.commit()
                found_names.add(name)

    display.status_success(f"found {len(found_names)} projects: {', '.join(sorted(found_names)) or 'none'}")
    return list(found_names)


# ── Phase 3: File Tracking ────────────────────────────────────────────────────

SERVER_CONFIG_FILES = [
    ("/etc/nginx/nginx.conf", "nginx", False),
    ("/etc/nginx/sites-enabled/default", "nginx", False),
    ("/etc/fstab", "system", False),
    ("/etc/crontab", "cron", False),
    ("/etc/ssh/sshd_config", "ssh", False),
    ("/etc/environment", "system", False),
]

def phase3_file_tracking(server_name: str, project_names: list[str], ssh) -> int:
    display.status_info("phase 3: file tracking")
    count = 0

    # Server-level config files
    for path, category, is_sensitive in SERVER_CONFIG_FILES:
        out, code, _ = ssh.run(f"cat {path} 2>/dev/null", was_dry_run=False, confirm_all=True)
        if code == 0 and out.strip():
            track_file(server_name, path, out, category=category, is_sensitive=is_sensitive)
            count += 1

    # Per-project config files
    engine = get_engine()
    for proj_name in project_names:
        with Session(engine) as session:
            proj = session.exec(
                select(ProjectTable).where(
                    ProjectTable.server_name == server_name,
                    ProjectTable.name == proj_name
                )
            ).first()
        if not proj or not proj.path:
            continue

        proj_files = [
            (f"/etc/nginx/sites-available/{proj_name}", "nginx", False),
            (f"/etc/nginx/sites-enabled/{proj_name}", "nginx", False),
            (f"{proj.path}/.env", "env", True),           # sensitive!
            (f"{proj.path}/ecosystem.config.js", "pm2", False),
            (f"{proj.path}/docker-compose.yml", "docker", False),
            (f"/etc/systemd/system/{proj_name}.service", "systemd", False),
        ]
        for path, category, is_sensitive in proj_files:
            out, code, _ = ssh.run(f"cat {path} 2>/dev/null", was_dry_run=False, confirm_all=True)
            if code == 0 and out.strip():
                track_file(server_name, path, out, category=category,
                           project_name=proj_name, is_sensitive=is_sensitive)
                count += 1

    display.status_success(f"tracked {count} config files")
    return count


# ── Phase 4: Memory Extraction ────────────────────────────────────────────────

def phase4_memory_extraction(server_name: str, inventory: dict, project_names: list[str], ai_api_key: str, model_name: str) -> int:
    display.status_info("phase 4: memory extraction")

    # Build summary for AI
    context_parts = [f"Server: {server_name}"]
    for k, v in inventory.items():
        if v:
            context_parts.append(f"{k}: {v[:300]}")
    context_parts.append(f"Discovered projects: {', '.join(project_names)}")

    # Tracked file paths
    engine = get_engine()
    with Session(engine) as session:
        tracked = session.exec(
            select(TrackedFileTable).where(TrackedFileTable.server_name == server_name)
        ).all()
    for tf in tracked[:20]:
        if not tf.is_sensitive and tf.content_snapshot:
            context_parts.append(f"File {tf.path} ({tf.category}):\n{tf.content_snapshot[:500]}")

    context_str = "\n\n".join(context_parts)

    extraction_prompt = (
        "You are analyzing a Linux server. Given the data below, extract key facts as structured memory entries.\n"
        "Return ONLY a valid JSON array. Each item must have: key (snake_case slug), value (string), category (one of: config/deployment/incident/preference/discovery).\n"
        "Focus on: deploy commands, app ports, nginx config paths, SSL expiry, process manager names, runtime versions, key file paths.\n"
        "Max 25 memories. Do not include passwords or secret values.\n\n"
        f"SERVER DATA:\n{context_str}"
    )

    try:
        import openai
        from cli.ai import DEEPSEEK_BASE_URL
        client = openai.OpenAI(api_key=ai_api_key, base_url=DEEPSEEK_BASE_URL)
        response = client.chat.completions.create(
            model=model_name,
            max_tokens=2000,
            messages=[{"role": "user", "content": extraction_prompt}]
        )
        raw = response.choices[0].message.content.strip()

        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.split("```")[0].strip()

        memories_json = json.loads(raw)
        count = 0
        for m in memories_json:
            key = m.get("key", "").strip()
            value = m.get("value", "").strip()
            category = m.get("category", "discovery")
            if key and value:
                set_memory(server_name, key, value, source="sync_discovered", category=category, confidence=0.9)
                count += 1
        display.status_success(f"{count} memories extracted and stored")
        return count
    except Exception as e:
        display.status_warning(f"Memory extraction failed: {e}")
        return 0


# ── Phase 5: Brain File Generation ───────────────────────────────────────────

def phase5_brain_generation(server_name: str, project_names: list[str], inventory: dict) -> list[str]:
    display.status_info("phase 5: brain files")
    written = []

    # SERVER.md
    snapshot_ctx = "\n".join(f"{k}: {v}" for k, v in inventory.items() if v)
    content = generate_server_brain(server_name, snapshot_context=snapshot_ctx)
    v = save_brain_version(server_name, content, trigger="sync")
    write_brain_file(server_name, content)
    display.status_info(f"regenerating SERVER.md (v{v})...")
    written.append("SERVER.md")

    # Per-project
    for proj_name in project_names:
        proj_content = generate_project_brain(server_name, proj_name)
        pv = save_brain_version(server_name, proj_content, project_name=proj_name, trigger="sync")
        write_brain_file(server_name, proj_content, project_name=proj_name)
        display.status_info(f"regenerating {proj_name}.md (v{pv})...")
        written.append(f"{proj_name}.md")

    display.status_success(f"brain files written")
    return written


# ── Orchestrator ─────────────────────────────────────────────────────────────

def run_sync(
    server_name: str,
    ssh,
    ai_api_key: str,
    model_name: str = "deepseek-chat",
    quick: bool = False,
    only_project: Optional[str] = None,
    only_files: bool = False,
    only_memory: bool = False,
):
    start = time.time()
    print()
    display.status_info(f"Starting /sync for {server_name}")
    print()

    inventory = {}
    project_names = []

    if only_files:
        # Phase 3 only — re-read tracked files
        engine = get_engine()
        with Session(engine) as session:
            projects = session.exec(select(ProjectTable).where(ProjectTable.server_name == server_name)).all()
        project_names = [p.name for p in projects]
        phase3_file_tracking(server_name, project_names, ssh)
    elif only_memory:
        # Phase 4 only — re-extract from cached snapshot
        engine = get_engine()
        with Session(engine) as session:
            snap = session.exec(
                select(ServerSnapshotTable).where(ServerSnapshotTable.server_name == server_name)
            ).all()
        if snap:
            latest = max(snap, key=lambda s: s.captured_at)
            inventory = {"raw": latest.raw_context or ""}
        phase4_memory_extraction(server_name, inventory, [], ai_api_key, model_name)
    elif only_project:
        # Phases 2-5 for one project
        project_names = [only_project]
        phase3_file_tracking(server_name, project_names, ssh)
        phase4_memory_extraction(server_name, {}, project_names, ai_api_key, model_name)
        phase5_brain_generation(server_name, project_names, {})
    elif quick:
        # Phases 1 + 4 only
        inventory = phase1_inventory(server_name, ssh)
        phase4_memory_extraction(server_name, inventory, [], ai_api_key, model_name)
    else:
        # Full sync — all 5 phases
        inventory = phase1_inventory(server_name, ssh)
        project_names = phase2_discovery(server_name, ssh)
        phase3_file_tracking(server_name, project_names, ssh)
        phase4_memory_extraction(server_name, inventory, project_names, ai_api_key, model_name)
        phase5_brain_generation(server_name, project_names, inventory)

    elapsed = time.time() - start
    mem_count = len(list_memories(server_name))
    print()
    display.status_success(
        f"sync complete in {elapsed:.1f}s — "
        f"{len(project_names)} projects · {mem_count} memories"
    )
    
    # Auto-push to cloud database
    push_to_cloud(server_name)


def push_to_cloud(server_name: str) -> bool:
    """Fetch all local data for this server and push it to the web dashboard API."""
    import urllib.request
    import json
    import os
    from datetime import datetime
    from cli import display
    from sqlmodel import Session, select
    from cli.db.models import (
        get_engine, SessionTable, CommandTable, AIMemoryTable,
        SettingTable, ServerSnapshotTable, ProjectTable, BrainVersionTable
    )

    # 1. Determine Sync Endpoint URL
    sync_url = os.environ.get("QWERTY_SYNC_URL")
    if not sync_url:
        from cli.db import session_log
        db_settings = session_log.get_all_settings(server_name)
        sync_url = db_settings.get("cloud_sync_url")
    if not sync_url:
        sync_url = "http://localhost:3000/api/sync"
    else:
        sync_url = sync_url.rstrip("/") + "/api/sync"

    display.status_info(f"Syncing local database to cloud: {sync_url}...")

    engine = get_engine()
    def to_dict_list(statement):
        with Session(engine) as session:
            rows = session.exec(statement).all()
            result = []
            for r in rows:
                d = {}
                for col in r.__table__.columns:
                    val = getattr(r, col.name)
                    if isinstance(val, datetime):
                        d[col.name] = val.isoformat()
                    else:
                        d[col.name] = val
                result.append(d)
            return result

    try:
        sessions = to_dict_list(select(SessionTable).where(SessionTable.server_name == server_name))
        commands = to_dict_list(select(CommandTable).where(CommandTable.server_name == server_name))
        memories = to_dict_list(select(AIMemoryTable).where(AIMemoryTable.server_name == server_name))
        settings = to_dict_list(select(SettingTable).where((SettingTable.server_name == server_name) | (SettingTable.server_name == None)))
        snapshots = to_dict_list(select(ServerSnapshotTable).where(ServerSnapshotTable.server_name == server_name))
        projects = to_dict_list(select(ProjectTable).where(ProjectTable.server_name == server_name))
        brain_versions = to_dict_list(select(BrainVersionTable).where(BrainVersionTable.server_name == server_name))

        payload = {
            "sessions": sessions,
            "commands": commands,
            "memories": memories,
            "settings": settings,
            "snapshots": snapshots,
            "projects": projects,
            "brain_versions": brain_versions
        }

        req = urllib.request.Request(
            sync_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=10) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            if res_data.get("success"):
                display.status_success("Cloud sync complete!")
                return True
            else:
                display.status_warning(f"Cloud sync completed with warnings: {res_data.get('error')}")
                return False

    except Exception as e:
        display.status_warning(f"Cloud sync connection failed: {e}")
        display.status_warning("Make sure the Next.js web application is running locally or configured correctly.")
        return False
