"""前台只读接口。

提供 /api/overview 一次性返回首页所需数据，减少首屏请求数；
其余为各模块的列表 / 详情接口。
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from ..database import SessionLocal
from ..models import (
    Category,
    Interest,
    JourneyStep,
    Movie,
    PageSection,
    Profile,
    ResumeItem,
    SkillItem,
    Work,
)
from ..schemas import (
    CategoryOut,
    InterestOut,
    JourneyStepOut,
    MovieBrief,
    MovieOut,
    PageSectionOut,
    ProfileOut,
    ResumeItemOut,
    SkillItemOut,
    WorkOut,
)

router = APIRouter(prefix="/api", tags=["public"])


def _get_profile() -> Profile:
    """Profile 恒定单行，缺失时按默认补一行，保证前台永不 500。"""
    with SessionLocal() as db:
        profile = db.get(Profile, 1)
        if profile is None:
            profile = Profile(id=1)
            db.add(profile)
            db.commit()
            db.refresh(profile)
        return profile


@router.get("/profile", response_model=ProfileOut)
def read_profile() -> Profile:
    return _get_profile()


@router.get("/interests", response_model=list[InterestOut])
def list_interests() -> list[Interest]:
    with SessionLocal() as db:
        return list(
            db.scalars(
                select(Interest).order_by(Interest.sort_order, Interest.id)
            ).all()
        )


@router.get("/categories", response_model=list[CategoryOut])
def list_categories(kind: str | None = Query(default=None)) -> list[Category]:
    with SessionLocal() as db:
        stmt = select(Category).order_by(Category.sort_order, Category.id)
        if kind:
            stmt = stmt.where(Category.kind == kind)
        return list(db.scalars(stmt).all())


@router.get("/movies", response_model=list[MovieBrief])
def list_movies(
    category_id: int | None = Query(default=None),
    keyword: str | None = Query(default=None),
    status: str | None = Query(
        default=None,
        pattern="^(watched|candidate)$",
        description="watched = 正式档案；candidate = 待看候选。不传则两者都返回。",
    ),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[Movie]:
    with SessionLocal() as db:
        stmt = select(Movie).order_by(Movie.sort_order, Movie.id)
        if category_id:
            stmt = stmt.where(Movie.category_id == category_id)
        if status:
            stmt = stmt.where(Movie.status == status)
        if keyword:
            like = f"%{keyword.strip()}%"
            stmt = stmt.where(Movie.title.like(like))
        return list(db.scalars(stmt.limit(limit)).all())


@router.get("/movies/{movie_id}", response_model=MovieOut)
def read_movie(movie_id: int) -> Movie:
    with SessionLocal() as db:
        movie = db.get(Movie, movie_id)
        if movie is None:
            raise HTTPException(status_code=404, detail="电影不存在")
        return movie


@router.get("/works", response_model=list[WorkOut])
def list_works(
    kind: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[Work]:
    with SessionLocal() as db:
        stmt = select(Work).order_by(Work.sort_order, Work.id)
        if kind:
            stmt = stmt.where(Work.kind == kind)
        if status:
            stmt = stmt.where(Work.status == status)
        return list(db.scalars(stmt.limit(limit)).all())


@router.get("/works/{work_id}", response_model=WorkOut)
def read_work(work_id: int) -> Work:
    with SessionLocal() as db:
        work = db.get(Work, work_id)
        if work is None:
            raise HTTPException(status_code=404, detail="作品不存在")
        return work


@router.get("/skills", response_model=list[SkillItemOut])
def list_skills() -> list[SkillItem]:
    with SessionLocal() as db:
        return list(
            db.scalars(select(SkillItem).order_by(SkillItem.sort_order, SkillItem.id))
        )


@router.get("/journey", response_model=list[JourneyStepOut])
def list_journey() -> list[JourneyStep]:
    """成长路径。「我是怎么一步步走到这儿的」——简历页的主角。"""
    with SessionLocal() as db:
        return list(
            db.scalars(select(JourneyStep).order_by(JourneyStep.sort_order, JourneyStep.id))
        )


@router.get("/resume")
def read_resume() -> dict:
    """简历页聚合：成长路径 + 经历时间轴 + 技能条（技能同时供 3D 球使用）。

    顺序即立场：先讲怎么走过来的，再摆履历做佐证。
    """
    with SessionLocal() as db:
        steps = list(
            db.scalars(select(JourneyStep).order_by(JourneyStep.sort_order, JourneyStep.id))
        )
        items = list(
            db.scalars(
                select(ResumeItem).order_by(ResumeItem.sort_order, ResumeItem.id)
            )
        )
        skills = list(
            db.scalars(select(SkillItem).order_by(SkillItem.sort_order, SkillItem.id))
        )
        return {
            "journey": [JourneyStepOut.model_validate(s) for s in steps],
            "items": [ResumeItemOut.model_validate(i) for i in items],
            "skills": [SkillItemOut.model_validate(s) for s in skills],
        }


@router.get("/overview")
def overview() -> dict:
    """首页聚合接口：一次请求拿齐首屏数据。"""
    with SessionLocal() as db:
        profile = db.get(Profile, 1)
        if profile is None:
            profile = Profile(id=1)
            db.add(profile)
            db.commit()
            db.refresh(profile)
        interests = list(
            db.scalars(select(Interest).order_by(Interest.sort_order, Interest.id))
        )
        movies = list(
            db.scalars(select(Movie).order_by(Movie.sort_order, Movie.id).limit(6))
        )
        works = list(
            db.scalars(select(Work).order_by(Work.sort_order, Work.id).limit(6))
        )
        categories = list(
            db.scalars(select(Category).order_by(Category.sort_order, Category.id))
        )
        skills = list(
            db.scalars(select(SkillItem).order_by(SkillItem.sort_order, SkillItem.id))
        )
        return {
            "profile": ProfileOut.model_validate(profile),
            "interests": [InterestOut.model_validate(i) for i in interests],
            "movies": [MovieBrief.model_validate(m) for m in movies],
            "works": [WorkOut.model_validate(w) for w in works],
            "categories": [CategoryOut.model_validate(c) for c in categories],
            "skills": [SkillItemOut.model_validate(s) for s in skills],
        }


@router.get("/page-sections/{page}", response_model=list[PageSectionOut])
def page_sections(page: str) -> list[PageSection]:
    """前台渲染某个页面前先问一句：这一页要显示哪些区块、按什么顺序。

    查不到任何配置时返回空数组 —— 前台据此「什么都不渲染」，
    所以后台把某一页全删了就是真的清空，不是回到默认。
    """
    with SessionLocal() as db:
        return list(
            db.scalars(
                select(PageSection)
                .where(PageSection.page == page)
                .order_by(PageSection.sort_order, PageSection.id)
            )
        )


@router.get("/page-sections", response_model=list[PageSectionOut])
def all_page_sections() -> list[PageSection]:
    """全部区块，后台概览用。"""
    with SessionLocal() as db:
        return list(
            db.scalars(
                select(PageSection).order_by(
                    PageSection.page, PageSection.sort_order, PageSection.id
                )
            )
        )
