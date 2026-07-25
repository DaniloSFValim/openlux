-- Recria v_parque_export, perdida em 2026-07-25.
--
-- Causa: na limpeza do filtro de comunidades foi executado
--   ALTER TABLE public.pontos_luminaria DROP COLUMN IF EXISTS comunidade_nome CASCADE;
-- A migration de comunidades (revertida no PR #74) havia adicionado essa coluna a esta
-- view. O CASCADE removeu a coluna e todo objeto dependente dela — inclusive a view.
-- Nenhum dado foi perdido: pontos_luminaria seguiu com 42.764 linhas e
-- pontos_luminaria_historico com 171.117. Apenas o objeto de apresentacao caiu.
--
-- Sintoma: a tabela "Registro de luminarias" mostrava "Falha ao carregar" e o toast
-- "Could not find the table 'public.v_parque_export' in the schema cache". Junto com a
-- tabela pararam a busca da sidebar, todas as exportacoes (fetchFiltrado), a contagem da
-- fila de auditoria, o handler de /api/v1/bairros e as RPCs ip_atualizar_ponto e
-- ip_remover_ponto, que leem a view para gravar o "antes" no historico.
--
-- Definicao identica a de 20260720000000_initial_schema_recreation.sql (linhas 131-167),
-- sem comunidade_nome — o estado correto apos o revert do filtro de comunidades.
--
-- Ao aplicar fora de uma migration, e necessario tambem NOTIFY pgrst, 'reload schema':
-- o PostgREST mantem cache de schema e continua respondendo "not found" ate recarregar.
--
-- Licao: DROP ... CASCADE apenas depois de listar o que sera derrubado. Para colunas de
-- pontos_luminaria, as views dependentes aparecem em:
--   SELECT dv.relname
--   FROM pg_depend d
--   JOIN pg_rewrite r ON r.oid = d.objid
--   JOIN pg_class dv ON dv.oid = r.ev_class
--   WHERE d.refobjid = 'public.pontos_luminaria'::regclass AND dv.relkind = 'v';

CREATE OR REPLACE VIEW public.v_parque_export AS
SELECT
  p.id,
  p.numero_patrimonio,
  p.codigo_seconser,
  p.endereco,
  p.bairro_nome,
  p.bairro_enel,
  p.tipo_ativo,
  p.tipo_luminaria,
  p.tipo_lampada,
  p.potencia_w,
  p.status,
  p.health_status,
  p.modernizado_led,
  p.classe_nbr,
  p.fonte,
  p.fonte_modernizacao,
  p.data_modernizacao,
  p.censo_tipo_original,
  p.censo_potencia_original,
  p.status_operacional_censo,
  p.flag_revisao_censo,
  p.observacoes,
  ST_Y(p.geom) as lat,
  ST_X(p.geom) as lon,
  p.criado_em,
  p.atualizado_em,
  p.criado_por,
  p.angulo_inclinacao_graus,
  p.material_piso,
  p.campanha_id,
  p.verificado_em,
  p.verificado_por,
  p.municipio_id
FROM public.pontos_luminaria p
ORDER BY p.criado_em DESC;

GRANT SELECT ON public.v_parque_export TO anon, authenticated, service_role;
