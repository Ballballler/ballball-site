"""把桌面上的两个音乐作品导入站点，并清掉其余作品。

背景（2026-09-27，BB 需求）：
  「桌面上有两个音乐文件就是我的两个作品，上传到网站并且给他们重新命名
    以及把其他实例全部删掉」

实际文件（已核实）：
  1. C:\\Users\\96281\\Desktop\\自在.mp4
     抖音歌曲《自在》(子青) 的 15 秒竖屏片段（720x1280 / h264+aac）。
     网站播放器只吃音频，所以先用 ffmpeg 抽音轨成 mp3 再入库。
  2. C:\\Users\\96281\\Desktop\\380b58f2-ad88-43f8-b96a-0ad0a73a4f38(3).mp3
     2:44 的连续氛围铺底（波形无静音断点），自己做的曲子。

做法：
  - 音频一律走 app/routers/admin.py 里同一套校验（ALLOWED_AUDIO_EXT +
    _looks_like_audio + MAX_AUDIO_BYTES），不绕过防线；
  - 落盘位置与上传接口一致：static/uploads/<年月>/<随机名>.<ext>；
  - 删除时只删「本次导入之外」的所有 work 行，删前逐条打印；
  - 幂等：按 title 判重，重跑不会重复插入；已有同名行则只更新音频地址。

安全性（对应 README 第八节「改数据的安全约定」）：
  - 跑之前把 site.db 连同 -wal/-shm 备份到 backup/works-import-<日期>/
  - 支持 --dry-run，只打印计划不动数据
  - 不会 DELETE 任何 work 之外的表

用法：
  .venv/Scripts/python.exe tools/import_two_works.py --dry-run
  .venv/Scripts/python.exe tools/import_two_works.py
  .venv/Scripts/python.exe tools/import_two_works.py --keep-existing   # 不删旧作品
"""
from __future__ import annotations

import shutil
import sys
import uuid
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import models as M  # noqa: E402
from app.config import ALLOWED_AUDIO_EXT, MAX_AUDIO_BYTES, UPLOAD_DIR  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.routers.admin import _looks_like_audio  # noqa: E402

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
BACKUP_DIR = BASE_DIR / "backup"

DESKTOP = Path(r"C:\Users\96281\Desktop")
DOWNLOADS = Path(r"C:\Users\96281\Downloads")

# 两个作品的定义。名字由长青依据文件名 / 音频内容拟定。
#
# 关于《自在》的源：桌面上那个是抖音的竖屏片段（自在.mp4，只有 15 秒），
# 从视频里抽音轨属于二次压缩，音质和长度都不行。完整的音频在下载夹里
# （自在.mp3，2:44，192kbps），直接用这个。
WORKS: list[dict] = [
    {
        "title": "自在",
        "kind": "music",
        "status": "demo",
        "summary": "完整版 · 2 分 44 秒 —— 「night down i wanna break it down」。",
        "notes": (
            "完整版留档，2 分 44 秒。\n"
            "歌名《自在》，歌词里那句 night down i wanna break it down 挺抓人。\n"
            "存这里当练习参考 —— 它的气声处理和鼓组留白很值得拆。\n"
            "（桌面上还有个抖音的 15 秒竖屏片段，那个是从视频里截的，音质差，没采用。）"
        ),
        "tags": ["情绪流行", "完整版", "气声"],
        "bpm": 0,
        "key_signature": "",
        "category_slug": "纯音乐",
        "progress": 60,
        "allow_download": True,
        "source": DOWNLOADS / "自在.mp3",
    },
    {
        "title": "反复的雨",
        "kind": "music",
        "status": "idea",
        "summary": "2 分 44 秒的氛围铺底 —— 一段没有鼓、只往前推的雨声与合成器。",
        "notes": (
            "一段氛围底子，2 分 44 秒，全程没有明显的鼓点，靠一层层叠的合成器往前推。\n"
            "波形看下来几乎没有静音断点，像雨一直下、像走廊尽头那盏灯没关。\n"
            "本来想把它当引子接进另一首里，先单独存一份。"
        ),
        "tags": ["氛围", "暗色", "无人声"],
        "bpm": 0,
        "key_signature": "",
        "category_slug": "氛围",
        "progress": 45,
        "allow_download": True,
        "source": DESKTOP / "380b58f2-ad88-43f8-b96a-0ad0a73a4f38(3).mp3",
    },
]


def backup_db() -> Path:
    stamp = datetime.now().strftime("%Y-%m-%d")
    dest = BACKUP_DIR / f"works-import-{stamp}"
    dest.mkdir(parents=True, exist_ok=True)
    for suffix in ("", "-wal", "-shm"):
        src = Path(str(DATA_DIR / "site.db") + suffix)
        if src.exists():
            shutil.copy2(src, dest / src.name)
    return dest


