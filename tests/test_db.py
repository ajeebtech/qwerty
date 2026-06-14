import pytest
from datetime import datetime
from unittest.mock import patch
from sqlmodel import SQLModel, create_engine

import cli.db.models as models
import cli.db.session_log as session_log
import cli.db.memory as memory

@pytest.fixture(autouse=True)
def mock_db_engine():
    # Setup in-memory SQLite engine
    test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    
    with patch("cli.db.models.get_engine", return_value=test_engine), \
         patch("cli.db.session_log.get_engine", return_value=test_engine), \
         patch("cli.db.memory.get_engine", return_value=test_engine):
        models.init_db()
        yield test_engine

def test_session_lifecycle():
    sess = session_log.create_session("prod", "1.2.3.4", "ubuntu", "deploy")
    assert sess.id is not None
    assert sess.server_name == "prod"
    assert sess.mode == "deploy"
    assert sess.ended_at is None
    
    session_log.end_session(sess.id, command_count=5, notes="Succesful deployment")
    
    history = session_log.get_session_history("prod")
    assert len(history) == 1
    assert history[0].command_count == 5
    assert history[0].notes == "Succesful deployment"
    assert history[0].ended_at is not None

def test_log_command():
    sess = session_log.create_session("prod", "1.2.3.4", "ubuntu", "general")
    cmd = session_log.log_command(
        session_id=sess.id,
        server_name="prod",
        command="nginx -t",
        description="Check nginx configuration",
        output="nginx syntax is ok",
        exit_code=0,
        duration_ms=120,
        was_dry_run=False
    )
    assert cmd.id is not None
    assert cmd.command == "nginx -t"
    
    cmds = session_log.get_commands_for_session(sess.id)
    assert len(cmds) == 1
    assert cmds[0].command == "nginx -t"

def test_ai_memory_crud():
    memory.set_memory("prod", "port", "8080", source="ai_inferred")
    m = memory.get_memory("prod", "port")
    assert m is not None
    assert m.value == "8080"
    
    mems = memory.list_memories("prod")
    assert len(mems) == 1
    assert mems[0].key == "port"
    
    memory.forget_memory("prod", "port")
    assert memory.get_memory("prod", "port") is None

def test_settings_crud():
    session_log.set_setting("confirm_all", True)
    assert session_log.get_setting("confirm_all") is True
    
    # Scoped override
    session_log.set_setting("confirm_all", False, server_name="prod")
    assert session_log.get_setting("confirm_all", server_name="prod") is False
    assert session_log.get_setting("confirm_all", server_name="staging") is True
