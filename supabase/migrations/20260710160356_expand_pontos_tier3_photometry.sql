-- Tier 3 · Fotometria de instalacao (Fase 1 angulo + Fase 2 material do piso)
-- Captura, por ponto, o angulo de apontamento do facho e o material do piso,
-- insumos para os indices de aproveitamento no piso e de poluicao luminosa.
-- Colunas nullable (backward-compat com os 42k pontos existentes).
--
-- APLICADA EM PRODUCAO em 2026-07-10 (versao 20260710160356).
-- Documentacao do modelo: docs/FIELD_REFERENCE_TIER3_PHOTOMETRY.md

-- 1) Tabela de referencia: refletancia difusa media (rho) por material de piso.
--    Estatica, leitura publica, citavel em analises SQL e no artigo.
CREATE TABLE IF NOT EXISTS public.ref_material_piso (
  material     text PRIMARY KEY,
  rotulo       text NOT NULL,
  refletancia  numeric(3,2) NOT NULL CHECK (refletancia >= 0 AND refletancia <= 1),
  fonte        text
);

INSERT INTO public.ref_material_piso (material, rotulo, refletancia, fonte) VALUES
  ('asfalto_novo',       'Asfalto novo (escuro)',       0.07, 'CIE 144 / ABNT NBR 5101'),
  ('asfalto_desgastado', 'Asfalto desgastado (claro)',  0.12, 'CIE 144'),
  ('concreto',           'Concreto / cimento',          0.30, 'CIE 144 / IESNA'),
  ('paralelepipedo',     'Paralelepipedo / pedra',      0.18, 'CIE 144'),
  ('terra',              'Terra batida',                0.20, 'CIE 30.2'),
  ('vegetacao',          'Vegetacao / grama',           0.08, 'CIE 30.2'),
  ('areia',              'Areia',                       0.25, 'CIE 30.2'),
  ('agua',               'Agua (espelho d''agua)',      0.06, 'CIE 30.2')
ON CONFLICT (material) DO NOTHING;

ALTER TABLE public.ref_material_piso ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS ref_material_piso_read ON public.ref_material_piso;
CREATE POLICY ref_material_piso_read ON public.ref_material_piso FOR SELECT USING (true);
GRANT SELECT ON public.ref_material_piso TO anon, authenticated, service_role;

-- 2) Colunas em pontos_luminaria
ALTER TABLE public.pontos_luminaria
  ADD COLUMN IF NOT EXISTS angulo_inclinacao_graus smallint
    CHECK (angulo_inclinacao_graus IS NULL OR angulo_inclinacao_graus IN (0,15,30,45,60,75,90,120)),
  ADD COLUMN IF NOT EXISTS material_piso text
    REFERENCES public.ref_material_piso(material);

COMMENT ON COLUMN public.pontos_luminaria.angulo_inclinacao_graus IS
  'Tier 3 fotometria: angulo de apontamento do facho a partir da vertical descendente (nadir). 0=reto para baixo (full-cutoff, ideal), 90=horizontal, 120=uplight.';
COMMENT ON COLUMN public.pontos_luminaria.material_piso IS
  'Tier 3 fotometria: material predominante do piso sob a luminaria (FK ref_material_piso; define a refletancia rho).';

-- 3) Recriar RPCs de escrita com 2 parametros novos (DEFAULT NULL, sem overload)
DROP FUNCTION IF EXISTS public.ip_inserir_ponto(numeric,numeric,text,integer,text,boolean,text,text,text,text,text,text,boolean);
CREATE FUNCTION public.ip_inserir_ponto(
  p_lat numeric, p_lng numeric, p_tipo text, p_potencia integer, p_status text,
  p_modernizado boolean, p_endereco text, p_patrimonio text, p_obs text,
  p_tipo_ativo text, p_tipo_luminaria text, p_classe_nbr text, p_requer_aprovacao boolean,
  p_angulo integer DEFAULT NULL, p_material text DEFAULT NULL)
