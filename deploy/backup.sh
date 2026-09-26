#!/usr/bin/env bash
# 备份 site.db、admin.json 与上传的图片，保留最近 30 份
# 用法：sudo ballball-backup
set -euo pipefail

APP_DIR="${APP_DIR:-/srv/ballball}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/ballball}"
KEEP="${KEEP:-30}"
STAMP="$(date +%Y%m%d-%H%M)"

mkdir -p "$BACKUP_DIR"

# SQLite 开了 WAL，先用 .backup 拿一份一致性快照，避免拷到半写状态
if command -v sqlite3 >/dev/null 2>&1; then
    sqlite3 "$APP_DIR/data/site.db" ".backup '$BACKUP_DIR/site-$STAMP.db'"
else
    cp "$APP_DIR/data/site.db" "$BACKUP_DIR/site-$STAMP.db"
fi

[ -f "$APP_DIR/data/admin.json" ] && cp "$APP_DIR/data/admin.json" "$BACKUP_DIR/admin-$STAMP.json"

# 上传的图片：数据库里只存路径，文件不备份的话页面会开天窗。
# 图片体积大、变化少，用增量同步：内容没变的文件不重复搬运。
UPLOADS="$APP_DIR/static/uploads"
if [ -d "$UPLOADS" ]; then
    if command -v rsync >/dev/null 2>&1; then
        rsync -a --delete "$UPLOADS/" "$BACKUP_DIR/uploads/"
    else
        # 没有 rsync 就整目录覆盖。图片一般是几百 KB 级，够用。
        rm -rf "$BACKUP_DIR/uploads"
        mkdir -p "$BACKUP_DIR/uploads"
        cp -R "$UPLOADS/." "$BACKUP_DIR/uploads/"
    fi
    echo "[backup] OK  uploads/（$(find "$BACKUP_DIR/uploads" -type f | wc -l) 个文件）"
fi

# 顺手检查一下备份是不是一个能打开的 SQLite 文件
if command -v sqlite3 >/dev/null 2>&1; then
    COUNT="$(sqlite3 "$BACKUP_DIR/site-$STAMP.db" 'SELECT count(*) FROM movie;' || echo -1)"
    if [ "$COUNT" = "-1" ]; then
        echo "[backup] 警告：备份文件校验失败" >&2
        exit 1
    fi
    echo "[backup] OK  site-$STAMP.db（movie 表 $COUNT 行）"
fi

# 清理旧备份
ls -1t "$BACKUP_DIR"/site-*.db 2>/dev/null | tail -n +$((KEEP + 1)) | xargs -r rm -f
ls -1t "$BACKUP_DIR"/admin-*.json 2>/dev/null | tail -n +$((KEEP + 1)) | xargs -r rm -f

echo "[backup] 完成：$BACKUP_DIR/site-$STAMP.db"
