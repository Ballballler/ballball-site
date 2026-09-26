"""把站点导出成一份**纯静态文件**，用来发到 GitHub Pages。

为什么需要它：GitHub Pages 只会分发静态文件，不支持运行 Python，
所以 FastAPI / SQLite / 后台登录在那儿全都跑不起来。这个脚本把数据库里的内容
拍成一份快照内联进 HTML，前台照旧能渲染，只是变成只读。

三个刻意的设计：

1. **数据用 TestClient 直接调自己的接口取**（不是手写 SQL）。
   这样静态快照和动态接口返回的数据结构天然一致，不会出现
   「本地好使、Pages 上少了字段」这种事。

2. **复用 app/assets.py 的指纹**。Pages 会给静态资源上缓存，
   没有 `?v=<hash>` 的话改了样式老访客还拿着旧文件。

3. **不导出 admin.html**。Pages 上没有后端，后台登录页只会报错，
   不如不出现。

用法：
    .venv/Scripts/python.exe tools/export_static.py
    .venv/Scripts/python.exe tools/export_static.py --out dist --site-url https://x.github.io/y
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from app import assets  # noqa: E402
from app.main import app  # noqa: E402

# 需要导出的公开页面。admin.html 刻意不在列表里。
PAGES = ["index.html", "movies.html", "works.html", "resume.html"]

# 前台会请求的 GET 接口（见 static/js 里的 API.get 调用清单）
SIMPLE_ENDPOINTS = [
    "/api/profile",
    "/api/movies",
    "/api/works",
    "/api/resume",
    "/api/categories?kind=movie_genre",
    "/api/categories?kind=work_type",
]

# 每条共用一份 section 配置
PAGE_SECTIONS = ["index", "resume", "movies", "works"]

# 评论的两种归属，和前端 createComments 的 targetType 对应
COMMENT_TARGETS = [("movie", "movies"), ("work", "works")]


def build_snapshot(client: TestClient) -> dict:
    """把前台需要的全部数据拉成一份字典。"""
    snap: dict = {}

    for path in SIMPLE_ENDPOINTS:
        snap[path] = _get_json(client, path)

    for page in PAGE_SECTIONS:
        path = f"/api/page-sections/{page}"
        snap[path] = _get_json(client, path)

    # 评论没有「全量」接口，只能按条目拉，这里合并成一整份，
    # 前端 common.js 的 staticLookup 会按 target_type / target_id 现场筛。
    comments: list = []
    for target_type, list_key in COMMENT_TARGETS:
        for item in snap[f"/api/{list_key}"] or []:
            item_id = item.get("id")
            if item_id is None:
                continue
            path = f"/api/comments?target_type={target_type}&target_id={item_id}"
            rows = _get_json(client, path) or []
            comments.extend(rows)
    # 按时间倒序，和后台列表一致
    comments.sort(key=lambda c: c.get("created_at") or "", reverse=True)
    snap["/api/comments"] = comments

    return snap


def _get_json(client: TestClient, path: str):
    res = client.get(path)
    if res.status_code != 200:
        raise SystemExit(f"接口 {path} 返回 {res.status_code}，导出中止")
    return res.json()


def _inline_script(var: str, payload: str) -> str:
    """内联 JSON。必须转义 </script>，否则正文里出现这四个字符就会提前截断脚本。"""
    safe = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace(
        "</", "<\\/"
    )
    return f"<script>window.{var}={safe}</script>"


def giscus_config() -> dict:
    """Giscus 配置。GitHub Actions 里 GITHUB_REPOSITORY 会自动填成 owner/repo。"""
    return {
        "repo": os.getenv("GISCUS_REPO") or os.getenv("GITHUB_REPOSITORY") or "",
        "repoId": os.getenv("GISCUS_REPO_ID", ""),
        "category": os.getenv("GISCUS_CATEGORY", "Announcements"),
        "categoryId": os.getenv("GISCUS_CATEGORY_ID", ""),
        "theme": os.getenv("GISCUS_THEME", "transparent_dark"),
    }


def render_pages(dist: Path, snap: dict, site_url: str) -> list[str]:
    written = []
    giscus = giscus_config()

    for name in PAGES:
        src = assets.STATIC_DIR / name
        if not src.exists():
            print(f"  ! 跳过不存在的页面 {name}")
            continue
        html = src.read_text(encoding="utf-8")

        payload = _inline_script("__SITE_DATA__", snap)
        if giscus["repo"]:
            payload += "\n" + _inline_script("__GISCUS__", giscus)

        # 放在 </head> 前，保证业务脚本执行时数据已经就位
        if "</head>" in html:
            html = html.replace("</head>", f"{payload}\n</head>", 1)
        else:
            html = html + payload

        # 指纹：让改过的 css/js 换 URL，绕开 Pages 的缓存
        html = assets.stamp(html)

        (dist / name).write_text(html, encoding="utf-8")
        written.append(name)

    # 404 页：Pages 上访问不存在的路径会用到
    _write_404(dist, site_url)
    return written


def _write_404(dist: Path, site_url: str) -> None:
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>页面不存在 · Ballball 的主页</title>
<link rel="stylesheet" href="css/orbit.css">
<style>
  body {{ min-height: 100dvh; display: grid; place-items: center; text-align: center; padding: 24px; }}
  .nf__code {{ font-family: var(--mono, monospace); font-size: 64px; color: var(--mint, #8fb8a8); }}
  .nf__links {{ display: flex; gap: 14px; justify-content: center; margin-top: 22px; flex-wrap: wrap; }}
</style>
</head>
<body>
<main class="shell">
  <div class="nf__code">404</div>
  <h1 style="margin:10px 0 8px">这个页面不在轨道上</h1>
  <p style="color:var(--muted,#8b95a5)">链接可能已经改了，或者从来没存在过。</p>
  <div class="nf__links">
    <a class="btn btn--primary" href="{site_url}/">回到首页</a>
    <a class="btn" href="{site_url}/movies.html">恐怖电影</a>
    <a class="btn" href="{site_url}/works.html">音乐构思</a>
  </div>
</main>
</body>
</html>
"""
    (dist / "404.html").write_text(html, encoding="utf-8")


