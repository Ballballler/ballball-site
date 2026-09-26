"""评论区：对所有访客开放，昵称即可发言。

限流放在进程内存里（单进程部署足够；多 worker 场景请把 Comment 计数改到 Redis）。
评论内容前端一律用 textContent 渲染，天然免疫 XSS。
"""
from __future__ import annotations

import time
from collections import defaultdict

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import select

from ..config import (
    COMMENT_MODERATION,
    COMMENT_RATE_LIMIT,
    COMMENT_RATE_WINDOW,
    COMMENT_TARGETS,
)
from ..database import SessionLocal
from ..models import Comment, Movie, Profile, Work
from ..schemas import CommentCreate, CommentOut
from ..security import client_ip, ip_hash

router = APIRouter(prefix="/api/comments", tags=["comments"])

# ip_hash -> 最近发言时间戳
_RATE_BUCKET: dict[str, list[float]] = defaultdict(list)


def _target_exists(target_type: str, target_id: int) -> bool:
    with SessionLocal() as db:
        if target_type == "movie":
            return db.get(Movie, target_id) is not None
        if target_type == "work":
            return db.get(Work, target_id) is not None
        if target_type == "profile":
            return db.get(Profile, target_id) is not None
    return False


@router.get("", response_model=list[CommentOut])
def list_comments(
    target_type: str,
    target_id: int = 0,
    limit: int = 200,
) -> list[Comment]:
    if target_type not in COMMENT_TARGETS:
        raise HTTPException(status_code=400, detail="不支持的评论目标")
    with SessionLocal() as db:
        stmt = (
            select(Comment)
            .where(
                Comment.target_type == target_type,
                Comment.target_id == target_id,
                Comment.hidden.is_(False),
            )
            .order_by(Comment.created_at.desc())
            .limit(min(limit, 500))
        )
        # 前台按时间正序阅读更自然
        rows = list(db.scalars(stmt).all())
        return list(reversed(rows))


@router.post("/{target_type}/{target_id}", response_model=CommentOut)
def create_comment(
    target_type: str,
    target_id: int,
    payload: CommentCreate,
    request: Request,
) -> Comment:
    if target_type not in COMMENT_TARGETS:
        raise HTTPException(status_code=400, detail="不支持的评论目标")
    if not _target_exists(target_type, target_id):
        raise HTTPException(status_code=404, detail="评论目标不存在")

    ip = client_ip(dict(request.headers), request.client.host if request.client else "")
    key = ip_hash(ip)

    now = time.time()
    bucket = [t for t in _RATE_BUCKET[key] if now - t < COMMENT_RATE_WINDOW]
    if len(bucket) >= COMMENT_RATE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail=f"发言太频繁了，{COMMENT_RATE_WINDOW // 60} 分钟后再来吧",
        )
    bucket.append(now)
    _RATE_BUCKET[key] = bucket

    with SessionLocal() as db:
        comment = Comment(
            target_type=target_type,
            target_id=target_id,
            nickname=payload.nickname,
            content=payload.content,
            ip_hash=key,
            # 先审后发：留言先扣下，等站长在后台点「通过」才公开
            hidden=COMMENT_MODERATION,
            reviewed=not COMMENT_MODERATION,
        )
        db.add(comment)
        db.commit()
        db.refresh(comment)
        return comment