RETURNS text
LANGUAGE plpgsql SECURITY DEFINER SET search_path TO 'public'
AS $function$
DECLARE
  v_role TEXT;
  v_id UUID;
BEGIN
  SELECT role INTO v_role FROM public.profiles WHERE id = auth.uid();
  IF v_role IS NULL THEN v_role := 'leitura'; END IF;

  IF v_role NOT IN ('editor', 'admin') THEN
    RAISE EXCEPTION 'Permissao negada: apenas editores e administradores podem criar pontos';
  END IF;

  v_id := gen_random_uuid();

  INSERT INTO public.pontos_luminaria (
    id, geom, tipo_ativo, tipo_luminaria, potencia_w,
    modernizado_led, tipo_lampada, status, observacoes,
    endereco, numero_patrimonio, criado_em, criado_por, classe_nbr, fonte,
    angulo_inclinacao_graus, material_piso
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
    'levantamento_campo'::fonte_ponto,
    CASE WHEN p_tipo_ativo = 'luminaria' THEN p_angulo ELSE NULL END,
    CASE WHEN p_tipo_ativo = 'luminaria' THEN p_material ELSE NULL END
  );

  RETURN v_id::TEXT;
END;
$function$;

DROP FUNCTION IF EXISTS public.ip_atualizar_ponto(uuid,text,integer,text,boolean,text,numeric,numeric,text,text,boolean);
CREATE FUNCTION public.ip_atualizar_ponto(
  p_id uuid, p_tipo text DEFAULT NULL, p_potencia integer DEFAULT NULL, p_status text DEFAULT NULL,
  p_modernizado boolean DEFAULT NULL, p_obs text DEFAULT NULL, p_lat numeric DEFAULT NULL, p_lng numeric DEFAULT NULL,
  p_tipo_luminaria text DEFAULT NULL, p_classe_nbr text DEFAULT NULL, p_requer_aprovacao boolean DEFAULT false,
  p_angulo integer DEFAULT NULL, p_material text DEFAULT NULL)
RETURNS jsonb
LANGUAGE plpgsql SECURITY DEFINER SET search_path TO 'public'
AS $function$
DECLARE
  v_user_id uuid;
  v_role text;
  v_dados_antes jsonb;
  v_dados_depois jsonb;
BEGIN
  v_user_id := auth.uid();
  IF v_user_id IS NULL THEN
    RETURN jsonb_build_object('error', 'Nao autenticado');
  END IF;

  SELECT role INTO v_role FROM public.profiles WHERE id = v_user_id;
  IF v_role IS NULL OR v_role NOT IN ('editor', 'admin') THEN
    RETURN jsonb_build_object('error', 'Sem permissao para editar');
  END IF;

  SELECT to_jsonb(p.*) INTO v_dados_antes FROM public.v_parque_export p WHERE id = p_id;
  IF v_dados_antes IS NULL THEN
    RETURN jsonb_build_object('error', 'Ponto nao encontrado');
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
      'classe_nbr', COALESCE(p_classe_nbr, (v_dados_antes->>'classe_nbr')),
      'angulo_inclinacao_graus', COALESCE(p_angulo, (v_dados_antes->>'angulo_inclinacao_graus')::int),
      'material_piso', COALESCE(p_material, (v_dados_antes->>'material_piso'))
    );

    INSERT INTO public.fila_aprovacao (tipo_operacao, tabela_alvo, registro_id, usuario_id, dados_antes, dados_depois)
    VALUES ('UPDATE', 'pontos_luminaria', p_id, v_user_id, v_dados_antes, v_dados_depois);

    UPDATE public.pontos_luminaria SET pendente_aprovacao = true WHERE id = p_id;

    RETURN jsonb_build_object('success', true, 'message', 'Alteracao registrada - aguardando aprovacao');
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
    angulo_inclinacao_graus = COALESCE(p_angulo, angulo_inclinacao_graus),
    material_piso = COALESCE(p_material, material_piso),
    pendente_aprovacao = false,
    atualizado_em = now()
  WHERE id = p_id;

  RETURN jsonb_build_object('success', true, 'message', 'Ponto atualizado');
