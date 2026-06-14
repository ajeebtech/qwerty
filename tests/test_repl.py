import pytest
from unittest.mock import MagicMock, patch
from cli.repl import REPLSession
from cli.db import session_log

@pytest.fixture(autouse=True)
def mock_db_engine():
    from sqlmodel import create_engine
    import cli.db.models as models
    test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    with patch("cli.db.models.get_engine", return_value=test_engine), \
         patch("cli.db.session_log.get_engine", return_value=test_engine), \
         patch("cli.db.memory.get_engine", return_value=test_engine):
        models.init_db()
        yield test_engine

@patch("cli.repl.SSHManager")
@patch("cli.repl.config.get_server_profile")
def test_repl_execute_ai_turn(mock_profile, mock_ssh_cls):
    mock_profile.return_value = {
        "host": "127.0.0.1",
        "user": "root",
        "port": 22
    }
    
    mock_ssh = mock_ssh_cls.return_value
    mock_ssh.run.return_value = ("Ubuntu 22.04", 0, 100)
    
    session = REPLSession("dev-vps", initial_mode="general", dry_run=False)
    session.connect()
    
    # Verify SSH initialized with default log_color "dim"
    mock_ssh_cls.assert_called_once_with(
        host="127.0.0.1",
        user="root",
        port=22,
        key_path=None,
        password=None,
        log_color="dim"
    )
    
    # Mock AI pipeline calls
    with patch("cli.repl.ai.call_ai_pipeline") as mock_pipeline, \
         patch("cli.repl.ai.call_final_response") as mock_final:
         
        mock_pipeline.return_value = {
            "plan": [{"description": "check OS", "command": "uname"}],
            "narration": "Checking OS",
            "warnings": [],
            "follow_up": "Check memory next"
        }
        mock_final.return_value = "This is a summary response."
        
        session.execute_ai_turn("what OS is this?", "fake-key")
        
        # Verify call_ai_pipeline was called with user message
        mock_pipeline.assert_called_once()
        
        # Verify call_final_response was called
        mock_final.assert_called_once()
        
        # Check alternating roles in conversation history:
        # 0: user (original prompt)
        # 1: assistant (plan + narration)
        # 2: user (command outputs + follow up suggestion)
        # 3: assistant (final summary)
        history = session.conversation_history
        assert len(history) == 4
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "what OS is this?"
        assert history[1]["role"] == "assistant"
        assert "Plan:" in history[1]["content"]
        assert "Checking OS" in history[1]["content"]
        
        assert history[2]["role"] == "user"
        assert "Outputs:" in history[2]["content"]
        assert "uname" in history[2]["content"]
        assert "Follow up suggestion: Check memory next" in history[2]["content"]
        
        assert history[3]["role"] == "assistant"
        assert history[3]["content"] == "This is a summary response."