def copy_assets(dist: Path) -> int:
    """搬 css / js / vendor / fonts / img / uploads 等静态资源。HTML 单独处理，不在这里搬。"""
    copied = 0
    for item in sorted(assets.STATIC_DIR.iterdir()):
        if item.is_file() and item.suffix == ".html":
            continue
        dest = dist / item.name
        if item.is_dir():
            shutil.copytree(item, dest, dirs_exist_ok=True)
            copied += sum(1 for _ in dest.rglob("*") if _.is_file())
        else:
            shutil.copy2(item, dest)
            copied += 1
    return copied


def write_seo(dist: Path, site_url: str, pages: list[str]) -> None:
    base = site_url.rstrip("/")
    urls = "\n".join(
        f"  <url><loc>{base}/{p if p != 'index.html' else ''}</loc></url>" for p in pages
    )
    (dist / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{urls}\n"
        "</urlset>\n",
        encoding="utf-8",
    )
    (dist / "robots.txt").write_text(
        "User-agent: *\nAllow: /\n\nSitemap: " + base + "/sitemap.xml\n",
        encoding="utf-8",
    )
    # Pages 用自定义域时靠这个文件跳过 Jekyll 处理（下划线开头的目录会被吞）
    (dist / ".nojekyll").write_text("", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="导出静态站点供 GitHub Pages 使用")
    parser.add_argument("--out", default="dist", help="输出目录，默认 dist")
    parser.add_argument(
        "--site-url",
        default=os.getenv("SITE_URL", "https://ballballler.github.io/ballball-site"),
        help="线上地址，用于 sitemap 与 robots",
    )
    args = parser.parse_args()

    dist = ROOT / args.out
    if dist.exists():
        shutil.rmtree(dist)
    dist.mkdir(parents=True)

    print(f"导出目标：{dist}")
    client = TestClient(app)

    snap = build_snapshot(client)
    print(
        f"  数据快照：{len(snap)} 个键，"
        f"电影 {len(snap.get('/api/movies') or [])} 部 / "
        f"作品 {len(snap.get('/api/works') or [])} 个 / "
        f"评论 {len(snap.get('/api/comments') or [])} 条"
    )

    files = copy_assets(dist)
    print(f"  静态资源：{files} 个文件")

    pages = render_pages(dist, snap, args.site_url)
    print(f"  页面：{', '.join(pages)} + 404.html")

    write_seo(dist, args.site_url, pages)
    total = sum(1 for _ in dist.rglob("*") if _.is_file())
    print(f"\n完成：{dist}（共 {total} 个文件）")
    print("接下来：把 dist/ 整个目录推到 gh-pages 分支，或用 GitHub Actions 自动发布。")


if __name__ == "__main__":
    main()
