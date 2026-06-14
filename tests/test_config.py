import os
import pytest
from pathlib import Path
from unittest.mock import patch

import cli.config as config

@pytest.fixture(autouse=True)
def mock_config_paths(tmp_path):
    temp_dir = tmp_path / ".vibe-server"
    temp_path = temp_dir / "config.yaml"
    with patch("cli.config.CONFIG_DIR", temp_dir), \
         patch("cli.config.CONFIG_PATH", temp_path):
        yield temp_dir, temp_path

def test_load_config_default():
    cfg = config.load_config()
    assert cfg["default_server"] is None
    assert cfg["anthropic_api_key"] is None
    assert cfg["servers"] == {}

def test_add_and_get_server_profile():
    config.add_server(
        name="test_prod",
        host="1.2.3.4",
        user="ubuntu",
        port=2222,
        key_path="~/key.pem",
        hoster="aws"
    )
    
    profile = config.get_server_profile("test_prod")
    assert profile["host"] == "1.2.3.4"
    assert profile["user"] == "ubuntu"
    assert profile["port"] == 2222
    assert profile["key_path"] == "~/key.pem"
    assert profile["hoster"] == "aws"

def test_remove_server():
    config.add_server("test_stage", "1.1.1.1", "root")
    assert "test_stage" in config.load_config()["servers"]
    
    config.remove_server("test_stage")
    assert "test_stage" not in config.load_config()["servers"]

def test_set_default_server():
    config.add_server("s1", "1.2.3.4", "root")
    config.add_server("s2", "5.6.7.8", "root")
    
    config.set_default_server("s2")
    assert config.get_default_server() == "s2"

def test_get_api_key_override():
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "env_key"}):
        assert config.get_api_key() == "env_key"
        
    # Test fallback to config file
    with patch.dict(os.environ, {}, clear=True):
        cfg = config.load_config()
        cfg["anthropic_api_key"] = "file_key"
        config.save_config(cfg)
        assert config.get_api_key() == "file_key"
