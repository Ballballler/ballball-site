"""生成站点品牌图：分享卡 og-image.png、favicon.ico、apple-touch-icon.png。

用法（在项目根目录执行）：
    .venv/Scripts/python.exe deploy/make_brand_assets.py
    .venv/Scripts/python.exe deploy/make_brand_assets.py --title "张三的主页" --subtitle "一句话自我介绍"

脚本会先试着从本地跑着的服务（默认 http://127.0.0.1:8800）读 /api/profile，
拿到真实的名字和一句话身份；服务没开或加了 --title 就用命令行给的值。
换名字、换简介之后重跑一次，分享卡就跟着更新。

依赖：Pillow（只在生成图片时需要，服务器运行时不需要）
    .venv/Scripts/python.exe -m pip install pillow
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover - 缺依赖时给出明确指引
    sys.exit("缺少 Pillow：先跑 .venv/Scripts/python.exe -m pip install pillow")

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

# 站点配色，和 static/css/base.css 里的令牌保持一致
INK = (11, 18, 32)
INK_DEEP = (7, 11, 20)
PRIMARY = (0, 184, 212)
VIOLET = (124, 92, 255)
MINT = (0, 229, 176)
WHITE = (255, 255, 255)
SOFT = (170, 190, 214)

DEFAULT_TITLE = "Ballball 的主页"
DEFAULT_SUBTITLE = "在恐怖片里找灵感，在音乐里找节奏，在代码里把它们落地。"


# ---------------------------------------------------------------- 字体


def _font_candidates() -> list[tuple[str, str]]:
    """(用途, 字体文件路径)。按平台顺序尝试，找不到就跳过。"""
    win = "C:/Windows/Fonts"
    mac = "/System/Library/Fonts"
    linux = "/usr/share/fonts/truetype"
    return [
        ("display_bold", f"{win}/msyhbd.ttc"),
        ("display_bold", f"{mac}/PingFang.ttc"),
        ("display_bold", f"{linux}/wqy/wqy-zenhei.ttc"),
        ("display", f"{win}/msyh.ttc"),
        ("display", f"{mac}/PingFang.ttc"),
        ("display", f"{linux}/wqy/wqy-zenhei.ttc"),
        ("mono", f"{win}/consola.ttf"),
        ("mono", f"{mac}/Menlo.ttc"),
        ("mono", f"{linux}/dejavu/DejaVuSansMono.ttf"),
    ]


def load_fonts() -> dict[str, str]:
    """挑出每个用途第一个真实存在的字体。"""
    found: dict[str, str] = {}
    for role, path in _font_candidates():
        if role in found or not Path(path).exists():
            continue
        found[role] = path
    if "display" not in found or "display_bold" not in found:
        print("⚠️  没找到中文字体，标题可能渲染成方块。可手动指定字体路径后重试。")
    return found


def font(role: str, size: int, fonts: dict[str, str]) -> ImageFont.FreeTypeFont:
    path = fonts.get(role) or fonts.get("display")
    if not path:
        return ImageFont.load_default()
    return ImageFont.truetype(path, size)


# ---------------------------------------------------------------- 素材


def fetch_profile(base_url: str) -> tuple[str | None, str | None]:
    """从本地服务读真实的名字和一句话身份，读不到就返回 (None, None)。"""
    try:
        with urllib.request.urlopen(f"{base_url}/api/profile", timeout=2) as resp:
            data = json.load(resp)
        name = (data.get("name") or "").strip()
        tagline = (data.get("tagline") or "").strip()
        return (name or None), (tagline or None)
    except Exception:
        return None, None


def wrap(draw: ImageDraw.ImageDraw, text: str, fnt, max_width: int) -> list[str]:
    """按像素宽度折行，中英文混排都按字符切。"""
    lines: list[str] = []
    current = ""
    for ch in text:
        trial = current + ch
        if draw.textlength(trial, font=fnt) > max_width and current:
            lines.append(current)
            current = ch
        else:
            current = trial
    if current:
        lines.append(current)
    return lines


def draw_backdrop(img: Image.Image) -> None:
    """深空底 + 透视网格地平线，和首页 aurora 的氛围对齐。"""
    w, h = img.size
    px = img.load()

    # 对角渐变：右上偏青、左下更沉
    for y in range(h):
        for x in range(0, w, 2):
            t = (x / w) * 0.5 + (y / h) * 0.5
            r = int(INK_DEEP[0] + (INK[0] - INK_DEEP[0]) * t)
            g = int(INK_DEEP[1] + (INK[1] - INK_DEEP[1]) * t)
            b = int(INK_DEEP[2] + (30 - INK_DEEP[2]) * t)
            for dx in range(2):
                if x + dx < w:
                    px[x + dx, y] = (r, g, b)

    draw = ImageDraw.Draw(img)
    horizon = int(h * 0.72)
    # 地平线以下画横线，越远越密，做出透视感
    step = 6
    i = 0
    y = horizon
    while y < h:
        alpha = int(70 * (1 - (y - horizon) / (h - horizon)))
        draw.line([(0, y), (w, y)], fill=(PRIMARY[0], PRIMARY[1], PRIMARY[2]), width=1)
        y += max(2, int(step))
        step *= 1.28
        i += 1
        if i > 40:
            break
    # 竖线从消失点发散
    vanish_x = w // 2
    for k in range(-12, 13):
        x_bottom = vanish_x + k * (w // 10)
        draw.line(
            [(vanish_x, horizon), (x_bottom, h)],
            fill=(PRIMARY[0], PRIMARY[1], PRIMARY[2]),
            width=1,
        )
    # 地平线本身
    draw.line([(0, horizon), (w, horizon)], fill=(PRIMARY[0], PRIMARY[1], PRIMARY[2]), width=2)


def make_og_image(title: str, subtitle: str, fonts: dict[str, str]) -> Image.Image:
    w, h = 1200, 630
    img = Image.new("RGB", (w, h), INK)
    draw_backdrop(img)
    draw = ImageDraw.Draw(img)

    f_label = font("mono", 26, fonts)
    f_title = font("display_bold", 78, fonts)
    f_sub = font("display", 34, fonts)

    # 顶部小标签
    draw.text((72, 74), "B A L L B A L L   //   P E R S O N A L   S I T E", font=f_label, fill=PRIMARY)

    # 主标题（过长自动折行，最多两行）
    title_lines = wrap(draw, title, f_title, w - 200)[:2]
    y = 210
    for line in title_lines:
        draw.text((72, y), line, font=f_title, fill=WHITE)
        y += 96

    # 副标题
    y += 8
    for line in wrap(draw, subtitle, f_sub, w - 240)[:3]:
        draw.text((74, y), line, font=f_sub, fill=SOFT)
        y += 52

    # 底部品牌三色条
    bar_y = h - 46
    draw.rectangle([(72, bar_y), (232, bar_y + 10)], fill=PRIMARY)
    draw.rectangle([(244, bar_y), (404, bar_y + 10)], fill=VIOLET)
    draw.rectangle([(416, bar_y), (576, bar_y + 10)], fill=MINT)

    # 右下角轨道环，呼应 favicon
    cx, cy = w - 150, h - 150
    draw.ellipse([cx - 92, cy - 38, cx + 92, cy + 38], outline=PRIMARY, width=4)
    draw.ellipse([cx - 60, cy - 60, cx + 60, cy + 60], outline=VIOLET, width=2)
    draw.ellipse([cx + 60, cy - 84, cx + 78, cy - 66], fill=MINT)

    return img


def make_mark(size: int, fonts: dict[str, str]) -> Image.Image:
    """站点标记：深底 + 轨道环 + B。用于 favicon.ico 与 apple-touch-icon。"""
    img = Image.new("RGB", (size, size), INK)
    draw = ImageDraw.Draw(img)
    s = size / 64

    # 倾斜轨道：PIL 画不了旋转椭圆，用多边形近似
    import math

    cx, cy, rx, ry = 32 * s, 32 * s, 25 * s, 10 * s
    angle = math.radians(-22)
    pts = []
    for deg in range(0, 360, 6):
        t = math.radians(deg)
        x = rx * math.cos(t)
        y = ry * math.sin(t)
        pts.append(
            (cx + x * math.cos(angle) - y * math.sin(angle),
             cy + x * math.sin(angle) + y * math.cos(angle))
        )
    draw.polygon(pts, outline=PRIMARY)
    draw.ellipse([cx - 16.5 * s, cy - 16.5 * s, cx + 16.5 * s, cy + 16.5 * s], outline=PRIMARY)

    f = font("display_bold", int(30 * s), fonts)
    draw.text((cx, cy), "B", font=f, fill=WHITE, anchor="mm")

    draw.ellipse(
        [55 * s - 3.4 * s, 24 * s - 3.4 * s, 55 * s + 3.4 * s, 24 * s + 3.4 * s],
        fill=MINT,
    )
    return img


# ---------------------------------------------------------------- 入口


def main() -> int:
    parser = argparse.ArgumentParser(description="生成站点品牌图")
    parser.add_argument("--title", default=None, help="分享卡主标题")
    parser.add_argument("--subtitle", default=None, help="分享卡副标题")
    parser.add_argument(
        "--site", default="http://127.0.0.1:8800", help="读 profile 用的站点地址"
    )
    parser.add_argument("--no-fetch", action="store_true", help="不读服务，直接用默认值")
    args = parser.parse_args()

    fonts = load_fonts()

    title, subtitle = args.title, args.subtitle
    if title is None or subtitle is None:
        api_title, api_sub = (None, None) if args.no_fetch else fetch_profile(args.site)
        title = title or (f"{api_title} 的主页" if api_title else DEFAULT_TITLE)
        subtitle = subtitle or (api_sub or DEFAULT_SUBTITLE)

    STATIC_DIR.mkdir(parents=True, exist_ok=True)

    og = make_og_image(title, subtitle, fonts)
    og_path = STATIC_DIR / "og-image.png"
    og.save(og_path, "PNG", optimize=True)

    ico_path = STATIC_DIR / "favicon.ico"
    make_mark(64, fonts).save(
        ico_path, "ICO", sizes=[(16, 16), (32, 32), (48, 48)]
    )

    touch_path = STATIC_DIR / "apple-touch-icon.png"
    make_mark(180, fonts).save(touch_path, "PNG", optimize=True)

    for path in (og_path, ico_path, touch_path):
        print(f"✅ {path.relative_to(BASE_DIR)}  {path.stat().st_size / 1024:.1f} KB")
    print(f"\n标题：{title}\n副标题：{subtitle}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
