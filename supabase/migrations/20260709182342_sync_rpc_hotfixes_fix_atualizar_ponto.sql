-- Sincroniza no histórico de migrations o estado real dos RPCs corrigidos
-- (hotfixes aplicados manualmente em 2026-07-09) e corrige ip_atualizar_ponto,
-- que fazia UPDATE na view v_parque_export referenciando colunas
-- inexistentes/calculadas (pendente_aprovacao não projetada; lat/lon são
-- st_y/st_x, não atualizáveis).
--
-- APLICADA EM PRODUÇÃO em 2026-07-09 (versão 20260709182342).

-- ============================================================
-- 1. ip_inserir_ponto — estado atual (geom + fonte + modernizado_led)
-- ============================================================
CREATE OR REPLACE FUNCTION public.ip_inserir_ponto(
  p_lat numeric, p_lng numeric, p_tipo text, p_potencia integer,
  p_status text, p_modernizado boolean, p_endereco text, p_patrimonio text, p_obs text,
  p_tipo_ativo text, p_tipo_luminaria text, p_classe_nbr text, p_requer_aprovacao boolean
)
RETURNS text
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
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

-- ============================================================
-- 2. ip_atualizar_ponto — FIX: UPDATE direto em pontos_luminaria
-- ============================================================
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
SET search_path = public
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

  SELECT role INTO v_role FROM public.profiles WHERE id = v_user_id;
  IF v_role IS NULL OR v_role NOT IN ('editor', 'admin') THEN
    RETURN jsonb_build_object('error', 'Sem permissão para editar');
  END IF;

  SELECT to_jsonb(p.*) INTO v_dados_antes FROM public.v_parque_export p WHERE id = p_id;
  IF v_dados_antes IS NULL THEN
    RETURN jsonb_build_object('error', 'Ponto não encontrado');
  END IF;

  IF p_requer_aprovacao AND v_role <> 'admin' THEN
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

    INSERT INTO public.fila_aprovacao (tipo_operacao, tabela_alvo, registro_id, usuario_id, dados_antes, dados_depois)
    VALUES ('UPDATE', 'pontos_luminaria', p_id, v_user_id, v_dados_antes, v_dados_depois);

    UPDATE public.pontos_luminaria SET pendente_aprovacao = true WHERE id = p_id;

    RETURN jsonb_build_object('success', true, 'message', 'Alteração registrada - aguardando aprovação');
  END IF;

  UPDATE public.pontos_luminaria SET
    tipo_lampada = COALESCE(p_tipo::tipo_lampada, tipo_lampada),
    potencia_w = COALESCE(p_potencia, potencia_w),
    status = COALESCE(p_status::status_luminaria, status),
    modernizado_led = COALESCE(p_modernizado, modernizado_led),
    observacoes = COALESCE(p_obs, observacoes),
    geom = CASE WHEN p_lat IS NOT NULL AND p_lng IS NOT NULL
                THEN ST_SetSRID(ST_MakePoint(p_lng::double precision, p_lat::double precision), 4326)
                ELSE geom END,
    tipo_luminaria = CASE WHEN p_tipo_luminaria IS NOT NULL
                          THEN p_tipo_luminaria::luminaria_tipo
                          ELSE tipo_luminaria END,
    classe_nbr = COALESCE(p_classe_nbr, classe_nbr),
    pendente_aprovacao = false,
    atualizado_em = now()
  WHERE id = p_id;

  RETURN jsonb_build_object('success', true, 'message', 'Ponto atualizado');
END;
$function$;

-- ============================================================
-- 3. v_parque_export — estado atual (inclui health_status)
-- ============================================================
CREATE OR REPLACE VIEW public.v_parque_export AS
SELECT
  id, numero_patrimonio, endereco, bairro_nome, tipo_lampada, potencia_w,
  status, modernizado_led, fonte, fonte_modernizacao, data_modernizacao,
  censo_tipo_original, censo_potencia_original, bairro_enel,
  status_operacional_censo, flag_revisao_censo, criado_por,
  st_y(geom) AS lat, st_x(geom) AS lon,
  criado_em, atualizado_em, observacoes, codigo_seconser,
  tipo_ativo, tipo_luminaria, classe_nbr, health_status
FROM pontos_luminaria;
