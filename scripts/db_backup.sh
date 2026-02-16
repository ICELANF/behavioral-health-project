#!/usr/bin/env bash
# ============================================================================
# PostgreSQL 自动备份脚本
# 用法:
#   ./db_backup.sh              # 执行备份
#   ./db_backup.sh --restore <file>  # 恢复备份
#   ./db_backup.sh --list       # 列出可用备份
#   ./db_backup.sh --cleanup    # 清理过期备份
#
# 环境变量 (可覆盖):
#   DB_HOST, DB_PORT, DB_NAME, DB_USER, PGPASSWORD
#   BACKUP_DIR, BACKUP_RETENTION_DAYS
# ============================================================================

set -euo pipefail

# --------------- 配置 ---------------
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-bhp_db}"
DB_USER="${DB_USER:-bhp_user}"
BACKUP_DIR="${BACKUP_DIR:-./backups}"
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
BACKUP_FILE="$BACKUP_DIR/${DB_NAME}_${TIMESTAMP}.sql.gz"

# --------------- 辅助函数 ---------------
log_info()  { echo "[$(date '+%H:%M:%S')] INFO  $1"; }
log_error() { echo "[$(date '+%H:%M:%S')] ERROR $1" >&2; }
log_ok()    { echo "[$(date '+%H:%M:%S')] OK    $1"; }

check_pg_tools() {
    if ! command -v pg_dump &> /dev/null; then
        # 尝试通过 Docker 执行 (兼容多种容器名)
        PG_CONTAINER="${PG_CONTAINER:-}"
        for name in bhp_v3_postgres dify-db-1 postgres; do
            if docker exec "$name" pg_dump --version &> /dev/null 2>&1; then
                PG_CONTAINER="$name"
                break
            fi
        done
        if [[ -n "$PG_CONTAINER" ]]; then
            PG_VIA_DOCKER=true
            log_info "使用 Docker 容器 $PG_CONTAINER 内 pg_dump"
            return 0
        fi
        log_error "pg_dump 未安装且无可用 PostgreSQL Docker 容器"
        exit 1
    fi
    PG_VIA_DOCKER=false
}

do_pg_dump() {
    if [[ "$PG_VIA_DOCKER" == true ]]; then
        docker exec "$PG_CONTAINER" pg_dump -U "$DB_USER" -d "$DB_NAME" \
            --no-owner --no-privileges --clean --if-exists 2>/dev/null | gzip
    else
        PGPASSWORD="${PGPASSWORD:-bhp_password}" pg_dump \
            -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
            --no-owner --no-privileges --clean --if-exists 2>/dev/null | gzip
    fi
}

do_pg_restore() {
    local file="$1"
    if [[ "$PG_VIA_DOCKER" == true ]]; then
        gunzip -c "$file" | docker exec -i dify-db-1 psql -U "$DB_USER" -d "$DB_NAME" 2>/dev/null
    else
        PGPASSWORD="${PGPASSWORD:-bhp_password}" gunzip -c "$file" | \
            psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" 2>/dev/null
    fi
}

# --------------- 模式: list ---------------
if [[ "${1:-}" == "--list" ]]; then
    if [[ ! -d "$BACKUP_DIR" ]]; then
        echo "备份目录不存在: $BACKUP_DIR"
        exit 0
    fi
    echo "可用备份 ($BACKUP_DIR):"
    echo ""
    ls -lhS "$BACKUP_DIR"/${DB_NAME}_*.sql.gz 2>/dev/null || echo "  (无备份文件)"
    echo ""
    total=$(ls "$BACKUP_DIR"/${DB_NAME}_*.sql.gz 2>/dev/null | wc -l)
    echo "总计: $total 个备份"
    exit 0
fi

# --------------- 模式: cleanup ---------------
if [[ "${1:-}" == "--cleanup" ]]; then
    if [[ ! -d "$BACKUP_DIR" ]]; then
        echo "备份目录不存在"
        exit 0
    fi
    log_info "清理 $BACKUP_RETENTION_DAYS 天前的备份..."
    count=0
    while IFS= read -r f; do
        rm -f "$f"
        log_info "  已删除: $(basename "$f")"
        count=$((count + 1))
    done < <(find "$BACKUP_DIR" -name "${DB_NAME}_*.sql.gz" -mtime "+$BACKUP_RETENTION_DAYS" 2>/dev/null)
    log_ok "清理完成: 删除 $count 个过期备份"
    exit 0
fi

# --------------- 模式: restore ---------------
if [[ "${1:-}" == "--restore" ]]; then
    restore_file="${2:-}"
    if [[ -z "$restore_file" ]]; then
        log_error "用法: $0 --restore <backup_file.sql.gz>"
        exit 1
    fi
    if [[ ! -f "$restore_file" ]]; then
        log_error "文件不存在: $restore_file"
        exit 1
    fi

    check_pg_tools

    log_info "即将恢复数据库 $DB_NAME 从 $restore_file"
    echo "  !!! 此操作将覆盖当前数据库 !!!"
    read -p "  确认继续? (输入 YES): " confirm
    if [[ "$confirm" != "YES" ]]; then
        log_info "已取消"
        exit 0
    fi

    log_info "恢复中..."
    do_pg_restore "$restore_file"
    log_ok "数据库恢复完成"
    exit 0
fi

# --------------- 模式: backup (默认) ---------------
check_pg_tools

mkdir -p "$BACKUP_DIR"

log_info "开始备份 $DB_NAME → $BACKUP_FILE"

start_time=$(date +%s)
do_pg_dump > "$BACKUP_FILE"
end_time=$(date +%s)
duration=$((end_time - start_time))

if [[ -f "$BACKUP_FILE" ]]; then
    size=$(du -h "$BACKUP_FILE" | cut -f1)
    log_ok "备份完成: $BACKUP_FILE ($size, ${duration}秒)"

    # 自动清理过期备份
    expired=$(find "$BACKUP_DIR" -name "${DB_NAME}_*.sql.gz" -mtime "+$BACKUP_RETENTION_DAYS" 2>/dev/null | wc -l)
    if [[ "$expired" -gt 0 ]]; then
        log_info "发现 $expired 个过期备份，自动清理..."
        find "$BACKUP_DIR" -name "${DB_NAME}_*.sql.gz" -mtime "+$BACKUP_RETENTION_DAYS" -delete 2>/dev/null
        log_ok "过期备份已清理"
    fi

    # 统计
    total=$(ls "$BACKUP_DIR"/${DB_NAME}_*.sql.gz 2>/dev/null | wc -l)
    log_info "当前备份总数: $total (保留 ${BACKUP_RETENTION_DAYS} 天)"
else
    log_error "备份失败: 文件未生成"
    exit 1
fi
