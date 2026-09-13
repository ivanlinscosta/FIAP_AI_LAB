#!/usr/bin/env python3
"""Create LiteLLM virtual keys for student groups and save them locally.

Requires a running LiteLLM gateway and a professor-only master key.
No third-party Python packages are required.

Usage:
    python scripts/provision_groups.py              # Create/update all groups
    python scripts/provision_groups.py --list       # List existing keys
    python scripts/provision_groups.py --dry-run    # Preview without creating
    python scripts/provision_groups.py --count 15   # Override group count
"""
from __future__ import annotations
import argparse
import csv
import json
import os
import sys
try:
    import requests
except ImportError:
    import urllib.request
    import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / ".env"
SECRETS_DIR = ROOT / "secrets"
SECRETS_DIR.mkdir(exist_ok=True)

class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    END = "\033[0m"

def log_ok(msg: str) -> None:
    print(f"{Colors.GREEN}✓{Colors.END} {msg}")

def log_warn(msg: str) -> None:
    print(f"{Colors.YELLOW}⚠{Colors.END} {msg}")

def log_error(msg: str) -> None:
    print(f"{Colors.RED}✗{Colors.END} {msg}", file=sys.stderr)

def log_info(msg: str) -> None:
    print(f"{Colors.CYAN}→{Colors.END} {msg}")


def load_env(path: Path) -> dict[str, str]:
    data = {}
    if not path.exists():
        return data
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        data[k.strip()] = v.strip()
    return data


