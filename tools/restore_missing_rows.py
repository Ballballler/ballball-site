"""从迁移前的旧库补回被误删的记录。

背景：2026-09-26 有一轮自动化测试直接打到线上库，把 work / skill_item /
resume_item 里 id 连续的前几条删掉了（4 作品 → 1、16 技能 → 13、5 经历 → 3）。
旧库 `C:\\Users\\96281\\WorkBuddy\\Ballball 的主页\\data\\site.db` 里这些行都还在，
且新库里没有 id 冲突，所以按 id 逐行补回，只写两库共有的列。

安全性：
  - 只做 INSERT OR IGNORE，不 UPDATE、不 DELETE
  - 只补「旧库有、新库没有」的 id
  - 跑之前先把新库整体备份到 backup/db-restore-<日期>/

用法：python tools/restore_missing_rows.py [--dry-run]
"""
from __future__ import annotations

import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

NEW_DB = Path(r"D:\ballball-site\data\site.db")
OLD_DB = Path(r"C:\Users\96281\WorkBuddy\Ballball 的主页\data\site.db")
BACKUP_DIR = Path(r"D:\ballball-site\backup")

TABLES = ("work", "skill_item", "resume_item")


def columns(db: Path, table: str) -> list[str]:
    con = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)
    try:
        return [r[1] for r in con.execute(f"PRAGMA table_info({table})")]
    finally:
        con.close()


def main() -> int:
    dry = "--dry-run" in sys.argv

    if not NEW_DB.exists() or not OLD_DB.exists():
        print(f"数据库缺失：new={NEW_DB.exists()} old={OLD_DB.exists()}")
        return 1

    # 1) 备份：连同 -wal / -shm 一起复制，否则会漏掉还没 checkpoint 的数据
    if not dry:
        stamp = datetime.now().strftime("%Y-%m-%d")
        dest = BACKUP_DIR / f"db-restore-{stamp}"
        dest.mkdir(parents=True, exist_ok=True)
        for suffix in ("", "-wal", "-shm"):
            src = Path(str(NEW_DB) + suffix)
            if src.exists():
                shutil.copy2(src, dest / src.name)
        print(f"已备份 → {dest}")

    new_con = sqlite3.connect(NEW_DB)
    new_con.execute("PRAGMA foreign_keys=ON")
    old_con = sqlite3.connect(f"file:{OLD_DB.as_posix()}?mode=ro", uri=True)

    total = 0
    for table in TABLES:
        shared = [c for c in columns(NEW_DB, table) if c in columns(OLD_DB, table)]
        have = {r[0] for r in new_con.execute(f"SELECT id FROM {table}")}
        missing = [r for r in old_con.execute(f"SELECT * FROM {table}") if r[0] not in have]
        if not missing:
            print(f"{table:12s} 无需补")
            continue

        old_cols = [r[1] for r in old_con.execute(f"PRAGMA table_info({table})")]
        idx = [old_cols.index(c) for c in shared]
        placeholders = ",".join("?" * len(shared))
        # 列名一律加引号：skill_item 里有一列叫 group，是 SQLite 保留字
        quoted = ",".join(f'"{c}"' for c in shared)
        sql = f"INSERT OR IGNORE INTO {table} ({quoted}) VALUES ({placeholders})"
        rows = [tuple(r[i] for i in idx) for r in missing]
        label_col = "title" if "title" in shared else "name"
        print(f"{table:12s} 待补 {len(rows)} 条：{rows[0][shared.index(label_col)]!r} …")
        if not dry:
            new_con.executemany(sql, rows)
        total += len(rows)

    if not dry:
        new_con.commit()

    print()
    for table in TABLES:
        n = new_con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"{table:12s} 现在 {n} 条")
    print(f"\n{'（dry-run）' if dry else ''}合计补回 {total} 条")

    new_con.close()
    old_con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
