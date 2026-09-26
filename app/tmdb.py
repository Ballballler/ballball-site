"""TMDB 客户端。

设计红线：**只取元数据与图片 URL，绝不把图片下载到本地**。
海报渲染时直接指向 image.tmdb.org，本地磁盘占用恒为 0。

为什么这样选：
- TMDB 免费 key，40 请求 / 10 秒，90 万+ 影片，支持 zh-CN；
- 它自己就是 CDN，图片在用户侧加载比本地磁盘更快（有边缘节点）；
- 存 1000 张海报原图约 1–3GB，存 1000 条 URL 约 200KB。

TMDB 要求使用方标注来源，见 ATTRIBUTION 常量，页脚必须露出来。
"""
from __future__ import annotations

import time
from urllib.parse import urlencode

import httpx

from .config import (
    TMDB_API_KEY,
    TMDB_CACHE_TTL,
    TMDB_IMAGE_BASE,
    TMDB_LANGUAGE,
)

_API = "https://api.themoviedb.org/3"
_TIMEOUT = httpx.Timeout(8.0, connect=4.0)

# 恐怖类型的 genre id，TMDB 官方固定值
HORROR_GENRE_ID = 27

# 使用条款要求的署名文案
ATTRIBUTION = (
    "This product uses the TMDB API but is not endorsed or certified by TMDB."
)

# key -> (过期时间戳, 数据)
_cache: dict[str, tuple[float, object]] = {}

# 图片基础地址由 /3/configuration 下发，不要硬编码；拉不到就用配置里的兜底值
_image_base: str = TMDB_IMAGE_BASE
_image_base_at = 0.0


class TmdbError(RuntimeError):
    """TMDB 不可用。message 会直接展示给站长，所以写人话。"""


def configured() -> bool:
    """是否配置了 key。没配置时后台要给出明确指引，而不是报一个莫名错误。"""
    return bool(TMDB_API_KEY)


def image_url(path: str, size: str = "w500") -> str:
    """把 TMDB 的图片相对路径拼成完整 URL。空路径返回空串，交给前端兜底。"""
    if not path:
        return ""
    return f"{_image_base}/{size}/{path.lstrip('/')}"


async def _get(path: str, params: dict, ttl: float | None = None) -> dict:
    key = f"{path}?{urlencode(sorted(params.items()))}"
    now = time.monotonic()
    hit = _cache.get(key)
    if hit and hit[0] > now:
        return hit[1]  # type: ignore[return-value]

    query = dict(params)
    query["api_key"] = TMDB_API_KEY
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            res = await client.get(_API + path, params=query)
    except httpx.HTTPError as exc:
        raise TmdbError(f"连不上 TMDB（{exc.__class__.__name__}），请检查网络") from exc

    if res.status_code == 401:
        raise TmdbError("TMDB_API_KEY 无效或被吊销（401）")
    if res.status_code == 429:
        raise TmdbError("TMDB 限流了（429），十几秒后重试")
    if res.status_code >= 400:
        raise TmdbError(f"TMDB 返回 {res.status_code}")

    data = res.json()
    _cache[key] = (now + (ttl if ttl is not None else TMDB_CACHE_TTL), data)
    return data


async def refresh_configuration(force: bool = False) -> str:
    """拉一次图片基础地址。TMDB 建议不要硬编码 CDN 域名，所以启动时刷一次。

    失败静默回落到配置里的 TMDB_IMAGE_BASE，不影响站点运行。
    """
    global _image_base, _image_base_at
    now = time.monotonic()
    if not force and _image_base_at and now - _image_base_at < 86400:
        return _image_base
    if not configured():
        return _image_base
    try:
        data = await _get("/configuration", {}, ttl=86400)
        base = (data.get("images") or {}).get("secure_base_url") or ""
        if base:
            _image_base = base.rstrip("/")
            _image_base_at = now
    except Exception:  # noqa: BLE001 - 配置拉取失败不该让站点起不来
        pass
    return _image_base


