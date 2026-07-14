-- OpenLux Fase 1+2: entidade municipio (cidade como dado) + campanhas de
-- recenseamento com estado herdado/verificado por ponto.
-- Compat total: colunas nullable, assinaturas de ip_inserir/atualizar_ponto
-- INALTERADAS (CREATE OR REPLACE preserva grants). bbox/clusters ganham 1 parametro
-- novo com DEFAULT (DROP+CREATE + re-grant, padrao ja validado).
--
-- APLICADA EM PRODUCAO em 2026-07-11 (versao 20260711155442).
-- NOTA: este arquivo e o espelho fiel do SQL aplicado via MCP apply_migration.

-- ============ FASE 1: municipio ============
CREATE TABLE IF NOT EXISTS public.municipios (
  id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  slug       text UNIQUE NOT NULL,
  nome       text NOT NULL,
  uf         text,
  criado_em  timestamptz NOT NULL DEFAULT now()
);
INSERT INTO public.municipios (slug, nome, uf)
VALUES ('niteroi', 'Niterói', 'RJ')
ON CONFLICT (slug) DO NOTHING;

ALTER TABLE public.municipios ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS municipios_read ON public.municipios;
CREATE POLICY municipios_read ON public.municipios FOR SELECT USING (true);
GRANT SELECT ON public.municipios TO anon, authenticated, service_role;

ALTER TABLE public.pontos_luminaria
  ADD COLUMN IF NOT EXISTS municipio_id uuid REFERENCES public.municipios(id);

-- ============ FASE 2: campanhas de recenseamento ============
CREATE TABLE IF NOT EXISTS public.campanhas (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  municipio_id  uuid REFERENCES public.municipios(id),
  nome          text NOT NULL,
  descricao     text,
  status        text NOT NULL DEFAULT 'ativa' CHECK (status IN ('ativa','encerrada')),
  criado_por    uuid,
  criado_em     timestamptz NOT NULL DEFAULT now(),
  encerrada_em  timestamptz
);
ALTER TABLE public.campanhas ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS campanhas_read ON public.campanhas;
CREATE POLICY campanhas_read ON public.campanhas FOR SELECT USING (true);
GRANT SELECT ON public.campanhas TO anon, authenticated, service_role;

ALTER TABLE public.pontos_luminaria
  ADD COLUMN IF NOT EXISTS verificado_em  timestamptz,
  ADD COLUMN IF NOT EXISTS verificado_por uuid,
  ADD COLUMN IF NOT EXISTS campanha_id    uuid REFERENCES public.campanhas(id);

COMMENT ON COLUMN public.pontos_luminaria.verificado_em IS
  'Recenseamento: momento em que o dado do ponto foi verificado em campo. NULL = dado herdado (censo/base historica), nunca verificado.';

CREATE INDEX IF NOT EXISTS idx_pontos_campanha ON public.pontos_luminaria (campanha_id);
CREATE INDEX IF NOT EXISTS idx_pontos_municipio ON public.pontos_luminaria (municipio_id);

-- Backfill municipio + defaults (single-tenant: Niterói)
DO $$
DECLARE v uuid;
BEGIN
  SELECT id INTO v FROM public.municipios WHERE slug='niteroi';
  UPDATE public.pontos_luminaria SET municipio_id = v WHERE municipio_id IS NULL;
  EXECUTE format('ALTER TABLE public.pontos_luminaria ALTER COLUMN municipio_id SET DEFAULT %L', v);
  EXECUTE format('ALTER TABLE public.campanhas ALTER COLUMN municipio_id SET DEFAULT %L', v);
END $$;