def request_json(method: str, url: str, payload: dict | None, master_key: str) -> dict:
    headers = {
        "Authorization": f"Bearer {master_key}",
        "Content-Type": "application/json",
    }
    
    if 'requests' in globals():
        resp = requests.request(
            method,
            url,
            json=payload,
            headers=headers,
            timeout=30
        )
        if resp.status_code >= 400:
            raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:500]}")
        return resp.json()
    else:
        data = json.dumps(payload).encode("utf-8") if payload else None
        req = urllib.request.Request(
            url,
            data=data,
            headers=headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {e.code}: {body}") from e


def get_existing_keys(base_url: str, master_key: str) -> list[dict]:
    """Fetch all existing virtual keys from the gateway."""
    try:
        result = request_json("GET", f"{base_url}/key/list?page=1&size=100", None, master_key)
        if isinstance(result, list):
            return result
        if isinstance(result, dict):
            return result.get("keys") or result.get("data") or []
        return []
    except RuntimeError as e:
        log_warn(f"Could not list existing keys: {e}")
        return []


def mask_key(value: str | None) -> str:
    if not value:
        return "<missing>"
    text = str(value)
    if len(text) <= 8:
        return "sk-..." + text[-4:]
    return f"sk-...{text[-4:]}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Provision LiteLLM virtual keys for FIAP AI Lab student groups"
    )
    parser.add_argument(
        "--list", action="store_true",
        help="List existing virtual keys and exit"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview what would be created without actually creating keys"
    )
    parser.add_argument(
        "--count", type=int, default=None,
        help="Override GROUP_COUNT (default: from env or 10)"
    )
    parser.add_argument(
        "--budget", type=float, default=None,
        help="Override GROUP_BUDGET_USD (default: from env or 5)"
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Regenerate keys even if they already exist"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    env = {**load_env(ENV), **os.environ}
    base_url = env.get("GATEWAY_PUBLIC_URL", "http://localhost:4000").rstrip("/")
    master_key = env.get("LITELLM_MASTER_KEY", "")

    if not master_key or master_key == "CHANGE_ME":
        log_error("LITELLM_MASTER_KEY is missing. Run scripts/generate_secrets.py first.")
        sys.exit(1)

    count = args.count or int(env.get("GROUP_COUNT", "10"))
    budget = args.budget if args.budget is not None else float(env.get("GROUP_BUDGET_USD", "5"))
    budget_duration = env.get("GROUP_BUDGET_DURATION", "30d")
    rpm = int(env.get("GROUP_RPM_LIMIT", "30"))
    tpm = int(env.get("GROUP_TPM_LIMIT", "100000"))
    key_duration = env.get("GROUP_KEY_DURATION", "45d")
    models = ["fiap-fast", "fiap-standard", "fiap-embedding"]

    log_info(f"Gateway: {base_url}")
    log_info(f"Groups: {count} | Budget: US$ {budget} | RPM: {rpm} | TPM: {tpm}")

    if args.list:
        log_info("Fetching existing keys...")
        keys = get_existing_keys(base_url, master_key)
        if not keys:
            log_warn("No keys found or unable to fetch keys.")
            return

        print(f"\n{Colors.BOLD}{'Alias':<25} {'Key':<20} {'Budget':<10} {'Spend':<10} {'Status':<10}{Colors.END}")
        print("-" * 75)
        for key_info in keys:
            alias = key_info.get("key_alias") or key_info.get("key_name") or "-"
            key_val = key_info.get("key") or key_info.get("token") or ""
            budget_val = key_info.get("max_budget", "-")
            spend_val = key_info.get("spend", 0)
            blocked = key_info.get("blocked", False)
            status = "BLOCKED" if blocked else "Active"
            print(f"{alias:<25} {mask_key(key_val):<20} {budget_val:<10} {spend_val:<10} {status:<10}")
        print(f"\nTotal: {len(keys)} keys")
        return

    rows = []
    created = 0
    skipped = 0

    for i in range(1, count + 1):
        group = f"grupo-{i:02d}"
        alias = f"fiap-{group}"

        payload = {
            "key_alias": alias,
            "models": models,
            "max_budget": budget,
            "budget_duration": budget_duration,
            "rpm_limit": rpm,
            "tpm_limit": tpm,
            "duration": key_duration,
            "metadata": {
                "course": "FIAP Tools Automations and Workflows",
                "group": group,
            },
        }

        if args.dry_run:
            log_info(f"[DRY RUN] Would create: {group} (alias: {alias})")
            rows.append({
                "group": group,
                "gateway_url": base_url,
                "openai_base_url": f"{base_url}/v1",
                "api_key": "DRY_RUN_KEY",
                "chat_model": "fiap-fast",
                "standard_model": "fiap-standard",
                "embedding_model": "fiap-embedding",
                "budget_usd": budget,
                "rpm_limit": rpm,
                "tpm_limit": tpm,
            })
            continue

        try:
            result = request_json("POST", f"{base_url}/key/generate", payload, master_key)
            virtual_key = result.get("key") or result.get("token")
            if not virtual_key:
                log_error(f"Unexpected response for {group}: {result}")
                continue

            rows.append({
                "group": group,
                "gateway_url": base_url,
                "openai_base_url": f"{base_url}/v1",
                "api_key": virtual_key,
                "chat_model": "fiap-fast",
                "standard_model": "fiap-standard",
                "embedding_model": "fiap-embedding",
                "budget_usd": budget,
                "rpm_limit": rpm,
                "tpm_limit": tpm,
            })

            (SECRETS_DIR / f"{group}.txt").write_text(
                f"FIAP AI Lab - {group}\n"
                f"Gateway: {base_url}\n"
                f"OpenAI-compatible Base URL: {base_url}/v1\n"
                f"API Key: {virtual_key}\n"
                f"Modelo padrão: fiap-fast\n"
                f"Modelo avançado: fiap-standard\n"
                f"Embedding: fiap-embedding\n",
                encoding="utf-8",
            )
            log_ok(f"Created {group} → {mask_key(virtual_key)}")
            created += 1

        except RuntimeError as e:
            log_error(f"Failed to create {group}: {e}")
            skipped += 1

    if rows:
        csv_path = SECRETS_DIR / "group_keys.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        log_ok(f"CSV saved: {csv_path}")

    print(f"\n{Colors.BOLD}{'='*50}{Colors.END}")
    if args.dry_run:
        log_info(f"Dry run complete. {len(rows)} groups would be created.")
    else:
        log_ok(f"Provisioning complete: {created} created, {skipped} failed")
        log_warn("Do NOT commit or send the CSV to students.")
        log_warn("Send only each group's own .txt file from secrets/")
    print(f"{Colors.BOLD}{'='*50}{Colors.END}")


if __name__ == "__main__":
    main()
