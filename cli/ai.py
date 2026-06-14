import os
import re
import sys
import json
import time
import anthropic
from cli import display

def assemble_system_prompt(
    mode_overlay: str,
    hoster_overlay: str,
    snapshot_context: str | None,
    memories: list,
    settings: dict
) -> str:
    parts = []
    
    # 1. Base personality
    parts.append(
        "You are an expert Linux systems administrator. You are transparent, specific, and precise. "
        "You NEVER guess or assume; if you don't know, say so. You provide clean, working shell commands."
    )
    
    # 2. Mode overlay
    if mode_overlay:
        parts.append(f"--- MODE INSTANCES ---\n{mode_overlay}")
        
    # 3. Hoster overlay
    if hoster_overlay:
        parts.append(f"--- CLOUD PROVIDER INSTANCES ---\n{hoster_overlay}")
        
    # 4. Server context
    if snapshot_context:
        parts.append(f"--- SERVER SNAPSHOT SYSTEM CONTEXT ---\n{snapshot_context}")
        
    # 5. AI memory
    if memories:
        mem_str = "\n".join([f"- {m.key}: {m.value} (source: {m.source})" for m in memories])
        parts.append(f"--- REMEMBERED SERVER FACTS (AI MEMORY) ---\n{mem_str}")
        
    # 6. User preferences
    pref_parts = []
    pref_parts.append(f"AI Verbosity level: {settings.get('ai_verbosity', 'normal')}")
    pref_parts.append(f"Preferred editor: {settings.get('preferred_editor', 'nano')}")
    pref_parts.append(f"Preferred process manager: {settings.get('preferred_process_manager', 'pm2')}")
    pref_parts.append(f"Preferred web server: {settings.get('preferred_web_server', 'nginx')}")
    parts.append(f"--- USER PREFERENCES ---\n" + "\n".join(pref_parts))

    # 7. JSON Format Instructions
    parts.append(
        "--- RESPONSE JSON SCHEMA ---\n"
        "You MUST respond ONLY with a single valid JSON object. Do not include markdown codeblocks or wrap in ```json ... ```. "
        "To support real-time streaming, the key \"narration\" MUST be the VERY FIRST key in your JSON object. "
        "The response MUST conform to this schema:\n"
        "{\n"
        "  \"narration\": \"plain English summary or rationale for the actions/commands, streamed to user first\",\n"
        "  \"plan\": [\n"
        "    {\n"
        "      \"description\": \"one-line human description of what this command does\",\n"
        "      \"command\": \"the exact shell command to execute\"\n"
        "    }\n"
        "  ],\n"
        "  \"memories\": [\n"
        "    { \"key\": \"remembered_key\", \"value\": \"remembered_value\", \"action\": \"set\" },\n"
        "    { \"key\": \"old_key\", \"action\": \"forget\" }\n"
        "  ],\n"
        "  \"warnings\": [\n"
        "    \"any critical warning messages for the user\"\n"
        "  ],\n"
        "  \"follow_up\": \"optional suggested next action\"\n"
        "}"
    )

    return "\n\n".join(parts)

