-- Migration: Add Health Status to Luminarias
-- Purpose: Calculate and track health status of lighting fixtures
-- Status values: 'verde' (good), 'amarelo' (needs maintenance), 'vermelho' (critical), 'cinza' (unmapped)

-- ============================================================================
-- 1. Add health_status column to pontos_luminaria
-- ============================================================================

ALTER TABLE public.pontos_luminaria
ADD COLUMN IF NOT EXISTS health_status text DEFAULT 'cinza'
CHECK (health_status IN ('verde', 'amarelo', 'vermelho', 'cinza'));

-- Index for filtering by status
CREATE INDEX IF NOT EXISTS idx_pontos_health_status ON public.pontos_luminaria(health_status);

-- ============================================================================
-- 2. Create function to calculate health status
-- ============================================================================

CREATE OR REPLACE FUNCTION public.calc_health_status(
  p_idade_anos integer,
  p_modernizado_led boolean,
  p_potencia_w integer,
  p_flag_revisao boolean
)
RETURNS text
LANGUAGE sql
IMMUTABLE
AS $$
  SELECT CASE
    -- Vermelho: Crítico
    WHEN p_idade_anos IS NULL THEN 'cinza'
    WHEN p_idade_anos > 12 THEN 'vermelho'
    WHEN p_modernizado_led = false AND p_potencia_w > 400 THEN 'vermelho'
    -- Amarelo: Manutenção necessária
    WHEN p_idade_anos >= 8 AND p_idade_anos <= 12 THEN 'amarelo'
    WHEN p_flag_revisao = true THEN 'amarelo'
    -- Verde: Funcionando bem
    WHEN p_idade_anos < 8 THEN 'verde'
    ELSE 'cinza'
  END;
$$;

-- ============================================================================
-- 3. Update existing records with calculated health status
-- ============================================================================

UPDATE public.pontos_luminaria
SET health_status = public.calc_health_status(
  EXTRACT(YEAR FROM AGE(data_instalacao))::integer,
  modernizado_led,
  potencia_w,
  flag_revisao_censo
)
WHERE data_instalacao IS NOT NULL;

-- Mark records without data_instalacao as 'cinza'
UPDATE public.pontos_luminaria
SET health_status = 'cinza'
WHERE data_instalacao IS NULL;

-- ============================================================================
-- 4. Create trigger to auto-update health_status on insert/update
-- ============================================================================

CREATE OR REPLACE FUNCTION public.update_health_status()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
  NEW.health_status := public.calc_health_status(
    EXTRACT(YEAR FROM AGE(NEW.data_instalacao))::integer,
    NEW.modernizado_led,
    NEW.potencia_w,
    NEW.flag_revisao_censo
  );
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_update_health_status ON public.pontos_luminaria;
CREATE TRIGGER trg_update_health_status
BEFORE INSERT OR UPDATE ON public.pontos_luminaria
FOR EACH ROW
EXECUTE FUNCTION public.update_health_status();

-- ============================================================================
-- 5. Update ip_pontos_bbox to include health_status
-- ============================================================================

CREATE OR REPLACE FUNCTION public.ip_pontos_bbox(
  min_lng double precision,
  min_lat double precision,
  max_lng double precision,
  max_lat double precision,
  limite integer DEFAULT 4000,
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
  SELECT coalesce(json_agg(row_to_json(t)),'[]'::json) FROM (
    SELECT id, ST_Y(geom) lat, ST_X(geom) lon, modernizado_led, tipo_lampada,
           potencia_w, status, bairro_nome, numero_patrimonio, endereco, fonte,
           fonte_modernizacao, censo_tipo_original, observacoes, flag_revisao_censo,
           codigo_seconser, tipo_ativo, tipo_luminaria, classe_nbr, health_status
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
    LIMIT limite) t;
$function$;

-- ============================================================================
-- 6. Create aggregation function for health status by area
-- ============================================================================

CREATE OR REPLACE FUNCTION public.ip_health_status_summary(
  min_lng double precision,
  min_lat double precision,
  max_lng double precision,
  max_lat double precision
)
RETURNS json
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = 'public'
AS $function$
  SELECT json_build_object(
    'verde', COUNT(*) FILTER (WHERE health_status = 'verde'),
    'amarelo', COUNT(*) FILTER (WHERE health_status = 'amarelo'),
    'vermelho', COUNT(*) FILTER (WHERE health_status = 'vermelho'),
    'cinza', COUNT(*) FILTER (WHERE health_status = 'cinza'),
    'total', COUNT(*)
  )
  FROM pontos_luminaria
  WHERE geom && ST_MakeEnvelope(min_lng,min_lat,max_lng,max_lat,4326);
$function$;

-- ============================================================================
-- 7. Grant permissions
-- ============================================================================

GRANT EXECUTE ON FUNCTION public.calc_health_status(integer, boolean, integer, boolean) TO authenticated;
GRANT EXECUTE ON FUNCTION public.ip_pontos_bbox(
  double precision, double precision, double precision, double precision,
  integer, text, text, boolean, integer, boolean, text, boolean,
  integer, integer, integer, integer, date, date, text
) TO authenticated;
GRANT EXECUTE ON FUNCTION public.ip_health_status_summary(
  double precision, double precision, double precision, double precision
) TO authenticated;
