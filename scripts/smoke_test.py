#!/usr/bin/env python3
from __future__ import annotations
import json
import os
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    import urllib.request

ROOT = Path(__file__).resolve().parents[1]

def load_env(path: Path):
    out = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k,v = line.split("=",1); out[k]=v
    return out

env = {**load_env(ROOT / ".env"), **os.environ}
base = env.get("GATEWAY_PUBLIC_URL", "http://localhost:4000").rstrip("/")
key = os.environ.get("FIAP_GROUP_KEY")
if not key:
    print("Set FIAP_GROUP_KEY to one virtual group key before running this test.")
    sys.exit(2)

payload = {
    "model": "fiap-fast",
    "messages": [{"role":"user","content":"Responda apenas: FIAP LAB OK"}],
    "max_tokens": 20,
}

if 'requests' in globals():
    resp = requests.post(
        f"{base}/v1/chat/completions",
        json=payload,
        headers={"Authorization": f"Bearer {key}"},
        timeout=60
    )
    data = resp.json()
else:
    req = urllib.request.Request(
        f"{base}/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type":"application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode())

print(json.dumps(data, ensure_ascii=False, indent=2))