END;
$function$;

-- 4) Re-aplicar hardening de grants (mesma politica da migration 20260709183630)
REVOKE EXECUTE ON FUNCTION public.ip_inserir_ponto(numeric,numeric,text,integer,text,boolean,text,text,text,text,text,text,boolean,integer,text) FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION public.ip_inserir_ponto(numeric,numeric,text,integer,text,boolean,text,text,text,text,text,text,boolean,integer,text) FROM anon;
GRANT  EXECUTE ON FUNCTION public.ip_inserir_ponto(numeric,numeric,text,integer,text,boolean,text,text,text,text,text,text,boolean,integer,text) TO authenticated;
GRANT  EXECUTE ON FUNCTION public.ip_inserir_ponto(numeric,numeric,text,integer,text,boolean,text,text,text,text,text,text,boolean,integer,text) TO service_role;

REVOKE EXECUTE ON FUNCTION public.ip_atualizar_ponto(uuid,text,integer,text,boolean,text,numeric,numeric,text,text,boolean,integer,text) FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION public.ip_atualizar_ponto(uuid,text,integer,text,boolean,text,numeric,numeric,text,text,boolean,integer,text) FROM anon;
GRANT  EXECUTE ON FUNCTION public.ip_atualizar_ponto(uuid,text,integer,text,boolean,text,numeric,numeric,text,text,boolean,integer,text) TO authenticated;
GRANT  EXECUTE ON FUNCTION public.ip_atualizar_ponto(uuid,text,integer,text,boolean,text,numeric,numeric,text,text,boolean,integer,text) TO service_role;

-- 5) Expor as 2 colunas no read-path (view + bbox), sem alterar assinaturas
CREATE OR REPLACE VIEW public.v_parque_export AS
 SELECT id,
    numero_patrimonio,
    endereco,
    bairro_nome,
    tipo_lampada,
    potencia_w,
    status,
    modernizado_led,
    fonte,
    fonte_modernizacao,
    data_modernizacao,
    censo_tipo_original,
    censo_potencia_original,
    bairro_enel,
    status_operacional_censo,
    flag_revisao_censo,
    criado_por,
    st_y(geom) AS lat,
    st_x(geom) AS lon,
    criado_em,
    atualizado_em,
    observacoes,
    codigo_seconser,
    tipo_ativo,
    tipo_luminaria,
    classe_nbr,
    health_status,
    angulo_inclinacao_graus,
    material_piso
   FROM pontos_luminaria;

CREATE OR REPLACE FUNCTION public.ip_pontos_bbox(min_lng double precision, min_lat double precision, max_lng double precision, max_lat double precision, limite integer DEFAULT 4000, p_bairro text DEFAULT NULL::text, p_tipo text DEFAULT NULL::text, p_modernizado boolean DEFAULT NULL::boolean, p_pot_min integer DEFAULT NULL::integer, p_revisao boolean DEFAULT NULL::boolean, p_fonte_mod text DEFAULT NULL::text, p_suspeito boolean DEFAULT NULL::boolean, p_led_min integer DEFAULT NULL::integer, p_led_max integer DEFAULT NULL::integer, p_power_min integer DEFAULT NULL::integer, p_power_max integer DEFAULT NULL::integer, p_data_inicio date DEFAULT NULL::date, p_data_fim date DEFAULT NULL::date, p_health_status text DEFAULT NULL::text)
 RETURNS json
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  SELECT coalesce(json_agg(row_to_json(t)),'[]'::json) FROM (
    SELECT id, ST_Y(geom) lat, ST_X(geom) lon, modernizado_led, tipo_lampada,
           potencia_w, status, bairro_nome, numero_patrimonio, endereco, fonte,
           fonte_modernizacao, censo_tipo_original, observacoes, flag_revisao_censo,
           codigo_seconser, tipo_ativo, tipo_luminaria, classe_nbr, health_status,
           angulo_inclinacao_graus, material_piso
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
