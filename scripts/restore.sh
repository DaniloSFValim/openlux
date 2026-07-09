#!/bin/bash
set -e

if [ -z "$1" ]; then
  echo "Uso: ./restore.sh <backup_file>"
  echo "Backups disponíveis:"
  ls -lh backups/
  exit 1
fi

BACKUP_FILE=$1

if [ ! -f "$BACKUP_FILE" ]; then
  echo "❌ Arquivo não encontrado: $BACKUP_FILE"
  exit 1
fi

echo "⚠️  RESTAURANDO DATABASE DE: $BACKUP_FILE"
read -p "Tem certeza? (s/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Ss]$ ]]; then
  supabase db reset
  psql -f "$BACKUP_FILE"
  echo "✅ Banco restaurado!"
else
  echo "Cancelado."
fi
