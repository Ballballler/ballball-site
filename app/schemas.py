"""Pydantic 请求 / 响应模型。

约定：
- 写操作（Create/Update）字段全部可选或带默认值，后台表单不需要填满；
- 读操作（Out）统一 from_attributes=True，直接吃 ORM 对象；
- 所有字符串做长度与空白校验，防止后台误填或恶意灌入超长内容。
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

CategoryKind = Literal["movie_genre", "work_type", "interest", "skill"]
WorkStatus = Literal["idea", "demo", "released"]


def _clean(v: str | None) -> str | None:
    if isinstance(v, str):
        return v.strip()
    return v


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ----------------------------- Profile -----------------------------


class ProfileOut(ORMModel):
    id: int
    name: str
    headline: str
    tagline: str
    avatar: str
    bio: str
    location: str
    email: str
    links: list = []
    highlights: list = []
    updated_at: datetime


class ProfileUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=80)
    headline: str | None = Field(default=None, max_length=160)
    tagline: str | None = None
    avatar: str | None = Field(default=None, max_length=500)
    bio: str | None = None
    location: str | None = Field(default=None, max_length=80)
    email: str | None = Field(default=None, max_length=120)
    links: list | None = None
    highlights: list | None = None


# ----------------------------- Category -----------------------------


class CategoryOut(ORMModel):
    id: int
    kind: str
    name: str
    slug: str
    color: str
    description: str
    sort_order: int
    created_at: datetime


class CategoryCreate(BaseModel):
    kind: CategoryKind = "movie_genre"
    name: str = Field(min_length=1, max_length=60)
    slug: str = Field(default="", max_length=80)
    color: str = Field(default="#38bdf8", max_length=20)
    description: str = ""
    sort_order: int = 0

    @field_validator("name", mode="before")
    @classmethod
    def _strip_name(cls, v: str) -> str:
        v = (v or "").strip()
        if not v:
            raise ValueError("分类名称不能为空")
        return v


class CategoryUpdate(BaseModel):
    kind: CategoryKind | None = None
    name: str | None = Field(default=None, max_length=60)
    slug: str | None = Field(default=None, max_length=80)
    color: str | None = Field(default=None, max_length=20)
    description: str | None = None
    sort_order: int | None = None


# ----------------------------- Interest -----------------------------


class InterestOut(ORMModel):
    id: int
    title: str
    icon: str
    description: str
    link: str
    accent: str
    sort_order: int


class InterestCreate(BaseModel):
    title: str = Field(min_length=1, max_length=60)
    icon: str = Field(default="✨", max_length=16)
    description: str = ""
    link: str = Field(default="", max_length=300)
    accent: str = Field(default="#a78bfa", max_length=20)
    sort_order: int = 0

    @field_validator("title", mode="before")
    @classmethod
    def _strip_title(cls, v: str) -> str:
        v = (v or "").strip()
        if not v:
            raise ValueError("兴趣标题不能为空")
        return v


class InterestUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=60)
    icon: str | None = Field(default=None, max_length=16)
    description: str | None = None
    link: str | None = Field(default=None, max_length=300)
    accent: str | None = Field(default=None, max_length=20)
    sort_order: int | None = None


# ----------------------------- Movie -----------------------------


class MovieOut(ORMModel):
    id: int
    title: str
    original_title: str
    year: int
    director: str
    country: str
    poster: str
    # TMDB 元数据（图片只存相对路径，渲染时拼 CDN）
    tmdb_id: int | None = None
    poster_path: str = ""
    backdrop_path: str = ""
    overview: str = ""
    runtime: int = 0
    tmdb_rating: float = 0
    genres: list = []
    # 派生字段，不入库：拼好的海报 URL，前端拿去直接用
    poster_url: str = ""
    backdrop_url: str = ""
    rating: float
    verdict: str
    review: str
    scare_level: int
    recommend_level: int
    category_id: int | None
    category: CategoryOut | None = None
    tags: list = []
    watched_at: str
    # watched = 看过并写进档案；candidate = 候选片（还没看，留着打分做记号）
    status: str = "watched"
    sort_order: int
    created_at: datetime
    updated_at: datetime


class MovieBrief(ORMModel):
    """列表接口：不带长评正文，减少传输量。"""

    id: int
    title: str
    original_title: str
    year: int
    director: str
    country: str
    poster: str
    tmdb_id: int | None = None
    poster_path: str = ""
    backdrop_path: str = ""
    overview: str = ""
    runtime: int = 0
    tmdb_rating: float = 0
    genres: list = []
    poster_url: str = ""
    rating: float
    verdict: str
    scare_level: int
    recommend_level: int
    category_id: int | None
    category: CategoryOut | None = None
    tags: list = []
    watched_at: str
    status: str = "watched"
    sort_order: int


class MovieCreate(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    original_title: str = Field(default="", max_length=160)
    year: int = Field(default=2000, ge=1900, le=2100)
    director: str = Field(default="", max_length=120)
    country: str = Field(default="", max_length=60)
    poster: str = Field(default="", max_length=500)
    tmdb_id: int | None = None
    poster_path: str = Field(default="", max_length=300)
    backdrop_path: str = Field(default="", max_length=300)
    overview: str = ""
    runtime: int = Field(default=0, ge=0, le=1000)
    tmdb_rating: float = Field(default=0, ge=0, le=10)
    genres: list = []
    rating: float = Field(default=7.0, ge=0, le=10)
    verdict: str = ""
    review: str = ""
    scare_level: int = Field(default=3, ge=0, le=5)
    recommend_level: int = Field(default=3, ge=0, le=5)
    category_id: int | None = None
    tags: list = []
    watched_at: str = Field(default="", max_length=20)
    status: str = Field(default="watched", pattern="^(watched|candidate)$")
    sort_order: int = 0

    @field_validator("title", mode="before")
    @classmethod
    def _strip_title(cls, v: str) -> str:
        v = (v or "").strip()
        if not v:
            raise ValueError("电影标题不能为空")
        return v


class MovieUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=160)
    original_title: str | None = Field(default=None, max_length=160)
    year: int | None = Field(default=None, ge=1900, le=2100)
    director: str | None = Field(default=None, max_length=120)
    country: str | None = Field(default=None, max_length=60)
    poster: str | None = Field(default=None, max_length=500)
    tmdb_id: int | None = None
    poster_path: str | None = Field(default=None, max_length=300)
    backdrop_path: str | None = Field(default=None, max_length=300)
    overview: str | None = None
    runtime: int | None = Field(default=None, ge=0, le=1000)
    tmdb_rating: float | None = Field(default=None, ge=0, le=10)
    genres: list | None = None
    rating: float | None = Field(default=None, ge=0, le=10)
    verdict: str | None = None
    review: str | None = None
    scare_level: int | None = Field(default=None, ge=0, le=5)
    recommend_level: int | None = Field(default=None, ge=0, le=5)
    category_id: int | None = None
    tags: list | None = None
    watched_at: str | None = Field(default=None, max_length=20)
    status: str | None = Field(default=None, pattern="^(watched|candidate)$")
    sort_order: int | None = None


# ----------------------------- Work -----------------------------


class WorkOut(ORMModel):
    id: int
    title: str
    kind: str
    status: WorkStatus
    summary: str
    notes: str
    cover: str
    audio_url: str
    audio_size: int = 0
    audio_duration: int = 0
    allow_download: bool = True
    bpm: int
    key_signature: str
    # 自动分析快照。没跑过是 {}，前端据此显示「还没分析」
    analysis: dict = Field(default_factory=dict)
    category_id: int | None
    category: CategoryOut | None = None
    tags: list = []
    progress: int
    sort_order: int
    created_at: datetime
    updated_at: datetime


class WorkCreate(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    kind: str = Field(default="music", max_length=32)
    status: WorkStatus = "idea"
    summary: str = ""
    notes: str = ""
    cover: str = Field(default="", max_length=500)
    audio_url: str = Field(default="", max_length=500)
    audio_size: int = Field(default=0, ge=0)
    audio_duration: int = Field(default=0, ge=0)
    allow_download: bool = True
    bpm: int = Field(default=0, ge=0, le=300)
    key_signature: str = Field(default="", max_length=20)
    category_id: int | None = None
    tags: list = []
    progress: int = Field(default=0, ge=0, le=100)
    sort_order: int = 0

    @field_validator("title", mode="before")
    @classmethod
    def _strip_title(cls, v: str) -> str:
        v = (v or "").strip()
        if not v:
            raise ValueError("作品标题不能为空")
        return v


class WorkUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=160)
    kind: str | None = Field(default=None, max_length=32)
    status: WorkStatus | None = None
    summary: str | None = None
    notes: str | None = None
    cover: str | None = Field(default=None, max_length=500)
    audio_url: str | None = Field(default=None, max_length=500)
    audio_size: int | None = Field(default=None, ge=0)
    audio_duration: int | None = Field(default=None, ge=0)
    allow_download: bool | None = None
    bpm: int | None = Field(default=None, ge=0, le=300)
    key_signature: str | None = Field(default=None, max_length=20)
    category_id: int | None = None
    tags: list | None = None
    progress: int | None = Field(default=None, ge=0, le=100)
    sort_order: int | None = None


# ----------------------------- Resume -----------------------------


class ResumeItemOut(ORMModel):
    id: int
    kind: str
    title: str
    org: str
    role: str
    location: str
    start_date: str
    end_date: str
    current: bool
    summary: str
    highlights: list = []
    tags: list = []
    link: str
    sort_order: int


class ResumeItemCreate(BaseModel):
    kind: Literal["education", "work", "project", "award"] = "work"
    title: str = Field(min_length=1, max_length=160)
    org: str = Field(default="", max_length=160)
    role: str = Field(default="", max_length=120)
    location: str = Field(default="", max_length=80)
    start_date: str = Field(default="", max_length=20)
    end_date: str = Field(default="", max_length=20)
    current: bool = False
    summary: str = ""
    highlights: list = []
    tags: list = []
    link: str = Field(default="", max_length=500)
    sort_order: int = 0

    @field_validator("title", mode="before")
    @classmethod
    def _strip(cls, v: str) -> str:
        v = (v or "").strip()
        if not v:
            raise ValueError("标题不能为空")
        return v


class ResumeItemUpdate(BaseModel):
    kind: Literal["education", "work", "project", "award"] | None = None
    title: str | None = Field(default=None, max_length=160)
    org: str | None = Field(default=None, max_length=160)
    role: str | None = Field(default=None, max_length=120)
    location: str | None = Field(default=None, max_length=80)
    start_date: str | None = Field(default=None, max_length=20)
    end_date: str | None = Field(default=None, max_length=20)
    current: bool | None = None
    summary: str | None = None
    highlights: list | None = None
    tags: list | None = None
    link: str | None = Field(default=None, max_length=500)
    sort_order: int | None = None


# ----------------------------- 成长路径 -----------------------------

JourneyStage = Literal["start", "turn", "now", "next"]


class JourneyStepOut(ORMModel):
    id: int
    stage: str
    title: str
    when: str
    stuck: str
    action: str
    gained: str
    evidence: str
    link: str
    sort_order: int


class JourneyStepCreate(BaseModel):
    stage: JourneyStage = "turn"
    title: str = Field(min_length=1, max_length=160)
    when: str = Field(default="", max_length=40)
    stuck: str = ""
    action: str = ""
    gained: str = ""
    evidence: str = Field(default="", max_length=300)
    link: str = Field(default="", max_length=500)
    sort_order: int = 0

    @field_validator("title", mode="before")
    @classmethod
    def _strip(cls, v: str) -> str:
        v = (v or "").strip()
        if not v:
            raise ValueError("这一步的标题不能为空")
        return v


class JourneyStepUpdate(BaseModel):
    stage: JourneyStage | None = None
    title: str | None = Field(default=None, max_length=160)
    when: str | None = Field(default=None, max_length=40)
    stuck: str | None = None
    action: str | None = None
    gained: str | None = None
    evidence: str | None = Field(default=None, max_length=300)
    link: str | None = Field(default=None, max_length=500)
    sort_order: int | None = None


class SkillItemOut(ORMModel):
    id: int
    name: str
    level: int
    group: str
    color: str
    note: str
    sort_order: int


class SkillItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    level: int = Field(default=60, ge=0, le=100)
    group: str = Field(default="其他", max_length=60)
    color: str = Field(default="#22d3ee", max_length=20)
    note: str = Field(default="", max_length=200)
    sort_order: int = 0

    @field_validator("name", mode="before")
    @classmethod
    def _strip(cls, v: str) -> str:
        v = (v or "").strip()
        if not v:
            raise ValueError("技能名不能为空")
        return v


class SkillItemUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=60)
    level: int | None = Field(default=None, ge=0, le=100)
    group: str | None = Field(default=None, max_length=60)
    color: str | None = Field(default=None, max_length=20)
    note: str | None = Field(default=None, max_length=200)
    sort_order: int | None = None


# ----------------------------- Admin -----------------------------


class UploadOut(BaseModel):
    """后台上传的结果，url 直接写进 poster / cover / avatar / audio_url 字段。"""

    url: str
    filename: str
    size: int
    kind: str = "image"  # image / audio


# ----------------------------- TMDB -----------------------------


class TmdbResultItem(BaseModel):
    """TMDB 搜索结果里的一条。poster_url 已拼好，前端直接塞进 <img src>。"""

    tmdb_id: int | None = None
    title: str = ""
    original_title: str = ""
    year: int = 0
    overview: str = ""
    poster_path: str = ""
    poster_url: str = ""
    backdrop_url: str = ""
    tmdb_rating: float = 0
    vote_count: int = 0
    popularity: float = 0
    genres: list = []
    genre_ids: list = []
    director: str = ""
    country: str = ""
    runtime: int = 0
    tmdb_url: str = ""


class TmdbSearchOut(BaseModel):
    results: list[TmdbResultItem] = []
    page: int = 1
    total_pages: int = 0
    total_results: int = 0
    # 没配 key 时后台要提示去申请，而不是显示一个空列表让人以为是坏了
    configured: bool = True
    attribution: str = ""


class MovieFromTmdb(BaseModel):
    """从 TMDB 一键建档。

    元数据（海报 / 简介 / 年份 / 导演）由服务端抓；
    评价字段可选 —— 前台「看完 → 搜索 → 写评价 → 保存」会一次性带上，
    后台手动导入时留空，之后再补。
    """

    tmdb_id: int
    category_id: int | None = None
    rating: float = Field(default=7.0, ge=0, le=10)
    scare_level: int = Field(default=3, ge=0, le=5)
    recommend_level: int = Field(default=3, ge=0, le=5)
    watched_at: str = Field(default="", max_length=20)
    verdict: str = Field(default="", max_length=300)
    review: str = ""


PageKey = Literal["index", "resume", "movies", "works"]


class PageSectionOut(ORMModel):
    id: int
    page: str
    key: str
    title: str
    visible: bool
    sort_order: int


class PageSectionCreate(BaseModel):
    page: PageKey = "index"
    key: str = Field(min_length=1, max_length=40)
    title: str = Field(default="", max_length=80)
    visible: bool = True
    sort_order: int = 0

    @field_validator("key", mode="before")
    @classmethod
    def _clean_key(cls, v: str) -> str:
        v = (v or "").strip()
        if not v:
            raise ValueError("区块标识不能为空")
        return v


class PageSectionUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=80)
    visible: bool | None = None
    sort_order: int | None = None


class PageSectionReset(BaseModel):
    """恢复某一页的默认区块：先清掉这一页的配置，再按注册表重建。"""

    page: PageKey


class WorkTagSuggest(BaseModel):
    """给后台「推断风格标签」用：把作品当前填的字段原样发回来。"""

    title: str = Field(default="", max_length=200)
    summary: str = ""
    notes: str = ""
    bpm: int = Field(default=0, ge=0, le=400)
    key_signature: str = Field(default="", max_length=20)
    progress: int = Field(default=0, ge=0, le=100)
    tags: list[str] = []


class TagSuggestOut(BaseModel):
    """推断出的候选风格标签；adopted 是已经写进 tags 的。"""

    styles: list[str] = []
    adopted: list[str] = []


class LoginIn(BaseModel):
    password: str = Field(min_length=1, max_length=200)


class PasswordChange(BaseModel):
    old_password: str = Field(min_length=1, max_length=200)
    new_password: str = Field(min_length=6, max_length=200)


class OkOut(BaseModel):
    ok: bool = True
    message: str = ""


class StatsOut(BaseModel):
    movies: int = 0
    works: int = 0
    categories: int = 0
    interests: int = 0
    resume_items: int = 0
    skills: int = 0
    avg_rating: float = 0
    using_default_password: bool = False
