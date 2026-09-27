"""把站点里的雇主名、产品线等身份信息换成行业代称。

为什么单独成 script：站点要推公开仓库和 GitHub Pages，公司名一旦上线就收不回来。
数据只有本地 data/site.db 一份，改之前脚本会先备份。

用法：
    python tools/deidentify.py --check     # 只扫描，不改库
    python tools/deidentify.py             # 执行替换（幂等，重复跑不会叠加）

顺序敏感：长串必须先替换，否则「出行业务」会先被「某互联网公司」截断。
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

# (原文, 替身)。长串在前。
REPLACEMENTS: list[tuple[str, str]] = [
    ("出行业务", "出行业务"),
    ("某全球消费电子品牌 · 中国区官网运营", "某全球消费电子品牌 · 中国区官网运营"),
    ("某出行服务平台", "某出行服务平台"),
    ("某零售集团（购物中心）", "某零售集团（购物中心）"),
    ("负责某全球消费电子品牌", "负责某全球消费电子品牌"),
    ("某全球消费电子品牌", "某全球消费电子品牌"),
    ("在一家互联网公司", "在一家互联网公司"),
    ("某互联网公司", "某互联网公司"),
]

# 这些留着不替换是有意的，改动前先想清楚：
#   - 北京物资学院：学历需要可核验，泛化了反而像在隐瞒
#   - 962817243@qq.com：站点对外联系邮箱，bio 里也写了「发邮件反驳我」
KEEP = ["北京物资学院", "962817243@qq.com"]

TABLES = ["profile", "resume_item", "skill_item", "journey_step", "work",
          "interest", "movie", "page_section", "category"]


def pk_of(row: sqlite3.Row) -> str:
    """取主键列名。这里的 id 都是 INTEGER PRIMARY KEY，本身就是 rowid 别名，
    所以不能再 `select rowid, *`（两列会都叫 id，Row 取不到 rowid 这个 key）。"""
    keys = row.keys()
    return "id" if "id" in keys else keys[0]


def _ascii_escaped(s: str) -> str:
    """把中文转成 \\uXXXX。highlights / tags 这些 JSON 字段是用 ensure_ascii=True
    存的，原文在库里是转义形态，直接按中文找会漏（出行业务就漏过一次）。"""
    return json.dumps(s, ensure_ascii=True)[1:-1]


def pairs() -> list[tuple[str, str]]:
    """每个替换都配一版「原文转转义」的写法，两种形态都覆盖。"""
    out: list[tuple[str, str]] = []
    for needle, repl in REPLACEMENTS:
        out.append((needle, repl))
        esc_n = _ascii_escaped(needle)
        if esc_n != needle:
            out.append((esc_n, _ascii_escaped(repl)))
    return out


def scan(conn: sqlite3.Connection) -> list[tuple[str, object, str, str]]:
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
                for needle, _ in pairs():
                    if needle in val:
                        hits.append((table, row[pk], col, needle))
    return hits


def bake(conn: sqlite3.Connection) -> int:
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
                new = val
                for needle, repl in pairs():
                    new = new.replace(needle, repl)
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
    args = ap.parse_args()

    db = Path(args.db)
    if not db.exists():
        print(f"找不到数据库：{db}", file=sys.stderr)
        return 1

    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row

    if args.check:
        hits = scan(conn)
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

    n = bake(conn)
    conn.commit()

    left = scan(conn)
    print(f"\n改动字段 {n} 个；剩余未替换 {len(left)} 处")
    for t, rid, col, needle in left:
        print(f"  !! {t}#{rid}.{col} 仍含「{needle}」")
    if KEEP:
        print("有意保留：" + "、".join(KEEP))
    return 0 if not left else 2


if __name__ == "__main__":
    raise SystemExit(main())
