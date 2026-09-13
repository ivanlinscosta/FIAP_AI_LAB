#!/usr/bin/env python3
from pathlib import Path
import json
import sys
from urllib.parse import urlparse

if len(sys.argv) != 2:
    raise SystemExit("Usage: python scripts/render_power_automate_swagger.py https://gateway.example.com")
url = urlparse(sys.argv[1])
if url.scheme != "https" or not url.netloc:
    raise SystemExit("Power Automate requires a public HTTPS gateway URL.")
root = Path(__file__).resolve().parents[1]
template = json.loads((root / "power-automate" / "fiap-ai-gateway.swagger.template.json").read_text(encoding="utf-8"))
template["host"] = url.netloc
template["basePath"] = (url.path.rstrip("/") + "/v1") if url.path else "/v1"
out = root / "power-automate" / "fiap-ai-gateway.swagger.json"
out.write_text(json.dumps(template, ensure_ascii=False, indent=2), encoding="utf-8")
print(out)
