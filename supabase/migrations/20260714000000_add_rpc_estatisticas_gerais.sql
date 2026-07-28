-- Fase 2: Dashboard RPC for KPI Sparklines
-- Returns general statistics: total count, LED percentage, average power, average efficacy
CREATE OR REPLACE FUNCTION public.ip_estatisticas_gerais()
RETURNS json
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path TO 'public'
AS $function$
  SELECT json_build_object(
    'total_luminas', COUNT(*),
    'led_total', ROUND(100.0 * COUNT(*) FILTER (WHERE modernizado_led) / NULLIF(COUNT(*), 0), 1),
    'potencia_media', ROUND((AVG(potencia_w) FILTER (WHERE potencia_w > 0))::numeric, 1),
    'eficacia_media', ROUND((AVG(COALESCE(eficacia_luminosa_lm_w, 80)) FILTER (WHERE modernizado_led))::numeric, 1)
  )
  FROM pontos_luminaria;
$function$;

-- Grant execute to authenticated users
GRANT EXECUTE ON FUNCTION public.ip_estatisticas_gerais() TO authenticated;
