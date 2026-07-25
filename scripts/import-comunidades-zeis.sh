#!/bin/bash
# Recarrega a tabela public.comunidades_zeis a partir da fonte oficial (SIGEO Niteroi).
#
# Fonte: ArcGIS FeatureServer camada 430 — "Zonas de Especial Interesse Social (Mapa 8)"
#        do Plano Diretor, owner pmngeo.
# Dataset (pagina): https://www.sigeo.niteroi.rj.gov.br/datasets/0d0b8e7a3643432999a9d7f75f763e21_430/explore
#
# O download e feito pelo proprio Postgres (extensao http, instalada e removida na mesma
# transacao) para nao trafegar ~1,7 MB de GeoJSON pela maquina que roda o script.
#
# Uso:
#   export SUPABASE_DB_URL='postgresql://postgres:SENHA@db.<ref>.supabase.co:5432/postgres'
#   ./scripts/import-comunidades-zeis.sh
#
# Notas sobre os dados (verificado em 2026-07-25):
#   - 145 features na origem; 1 sem geometria e descartada -> 144 inseridas, 137 nomes distintos
#   - nomes repetem legitimamente (ex.: "Nao identificada"); as RPCs agregam por nome com ST_Union
#   - geometrias chegam como Polygon/MultiPolygon em SRID 31983; pedimos outSR=4326
#   - ST_MakeValid pode devolver GeometryCollection; ST_CollectionExtract(...,3) mantem so poligonos

set -euo pipefail

if [ -z "${SUPABASE_DB_URL:-}" ]; then
  echo "erro: defina SUPABASE_DB_URL" >&2
  exit 1
fi

SRC='https://services8.arcgis.com/TpaOLI1HCh5AcRQB/arcgis/rest/services/Grouplayer_SMU_PLANODIRETOR_AGOL/FeatureServer/430/query?where=1%3D1&outFields=tx_comunidade,tx_bairro,tx_siglareg&outSR=4326&geometryPrecision=6&f=geojson'

psql "$SUPABASE_DB_URL" -v ON_ERROR_STOP=1 <<SQL
BEGIN;

CREATE EXTENSION IF NOT EXISTS http WITH SCHEMA extensions;
SELECT extensions.http_set_curlopt('CURLOPT_TIMEOUT', '180');

DELETE FROM public.comunidades_zeis;

WITH resp AS (
  SELECT content::json AS j FROM extensions.http_get('$SRC')
),
feats AS (
  SELECT json_array_elements(j->'features') AS f FROM resp
),
norm AS (
  SELECT
    nullif(btrim(f->'properties'->>'tx_comunidade'), '') AS nome,
    nullif(btrim(f->'properties'->>'tx_bairro'), '')     AS bairro,
    nullif(btrim(f->'properties'->>'tx_siglareg'), '')   AS sigla_regiao,
    ST_Multi(ST_CollectionExtract(
      ST_MakeValid(ST_SetSRID(ST_GeomFromGeoJSON(f->>'geometry'), 4326)), 3
    )) AS geom
  FROM feats
  WHERE f->'geometry' IS NOT NULL
    AND json_typeof(f->'geometry') = 'object'
    AND nullif(btrim(f->'properties'->>'tx_comunidade'), '') IS NOT NULL
)
INSERT INTO public.comunidades_zeis (nome, bairro, sigla_regiao, geom)
SELECT nome, bairro, sigla_regiao, geom
FROM norm
WHERE geom IS NOT NULL AND NOT ST_IsEmpty(geom);

-- A extensao http nao fica instalada: e superficie de rede desnecessaria em runtime.
DROP EXTENSION IF EXISTS http;

SELECT count(*) AS inseridas,
       count(DISTINCT nome) AS nomes_distintos,
       count(*) FILTER (WHERE NOT ST_IsValid(geom)) AS invalidas
FROM public.comunidades_zeis;

COMMIT;
SQL

echo "✅ comunidades_zeis recarregada"