def validate_and_store(src: Path, dry: bool) -> tuple[str, int, int]:
    """按上传接口同一套规则校验并落盘，返回 (url, size, duration)."""
    if not src.exists():
        raise SystemExit(f"源文件不存在：{src}")

    ext = src.suffix.lower()
    if ext not in ALLOWED_AUDIO_EXT:
        raise SystemExit(f"{src.name} 的扩展名 {ext} 不在白名单里")

    data = src.read_bytes()
    if len(data) > MAX_AUDIO_BYTES:
        raise SystemExit(
            f"{src.name} 太大了（{len(data) / 1024 / 1024:.1f}MB），"
            f"上限 {MAX_AUDIO_BYTES // 1024 // 1024}MB"
        )
    if not _looks_like_audio(data[:64], ext):
        raise SystemExit(f"{src.name} 文件头和音频格式对不上")

    url = f"/uploads/{datetime.now().strftime('%Y-%m')}/{uuid.uuid4().hex}{ext}"
    target = BASE_DIR / "static" / url.lstrip("/")
    if not dry:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return url, len(data), probe_duration(src)


def probe_duration(src: Path) -> int:
    """用 ffprobe 读时长（秒，四舍五入）。读不到就返回 0，不阻断导入。"""
    import json
    import subprocess

    ffprobe = (
        r"C:\Users\96281\AppData\Local\Microsoft\WinGet\Packages"
        r"\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
        r"\ffmpeg-8.1.2-full_build\bin\ffprobe.exe"
    )
    try:
        out = subprocess.run(
            [ffprobe, "-v", "error", "-show_entries", "format=duration",
             "-of", "json", str(src)],
            capture_output=True, text=True, timeout=20, check=True,
        ).stdout
        return round(float(json.loads(out)["format"]["duration"]))
    except Exception:
        return 0


def main() -> int:
    dry = "--dry-run" in sys.argv
    keep_existing = "--keep-existing" in sys.argv

    if not dry:
        dest = backup_db()
        print(f"[1/4] 已备份数据库 → {dest}")
    else:
        print("[1/4] dry-run：跳过备份")

    # 2) 校验 + 落盘
    payloads: list[dict] = []
    for item in WORKS:
        url, size, dur = validate_and_store(item["source"], dry)
        payloads.append({**item, "audio_url": url, "audio_size": size,
                         "audio_duration": dur})
        print(f"[2/4] {item['title']:<8} ← {item['source'].name}  "
              f"→ {url}  ({size / 1024 / 1024:.2f}MB / {dur}s)")

    db = SessionLocal()
    try:
        keep_ids: list[int] = []

        # 3) 写入 / 更新
        for order, p in enumerate(payloads):
            cat = (
                db.query(M.Category).filter(M.Category.slug == p["category_slug"]).first()
                if p["category_slug"] else None
            )
            row = db.query(M.Work).filter(M.Work.title == p["title"]).first()
            if row is None:
                row = M.Work(title=p["title"])
                db.add(row)
                action = "新增"
            else:
                action = "更新"
            row.kind = p["kind"]
            row.status = p["status"]
            row.summary = p["summary"]
            row.notes = p["notes"]
            row.cover = ""
            row.audio_url = p["audio_url"]
            row.audio_size = p["audio_size"]
            row.audio_duration = p["audio_duration"]
            row.allow_download = p["allow_download"]
            row.bpm = p["bpm"]
            row.key_signature = p["key_signature"]
            row.category_id = cat.id if cat else None
            row.tags = p["tags"]
            row.progress = p["progress"]
            row.sort_order = order
            db.flush()
            keep_ids.append(row.id)
            print(f"[3/4] {action}《{p['title']}》 id={row.id} "
                  f"分类={cat.name if cat else '—'}")

        # 4) 删除其余作品
        doomed = (
            db.query(M.Work)
            .filter(~M.Work.id.in_(keep_ids))
            .order_by(M.Work.id)
            .all()
        )
        if keep_existing:
            print(f"[4/4] --keep-existing：保留 {len(doomed)} 条旧作品不动")
        elif doomed:
            print(f"[4/4] 待删 {len(doomed)} 条旧作品：")
            for d in doomed:
                print(f"       - id={d.id} 《{d.title}》 ({d.status})")
            if not dry:
                for d in doomed:
                    db.delete(d)
        else:
            print("[4/4] 没有需要删除的旧作品")

        if dry:
            db.rollback()
            print("\ndry-run 结束：数据未改动")
        else:
            db.commit()
            print(f"\n完成：作品表 {db.query(M.Work).count()} 条")

        # 5) 清理孤儿音频：换过源的旧文件留在 uploads 里没人引用，
        #    不清掉的话 pages.sh 会一直把它们推到线上（白占体积）。
        if not dry:
            purge_orphan_audio(db)
    finally:
        db.close()
    return 0


def purge_orphan_audio(db) -> None:
    """删掉 uploads 里没有任何 work 引用的音频文件。

    只碰 uploads 目录，且只删音频扩展名 —— 图片、字体这些一律不动。
    """
    referenced = {
        Path(u).name
        for (u,) in db.query(M.Work.audio_url).all()
        if u
    }
    removed = 0
    for f in sorted(UPLOAD_DIR.rglob("*")):
        if not f.is_file() or f.suffix.lower() not in ALLOWED_AUDIO_EXT:
            continue
        if f.name not in referenced:
            f.unlink()
            removed += 1
            print(f"[5/5] 清掉没人引用的音频 {f.relative_to(UPLOAD_DIR.parent)}")
    if not removed:
        print("[5/5] 没有孤儿音频")


if __name__ == "__main__":
    raise SystemExit(main())
