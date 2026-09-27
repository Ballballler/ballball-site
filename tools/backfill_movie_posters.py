"""给正式档案里缺海报的电影补上 TMDB 元数据。

为什么需要：这 6 部是 seed 数据，当年没配 poster_path，页面上是灰底占位符；
而候选片全都带 TMDB 海报，两栏摆在一起视觉断裂很明显。

做法：按片名走 TMDB 官网搜索接口（见 fetch_horror_candidates.py 的说明），
拿 tmdb_id + poster_path + overview + 评分，只补**空缺字段**，
已有的评价类字段（rating / verdict / review / watched_at）一律不动。

用法：
    python tools/backfill_movie_posters.py --dry-run
    python tools/backfill_movie_posters.py
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.database import Base, SessionLocal, engine, ensure_extra_columns  # noqa: E402
from app import models as M  # noqa: E402
from tools.fetch_horror_candidates import (  # noqa: E402
    _detail_meta,
    _detail_overview,
    _detail_page,
    _detail_poster,
    fetch_detail,
    pick,
    search,
)

DB = ROOT / "data" / "site.db"
BACKUP_DIR = ROOT / "backup"

# 片名 -> (搜索用原名, 期望年份)。tmdb_id 写死就没必要搜了，这里都走搜索。
TARGETS: dict[str, tuple[str, int]] = {
    "闪灵": ("The Shining", 1980),
    "遗传厄运": ("Hereditary", 2018),
    "逃出绝命镇": ("Get Out", 2017),
    "咒怨": ("Ju-on: The Grudge", 2002),
    "异形": ("Alien", 1979),
    "仲夏夜惊魂": ("Midsommar", 2019),
}


def backup_db() -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = BACKUP_DIR / f"movies-posters-{stamp}"
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
    try:
        movies = db.query(M.Movie).filter(M.Movie.status == "watched").all()
        touched = 0
        for m in movies:
            spec = TARGETS.get(m.title)
            if not spec:
                print(f"  [跳过] 《{m.title}》不在补全清单里")
                continue
            if m.poster_path and m.overview:
                print(f"  [已有] 《{m.title}》海报与简介都在，跳过")
                continue

            name, year = spec
            print(f"\n[{m.title}] 搜索 TMDB：{name} ({year})")
            hits = search(name)
            if not hits:
                print("    -> 没搜到")
                continue
            hit = pick(hits, name, year)
            if not hit:
                print("    -> 没挑出合适条目")
                continue
            tid = int(hit["id"])
            print(f"    -> id={tid} {hit.get('title')} / {hit.get('original_title')}")

            detail = fetch_detail(tid)
            # 只填空缺，绝不覆盖站长自己写的东西
            if not m.poster_path:
                m.poster_path = hit.get("poster_path") or _detail_poster(tid) or ""
            if not m.backdrop_path:
                m.backdrop_path = hit.get("backdrop_path") or ""
            if not m.overview:
                m.overview = (hit.get("overview") or "").strip() or _detail_overview(tid)
            if not m.tmdb_id:
                m.tmdb_id = tid
            if not m.runtime and detail.get("runtime"):
                m.runtime = int(detail["runtime"])
            if not m.tmdb_rating:
                m.tmdb_rating = float(hit.get("vote_average") or 0)
            if not m.director and detail.get("director"):
                m.director = detail["director"]
            if not m.genres and detail.get("genres"):
                m.genres = detail["genres"]

            print(
                f"    海报 {m.poster_path}  片长 {m.runtime}min  "
                f"导演 {m.director}  TMDB {m.tmdb_rating}"
            )
            touched += 1
            time.sleep(0.35)

        if args.dry_run:
            db.rollback()
            print(f"\n[dry-run] 会更新 {touched} 部，未写库")
        else:
            db.commit()
            print(f"\n[完成] 更新 {touched} 部")
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
