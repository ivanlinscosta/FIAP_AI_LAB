#!/usr/bin/env python3
from pathlib import Path
import secrets
import re

root = Path(__file__).resolve().parents[1]
env_path = root / ".env"
example = root / ".env.example"

if env_path.exists():
    text = env_path.read_text(encoding="utf-8")
else:
    text = example.read_text(encoding="utf-8")

def token(prefix, n=32):
    return prefix + secrets.token_urlsafe(n)

replacements = {
    "LITELLM_MASTER_KEY": token("sk-fiap-admin-", 32),
    "POSTGRES_PASSWORD": secrets.token_urlsafe(32),
    "N8N_ENCRYPTION_KEY": secrets.token_urlsafe(48),
}

for key, value in replacements.items():
    text = re.sub(rf"^{re.escape(key)}=.*$", f"{key}={value}", text, flags=re.MULTILINE)

# Keep DATABASE_URL referencing the password variable; Docker Compose expands it.
env_path.write_text(text, encoding="utf-8")
print(f"Created/updated {env_path}")
print("Next: edit .env and replace OPENAI_API_KEY with the dedicated FIAP lab key.")
