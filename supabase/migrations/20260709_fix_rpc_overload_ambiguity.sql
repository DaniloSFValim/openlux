-- Fix: Remover overload duplicada de ip_inserir_ponto (double precision)
-- Problema: Existiam 2 overloads conflitantes:
--   1. ip_inserir_ponto(double precision, double precision, ...) - SEM p_requer_aprovacao
--   2. ip_inserir_ponto(numeric, numeric, ...) - COM p_requer_aprovacao
-- PostgreSQL não conseguia disambiguar qual usar → erro na criação de pontos
-- Solução: Manter APENAS a versão numeric com p_requer_aprovacao

-- Remover todas as versões com double precision
DROP FUNCTION IF EXISTS public.ip_inserir_ponto(
  p_lat double precision,
  p_lng double precision,
  p_tipo text,
  p_potencia integer,
  p_status text,
  p_modernizado boolean,
  p_endereco text,
  p_patrimonio text,
  p_obs text,
  p_tipo_ativo text,
  p_tipo_luminaria text,
  p_classe_nbr text,
  p_requer_aprovacao boolean
) CASCADE;

-- Versão consolidada: APENAS numeric com p_requer_aprovacao
-- (Já criada em 20260709_fix_rpc_enum_type_casting.sql, apenas confirmando unicidade)
CREATE OR REPLACE FUNCTION public.ip_inserir_ponto(
  p_lat numeric, p_lng numeric, p_tipo text, p_potencia integer,
  p_status text, p_modernizado boolean, p_endereco text, p_patrimonio text, p_obs text,
  p_tipo_ativo text, p_tipo_luminaria text, p_classe_nbr text, p_requer_aprovacao boolean
)
RETURNS text
LANGUAGE plpgsql
SECURITY DEFINER
AS $function$
DECLARE
  v_role TEXT;
  v_id UUID;
BEGIN
  SELECT role INTO v_role FROM public.profiles WHERE id = auth.uid();
  IF v_role IS NULL THEN v_role := 'leitura'; END IF;

  IF v_role NOT IN ('editor', 'admin') THEN
    RAISE EXCEPTION 'Permissão negada: apenas editores e administradores podem criar pontos';
  END IF;

  v_id := gen_random_uuid();

  INSERT INTO public.pontos_luminaria (
    id, latitude, longitude, tipo_ativo, tipo_luminaria,
    potencia, led_instalado, tipo_iluminacao, status, observacoes,
    endereco, patrimonio_enel, criado_em, criado_por
  ) VALUES (
    v_id,
    p_lat::double precision, p_lng::double precision, p_tipo_ativo::ativo_tipo,
    CASE WHEN p_tipo_luminaria IS NOT NULL THEN p_tipo_luminaria::luminaria_tipo ELSE NULL END,
    CASE WHEN p_tipo_ativo = 'luminaria' THEN p_potencia ELSE NULL END,
    CASE WHEN p_tipo_ativo = 'luminaria' THEN p_modernizado ELSE NULL END,
    CASE WHEN p_tipo_ativo = 'luminaria' THEN p_tipo ELSE NULL END,
    COALESCE(p_status, 'a_verificar'),
    COALESCE(p_obs, ''),
    p_endereco, p_patrimonio, NOW(), auth.uid()
  );

  RETURN v_id::TEXT;
END;
$function$;
