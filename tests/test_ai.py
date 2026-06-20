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

@patch("cli.ai.openai.OpenAI")
def test_call_ai_pipeline_non_streaming(mock_openai_cls):
    mock_client = mock_openai_cls.return_value
    
    # Mock return value of create method
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = '{"narration": "Test narration", "plan": []}'
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_response
    
    res = ai.call_ai_pipeline(
        api_key="fake-key",
        system_prompt="SYS",
        messages=[],
        show_stream=False
    )
    
    assert res["narration"] == "Test narration"
    assert res["plan"] == []

@patch("cli.ai.openai.OpenAI")
def test_call_ai_pipeline_invalid_json_retry(mock_openai_cls):
    mock_client = mock_openai_cls.return_value
    
    # Mocking first call to return invalid JSON, and second recursive call to return valid JSON
    mock_response_invalid = MagicMock()
    mock_choice_invalid = MagicMock()
    mock_choice_invalid.message.content = 'invalid json'
    mock_response_invalid.choices = [mock_choice_invalid]
    
    mock_response_valid = MagicMock()
    mock_choice_valid = MagicMock()
    mock_choice_valid.message.content = '{"narration": "Fixed narration", "plan": []}'
    mock_response_valid.choices = [mock_choice_valid]
    
    mock_client.chat.completions.create.side_effect = [
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

@patch("cli.ai.openai.OpenAI")
def test_call_final_response(mock_openai_cls):
    mock_client = mock_openai_cls.return_value
    
    # Mock stream generator chunks
    mock_chunk1 = MagicMock()
    mock_chunk1.choices = [MagicMock()]
    mock_chunk1.choices[0].delta.content = "This "
    
    mock_chunk2 = MagicMock()
    mock_chunk2.choices = [MagicMock()]
    mock_chunk2.choices[0].delta.content = "is "
    
    mock_chunk3 = MagicMock()
    mock_chunk3.choices = [MagicMock()]
    mock_chunk3.choices[0].delta.content = "a "
    
    mock_chunk4 = MagicMock()
    mock_chunk4.choices = [MagicMock()]
    mock_chunk4.choices[0].delta.content = "test."
    
    mock_client.chat.completions.create.return_value = [
        mock_chunk1, mock_chunk2, mock_chunk3, mock_chunk4
    ]
    
    res = ai.call_final_response(
        api_key="fake-key",
        system_prompt="SYS",
        messages=[]
    )
    
    assert res == "This is a test."
