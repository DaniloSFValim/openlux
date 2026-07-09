-- Migration: Fix ip_clusters_grid to support health_status filter
-- Purpose: Add missing p_health_status parameter to ip_clusters_grid function

-- ============================================================================
-- Update ip_clusters_grid to include health_status parameter and filter
-- ============================================================================

CREATE OR REPLACE FUNCTION public.ip_clusters_grid(
  min_lng double precision,
  min_lat double precision,
  max_lng double precision,
  max_lat double precision,
  zoom_level integer,
  p_bairro text DEFAULT NULL,
  p_tipo text DEFAULT NULL,
  p_modernizado boolean DEFAULT NULL,
  p_pot_min integer DEFAULT NULL,
  p_revisao boolean DEFAULT NULL,
  p_fonte_mod text DEFAULT NULL,
  p_suspeito boolean DEFAULT NULL,
  p_led_min integer DEFAULT NULL,
  p_led_max integer DEFAULT NULL,
  p_power_min integer DEFAULT NULL,
  p_power_max integer DEFAULT NULL,
  p_data_inicio date DEFAULT NULL,
  p_data_fim date DEFAULT NULL,
  p_health_status text DEFAULT NULL
)
RETURNS json
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = 'public'
AS $function$
  WITH grid AS (
    SELECT
      ST_GeoHash(
        ST_PointOnSurface(geom),
        CASE WHEN zoom_level < 6 THEN 3
             WHEN zoom_level < 10 THEN 4
             WHEN zoom_level < 13 THEN 5
             ELSE 6 END
      ) as hash,
      COUNT(*) as cnt,
      SUM(CASE WHEN modernizado_led THEN 1 ELSE 0 END)::float / COUNT(*) * 100 as led_pct,
      AVG(CAST(potencia_w AS float)) as avg_power,
      ST_AsText(ST_PointOnSurface(geom)) as pt
    FROM pontos_luminaria
    WHERE geom && ST_MakeEnvelope(min_lng,min_lat,max_lng,max_lat,4326)
      AND (p_bairro IS NULL OR bairro_nome=p_bairro)
      AND (p_tipo IS NULL OR tipo_lampada::text=p_tipo)
      AND (p_modernizado IS NULL OR modernizado_led=p_modernizado)
      AND (p_pot_min IS NULL OR potencia_w>=p_pot_min)
      AND (p_revisao IS NULL OR flag_revisao_censo=p_revisao)
      AND (p_fonte_mod IS NULL OR fonte_modernizacao=p_fonte_mod)
      AND (p_suspeito IS NULL OR (modernizado_led AND potencia_w>400))
      AND (p_led_min IS NULL OR potencia_w >= p_led_min)
      AND (p_led_max IS NULL OR potencia_w <= p_led_max)
      AND (p_power_min IS NULL OR potencia_w >= p_power_min)
      AND (p_power_max IS NULL OR potencia_w <= p_power_max)
      AND (p_data_inicio IS NULL OR data_modernizacao >= p_data_inicio)
      AND (p_data_fim IS NULL OR data_modernizacao <= p_data_fim)
      AND (p_health_status IS NULL OR health_status = p_health_status)
    GROUP BY hash, ST_PointOnSurface(geom)
  )
  SELECT coalesce(json_agg(row_to_json(g)),'[]'::json) FROM grid g;
$function$;

-- ============================================================================
-- Update GRANT permissions for new signature
-- ============================================================================

GRANT EXECUTE ON FUNCTION public.ip_clusters_grid(
  double precision, double precision, double precision, double precision,
  integer, text, text, boolean, integer, boolean, text, boolean,
  integer, integer, integer, integer, date, date, text
) TO authenticated;
