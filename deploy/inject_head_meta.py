"""把各页 <head> 里的品牌图标与分享信息统一注入。

手工在 5 个 HTML 里各写一遍 og 标签，改一次要改五处，迟早写歪一处。
这里集中生成，跑一次全站对齐。幂等：重复执行只会覆盖同一段。

用法：.venv/Scripts/python.exe deploy/inject_head_meta.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

MARKER_START = "<!-- brand:start（由 deploy/inject_head_meta.py 生成，勿手改）-->"
MARKER_END = "<!-- brand:end -->"

# 与 favicon 一起放在 static 下，部署时整个 static 目录就是站点根
ICON_LINKS = """    <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
    <link rel="icon" href="/favicon.ico" sizes="32x32" />
    <link rel="apple-touch-icon" href="/apple-touch-icon.png" />"""


def block(title: str, description: str, path: str, og_type: str = "website") -> str:
    return (
        f"{MARKER_START}\n"
        f'{ICON_LINKS}\n'
        f'    <meta property="og:type" content="{og_type}" />\n'
        f'    <meta property="og:site_name" content="Ballball 的主页" />\n'
        f'    <meta property="og:title" content="{title}" />\n'
        f'    <meta property="og:description" content="{description}" />\n'
        f'    <meta property="og:url" content="{path}" />\n'
        f'    <meta property="og:image" content="/og-image.png" />\n'
        f'    <meta property="og:image:width" content="1200" />\n'
        f'    <meta property="og:image:height" content="630" />\n'
        f'    <meta name="twitter:card" content="summary_large_image" />\n'
        f"    {MARKER_END}"
    )


PAGES: dict[str, dict[str, str]] = {
    "index.html": {
        "title": "Ballball 的主页",
        "description": "在恐怖片里找灵感，在音乐里找节奏，在代码里把它们落地。",
        "path": "/",
    },
    "movies.html": {
        "title": "恐怖电影档案 · Ballball 的主页",
        "description": "一部一部看过来，每部都写下自己的评价：评分、恐怖强度、值不值得看。",
        "path": "/movies.html",
    },
    "works.html": {
        "title": "音乐构思 · Ballball 的主页",
        "description": "还没做完的音乐：BPM、调性、完成度，以及每首背后的构思笔记。",
        "path": "/works.html",
    },
    "resume.html": {
        "title": "简历 · Ballball 的主页",
        "description": "完整的简历：自我介绍、技能三维分布、教育与工作经历时间轴，可直接打印。",
        "path": "/resume.html",
    },
}


def strip_old(html: str) -> str:
    """去掉上一次注入的整段、旧的 emoji favicon 和零散的 og 标签。"""
    html = re.sub(
        re.escape(MARKER_START) + r".*?" + re.escape(MARKER_END) + r"\s*",
        "",
        html,
        flags=re.S,
    )
    # 旧的 emoji data-URI favicon。它可能写成一行，也可能 href 单独占一行
    html = re.sub(
        r'[ \t]*<link\s+rel="icon"\s+href="data:[^"]*?"\s*/>\n',
        "",
        html,
        flags=re.S,
    )
    html = re.sub(
        r'[ \t]*<link\s+rel="icon"\s*\n\s*href="data:[^"]*?"\s*/>\n',
        "",
        html,
        flags=re.S,
    )
    html = re.sub(r'[ \t]*<link rel="icon" href="/favicon\.(svg|ico)"[^>]*/>\n', "", html)
    html = re.sub(r'[ \t]*<link rel="apple-touch-icon"[^>]*/>\n', "", html)
    # 旧的 og / twitter 标签（第一轮在几个页面里手写过）
    html = re.sub(r'[ \t]*<meta property="og:[^>]*>\n', "", html)
    html = re.sub(r'[ \t]*<meta name="twitter:[^>]*>\n', "", html)
    return html


def inject(name: str, meta: dict[str, str]) -> bool:
    path = STATIC_DIR / name
    if not path.exists():
        print(f"跳过 {name}：文件不存在")
        return False

    html = path.read_text(encoding="utf-8")
    html = strip_old(html)

    # <meta name="theme-color"> 之后插入，那里是 head 里所有 meta 的末尾。
    # 收尾的 [ \t]* 不能换成 \s*：theme-color 行尾本身就是换行，多吃了会把下一行顶到行首。
    anchor = re.search(r'[ \t]*<meta name="theme-color"[^>]*>[ \t]*\n', html)
    if anchor:
        insert_at = anchor.end()
        indent_after = False
    else:
        m = re.search(r"[ \t]*<title>.*?</title>\n", html)
        if not m:
            print(f"跳过 {name}：找不到锚点")
            return False
        insert_at = m.end()
        indent_after = True

    payload = block(meta["title"], meta["description"], meta["path"]) + "\n"
    html = html[:insert_at] + payload + html[insert_at:]
    # 收拾掉可能出现的连续空行
    html = re.sub(r"\n{3,}", "\n\n", html)
    if indent_after:
        # 落在 <title> 后面时，注入段首行会贴到上一行行尾，补缩进
        html = html.replace("-->\n<", "-->\n    <")
    path.write_text(html, encoding="utf-8")
    print(f"✅ {name}")
    return True


def ensure_noindex() -> bool:
    """后台页加 noindex。nginx 里也配了，但换个托管方式就只有这层兜底了。"""
    path = STATIC_DIR / "admin.html"
    if not path.exists():
        print("跳过 admin.html：文件不存在")
        return False
    html = path.read_text(encoding="utf-8")
    if 'name="robots"' in html:
        print("✅ admin.html（已有 noindex）")
        return True
    anchor = re.search(r'[ \t]*<meta name="theme-color"[^>]*>\n', html)
    if not anchor:
        return False
    payload = '    <meta name="robots" content="noindex, nofollow" />\n'
    html = html[: anchor.end()] + payload + html[anchor.end() :]
    path.write_text(html, encoding="utf-8")
    print("✅ admin.html（已加 noindex）")
    return True


def main() -> int:
    if not (STATIC_DIR / "og-image.png").exists():
        print("⚠️  还没生成 og-image.png，先跑 deploy/make_brand_assets.py")
    done = sum(1 for name, meta in PAGES.items() if inject(name, meta))
    ensure_noindex()
    print(f"\n共处理 {done} 个前台页面")
    return 0 if done else 1


if __name__ == "__main__":
    raise SystemExit(main())
