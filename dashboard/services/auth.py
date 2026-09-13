from __future__ import annotations

import json
import logging
import os
import secrets
import time
from datetime import UTC, datetime
from hashlib import pbkdf2_hmac
from pathlib import Path
from typing import Any

from fastapi import Request, Response


logger = logging.getLogger(__name__)


class AuthService:
    cookie_name = "fiap_admin_session"
    password_hash_name = "sha256"
    password_hash_iterations = 310_000

    def __init__(self) -> None:
        self.username = os.getenv("ADMIN_USERNAME", "")
        self.password = os.getenv("ADMIN_PASSWORD", "")
        self.session_ttl = int(os.getenv("ADMIN_SESSION_TTL_SECONDS", "43200"))
        self._sessions: dict[str, float] = {}
        self._default_profile_path = Path("/data/professor_profile.json")
        self._fallback_profile_path = Path(__file__).resolve().parent.parent / ".data" / "professor_profile.json"
        self._resolved_profile_path: Path | None = None

    def is_configured(self) -> bool:
        return self.profile_exists() or self.env_credentials_configured()

    def env_credentials_configured(self) -> bool:
        return bool(self.username and self.password)

    def resolve_profile_path(self) -> Path:
        configured_path = Path(os.getenv("ADMIN_PROFILE_PATH", str(self._default_profile_path)))
        profile_path = self._select_profile_path(configured_path)
        if self._resolved_profile_path != profile_path:
            logger.info("Using admin profile path: %s", profile_path)
            self._resolved_profile_path = profile_path
        return profile_path

    def profile_exists(self) -> bool:
        return self.load_profile() is not None

    def load_profile(self) -> dict[str, Any] | None:
        profile_path = self.resolve_profile_path()
        if not profile_path.is_file():
            return None
        try:
            profile = json.loads(profile_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Failed to read admin profile from %s: %s", profile_path, exc)
            return None
        required_fields = {"username", "salt", "password_hash", "created_at", "updated_at"}
        if not isinstance(profile, dict) or not required_fields.issubset(profile):
            logger.warning("Admin profile at %s is missing required fields", profile_path)
            return None
        return profile

    def create_profile(self, username: str, password: str) -> dict[str, Any]:
        profile_path = self.resolve_profile_path()
        profile_path.parent.mkdir(parents=True, exist_ok=True)
        timestamp = self._timestamp_utc()
        salt = secrets.token_hex(16)
        profile = {
            "username": username.strip(),
            "salt": salt,
            "password_hash": self._derive_password_hash(password, salt),
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        tmp_path = profile_path.with_name(f".{profile_path.name}.{secrets.token_hex(8)}.tmp")
        try:
            tmp_path.write_text(json.dumps(profile, ensure_ascii=True, indent=2), encoding="utf-8")
            os.replace(tmp_path, profile_path)
        finally:
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)
        return profile

    def verify_credentials(self, username: str, password: str) -> bool:
        profile = self.load_profile()
        if profile is not None:
            if not secrets.compare_digest(username or "", str(profile["username"])):
                return False
            candidate_hash = self._derive_password_hash(password or "", str(profile["salt"]))
            return secrets.compare_digest(candidate_hash, str(profile["password_hash"]))
        if not self.env_credentials_configured():
            return False
        return secrets.compare_digest(username or "", self.username) and secrets.compare_digest(password or "", self.password)

    def create_session(self) -> str:
        token = secrets.token_urlsafe(32)
        self._sessions[token] = time.time() + self.session_ttl
        self._cleanup_sessions()
        return token

    def invalidate_session(self, token: str | None) -> None:
        if token:
            self._sessions.pop(token, None)

    def get_session_token(self, request: Request) -> str | None:
        token = request.cookies.get(self.cookie_name)
        if not token:
            return None
        expires_at = self._sessions.get(token)
        if not expires_at or expires_at < time.time():
            self.invalidate_session(token)
            return None
        return token

    def is_authenticated(self, request: Request) -> bool:
        return self.get_session_token(request) is not None

    def set_session_cookie(self, response: Response, token: str) -> None:
        response.set_cookie(
            key=self.cookie_name,
            value=token,
            max_age=self.session_ttl,
            httponly=True,
            secure=True,
            samesite="strict",
            path="/",
        )

    def clear_session_cookie(self, response: Response) -> None:
        response.delete_cookie(
            key=self.cookie_name,
            path="/",
            httponly=True,
            secure=True,
            samesite="strict",
        )

    def config_status(self) -> dict[str, Any]:
        return {
            "admin_credentials": self.is_configured(),
            "admin_profile": self.profile_exists(),
            "session_ttl_seconds": self.session_ttl,
        }

    def _cleanup_sessions(self) -> None:
        now = time.time()
        expired = [token for token, expires_at in self._sessions.items() if expires_at < now]
        for token in expired:
            self._sessions.pop(token, None)

    def _select_profile_path(self, configured_path: Path) -> Path:
        if configured_path.is_file():
            return configured_path
        parent = configured_path.parent
        if parent.exists() and os.access(parent, os.W_OK):
            return configured_path
        fallback_parent = self._fallback_profile_path.parent
        fallback_parent.mkdir(parents=True, exist_ok=True)
        return self._fallback_profile_path

    def _derive_password_hash(self, password: str, salt: str) -> str:
        derived_key = pbkdf2_hmac(
            self.password_hash_name,
            password.encode("utf-8"),
            bytes.fromhex(salt),
            self.password_hash_iterations,
        )
        return derived_key.hex()

    def _timestamp_utc(self) -> str:
        return datetime.now(UTC).isoformat().replace("+00:00", "Z")
