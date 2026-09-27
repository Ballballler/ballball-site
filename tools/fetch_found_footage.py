"""抓取「伪纪录片 / found footage」恐怖片片单的真实 TMDB 元数据。

与 fetch_horror_candidates.py 是**姊妹脚本**，共用同一套官网搜索 + 详情页解析
（从那个模块 import，不重复实现），区别只有两点：
    1. 片单换成本文件里的 SLATE（伪纪录片专场）；
    2. 输出到独立的 data/found_footage.json —— **绝不覆盖** horror_candidates.json。

为什么单开一个文件而不是往里加：
    fetch_horror_candidates.py 的 OUT 是**整体覆盖写**。那份 45 条的
    horror_candidates.json 是上一轮辛苦抓的、已经入库在跑的资产，重跑一次若中途
    失败就会把它写坏。分成两个输出文件，两个片单互不干扰。

用法：
    python tools/fetch_found_footage.py                # 全量抓，写 found_footage.json
    python tools/fetch_found_footage.py "Blair"        # 只抓名字含 Blair 的（调试用）
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.fetch_horror_candidates import (  # noqa: E402
    _detail_meta,
    _detail_overview,
    _detail_poster,
    _norm,
    _num,
    fetch_detail,
    pick,
    search,
)

OUT = ROOT / "data" / "found_footage.json"


def search_retry(name: str, tries: int = 3) -> list[dict]:
    """官网搜索接口偶发 read timeout，退避重试几次再放弃。

    上两轮实测：22 条里有 1-2 条会撞上超时，重跑一次就好——但这靠人工重跑不体面，
    而且重跑会把整个片单重抓一遍。这里就地重试。
    """
    for i in range(tries):
        hits = search(name)
        if hits:
            return hits
        if i < tries - 1:
            time.sleep(1.2 * (i + 1))
    return []

# 伪纪录片（found footage）恐怖片片单。
# 格式三选一（与 horror_candidates.py 一致）：
#     ("原名", 年份)               —— 走搜索自动挑
#     ("原名", 年份, tmdb_id)      —— 跳过搜索，直接指定 id
#
# 非英语片名 / 同名译名多的，一律写死 tmdb_id（搜索召回不稳，见姊妹脚本注释）。
SLATE: list[tuple] = [
    # —— 开山鼻祖与经典 ——
    ("The Blair Witch Project", 1999, 2667),  # 《女巫布莱尔》，搜索会命中 2016 同名续集，写死
    ("Cannibal Holocaust", 1980),
    ("The Last Broadcast", 1998),
    # —— 2000s 的爆发期 ——
    ("REC", 2007),
    ("Paranormal Activity", 2007),
    ("Cloverfield", 2008),
    ("Diary of the Dead", 2007, 13025),  # 《死亡日记》罗梅罗，搜索首条常并到 1976 同名片
    ("Lake Mungo", 2008, 27374),  # 《蒙哥湖》，官网搜索偶发超时，直接写死
    ("Noroi: The Curse", 2005, 21506),  # 《灵异咒》ノロイ（白石晃士），写死
    # —— 2010s ——
    ("Trollhunter", 2010, 46146),  # 《追击巨怪》Trolljegeren，写死
    ("Grave Encounters", 2011),
    ("The Bay", 2012),
    ("V/H/S", 2012),
    ("As Above, So Below", 2014),
    ("The Taking of Deborah Logan", 2014),
    ("Hell House LLC", 2015),
    # —— 亚洲 ——
    ("Gonjiam: Haunted Asylum", 2018, 508642),  # 《昆池岩》곤지암，写死
    ("Occult", 2009, 118315),  # 《超自然》オカルト（白石晃士），写死
    # —— 近年 ——
    ("Host", 2020),
    ("Deadstream", 2022),
    ("Dashcam", 2021),
    ("The Outwaters", 2022),
]


def main() -> int:
    only = None
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        only = sys.argv[1]

    results: list[dict] = []
    seen_ids: set[int] = set()
    missed: list[str] = []

    for idx, spec in enumerate(SLATE, 1):
        name, year = spec[0], spec[1]
        forced_id = spec[2] if len(spec) > 2 else None
        if only and _norm(only) not in _norm(name):
            continue
        print(f"[{idx:>2}/{len(SLATE)}] {name} ({year})")

        if forced_id:
            tmdb_id = int(forced_id)
            print(f"    -> 指定 id={tmdb_id}")
            if tmdb_id in seen_ids:
                print("    -> 重复条目，跳过")
                continue
            seen_ids.add(tmdb_id)
            detail = fetch_detail(tmdb_id)
            title, orig, rating, votes = _detail_meta(tmdb_id)
            print(
                f"    -> 中文名={title}  原名={orig}  "
                f"{detail.get('year') or year}  TMDB={rating:.1f}  votes={votes}"
            )
            rec = {
                "search_name": name,
                "tmdb_id": tmdb_id,
                "title": title or name,
                "original_title": orig or "",
                "year": detail.get("year") or year,
                "overview": _detail_overview(tmdb_id),
                "poster_path": _detail_poster(tmdb_id),
                "backdrop_path": "",
                "tmdb_rating": rating,
                "vote_count": votes,
                "genre_ids": [],
                "popularity": 0.0,
            }
            rec.update(detail)
            results.append(rec)
            time.sleep(0.35)
            continue

        hits = search_retry(name)
        if not hits:
            print("    -> 没有搜索结果")
            missed.append(name)
            continue
        hit = pick(hits, name, year)
        if not hit:
            print("    -> 没挑出合适条目")
            missed.append(name)
            continue
        tmdb_id = int(hit["id"])
        if tmdb_id in seen_ids:
            print(f"    -> 重复条目，跳过（id={tmdb_id}）")
            continue
        seen_ids.add(tmdb_id)

        release = (hit.get("release_date") or "")[:4]
        print(
            f"    -> id={tmdb_id}  中文名={hit.get('title')}  "
            f"原名={hit.get('original_title')}  {release}  "
            f"TMDB={_num(hit.get('vote_average')):.1f}  "
            f"votes={int(_num(hit.get('vote_count')))}"
        )
        detail = fetch_detail(tmdb_id)
        rec = {
            "search_name": name,
            "tmdb_id": tmdb_id,
            "title": hit.get("title") or name,
            "original_title": hit.get("original_title") or "",
            "year": detail.get("year") or (int(release) if release.isdigit() else year),
            "overview": hit.get("overview") or "",
            "poster_path": hit.get("poster_path") or "",
            "backdrop_path": hit.get("backdrop_path") or "",
            "tmdb_rating": round(_num(hit.get("vote_average")), 1),
            "vote_count": int(_num(hit.get("vote_count"))),
            "genre_ids": hit.get("genre_ids") or [],
            "popularity": round(_num(hit.get("popularity")), 1),
        }
        rec.update(detail)
        results.append(rec)
        time.sleep(0.35)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n写出 {len(results)} 条 -> {OUT}")
    if missed:
        print(f"未命中 {len(missed)} 条：{', '.join(missed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
