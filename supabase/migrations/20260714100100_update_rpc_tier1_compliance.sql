-- Migration: Update RPC functions with Tier 1 compliance fields
-- Purpose: Add INMETRO registration, service life, warranty, and maintenance parameters
-- Date: 2026-07-14

-- ============================================================================
-- 1. Update RPC: ip_criar_modelo - add 4 Tier 1 compliance parameters
-- ============================================================================

CREATE OR REPLACE FUNCTION public.ip_criar_modelo(
  p_fabricante text,
  p_modelo text,
  p_potencia_w integer,
  p_temperatura_cor_k integer DEFAULT NULL,
  p_tensao text DEFAULT NULL,
  p_ip text DEFAULT NULL,
  p_classe_nbr text DEFAULT NULL,
  p_tecnologia text DEFAULT 'LED',
  p_tipo_luminaria text DEFAULT NULL,
  p_tipo_lampada text DEFAULT 'led',
  p_foto_url text DEFAULT NULL,
  p_descricao text DEFAULT NULL,
  -- TIER 2 FIELDS (Photometry + Energy)
  p_fluxo_luminoso_lm integer DEFAULT NULL,
  p_eficacia_luminosa_lm_w numeric DEFAULT NULL,
  p_fator_potencia_fp numeric DEFAULT NULL,
  p_thd_percentual numeric DEFAULT NULL,
  p_grau_ik text DEFAULT NULL,
  p_dps_especificacao text DEFAULT NULL,
  p_tipo_conectividade text DEFAULT NULL,
  p_arquivo_ies_url text DEFAULT NULL,
  -- TIER 1 FIELDS (Regulatory Compliance)
  p_inmetro_registro text DEFAULT NULL,
  p_vida_util_anos integer DEFAULT NULL,
  p_garantia_anos integer DEFAULT NULL,
  p_dias_manutencao_preventiva integer DEFAULT NULL
)
RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = 'public'
AS $$
DECLARE
  v_id uuid;
BEGIN
  INSERT INTO public.equipamentos_modelo (
    fabricante,
    modelo,
    potencia_w,
    temperatura_cor_k,
    tensao,
    ip,
    classe_nbr,
    tecnologia,
    tipo_luminaria,
    tipo_lampada,
    foto_url,
    descricao,
    -- TIER 2
    fluxo_luminoso_lm,
    eficacia_luminosa_lm_w,
    fator_potencia_fp,
    thd_percentual,
    grau_ik,
    dps_especificacao,
    tipo_conectividade,
    arquivo_ies_url,
    -- TIER 1
    inmetro_registro,
    vida_util_anos,
    garantia_anos,
    dias_manutencao_preventiva,
    created_by
  )
  VALUES (
    p_fabricante,
    p_modelo,
    p_potencia_w,
    p_temperatura_cor_k,
    p_tensao,
    p_ip,
    p_classe_nbr,
    p_tecnologia,
    p_tipo_luminaria,
    p_tipo_lampada,
    p_foto_url,
    p_descricao,
    -- TIER 2
    p_fluxo_luminoso_lm,
    p_eficacia_luminosa_lm_w,
    p_fator_potencia_fp,
    p_thd_percentual,
    p_grau_ik,
    p_dps_especificacao,
    p_tipo_conectividade,
    p_arquivo_ies_url,
    -- TIER 1
    p_inmetro_registro,
    p_vida_util_anos,
    p_garantia_anos,
    p_dias_manutencao_preventiva,
    auth.uid()
  )
  RETURNING id INTO v_id;

  RETURN v_id;
END;
$$;

-- ============================================================================
-- 2. Update RPC: ip_atualizar_modelo - add 4 Tier 1 compliance parameters
-- ============================================================================

