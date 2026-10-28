"""Google Sign-In verification + signed session cookie. No third-party auth service."""
import base64
import hashlib
import hmac
import json
import secrets
import time

import httpx
from fastapi import Depends, HTTPException, Request, Response
from sqlmodel import select

from . import config
from .db import get_session
from .models import User

COOKIE = "bolo_session"
_TTL = 30 * 24 * 3600

_secret_cache: bytes | None = None


def _secret() -> bytes:
    """Session signing key: BOLO_SESSION_SECRET env, else a persisted random key."""
    global _secret_cache
    if _secret_cache is not None:
        return _secret_cache
    env = getattr(config, "BOLO_SESSION_SECRET", "")
    if env:
        _secret_cache = env.encode()
        return _secret_cache
    config.ensure_dirs()
    key_file = config.DB_PATH.parent / "session_secret"
    if key_file.exists():
        _secret_cache = key_file.read_bytes()
    else:
        key = secrets.token_hex(32)
        key_file.write_text(key)
        _secret_cache = key.encode()
    return _secret_cache


def _sign(payload_b64: bytes) -> str:
    return hmac.new(_secret(), payload_b64, hashlib.sha256).hexdigest()


def make_session_token(user_id: int) -> str:
    payload = {"uid": user_id, "exp": int(time.time()) + _TTL}
    raw = json.dumps(payload, separators=(",", ":")).encode()
    b64 = base64.urlsafe_b64encode(raw).rstrip(b"=")
    return f"{b64.decode()}.{_sign(b64)}"


def _decode_session_token(token: str) -> int | None:
    try:
        b64, sig = token.split(".")
        raw = base64.urlsafe_b64decode(b64 + "==")
        if not hmac.compare_digest(_sign(b64.encode()), sig):
            return None
        payload = json.loads(raw)
        if payload.get("exp", 0) < time.time():
            return None
        return int(payload["uid"])
    except Exception:
        return None


async def verify_google_credential(credential: str) -> dict:
    """Verify a Google ID token via Google's tokeninfo endpoint. Returns the claims."""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                "https://oauth2.googleapis.com/tokeninfo",
                params={"id_token": credential},
            )
    except httpx.HTTPError as exc:
        raise HTTPException(502, f"could not reach Google tokeninfo: {exc}") from exc
    if resp.status_code != 200:
        raise HTTPException(401, "invalid Google credential")
    claims = resp.json()
    aud = str(claims.get("aud", ""))
    if config.GOOGLE_CLIENT_ID and aud != config.GOOGLE_CLIENT_ID:
        raise HTTPException(401, "Google credential was issued for a different client")
    if claims.get("email_verified") in (False, "false") and claims.get("email"):
        raise HTTPException(401, "Google account email is not verified")
    return claims


async def current_user(request: Request) -> User:
    token = request.cookies.get(COOKIE)
    if not token:
        raise HTTPException(401, "not signed in")
    uid = _decode_session_token(token)
    if uid is None:
        raise HTTPException(401, "session expired or invalid")
    with get_session() as session:
        user = session.get(User, uid)
    if user is None:
        raise HTTPException(401, "account no longer exists")
    return user


def set_session_cookie(response: Response, user_id: int) -> None:
    response.set_cookie(
        COOKIE, make_session_token(user_id),
        max_age=_TTL, httponly=True, samesite="lax", secure=False,
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(COOKIE)


async def login_or_create_user(claims: dict) -> User:
    """Find or create the owner for a verified Google (or dev) identity."""
    sub = str(claims.get("sub") or claims.get("google_sub") or claims.get("email") or "")
    if not sub:
        raise HTTPException(400, "credential has no subject")
    with get_session() as session:
        user = session.exec(select(User).where(User.google_sub == sub)).first()
        if user is None:
            user = User(
                google_sub=sub,
                email=str(claims.get("email") or ""),
                name=str(claims.get("name") or claims.get("email") or "Shop owner"),
                picture=str(claims.get("picture") or ""),
            )
            session.add(user)
            session.commit()
        else:
            changed = False
            for field in ("name", "picture"):
                value = str(claims.get(field) or "")
                if value and getattr(user, field) != value:
                    setattr(user, field, value)
                    changed = True
            email = str(claims.get("email") or "")
            if email and not user.email:
                user.email = email
                changed = True
            if changed:
                session.add(user)
                session.commit()
        session.refresh(user)
    return user
