import os
import re
import sys
import json
import time
import openai
from cli import display

DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"

# ANSI codes
ANSI_RESET  = "\033[0m"
ANSI_BOLD   = "\033[1m"
ANSI_CYAN   = "\033[36m"
ANSI_YELLOW = "\033[33m"
ANSI_DIM    = "\033[2m"

def render_markdown_ansi(text: str) -> str:
    """Convert a subset of markdown to ANSI terminal styling."""
    lines = text.split("\n")
    rendered = []
    for line in lines:
        # Headings: ## Title  →  bold + yellow
        if line.startswith("### "):
            line = f"{ANSI_BOLD}{ANSI_YELLOW}{line[4:]}{ANSI_RESET}"
        elif line.startswith("## "):
            line = f"{ANSI_BOLD}{ANSI_YELLOW}{line[3:]}{ANSI_RESET}"
        elif line.startswith("# "):
            line = f"{ANSI_BOLD}{ANSI_YELLOW}{line[2:]}{ANSI_RESET}"
        # Inline: **bold** → bold white, `code` → cyan
        # Process inline patterns left-to-right
        result = ""
        i = 0
        while i < len(line):
            if line[i:i+2] == "**":
                end = line.find("**", i + 2)
                if end != -1:
                    result += f"{ANSI_BOLD}{line[i+2:end]}{ANSI_RESET}"
                    i = end + 2
                    continue
            elif line[i] == "`":
                end = line.find("`", i + 1)
                if end != -1:
                    result += f"{ANSI_CYAN}{line[i+1:end]}{ANSI_RESET}"
                    i = end + 1
                    continue
            result += line[i]
            i += 1
        rendered.append(result)
    return "\n".join(rendered)

def assemble_system_prompt(
    mode_overlay: str,
    hoster_overlay: str,
    settings: dict,
    brain_context: str | None = None
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
        
    # 4. Server context / Brain Context
    if brain_context:
        parts.append(brain_context)
        
    # 6. User preferences
    pref_parts = []
    pref_parts.append(f"AI Verbosity level: {settings.get('ai_verbosity', 'normal')}")
    pref_parts.append(f"Preferred editor: {settings.get('preferred_editor', 'nano')}")
    pref_parts.append(f"Preferred process manager: {settings.get('preferred_process_manager', 'pm2')}")
    pref_parts.append(f"Preferred web server: {settings.get('preferred_web_server', 'nginx')}")
    parts.append(f"--- USER PREFERENCES ---\n" + "\n".join(pref_parts))

    # 7. Readonly mode enforcement
    if settings.get("readonly", False):
        parts.append(
            "--- READONLY MODE ACTIVE ---\n"
            "CRITICAL RESTRICTION: The user has enabled readonly mode. You MUST NOT generate any commands that "
            "create, write, modify, or delete files on the server. This includes but is not limited to: "
            "redirects (>, >>), heredocs (cat > ... << EOF, tee), sed -i, awk with output, chmod, chown, "
            "rm, mv, cp (when creating new files), touch, truncate, or any command that writes to disk. "
            "You may ONLY run read-only or purely execution commands (e.g. systemctl start/stop/restart, "
            "apt install, curl, wget, bash scripts that already exist on the server). "
            "If a task requires file editing, explain to the user what changes are needed and ask them to make "
            "the edits manually, or disable readonly mode with: /set readonly false"
        )

    # 7. JSON Format Instructions
    parts.append(
        "--- RESPONSE JSON SCHEMA ---\n"
        "You MUST respond ONLY with a single valid JSON object. Do not include markdown codeblocks or wrap in ```json ... ```. "
        "To support real-time streaming, the key \"narration\" MUST be the VERY FIRST key in your JSON object. "
        "The response MUST conform to this schema:\n"
        "{\n"
        "  \"narration\": \"plain English summary or rationale for the actions/commands, streamed to user first. CRITICAL: DO NOT put your JSON plan array in this string! Only put conversational text here.\",\n"
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
    model_name: str = "deepseek-chat"
) -> dict:
    client = openai.OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)
    
    # Cap messages history to last 20 turns
    # Each turn is usually user/assistant pair. 20 turns = 40 messages.
    capped_messages = messages[-40:]
    
    max_retries = 3
    retry_delay = 5
    
    # We will try up to 3 times for API rate limits / errors
    for attempt in range(max_retries):
        try:
            if show_stream:
                accumulated = []
                in_narration = False
                escaped = False
                narration_done = False

                stream = client.chat.completions.create(
                    model=model_name,
                    max_tokens=4000,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        *capped_messages
                    ],
                    stream=True
                )
                for chunk in stream:
                    delta = chunk.choices[0].delta.content
                    if delta is None:
                        continue
                    text = delta
                    accumulated.append(text)
                    chunk_so_far = "".join(accumulated)

                    if not in_narration and not narration_done:
                        match = re.search(r'"narration"\s*:\s*"', chunk_so_far)
                        if match:
                            in_narration = True
                            start_idx = match.end()
                            chunk_to_print = chunk_so_far[start_idx:]
                            sys.stdout.write(chunk_to_print)
                            sys.stdout.flush()
                    elif in_narration:
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
                                break
                            else:
                                sys.stdout.write(char)
                                sys.stdout.flush()

                print()
                raw_response = "".join(accumulated)
            else:
                # Non-streaming call
                response = client.chat.completions.create(
                    model=model_name,
                    max_tokens=4000,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        *capped_messages
                    ]
                )
                raw_response = response.choices[0].message.content
            
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
            
        except openai.RateLimitError as re_err:
            if attempt < max_retries - 1:
                display.status_warning(f"Rate limit hit. Waiting {retry_delay}s before retrying (attempt {attempt+1}/{max_retries})...")
                time.sleep(retry_delay)
                continue
            display.status_error("API rate limit exceeded. Please try again later.")
            raise re_err
            
        except openai.APIStatusError as se_err:
            display.status_error(f"DeepSeek API Error (Status: {se_err.status_code}): {se_err.message}")
            raise se_err
            
        except Exception as e:
            display.status_error(f"Unexpected error in AI pipeline: {e}")
            raise e
            
    raise RuntimeError("Failed to obtain response from AI after multiple retries.")

def call_final_response(api_key: str, system_prompt: str, messages: list, model_name: str = "deepseek-chat") -> str:
    client = openai.OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)
    accumulated = []
    stream = client.chat.completions.create(
        model=model_name,
        max_tokens=1000,
        messages=[
            {"role": "system", "content": system_prompt},
            *messages[-40:]
        ],
        stream=True
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta is None:
            continue
        accumulated.append(delta)
    raw = "".join(accumulated)
    formatted = render_markdown_ansi(raw)
    from cli import display
    display.status_ai_response(formatted)
    return raw
