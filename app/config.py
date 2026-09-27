"""全局配置：路径、密钥、管理员口令、数据库连接串。

所有敏感项都优先读环境变量，缺失时回落到 .env 文件；
首次运行会自动生成 SECRET_KEY 并持久化，避免重启后登录态全部失效。
"""
from __future__ import annotations

import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
DATA_DIR = Path(os.getenv("DATA_DIR", str(BASE_DIR / "data")))
DATA_DIR.mkdir(parents=True, exist_ok=True)

ENV_FILE = BASE_DIR / ".env"


def _load_env_file() -> None:
    """极简 .env 解析，避免为一个文件引入额外依赖。

    只做 setdefault：真正的环境变量（systemd / docker 注入）优先级更高。
    """
    if not ENV_FILE.exists():
        return
    for raw in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_env_file()


def _persist(key: str, value: str) -> None:
    """把生成出来的配置写回 .env，保证跨重启稳定。"""
    lines: list[str] = []
    if ENV_FILE.exists():
        lines = ENV_FILE.read_text(encoding="utf-8").splitlines()
    for idx, line in enumerate(lines):
        if line.strip().startswith(f"{key}="):
            lines[idx] = f"{key}={value}"
            break
    else:
        lines.append(f"{key}={value}")
    ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _ensure_secret_key() -> str:
    key = os.getenv("SECRET_KEY", "").strip()
    if not key:
        key = secrets.token_urlsafe(48)
        os.environ["SECRET_KEY"] = key
        _persist("SECRET_KEY", key)
    return key


# 用于签名管理员会话 Cookie，绝不可外泄
SECRET_KEY: str = _ensure_secret_key()

# 管理员口令。默认值仅供本地开发，生产环境必须通过环境变量覆盖。
ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin12345")
# 注意：别用「环境变量在不在」判断有没有换过口令 —— 口令可以在后台改，
# 改完写进 data/admin.json。真正的判断见 security.using_default_password()。

# 会话有效期
SESSION_TTL_SECONDS: int = int(os.getenv("SESSION_TTL_SECONDS", "43200"))  # 12 小时
SESSION_COOKIE_NAME: str = "bb_admin_session"

# 数据目录同时存放 SQLite 文件
DATABASE_URL: str = os.getenv(
    "DATABASE_URL", f"sqlite:///{(DATA_DIR / 'site.db').as_posix()}"
)

# 后台上传的图片存放位置（在 static 下，nginx 会直接命中）
UPLOAD_DIR: Path = STATIC_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 单张图片上限（字节）。nginx 侧 client_max_body_size 是 20m，这里收紧到 8MB
MAX_UPLOAD_BYTES: int = int(os.getenv("MAX_UPLOAD_BYTES", str(8 * 1024 * 1024)))
# 故意不放 .svg：SVG 能内嵌脚本，直接访问文件 URL 就是在同源下执行，等于存储型 XSS。
# 图标之类的静态资源我们自己写，不走上传通道。
ALLOWED_IMAGE_EXT = (".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif")

# 音频：音乐作品要能在站内直接播放并下载，所以必须收文件。
# 一首 4 分钟的 mp3（320kbps）约 9MB，30MB 上限足够放成品与 demo。
ALLOWED_AUDIO_EXT = (".mp3", ".wav", ".ogg", ".oga", ".m4a", ".flac", ".aac")
MAX_AUDIO_BYTES: int = int(os.getenv("MAX_AUDIO_BYTES", str(30 * 1024 * 1024)))

# 站点对外地址，用于 sitemap 与 og:image 的绝对 URL。
# 部署后务必设成 https://你的域名，否则搜索引擎收录的是 localhost。
SITE_URL: str = os.getenv("SITE_URL", "http://127.0.0.1:8800").rstrip("/")

# ------------------------- TMDB（电影元数据） -------------------------
# 关键设计：只存 TMDB 的图片相对路径，渲染时拼它的 CDN 域名。
# 本地因此不落任何一张海报，磁盘占用为 0。
# 免费 key 在 https://www.themoviedb.org/settings/api 申请（个人用途免费）。
TMDB_API_KEY: str = os.getenv("TMDB_API_KEY", "").strip()
TMDB_LANGUAGE: str = os.getenv("TMDB_LANGUAGE", "zh-CN").strip() or "zh-CN"
# 图片基础地址由 /3/configuration 下发并缓存，这里只是兜底
TMDB_IMAGE_BASE: str = os.getenv("TMDB_IMAGE_BASE", "https://image.tmdb.org/t/p").rstrip("/")
# 元数据缓存时长（秒）。TMDB 明确允许且鼓励缓存，能大幅省请求额度。
TMDB_CACHE_TTL: int = int(os.getenv("TMDB_CACHE_TTL", "600"))

APP_ENV: str = os.getenv("APP_ENV", "dev")
