"""抓取「近些年最受欢迎的恐怖片」候选片单的真实 TMDB 元数据。

为什么不用 app/tmdb.py：
    本机 api.themoviedb.org 被网络策略挡住（直连 ReadTimeout、代理端口未开），
    httpx 走不通。但实测 www.themoviedb.org 可达，且它自己的前端搜索接口
        /search/remote/movie?query=<片名>&language=zh-CN
    返回的 JSON 字段与 v3 API 完全一致（id / poster_path / overview /
    vote_average / genre_ids ...），无需 key。

本脚本做三件事：
    1. 按 SLATE 里的片单，逐部走官网搜索接口拿 tmdb_id（同名多版本按年份卡）；
    2. 对命中的 id 抓详情页，补 API 不给的字段：导演、片长、制片国家；
    3. 输出 data/horror_candidates.json，供导入脚本使用。

图片地址一律只存 poster_path 相对路径（沿用项目红线：不下载图片到本地），
渲染时由 Movie.poster_url 拼 image.tmdb.org。
"""
from __future__ import annotations

import html
import json
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "horror_candidates.json"

UA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}
SEARCH_UA = {**UA, "Accept": "application/json", "Referer": "https://www.themoviedb.org/"}

# 片单：近十年（2014-2025）口碑与热度双高的恐怖片。
# 格式三选一：
#     ("原名", 期望年份)                 —— 走搜索自动挑
#     ("原名", 期望年份, tmdb_id)        —— 跳过搜索，直接用指定 id（最可靠）
#
# 什么时候必须硬指定 id：搜索接口对**非英语片名**召回不稳。
# 实测踩坑：「Exhuma」并到 Exhumator(1300292)、「The Wailing」并到
# The Stranger(1413713)——都是完全无关的片子。这类一律写死 id。
#
# 想换片单改这里，脚本其余部分不用动。
SLATE: list[tuple] = [
    ("Sinners", 2025),
    ("Godzilla Minus One", 2023),
    ("Talk to Me", 2022),
    ("Barbarian", 2022),
    ("Nosferatu", 2024),
    ("Exhuma", 2024, 838209),  # 파묘 破墓，搜索会并到 Exhumator，必须写死
    ("The Wailing", 2016, 293670),  # 곡성 哭声，搜索会并到 The Stranger，必须写死
    ("Train to Busan", 2016),
    ("The Witch", 2015),
    ("It Follows", 2014),
    ("The Invisible Man", 2020),
    ("Midsommar", 2019),
    ("Hereditary", 2018),
    ("Get Out", 2017),
    ("Us", 2019),
    ("A Quiet Place", 2018),
    ("The Nun", 2018),
    ("It", 2017),
    ("Suspiria", 2018),
    ("The Babadook", 2014),
    ("Happy Death Day", 2017),
    ("The Conjuring", 2013),
    ("Insidious", 2010),
    ("The Substance", 2024),
    ("Pearl", 2022),
    ("X", 2022),
    ("Malignant", 2021),
    ("The Black Phone", 2021),
    ("Prey", 2022),
    ("Bones and All", 2022),
    ("The Menu", 2022),
    ("Skinamarink", 2022),
    ("Watcher", 2022),
    ("Fresh", 2022),
    ("Smile", 2022),
    ("M3GAN", 2022),
    ("Candyman", 2021),
    ("Last Night in Soho", 2021),
    ("The Night House", 2020),
    ("His House", 2020),
    ("Relic", 2020),
    ("The Lodge", 2019),
    ("Ready or Not", 2019),
    ("Crawl", 2019),
    ("Annihilation", 2018),
]


def _num(v) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def http_json(url: str, timeout: float = 12.0):
    req = urllib.request.Request(url, headers=SEARCH_UA)
    with urllib.request.urlopen(req, timeout=timeout) as res:
        return json.loads(res.read().decode("utf-8", errors="replace"))


def http_text(url: str, timeout: float = 15.0) -> str:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as res:
        return res.read().decode("utf-8", errors="replace")


def search(name: str) -> list[dict]:
    url = (
        "https://www.themoviedb.org/search/remote/movie?query="
        + urllib.parse.quote(name)
        + "&language=zh-CN"
    )
    try:
        data = http_json(url)
    except Exception as exc:  # noqa: BLE001
        print(f"    [搜索失败] {name}: {exc}")
        return []
    return data if isinstance(data, list) else []


def _norm(s: str) -> str:
    """归一化片名，用于模糊匹配（去空格、标点、全角半角差异）。"""
    s = unicodedata.normalize("NFKC", s or "").lower()
    return re.sub(r"[\s\-_:：·,，.。!！?？'\"“”‘’()（）\[\]]+", "", s)


def pick(hits: list[dict], name: str, year: int) -> dict | None:
    """在同名结果里挑最像的那条。

    打分顺序（经验来自本轮踩坑）：
      1. 原名精确匹配最重 —— "Sinners" 会命中 1920 年老片，只有原名+票数能救；
      2. 票数其次 —— 热门新片票数远高于同名冷门片；
      3. 年份只做**软性**加分，因为 TMDB 官网中文站的 release_date 并不可靠
         （《遗传厄运》返回 2025-06-14，那是中国大陆条目更新日），
         硬卡年份反而会把正确的条目排到后面。
    """
    target = _norm(name)
    best, best_score = None, -1e9
    for h in hits:
        title = _norm(h.get("title") or "")
        orig = _norm(h.get("original_title") or "")
        release = (h.get("release_date") or "")[:4]
        hy = int(release) if release.isdigit() else 0
        votes = _num(h.get("vote_count"))

        score = 0.0
        # 1) 片名
        if target and target == orig:
            score += 200  # 原名（通常是英文）精确命中，最可信
        elif target and target == title:
            score += 120
        elif target and (target in orig or orig in target):
            score += 50
        elif target and (target in title or title in target):
            score += 30
        # 2) 票数：5000 票封顶 100 分，压制同名冷门条目
        score += min(votes / 5000.0, 1.0) * 100
        # 3) 年份软性奖励：只加分不扣分
        if hy and year and hy == year:
            score += 25
        elif hy and year and abs(hy - year) <= 1:
            score += 12

        if score > best_score:
            best, best_score = h, score
    return best


