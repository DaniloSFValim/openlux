-- Fix: Corrigir coluna 'modernizado_led' obrigatória em ip_inserir_ponto
-- Problema: RPC estava inserindo NULL para ativos não-luminária (poste, caixa, etc)
-- Coluna tem NOT NULL com DEFAULT false, mas NULL explícito sobrescreve o default
-- Erro: "null value in column 'modernizado_led' violates not-null constraint"

-- Atualizar ip_inserir_ponto para sempre fornecer valor para modernizado_led
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
    id, geom, tipo_ativo, tipo_luminaria, potencia_w,
    modernizado_led, tipo_lampada, status, observacoes,
    endereco, numero_patrimonio, criado_em, criado_por, classe_nbr, fonte
  ) VALUES (
    v_id,
    ST_SetSRID(ST_MakePoint(p_lng::double precision, p_lat::double precision), 4326),
    p_tipo_ativo::ativo_tipo,
    CASE WHEN p_tipo_ativo = 'luminaria' AND p_tipo_luminaria IS NOT NULL THEN p_tipo_luminaria::luminaria_tipo ELSE NULL END,
    CASE WHEN p_tipo_ativo = 'luminaria' THEN p_potencia ELSE NULL END,
    CASE WHEN p_tipo_ativo = 'luminaria' THEN COALESCE(p_modernizado, false) ELSE false END,
    CASE WHEN p_tipo_ativo = 'luminaria' THEN p_tipo::tipo_lampada ELSE NULL END,
    COALESCE(p_status, 'a_verificar')::status_luminaria,
    COALESCE(p_obs, ''),
    p_endereco, p_patrimonio, NOW(), auth.uid(), p_classe_nbr,
    'levantamento_campo'::fonte_ponto
  );

  RETURN v_id::TEXT;
END;
$function$;
