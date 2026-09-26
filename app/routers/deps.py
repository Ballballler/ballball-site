"""路由公共依赖：管理员鉴权。"""
from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status

from ..config import SESSION_COOKIE_NAME
from ..security import verify_session_token


def get_admin(request: Request) -> bool:
    """校验管理员会话 Cookie，失败直接 401。"""
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not verify_session_token(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录或登录已过期"
        )
    return True


require_admin = Depends(get_admin)
