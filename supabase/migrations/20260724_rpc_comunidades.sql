-- Migration: Create RPC functions for communities filter
-- Purpose: Query communities and get GeoJSON for visualization
-- Date: 2026-07-24

-- RPC: List all communities with point counts
CREATE OR REPLACE FUNCTION public.ip_comunidades_lista()
RETURNS TABLE(
  comunidade text,
  total_pontos bigint,
  pontos_led bigint,
  percentual_led numeric
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    COALESCE(p.comunidade_nome, 'Sem comunidade') AS comunidade,
    COUNT(*) AS total_pontos,
    COUNT(CASE WHEN p.status = 'led_instalado' THEN 1 END) AS pontos_led,
    ROUND(100.0 * COUNT(CASE WHEN p.status = 'led_instalado' THEN 1 END) / COUNT(*), 2) AS percentual_led
  FROM public.pontos_luminaria p
  WHERE p.tipo_ativo = 'luminaria'
  GROUP BY p.comunidade_nome
  ORDER BY comunidade;
END;
$$ LANGUAGE plpgsql STABLE;

-- RPC: Get GeoJSON for a specific community
CREATE OR REPLACE FUNCTION public.ip_comunidade_geojson(p_comunidade text)
RETURNS jsonb AS $$
DECLARE
  v_result jsonb;
BEGIN
  SELECT jsonb_build_object(
    'type', 'FeatureCollection',
    'features', jsonb_agg(
      jsonb_build_object(
        'type', 'Feature',
        'geometry', ST_AsGeoJSON(c.geojson)::jsonb,
        'properties', jsonb_build_object(
          'nome', c.nome,
          'descricao', c.descricao
        )
      )
    )
  ) INTO v_result
  FROM public.comunidades_geojson c
  WHERE c.nome = p_comunidade;

  RETURN COALESCE(v_result, jsonb_build_object('type', 'FeatureCollection', 'features', jsonb_build_array()));
END;
$$ LANGUAGE plpgsql STABLE;

-- RPC: Statistics for a specific community
CREATE OR REPLACE FUNCTION public.ip_por_comunidade()
RETURNS TABLE(
  comunidade_nome text,
  total bigint,
  led_instalado bigint,
  pendente_troca bigint,
  a_verificar bigint,
  percentual_led numeric
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    COALESCE(p.comunidade_nome, 'Sem comunidade') AS comunidade_nome,
    COUNT(*) AS total,
    COUNT(CASE WHEN p.status = 'led_instalado' THEN 1 END) AS led_instalado,
    COUNT(CASE WHEN p.status = 'pendente_troca' THEN 1 END) AS pendente_troca,
    COUNT(CASE WHEN p.status = 'a_verificar' THEN 1 END) AS a_verificar,
    ROUND(100.0 * COUNT(CASE WHEN p.status = 'led_instalado' THEN 1 END) / COUNT(*), 2) AS percentual_led
  FROM public.pontos_luminaria p
  WHERE p.tipo_ativo = 'luminaria'
  GROUP BY p.comunidade_nome
  ORDER BY comunidade_nome;
END;
$$ LANGUAGE plpgsql STABLE;

-- Grant permissions
GRANT EXECUTE ON FUNCTION public.ip_comunidades_lista() TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.ip_comunidade_geojson(text) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.ip_por_comunidade() TO anon, authenticated, service_role;
