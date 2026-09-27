"""把 seed.py 里的真实个人资料 / 简历 / 技能同步进现有数据库。

为什么单独一个脚本：站点库里原有的是「（示例）某科技团队」这类占位数据，
而 seed.py 只在库全空时才灌，所以已经建好的库不会被更新。这个脚本做增量对齐：

- Profile：只改联系方式与简介这类「事实字段」，name / tagline 等保留 BB 手改的
- ResumeItem：全量替换（旧条目本来就是示例），按 seed 顺序重排
- SkillItem：按名字 upsert，BB 自己加过的技能不会被删

可以反复跑，跑第二次不会再产生变化。
用法：.venv/Scripts/python.exe tools/apply_real_profile.py [--dry]
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal  # noqa: E402
from app.models import Interest, Profile, ResumeItem, SkillItem  # noqa: E402
from app.seed import INTERESTS, PROFILE, RESUME_ITEMS, SKILL_ITEMS  # noqa: E402

DRY = "--dry" in sys.argv


def sync_profile(db) -> int:
    """只同步「事实」字段：地点、邮箱、联系方式、简介。
    name / headline / tagline / highlights 保留站长手改的版本。"""
    p = db.query(Profile).filter(Profile.id == 1).first()
    if not p:
        return 0
    changed = []
    for field in ("location", "email", "links", "bio"):
        want = PROFILE[field]
        if getattr(p, field) != want:
            changed.append(f"{field}: {str(getattr(p, field))[:40]!r} → {str(want)[:40]!r}")
            if not DRY:
                setattr(p, field, want)
    return len(changed)


def sync_resume(db) -> tuple[int, int]:
    """全量替换：旧条目是占位示例，没有保留价值。"""
    existing = db.query(ResumeItem).order_by(ResumeItem.sort_order, ResumeItem.id).all()
    old_titles = [i.title for i in existing]
    new_titles = [i["title"] for i in RESUME_ITEMS]
    if old_titles == new_titles:
        return 0, 0
    if not DRY:
        for row in existing:
            db.delete(row)
        db.flush()
        for idx, item in enumerate(RESUME_ITEMS):
            db.add(ResumeItem(**item, sort_order=idx))
    return len(existing), len(RESUME_ITEMS)


def sync_skills(db) -> tuple[int, int]:
    """按名字 upsert，多出来的（站长自己加的）不动。"""
    rows = {s.name: s for s in db.query(SkillItem).all()}
    added, updated = 0, 0
    for idx, (name, level, group, color, note) in enumerate(SKILL_ITEMS):
        row = rows.get(name)
        if row is None:
            added += 1
            if not DRY:
                db.add(
                    SkillItem(
                        name=name,
                        level=level,
                        group=group,
                        color=color,
                        note=note,
                        sort_order=idx,
                    )
                )
            continue
        fields = dict(level=level, group=group, color=color, note=note, sort_order=idx)
        diff = [k for k, v in fields.items() if getattr(row, k) != v]
        if diff:
            updated += 1
            if not DRY:
                for k in diff:
                    setattr(row, k, fields[k])
    return added, updated


def sync_interests(db) -> int:
    """按标题 upsert 描述与跳转；站长改名过的条目匹配不到就跳过，不硬盖。"""
    rows = {i.title: i for i in db.query(Interest).all()}
    changed = 0
    for item in INTERESTS:
        row = rows.get(item["title"])
        if row is None:
            continue
        fields = {
            k: v
            for k, v in item.items()
            if k in ("description", "link", "icon", "accent")
        }
        diff = [k for k, v in fields.items() if getattr(row, k) != v]
        if diff:
            changed += 1
            if not DRY:
                for k in diff:
                    setattr(row, k, fields[k])
    return changed


def main() -> None:
    with SessionLocal() as db:
        n_profile = sync_profile(db)
        n_old, n_new = sync_resume(db)
        n_add, n_upd = sync_skills(db)
        n_int = sync_interests(db)
        if DRY:
            print(f"[dry] 资料字段待更新 {n_profile} 项")
            print(f"[dry] 简历条目 {n_old} → {n_new}")
            print(f"[dry] 技能 新增 {n_add} / 更新 {n_upd}")
            print(f"[dry] 兴趣描述待更新 {n_int} 条")
            db.rollback()
            return
        db.commit()

    print(f"资料字段更新 {n_profile} 项")
    print(f"简历条目 {n_old} → {n_new} 条")
    print(f"技能 新增 {n_add} 条 / 更新 {n_upd} 条")
    print(f"兴趣描述更新 {n_int} 条")


if __name__ == "__main__":
    main()