def _normalize(item: dict) -> dict:
    """把 TMDB 的原始条目压成后台够用的最小集合。"""
    release = item.get("release_date") or ""
    year = int(release[:4]) if release[:4].isdigit() else 0
    poster = item.get("poster_path") or ""
    return {
        "tmdb_id": item.get("id"),
        "title": item.get("title") or "",
        "original_title": item.get("original_title") or "",
        "year": year,
        "overview": item.get("overview") or "",
        "poster_path": poster,
        "backdrop_path": item.get("backdrop_path") or "",
        "poster_url": image_url(poster, "w342"),
        "poster_large_url": image_url(poster, "w780"),
        "backdrop_url": image_url(item.get("backdrop_path") or "", "w1280"),
        "tmdb_rating": round(float(item.get("vote_average") or 0), 1),
        "vote_count": int(item.get("vote_count") or 0),
        "popularity": round(float(item.get("popularity") or 0), 2),
        "genres": item.get("genres") or [],
        "genre_ids": item.get("genre_ids") or [],
    }


async def search_movies(query: str, year: int | None = None, page: int = 1) -> dict:
    """按片名搜索。返回 {results, page, total_pages, total_results}。"""
    if not configured():
        raise TmdbError("还没配置 TMDB_API_KEY，见 .env.example 里的说明")
    q = (query or "").strip()
    if not q:
        return {"results": [], "page": 1, "total_pages": 0, "total_results": 0}
    params: dict = {
        "query": q,
        "language": TMDB_LANGUAGE,
        "include_adult": "false",
        "page": max(1, min(int(page), 500)),
    }
    if year:
        params["year"] = int(year)
    data = await _get("/search/movie", params)
    return {
        "results": [_normalize(m) for m in data.get("results", [])],
        "page": data.get("page", 1),
        "total_pages": data.get("total_pages", 0),
        "total_results": data.get("total_results", 0),
    }


async def discover_horror(
    page: int = 1,
    sort_by: str = "popularity.desc",
    min_vote_count: int = 100,
    year_from: int | None = None,
    year_to: int | None = None,
) -> dict:
    """恐怖片片库浏览。用户要的是「所有沾边恐怖的内容」，这里就是入口。

    min_vote_count 是关键：没有它，前几页全是没人评分的垃圾条目。
    """
    if not configured():
        raise TmdbError("还没配置 TMDB_API_KEY，见 .env.example 里的说明")
    params: dict = {
        "language": TMDB_LANGUAGE,
        "with_genres": HORROR_GENRE_ID,
        "sort_by": sort_by,
        "include_adult": "false",
        "vote_count.gte": int(min_vote_count),
        "page": max(1, min(int(page), 500)),
    }
    if year_from:
        params["release_date.gte"] = f"{int(year_from)}-01-01"
    if year_to:
        params["release_date.lte"] = f"{int(year_to)}-12-31"
    data = await _get("/discover/movie", params)
    return {
        "results": [_normalize(m) for m in data.get("results", [])],
        "page": data.get("page", 1),
        "total_pages": data.get("total_pages", 0),
        "total_results": data.get("total_results", 0),
    }


async def movie_detail(tmdb_id: int) -> dict:
    """单部详情，含导演与类型名。用于导入时把字段一次填满。"""
    if not configured():
        raise TmdbError("还没配置 TMDB_API_KEY，见 .env.example 里的说明")
    data = await _get(
        f"/movie/{int(tmdb_id)}",
        {"language": TMDB_LANGUAGE, "append_to_response": "credits"},
        ttl=3600,
    )
    item = _normalize(data)
    # 导演从 credits 里挖，TMDB 主对象不直接给
    directors = [
        c.get("name", "")
        for c in ((data.get("credits") or {}).get("crew") or [])
        if c.get("job") == "Director"
    ]
    item["director"] = "、".join([d for d in directors if d][:3])
    countries = data.get("production_countries") or []
    item["country"] = " / ".join(
        [c.get("name", "") for c in countries if c.get("name")][:3]
    )
    item["runtime"] = int(data.get("runtime") or 0)
    item["tmdb_url"] = f"https://www.themoviedb.org/movie/{int(tmdb_id)}"
    return item
