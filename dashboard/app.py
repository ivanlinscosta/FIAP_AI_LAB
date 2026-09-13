from __future__ import annotations

import asyncio
import csv
import io
import json
import logging
import os
import re
from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from services.auth import AuthService
from services.litellm import LiteLLMService, mask_key

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
GROUP_PATTERN = re.compile(r"(grupo-\d+)", re.IGNORECASE)
MODEL_OPTIONS = ["fiap-fast", "fiap-standard", "fiap-embedding"]

auth_service = AuthService()
litellm_service = LiteLLMService()

app = FastAPI(title="FIAP AI Lab Dashboard", docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class LoginPayload(BaseModel):
    username: str = ""
    password: str = ""


class SetupPayload(BaseModel):
    username: str = ""
    password: str = ""
    confirm_password: str = ""


class BudgetPayload(BaseModel):
    max_budget: float = Field(..., ge=0)


def now_utc() -> datetime:
    return datetime.now(UTC)


def ensure_api_auth(request: Request) -> None:
    if not auth_service.is_authenticated(request):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")


def ensure_page_auth(request: Request):
    if not auth_service.is_authenticated(request):
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    return None


def parse_datetime(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value), tz=UTC)
        except (OverflowError, OSError, ValueError):
            return None
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    cleaned = cleaned.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(cleaned)
    except ValueError:
        for pattern in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                parsed = datetime.strptime(cleaned, pattern)
                parsed = parsed.replace(tzinfo=UTC)
                break
            except ValueError:
                parsed = None
        if parsed is None:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def safe_float(value: Any, default: float = 0.0) -> float:
    if value in (None, ""):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    if value in (None, ""):
        return default
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def parse_metadata(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        if isinstance(parsed, dict):
            return parsed
    return {}


def extract_metadata(record: dict[str, Any]) -> dict[str, Any]:
    for key in ("metadata", "litellm_metadata", "user_metadata"):
        metadata = parse_metadata(record.get(key))
        if metadata:
            return metadata
    return {}


def extract_group_name(*values: Any) -> str | None:
    for value in values:
        if value is None:
            continue
        if isinstance(value, dict):
            result = extract_group_name(*value.values())
            if result:
                return result
        elif isinstance(value, list):
            result = extract_group_name(*value)
            if result:
                return result
        else:
            match = GROUP_PATTERN.search(str(value))
            if match:
                return match.group(1).lower()
    return None


def isoformat(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def status_from_usage(blocked: bool, usage_pct: float) -> dict[str, str]:
    if blocked:
        return {"label": "Bloqueado", "tone": "danger"}
    if usage_pct >= 100:
        return {"label": "Limite excedido", "tone": "danger"}
    if usage_pct >= 85:
        return {"label": "Crítico", "tone": "warning-high"}
    if usage_pct >= 70:
        return {"label": "Atenção", "tone": "warning"}
    return {"label": "Ativo", "tone": "success"}


def bucket_timestamp(timestamp: datetime, mode: str) -> str:
    if mode == "hour":
        return timestamp.replace(minute=0, second=0, microsecond=0).isoformat().replace("+00:00", "Z")
    return timestamp.replace(hour=0, minute=0, second=0, microsecond=0).isoformat().replace("+00:00", "Z")


def choose_bucket_mode(call_timestamps: list[datetime]) -> str:
    if not call_timestamps:
        return "day"
    span = max(call_timestamps) - min(call_timestamps)
    return "hour" if span <= timedelta(days=2) else "day"


def normalize_key_record(record: dict[str, Any]) -> dict[str, Any]:
    info = record.get("info") if isinstance(record.get("info"), dict) else record
    metadata = extract_metadata(info)
    group_name = extract_group_name(
        metadata.get("group"),
        metadata.get("group_name"),
        info.get("key_alias"),
        info.get("key_name"),
        info.get("user_id"),
    )
    key_value = record.get("key") or info.get("key") or info.get("token") or record.get("token")
    models = info.get("models") or record.get("models") or []
    if not isinstance(models, list):
        models = []
    spend = safe_float(info.get("spend", record.get("spend", 0)))
    max_budget = info.get("max_budget", record.get("max_budget"))
    max_budget_value = safe_float(max_budget, 0.0) if max_budget is not None else None
    blocked = bool(info.get("blocked", record.get("blocked", False)))
    return {
        "group": group_name,
        "key_alias": info.get("key_alias") or record.get("key_alias"),
        "key_name": info.get("key_name") or record.get("key_name"),
        "key_value": key_value,
        "masked_key": mask_key(key_value) if key_value else None,
        "metadata": metadata,
        "models": models,
        "spend": spend,
        "max_budget": max_budget_value,
        "budget_duration": info.get("budget_duration") or record.get("budget_duration"),
        "rpm_limit": info.get("rpm_limit") or record.get("rpm_limit"),
        "tpm_limit": info.get("tpm_limit") or record.get("tpm_limit"),
        "blocked": blocked,
        "expires": info.get("expires") or record.get("expires"),
        "raw": record,
    }


def normalize_call_record(record: dict[str, Any], alias_lookup: dict[str, str]) -> dict[str, Any] | None:
    metadata = extract_metadata(record)
    timestamp = parse_datetime(
        record.get("startTime")
        or record.get("start_time")
        or record.get("timestamp")
        or record.get("created_at")
        or record.get("request_time")
        or record.get("date")
    )
    end_time = parse_datetime(record.get("endTime") or record.get("end_time") or record.get("completed_at"))
    model = str(
        metadata.get("original_model_group")
        or record.get("model")
        or record.get("model_name")
        or record.get("custom_llm_provider")
        or "unknown"
    )
    input_tokens = safe_int(record.get("prompt_tokens") or record.get("input_tokens"))
    output_tokens = safe_int(record.get("completion_tokens") or record.get("output_tokens"))
    total_tokens = safe_int(record.get("total_tokens")) or input_tokens + output_tokens
    cost = safe_float(record.get("spend") or record.get("cost") or record.get("response_cost"))
    latency_ms = safe_float(record.get("latency") or record.get("latency_ms"))
    if not latency_ms and timestamp and end_time:
        latency_ms = max((end_time - timestamp).total_seconds() * 1000, 0)
    status_code = safe_int(record.get("status_code") or record.get("http_status") or record.get("response_status_code"))
    group_name = extract_group_name(
        metadata.get("group"),
        metadata.get("group_name"),
        metadata.get("user_api_key_alias"),
        metadata.get("api_key_alias"),
        record.get("group"),
        record.get("key_alias"),
        record.get("api_key_alias"),
        record.get("user_api_key_alias"),
        record.get("key_name"),
    )
    if not group_name:
        for candidate in (
            record.get("key_alias"),
            record.get("api_key_alias"),
            record.get("user_api_key_alias"),
            record.get("key_name"),
        ):
            if candidate and str(candidate).lower() in alias_lookup:
                group_name = alias_lookup[str(candidate).lower()]
                break
    if not group_name:
        return None
    return {
        "group": group_name,
        "timestamp": isoformat(timestamp),
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "cost": round(cost, 6),
        "latency_ms": round(latency_ms, 2),
        "http_status": status_code,
        "request_id": record.get("request_id") or record.get("id") or "-",
    }


def build_group_base(key_record: dict[str, Any]) -> dict[str, Any]:
    group_name = key_record["group"]
    max_budget = key_record["max_budget"]
    spend = key_record["spend"]
    budget_remaining = None if max_budget is None else max(max_budget - spend, 0.0)
    budget_used_pct = 0.0 if not max_budget else (spend / max_budget) * 100
    status_info = status_from_usage(key_record["blocked"], budget_used_pct)
    return {
        "group": group_name,
        "key_alias": key_record["key_alias"],
        "masked_key": key_record["masked_key"],
        "models": key_record["models"],
        "metadata": key_record["metadata"],
        "requests": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "cost": 0.0,
        "budget": max_budget,
        "budget_remaining": budget_remaining,
        "budget_used_pct": round(budget_used_pct, 2),
        "current_spend": round(spend, 6),
        "last_called_at": None,
        "status": status_info,
        "blocked": key_record["blocked"],
        "budget_duration": key_record["budget_duration"],
        "rpm_limit": key_record["rpm_limit"],
        "tpm_limit": key_record["tpm_limit"],
        "expires": key_record["expires"],
        "model_distribution": [],
        "recent_calls": [],
    }


async def fetch_dashboard_snapshot() -> dict[str, Any]:
    lookback_days = int(os.getenv("DASHBOARD_LOOKBACK_DAYS", "90"))

    try:
        keys_raw, spend_raw = await asyncio.gather(
            litellm_service.get_keys(),
            litellm_service.get_spend(
                last_n_hours=lookback_days * 24,
                summarize="false",
            ),
        )
    except RuntimeError as exc:
        logger.error("Failed to build dashboard snapshot: %s", exc)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    key_records = [normalize_key_record(item) for item in keys_raw]
    key_records = [item for item in key_records if item.get("group")]
    alias_lookup: dict[str, str] = {}
    key_lookup: dict[str, dict[str, Any]] = {}
    groups: dict[str, dict[str, Any]] = {}

    for record in key_records:
        if record["key_alias"]:
            alias_lookup[str(record["key_alias"]).lower()] = record["group"]
        if record["key_name"]:
            alias_lookup[str(record["key_name"]).lower()] = record["group"]
        groups[record["group"]] = build_group_base(record)
        key_lookup[record["group"]] = record

    calls: list[dict[str, Any]] = []
    calls_by_group: dict[str, list[dict[str, Any]]] = defaultdict(list)
    model_counters: dict[str, Counter[str]] = defaultdict(Counter)
    request_times: dict[str, list[datetime]] = defaultdict(list)

    for row in spend_raw:
        call = normalize_call_record(row, alias_lookup)
        if not call:
            continue
        calls.append(call)
        group_name = call["group"]
        if group_name not in groups:
            groups[group_name] = {
                "group": group_name,
                "key_alias": None,
                "masked_key": None,
                "models": MODEL_OPTIONS,
                "metadata": {},
                "requests": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "cost": 0.0,
                "budget": None,
                "budget_remaining": None,
                "budget_used_pct": 0.0,
                "current_spend": 0.0,
                "last_called_at": None,
                "status": {"label": "Ativo", "tone": "success"},
                "blocked": False,
                "budget_duration": None,
                "rpm_limit": None,
                "tpm_limit": None,
                "expires": None,
                "model_distribution": [],
                "recent_calls": [],
            }

        group_entry = groups[group_name]
        group_entry["requests"] += 1
        group_entry["input_tokens"] += call["input_tokens"]
        group_entry["output_tokens"] += call["output_tokens"]
        group_entry["total_tokens"] += call["total_tokens"]
        group_entry["cost"] = round(group_entry["cost"] + call["cost"], 6)
        if not group_entry["last_called_at"] or (call["timestamp"] and call["timestamp"] > group_entry["last_called_at"]):
            group_entry["last_called_at"] = call["timestamp"]

        calls_by_group[group_name].append(call)
        model_counters[group_name][call["model"]] += 1
        parsed_call_time = parse_datetime(call["timestamp"])
        if parsed_call_time:
            request_times[group_name].append(parsed_call_time)

    sorted_calls = sorted(
        calls,
        key=lambda item: parse_datetime(item["timestamp"]) or datetime.min.replace(tzinfo=UTC),
        reverse=True,
    )

    alerts: list[dict[str, Any]] = []
    for group_name, group_entry in groups.items():
        recent_calls = sorted(
            calls_by_group.get(group_name, []),
            key=lambda item: parse_datetime(item["timestamp"]) or datetime.min.replace(tzinfo=UTC),
            reverse=True,
        )[:25]
        group_entry["recent_calls"] = recent_calls
        group_entry["last_called_at"] = group_entry["last_called_at"]
        group_entry["model_distribution"] = [
            {"model": model, "requests": count}
            for model, count in model_counters[group_name].most_common()
        ]

        usage_pct = group_entry["budget_used_pct"]
        if group_entry["budget"] is not None:
            if usage_pct >= 100:
                alerts.append(
                    {
                        "group": group_name,
                        "severity": "critical",
                        "type": "budget",
                        "message": f"{group_name} atingiu ou ultrapassou 100% do budget.",
                    }
                )
            elif usage_pct >= 85:
                alerts.append(
                    {
                        "group": group_name,
                        "severity": "high",
                        "type": "budget",
                        "message": f"{group_name} ultrapassou 85% do budget.",
                    }
                )
            elif usage_pct >= 70:
                alerts.append(
                    {
                        "group": group_name,
                        "severity": "medium",
                        "type": "budget",
                        "message": f"{group_name} ultrapassou 70% do budget.",
                    }
                )

        timestamps = sorted(request_times.get(group_name, []))
        left = 0
        for right, current_time in enumerate(timestamps):
            while current_time - timestamps[left] > timedelta(minutes=5):
                left += 1
            if right - left + 1 > 100:
                alerts.append(
                    {
                        "group": group_name,
                        "severity": "high",
                        "type": "anomaly",
                        "message": f"{group_name}: POSSÍVEL LOOP DE AUTOMAÇÃO (>100 chamadas em 5 min).",
                    }
                )
                break

    overview = {
        "total_requests": len(sorted_calls),
        "total_tokens": sum(call["total_tokens"] for call in sorted_calls),
        "total_cost": round(sum(call["cost"] for call in sorted_calls), 6),
        "active_groups": sum(1 for group in groups.values() if not group["blocked"]),
        "total_groups": len(groups),
    }

    return {
        "generated_at": isoformat(now_utc()),
        "lookback_days": lookback_days,
        "overview": overview,
        "groups": sorted(groups.values(), key=lambda item: item["group"]),
        "calls": sorted_calls,
        "alerts": alerts,
        "available_models": MODEL_OPTIONS,
        "key_lookup": key_lookup,
    }


def build_chart_payload(calls: list[dict[str, Any]], mode: str) -> dict[str, Any]:
    if mode == "cost-per-group":
        values: dict[str, float] = defaultdict(float)
        for call in calls:
            values[call["group"]] += call["cost"]
        labels = sorted(values)
        return {"labels": labels, "datasets": [{"label": "Custo (US$)", "data": [round(values[label], 6) for label in labels]}]}

    if mode == "tokens-per-group":
        values: dict[str, int] = defaultdict(int)
        for call in calls:
            values[call["group"]] += call["total_tokens"]
        labels = sorted(values)
        return {"labels": labels, "datasets": [{"label": "Tokens", "data": [values[label] for label in labels]}]}

    if mode == "model-distribution":
        values: dict[str, int] = defaultdict(int)
        for call in calls:
            values[call["model"]] += 1
        labels = list(values.keys())
        return {"labels": labels, "datasets": [{"label": "Chamadas", "data": [values[label] for label in labels]}]}

    call_timestamps = [parse_datetime(call["timestamp"]) for call in calls if parse_datetime(call["timestamp"])]
    bucket_mode = choose_bucket_mode([item for item in call_timestamps if item])
    buckets: dict[str, dict[str, float]] = defaultdict(lambda: {"cost": 0.0, "tokens": 0, "requests": 0})
    for call in calls:
        timestamp = parse_datetime(call["timestamp"])
        if not timestamp:
            continue
        key = bucket_timestamp(timestamp, bucket_mode)
        buckets[key]["cost"] += call["cost"]
        buckets[key]["tokens"] += call["total_tokens"]
        buckets[key]["requests"] += 1
    labels = sorted(buckets)
    return {
        "labels": labels,
        "bucket_mode": bucket_mode,
        "datasets": [
            {"label": "Custo (US$)", "data": [round(buckets[label]["cost"], 6) for label in labels]},
            {"label": "Tokens", "data": [buckets[label]["tokens"] for label in labels]},
            {"label": "Requisições", "data": [buckets[label]["requests"] for label in labels]},
        ],
    }


async def resolve_group(group_name: str) -> tuple[dict[str, Any], dict[str, Any]]:
    snapshot = await fetch_dashboard_snapshot()
    group = next((item for item in snapshot["groups"] if item["group"] == group_name.lower()), None)
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grupo não encontrado")
    key_record = snapshot["key_lookup"].get(group_name.lower())
    return group, key_record or {}


@app.get("/")
async def index(request: Request):
    redirect = ensure_page_auth(request)
    if redirect:
        return redirect
    return FileResponse(TEMPLATES_DIR / "index.html")


@app.get("/login")
async def login_page(request: Request):
    if auth_service.is_authenticated(request):
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    if not auth_service.profile_exists():
        return RedirectResponse(url="/setup", status_code=status.HTTP_303_SEE_OTHER)
    return FileResponse(TEMPLATES_DIR / "login.html")


@app.get("/setup")
async def setup_page():
    if auth_service.profile_exists():
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    return FileResponse(TEMPLATES_DIR / "setup.html")


@app.post("/api/login")
async def login(payload: LoginPayload):
    if not auth_service.is_configured():
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Admin credentials are not configured")
    if not auth_service.verify_credentials(payload.username, payload.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário ou senha inválidos")

    response = JSONResponse({"success": True})
    auth_service.set_session_cookie(response, auth_service.create_session())
    return response


@app.post("/api/setup")
async def setup(payload: SetupPayload):
    if auth_service.profile_exists():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Perfil do professor já configurado")

    username = payload.username.strip()
    if not username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Informe um nome de usuário")
    if len(payload.password) < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A senha deve ter pelo menos 8 caracteres")
    if payload.password != payload.confirm_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="As senhas não coincidem")

    auth_service.create_profile(username, payload.password)
    response = JSONResponse({"success": True})
    auth_service.set_session_cookie(response, auth_service.create_session())
    return response


@app.post("/api/logout")
async def logout(request: Request):
    response = JSONResponse({"success": True})
    auth_service.invalidate_session(auth_service.get_session_token(request))
    auth_service.clear_session_cookie(response)
    return response


@app.get("/api/overview")
async def get_overview(request: Request):
    ensure_api_auth(request)
    snapshot = await fetch_dashboard_snapshot()
    return snapshot["overview"]


@app.get("/api/groups")
async def get_groups(request: Request):
    ensure_api_auth(request)
    snapshot = await fetch_dashboard_snapshot()
    return {
        "generated_at": snapshot["generated_at"],
        "overview": snapshot["overview"],
        "groups": snapshot["groups"],
        "calls": snapshot["calls"],
        "alerts": snapshot["alerts"],
        "available_models": snapshot["available_models"],
    }


@app.get("/api/groups/{group_name}")
async def get_group_detail(group_name: str, request: Request):
    ensure_api_auth(request)
    group, key_record = await resolve_group(group_name)
    detail = dict(group)
    key_value = key_record.get("key_value")
    if key_value:
        try:
            key_info = await litellm_service.get_key_info(key_value)
        except RuntimeError:
            key_info = {}
        info = key_info.get("info", key_info)
        detail["key_info"] = {
            "key_alias": info.get("key_alias"),
            "spend": info.get("spend"),
            "max_budget": info.get("max_budget"),
            "budget_duration": info.get("budget_duration"),
            "rpm_limit": info.get("rpm_limit"),
            "tpm_limit": info.get("tpm_limit"),
            "blocked": info.get("blocked"),
            "expires": info.get("expires"),
        }
    detail["recent_calls"] = group.get("recent_calls", [])
    return detail


@app.get("/api/groups/{group_name}/calls")
async def get_group_calls(group_name: str, request: Request):
    ensure_api_auth(request)
    group, _ = await resolve_group(group_name)
    return {"group": group_name.lower(), "calls": group.get("recent_calls", [])}


@app.get("/api/charts/cost-per-group")
async def chart_cost_per_group(request: Request):
    ensure_api_auth(request)
    snapshot = await fetch_dashboard_snapshot()
    return build_chart_payload(snapshot["calls"], "cost-per-group")


@app.get("/api/charts/tokens-per-group")
async def chart_tokens_per_group(request: Request):
    ensure_api_auth(request)
    snapshot = await fetch_dashboard_snapshot()
    return build_chart_payload(snapshot["calls"], "tokens-per-group")


@app.get("/api/charts/consumption-over-time")
async def chart_consumption_over_time(request: Request):
    ensure_api_auth(request)
    snapshot = await fetch_dashboard_snapshot()
    return build_chart_payload(snapshot["calls"], "consumption-over-time")


@app.get("/api/charts/model-distribution")
async def chart_model_distribution(request: Request):
    ensure_api_auth(request)
    snapshot = await fetch_dashboard_snapshot()
    return build_chart_payload(snapshot["calls"], "model-distribution")


@app.get("/api/export/csv")
async def export_csv(request: Request):
    ensure_api_auth(request)
    snapshot = await fetch_dashboard_snapshot()
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "Grupo",
            "Requests",
            "Input Tokens",
            "Output Tokens",
            "Total Tokens",
            "Custo",
            "Budget",
            "Budget Restante",
            "% Utilizado",
            "Última Chamada",
            "Status",
        ]
    )
    for group in snapshot["groups"]:
        writer.writerow(
            [
                group["group"],
                group["requests"],
                group["input_tokens"],
                group["output_tokens"],
                group["total_tokens"],
                group["cost"],
                group["budget"],
                group["budget_remaining"],
                group["budget_used_pct"],
                group["last_called_at"],
                group["status"]["label"],
            ]
        )
    payload = io.BytesIO(buffer.getvalue().encode("utf-8"))
    headers = {"Content-Disposition": 'attachment; filename="fiap-ai-lab-dashboard.csv"'}
    return StreamingResponse(payload, media_type="text/csv", headers=headers)


