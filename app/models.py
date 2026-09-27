"""ORM 模型。

设计原则：
1. 所有面向前台展示的内容都带 sort_order / created_at，后台可排序可归档；
2. 需要多值的轻量字段（标签、外链）用 JSON 列，避免为标签再开两张表。
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    JSON,
    ForeignKey,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def _utcnow() -> datetime:
    return datetime.utcnow()


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, onupdate=_utcnow, nullable=False
    )


class Profile(Base):
    """自我介绍。整站只维护 id=1 这一行。"""

    __tablename__ = "profile"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(80), default="Ballball", nullable=False)
    headline: Mapped[str] = mapped_column(
        String(160), default="把想法做成东西的人", nullable=False
    )
    tagline: Mapped[str] = mapped_column(
        Text, default="在恐怖片里找灵感，在音乐里找节奏。", nullable=False
    )
    avatar: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    bio: Mapped[str] = mapped_column(Text, default="", nullable=False)
    location: Mapped[str] = mapped_column(String(80), default="", nullable=False)
    email: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    # [{"label": "GitHub", "url": "https://..."}]
    links: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    # [{"icon": "🎬", "title": "恐怖电影", "text": "..."}]
    highlights: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, onupdate=_utcnow, nullable=False
    )


class Category(Base):
    """通用分类（细小分类）。用 kind 区分挂在哪个模块下。

    kind 取值：movie_genre / work_type / interest / skill
    """

    __tablename__ = "category"
    __table_args__ = (Index("ix_category_kind_sort", "kind", "sort_order"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kind: Mapped[str] = mapped_column(String(32), default="movie_genre", nullable=False)
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    slug: Mapped[str] = mapped_column(String(80), default="", nullable=False)
    color: Mapped[str] = mapped_column(String(20), default="#38bdf8", nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)

    movies: Mapped[list["Movie"]] = relationship(back_populates="category")
    works: Mapped[list["Work"]] = relationship(back_populates="category")


class Interest(Base, TimestampMixin):
    """兴趣爱好卡片（首页展示用，恐怖电影之外也可以有别的）。"""

    __tablename__ = "interest"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(60), nullable=False)
    icon: Mapped[str] = mapped_column(String(16), default="✨", nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    # 可跳转到站内页面，例如 /movies.html
    link: Mapped[str] = mapped_column(String(300), default="", nullable=False)
    accent: Mapped[str] = mapped_column(String(20), default="#a78bfa", nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class Movie(Base, TimestampMixin):
    """恐怖电影档案：基本信息 + 我自己的评分与长评。"""

    __tablename__ = "movie"
    __table_args__ = (Index("ix_movie_sort", "sort_order", "id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    original_title: Mapped[str] = mapped_column(String(160), default="", nullable=False)
    year: Mapped[int] = mapped_column(Integer, default=2000, nullable=False)
    director: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    country: Mapped[str] = mapped_column(String(60), default="", nullable=False)
    poster: Mapped[str] = mapped_column(String(500), default="", nullable=False)

    # ---------------- TMDB 元数据 ----------------
    # 只存相对路径（如 /kqjL17yufvn9OVLyXYpvtyrFfak.jpg），渲染时拼 TMDB 的 CDN 域名。
    # 这样全站「所有恐怖电影的海报」在本地占 0 字节。
    tmdb_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    poster_path: Mapped[str] = mapped_column(String(300), default="", nullable=False)
    backdrop_path: Mapped[str] = mapped_column(String(300), default="", nullable=False)
    # TMDB 官方简介，与自己写的 review 分开：overview 是资料，review 是观点
    overview: Mapped[str] = mapped_column(Text, default="", nullable=False)
    runtime: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tmdb_rating: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    # [{"id": 27, "name": "恐怖"}]
    genres: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    # 0 - 10，允许一位小数
    rating: Mapped[float] = mapped_column(Float, default=7.0, nullable=False)
    verdict: Mapped[str] = mapped_column(
        Text, default="", nullable=False
    )  # 一句话短评
    review: Mapped[str] = mapped_column(Text, default="", nullable=False)  # 长评正文
    # 恐怖强度 / 推荐指数，用于页面上的可视化条
    scare_level: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    recommend_level: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("category.id", ondelete="SET NULL"), nullable=True
    )
    tags: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    watched_at: Mapped[str] = mapped_column(String(20), default="", nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # selectin：查询时一并抓出分类，避免响应序列化时会话已关闭导致 DetachedInstanceError
    category: Mapped[Category | None] = relationship(
        back_populates="movies", lazy="selectin"
    )

    @property
    def poster_url(self) -> str:
        """渲染时真正用的海报地址。

        优先级：TMDB 相对路径（走 CDN，不占本地磁盘） > 手填的 poster > 空（前端给占位图）。
        """
        if self.poster_path:
            from .tmdb import image_url  # 局部导入，避免 models ↔ tmdb 循环依赖

            return image_url(self.poster_path, "w500")
        return self.poster or ""

    @property
    def backdrop_url(self) -> str:
        if self.backdrop_path:
            from .tmdb import image_url

            return image_url(self.backdrop_path, "w1280")
        return ""


class Work(Base, TimestampMixin):
    """作品。当前主要是「构思音乐」，结构预留给后续其他形态。"""

    __tablename__ = "work"
    __table_args__ = (Index("ix_work_sort", "sort_order", "id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    kind: Mapped[str] = mapped_column(String(32), default="music", nullable=False)
    # idea（构思中）/ demo（有小样）/ released（已完成）
    status: Mapped[str] = mapped_column(String(20), default="idea", nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)  # 创作笔记
    cover: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    audio_url: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    # 音频元信息：体积（字节）与时长（秒），用于前台显示与下载按钮
    audio_size: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    audio_duration: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # 是否允许访客下载。默认允许，自己的曲子想只放不放就关掉。
    allow_download: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    bpm: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    key_signature: Mapped[str] = mapped_column(String(20), default="", nullable=False)
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("category.id", ondelete="SET NULL"), nullable=True
    )
    tags: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    category: Mapped[Category | None] = relationship(
        back_populates="works", lazy="selectin"
    )


class ResumeItem(Base, TimestampMixin):
    """简历条目：教育 / 工作 / 项目 / 获奖，用 kind 区分，按时间轴展示。"""

    __tablename__ = "resume_item"
    __table_args__ = (Index("ix_resume_sort", "kind", "sort_order", "id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # education / work / project / award
    kind: Mapped[str] = mapped_column(String(20), default="work", nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    org: Mapped[str] = mapped_column(String(160), default="", nullable=False)
    role: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    location: Mapped[str] = mapped_column(String(80), default="", nullable=False)
    # 用字符串存，兼容「2021.09」「至今」这类写法
    start_date: Mapped[str] = mapped_column(String(20), default="", nullable=False)
    end_date: Mapped[str] = mapped_column(String(20), default="", nullable=False)
    current: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    # ["负责……", "主导……"]
    highlights: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    tags: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    link: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class JourneyStep(Base, TimestampMixin):
    """成长路径上的一步。

    简历页真正要讲的不是「我做过什么」，而是「我是怎么一步步走到这儿的」。
    所以每一步只记三件事：当时卡在哪、我怎么走的、走出来之后得到了什么。
    已有的履历（ResumeItem）退到下面做佐证，不是主角。
    """

    __tablename__ = "journey_step"
    __table_args__ = (Index("ix_journey_sort", "stage", "sort_order", "id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # start / turn / now / next —— 起点、转折、现在、下一步
    stage: Mapped[str] = mapped_column(String(20), default="turn", nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    # 自由写法：「2023 年春天」「去年冬天」，不强行套日期格式
    when: Mapped[str] = mapped_column(String(40), default="", nullable=False)
    # 当时卡住我的那件事，写具体，不要写「遇到困难」这种废话
    stuck: Mapped[str] = mapped_column(Text, default="", nullable=False)
    # 我实际做了什么
    action: Mapped[str] = mapped_column(Text, default="", nullable=False)
    # 走出来之后手里剩下的东西
    gained: Mapped[str] = mapped_column(Text, default="", nullable=False)
    # 佐证：一个链接，或者一段「可以拿给你看」的东西
    evidence: Mapped[str] = mapped_column(String(300), default="", nullable=False)
    link: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class SkillItem(Base, TimestampMixin):
    """技能条：带熟练度，同时喂给 3D 技能球。"""

    __tablename__ = "skill_item"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=60, nullable=False)  # 0-100
    group: Mapped[str] = mapped_column(String(60), default="其他", nullable=False)
    color: Mapped[str] = mapped_column(String(20), default="#22d3ee", nullable=False)
    note: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class PageSection(Base, TimestampMixin):
    """页面区块：前台某一页上的一块展示区域。

    后台可以隐藏（visible=False）、删除（整行没了，前台不再渲染）、排序（sort_order）。
    一个 page + key 唯一。key 是前台渲染时认的标识，改 key 等于换了一个区块。
    """

    __tablename__ = "page_section"
    __table_args__ = (
        UniqueConstraint("page", "key", name="uq_page_section"),
        Index("ix_page_section_sort", "page", "sort_order", "id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # index / resume / movies / works
    page: Mapped[str] = mapped_column(String(20), default="index", nullable=False)
    # about / resume-preview / journey / grid ...
    key: Mapped[str] = mapped_column(String(40), default="", nullable=False)
    # 后台列表里给人看的名字，不参与前台渲染
    title: Mapped[str] = mapped_column(String(80), default="", nullable=False)
    visible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
