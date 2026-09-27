"""把站点数据库里的雇主名、产品线等身份信息换成行业代称。

为什么单独成 script：站点推的是公开仓库和 GitHub Pages，公司名一旦上线就收不回来。
数据只有本地 data/site.db 一份，改之前脚本会先备份。

⚠️ 映射表不住在仓库里
    要被替换的原文（公司全称、产品线）本身就是隐私 —— 把它写进代码，等于在公开仓库
    里留一份「原名 → 化名」对照表，脱敏等于白做。所以 REPLACEMENTS 不再内联，
    改成从 **data/identity_map.json** 读取（data/ 整个被 .gitignore 挡着）。

    文件格式（数组，**长串在前**，否则「A 地图打车」会先被「A」截断）：
        [
          ["某某某某有限公司", "某垂直行业公司"],
          ["某产品线", "某业务线"]
        ]
    其中 **原文与替身相同的条目算「保护项」**：它们会被先藏起来、最后原样放回，
    用来挡住同形异构的误伤（例如某影片简介里的某星级主厨头衔）。
    本地没有这个文件时脚本会直接退出并说明 —— 带着空映射跑完，会让人误以为库已干净。

用法：
    python tools/deidentify.py --check     # 只扫描，不改库
    python tools/deidentify.py             # 执行替换（幂等，重复跑不会叠加）
"""
from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "site.db"
MAP_FILE = ROOT / "data" / "identity_map.json"

# 这些留着不替换是有意的，改动前先想清楚：
#   - 北京物资学院：学历需要可核验，泛化了反而像在隐瞒
#   - 对外联系邮箱：bio 里也写了「发邮件反驳我」
KEEP = ["北京物资学院"]

TABLES = ["profile", "resume_item", "skill_item", "journey_step", "work",
          "interest", "movie", "page_section", "category"]


