-- Fix: Corrigir CAST do tipo ENUM em funções RPC
-- Problema: Funções ip_inserir_ponto e ip_atualizar_ponto não faziam CAST
-- correto de 'texto' para tipo ENUM 'luminaria_tipo', causando erro:
-- "column tipo_luminaria is of type luminaria_tipo but expression is of type text"

-- Atualizar ip_inserir_ponto (double precision version)
CREATE OR REPLACE FUNCTION public.ip_inserir_ponto(
  p_lat double precision, p_lng double precision, p_tipo text, p_potencia integer,
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
    potencia, led_instalado, tipo_iluminacao,
    status, observacoes, endereco, patrimonio_enel,
    criado_em, criado_por
  ) VALUES (
    v_id,
    p_lat, p_lng, p_tipo_ativo::ativo_tipo,
    CASE WHEN p_tipo_luminaria IS NOT NULL THEN p_tipo_luminaria::luminaria_tipo ELSE NULL END,
    CASE WHEN p_tipo_ativo = 'luminaria' THEN p_potencia ELSE NULL END,
    CASE WHEN p_tipo_ativo = 'luminaria' THEN p_modernizado ELSE NULL END,
    CASE WHEN p_tipo_ativo = 'luminaria' THEN p_tipo ELSE NULL END,
    COALESCE(p_status, 'a_verificar'),
    COALESCE(p_obs, ''),
    p_endereco,
    p_patrimonio,
    NOW(),
    auth.uid()
  );

  RETURN v_id::TEXT;
END;
$function$;

-- Atualizar ip_inserir_ponto (numeric version)
DROP FUNCTION IF EXISTS public.ip_inserir_ponto(numeric, numeric, text, integer, text, boolean, text, text, text, text, text, text, boolean);

CREATE FUNCTION public.ip_inserir_ponto(
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

-- Atualizar ip_atualizar_ponto com CAST correto
CREATE OR REPLACE FUNCTION public.ip_atualizar_ponto(
  p_id uuid, p_tipo text DEFAULT NULL::text, p_potencia integer DEFAULT NULL::integer,
  p_status text DEFAULT NULL::text, p_modernizado boolean DEFAULT NULL::boolean,
  p_obs text DEFAULT NULL::text, p_lat numeric DEFAULT NULL::numeric,
  p_lng numeric DEFAULT NULL::numeric, p_tipo_luminaria text DEFAULT NULL::text,
  p_classe_nbr text DEFAULT NULL::text, p_requer_aprovacao boolean DEFAULT false
)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
AS $function$
DECLARE
  v_user_id uuid;
  v_role text;
  v_dados_antes jsonb;
  v_dados_depois jsonb;
BEGIN
  v_user_id := auth.uid();
  IF v_user_id IS NULL THEN
    RETURN jsonb_build_object('error', 'Não autenticado');
  END IF;

  SELECT role INTO v_role FROM profiles WHERE id = v_user_id;
  IF v_role NOT IN ('editor', 'admin') THEN
    RETURN jsonb_build_object('error', 'Sem permissão para editar');
  END IF;

  SELECT to_jsonb(p.*) INTO v_dados_antes FROM v_parque_export p WHERE id = p_id;

  IF p_requer_aprovacao AND v_role != 'admin' THEN
    v_dados_depois := jsonb_build_object(
      'tipo_lampada', COALESCE(p_tipo, (v_dados_antes->>'tipo_lampada')),
      'potencia_w', COALESCE(p_potencia, (v_dados_antes->>'potencia_w')::int),
      'status', COALESCE(p_status, (v_dados_antes->>'status')),
      'modernizado_led', COALESCE(p_modernizado, (v_dados_antes->>'modernizado_led')::boolean),
      'observacoes', COALESCE(p_obs, (v_dados_antes->>'observacoes')),
      'lat', COALESCE(p_lat, (v_dados_antes->>'lat')::numeric),
      'lon', COALESCE(p_lng, (v_dados_antes->>'lon')::numeric),
      'tipo_luminaria', COALESCE(p_tipo_luminaria, (v_dados_antes->>'tipo_luminaria')),
      'classe_nbr', COALESCE(p_classe_nbr, (v_dados_antes->>'classe_nbr'))
    );

    INSERT INTO fila_aprovacao (tipo_operacao, tabela_alvo, registro_id, usuario_id, dados_antes, dados_depois)
    VALUES ('UPDATE', 'v_parque_export', p_id, v_user_id, v_dados_antes, v_dados_depois);

    UPDATE v_parque_export SET pendente_aprovacao = true WHERE id = p_id;

    RETURN jsonb_build_object('success', true, 'message', 'Alteração registrada - aguardando aprovação');
  END IF;

  -- Update with proper type casting for tipo_luminaria (ENUM)
  UPDATE v_parque_export SET
    tipo_lampada = COALESCE(p_tipo, tipo_lampada),
    potencia_w = COALESCE(p_potencia, potencia_w),
    status = COALESCE(p_status, status),
    modernizado_led = COALESCE(p_modernizado, modernizado_led),
    observacoes = COALESCE(p_obs, observacoes),
    lat = COALESCE(p_lat, lat),
    lon = COALESCE(p_lng, lon),
    tipo_luminaria = CASE
      WHEN p_tipo_luminaria IS NOT NULL THEN p_tipo_luminaria::luminaria_tipo
      ELSE tipo_luminaria
    END,
    classe_nbr = COALESCE(p_classe_nbr, classe_nbr),
    pendente_aprovacao = false,
    atualizado_em = now()
  WHERE id = p_id;

  RETURN jsonb_build_object('success', true, 'message', 'Ponto atualizado');
END;
$function$;
