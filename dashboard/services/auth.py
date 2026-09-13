from __future__ import annotations

import os
import secrets
import time
from typing import Any

from fastapi import Request, Response


class AuthService:
    cookie_name = "fiap_admin_session"

    def __init__(self) -> None:
        self.username = os.getenv("ADMIN_USERNAME", "")
        self.password = os.getenv("ADMIN_PASSWORD", "")
        self.session_ttl = int(os.getenv("ADMIN_SESSION_TTL_SECONDS", "43200"))
        self._sessions: dict[str, float] = {}

    def is_configured(self) -> bool:
        return bool(self.username and self.password)

    def verify_credentials(self, username: str, password: str) -> bool:
        if not self.is_configured():
            return False
        return secrets.compare_digest(username or "", self.username) and secrets.compare_digest(
            password or "", self.password
        )

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
            "session_ttl_seconds": self.session_ttl,
        }

    def _cleanup_sessions(self) -> None:
        now = time.time()
        expired = [token for token, expires_at in self._sessions.items() if expires_at < now]
        for token in expired:
            self._sessions.pop(token, None)
