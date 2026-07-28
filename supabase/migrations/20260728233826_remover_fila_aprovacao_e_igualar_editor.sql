-- Remove a fila de aprovacao e iguala editor a admin, exceto gestao de usuarios.
--
-- Regra do produto: a unica diferenca entre admin e editor e que o admin adiciona
-- e exclui usuarios. Editor faz tudo o mais — pontos, modelos, campanhas.
--
-- A fila de aprovacao nao existe mais como funcionalidade. Estava presente no
-- banco como codigo morto: `p_requer_aprovacao` tem DEFAULT false e o frontend
-- nunca passa true, entao o ramo da fila jamais era executado. Codigo morto que
-- parece vivo custa caro — foi o que me levou a um diagnostico errado do sintoma
-- relatado pelo editor.
--
-- ============================================================================
-- 1. ip_registrar_intervencao — estava QUEBRADA para todos os papeis
-- ============================================================================
--
-- Gravava em `intervencoes`, tabela que NAO EXISTE (a real e
-- `pontos_intervencoes`), e com nomes de coluna que tambem nao batem:
--
--   lampada_nova   -> tipo_lampada_nova
--   potencia_nova  -> potencia_nova_w
--   registrado_em  -> criado_em
--   id uuid        -> id bigint (nextval, nao deve ser fornecido)
--
-- Qualquer tentativa de registrar intervencao falhava com
-- 'relation "intervencoes" does not exist'. Confirmado em producao chamando a
-- funcao como editor e como admin. Nunca funcionou.

DROP FUNCTION IF EXISTS public.ip_registrar_intervencao(uuid, text, text, text, text, text, integer, boolean);

CREATE FUNCTION public.ip_registrar_intervencao(
  p_ponto uuid,
  p_tipo text,
  p_data text DEFAULT NULL,
  p_descricao text DEFAULT NULL,
  p_responsavel text DEFAULT NULL,
  p_lampada_nova text DEFAULT NULL,
  p_potencia_nova integer DEFAULT NULL
) RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO 'public'
AS $function$
DECLARE
  v_user_id uuid;
  v_role text;
BEGIN
  v_user_id := auth.uid();
  IF v_user_id IS NULL THEN
    RETURN jsonb_build_object('error', 'Não autenticado');
  END IF;

  SELECT role INTO v_role FROM public.profiles WHERE id = v_user_id;
  IF v_role IS NULL OR v_role NOT IN ('editor', 'admin') THEN
    RETURN jsonb_build_object('error', 'Sem permissão');
  END IF;

  IF NOT EXISTS (SELECT 1 FROM public.pontos_luminaria WHERE id = p_ponto) THEN
    RETURN jsonb_build_object('error', 'Ponto não encontrado');
  END IF;

  INSERT INTO public.pontos_intervencoes (
    ponto_id, tipo, data, descricao, responsavel,
    tipo_lampada_nova, potencia_nova_w, registrado_por
  ) VALUES (
    p_ponto,
    p_tipo::intervencao_tipo,
    COALESCE(p_data::date, CURRENT_DATE),
    p_descricao,
    p_responsavel,
    NULLIF(p_lampada_nova, '')::tipo_lampada,
    p_potencia_nova,
    COALESCE((SELECT email FROM public.profiles WHERE id = v_user_id), v_user_id::text)
  );

  RETURN jsonb_build_object('success', true, 'message', 'Intervenção registrada');
END;
$function$;

-- ============================================================================
-- 2. ip_atualizar_ponto — sem o ramo da fila e sem o parametro vestigial
-- ============================================================================

DROP FUNCTION IF EXISTS public.ip_atualizar_ponto(uuid, text, integer, text, boolean, text, numeric, numeric, text, text, boolean, integer, text);

CREATE FUNCTION public.ip_atualizar_ponto(
  p_id uuid,
  p_tipo text DEFAULT NULL,
  p_potencia integer DEFAULT NULL,
  p_status text DEFAULT NULL,
  p_modernizado boolean DEFAULT NULL,
  p_obs text DEFAULT NULL,
  p_lat numeric DEFAULT NULL,
  p_lng numeric DEFAULT NULL,
  p_tipo_luminaria text DEFAULT NULL,
  p_classe_nbr text DEFAULT NULL,
  p_angulo integer DEFAULT NULL,
  p_material text DEFAULT NULL
) RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO 'public'
AS $function$
DECLARE
  v_user_id uuid;
  v_role text;
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

  IF NOT EXISTS (SELECT 1 FROM public.pontos_luminaria WHERE id = p_id) THEN
    RETURN jsonb_build_object('error', 'Ponto não encontrado');
  END IF;

  -- Recenseamento: edicao durante campanha ativa carimba a verificacao
  SELECT id INTO v_camp FROM public.campanhas WHERE status='ativa' ORDER BY criado_em DESC LIMIT 1;

  UPDATE public.pontos_luminaria SET
    tipo_lampada    = COALESCE(p_tipo::tipo_lampada, tipo_lampada),
    potencia_w      = COALESCE(p_potencia, potencia_w),
    status          = COALESCE(p_status::status_luminaria, status),
    modernizado_led = COALESCE(p_modernizado, modernizado_led),
    observacoes     = COALESCE(p_obs, observacoes),
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
    atualizado_em = now()
  WHERE id = p_id;

  RETURN jsonb_build_object('success', true, 'message', 'Ponto atualizado');
END;
$function$;

-- ============================================================================
-- 3. ip_inserir_ponto — remove o parametro que ja era morto
-- ============================================================================
-- p_requer_aprovacao existia na assinatura e nunca era lido no corpo.

