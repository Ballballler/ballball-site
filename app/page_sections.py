"""页面区块注册表。

前台每一页由若干「区块」拼起来。这里定义默认有哪些区块、叫什么、什么顺序。
后台的「页面区块」页就是在这份注册表之上做增删改：
  - 隐藏：visible=False，前台不渲染，配置还在；
  - 删除：整行没了，前台也就不渲染了；
  - 排序：sort_order，越小越靠前。

启动时会把注册表里缺的补齐（幂等，不动已有配置），所以新增一个区块
只要往这里加一行，老库重启后也会自动出现。
"""
from __future__ import annotations

from sqlalchemy import select

from .models import PageSection

# page -> [(key, 后台显示名), ...]，列表顺序即默认顺序
DEFAULT_SECTIONS: dict[str, list[tuple[str, str]]] = {
    "index": [
        ("about", "关于我"),
        ("resume-preview", "简历速览"),
        ("movies-preview", "精选电影"),
        ("works-preview", "精选音乐"),
    ],
    "resume": [
        ("hero", "自我介绍头部"),
        ("journey", "成长路径"),
        ("skills", "技能与三维球"),
        ("timeline", "履历时间轴"),
    ],
    "movies": [
        ("hero", "幽灵主视觉"),
        ("stats", "数据概览"),
        ("filters", "分类筛选"),
        ("grid", "片单网格"),
    ],
    "works": [
        ("hero", "唱片主视觉"),
        ("stats", "数据概览"),
        ("filters", "状态筛选"),
        ("tag-filters", "风格筛选"),
        ("grid", "作品网格"),
    ],
}

PAGE_TITLES: dict[str, str] = {
    "index": "首页",
    "resume": "简历页",
    "movies": "电影页",
    "works": "音乐页",
}


def ensure_default_page_sections(db) -> int:
    """补齐缺失的默认区块。已有配置一律不动，返回新增条数。"""
    added = 0
    moved = 0
    for page, rows in DEFAULT_SECTIONS.items():
        current = list(db.scalars(select(PageSection).where(PageSection.page == page)))
        existing = {r.key for r in current}
        for idx, (key, title) in enumerate(rows):
            if key in existing:
                continue
            db.add(PageSection(page=page, key=key, title=title, visible=True, sort_order=idx))
            added += 1
        # 往注册表中间插入过新区块时，老库的 sort_order 会和它撞号（例如 works 的
        # tag-filters 与 grid 都是 3）。撞号时按注册表顺序重排这一页，其余情况不动。
        if current and _has_duplicate_order(current):
            moved += _renumber(db, page, current)
    if added or moved:
        db.commit()
    return added


def _has_duplicate_order(rows: list[PageSection]) -> bool:
    seen = {r.sort_order for r in rows}
    return len(seen) != len(rows)


def _renumber(db, page: str, rows: list[PageSection]) -> None:
    """按注册表顺序重写 sort_order；注册表里没有的 key 排在后面，保持原相对次序。"""
    default_keys = [key for key, _ in DEFAULT_SECTIONS.get(page, [])]
    by_key = {r.key: r for r in rows}
    ordered = [by_key[k] for k in default_keys if k in by_key]
    rest = sorted(
        (r for r in rows if r.key not in default_keys),
        key=lambda r: (r.sort_order, r.id),
    )
    for idx, row in enumerate(ordered + rest):
        row.sort_order = idx
    db.flush()
    return len(ordered + rest)


def reset_page_sections(db, page: str) -> int:
    """把某一页的区块恢复成注册表里的样子。会丢掉这一页的所有自定义配置。"""
    for row in db.scalars(select(PageSection).where(PageSection.page == page)):
        db.delete(row)
    db.flush()
    for idx, (key, title) in enumerate(DEFAULT_SECTIONS.get(page, [])):
        db.add(PageSection(page=page, key=key, title=title, visible=True, sort_order=idx))
    db.commit()
    return len(DEFAULT_SECTIONS.get(page, []))
