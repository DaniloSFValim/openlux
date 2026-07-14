-- Selecao por poligono desenhado: pontos e estatisticas restritos a uma area
-- arbitraria (GeoJSON). Leitura publica (o mapa funciona sem login). Usa o indice
-- GIST idx_pontos_geom via prefiltro && antes do ST_Contains.
--
-- APLICADA EM PRODUCAO em 2026-07-10 (versao 20260710191925).

-- Pontos dentro do poligono (mesmo shape do ip_pontos_bbox; usado no mapa e no export).
CREATE OR REPLACE FUNCTION public.ip_pontos_poligono(p_geojson text, limite integer DEFAULT 5000)
RETURNS json
LANGUAGE sql STABLE SECURITY DEFINER SET search_path TO 'public'
AS $function$
  WITH poly AS (SELECT ST_MakeValid(ST_SetSRID(ST_GeomFromGeoJSON(p_geojson), 4326)) AS g)
  SELECT coalesce(json_agg(row_to_json(t)),'[]'::json) FROM (
    SELECT pl.id, ST_Y(pl.geom) lat, ST_X(pl.geom) lon, pl.modernizado_led, pl.tipo_lampada,
           pl.potencia_w, pl.status, pl.bairro_nome, pl.numero_patrimonio, pl.endereco, pl.fonte,
           pl.fonte_modernizacao, pl.censo_tipo_original, pl.observacoes, pl.flag_revisao_censo,
           pl.codigo_seconser, pl.tipo_ativo, pl.tipo_luminaria, pl.classe_nbr, pl.health_status,
           pl.angulo_inclinacao_graus, pl.material_piso
    FROM pontos_luminaria pl, poly
    WHERE pl.geom && poly.g AND ST_Contains(poly.g, pl.geom)
    LIMIT limite) t;
$function$;

-- Estatisticas agregadas apenas da area do poligono.
CREATE OR REPLACE FUNCTION public.ip_stats_poligono(p_geojson text)
RETURNS json
LANGUAGE sql STABLE SECURITY DEFINER SET search_path TO 'public'
AS $function$
  WITH poly AS (SELECT ST_MakeValid(ST_SetSRID(ST_GeomFromGeoJSON(p_geojson), 4326)) AS g),
  ar AS (SELECT GREATEST(ST_Area(g::geography)/1e6, 0.000001) AS km2 FROM poly),
  sel AS (
    SELECT pl.* FROM pontos_luminaria pl, poly
    WHERE pl.geom && poly.g AND ST_Contains(poly.g, pl.geom)
  )
  SELECT json_build_object(
    'total',        (SELECT count(*) FROM sel),
    'area_km2',     (SELECT round(km2::numeric, 4) FROM ar),
    'densidade_km2',(SELECT round((count(*) / (SELECT km2 FROM ar))::numeric, 1) FROM sel),
    'led',          (SELECT count(*) FROM sel WHERE modernizado_led),
    'pendente',     (SELECT count(*) FROM sel WHERE NOT modernizado_led AND tipo_ativo = 'luminaria'),
    'pct_led',      (SELECT CASE WHEN count(*) FILTER (WHERE tipo_ativo='luminaria') > 0
                            THEN round(100.0 * count(*) FILTER (WHERE modernizado_led)
                                       / count(*) FILTER (WHERE tipo_ativo='luminaria'), 1)
                            ELSE 0 END FROM sel),
    'potencia_kw',  (SELECT round((coalesce(sum(potencia_w),0)/1000.0)::numeric, 1) FROM sel),
    'por_tipo_lampada', (SELECT coalesce(json_object_agg(tl, n), '{}'::json) FROM (
        SELECT coalesce(tipo_lampada::text,'—') tl, count(*) n FROM sel
        WHERE tipo_ativo='luminaria' GROUP BY 1 ORDER BY 2 DESC) x),
    'por_tipo_ativo', (SELECT coalesce(json_object_agg(ta, n), '{}'::json) FROM (
        SELECT tipo_ativo::text ta, count(*) n FROM sel GROUP BY 1 ORDER BY 2 DESC) x),
    'classificados_foto', (SELECT count(*) FROM sel
        WHERE angulo_inclinacao_graus IS NOT NULL AND material_piso IS NOT NULL),
    'aproveitamento_medio', (SELECT round(avg(GREATEST(0, cosd(angulo_inclinacao_graus)))::numeric, 3)
        FROM sel WHERE angulo_inclinacao_graus IS NOT NULL AND material_piso IS NOT NULL),
    'poluicao_media', (SELECT round(avg(LEAST(1,
          (1 - GREATEST(0, cosd(sel.angulo_inclinacao_graus)))
          + r.refletancia * GREATEST(0, cosd(sel.angulo_inclinacao_graus)) * 0.5))::numeric, 3)
        FROM sel JOIN ref_material_piso r ON r.material = sel.material_piso
        WHERE sel.angulo_inclinacao_graus IS NOT NULL)
  );
$function$;

-- Leitura publica (o mapa funciona sem login)
GRANT EXECUTE ON FUNCTION public.ip_pontos_poligono(text, integer) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.ip_stats_poligono(text)          TO anon, authenticated, service_role;
