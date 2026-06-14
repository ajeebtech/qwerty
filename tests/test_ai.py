import pytest
import json
from unittest.mock import MagicMock, patch

import cli.ai as ai

def test_assemble_system_prompt():
    prompt = ai.assemble_system_prompt(
        mode_overlay="MODE_INSTRUCTIONS",
        hoster_overlay="PROVIDER_INSTRUCTIONS",
        snapshot_context="SNAPSHOT_CONTEXT",
        memories=[],
        settings={"ai_verbosity": "verbose"}
    )
    
    assert "expert Linux systems administrator" in prompt
    assert "MODE_INSTRUCTIONS" in prompt
    assert "PROVIDER_INSTRUCTIONS" in prompt
    assert "SNAPSHOT_CONTEXT" in prompt
    assert "verbose" in prompt
    assert "narration" in prompt

def test_clean_json_response():
    raw_markdown = "```json\n{\n  \"plan\": []\n}\n```"
    cleaned = ai.clean_json_response(raw_markdown)
    assert cleaned == "{\n  \"plan\": []\n}"

@patch("cli.ai.anthropic.Anthropic")
def test_call_ai_pipeline_non_streaming(mock_anthropic_cls):
    mock_client = mock_anthropic_cls.return_value
    
    # Mock return value of create method
    mock_response = MagicMock()
    mock_response.content = [
        MagicMock(text='{"narration": "Test narration", "plan": []}')
    ]
    mock_client.messages.create.return_value = mock_response
    
    res = ai.call_ai_pipeline(
        api_key="fake-key",
        system_prompt="SYS",
        messages=[],
        show_stream=False
    )
    
    assert res["narration"] == "Test narration"
    assert res["plan"] == []

@patch("cli.ai.anthropic.Anthropic")
def test_call_ai_pipeline_invalid_json_retry(mock_anthropic_cls):
    mock_client = mock_anthropic_cls.return_value
    
    # Mocking first call to return invalid JSON, and second recursive call to return valid JSON
    mock_response_invalid = MagicMock()
    mock_response_invalid.content = [
        MagicMock(text='invalid json')
    ]
    mock_response_valid = MagicMock()
    mock_response_valid.content = [
        MagicMock(text='{"narration": "Fixed narration", "plan": []}')
    ]
    
    mock_client.messages.create.side_effect = [
        mock_response_invalid,  # Attempt 1 (non-stream recursive call has show_stream=False)
        mock_response_valid     # Attempt 2 (retry)
    ]
    
    res = ai.call_ai_pipeline(
        api_key="fake-key",
        system_prompt="SYS",
        messages=[],
        show_stream=False
    )
    
    assert res["narration"] == "Fixed narration"

@patch("cli.ai.anthropic.Anthropic")
def test_call_final_response(mock_anthropic_cls):
    mock_client = mock_anthropic_cls.return_value
    
    # Mock return value of streaming
    mock_stream = MagicMock()
    mock_stream.text_stream = ["This ", "is ", "a ", "test."]
    
    # Return mock stream when entering context manager
    mock_client.messages.stream.return_value.__enter__.return_value = mock_stream
    
    res = ai.call_final_response(
        api_key="fake-key",
        system_prompt="SYS",
        messages=[]
    )
    
    assert res == "This is a test."
