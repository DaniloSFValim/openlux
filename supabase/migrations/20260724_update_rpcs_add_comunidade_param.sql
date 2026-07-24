-- Migration: Update existing RPCs to support comunidade filtering
-- Purpose: Add p_comunidade parameter to existing point query RPCs
-- Date: 2026-07-24

-- Update ip_pontos_bbox to accept and filter by comunidade
CREATE OR REPLACE FUNCTION public.ip_pontos_bbox(
  p_bbox_south float8,
  p_bbox_west float8,
  p_bbox_north float8,
  p_bbox_east float8,
  p_zoom int,
  p_bairro text DEFAULT NULL,
  p_comunidade text DEFAULT NULL,
  p_tipo_ativo text DEFAULT NULL,
  p_status text DEFAULT NULL
)
RETURNS TABLE(
  id uuid,
  lat float8,
  lon float8,
  tipo_ativo text,
  tipo_luminaria text,
  potencia_w int,
  status text,
  health_status text,
  codigo_seconser text
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    p.id,
    ST_Y(p.geom)::float8 as lat,
    ST_X(p.geom)::float8 as lon,
    p.tipo_ativo::text,
    p.tipo_luminaria::text,
    p.potencia_w,
    p.status::text,
    p.health_status,
    p.codigo_seconser
  FROM public.pontos_luminaria p
  WHERE
    p.geom IS NOT NULL
    AND ST_Y(p.geom) BETWEEN p_bbox_south AND p_bbox_north
    AND ST_X(p.geom) BETWEEN p_bbox_west AND p_bbox_east
    AND (p_bairro IS NULL OR p.bairro_nome = p_bairro)
    AND (p_comunidade IS NULL OR p.comunidade_nome = p_comunidade)
    AND (p_tipo_ativo IS NULL OR p.tipo_ativo::text = p_tipo_ativo)
    AND (p_status IS NULL OR p.status::text = p_status)
  ORDER BY p.criado_em DESC;
END;
$$ LANGUAGE plpgsql STABLE;

-- Update ip_clusters_grid to accept and filter by comunidade
CREATE OR REPLACE FUNCTION public.ip_clusters_grid(
  p_bbox_south float8,
  p_bbox_west float8,
  p_bbox_north float8,
  p_bbox_east float8,
  p_zoom int,
  p_bairro text DEFAULT NULL,
  p_comunidade text DEFAULT NULL,
  p_tipo_ativo text DEFAULT NULL,
  p_status text DEFAULT NULL
)
RETURNS TABLE(
  cluster_lat float8,
  cluster_lon float8,
  point_count int,
  led_count int,
  pending_count int,
  unknown_count int,
  health_status text
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    ROUND(AVG(ST_Y(p.geom))::numeric, 4)::float8 as cluster_lat,
    ROUND(AVG(ST_X(p.geom))::numeric, 4)::float8 as cluster_lon,
    COUNT(*)::int as point_count,
    COUNT(CASE WHEN p.status = 'led_instalado' THEN 1 END)::int as led_count,
    COUNT(CASE WHEN p.status = 'pendente_troca' THEN 1 END)::int as pending_count,
    COUNT(CASE WHEN p.status = 'a_verificar' THEN 1 END)::int as unknown_count,
    p.health_status
  FROM public.pontos_luminaria p
  WHERE
    p.geom IS NOT NULL
    AND p.tipo_ativo = 'luminaria'
    AND ST_Y(p.geom) BETWEEN p_bbox_south AND p_bbox_north
    AND ST_X(p.geom) BETWEEN p_bbox_west AND p_bbox_east
    AND (p_bairro IS NULL OR p.bairro_nome = p_bairro)
    AND (p_comunidade IS NULL OR p.comunidade_nome = p_comunidade)
    AND (p_tipo_ativo IS NULL OR p.tipo_ativo::text = p_tipo_ativo)
    AND (p_status IS NULL OR p.status::text = p_status)
  GROUP BY p.health_status
  ORDER BY cluster_lat, cluster_lon;
END;
$$ LANGUAGE plpgsql STABLE;

-- Update ip_estatisticas to accept and filter by comunidade
CREATE OR REPLACE FUNCTION public.ip_estatisticas(
  p_bairro text DEFAULT NULL,
  p_comunidade text DEFAULT NULL,
  p_tipo_ativo text DEFAULT NULL,
  p_status text DEFAULT NULL
)
RETURNS TABLE(
  total_pontos bigint,
  total_led bigint,
  total_pendente bigint,
  total_verificar bigint,
  percentual_led numeric,
  media_potencia numeric,
  total_potencia bigint
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    COUNT(*) as total_pontos,
    COUNT(CASE WHEN p.status = 'led_instalado' THEN 1 END) as total_led,
    COUNT(CASE WHEN p.status = 'pendente_troca' THEN 1 END) as total_pendente,
    COUNT(CASE WHEN p.status = 'a_verificar' THEN 1 END) as total_verificar,
    ROUND(100.0 * COUNT(CASE WHEN p.status = 'led_instalado' THEN 1 END) / NULLIF(COUNT(*), 0), 2) as percentual_led,
    ROUND(AVG(p.potencia_w), 2) as media_potencia,
    COALESCE(SUM(p.potencia_w), 0) as total_potencia
  FROM public.pontos_luminaria p
  WHERE
    p.tipo_ativo = 'luminaria'
    AND (p_bairro IS NULL OR p.bairro_nome = p_bairro)
    AND (p_comunidade IS NULL OR p.comunidade_nome = p_comunidade)
    AND (p_tipo_ativo IS NULL OR p.tipo_ativo::text = p_tipo_ativo)
    AND (p_status IS NULL OR p.status::text = p_status);
END;
$$ LANGUAGE plpgsql STABLE;

-- Grant permissions
GRANT EXECUTE ON FUNCTION public.ip_pontos_bbox(float8, float8, float8, float8, int, text, text, text, text) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.ip_clusters_grid(float8, float8, float8, float8, int, text, text, text, text) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.ip_estatisticas(text, text, text, text) TO anon, authenticated, service_role;
