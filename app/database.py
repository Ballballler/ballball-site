"""数据库引擎与会话管理。"""
from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import DATABASE_URL


class Base(DeclarativeBase):
    """所有 ORM 模型的基类。"""


_is_sqlite = DATABASE_URL.startswith("sqlite")

# check_same_thread=False 是 SQLite + 多线程 WSGI/ASGI 服务的必要开关
engine = create_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    connect_args={"check_same_thread": False} if _is_sqlite else {},
)


if _is_sqlite:
    @event.listens_for(engine, "connect")
    def _sqlite_pragmas(dbapi_conn, _record):  # pragma: no cover - 驱动回调
        """打开外键约束与 WAL，避免并发读写时锁死。"""
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.execute("PRAGMA journal_mode=WAL")
        cur.execute("PRAGMA synchronous=NORMAL")
        cur.close()


SessionLocal = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """FastAPI 依赖项：请求级会话，结束后自动关闭。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 后加的列。create_all 只建表、不补列，已有库要靠这里升级。
# 值：表名 -> {列名: 列定义}。SQLite 的 ADD COLUMN 必须带默认值。
_EXTRA_COLUMNS: dict[str, dict[str, str]] = {
    # 电影：TMDB 元数据。只存图片相对路径与文本，不落图片文件，磁盘占用为 0。
    "movie": {
        "tmdb_id": "INTEGER",
        "poster_path": "TEXT DEFAULT ''",
        "backdrop_path": "TEXT DEFAULT ''",
        "overview": "TEXT DEFAULT ''",
        "runtime": "INTEGER DEFAULT 0",
        "tmdb_rating": "FLOAT DEFAULT 0",
        "genres": "TEXT DEFAULT '[]'",
        # 候选片标记。老库里的行全是「看过」，所以默认 watched 正好对。
        "status": "TEXT DEFAULT 'watched' NOT NULL",
    },
    # 作品：音频上传后的元信息与下载开关
    "work": {
        "audio_size": "INTEGER DEFAULT 0",
        "audio_duration": "INTEGER DEFAULT 0",
        "allow_download": "BOOLEAN DEFAULT 1 NOT NULL",
        # 音频自动分析快照（JSON）
        "analysis": "TEXT DEFAULT '{}'",
    },
}


def ensure_extra_columns() -> list[str]:
    """补齐后加的列，返回实际新增的「表.列」列表（幂等，重复调用无副作用）。"""
    added: list[str] = []
    if not _is_sqlite:
        return added
    with engine.begin() as conn:
        for table, columns in _EXTRA_COLUMNS.items():
            existing = {
                row[1] for row in conn.execute(text(f"PRAGMA table_info('{table}')"))
            }
            for column, ddl in columns.items():
                if column in existing:
                    continue
                conn.execute(text(f'ALTER TABLE {table} ADD COLUMN {column} {ddl}'))
                added.append(f"{table}.{column}")
    return added