-- ============ RPCs de campanha ============
CREATE OR REPLACE FUNCTION public.ip_criar_campanha(p_nome text, p_descricao text DEFAULT NULL)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path TO 'public'
AS $function$
DECLARE v_role text; v_id uuid;
BEGIN
  SELECT role INTO v_role FROM public.profiles WHERE id = auth.uid();
  IF v_role IS DISTINCT FROM 'admin' THEN
    RETURN jsonb_build_object('error','Apenas administradores criam campanhas');
  END IF;
  IF coalesce(trim(p_nome),'') = '' THEN
    RETURN jsonb_build_object('error','Informe o nome da campanha');
  END IF;
  IF EXISTS (SELECT 1 FROM public.campanhas WHERE status='ativa') THEN
    RETURN jsonb_build_object('error','Já existe uma campanha ativa — encerre-a antes de criar outra');
  END IF;
  INSERT INTO public.campanhas (nome, descricao, criado_por)
  VALUES (trim(p_nome), nullif(trim(coalesce(p_descricao,'')),''), auth.uid())
  RETURNING id INTO v_id;
  RETURN jsonb_build_object('success', true, 'id', v_id);
END $function$;

CREATE OR REPLACE FUNCTION public.ip_encerrar_campanha(p_id uuid)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path TO 'public'
AS $function$
DECLARE v_role text;
BEGIN
  SELECT role INTO v_role FROM public.profiles WHERE id = auth.uid();
  IF v_role IS DISTINCT FROM 'admin' THEN
    RETURN jsonb_build_object('error','Apenas administradores encerram campanhas');
  END IF;
  UPDATE public.campanhas SET status='encerrada', encerrada_em=now()
  WHERE id = p_id AND status='ativa';
  IF NOT FOUND THEN
    RETURN jsonb_build_object('error','Campanha não encontrada ou já encerrada');
  END IF;
  RETURN jsonb_build_object('success', true);
END $function$;

CREATE OR REPLACE FUNCTION public.ip_listar_campanhas()
RETURNS json LANGUAGE sql STABLE SECURITY DEFINER SET search_path TO 'public'
AS $function$
  SELECT coalesce(json_agg(row_to_json(t)),'[]'::json) FROM (
    SELECT c.id, c.nome, c.descricao, c.status, c.criado_em, c.encerrada_em,
           (SELECT count(*) FROM pontos_luminaria pl WHERE pl.campanha_id = c.id) AS verificados,
           (SELECT count(*) FROM pontos_luminaria) AS total_parque
    FROM campanhas c
    ORDER BY c.criado_em DESC) t;
$function$;

CREATE OR REPLACE FUNCTION public.ip_confirmar_ponto(p_id uuid)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path TO 'public'
AS $function$
DECLARE v_user uuid; v_role text; v_camp uuid; v_nome text;
BEGIN
  v_user := auth.uid();
  IF v_user IS NULL THEN RETURN jsonb_build_object('error','Não autenticado'); END IF;
  SELECT role INTO v_role FROM public.profiles WHERE id = v_user;
  IF v_role IS NULL OR v_role NOT IN ('editor','admin') THEN
    RETURN jsonb_build_object('error','Sem permissão para verificar pontos');
  END IF;
  SELECT id, nome INTO v_camp, v_nome FROM public.campanhas
  WHERE status='ativa' ORDER BY criado_em DESC LIMIT 1;
  IF v_camp IS NULL THEN
    RETURN jsonb_build_object('error','Nenhuma campanha de recenseamento ativa — crie uma em Admin → Campanhas');
  END IF;
  UPDATE public.pontos_luminaria
  SET verificado_em=now(), verificado_por=v_user, campanha_id=v_camp, atualizado_em=now()
  WHERE id = p_id;
  IF NOT FOUND THEN RETURN jsonb_build_object('error','Ponto não encontrado'); END IF;
  RETURN jsonb_build_object('success', true, 'campanha', v_nome);
END $function$;

-- Grants das novas funções
REVOKE EXECUTE ON FUNCTION public.ip_criar_campanha(text,text) FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION public.ip_criar_campanha(text,text) FROM anon;
GRANT  EXECUTE ON FUNCTION public.ip_criar_campanha(text,text) TO authenticated, service_role;
REVOKE EXECUTE ON FUNCTION public.ip_encerrar_campanha(uuid) FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION public.ip_encerrar_campanha(uuid) FROM anon;
GRANT  EXECUTE ON FUNCTION public.ip_encerrar_campanha(uuid) TO authenticated, service_role;
REVOKE EXECUTE ON FUNCTION public.ip_confirmar_ponto(uuid) FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION public.ip_confirmar_ponto(uuid) FROM anon;
GRANT  EXECUTE ON FUNCTION public.ip_confirmar_ponto(uuid) TO authenticated, service_role;
GRANT  EXECUTE ON FUNCTION public.ip_listar_campanhas() TO anon, authenticated, service_role;

