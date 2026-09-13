from __future__ import annotations

import json
import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)


def mask_key(value: str | None) -> str:
    if not value:
        return "<missing>"
    text = str(value)
    if len(text) <= 4:
        return "sk-..." + text
    return f"sk-...{text[-4:]}"


class LiteLLMService:
    def __init__(self) -> None:
        self.base_url = os.getenv("LITELLM_BASE_URL", "").rstrip("/")
        self.master_key = os.getenv("LITELLM_MASTER_KEY", "")
        self.timeout = float(os.getenv("LITELLM_TIMEOUT_SECONDS", "30"))

    def is_configured(self) -> bool:
        return bool(self.base_url and self.master_key)

    async def get_keys(self) -> list[dict[str, Any]]:
        page = 1
        size = 100
        items: list[dict[str, Any]] = []
        while page <= 20:
            payload = await self._request(
                "GET",
                "/key/list",
                params={"page": page, "size": size, "return_full_object": "true"},
            )
            batch = self._extract_list(payload)
            if not batch:
                break
            items.extend(batch)
            if len(batch) < size:
                break
            page += 1
        return items

    async def get_key_info(self, key: str) -> dict[str, Any]:
        logger.info("Fetching LiteLLM key info for %s", mask_key(key))
        return await self._request("GET", "/key/info", params={"key": key})

    async def generate_key(self, payload: dict[str, Any]) -> dict[str, Any]:
        logger.info("Generating LiteLLM virtual key for alias=%s", payload.get("key_alias", "<unknown>"))
        return await self._request("POST", "/key/generate", json=payload)

    async def update_key(self, key: str, payload: dict[str, Any]) -> dict[str, Any]:
        logger.info("Updating LiteLLM key %s", mask_key(key))
        return await self._request("POST", "/key/update", json={"key": key, **payload})

    async def delete_key(self, key: str) -> dict[str, Any]:
        logger.info("Deleting LiteLLM key %s", mask_key(key))
        return await self._request("POST", "/key/delete", json={"keys": [key]})

    async def get_spend(self, **params: Any) -> list[dict[str, Any]]:
        payload = await self._request("GET", "/spend/logs", params=params)
        return self._extract_list(payload)

    async def block_key(self, key: str) -> dict[str, Any]:
        logger.info("Blocking LiteLLM key %s", mask_key(key))
        return await self._request("POST", "/key/block", json={"key": key})

    async def unblock_key(self, key: str) -> dict[str, Any]:
        logger.info("Unblocking LiteLLM key %s", mask_key(key))
        return await self._request("POST", "/key/unblock", json={"key": key})

    async def regenerate_key(self, key: str) -> dict[str, Any]:
        logger.info("Regenerating LiteLLM key %s", mask_key(key))
        return await self._request("POST", "/key/regenerate", json={"key": key})

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        if not self.is_configured():
            raise RuntimeError("LiteLLM service is not configured. Set LITELLM_BASE_URL and LITELLM_MASTER_KEY.")

        headers = {"Authorization": f"Bearer {self.master_key}"}
        if json is not None:
            headers["Content-Type"] = "application/json"

        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout, headers=headers) as client:
            try:
                response = await client.request(method, path, params=params, json=json)
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                logger.error(
                    "LiteLLM API error %s %s status=%s params=%s payload=%s",
                    method,
                    path,
                    exc.response.status_code,
                    self._mask_payload(params),
                    self._mask_payload(json),
                )
                raise RuntimeError(f"LiteLLM API request failed with status {exc.response.status_code}") from exc
            except httpx.HTTPError as exc:
                logger.error("LiteLLM API connection error %s %s: %s", method, path, exc)
                raise RuntimeError("LiteLLM API connection failed") from exc

        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            return response.json()
        return response.text

    def _extract_list(self, payload: Any) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        if not isinstance(payload, dict):
            return []
        for key in ("keys", "data", "items", "spend_logs", "logs"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        return []

    def _mask_payload(self, payload: dict[str, Any] | None) -> dict[str, Any] | None:
        if payload is None:
            return None
        masked: dict[str, Any] = {}
        for key, value in payload.items():
            if key.lower() in {"key", "token", "api_key"} and isinstance(value, str):
                masked[key] = mask_key(value)
            elif key.lower() in {"keys", "tokens"} and isinstance(value, list):
                masked[key] = [mask_key(item) if isinstance(item, str) else item for item in value]
            elif isinstance(value, dict):
                masked[key] = self._mask_payload(value)
            elif isinstance(value, str):
                masked[key] = self._mask_string(value)
            else:
                masked[key] = value
        return masked

    def _mask_string(self, value: str) -> str:
        if value.startswith("sk-"):
            return mask_key(value)
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return value
        if isinstance(parsed, dict):
            return json.dumps(self._mask_payload(parsed))
        return value
