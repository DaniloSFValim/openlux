-- Fase 2.1 do recenseamento + conserto latente da fila de aprovação.
--
-- aprovar_mudanca operava sobre a VIEW v_parque_export (lat/lon são colunas
-- calculadas, não atualizáveis) e usava casts de enum com nomes errados
-- (::tipo_luminaria e ::tipo_ativo — os enums reais são luminaria_tipo e
-- ativo_tipo). Nunca explodiu porque o frontend envia p_requer_aprovacao:false.
-- Mesma classe de bug do item C2 da auditoria.
--
-- Agora: opera em pontos_luminaria (geom via ST_SetSRID/ST_MakePoint), casts
-- corretos, campos Tier 3 (angulo/material) aplicados, e a APROVAÇÃO CARIMBA
-- A VERIFICAÇÃO usando a campanha ativa no momento em que o campo registrou
-- (fila.criado_em) — verificado_por é o editor original, não o admin.
-- Assinatura inalterada (CREATE OR REPLACE preserva grants).
--
-- APLICADA EM PRODUCAO em 2026-07-12 (versao 20260712215601).

CREATE OR REPLACE FUNCTION public.aprovar_mudanca(p_fila_id uuid, p_aprovado boolean DEFAULT true, p_motivo_rejeicao text DEFAULT NULL::text)
RETURNS jsonb
LANGUAGE plpgsql SECURITY DEFINER SET search_path TO 'public'
AS $function$
DECLARE
  v_user_id uuid;
  v_fila record;
  v_camp uuid;
BEGIN
  v_user_id := auth.uid();

  IF NOT EXISTS (SELECT 1 FROM profiles WHERE id = v_user_id AND role = 'admin') THEN
    RETURN jsonb_build_object('error', 'Apenas admins podem aprovar');
  END IF;

  SELECT * INTO v_fila FROM fila_aprovacao WHERE id = p_fila_id;
  IF v_fila IS NULL THEN
    RETURN jsonb_build_object('error', 'Registro de aprovação não encontrado');
  END IF;

  UPDATE fila_aprovacao SET
    status = CASE WHEN p_aprovado THEN 'aprovado' ELSE 'rejeitado' END,
    aprovado_por = v_user_id,
    aprovado_em = now(),
    motivo_rejeicao = p_motivo_rejeicao
  WHERE id = p_fila_id;

  IF p_aprovado THEN
    -- Campanha ativa quando o campo registrou a mudança (Fase 2.1)
    SELECT id INTO v_camp FROM campanhas
    WHERE criado_em <= v_fila.criado_em
      AND (encerrada_em IS NULL OR encerrada_em > v_fila.criado_em)
    ORDER BY criado_em DESC LIMIT 1;

    IF v_fila.tipo_operacao = 'UPDATE' THEN
      UPDATE pontos_luminaria SET
        tipo_lampada = COALESCE((v_fila.dados_depois->>'tipo_lampada')::tipo_lampada, tipo_lampada),
        potencia_w = COALESCE((v_fila.dados_depois->>'potencia_w')::int, potencia_w),
        status = COALESCE((v_fila.dados_depois->>'status')::status_luminaria, status),
        modernizado_led = COALESCE((v_fila.dados_depois->>'modernizado_led')::boolean, modernizado_led),
        observacoes = COALESCE(v_fila.dados_depois->>'observacoes', observacoes),
        geom = CASE WHEN (v_fila.dados_depois->>'lat') IS NOT NULL AND (v_fila.dados_depois->>'lon') IS NOT NULL
                    THEN ST_SetSRID(ST_MakePoint((v_fila.dados_depois->>'lon')::double precision,
                                                 (v_fila.dados_depois->>'lat')::double precision), 4326)
                    ELSE geom END,
        tipo_luminaria = CASE WHEN (v_fila.dados_depois->>'tipo_luminaria') IS NOT NULL
                              THEN (v_fila.dados_depois->>'tipo_luminaria')::luminaria_tipo
                              ELSE tipo_luminaria END,
        classe_nbr = COALESCE(v_fila.dados_depois->>'classe_nbr', classe_nbr),
        angulo_inclinacao_graus = COALESCE((v_fila.dados_depois->>'angulo_inclinacao_graus')::int, angulo_inclinacao_graus),
        material_piso = COALESCE(v_fila.dados_depois->>'material_piso', material_piso),
        verificado_em  = CASE WHEN v_camp IS NOT NULL THEN v_fila.criado_em ELSE verificado_em END,
        verificado_por = CASE WHEN v_camp IS NOT NULL THEN v_fila.usuario_id ELSE verificado_por END,
        campanha_id    = CASE WHEN v_camp IS NOT NULL THEN v_camp ELSE campanha_id END,
        pendente_aprovacao = false,
        atualizado_em = now()
      WHERE id = v_fila.registro_id;

    ELSIF v_fila.tipo_operacao = 'INSERT' THEN
      INSERT INTO pontos_luminaria (id, geom, tipo_lampada, potencia_w, status, modernizado_led,
        endereco, numero_patrimonio, observacoes, tipo_ativo, tipo_luminaria, classe_nbr,
        fonte, criado_em, criado_por, verificado_em, verificado_por, campanha_id)
      VALUES (
        v_fila.registro_id,
        ST_SetSRID(ST_MakePoint((v_fila.dados_depois->>'lon')::double precision,
                                (v_fila.dados_depois->>'lat')::double precision), 4326),
        (v_fila.dados_depois->>'tipo_lampada')::tipo_lampada,
        (v_fila.dados_depois->>'potencia_w')::int,
        COALESCE(v_fila.dados_depois->>'status','a_verificar')::status_luminaria,
        COALESCE((v_fila.dados_depois->>'modernizado_led')::boolean, false),
        v_fila.dados_depois->>'endereco',
        v_fila.dados_depois->>'numero_patrimonio',
        v_fila.dados_depois->>'observacoes',
        COALESCE(v_fila.dados_depois->>'tipo_ativo','luminaria')::ativo_tipo,
        (v_fila.dados_depois->>'tipo_luminaria')::luminaria_tipo,
        v_fila.dados_depois->>'classe_nbr',
        'levantamento_campo'::fonte_ponto,
        now(), v_fila.usuario_id,
        CASE WHEN v_camp IS NOT NULL THEN v_fila.criado_em ELSE NULL END,
        CASE WHEN v_camp IS NOT NULL THEN v_fila.usuario_id ELSE NULL END,
        v_camp
      );

    ELSIF v_fila.tipo_operacao = 'DELETE' THEN
      DELETE FROM pontos_luminaria WHERE id = v_fila.registro_id;
    END IF;

    RETURN jsonb_build_object('success', true, 'message', 'Mudança aprovada e aplicada');
  ELSE
    RETURN jsonb_build_object('success', true, 'message', 'Mudança rejeitada');
  END IF;
END;
$function$;