-- ============ Carimbo de verificação nos RPCs de escrita ============
-- Mesmas assinaturas → CREATE OR REPLACE (grants preservados, zero overload)
CREATE OR REPLACE FUNCTION public.ip_inserir_ponto(
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
  v_camp uuid;
BEGIN
  SELECT role INTO v_role FROM public.profiles WHERE id = auth.uid();
  IF v_role IS NULL THEN v_role := 'leitura'; END IF;

  IF v_role NOT IN ('editor', 'admin') THEN
    RAISE EXCEPTION 'Permissão negada: apenas editores e administradores podem criar pontos';
  END IF;

  v_id := gen_random_uuid();
  SELECT id INTO v_camp FROM public.campanhas WHERE status='ativa' ORDER BY criado_em DESC LIMIT 1;

  INSERT INTO public.pontos_luminaria (
    id, geom, tipo_ativo, tipo_luminaria, potencia_w,
    modernizado_led, tipo_lampada, status, observacoes,
    endereco, numero_patrimonio, criado_em, criado_por, classe_nbr, fonte,
    angulo_inclinacao_graus, material_piso,
    verificado_em, verificado_por, campanha_id
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
    CASE WHEN p_tipo_ativo = 'luminaria' THEN p_material ELSE NULL END,
    now(), auth.uid(), v_camp
  );

  RETURN v_id::TEXT;
END;
$function$;

CREATE OR REPLACE FUNCTION public.ip_atualizar_ponto(
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
  v_camp uuid;
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
      'classe_nbr', COALESCE(p_classe_nbr, (v_dados_antes->>'classe_nbr')),
      'angulo_inclinacao_graus', COALESCE(p_angulo, (v_dados_antes->>'angulo_inclinacao_graus')::int),
      'material_piso', COALESCE(p_material, (v_dados_antes->>'material_piso'))
    );

    INSERT INTO public.fila_aprovacao (tipo_operacao, tabela_alvo, registro_id, usuario_id, dados_antes, dados_depois)
    VALUES ('UPDATE', 'pontos_luminaria', p_id, v_user_id, v_dados_antes, v_dados_depois);

    UPDATE public.pontos_luminaria SET pendente_aprovacao = true WHERE id = p_id;

    RETURN jsonb_build_object('success', true, 'message', 'Alteração registrada - aguardando aprovação');
  END IF;

  -- Recenseamento: edição direta durante campanha ativa carimba a verificação
  SELECT id INTO v_camp FROM public.campanhas WHERE status='ativa' ORDER BY criado_em DESC LIMIT 1;

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
    verificado_em  = CASE WHEN v_camp IS NOT NULL THEN now() ELSE verificado_em END,
    verificado_por = CASE WHEN v_camp IS NOT NULL THEN v_user_id ELSE verificado_por END,
    campanha_id    = CASE WHEN v_camp IS NOT NULL THEN v_camp ELSE campanha_id END,
    pendente_aprovacao = false,
    atualizado_em = now()
  WHERE id = p_id;

  RETURN jsonb_build_object('success', true, 'message', 'Ponto atualizado');
END;
$function$;

-- ============ Read-path: expor verificação + filtro "não verificados" ============
CREATE OR REPLACE VIEW public.v_parque_export AS
 SELECT id, numero_patrimonio, endereco, bairro_nome, tipo_lampada, potencia_w,
    status, modernizado_led, fonte, fonte_modernizacao, data_modernizacao,
    censo_tipo_original, censo_potencia_original, bairro_enel,
    status_operacional_censo, flag_revisao_censo, criado_por,
    st_y(geom) AS lat, st_x(geom) AS lon, criado_em, atualizado_em, observacoes,
    codigo_seconser, tipo_ativo, tipo_luminaria, classe_nbr, health_status,
    angulo_inclinacao_graus, material_piso,
    verificado_em, campanha_id
   FROM pontos_luminaria;

DROP FUNCTION IF EXISTS public.ip_pontos_bbox(double precision,double precision,double precision,double precision,integer,text,text,boolean,integer,boolean,text,boolean,integer,integer,integer,integer,date,date,text);
CREATE FUNCTION public.ip_pontos_bbox(min_lng double precision, min_lat double precision, max_lng double precision, max_lat double precision, limite integer DEFAULT 4000, p_bairro text DEFAULT NULL::text, p_tipo text DEFAULT NULL::text, p_modernizado boolean DEFAULT NULL::boolean, p_pot_min integer DEFAULT NULL::integer, p_revisao boolean DEFAULT NULL::boolean, p_fonte_mod text DEFAULT NULL::text, p_suspeito boolean DEFAULT NULL::boolean, p_led_min integer DEFAULT NULL::integer, p_led_max integer DEFAULT NULL::integer, p_power_min integer DEFAULT NULL::integer, p_power_max integer DEFAULT NULL::integer, p_data_inicio date DEFAULT NULL::date, p_data_fim date DEFAULT NULL::date, p_health_status text DEFAULT NULL::text, p_nao_verificado boolean DEFAULT NULL::boolean)
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
           angulo_inclinacao_graus, material_piso, verificado_em, campanha_id
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
      AND (p_nao_verificado IS NULL OR (p_nao_verificado AND verificado_em IS NULL) OR (NOT p_nao_verificado AND verificado_em IS NOT NULL))
    LIMIT limite) t;
