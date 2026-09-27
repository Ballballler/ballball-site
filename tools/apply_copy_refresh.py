"""站点文案微调。

为什么是脚本而不是手改数据库：这些字将来会被 seed 或后台覆盖，
写成幂等脚本才能改完再改回来，也能一眼看清改了哪几处、原文是什么。

用法：
    python tools/apply_copy_refresh.py --dry-run   # 只打印差异
    python tools/apply_copy_refresh.py             # 落库

只改表达，不动事实：这里没有任何数字是编的，涉及实测数值的一律来自分析输出。
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "site.db"

# id / kind -> 新文案。改之前先看一眼 WAS，确认原文确实是那个。
CHANGES: list[dict] = [
    {
        "where": "profile.highlights[2]",
        "reason": "「为自己的喜好买单」是句口号，没说清到底做了什么",
        "was_title": "自己做自己的工程师",
        "was_text": "为自己的喜好买单。",
        "title": "自己给自己写工具",
        "text": "这个站从后端到三维都是自己写的。想要什么功能，当晚就能上线。",
    },
    {
        "where": "interest#3 描述",
        "reason": "「比起炫技，更在意它是不是真的有用」是万能句，换成具体动作",
        "was": "用 Python 把想法落成能跑的东西，日常靠 Codex / Hermes / Workbuddy 这些 Agent 提效。比起炫技，更在意它是不是真的有用。",
        "text": "拿 Python 把想法落成能跑的东西，重复的环节交给 Codex、Hermes、Workbuddy 这些 Agent。炫技没意思，自己天天用得上才算。",
    },
    {
        "where": "interest#4 描述",
        "reason": "收掉半句废话",
        "was": "影评、随笔、零散的想法。写下来才算真的想过一遍。",
        "text": "影评、随笔、零散的念头。没写下来就不算想过。",
    },
]


def load_json(raw: str) -> list:
    try:
        return json.loads(raw or "[]")
    except json.JSONDecodeError:
        print(f"!! JSON 解析失败，跳过：{raw[:60]}", file=sys.stderr)
        return None  # type: ignore[return-value]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    writes = False

    # 1. profile.highlights
    row = conn.execute("select highlights from profile where id = 1").fetchone()
    highlights = load_json(row["highlights"]) if row else None
    if highlights:
        change = CHANGES[0]
        item = highlights[2]
        if item.get("title") == change["was_title"] and item.get("text") == change["was_text"]:
            print(f"[{change['where']}]")
            print(f"  原：{change['was_title']} / {change['was_text']}")
            print(f"  新：{change['title']} / {change['text']}")
            highlights[2] = {**item, "title": change["title"], "text": change["text"]}
            if not args.dry_run:
                conn.execute(
                    "update profile set highlights = ? where id = 1",
                    (json.dumps(highlights, ensure_ascii=False),),
                )
                writes = True
        else:
            print(f"[{change['where']}] 原文已不是预期内容，跳过")

    # 2/3. interest 描述
    for idx, change in [(3, CHANGES[1]), (4, CHANGES[2])]:
        row = conn.execute("select id, title, description from interest where id = ?", (idx,)).fetchone()
        if not row:
            print(f"[{change['where']}] 找不到 id={idx}，跳过")
            continue
        if row["description"].strip() == change["was"]:
            print(f"[{change['where']}] {row['title']}")
            print(f"  原：{change['was']}")
            print(f"  新：{change['text']}")
            if not args.dry_run:
                conn.execute(
                    "update interest set description = ? where id = ?",
                    (change["text"], idx),
                )
                writes = True
        else:
            print(f"[{change['where']}] 原文已改过，跳过")

    if writes:
        conn.commit()
        print("\n已写入数据库")
    else:
        print("\n没有改动（--dry-run 或内容对不上）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