def clean_json_response(raw_text: str) -> str:
    # Remove markdown code fence if AI wraps the JSON in ```json ... ```
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        # Match ```json or similar and remove it
        cleaned = re.sub(r"^```[a-zA-Z]*\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()

def call_ai_pipeline(
    api_key: str,
    system_prompt: str,
    messages: list,
    show_stream: bool = True,
    model_name: str = "claude-sonnet-4-6"
) -> dict:
    client = anthropic.Anthropic(api_key=api_key)
    
    # Cap messages history to last 20 turns
    # Each turn is usually user/assistant pair. 20 turns = 40 messages.
    capped_messages = messages[-40:]
    
    max_retries = 3
    retry_delay = 5
    
    # We will try up to 3 times for API rate limits / errors
    for attempt in range(max_retries):
        try:
            if show_stream:
                # We stream the response to parse the narration field on the fly
                accumulated = []
                in_narration = False
                escaped = False
                
                # We show a subtle spinner before the stream starts
                narration_done = False
                with client.messages.stream(
                    model=model_name,
                    max_tokens=4000,
                    system=system_prompt,
                    messages=capped_messages
                ) as stream:
                    for text in stream.text_stream:
                        accumulated.append(text)
                        chunk = "".join(accumulated)
                        
                        # Custom narration streaming logic
                        if not in_narration and not narration_done:
                            match = re.search(r'"narration"\s*:\s*"', chunk)
                            if match:
                                in_narration = True
                                # Print everything in the chunk after the starting quote
                                start_idx = match.end()
                                chunk_to_print = chunk[start_idx:]
                                sys.stdout.write(chunk_to_print)
                                sys.stdout.flush()
                        elif in_narration:
                            # We are inside the narration string, print the incoming delta text character-by-character
                            for char in text:
                                if escaped:
                                    sys.stdout.write(char)
                                    sys.stdout.flush()
                                    escaped = False
                                elif char == "\\":
                                    sys.stdout.write(char)
                                    sys.stdout.flush()
                                    escaped = True
                                elif char == '"':
                                    in_narration = False
                                    narration_done = True
                                    # Break to stop printing anything after the closing quote
                                    break
                                else:
                                    sys.stdout.write(char)
                                    sys.stdout.flush()
                
                # Output newline after streaming finishes
                print()
                
                raw_response = "".join(accumulated)
            else:
                # Non-streaming call
                response = client.messages.create(
                    model=model_name,
                    max_tokens=4000,
                    system=system_prompt,
                    messages=capped_messages
                )
                raw_response = response.content[0].text
            
            cleaned = clean_json_response(raw_response)
            parsed = json.loads(cleaned)
            return parsed
            
        except json.JSONDecodeError as je:
            display.status_warning(f"AI returned invalid JSON on attempt {attempt+1}. Retrying once...")
            # Try to fix by appending a correction turn in the message list
            if attempt == 0:
                # Append retry instructions
                messages_with_retry = list(capped_messages)
                messages_with_retry.append({"role": "assistant", "content": raw_response})
                messages_with_retry.append({
                    "role": "user",
                    "content": "Your response was not valid JSON. Please output ONLY valid JSON without any surrounding text or markdown blocks."
                })
                # Call recursive but non-streaming retry
                try:
                    return call_ai_pipeline(api_key, system_prompt, messages_with_retry, show_stream=False, model_name=model_name)
                except Exception as e:
                    display.status_error(f"Retry failed: {e}")
                    raise e
            raise je
            
        except anthropic.RateLimitError as re_err:
            if attempt < max_retries - 1:
                display.status_warning(f"Rate limit hit. Waiting {retry_delay}s before retrying (attempt {attempt+1}/{max_retries})...")
                time.sleep(retry_delay)
                continue
            display.status_error("API rate limit exceeded. Please try again later.")
            raise re_err
            
        except anthropic.APIStatusError as se_err:
            display.status_error(f"Anthropic API Error (Status: {se_err.status_code}): {se_err.message}")
            raise se_err
            
        except Exception as e:
            display.status_error(f"Unexpected error in AI pipeline: {e}")
            raise e
            
    raise RuntimeError("Failed to obtain response from AI after multiple retries.")

def call_final_response(api_key: str, system_prompt: str, messages: list, model_name: str = "claude-sonnet-4-6") -> str:
    client = anthropic.Anthropic(api_key=api_key)
    accumulated = []
    with client.messages.stream(
        model=model_name,
        max_tokens=1000,
        system=system_prompt,
        messages=messages[-40:]
    ) as stream:
        for text in stream.text_stream:
            sys.stdout.write(text)
            sys.stdout.flush()
            accumulated.append(text)
    print()
    return "".join(accumulated)