DROP FUNCTION IF EXISTS public.ip_inserir_ponto(numeric, numeric, text, integer, text, boolean, text, text, text, text, text, text, boolean, integer, text);

CREATE FUNCTION public.ip_inserir_ponto(
  p_lat numeric, p_lng numeric, p_tipo text, p_potencia integer, p_status text,
  p_modernizado boolean, p_endereco text, p_patrimonio text, p_obs text,
  p_tipo_ativo text, p_tipo_luminaria text, p_classe_nbr text,
  p_angulo integer DEFAULT NULL, p_material text DEFAULT NULL
) RETURNS text
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO 'public'
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

-- ============================================================================
-- 4. Campanhas: editor tambem cria e encerra
-- ============================================================================
-- Campanha e levantamento de campo, e quem faz campo e o editor. Exigir admin
-- deixava o editor travado: ip_confirmar_ponto exige campanha ativa, entao ele
-- nao conseguia verificar ponto nenhum sem pedir a um admin.

CREATE OR REPLACE FUNCTION public.ip_criar_campanha(p_nome text, p_descricao text DEFAULT NULL)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path TO 'public'
AS $function$
DECLARE v_role text; v_id uuid;
BEGIN
  SELECT role INTO v_role FROM public.profiles WHERE id = auth.uid();
  IF v_role IS NULL OR v_role NOT IN ('editor','admin') THEN
    RETURN jsonb_build_object('error','Sem permissão para criar campanhas');
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
  IF v_role IS NULL OR v_role NOT IN ('editor','admin') THEN
    RETURN jsonb_build_object('error','Sem permissão para encerrar campanhas');
  END IF;
  UPDATE public.campanhas SET status='encerrada', encerrada_em=now()
  WHERE id = p_id AND status='ativa';
  IF NOT FOUND THEN
    RETURN jsonb_build_object('error','Campanha não encontrada ou já encerrada');
  END IF;
  RETURN jsonb_build_object('success', true);
END $function$;

-- ============================================================================
-- 5. RLS: editor equiparado a admin, exceto em profiles
-- ============================================================================
-- profiles fica intocado: gestao de usuarios segue exclusiva do admin, que e a
-- unica diferenca de papel que o produto mantem.

-- Modelos: criar e remover deixam de exigir admin
DROP POLICY IF EXISTS modelos_writable ON public.equipamentos_modelo;
CREATE POLICY modelos_writable ON public.equipamentos_modelo
  FOR INSERT TO public
  WITH CHECK (EXISTS (SELECT 1 FROM public.profiles
                      WHERE id = auth.uid() AND role IN ('admin','editor')));

DROP POLICY IF EXISTS modelos_deletable ON public.equipamentos_modelo;
CREATE POLICY modelos_deletable ON public.equipamentos_modelo
  FOR DELETE TO public
  USING (EXISTS (SELECT 1 FROM public.profiles
                 WHERE id = auth.uid() AND role IN ('admin','editor')));

-- Pontos: excluir deixa de exigir admin
DROP POLICY IF EXISTS pontos_delete ON public.pontos_luminaria;
CREATE POLICY pontos_delete ON public.pontos_luminaria
  FOR DELETE TO public
  USING (EXISTS (SELECT 1 FROM public.profiles
                 WHERE id = auth.uid() AND role IN ('admin','editor')));

-- Ativos removidos: quem exclui precisa poder desfazer
DROP POLICY IF EXISTS removidos_admin_all ON public.ativos_removidos;
CREATE POLICY removidos_admin_all ON public.ativos_removidos
  FOR ALL TO public
  USING (EXISTS (SELECT 1 FROM public.profiles
                 WHERE id = auth.uid() AND role IN ('admin','editor')))
  WITH CHECK (EXISTS (SELECT 1 FROM public.profiles
                      WHERE id = auth.uid() AND role IN ('admin','editor')));

DROP POLICY IF EXISTS removidos_view ON public.ativos_removidos;
CREATE POLICY removidos_view ON public.ativos_removidos
  FOR SELECT TO public
  USING (EXISTS (SELECT 1 FROM public.profiles
                 WHERE id = auth.uid() AND role IN ('admin','editor')));

-- Configuracao do site (aparencia e painel descritivo)
DROP POLICY IF EXISTS "config admin escreve" ON public.site_config;
CREATE POLICY "config admin escreve" ON public.site_config
  FOR UPDATE TO public
  USING (EXISTS (SELECT 1 FROM public.profiles
                 WHERE id = auth.uid() AND role IN ('admin','editor')));

DROP POLICY IF EXISTS admin_update_painel_config ON public.site_config;
CREATE POLICY admin_update_painel_config ON public.site_config
  FOR UPDATE TO public
  USING (EXISTS (SELECT 1 FROM public.profiles
                 WHERE id = auth.uid() AND role IN ('admin','editor')))
  WITH CHECK (EXISTS (SELECT 1 FROM public.profiles
                      WHERE id = auth.uid() AND role IN ('admin','editor')));

-- ============================================================================
-- 6. Remover o que sobrou da fila
-- ============================================================================
-- Nenhuma view depende de fila_aprovacao nem de pendente_aprovacao — verificado
-- no catalogo antes de remover. As unicas 3 funcoes que os citavam foram
-- reescritas acima ou serao removidas aqui.

DROP FUNCTION IF EXISTS public.aprovar_mudanca(uuid, boolean, text);
DROP TABLE IF EXISTS public.fila_aprovacao;
ALTER TABLE public.pontos_luminaria DROP COLUMN IF EXISTS pendente_aprovacao;
