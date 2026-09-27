"""把抓好的恐怖片候选片单导入电影档案，标成「候选（还没看）」。

用法：
    python tools/import_horror_candidates.py --dry-run     # 只看会做什么
    python tools/import_horror_candidates.py               # 真导入
    python tools/import_horror_candidates.py --replace     # 先删掉已有候选再导入

安全设计（沿用 import_two_works.py 的教训）：
    - 跑前自动把 site.db（含 -wal/-shm）备份到 backup/movies-candidates-<日期>/
    - --dry-run 全程不写库
    - 幂等：按 tmdb_id 判重，已存在就跳过（除非 --replace）
    - **绝不碰 status='watched' 的正式档案**，只增删候选

数据来源：data/horror_candidates.json（由 tools/fetch_horror_candidates.py 生成）
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.database import Base, SessionLocal, engine, ensure_extra_columns  # noqa: E402
from app import models as M  # noqa: E402


def init_db() -> list[str]:
    """建表 + 补列，跟 app/main.py 启动时做的一样（幂等）。"""
    Base.metadata.create_all(bind=engine)
    return ensure_extra_columns()

SRC = ROOT / "data" / "horror_candidates.json"
DB = ROOT / "data" / "site.db"
BACKUP_DIR = ROOT / "backup"

# TMDB 的 genre id -> 本站 movie_genre 分类名。
# 只在候选片没被显式指定分类时用，命中第一个。
GENRE_TO_CATEGORY = {
    27: "超自然",      # Horror，本站没有「恐怖」这个通用类，落到最接近的
    53: "心理惊悚",    # Thriller
    9648: "心理惊悚",  # Mystery
    878: "身体恐怖",   # Science Fiction（异形那类）
    10749: "",         # Romance，归类意义不大
    35: "恐怖喜剧",    # Comedy
    18: "",            # Drama
    14: "超自然",      # Fantasy
    80: "",            # Crime
}

# 写死 tmdb_id 的条目拿不到 genre_ids，用中文类型名兜底（详情页给的是中文）
GENRE_CN_TO_CATEGORY = {
    "恐怖": "超自然",
    "惊悚": "心理惊悚",
    "悬疑": "心理惊悚",
    "科幻": "身体恐怖",
    "喜剧": "恐怖喜剧",
    "奇幻": "超自然",
    "动作": "",
    "剧情": "",
    "犯罪": "",
}


def backup_db() -> Path:
    """整库备份（含 WAL/SHM，缺一不可）。"""
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = BACKUP_DIR / f"movies-candidates-{stamp}"
    dest.mkdir(parents=True, exist_ok=True)
    copied = []
    for suffix in ("", "-wal", "-shm"):
        src = Path(str(DB) + suffix)
        if src.exists():
            shutil.copy2(src, dest / src.name)
            copied.append(src.name)
    print(f"[备份] {', '.join(copied)} -> {dest}")
    return dest


def pick_category_id(rec: dict, cat_by_name: dict[str, int]) -> int | None:
    """按类型映射到本站分类。

    两条路：优先用 TMDB 的 genre_ids（数字，来自搜索接口）；
    写死 tmdb_id 的条目没有 genre_ids，退回用中文类型名匹配。
    """
    for gid in rec.get("genre_ids") or []:
        name = GENRE_TO_CATEGORY.get(int(gid))
        if name and name in cat_by_name:
            return cat_by_name[name]
    for gname in rec.get("genres") or []:
        name = GENRE_CN_TO_CATEGORY.get(gname)
        if name and name in cat_by_name:
            return cat_by_name[name]
    return None


def build_payload(rec: dict, cat_by_name: dict[str, int]) -> dict:
    """候选片只填「资料」部分，不留任何评价 —— 评价等站长看完自己写。"""
    return {
        "title": rec["title"],
        "original_title": rec.get("original_title") or "",
        "year": int(rec.get("year") or 0) or 2000,
        "director": rec.get("director") or "",
        "country": rec.get("country") or "",
        "tmdb_id": rec.get("tmdb_id"),
        "poster_path": rec.get("poster_path") or "",
        "backdrop_path": rec.get("backdrop_path") or "",
        "overview": (rec.get("overview") or "").strip(),
        "runtime": int(rec.get("runtime") or 0),
        "tmdb_rating": float(rec.get("tmdb_rating") or 0),
        "genres": rec.get("genres") or [],
        "category_id": pick_category_id(rec, cat_by_name),
        # 评分字段留默认值，站长打分时再改
        "rating": 0.0,
        "verdict": "",
        "review": "",
        "scare_level": 3,
        "recommend_level": 3,
        "tags": ["候选"],
        "watched_at": "",
        "status": "candidate",
        "sort_order": 0,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="导入恐怖片候选片单")
    ap.add_argument("--dry-run", action="store_true", help="只显示计划，不写库")
    ap.add_argument("--replace", action="store_true", help="先清掉已有候选片再导入")
    ap.add_argument("--src", default=str(SRC), help="候选 JSON 路径")
    args = ap.parse_args()

    src = Path(args.src)
    if not src.exists():
        print(f"找不到候选文件 {src}，先跑 tools/fetch_horror_candidates.py")
        return 1
    records = json.loads(src.read_text(encoding="utf-8"))
    print(f"[读取] {len(records)} 条候选 <- {src.name}")

    if not args.dry_run:
        backup_db()

    added_cols = init_db()
    if added_cols:
        print(f"[迁移] 补列：{', '.join(added_cols)}")

    db = SessionLocal()
    try:
        cats = db.query(M.Category).filter(M.Category.kind == "movie_genre").all()
        cat_by_name = {c.name: c.id for c in cats}
        print(f"[分类] 可用：{', '.join(cat_by_name)}")

        existing = {m.tmdb_id: m for m in db.query(M.Movie).all() if m.tmdb_id}
        watched_titles = {
            m.title for m in db.query(M.Movie).filter(M.Movie.status == "watched").all()
        }

        if args.replace:
            doomed = db.query(M.Movie).filter(M.Movie.status == "candidate").all()
            print(f"[替换] 将删除 {len(doomed)} 条已有候选")
            for m in doomed:
                print(f"        - {m.title}（{m.year}）")
            if not args.dry_run:
                for m in doomed:
                    db.delete(m)
                db.flush()

        created = updated = skipped = 0
        for rec in records:
            tid = rec.get("tmdb_id")
            title = rec["title"]

            # 已经作为「看过」的正式档案存在 -> 不重复添加
            if title in watched_titles:
                print(f"  [跳过] 《{title}》已在正式档案里")
                skipped += 1
                continue

            payload = build_payload(rec, cat_by_name)

            hit = existing.get(tid) if tid else None
            if hit:
                # 已存在（可能是上次导入的候选）-> 刷新资料，不动评价字段
                for k, v in payload.items():
                    if k in ("rating", "verdict", "review", "status"):
                        continue
                    setattr(hit, k, v)
                updated += 1
                print(f"  [更新] 《{title}》（{payload['year']}）id={hit.id}")
            else:
                obj = M.Movie(**payload)
                db.add(obj)
                db.flush()
                existing[tid] = obj
                created += 1
                print(f"  [新增] 《{title}》（{payload['year']}）id={obj.id}")

        if args.dry_run:
            db.rollback()
            print(f"\n[dry-run] 会新增 {created}、更新 {updated}、跳过 {skipped}，未写库")
        else:
            db.commit()
            print(f"\n[完成] 新增 {created}、更新 {updated}、跳过 {skipped}")

        total_candidate = (
            db.query(M.Movie).filter(M.Movie.status == "candidate").count()
            if not args.dry_run
            else created
        )
        print(f"[统计] 库中候选片 {total_candidate} 条")
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
