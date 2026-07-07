#!/bin/bash
# Restore Script - Iluminação LED Niterói
# Restaura o Supabase database de um backup
#
# Uso:
#   ./scripts/restore.sh <backup_file>
#   ./scripts/restore.sh backups/db_2026-07-07_14-30-00.sql

set -e  # Exit on error

# Validar argumentos
if [ -z "$1" ]; then
  echo "❌ Nenhum arquivo de backup especificado"
  echo ""
  echo "Uso: ./scripts/restore.sh <backup_file>"
  echo ""
  echo "Backups disponíveis:"
  ls -lh backups/ 2>/dev/null | grep -E "\.sql$" || echo "  (nenhum backup encontrado)"
  exit 1
fi

BACKUP_FILE=$1

# Validar arquivo
if [ ! -f "$BACKUP_FILE" ]; then
  echo "❌ Arquivo não encontrado: $BACKUP_FILE"
  exit 1
fi

BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)

echo "⚠️  RESTAURANDO DATABASE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Arquivo: $BACKUP_FILE"
echo "Tamanho: $BACKUP_SIZE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "⚠️  AVISO: Isso vai DELETAR todos os dados atuais!"
echo "⚠️  Esta operação NÃO pode ser desfeita!"
echo ""

# Confirmação dupla
read -p "Tem certeza que deseja continuar? Digite 'sim' para confirmar: " confirmation

if [ "$confirmation" != "sim" ]; then
  echo "❌ Restauração cancelada"
  exit 0
fi

echo ""
echo "🔄 Iniciando restauração..."

# Restaurar no Supabase local
echo "🔍 Verificando se Supabase local está rodando..."
if ! supabase status &>/dev/null; then
  echo "❌ Erro: Supabase local não está rodando"
  echo "   Execute: supabase start"
  exit 1
fi

# Resetar database
echo "🗑️  Resetando database..."
supabase db reset 2>/dev/null || true

# Restaurar de arquivo
echo "📥 Restaurando de arquivo..."
if command -v psql &> /dev/null; then
  psql postgresql://postgres:postgres@localhost:54322/postgres \
    -f "$BACKUP_FILE" \
    -v ON_ERROR_STOP=1 \
    2>&1 | tail -20  # mostrar últimas 20 linhas

  if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Database restaurado com sucesso!"
    echo ""
    echo "📝 Próximos passos:"
    echo "   1. Verificar dados: psql postgresql://postgres:postgres@localhost:54322/postgres"
    echo "   2. Recriar usuários de teste (se necessário)"
    echo "   3. Recarregar página do frontend"
    echo ""
    echo "💾 Backup restaurado de: $BACKUP_FILE"
  else
    echo "❌ Erro ao restaurar database"
    exit 1
  fi
else
  echo "❌ Erro: psql não encontrado"
  echo "   Instale PostgreSQL client tools"
  exit 1
fi
