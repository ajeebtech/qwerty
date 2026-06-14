import sys
import yaml
from pathlib import Path
import anthropic

cfg_path = Path.home() / ".vibe-server-dev" / "config.yaml"
if not cfg_path.exists():
    print("No dev config found!")
    sys.exit(1)

with open(cfg_path, "r") as f:
    cfg = yaml.safe_load(f)

key = cfg.get("anthropic_api_key")
if not key:
    print("No Anthropic API Key found in dev config!")
    sys.exit(1)

client = anthropic.Anthropic(api_key=key)

models = [
    "claude-sonnet-4-6",
    "claude-haiku-4-5",
    "claude-opus-4-8",
    "claude-fable-5"
]

print("Testing 2026 model access...")
for m in models:
    try:
        response = client.messages.create(
            model=m,
            max_tokens=10,
            messages=[{"role": "user", "content": "Ping"}]
        )
        print(f"✓ Success: {m}")
        print(f"  Response: {response.content[0].text.strip()}")
    except Exception as e:
        print(f"✗ Failed: {m} -> {e}")
