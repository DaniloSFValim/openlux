-- Fix: Corrigir parâmetros de RPC e coluna ausente em profiles
-- Problema 1: Frontend passa 'grid_deg', não 'zoom_level'
-- Problema 2: Coluna 'profiles.created_at' não existe

-- ============================================================================
-- 1. ATUALIZAR ip_clusters_grid com parâmetro correto (grid_deg, não zoom_level)
-- ============================================================================

CREATE OR REPLACE FUNCTION public.ip_clusters_grid(
  min_lng double precision,
  min_lat double precision,
  max_lng double precision,
  max_lat double precision,
  grid_deg numeric,
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
  p_data_fim date DEFAULT NULL
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
        CASE WHEN grid_deg > 0.05 THEN 4
             WHEN grid_deg > 0.02 THEN 5
             WHEN grid_deg > 0.01 THEN 6
             ELSE 7 END
      ) as hash,
      COUNT(*) as cnt,
      SUM(CASE WHEN modernizado_led THEN 1 ELSE 0 END)::float / COUNT(*) * 100 as led_pct,
      AVG(CAST(potencia_w AS float)) as avg_power,
      AVG(ST_Y(geom)) as lat,
      AVG(ST_X(geom)) as lon
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
    GROUP BY hash
  )
  SELECT coalesce(json_agg(
    json_build_object(
      'hash', hash,
      'n', cnt,
      'led', ROUND(led_pct)::int,
      'power', ROUND(avg_power)::int,
      'lat', lat,
      'lon', lon
    )
  ),'[]'::json) FROM grid g;
$function$;

-- ============================================================================
-- 2. ADICIONAR coluna 'created_at' em profiles se não existir
-- ============================================================================

ALTER TABLE public.profiles
ADD COLUMN IF NOT EXISTS created_at timestamp with time zone DEFAULT now();

-- ============================================================================
-- 3. GRANT EXECUTE ao profiles
-- ============================================================================

GRANT EXECUTE ON FUNCTION public.ip_clusters_grid(
  double precision, double precision, double precision, double precision,
  numeric, text, text, boolean, integer, boolean, text, boolean,
  integer, integer, integer, integer, date, date
) TO authenticated;
