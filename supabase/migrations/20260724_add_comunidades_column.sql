-- Migration: Add comunidade_nome column to pontos_luminaria
-- Purpose: Support filtering and spatial joining with community zones
-- Date: 2026-07-24

-- 1. Add column to pontos_luminaria table
ALTER TABLE public.pontos_luminaria ADD COLUMN IF NOT EXISTS comunidade_nome text;

-- 2. Create index for performance on community filtering
CREATE INDEX IF NOT EXISTS idx_pontos_comunidade ON public.pontos_luminaria(comunidade_nome);

-- 3. Update v_parque_export view to include comunidade_nome
DROP VIEW IF EXISTS public.v_parque_export CASCADE;

CREATE OR REPLACE VIEW public.v_parque_export AS
SELECT
  p.id,
  p.numero_patrimonio,
  p.codigo_seconser,
  p.endereco,
  p.bairro_nome,
  p.bairro_enel,
  p.comunidade_nome,
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

-- Grant permissions
GRANT SELECT ON public.v_parque_export TO anon, authenticated, service_role;
