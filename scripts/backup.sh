#!/bin/bash
# Backup Script - Iluminação LED Niterói
# Faz backup do Supabase database
#
# Uso:
#   ./scripts/backup.sh                 # Backup Supabase local
#   ./scripts/backup.sh --prod          # Backup produção (requer credenciais)

set -e  # Exit on error

BACKUP_DIR="./backups"
DATE=$(date +%Y-%m-%d_%H-%M-%S)
BACKUP_FILE="$BACKUP_DIR/db_$DATE.sql"

# Criar diretório de backups se não existir
mkdir -p "$BACKUP_DIR"

echo "📦 Iniciando backup do Supabase..."
echo "📁 Diretório: $BACKUP_DIR"
echo "📄 Arquivo: $(basename $BACKUP_FILE)"

# Supabase Local (default)
if [ "$1" != "--prod" ]; then
  echo "🔄 Usando Supabase LOCAL (http://localhost:54321)"

  # Verificar se Supabase está rodando
  if ! supabase status &>/dev/null; then
    echo "❌ ERRO: Supabase local não está rodando"
    echo "   Execute: supabase start"
    exit 1
  fi

  # Fazer dump do banco local
  supabase db dump -f "$BACKUP_FILE"

  BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
  echo "✅ Backup local concluído!"
  echo "   Arquivo: $BACKUP_FILE"
  echo "   Tamanho: $BACKUP_SIZE"

# Supabase Produção
else
  echo "🔴 Usando Supabase PRODUÇÃO"

  # Verificar se credenciais estão disponíveis
  if [ -z "$SUPABASE_ACCESS_TOKEN" ] || [ -z "$SUPABASE_DB_URL" ]; then
    echo "❌ ERRO: Credenciais não configuradas"
    echo "   Configure as variáveis de ambiente:"
    echo "   export SUPABASE_ACCESS_TOKEN=<seu_token>"
    echo "   export SUPABASE_DB_URL=<sua_db_url>"
    exit 1
  fi

  echo "⚠️  BACKUPANDO PRODUÇÃO - Tenha cuidado!"
  read -p "Tem certeza? (s/n) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    echo "❌ Cancelado"
    exit 1
  fi

  # Fazer dump do banco de produção
  # supabase db dump --db-url "$SUPABASE_DB_URL" -f "$BACKUP_FILE"

  # Alternativa: usar pg_dump direto
  if command -v pg_dump &> /dev/null; then
    pg_dump "$SUPABASE_DB_URL" -f "$BACKUP_FILE"
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "✅ Backup produção concluído!"
    echo "   Arquivo: $BACKUP_FILE"
    echo "   Tamanho: $BACKUP_SIZE"
  else
    echo "❌ ERRO: pg_dump não encontrado"
    echo "   Instale PostgreSQL client tools"
    exit 1
  fi
fi

# Manter apenas últimos 30 backups (cleanup automático)
echo "🧹 Limpando backups antigos (mantendo últimos 30)..."
ls -t "$BACKUP_DIR"/*.sql 2>/dev/null | tail -n +31 | xargs rm -f 2>/dev/null || true

TOTAL_BACKUPS=$(ls "$BACKUP_DIR"/*.sql 2>/dev/null | wc -l)
echo "📊 Total de backups: $TOTAL_BACKUPS"

echo "✨ Backup finalizado com sucesso!"
