-- Migration: Create RPC to perform spatial join and assign communities to points
-- Purpose: Match points to community zones via ST_Intersects geometry
-- Date: 2026-07-24

-- RPC function to assign communities to all points via spatial join
CREATE OR REPLACE FUNCTION public.ip_atribuir_comunidades()
RETURNS TABLE(
  pontos_atualizados bigint,
  comunidades_encontradas text[]
) AS $$
DECLARE
  v_pontos_atualizados bigint;
  v_comunidades text[];
BEGIN
  -- Update pontos_luminaria with community names via spatial intersection
  WITH pontos_com_comunidade AS (
    SELECT
      p.id,
      c.nome AS comunidade
    FROM public.pontos_luminaria p
    LEFT JOIN public.comunidades_geojson c ON ST_Intersects(p.geom, c.geojson)
    WHERE p.geom IS NOT NULL
  )
  UPDATE public.pontos_luminaria p
  SET
    comunidade_nome = pcc.comunidade,
    atualizado_em = now()
  FROM pontos_com_comunidade pcc
  WHERE p.id = pcc.id;

  -- Get count of updated points
  SELECT COUNT(*) INTO v_pontos_atualizados
  FROM public.pontos_luminaria
  WHERE comunidade_nome IS NOT NULL;

  -- Get list of unique communities assigned
  SELECT ARRAY_AGG(DISTINCT comunidade_nome ORDER BY comunidade_nome)
  INTO v_comunidades
  FROM public.pontos_luminaria
  WHERE comunidade_nome IS NOT NULL;

  RETURN QUERY SELECT v_pontos_atualizados, COALESCE(v_comunidades, ARRAY[]::text[]);
END;
$$ LANGUAGE plpgsql;

-- Grant permission to execute
GRANT EXECUTE ON FUNCTION public.ip_atribuir_comunidades() TO authenticated, service_role;
