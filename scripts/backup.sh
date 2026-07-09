#!/bin/bash
set -e

BACKUP_DIR="./backups"
DATE=$(date +%Y-%m-%d_%H-%M-%S)
BACKUP_FILE="$BACKUP_DIR/db_$DATE.sql"

mkdir -p "$BACKUP_DIR"

# Supabase produção
if [ "$1" = "--prod" ]; then
  supabase db dump --db-url "$SUPABASE_DB_URL" -f "$BACKUP_FILE"
  echo "✅ Backup produção: $BACKUP_FILE"
else
  # Supabase local
  supabase db dump -f "$BACKUP_FILE"
  echo "✅ Backup local: $BACKUP_FILE"
fi

# Manter apenas últimos 30 backups
ls -t "$BACKUP_DIR"/*.sql 2>/dev/null | tail -n +31 | xargs rm -f 2>/dev/null || true