$function$;

DROP FUNCTION IF EXISTS public.ip_clusters_grid(double precision,double precision,double precision,double precision,double precision,text,text,boolean,integer,boolean,text,boolean,integer,integer,integer,integer,date,date,text);
CREATE FUNCTION public.ip_clusters_grid(min_lng double precision, min_lat double precision, max_lng double precision, max_lat double precision, grid_deg double precision, p_bairro text DEFAULT NULL::text, p_tipo text DEFAULT NULL::text, p_modernizado boolean DEFAULT NULL::boolean, p_pot_min integer DEFAULT NULL::integer, p_revisao boolean DEFAULT NULL::boolean, p_fonte_mod text DEFAULT NULL::text, p_suspeito boolean DEFAULT NULL::boolean, p_led_min integer DEFAULT NULL::integer, p_led_max integer DEFAULT NULL::integer, p_power_min integer DEFAULT NULL::integer, p_power_max integer DEFAULT NULL::integer, p_data_inicio date DEFAULT NULL::date, p_data_fim date DEFAULT NULL::date, p_health_status text DEFAULT NULL::text, p_nao_verificado boolean DEFAULT NULL::boolean)
 RETURNS json
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  SELECT coalesce(json_agg(row_to_json(t)),'[]'::json) FROM (
    SELECT count(*) n, count(*) FILTER (WHERE modernizado_led) led,
           avg(ST_X(geom)) lon, avg(ST_Y(geom)) lat
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
      AND (p_nao_verificado IS NULL OR (p_nao_verificado AND verificado_em IS NULL) OR (NOT p_nao_verificado AND verificado_em IS NOT NULL))
    GROUP BY ST_SnapToGrid(geom, grid_deg)) t;
$function$;

-- Re-grant (leitura pública: o mapa funciona sem login)
GRANT EXECUTE ON FUNCTION public.ip_pontos_bbox(double precision,double precision,double precision,double precision,integer,text,text,boolean,integer,boolean,text,boolean,integer,integer,integer,integer,date,date,text,boolean) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.ip_clusters_grid(double precision,double precision,double precision,double precision,double precision,text,text,boolean,integer,boolean,text,boolean,integer,integer,integer,integer,date,date,text,boolean) TO anon, authenticated, service_role;