CREATE OR REPLACE FUNCTION public.ip_atualizar_modelo(
  p_id uuid,
  p_fabricante text DEFAULT NULL,
  p_modelo text DEFAULT NULL,
  p_potencia_w integer DEFAULT NULL,
  p_temperatura_cor_k integer DEFAULT NULL,
  p_tensao text DEFAULT NULL,
  p_ip text DEFAULT NULL,
  p_classe_nbr text DEFAULT NULL,
  p_tecnologia text DEFAULT NULL,
  p_tipo_luminaria text DEFAULT NULL,
  p_tipo_lampada text DEFAULT NULL,
  p_foto_url text DEFAULT NULL,
  p_descricao text DEFAULT NULL,
  -- TIER 2 FIELDS (Photometry + Energy)
  p_fluxo_luminoso_lm integer DEFAULT NULL,
  p_eficacia_luminosa_lm_w numeric DEFAULT NULL,
  p_fator_potencia_fp numeric DEFAULT NULL,
  p_thd_percentual numeric DEFAULT NULL,
  p_grau_ik text DEFAULT NULL,
  p_dps_especificacao text DEFAULT NULL,
  p_tipo_conectividade text DEFAULT NULL,
  p_arquivo_ies_url text DEFAULT NULL,
  -- TIER 1 FIELDS (Regulatory Compliance)
  p_inmetro_registro text DEFAULT NULL,
  p_vida_util_anos integer DEFAULT NULL,
  p_garantia_anos integer DEFAULT NULL,
  p_dias_manutencao_preventiva integer DEFAULT NULL
)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = 'public'
AS $$
BEGIN
  UPDATE public.equipamentos_modelo
  SET
    fabricante = COALESCE(p_fabricante, fabricante),
    modelo = COALESCE(p_modelo, modelo),
    potencia_w = COALESCE(p_potencia_w, potencia_w),
    temperatura_cor_k = COALESCE(p_temperatura_cor_k, temperatura_cor_k),
    tensao = COALESCE(p_tensao, tensao),
    ip = COALESCE(p_ip, ip),
    classe_nbr = COALESCE(p_classe_nbr, classe_nbr),
    tecnologia = COALESCE(p_tecnologia, tecnologia),
    tipo_luminaria = COALESCE(p_tipo_luminaria, tipo_luminaria),
    tipo_lampada = COALESCE(p_tipo_lampada, tipo_lampada),
    foto_url = COALESCE(p_foto_url, foto_url),
    descricao = COALESCE(p_descricao, descricao),
    -- TIER 2
    fluxo_luminoso_lm = COALESCE(p_fluxo_luminoso_lm, fluxo_luminoso_lm),
    eficacia_luminosa_lm_w = COALESCE(p_eficacia_luminosa_lm_w, eficacia_luminosa_lm_w),
    fator_potencia_fp = COALESCE(p_fator_potencia_fp, fator_potencia_fp),
    thd_percentual = COALESCE(p_thd_percentual, thd_percentual),
    grau_ik = COALESCE(p_grau_ik, grau_ik),
    dps_especificacao = COALESCE(p_dps_especificacao, dps_especificacao),
    tipo_conectividade = COALESCE(p_tipo_conectividade, tipo_conectividade),
    arquivo_ies_url = COALESCE(p_arquivo_ies_url, arquivo_ies_url),
    -- TIER 1
    inmetro_registro = COALESCE(p_inmetro_registro, inmetro_registro),
    vida_util_anos = COALESCE(p_vida_util_anos, vida_util_anos),
    garantia_anos = COALESCE(p_garantia_anos, garantia_anos),
    dias_manutencao_preventiva = COALESCE(p_dias_manutencao_preventiva, dias_manutencao_preventiva),
    updated_at = now()
  WHERE id = p_id;
END;
$$;

-- ============================================================================
-- 3. Update GRANT permissions: revoke old signatures, grant new ones
-- ============================================================================

-- Revoke old Tier 2 signatures (without Tier 1 params)
REVOKE IF EXISTS EXECUTE ON FUNCTION public.ip_criar_modelo(
  text, text, integer, integer, text, text, text, text, text, text, text, text,
  integer, numeric, numeric, numeric, text, text, text, text
) FROM public, anon;

REVOKE IF EXISTS EXECUTE ON FUNCTION public.ip_atualizar_modelo(
  uuid, text, text, integer, integer, text, text, text, text, text, text, text, text,
  integer, numeric, numeric, numeric, text, text, text, text
) FROM public, anon;

-- Grant new Tier 1 + Tier 2 combined signatures to authenticated and service_role
GRANT EXECUTE ON FUNCTION public.ip_criar_modelo(
  text, text, integer, integer, text, text, text, text, text, text, text, text,
  integer, numeric, numeric, numeric, text, text, text, text,
  text, integer, integer, integer
) TO authenticated, service_role;

GRANT EXECUTE ON FUNCTION public.ip_atualizar_modelo(
  uuid, text, text, integer, integer, text, text, text, text, text, text, text, text,
  integer, numeric, numeric, numeric, text, text, text, text,
  text, integer, integer, integer
) TO authenticated, service_role;
