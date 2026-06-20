"""
Context assembler — builds rich system prompt context at session start.
Loads brain files, top memories, and last session summary.
"""
from typing import Optional
from sqlmodel import Session, select
from cli.db.models import get_engine, SessionTable
from cli.db.memory import list_memories_top, bump_access
from cli.db.brain import read_brain_file

MAX_BRAIN_CHARS = 6000    # cap brain file injection to avoid bloating prompt
MAX_MEMORY_COUNT = 20


def assemble_context(server_name: str) -> str:
    """
    Assemble a rich context string to prepend into the AI system prompt.
    Returns a multi-section string covering brain files, memories, and last session.
    """
    parts = []

    # 1. SERVER.md brain file
    server_brain = read_brain_file(server_name)
    if server_brain:
        content = server_brain[:MAX_BRAIN_CHARS]
        if len(server_brain) > MAX_BRAIN_CHARS:
            content += "\n... [brain file truncated for context budget]"
        parts.append(f"--- SERVER BRAIN (SERVER.md) ---\n{content}")

    # 2. Top memories by access frequency
    top_memories = list_memories_top(server_name, limit=MAX_MEMORY_COUNT)
    if top_memories:
        mem_lines = []
        for m in top_memories:
            bump_access(server_name, m.key)
            cat = f"[{m.category}] " if m.category else ""
            mem_lines.append(f"  {cat}{m.key}: {m.value}")
        parts.append("--- REMEMBERED SERVER FACTS ---\n" + "\n".join(mem_lines))

    # 3. Last session summary
    last_summary = _get_last_session_summary(server_name)
    if last_summary:
        parts.append(f"--- LAST SESSION SUMMARY ---\n{last_summary}")

    if not parts:
        return ""

    return "\n\n".join(parts)


def _get_last_session_summary(server_name: str) -> Optional[str]:
    """Return the AI-generated summary from the most recent completed session."""
    engine = get_engine()
    with Session(engine) as session:
        stmt = select(SessionTable).where(
            SessionTable.server_name == server_name,
            SessionTable.ended_at != None,
            SessionTable.summary != None
        )
        rows = session.exec(stmt).all()
        if not rows:
            return None
        latest = max(rows, key=lambda r: r.ended_at)
        return latest.summary


def generate_session_summary(conversation_history: list, api_key: str, model_name: str) -> str:
    """
    Call AI to generate a 3-5 sentence summary of what happened in this session.
    Called at /exit time.
    """
    try:
        import openai
        from cli.ai import DEEPSEEK_BASE_URL
        client = openai.OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)
        summary_prompt = (
            "The following is a conversation log of a Linux server management session. "
            "Write a concise 3-5 sentence summary of what was accomplished, what commands were run, "
            "and any issues or tasks left incomplete. Be specific — mention file paths, service names, "
            "and version numbers where relevant. Do not include any markdown or bullet points."
        )
        response = client.chat.completions.create(
            model=model_name,
            max_tokens=300,
            messages=[
                {"role": "system", "content": summary_prompt},
                *conversation_history[-20:]
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return ""
