"""把展示字与等宽字的 latin 分片下载到本地，生成 fonts.css。

部署后站点不再依赖 Google Fonts CDN（国内服务器访问不稳定）。
只取 latin 分片，两套字体合计通常不到 100KB。

用法：python deploy/fetch_fonts.py
"""
from __future__ import annotations

import re
import urllib.request
from pathlib import Path

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)

FAMILIES = {
    "Chakra Petch": [500, 600, 700],
    "JetBrains Mono": [400, 700],
}

ROOT = Path(__file__).resolve().parent.parent
FONT_DIR = ROOT / "static" / "fonts"
CSS_OUT = ROOT / "static" / "css" / "fonts.css"

# 只保留 latin（含基本拉丁与拉丁-1 补充），其余分片体积大且用不上
LATIN_MARK = "U+0000-00FF"


def slug(name: str) -> str:
    return name.lower().replace(" ", "-")


def fetch(url: str, binary: bool = False):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read()
    return data if binary else data.decode("utf-8")


def main() -> None:
    FONT_DIR.mkdir(parents=True, exist_ok=True)

    query = "&".join(
        f"family={name.replace(' ', '+')}:wght@{';'.join(str(w) for w in weights)}"
        for name, weights in FAMILIES.items()
    )
    css = fetch(f"https://fonts.googleapis.com/css2?{query}&display=swap")

    blocks = re.findall(r"/\*\s*([\w-]+)\s*\*/\s*(@font-face\s*\{[^}]*\})", css)
    out_lines = [
        "/* 自托管字体：由 deploy/fetch_fonts.py 生成，勿手改 */",
        "/* 展示字 Chakra Petch（未来感）+ 等宽 JetBrains Mono（标签与数字） */",
        "",
    ]
    count = 0
    for subset, block in blocks:
        if subset != "latin":
            continue
        fam = re.search(r"font-family:\s*'([^']+)'", block).group(1)
        weight = re.search(r"font-weight:\s*(\d+)", block).group(1)
        url = re.search(r"url\((https://[^)]+)\)", block).group(1)
        fname = f"{slug(fam)}-{weight}.woff2"
        target = FONT_DIR / fname
        if not target.exists():
            target.write_bytes(fetch(url, binary=True))
            print(f"下载 {fname}  {target.stat().st_size / 1024:.1f} KB")
        out_lines.append(
            "@font-face {\n"
            f"  font-family: '{fam}';\n"
            f"  font-style: normal;\n"
            f"  font-weight: {weight};\n"
            "  font-display: swap;\n"
            f"  src: url('../fonts/{fname}') format('woff2');\n"
            "  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC,\n"
            "                 U+2000-206F, U+2074, U+20AC, U+2122, U+2191;\n"
            "}"
        )
        out_lines.append("")
        count += 1

    CSS_OUT.write_text("\n".join(out_lines), encoding="utf-8")
    print(f"\n共 {count} 个字体文件，已生成 {CSS_OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