def load_map(path: Path) -> list[tuple[str, str]]:
    """读外部映射表。缺文件要明确失败 —— 空映射跑完会伪装成「已经干净」。"""
    if not path.exists():
        print(f"缺少映射文件：{path}", file=sys.stderr)
        print("照 tools/identity_map.example.json 的格式建一个，填「原文 → 代称」。", file=sys.stderr)
        raise SystemExit(2)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        print(f"映射文件不是合法 JSON：{exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    out = [(str(a), str(b)) for pair in raw for a, b in [pair] if str(a)]
    if not out:
        print("映射文件是空的，什么都不会替换。", file=sys.stderr)
        raise SystemExit(2)
    return out


def pk_of(row: sqlite3.Row) -> str:
    """取主键列名。这里的 id 都是 INTEGER PRIMARY KEY，本身就是 rowid 别名，
    所以不能再 `select rowid, *`（两列会都叫 id，Row 取不到 rowid 这个 key）。"""
    keys = row.keys()
    return "id" if "id" in keys else keys[0]


def _ascii_escaped(s: str) -> str:
    """把中文转成 \\uXXXX。highlights / tags 这些 JSON 字段是用 ensure_ascii=True
    存的，原文在库里是转义形态，直接按中文找会漏（有记录度 > 40 的一次漏网）。"""
    return json.dumps(s, ensure_ascii=True)[1:-1]


def _forms(s: str) -> list[str]:
    """同一个串的两种形态：中文原文 + \\uXXXX 转义。去重后返回。"""
    esc = _ascii_escaped(s)
    return [s] if esc == s else [s, esc]


def split_guards(replacements: list[tuple[str, str]]
                 ) -> tuple[list[str], list[tuple[str, str]]]:
    """映射里 **原文 == 替身** 的条目算「保护项」，不是替换。

    典型例子：某部电影的简介里有「某星级主厨」，跟公司名无关，不能被
    「那条短规则」误伤。保护项先被换成哨兵藏起来，替换跑完再原样放回，
    这样无论它在列表里的什么位置都不会被后面的短串截断。
    """
    guards = [needle for needle, repl in replacements if needle == repl]
    real = [(n, r) for n, r in replacements if n != r]
    return guards, real


def apply_replacements(text: str, replacements: list[tuple[str, str]]) -> str:
    """按「先藏保护项 → 跑替换 → 还原保护项」的顺序处理。"""
    guards, real = split_guards(replacements)
    tokens: dict[str, str] = {}
    for gi, guard in enumerate(guards):
        for fi, form in enumerate(_forms(guard)):
            token = f"\x00{gi}.{fi}\x00"
            tokens[token] = form
            text = text.replace(form, token)
    for needle, repl in real:
        for n_form, r_form in zip(_forms(needle), _forms(repl)):
            text = text.replace(n_form, r_form)
    for token, form in tokens.items():
        text = text.replace(token, form)
    return text


def hits_in(text: str, replacements: list[tuple[str, str]]) -> list[str]:
    """返回这段文本里真正命中的 needle（保护项已经先被抠掉，不会误报）。"""
    guards, real = split_guards(replacements)
    masked = text
    for gi, guard in enumerate(guards):
        for fi, form in enumerate(_forms(guard)):
            masked = masked.replace(form, f"\x00{gi}.{fi}\x00")
    return [needle for needle, _ in real for f in _forms(needle) if f in masked]


def scan(conn: sqlite3.Connection, replacements: list[tuple[str, str]]
         ) -> list[tuple[str, object, str, str]]:
    """返回还剩哪些隐私串。"""
    hits: list[tuple[str, object, str, str]] = []
    for table in TABLES:
        try:
            rows = conn.execute(f"select * from {table}").fetchall()
        except sqlite3.OperationalError:
            continue
        for row in rows:
            pk = pk_of(row)
            for col in row.keys():
                val = row[col]
                if not isinstance(val, str):
                    continue
                needles = hits_in(val, replacements)
                for needle in needles:
                    hits.append((table, row[pk], col, needle))
    return hits


def bake(conn: sqlite3.Connection, replacements: list[tuple[str, str]]) -> int:
    total = 0
    for table in TABLES:
        try:
            rows = conn.execute(f"select * from {table}").fetchall()
        except sqlite3.OperationalError:
            continue
        for row in rows:
            pk = pk_of(row)
            patch: dict[str, str] = {}
            for col in row.keys():
                if col == pk:
                    continue
                val = row[col]
                if not isinstance(val, str) or not val:
                    continue
                new = apply_replacements(val, replacements)
                if new != val:
                    patch[col] = new
            if not patch:
                continue
            if "updated_at" in row.keys():
                patch["updated_at"] = datetime.now().isoformat(sep=" ", timespec="seconds")
            sets = ", ".join(f"{c} = ?" for c in patch)
            sql = f"update {table} set {sets} where {pk} = ?"
            conn.execute(sql, [*patch.values(), row[pk]])
            total += len(patch)
            print(f"  {table}#{row[pk]}: {[c for c in patch if c != 'updated_at']}")
    return total


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只扫描不修改")
    ap.add_argument("--db", default=str(DB))
    ap.add_argument("--map", default=str(MAP_FILE), help="原名 → 代称的映射表（不入库）")
    args = ap.parse_args()

    map_file = Path(args.map)
    replacements = load_map(map_file)
    db = Path(args.db)
    if not db.exists():
        print(f"找不到数据库：{db}", file=sys.stderr)
        return 1

    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row

    if args.check:
        hits = scan(conn, replacements)
        if hits:
            for t, rid, col, needle in hits:
                print(f"命中 {t}#{rid} 的 {col}：包含「{needle}」")
            print(f"\n共 {len(hits)} 处待处理")
        else:
            print("干净，没有匹配到隐私串")
        return 0 if not hits else 2

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = db.parent / f"site.db.deidentify-{stamp}"
    shutil.copy2(db, backup)
    print(f"已备份到 {backup.name}")

    n = bake(conn, replacements)
    conn.commit()

    left = scan(conn, replacements)
    print(f"\n改动字段 {n} 个；剩余未替换 {len(left)} 处")
    for t, rid, col, needle in left:
        print(f"  !! {t}#{rid}.{col} 仍含「{needle}」")
    if KEEP:
        print("有意保留：" + "、".join(KEEP))
    return 0 if not left else 2


if __name__ == "__main__":
    raise SystemExit(main())
