"""口令散列、会话签名、访客标识。

不引入 passlib / jwt 这类额外依赖：
- 口令用标准库 pbkdf2_hmac(salt 随机, 200k 轮)；
- 会话用 HMAC-SHA256 签名的短令牌，服务端无状态，重启不丢登录（密钥持久化在 .env）。
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from pathlib import Path

from .config import (
    DATA_DIR,
    SECRET_KEY,
    SECRET_KEY as _KEY,
    SESSION_TTL_SECONDS,
)

ADMIN_FILE = DATA_DIR / "admin.json"
PBKDF2_ROUNDS = 200_000

# 部署在 nginx 之后时需要读 X-Forwarded-For，否则所有人都是 127.0.0.1
TRUST_PROXY = os.getenv("TRUST_PROXY", "1") not in ("0", "false", "False")


# ------------------------------ 口令 ------------------------------


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ROUNDS)
    return "pbkdf2$%d$%s$%s" % (
        PBKDF2_ROUNDS,
        base64.b64encode(salt).decode(),
        base64.b64encode(dk).decode(),
    )


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, rounds, salt_b64, dk_b64 = stored.split("$")
        if algo != "pbkdf2":
            return False
        salt = base64.b64decode(salt_b64)
        expect = base64.b64decode(dk_b64)
    except Exception:
        return False
    got = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, int(rounds)
    )
    return hmac.compare_digest(got, expect)


def _read_admin() -> dict:
    if ADMIN_FILE.exists():
        try:
            return json.loads(ADMIN_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _write_admin(data: dict) -> None:
    ADMIN_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    try:
        os.chmod(ADMIN_FILE, 0o600)
    except OSError:
        pass


def ensure_admin_password(default_password: str) -> None:
    """首次启动时把环境变量里的初始口令落成散列文件。"""
    data = _read_admin()
    if not data.get("password_hash"):
        data["password_hash"] = hash_password(default_password)
        data["updated_at"] = time.time()
        _write_admin(data)


def check_admin_password(password: str) -> bool:
    data = _read_admin()
    return verify_password(password, data.get("password_hash", ""))


def set_admin_password(new_password: str) -> None:
    data = _read_admin()
    data["password_hash"] = hash_password(new_password)
    data["updated_at"] = time.time()
    _write_admin(data)


# ------------------------------ 会话 ------------------------------


def _sign(payload: str) -> str:
    return hmac.new(_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()


def create_session_token() -> str:
    exp = int(time.time()) + SESSION_TTL_SECONDS
    payload = f"{exp}.{secrets.token_urlsafe(12)}"
    return f"{payload}.{_sign(payload)}"


def verify_session_token(token: str | None) -> bool:
    if not token:
        return False
    parts = token.split(".")
    if len(parts) != 3:
        return False
    exp, nonce, sig = parts
    if not hmac.compare_digest(_sign(f"{exp}.{nonce}"), sig):
        return False
    try:
        return int(exp) > time.time()
    except ValueError:
        return False


# ------------------------------ 访客标识 ------------------------------


def client_ip(headers: dict, client_host: str | None) -> str:
    if TRUST_PROXY:
        xff = headers.get("x-forwarded-for", "")
        if xff:
            return xff.split(",")[0].strip()
        real = headers.get("x-real-ip", "")
        if real:
            return real.strip()
    return client_host or "unknown"


def ip_hash(ip: str) -> str:
    """只存哈希：既能限流与识别同一访客，又不落明文 IP。"""
    return hashlib.sha256(f"{ip}|{SECRET_KEY}".encode()).hexdigest()[:32]
