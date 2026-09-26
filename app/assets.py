"""静态资源指纹（cache busting）。

nginx 给 css/js 设了 `expires 30d + immutable`（见 deploy/nginx.conf），
好处是回头客几乎零等待，代价是改了样式之后老访客一个月都拿不到新版。

解决办法：HTML 经后端返回时，把里面的 css/js/img 引用追加上 `?v=<内容哈希>`。
改了文件哈希就变，URL 变了浏览器自然去拉新的；没改的文件继续吃缓存。

HTML 源文件本身保持干净——直接双击打开、或者哪天换成纯静态托管，都还是正常的。
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

from .config import STATIC_DIR

# 只处理我们自己写的相对引用，外链（http/https/协议相对）一律不动。
# vendor/ 里是钉死的第三方库（Three.js 等），也纳入指纹，避免升级后浏览器拿旧缓存。
# data-wallpaper 是首页折叠屏的壁纸路径（写在 HTML 上，浏览器刷新后才会带新版本号）。
_ASSET_RE = re.compile(
    r'(?P<attr>(?:href|src|data-wallpaper)=")'
    r"(?P<path>(?:css|js|vendor|img)/[A-Za-z0-9._/\-]+\.(?:css|js|png|jpe?g|webp|avif))"
    r'(?P<tail>")'
)

# 路径 -> (mtime, size, hash)。按 mtime+size 判断是否要重算，省掉每次读全文
_FINGERPRINTS: dict[str, tuple[float, int, str]] = {}


def _fingerprint(rel_path: str) -> str:
    """返回 12 位内容哈希，文件不存在时回落成 0。"""
    file_path = STATIC_DIR / rel_path
    try:
        stat = file_path.stat()
    except OSError:
        return "0" * 12

    cached = _FINGERPRINTS.get(rel_path)
    if cached and cached[0] == stat.st_mtime and cached[1] == stat.st_size:
        return cached[2]

    digest = hashlib.sha256(file_path.read_bytes()).hexdigest()[:12]
    _FINGERPRINTS[rel_path] = (stat.st_mtime, stat.st_size, digest)
    return digest


def stamp(html: str) -> str:
    """给 HTML 里的 css/js 引用加上版本号查询串。"""

    def _replace(match: re.Match[str]) -> str:
        rel = match.group("path")
        # 已经带过 ?v= 的不重复加（防止某些部署流程二次处理）
        if "?" in rel:
            return match.group(0)
        return f'{match.group("attr")}{rel}?v={_fingerprint(rel)}{match.group("tail")}'

    return _ASSET_RE.sub(_replace, html)


def render_page(name: str) -> str | None:
    """读取 static 下的页面并注入版本号；文件不存在返回 None。"""
    file_path = STATIC_DIR / name
    try:
        raw = file_path.read_text(encoding="utf-8")
    except OSError:
        return None
    return stamp(raw)


def invalidate() -> None:
    """清空缓存，测试用。"""
    _FINGERPRINTS.clear()


def tracked_files() -> list[Path]:
    """当前被跟踪的资源文件，便于自检。"""
    return sorted((STATIC_DIR / p).resolve() for p in _FINGERPRINTS)