def _one(pat: str, text: str) -> str | None:
    m = re.search(pat, text, re.S)
    return html.unescape(m.group(1).strip()) if m else None


def fetch_detail(tmdb_id: int) -> dict:
    """抓详情页补字段。失败不致命，返回空 dict。"""
    url = f"https://www.themoviedb.org/movie/{tmdb_id}"
    try:
        page = http_text(url)
    except Exception as exc:  # noqa: BLE001
        print(f"    [详情失败] {tmdb_id}: {exc}")
        return {}

    out: dict = {}

    # 真实年份：页面 <title> 形如「遗传厄运 (2018) — ...」
    tm = re.search(r"<title>.*?\((\d{4})\)", page)
    if tm:
        out["year"] = int(tm.group(1))

    # 片长 "2h 8m" / "1h 46m" -> 分钟
    rt = _one(r'<span class="runtime">([^<]+)</span>', page)
    if rt:
        h = re.search(r"(\d+)h", rt)
        m = re.search(r"(\d+)m", rt)
        out["runtime"] = (int(h.group(1)) * 60 if h else 0) + (int(m.group(1)) if m else 0)

    # 导演：people 区块里 character 含 Director 的那条
    people = re.findall(
        r'<li class="profile">\s*<p><a href="/person/[^"]+">([^<]+)</a></p>\s*'
        r'<p class="character">([^<]*)</p>',
        page,
        re.S,
    )
    directors = [html.unescape(n) for n, role in people if "Director" in (role or "")]
    if directors:
        out["director"] = "、".join(directors[:3])

    # 制片国家
    countries = re.findall(
        r'<a href="/movie\?with_original_language=[^"]+">([^<]+)</a>', page
    )
    # 更稳的是 facts 区里的「制片国家/地区」
    block = re.search(r"制片国家/地区</bdi>(.*?)</p>", page, re.S)
    if block:
        cs = re.findall(r">([^<>]+)</a>", block.group(1))
        cs = [html.unescape(c).strip() for c in cs if c.strip()]
        if cs:
            out["country"] = " / ".join(cs[:3])
    elif countries:
        out["country"] = " / ".join(countries[:3])

    # 类型名（中文）
    genres = re.findall(r'<a href="/genre/\d+[^"]*/movie">([^<]+)</a>', page)
    if genres:
        out["genres"] = [html.unescape(g).strip() for g in genres[:4]]

    return out


# 详情页缓存：写死 id 的分支要复用同一份 HTML 抓多个字段，别再请求一遍
_page_cache: dict[int, str] = {}


def _detail_page(tmdb_id: int) -> str:
    if tmdb_id not in _page_cache:
        try:
            _page_cache[tmdb_id] = http_text(f"https://www.themoviedb.org/movie/{tmdb_id}")
        except Exception:  # noqa: BLE001
            _page_cache[tmdb_id] = ""
    return _page_cache[tmdb_id]


def _detail_meta(tmdb_id: int) -> tuple[str, str, float, int]:
    """从详情页拿 (中文名, 原名, TMDB 评分, 票数)。"""
    page = _detail_page(tmdb_id)
    title = _one(r'<meta property="og:title" content="([^"]+)"', page) or ""
    # <title>「遗传厄运 (2018) — ...」里没有原名；原名在 og:title 之外的 h2 里
    orig = _one(r'<h2[^>]*>\s*<a[^>]*>([^<]+)</a>', page) or ""
    if not orig:
        orig = _one(r'<em[^>]*class="tagline"[^>]*>([^<]+)</em>', page) or ""
    rating = 0.0
    m = re.search(r'data-percent="([\d.]+)"', page)
    if m:
        rating = round(_num(m.group(1)) / 10.0, 1)
    votes = 0
    mv = re.search(r"([\d,]+)\s*(?:票|votes)", page)
    if mv:
        votes = int(mv.group(1).replace(",", ""))
    return title, orig, rating, votes


def _detail_overview(tmdb_id: int) -> str:
    page = _detail_page(tmdb_id)
    return _one(r'<div class="overview"[^>]*>\s*<p>(.*?)</p>', page) or ""


def _detail_poster(tmdb_id: int) -> str:
    page = _detail_page(tmdb_id)
    url = _one(r'<meta property="og:image" content="([^"]+)"', page) or ""
    m = re.search(r"/t/p/\w+/([^/\"?]+)$", url)
    return f"/{m.group(1)}" if m else ""


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
            # 写死 id：跳过搜索，直接抓详情（非英语片名只能这么办）
            print(f"    -> 指定 id={forced_id}")
            tmdb_id = int(forced_id)
            if tmdb_id in seen_ids:
                print("    -> 重复条目，跳过")
                continue
            seen_ids.add(tmdb_id)
            detail = fetch_detail(tmdb_id)
            # 写死 id 时搜索接口拿不到字段，从详情页补标题
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

        hits = search(name)
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
            # 年份以详情页 <title> 为准；拿不到才退回搜索结果
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
        time.sleep(0.35)  # 别把人家官网打疼了

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n写出 {len(results)} 条 -> {OUT}")
    if missed:
        print(f"未命中 {len(missed)} 条：{', '.join(missed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
