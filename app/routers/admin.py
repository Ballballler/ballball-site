"""管理后台接口：登录 + 全量增删改查 + 图片上传。

所有写操作都要经过 require_admin 依赖。
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import select

from ..config import (
    ADMIN_PASSWORD,
    ALLOWED_AUDIO_EXT,
    ALLOWED_IMAGE_EXT,
    MAX_AUDIO_BYTES,
    MAX_UPLOAD_BYTES,
    SESSION_COOKIE_NAME,
    SESSION_TTL_SECONDS,
    UPLOAD_DIR,
)
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
from ..page_sections import DEFAULT_SECTIONS, ensure_default_page_sections, reset_page_sections
from ..style_tags import suggest_style_tags
from ..security import (
    check_admin_password,
    create_session_token,
    ensure_admin_password,
    set_admin_password,
    using_default_password,
)
from ..schemas import (
    CategoryCreate,
    CategoryOut,
    CategoryUpdate,
    InterestCreate,
    InterestOut,
    InterestUpdate,
    JourneyStepCreate,
    JourneyStepOut,
    JourneyStepUpdate,
    MovieCreate,
    MovieFromTmdb,
    MovieOut,
    MovieUpdate,
    OkOut,
    PageSectionCreate,
    PageSectionOut,
    PageSectionReset,
    PageSectionUpdate,
    PasswordChange,
    ProfileOut,
    ProfileUpdate,
    ResumeItemCreate,
    ResumeItemOut,
    ResumeItemUpdate,
    SkillItemCreate,
    SkillItemOut,
    SkillItemUpdate,
    StatsOut,
    TagSuggestOut,
    TmdbSearchOut,
    UploadOut,
    WorkCreate,
    WorkOut,
    WorkTagSuggest,
    WorkUpdate,
)
from .. import tmdb
from ..audio_analysis import AudioAnalysisError, analyze_work_audio, available
from .deps import require_admin

router = APIRouter(prefix="/api/admin", tags=["admin"])

ensure_admin_password(ADMIN_PASSWORD)


def _set_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=SESSION_TTL_SECONDS,
        httponly=True,
        samesite="lax",
        # 部署文档要求配好 HTTPS 后把 secure 打开
        secure=False,
        path="/",
    )


# ------------------------------ 登录 ------------------------------


@router.post("/login", response_model=OkOut)
def login(payload: dict, response: Response) -> OkOut:
    password = str(payload.get("password", ""))
    if not check_admin_password(password):
        raise HTTPException(status_code=401, detail="口令不正确")
    _set_cookie(response, create_session_token())
    return OkOut(message="登录成功")


@router.post("/logout", response_model=OkOut)
def logout(response: Response) -> OkOut:
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")
    return OkOut(message="已退出")


@router.get("/session")
def session(_: bool = require_admin) -> dict:
    return {"ok": True, "using_default_password": using_default_password(ADMIN_PASSWORD)}


@router.post("/password", response_model=OkOut)
def change_password(payload: PasswordChange, _: bool = require_admin) -> OkOut:
    if not check_admin_password(payload.old_password):
        raise HTTPException(status_code=400, detail="原口令不正确")
    set_admin_password(payload.new_password)
    return OkOut(message="口令已更新，请记牢新口令")


@router.get("/stats", response_model=StatsOut)
def stats(_: bool = require_admin) -> StatsOut:
    with SessionLocal() as db:
        movies = db.query(Movie).count()
        works = db.query(Work).count()
        cats = db.query(Category).count()
        interests = db.query(Interest).count()
        resume_items = db.query(ResumeItem).count()
        skills = db.query(SkillItem).count()
        ratings = [m.rating for m in db.query(Movie.rating).all()]
    avg = round(sum(ratings) / len(ratings), 2) if ratings else 0
    return StatsOut(
        movies=movies,
        works=works,
        categories=cats,
        interests=interests,
        resume_items=resume_items,
        skills=skills,
        avg_rating=avg,
        using_default_password=using_default_password(ADMIN_PASSWORD),
    )


# ------------------------------ Profile ------------------------------


@router.put("/profile", response_model=ProfileOut)
def update_profile(payload: ProfileUpdate, _: bool = require_admin) -> Profile:
    with SessionLocal() as db:
        profile = db.get(Profile, 1)
        if profile is None:
            profile = Profile(id=1)
            db.add(profile)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(profile, field, value)
        db.commit()
        db.refresh(profile)
        return profile


# ------------------------------ Category ------------------------------


@router.get("/categories", response_model=list[CategoryOut])
def admin_list_categories(_: bool = require_admin) -> list[Category]:
    with SessionLocal() as db:
        return list(
            db.query(Category).order_by(Category.kind, Category.sort_order, Category.id)
        )


@router.post("/categories", response_model=CategoryOut)
def create_category(payload: CategoryCreate, _: bool = require_admin) -> Category:
    with SessionLocal() as db:
        data = payload.model_dump()
        # slug 留空时回落到名称，保证前台筛选链接永远有值
        data["slug"] = (payload.slug or "").strip() or payload.name.strip()
        item = Category(**data)
        db.add(item)
        db.commit()
        db.refresh(item)
        return item


@router.put("/categories/{item_id}", response_model=CategoryOut)
def update_category(
    item_id: int, payload: CategoryUpdate, _: bool = require_admin
) -> Category:
    with SessionLocal() as db:
        item = db.get(Category, item_id)
        if item is None:
            raise HTTPException(status_code=404, detail="分类不存在")
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(item, field, value)
        db.commit()
        db.refresh(item)
        return item


@router.delete("/categories/{item_id}", response_model=OkOut)
def delete_category(item_id: int, _: bool = require_admin) -> OkOut:
    with SessionLocal() as db:
        item = db.get(Category, item_id)
        if item is None:
            raise HTTPException(status_code=404, detail="分类不存在")
        db.delete(item)
        db.commit()
        return OkOut(message="分类已删除，引用它的条目会自动置为未分类")


# ------------------------------ Interest ------------------------------


@router.get("/interests", response_model=list[InterestOut])
def admin_list_interests(_: bool = require_admin) -> list[Interest]:
    with SessionLocal() as db:
        return list(db.query(Interest).order_by(Interest.sort_order, Interest.id))


@router.post("/interests", response_model=InterestOut)
def create_interest(payload: InterestCreate, _: bool = require_admin) -> Interest:
    with SessionLocal() as db:
        item = Interest(**payload.model_dump())
        db.add(item)
        db.commit()
        db.refresh(item)
        return item


@router.put("/interests/{item_id}", response_model=InterestOut)
def update_interest(
    item_id: int, payload: InterestUpdate, _: bool = require_admin
) -> Interest:
    with SessionLocal() as db:
        item = db.get(Interest, item_id)
        if item is None:
            raise HTTPException(status_code=404, detail="兴趣条目不存在")
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(item, field, value)
        db.commit()
        db.refresh(item)
        return item


@router.delete("/interests/{item_id}", response_model=OkOut)
def delete_interest(item_id: int, _: bool = require_admin) -> OkOut:
    with SessionLocal() as db:
        item = db.get(Interest, item_id)
        if item is None:
            raise HTTPException(status_code=404, detail="兴趣条目不存在")
        db.delete(item)
        db.commit()
        return OkOut(message="已删除")


# ------------------------------ Movie ------------------------------


@router.get("/movies", response_model=list[MovieOut])
def admin_list_movies(_: bool = require_admin) -> list[Movie]:
    with SessionLocal() as db:
        return list(db.query(Movie).order_by(Movie.sort_order, Movie.id))


@router.post("/movies", response_model=MovieOut)
def create_movie(payload: MovieCreate, _: bool = require_admin) -> Movie:
    with SessionLocal() as db:
        item = Movie(**payload.model_dump())
        db.add(item)
        db.commit()
        db.refresh(item)
        return item


@router.put("/movies/{item_id}", response_model=MovieOut)
def update_movie(item_id: int, payload: MovieUpdate, _: bool = require_admin) -> Movie:
    with SessionLocal() as db:
        item = db.get(Movie, item_id)
        if item is None:
            raise HTTPException(status_code=404, detail="电影不存在")
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(item, field, value)
        db.commit()
        db.refresh(item)
        return item


# --------------------- 电影：候选片打分与清理 ---------------------
# 候选片（status='candidate'）是「别人推荐、我还没看」的片子。站长看完之后
# 在这里打分，片子就从候选转正成正式档案；不看的直接删。
# 这一组只动 candidate，绝不碰 watched 的正式档案。


class RateIn(BaseModel):
    """给候选片打分并转正。只暴露「评价」相关的字段，资料字段由 TMDB 提供。"""

    rating: float = Field(default=7.0, ge=0, le=10)
    scare_level: int = Field(default=3, ge=0, le=5)
    recommend_level: int = Field(default=3, ge=0, le=5)
    verdict: str = Field(default="", max_length=300)
    watched_at: str = Field(default="", max_length=20)
    category_id: int | None = None
    tags: list | None = None


@router.post("/movies/{item_id}/rate", response_model=MovieOut)
def rate_movie(item_id: int, payload: RateIn, _: bool = require_admin) -> Movie:
    """打分 = 看过 = 转正。候选片打完分就进正式档案。"""
    with SessionLocal() as db:
        item = db.get(Movie, item_id)
        if item is None:
            raise HTTPException(status_code=404, detail="电影不存在")
        item.rating = payload.rating
        item.scare_level = payload.scare_level
        item.recommend_level = payload.recommend_level
        item.verdict = payload.verdict
        item.watched_at = payload.watched_at or datetime.now().strftime("%Y-%m-%d")
        if payload.category_id is not None:
            item.category_id = payload.category_id or None
        if payload.tags is not None:
            # 转正后不该再挂着「候选」这个标签
            item.tags = [t for t in payload.tags if t != "候选"]
        else:
            item.tags = [t for t in (item.tags or []) if t != "候选"]
        item.status = "watched"
        db.commit()
        db.refresh(item)
        return item


@router.delete("/movies/candidates", response_model=OkOut)
def purge_candidates(
    keep_rated: bool = Query(
        default=True,
        description="true 只删没打过分（rating=0）的候选；false 全删。",
    ),
    _: bool = require_admin,
) -> OkOut:
    """清掉候选片。默认保留已打分的，避免误删刚看完的那几部。"""
    with SessionLocal() as db:
        stmt = select(Movie).where(Movie.status == "candidate")
        if keep_rated:
            stmt = stmt.where(Movie.rating == 0)
        doomed = list(db.scalars(stmt).all())
        titles = [m.title for m in doomed]
        for m in doomed:
            db.delete(m)
        db.commit()
        if not titles:
            return OkOut(message="没有需要清理的候选片")
        return OkOut(message=f"已清理 {len(titles)} 部候选片：{'、'.join(titles[:5])}"
                             + ("…" if len(titles) > 5 else ""))


# --------------------- 电影：从 TMDB 导入 ---------------------
# 这一组的意义：把「找海报、写简介、抄年份导演」这些体力活交给 TMDB，
# 自己只留下评分、恐怖强度、长评这些真正属于看法的内容。


@router.get("/tmdb/search", response_model=TmdbSearchOut)
async def tmdb_search(
    q: str = "", year: int | None = None, page: int = 1, _: bool = require_admin
) -> TmdbSearchOut:
    """按片名搜索。key 没配时返回 configured=false，后台据此引导去申请。"""
    if not tmdb.configured():
        return TmdbSearchOut(configured=False, attribution=tmdb.ATTRIBUTION)
    try:
        data = await tmdb.search_movies(q, year=year, page=page)
    except tmdb.TmdbError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return TmdbSearchOut(**data, configured=True, attribution=tmdb.ATTRIBUTION)


@router.get("/tmdb/discover", response_model=TmdbSearchOut)
async def tmdb_discover(
    page: int = 1,
    sort_by: str = "popularity.desc",
    min_vote_count: int = 100,
    year_from: int | None = None,
    year_to: int | None = None,
    _: bool = require_admin,
) -> TmdbSearchOut:
    """恐怖片片库浏览 —— 「所有沾边恐怖的内容」的入口。

    min_vote_count 默认 100，否则前几页全是零评分的条目，翻起来毫无意义。
    """
    if not tmdb.configured():
        return TmdbSearchOut(configured=False, attribution=tmdb.ATTRIBUTION)
    try:
        data = await tmdb.discover_horror(
            page=page,
            sort_by=sort_by,
            min_vote_count=min_vote_count,
            year_from=year_from,
            year_to=year_to,
        )
    except tmdb.TmdbError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return TmdbSearchOut(**data, configured=True, attribution=tmdb.ATTRIBUTION)


@router.post("/movies/from-tmdb", response_model=MovieOut)
async def create_movie_from_tmdb(
    payload: MovieFromTmdb, _: bool = require_admin
) -> Movie:
    """一键建档：抓 TMDB 详情填元数据，评价字段按传进来的写（可留空）。"""
    try:
        info = await tmdb.movie_detail(payload.tmdb_id)
    except tmdb.TmdbError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    with SessionLocal() as db:
        # 同一部片只建一次，重复点导入会提示而不是静默建第二条
        exists = (
            db.query(Movie).filter(Movie.tmdb_id == payload.tmdb_id).one_or_none()
        )
        if exists is not None:
            raise HTTPException(
                status_code=409, detail=f"《{exists.title}》已经在库里了"
            )
        item = Movie(
            title=info.get("title") or "未命名",
            original_title=info.get("original_title") or "",
            year=info.get("year") or 2000,
            director=info.get("director") or "",
            country=info.get("country") or "",
            # 只存相对路径，不下载图片：这就是磁盘占用为 0 的原因
            poster_path=info.get("poster_path") or "",
            backdrop_path=info.get("backdrop_path") or "",
            overview=info.get("overview") or "",
            runtime=info.get("runtime") or 0,
            tmdb_rating=info.get("tmdb_rating") or 0,
            genres=info.get("genres") or [],
            tmdb_id=payload.tmdb_id,
            category_id=payload.category_id,
            rating=payload.rating,
            scare_level=payload.scare_level,
            recommend_level=payload.recommend_level,
            watched_at=payload.watched_at,
            verdict=payload.verdict,
            review=payload.review,
            tags=[g.get("name") for g in (info.get("genres") or [])][:4],
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item


@router.delete("/movies/{item_id}", response_model=OkOut)
def delete_movie(item_id: int, _: bool = require_admin) -> OkOut:
    with SessionLocal() as db:
        item = db.get(Movie, item_id)
        if item is None:
            raise HTTPException(status_code=404, detail="电影不存在")
        db.delete(item)
        db.commit()
        return OkOut(message="已删除该电影")


# --------------------------- 成长路径 ---------------------------


@router.get("/journey", response_model=list[JourneyStepOut])
def admin_list_journey(_: bool = require_admin) -> list[JourneyStep]:
    with SessionLocal() as db:
        return list(
            db.query(JourneyStep).order_by(JourneyStep.sort_order, JourneyStep.id)
        )


@router.post("/journey", response_model=JourneyStepOut)
def create_journey(payload: JourneyStepCreate, _: bool = require_admin) -> JourneyStep:
    with SessionLocal() as db:
        item = JourneyStep(**payload.model_dump())
        db.add(item)
        db.commit()
        db.refresh(item)
        return item


@router.put("/journey/{item_id}", response_model=JourneyStepOut)
def update_journey(
    item_id: int, payload: JourneyStepUpdate, _: bool = require_admin
) -> JourneyStep:
    with SessionLocal() as db:
        item = db.get(JourneyStep, item_id)
        if item is None:
            raise HTTPException(status_code=404, detail="这一步不存在")
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(item, field, value)
        db.commit()
        db.refresh(item)
        return item


@router.delete("/journey/{item_id}", response_model=OkOut)
def delete_journey(item_id: int, _: bool = require_admin) -> OkOut:
    with SessionLocal() as db:
        item = db.get(JourneyStep, item_id)
        if item is None:
            raise HTTPException(status_code=404, detail="这一步不存在")
        db.delete(item)
        db.commit()
        return OkOut(message="已删除这一步")


@router.post("/works/suggest-tags", response_model=TagSuggestOut)
def suggest_work_tags(payload: WorkTagSuggest, _: bool = require_admin) -> TagSuggestOut:
    """按规则推断风格标签。只给候选，写不写由站长点一下决定。"""
    styles = suggest_style_tags(
        title=payload.title,
        summary=payload.summary,
        notes=payload.notes,
        bpm=payload.bpm,
        key_signature=payload.key_signature,
        progress=payload.progress,
        existing=payload.tags,
    )
    return TagSuggestOut(styles=styles, adopted=list(payload.tags))


# --------------------------- 页面区块 ---------------------------


@router.get("/page-sections", response_model=list[PageSectionOut])
def admin_list_page_sections(_: bool = require_admin) -> list[PageSection]:
    """列出全部区块，顺便把注册表里缺的补上（前台新增区块后老库也能自动出现）。"""
    with SessionLocal() as db:
        ensure_default_page_sections(db)
        return list(
            db.scalars(
                select(PageSection).order_by(
                    PageSection.page, PageSection.sort_order, PageSection.id
                )
            )
        )


@router.post("/page-sections", response_model=PageSectionOut)
def create_page_section(
    payload: PageSectionCreate, _: bool = require_admin
) -> PageSection:
    with SessionLocal() as db:
        exists = db.scalar(
            select(PageSection).where(
                PageSection.page == payload.page, PageSection.key == payload.key
            )
        )
        if exists is not None:
            raise HTTPException(status_code=400, detail="这个区块已经存在了")
        data = payload.model_dump()
        data["title"] = data.get("title") or payload.key
        item = PageSection(**data)
        db.add(item)
        db.commit()
        db.refresh(item)
        return item


@router.put("/page-sections/{item_id}", response_model=PageSectionOut)
def update_page_section(
    item_id: int, payload: PageSectionUpdate, _: bool = require_admin
) -> PageSection:
    with SessionLocal() as db:
        item = db.get(PageSection, item_id)
        if item is None:
            raise HTTPException(status_code=404, detail="这个区块不存在")
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(item, field, value)
        db.commit()
        db.refresh(item)
        return item


@router.delete("/page-sections/{item_id}", response_model=OkOut)
def delete_page_section(item_id: int, _: bool = require_admin) -> OkOut:
    """真删除：前台不再渲染这个区块。想恢复用下面的 reset。"""
    with SessionLocal() as db:
        item = db.get(PageSection, item_id)
        if item is None:
            raise HTTPException(status_code=404, detail="这个区块不存在")
        db.delete(item)
        db.commit()
        return OkOut(message="已删除这个区块")


@router.post("/page-sections/reset", response_model=OkOut)
def reset_page_section(payload: PageSectionReset, _: bool = require_admin) -> OkOut:
    """把某一页的区块恢复成注册表里的默认状态（清掉这一页的全部自定义）。"""
    count = 0
    with SessionLocal() as db:
        count = reset_page_sections(db, payload.page)
    return OkOut(message=f"已恢复 {len(DEFAULT_SECTIONS.get(payload.page, []))} 个默认区块（写入 {count} 条）")


# ------------------------------ Work ------------------------------


@router.get("/works", response_model=list[WorkOut])
def admin_list_works(_: bool = require_admin) -> list[Work]:
    with SessionLocal() as db:
        return list(db.query(Work).order_by(Work.sort_order, Work.id))


@router.post("/works", response_model=WorkOut)
def create_work(payload: WorkCreate, _: bool = require_admin) -> Work:
    with SessionLocal() as db:
        item = Work(**payload.model_dump())
        db.add(item)
        db.commit()
        db.refresh(item)
        return item


@router.put("/works/{item_id}", response_model=WorkOut)
def update_work(item_id: int, payload: WorkUpdate, _: bool = require_admin) -> Work:
    with SessionLocal() as db:
        item = db.get(Work, item_id)
        if item is None:
            raise HTTPException(status_code=404, detail="作品不存在")
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(item, field, value)
        db.commit()
        db.refresh(item)
        return item


@router.get("/works/analyze/status")
def audio_analysis_status(_: bool = require_admin) -> dict:
    """告诉后台「能不能自动分析」。缺依赖时前端要把按钮按掉，别让站长白点。"""
    ok, engine = available()
    return {"available": ok, "engine": engine}


@router.post("/works/{item_id}/analyze", response_model=WorkOut)
def analyze_work(item_id: int, _: bool = require_admin) -> Work:
    """对这个作品的音频跑一遍分析，结果写进 work.analysis。

    只补不覆盖 composer 已经手写的部分：BPM 和调性原来为空才自动填。
    分析要好几秒，失败一律用 400 把原因原话说回去。
    """
    with SessionLocal() as db:
        item = db.get(Work, item_id)
        if item is None:
            raise HTTPException(status_code=404, detail="作品不存在")
        audio_url = item.audio_url
        had_bpm = item.bpm
        had_key = item.key_signature

    try:
        result = analyze_work_audio(audio_url)
    except AudioAnalysisError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:  # librosa 内部炸了也要说人话
        raise HTTPException(status_code=400, detail=f"分析失败：{exc}")

    with SessionLocal() as db:
        item = db.get(Work, item_id)
        item.analysis = result
        if not had_bpm and result.get("bpm"):
            item.bpm = int(result["bpm"])
        if not had_key and result.get("key"):
            item.key_signature = result["key"]
        if result.get("duration"):
            item.audio_duration = int(round(result["duration"]))
        db.commit()
        db.refresh(item)
        return item


@router.delete("/works/{item_id}", response_model=OkOut)
def delete_work(item_id: int, _: bool = require_admin) -> OkOut:
    with SessionLocal() as db:
        item = db.get(Work, item_id)
        if item is None:
            raise HTTPException(status_code=404, detail="作品不存在")
        db.delete(item)
        db.commit()
        return OkOut(message="已删除该作品")


# ------------------------------ Resume ------------------------------


@router.get("/resume", response_model=list[ResumeItemOut])
def admin_list_resume(_: bool = require_admin) -> list[ResumeItem]:
    with SessionLocal() as db:
        return list(
            db.query(ResumeItem).order_by(ResumeItem.sort_order, ResumeItem.id)
        )


@router.post("/resume", response_model=ResumeItemOut)
def create_resume(payload: ResumeItemCreate, _: bool = require_admin) -> ResumeItem:
    with SessionLocal() as db:
        item = ResumeItem(**payload.model_dump())
        db.add(item)
        db.commit()
        db.refresh(item)
        return item


@router.put("/resume/{item_id}", response_model=ResumeItemOut)
def update_resume(
    item_id: int, payload: ResumeItemUpdate, _: bool = require_admin
) -> ResumeItem:
    with SessionLocal() as db:
        item = db.get(ResumeItem, item_id)
        if item is None:
            raise HTTPException(status_code=404, detail="简历条目不存在")
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(item, field, value)
        db.commit()
        db.refresh(item)
        return item


@router.delete("/resume/{item_id}", response_model=OkOut)
def delete_resume(item_id: int, _: bool = require_admin) -> OkOut:
    with SessionLocal() as db:
        item = db.get(ResumeItem, item_id)
        if item is None:
            raise HTTPException(status_code=404, detail="简历条目不存在")
        db.delete(item)
        db.commit()
        return OkOut(message="已删除")


# ------------------------------ Skill ------------------------------


@router.get("/skills", response_model=list[SkillItemOut])
def admin_list_skills(_: bool = require_admin) -> list[SkillItem]:
    with SessionLocal() as db:
        return list(db.query(SkillItem).order_by(SkillItem.sort_order, SkillItem.id))


@router.post("/skills", response_model=SkillItemOut)
def create_skill(payload: SkillItemCreate, _: bool = require_admin) -> SkillItem:
    with SessionLocal() as db:
        item = SkillItem(**payload.model_dump())
        db.add(item)
        db.commit()
        db.refresh(item)
        return item


@router.put("/skills/{item_id}", response_model=SkillItemOut)
def update_skill(
    item_id: int, payload: SkillItemUpdate, _: bool = require_admin
) -> SkillItem:
    with SessionLocal() as db:
        item = db.get(SkillItem, item_id)
        if item is None:
            raise HTTPException(status_code=404, detail="技能不存在")
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(item, field, value)
        db.commit()
        db.refresh(item)
        return item


@router.delete("/skills/{item_id}", response_model=OkOut)
def delete_skill(item_id: int, _: bool = require_admin) -> OkOut:
    with SessionLocal() as db:
        item = db.get(SkillItem, item_id)
        if item is None:
            raise HTTPException(status_code=404, detail="技能不存在")
        db.delete(item)
        db.commit()
        return OkOut(message="已删除")


# ------------------------------ 图片上传 ------------------------------


def _looks_like_image(head: bytes, ext: str) -> bool:
    """按文件头判断真实类型，不信客户端给的内容类型。"""
    if len(head) < 12:
        return False
    if ext in (".jpg", ".jpeg"):
        return head[:3] == b"\xff\xd8\xff"
    if ext == ".png":
        return head[:8] == b"\x89PNG\r\n\x1a\n"
    if ext == ".gif":
        return head[:6] in (b"GIF87a", b"GIF89a")
    if ext == ".webp":
        return head[:4] == b"RIFF" and head[8:12] == b"WEBP"
    if ext == ".avif":
        # ISO-BMFF：brand 从第 4 字节开始
        return head[4:8] == b"ftyp"
    return False


@router.post("/upload", response_model=UploadOut)
def upload_image(
    file: UploadFile = File(...), _: bool = require_admin
) -> UploadOut:
    """上传一张图片，返回可直接填进 poster / cover / avatar 的 URL。

    存到 static/uploads/<年月>/<随机名>.<扩展名>：随机名避免覆盖与路径穿越，
    按月分目录便于日后清理和备份。
    """
    original = file.filename or ""
    ext = Path(original).suffix.lower()
    if ext not in ALLOWED_IMAGE_EXT:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的格式 {ext or '（无扩展名）'}，只收 {', '.join(ALLOWED_IMAGE_EXT)}",
        )

    # 多读一个字节来判断是否超限，避免把超大文件整个读进内存
    data = file.file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"图片太大了，上限 {MAX_UPLOAD_BYTES // 1024 // 1024}MB",
        )
    if not _looks_like_image(data, ext):
        raise HTTPException(status_code=400, detail="文件头和图片格式对不上，可能被改过扩展名")

    folder = UPLOAD_DIR / datetime.now().strftime("%Y-%m")
    folder.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4().hex}{ext}"
    (folder / filename).write_bytes(data)

    return UploadOut(
        url=f"/uploads/{folder.name}/{filename}",
        filename=original,
        size=len(data),
    )


def _looks_like_audio(head: bytes, ext: str) -> bool:
    """音频文件头校验。和图片一样，不信客户端给的 Content-Type。"""
    if len(head) < 12:
        return False
    if ext == ".mp3":
        # 有 ID3 标签的直接过；裸帧则看 MPEG 帧同步字
        return head[:3] == b"ID3" or (
            head[0] == 0xFF and (head[1] & 0xE0) == 0xE0
        )
    if ext == ".wav":
        return head[:4] == b"RIFF" and head[8:12] == b"WAVE"
    if ext in (".ogg", ".oga"):
        return head[:4] == b"OggS"
    if ext == ".flac":
        return head[:4] == b"fLaC"
    if ext in (".m4a", ".aac"):
        # ISO-BMFF 容器，第 4 字节起是 ftyp
        return head[4:8] == b"ftyp"
    return False


@router.post("/upload-audio", response_model=UploadOut)
def upload_audio(file: UploadFile = File(...), _: bool = require_admin) -> UploadOut:
    """上传一段音频，返回可直接填进 audio_url 的地址。

    音频不像海报能外链 CDN —— 自己写的曲子没有现成托管，必须落盘。
    所以这里的防线和图片一样严：扩展名白名单 + 文件头校验 + 体积上限。
    """
    original = file.filename or ""
    ext = Path(original).suffix.lower()
    if ext not in ALLOWED_AUDIO_EXT:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的音频格式 {ext or '（无扩展名）'}，只收 {', '.join(ALLOWED_AUDIO_EXT)}",
        )

    data = file.file.read(MAX_AUDIO_BYTES + 1)
    if len(data) > MAX_AUDIO_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"音频太大了，上限 {MAX_AUDIO_BYTES // 1024 // 1024}MB",
        )
    if not _looks_like_audio(data, ext):
        raise HTTPException(status_code=400, detail="文件头和音频格式对不上，可能被改过扩展名")

    folder = UPLOAD_DIR / datetime.now().strftime("%Y-%m")
    folder.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4().hex}{ext}"
    (folder / filename).write_bytes(data)

    return UploadOut(
        url=f"/uploads/{folder.name}/{filename}",
        filename=original,
        size=len(data),
        kind="audio",
    )
