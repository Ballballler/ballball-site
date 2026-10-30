"""把 TMDB 的海报下载到本地 static/posters/，让海报不再依赖境外图床。

为什么需要：海报地址一直是 `https://image.tmdb.org/t/p/w500/...` 直连 TMDB 的 CDN。
实测这台机器上能通（15/15 都是 200，但单张要 1.3–2.4 秒），可真实浏览器里
经常请求挂起 —— 不报错也不返回，`<img>` 就一直是空的，海报位塌成一条深色空条。
这次改成「本地有就用本地，没有才回落到 TMDB」，两边都不吃亏。

命名用 `movie.id` 而不是 tmdb_id：片名/元数据可能重抓，主键是稳定的。

用法：
    python tools/cache_movie_posters.py --dry-run
    python tools/cache_movie_posters.py
    python tools/cache_movie_posters.py --force      # 已有文件也重下
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "site.db"
OUT_DIR = ROOT / "static" / "posters"
IMAGE_BASE = "https://image.tmdb.org/t/p/w500"
UA = "ballball-site-poster-cache/1.0"


def fetch(row_id: int, poster_path: str, force: bool) -> tuple[str, int]:
    dest = OUT_DIR / f"{row_id}.jpg"
    if dest.exists() and dest.stat().st_size > 1024 and not force:
        return ("skip", dest.stat().st_size)
    url = f"{IMAGE_BASE}/{poster_path.lstrip('/')}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = resp.read()
    if len(data) < 1024:
        raise ValueError(f"返回内容过小（{len(data)} 字节），可能不是图片")
    dest.write_bytes(data)
    return ("ok", len(data))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="只列出要下哪些，不落盘")
    ap.add_argument("--force", action="store_true", help="已有文件也重新下载")
    args = ap.parse_args()

    if not DB.exists():
        print(f"找不到数据库：{DB}", file=sys.stderr)
        raise SystemExit(2)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB)
    rows = con.execute(
        "select id, title, poster_path from movie where poster_path != '' order by id"
    ).fetchall()
    con.close()

    ok = skip = fail = 0
    total_bytes = 0
    for row_id, title, poster_path in rows:
        if args.dry_run:
            print(f"  {row_id:3d} {title}  ←  {poster_path}")
            continue
        try:
            status, size = fetch(row_id, poster_path, args.force)
        except (urllib.error.URLError, urllib.error.HTTPError, ValueError, TimeoutError) as exc:
            fail += 1
            print(f"  FAIL {row_id:3d} {title}  {exc}")
            continue
        if status == "ok":
            ok += 1
            total_bytes += size
            print(f"  ok   {row_id:3d} {title}  {size // 1024} KB")
        else:
            skip += 1
        time.sleep(0.15)  # 别把 TMDB 打太急

    if args.dry_run:
        print(f"\n共 {len(rows)} 部待检查。")
        return

    have = sum(1 for _ in OUT_DIR.glob("*.jpg"))
    print(f"\n新下载 {ok} / 跳过 {skip} / 失败 {fail}")
    print(f"本次写入 {total_bytes / 1024 / 1024:.1f} MB；目录现有 {have} 张，"
          f"合计 {sum(f.stat().st_size for f in OUT_DIR.glob('*.jpg')) / 1024 / 1024:.1f} MB")
    if fail:
        print("有失败的：重跑一次即可（已下好的会跳过）。", file=sys.stderr)


if __name__ == "__main__":
    main()