@app.post("/api/groups/{group_name}/block")
async def block_group(group_name: str, request: Request):
    ensure_api_auth(request)
    _, key_record = await resolve_group(group_name)
    key_value = key_record.get("key_value")
    if not key_value:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Chave do grupo não disponível para bloqueio")
    await litellm_service.block_key(key_value)
    return {"success": True, "group": group_name.lower(), "action": "blocked"}


@app.post("/api/groups/{group_name}/unblock")
async def unblock_group(group_name: str, request: Request):
    ensure_api_auth(request)
    _, key_record = await resolve_group(group_name)
    key_value = key_record.get("key_value")
    if not key_value:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Chave do grupo não disponível para desbloqueio")
    await litellm_service.unblock_key(key_value)
    return {"success": True, "group": group_name.lower(), "action": "unblocked"}


@app.post("/api/groups/{group_name}/budget")
async def update_budget(group_name: str, payload: BudgetPayload, request: Request):
    ensure_api_auth(request)
    _, key_record = await resolve_group(group_name)
    key_value = key_record.get("key_value")
    if not key_value:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Chave do grupo não disponível para atualização")
    await litellm_service.update_key(key_value, {"max_budget": payload.max_budget})
    return {"success": True, "group": group_name.lower(), "max_budget": payload.max_budget}


@app.post("/api/groups/{group_name}/regenerate-key")
async def regenerate_group_key(group_name: str, request: Request):
    ensure_api_auth(request)
    _, key_record = await resolve_group(group_name)
    key_value = key_record.get("key_value")
    if not key_value:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Chave do grupo não disponível para regeneração")
    result = await litellm_service.regenerate_key(key_value)
    new_key = result.get("key") or result.get("token")
    return {
        "success": True,
        "group": group_name.lower(),
        "masked_key": mask_key(new_key) if new_key else None,
        "message": "Chave regenerada com sucesso.",
    }


@app.get("/api/health")
async def health_check():
    configured = {
        "litellm": litellm_service.is_configured(),
        **auth_service.config_status(),
    }
    required_checks = {"litellm", "admin_credentials"}
    missing = [name for name, ready in configured.items() if name in required_checks and ready is False]
    status_code = status.HTTP_200_OK if not missing else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ok" if not missing else "degraded",
            "configured": configured,
            "timestamp": isoformat(now_utc()),
        },
    )
