-- Migration: Create RPC ip_listar_modelos
-- Purpose: List all equipment models with DISTINCT to avoid duplicates
-- Date: 2026-07-16

CREATE OR REPLACE FUNCTION public.ip_listar_modelos()
RETURNS TABLE(
  id uuid,
  fabricante text,
  modelo text,
  potencia_w integer,
  temperatura_cor_k integer,
  tensao text,
  ip text,
  classe_nbr text,
  tecnologia text,
  tipo_luminaria text,
  tipo_lampada text,
  foto_url text,
  descricao text,
  fluxo_luminoso_lm integer,
  eficacia_luminosa_lm_w numeric,
  fator_potencia_fp numeric,
  thd_percentual numeric,
  grau_ik text,
  dps_especificacao text,
  tipo_conectividade text,
  arquivo_ies_url text,
  inmetro_registro text,
  vida_util_anos integer,
  garantia_anos integer,
  dias_manutencao_preventiva integer
)
LANGUAGE sql
STABLE
AS $$
  SELECT DISTINCT ON (em.id)
    em.id,
    em.fabricante,
    em.modelo,
    em.potencia_w,
    em.temperatura_cor_k,
    em.tensao,
    em.ip,
    em.classe_nbr,
    em.tecnologia,
    em.tipo_luminaria,
    em.tipo_lampada,
    em.foto_url,
    em.descricao,
    em.fluxo_luminoso_lm,
    em.eficacia_luminosa_lm_w,
    em.fator_potencia_fp,
    em.thd_percentual,
    em.grau_ik,
    em.dps_especificacao,
    em.tipo_conectividade,
    em.arquivo_ies_url,
    em.inmetro_registro,
    em.vida_util_anos,
    em.garantia_anos,
    em.dias_manutencao_preventiva
  FROM public.equipamentos_modelo em
  ORDER BY em.id, em.updated_at DESC
$$;

-- Grant permissions
GRANT EXECUTE ON FUNCTION public.ip_listar_modelos()
  TO authenticated, service_role, anon;
