-- Fix: Adicionar health_status à view v_parque_export
-- Problema: View estava faltando coluna health_status que foi adicionada
-- à tabela em migration anterior, causando erro ao consultar a view

CREATE OR REPLACE VIEW public.v_parque_export AS
SELECT
  id,
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
  health_status
FROM pontos_luminaria;
