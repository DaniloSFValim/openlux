#!/bin/bash
# Backup do banco Supabase.
#
# Uso:
#   ./scripts/backup.sh --prod   # producao, exige SUPABASE_DB_URL
#   ./scripts/backup.sh          # instancia local
#
# Historico: este script rodou 82 vezes no CI sem nunca produzir um backup.
# A causa era `--db-url ""` — o secret SUPABASE_DB_URL nao estava configurado.
# Com a URL vazia, o pg_dump ignora o destino remoto e tenta o socket local,
# falhando com "connection to server on socket ... failed", mensagem que nao
# diz nada sobre secret faltando. As checagens abaixo existem para que esse
# modo de falha nunca mais passe por problema de conectividade.

set -euo pipefail

BACKUP_DIR="./backups"
DATE=$(date +%Y-%m-%d_%H-%M-%S)
BACKUP_FILE="$BACKUP_DIR/db_$DATE.sql"

# Um dump real deste banco passa de 1 MB. Qualquer coisa abaixo de 1 KB e
# cabecalho de arquivo sem conteudo — dump incompleto disfarcado de sucesso.
TAMANHO_MINIMO_BYTES=1024

mkdir -p "$BACKUP_DIR"

if [ "${1:-}" = "--prod" ]; then
  if [ -z "${SUPABASE_DB_URL:-}" ]; then
    echo "ERRO: SUPABASE_DB_URL esta vazio ou nao definido." >&2
    echo "" >&2
    echo "Sem essa variavel o pg_dump tenta o socket local e falha com uma" >&2
    echo "mensagem de conexao que esconde a causa real." >&2
    echo "" >&2
    echo "No CI: configure o secret em Settings -> Secrets and variables ->" >&2
    echo "Actions -> SUPABASE_DB_URL." >&2
    echo "Localmente: exporte a variavel antes de rodar com --prod." >&2
    exit 1
  fi
  supabase db dump --db-url "$SUPABASE_DB_URL" -f "$BACKUP_FILE"
  DESTINO="producao"
else
  supabase db dump -f "$BACKUP_FILE"
  DESTINO="local"
fi

# O `supabase db dump` pode sair com codigo 0 e ainda deixar um arquivo vazio.
# Sem esta verificacao, o passo do workflow fica verde e o commit leva um
# arquivo inutil — falha silenciosa, que e exatamente o que aconteceu antes.
if [ ! -f "$BACKUP_FILE" ]; then
  echo "ERRO: o dump terminou sem erro mas $BACKUP_FILE nao foi criado." >&2
  exit 1
fi

TAMANHO=$(wc -c < "$BACKUP_FILE" | tr -d '[:space:]')
if [ "$TAMANHO" -lt "$TAMANHO_MINIMO_BYTES" ]; then
  echo "ERRO: $BACKUP_FILE tem apenas $TAMANHO bytes (minimo esperado:" >&2
  echo "$TAMANHO_MINIMO_BYTES). Dump incompleto — tratando como falha." >&2
  # Remover o arquivo invalido: deixa-lo no diretorio faria a rotacao dos 30
  # contar um dump que nao serve para restaurar nada.
  rm -f "$BACKUP_FILE"
  exit 1
fi

echo "Backup $DESTINO concluido: $BACKUP_FILE ($TAMANHO bytes)"

# Manter apenas os ultimos 30 backups.
ls -t "$BACKUP_DIR"/*.sql 2>/dev/null | tail -n +31 | xargs -r rm -f || true
