#!/bin/bash
# Backup pgvector memories table to local storage
# Usage: ./backup_memories.sh

set -e

# Fix PATH for brew-installed tools (cron uses minimal PATH)
export PATH="/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/bin:/bin"

# Source DATABASE_URL from memory-pre-action hook's .env (has real credentials with sslmode)
source /dev/stdin <<<"$(grep DATABASE_URL ~/.openclaw/hooks/memory-pre-action/.env)"

# Configuration
LOCAL_BACKUP_DIR="$HOME/.openclaw/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="/tmp/memories_backup_${TIMESTAMP}.sql"
MAX_BACKUPS=10

echo "=== Backing up memories table ==="
echo "Timestamp: $TIMESTAMP"
echo "Database: $DB_NAME"

# Parse DATABASE_URL components
DB_HOST=$(echo $DATABASE_URL | sed 's/.*@\([^:]*\):.*/\u0001/')
DB_PORT=$(echo $DATABASE_URL | sed 's/.*:\([0-9]*\)\/.*/\u0001/')
DB_NAME=$(echo $DATABASE_URL | sed 's/.*\/\([^?]*\).*/\u0001/')
DB_USER=$(echo $DATABASE_URL | sed 's/.*:\/\([^:]*\):.*/\u0001/')
DB_PASS=$(echo $DATABASE_URL | sed 's/.*:\([^@]*\)@.*/\u0001/')

echo "Host: $DB_HOST:$DB_PORT"
echo "Database: $DB_NAME"
echo "User: $DB_USER"

# Create backup directory if it doesn't exist
mkdir -p "$LOCAL_BACKUP_DIR"

# Export memories table to SQL
echo "Exporting memories table..."
export PGPASSWORD="$DB_PASS"
pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t memories -f "$BACKUP_FILE"

# Compress backup
echo "Compressing..."
gzip "$BACKUP_FILE"
BACKUP_FILE="${BACKUP_FILE}.gz"
FINAL_BACKUP_PATH="${LOCAL_BACKUP_DIR}/memories_${TIMESTAMP}.sql.gz"

# Move to local backup directory
mv "$BACKUP_FILE" "$FINAL_BACKUP_PATH"
echo "Local backup saved to: $FINAL_BACKUP_PATH"

# Prune old backups (keep only MAX_BACKUPS most recent)
echo "Pruning old backups (keeping latest $MAX_BACKUPS)..."
cd "$LOCAL_BACKUP_DIR"
ls -t memories_*.sql.gz 2>/dev/null | tail -n +$((MAX_BACKUPS + 1)) | xargs -r rm -f

# List remaining backups
echo "=== Backups remaining ==="
ls -lh "$LOCAL_BACKUP_DIR"/memories_*.sql.gz 2>/dev/null | tail -5 || echo "(none)"

# Cleanup temp file
rm -f "$BACKUP_FILE" 2>/dev/null || true

echo "=== Backup complete: memories_${TIMESTAMP}.sql.gz ==="
