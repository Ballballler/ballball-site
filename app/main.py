"""FastAPI 应用入口。"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from .assets import render_page
from .config import ADMIN_PASSWORD, APP_ENV, SITE_URL, STATIC_DIR
from .database import Base, engine, ensure_extra_columns, SessionLocal
from .models import Movie, Work
from .routers import admin, public
from .seed import seed_if_empty
from . import tmdb
from .security import using_default_password

app = FastAPI(
    title="Ballball 的主页",
    description="个人主页 + 恐怖电影档案 + 音乐构思",
    version="1.1.0",
    # 生产环境关闭交互式文档，减少暴露面
    docs_url=None if APP_ENV == "production" else "/api/docs",
    redoc_url=None,
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    resp = await call_next(request)
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    # 页面不缓存：改版后访客刷新就能拿到新 HTML（里面的资源指纹也跟着变）
    ctype = resp.headers.get("content-type", "")
    if ctype.startswith("text/html"):
        resp.headers.setdefault("Cache-Control", "no-cache")
    return resp


@app.on_event("startup")
async def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    # create_all 只建新表，后加的列靠这里补（幂等）
    added = ensure_extra_columns()
    if added:
        print(f"[数据库] 已补齐列：{', '.join(added)}")
    seed_if_empty()

    # 图片 CDN 地址由 TMDB 下发，不硬编码。拉不到就用兜底值，不影响启动。
    if tmdb.configured():
        base = await tmdb.refresh_configuration()
        print(f"[TMDB] 已接入，图片地址 {base}")
    else:
        print("[TMDB] 未配置 TMDB_API_KEY，后台的「从 TMDB 导入」暂不可用（手动建档不受影响）")

    if using_default_password(ADMIN_PASSWORD):
        print(
            "\n[安全提示] 当前使用的是默认管理员口令（admin12345）。\n"
            "          部署前请在 .env 中设置 ADMIN_PASSWORD，或登录后台后修改口令。\n"
        )


# API 路由必须先注册，之后再挂载静态目录，否则 /api/* 会被静态文件服务吞掉
app.include_router(public.router)
app.include_router(admin.router)


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}


# ---------------------------------------------------------------- 页面
# HTML 走这里而不是静态挂载：返回时给 css/js 引用加上内容指纹，
# 这样 nginx 的 30 天 immutable 缓存和「改完立刻生效」可以同时成立。

_PAGES = ("index.html", "movies.html", "works.html", "resume.html", "admin.html")


def _page(name: str) -> Response:
    html = render_page(name)
    if html is None:
        return JSONResponse(status_code=404, content={"detail": "页面不存在"})
    return HTMLResponse(html)


@app.get("/", include_in_schema=False)
def index_page() -> Response:
    return _page("index.html")


@app.get("/admin", include_in_schema=False)
def admin_page() -> Response:
    return _page("admin.html")


@app.get("/{name}.html", include_in_schema=False)
def html_page(name: str) -> Response:
    if f"{name}.html" not in _PAGES:
        return _page("index.html")
    return _page(f"{name}.html")


# ------------------------------------------------------- 站点元数据


@app.get("/robots.txt", include_in_schema=False)
def robots() -> Response:
    """后台与接口一律不进搜索引擎；sitemap 指到绝对地址。"""
    body = (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /admin\n"
        "Disallow: /admin.html\n"
        "Disallow: /api/\n"
        "\n"
        f"Sitemap: {SITE_URL}/sitemap.xml\n"
    )
    return Response(body, media_type="text/plain; charset=utf-8")


@app.get("/sitemap.xml", include_in_schema=False)
def sitemap() -> Response:
    """从数据库实际内容生成，新增电影/作品会自动出现在里面。"""
    with SessionLocal() as db:
        movies = db.query(Movie.id, Movie.updated_at).all()
        works = db.query(Work.id, Work.updated_at).all()

    today = datetime.now(timezone.utc).date().isoformat()
    urls = [
        (f"{SITE_URL}/", "1.0", today),
        (f"{SITE_URL}/resume.html", "0.8", today),
        (f"{SITE_URL}/movies.html", "0.9", today),
        (f"{SITE_URL}/works.html", "0.9", today),
    ]
    for mid, updated in movies:
        # 电影详情没有独立页面，深链 #movie-<id> 挂在主列表页上
        last = (updated or datetime.now(timezone.utc)).date().isoformat()
        urls.append((f"{SITE_URL}/movies.html#movie-{mid}", "0.6", last))
    for wid, updated in works:
        last = (updated or datetime.now(timezone.utc)).date().isoformat()
        urls.append((f"{SITE_URL}/works.html#work-{wid}", "0.6", last))

    items = "\n".join(
        f"  <url><loc>{loc}</loc><priority>{pri}</priority>"
        f"<lastmod>{last}</lastmod></url>"
        for loc, pri, last in urls
    )
    body = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{items}\n"
        "</urlset>\n"
    )
    return Response(body, media_type="application/xml; charset=utf-8")


@app.exception_handler(404)
async def not_found(request: Request, exc):  # noqa: ANN001
    if request.url.path.startswith("/api/"):
        return JSONResponse(status_code=404, content={"detail": "接口不存在"})
    page = _page("index.html")
    page.status_code = 404
    return page


app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")


def create_app() -> FastAPI:
    """供 gunicorn / 测试使用。"""
    Base.metadata.create_all(bind=engine)
    return app
