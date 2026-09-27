"""修复 movie 表里被误写回 candidate 的正式档案，并清理转正档案残留的「候选」标签。

为什么需要：
    后台电影编辑对话框会把整份字段一起 PUT 上来，其中「档案状态」下拉默认取
    `default: "watched"`。当一条记录本来就是 candidate 时，打开保存一次不会出问题；
    但当站长把一部片手动改成 watched 之后，若那次提交的 payload 里 status 仍是
    candidate（例如先前的表单缓存/误选），PUT 就直接 setattr 写库，**没有白名单、
    也没有触发器兜底**，于是正式档案被悄悄打回候选区。

    典型受害：id=5《异形》、id=6《仲夏夜惊魂》—— 它们带着完整长评、真实评分、
    观看日期，tags 里也没有「候选」痕迹，明显是正经档案，却被标成 candidate。

另外：走 PUT 转正的档案（釜山行/寂静之地/招魂/危笑）tags 里还留着「候选」，
    POST /rate 会自动剔除、PUT 不会，这里一并清掉。

用法：
    python tools/fix_movie_status.py --dry-run
    python tools/fix_movie_status.py
"""
from __future__ import annotations

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.database import Base, SessionLocal, engine, ensure_extra_columns  # noqa: E402
from app import models as M  # noqa: E402

DB = ROOT / "data" / "site.db"
BACKUP_DIR = ROOT / "backup"

# 被误标成 candidate 的正式档案（按片名，不按 id —— id 会漂移）
RESTORE_WATCHED = ["异形", "仲夏夜惊魂"]

CANDIDATE_TAG = "候选"


def backup_db() -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = BACKUP_DIR / f"fix-status-{stamp}"
    dest.mkdir(parents=True, exist_ok=True)
    for suffix in ("", "-wal", "-shm"):
        src = Path(str(DB) + suffix)
        if src.exists():
            shutil.copy2(src, dest / src.name)
    print(f"[备份] -> {dest}")
    return dest


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not args.dry_run:
        backup_db()

    Base.metadata.create_all(bind=engine)
    ensure_extra_columns()

    db = SessionLocal()
    changed = 0
    try:
        # 1. 恢复被误标的正式档案
        for title in RESTORE_WATCHED:
            m = db.query(M.Movie).filter(M.Movie.title == title).one_or_none()
            if m is None:
                print(f"  [缺失] 《{title}》不在库里，跳过")
                continue
            if m.status == "watched":
                print(f"  [无需] 《{title}》已是 watched")
                continue
            # 安全闸：必须是真档案才敢恢复（有评分或长评或观看日期）
            evidence = (m.rating or 0) > 0 or bool(m.review) or bool(m.watched_at)
            if not evidence:
                print(f"  [拒绝] 《{title}》没有任何正式档案特征，不恢复（status={m.status}）")
                continue
            print(f"  [恢复] 《{title}》 {m.status} -> watched  （评分 {m.rating} / 长评 {len(m.review or '')} 字 / 看于 {m.watched_at}）")
            m.status = "watched"
            changed += 1

        # 2. 清理转正档案残留的「候选」标签
        for m in db.query(M.Movie).filter(M.Movie.status == "watched").all():
            tags = list(m.tags or [])
            if CANDIDATE_TAG in tags:
                kept = [t for t in tags if t != CANDIDATE_TAG]
                print(f"  [清标签] 《{m.title}》 {tags} -> {kept}")
                m.tags = kept
                changed += 1

        if args.dry_run:
            db.rollback()
            print(f"\n[dry-run] 会改动 {changed} 处，未写库")
        else:
            db.commit()
            print(f"\n[完成] 改动 {changed} 处")
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
