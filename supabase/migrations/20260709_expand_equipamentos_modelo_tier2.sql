-- Migration: Expand equipamentos_modelo with Tier 2 fields (Photometry + Compliance + Energy)
-- Purpose: Add engineering parameters for efficient audit, regulatory compliance, and light pollution measurement
-- Tier 2 Fields: Luminous Flux, Efficacy, Power Factor, THD, IK Rating, Surge Protection, Connectivity, Photometric File
-- Date: 2026-07-09

-- ============================================================================
-- 1. Add 9 new columns to equipamentos_modelo table
-- ============================================================================

ALTER TABLE public.equipamentos_modelo
ADD COLUMN IF NOT EXISTS fluxo_luminoso_lm INTEGER
  CHECK (fluxo_luminoso_lm IS NULL OR fluxo_luminoso_lm > 0),
  COMMENT 'Luminous flux in lumens (lm) - indicates total light output regardless of wattage';

ALTER TABLE public.equipamentos_modelo
ADD COLUMN IF NOT EXISTS eficacia_luminosa_lm_w NUMERIC(5, 2)
  CHECK (eficacia_luminosa_lm_w IS NULL OR eficacia_luminosa_lm_w > 0),
  COMMENT 'Luminous efficacy in lm/W - efficiency ratio (lumens per watt)';

ALTER TABLE public.equipamentos_modelo
ADD COLUMN IF NOT EXISTS fator_potencia_fp NUMERIC(3, 2)
  CHECK (fator_potencia_fp IS NULL OR (fator_potencia_fp >= 0.90 AND fator_potencia_fp <= 1.0)),
  COMMENT 'Power factor (0.90-1.0) - reactive energy billing compliance per concessionária';

ALTER TABLE public.equipamentos_modelo
ADD COLUMN IF NOT EXISTS thd_percentual NUMERIC(5, 2)
  CHECK (thd_percentual IS NULL OR (thd_percentual >= 0 AND thd_percentual <= 100)),
  COMMENT 'Total Harmonic Distortion in percent (0-100%) - grid quality requirement, typically <10% or <20%';

ALTER TABLE public.equipamentos_modelo
ADD COLUMN IF NOT EXISTS grau_ik TEXT
  CHECK (grau_ik IS NULL OR grau_ik IN ('IK08', 'IK09', 'IK10')),
  COMMENT 'Mechanical resistance rating (IK08=2J, IK09=5J, IK10=20J) - vandalism/impact resistance';

ALTER TABLE public.equipamentos_modelo
ADD COLUMN IF NOT EXISTS dps_especificacao TEXT,
  COMMENT 'Surge protection specification (e.g., "10kV/10kA") - lightning/surge protection';

ALTER TABLE public.equipamentos_modelo
ADD COLUMN IF NOT EXISTS tipo_conectividade TEXT
  CHECK (tipo_conectividade IS NULL OR tipo_conectividade IN ('sem_tomada', 'ansi_3pin', 'ansi_7pin', 'zhaga')),
  COMMENT 'Socket type for photoelectric cell or telemanagement - sem_tomata, ANSI 3-pin, ANSI 7-pin (NEMA), Zhaga standard';

ALTER TABLE public.equipamentos_modelo
ADD COLUMN IF NOT EXISTS arquivo_ies_url TEXT,
  COMMENT 'URL to photometric file (.IES format) - enables Dialux import for lighting design';

-- ============================================================================
-- 2. Create indexes for query performance (Tier 2 fields)
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_equip_fluxo_lm
  ON public.equipamentos_modelo(fluxo_luminoso_lm);

CREATE INDEX IF NOT EXISTS idx_equip_eficacia_lm_w
  ON public.equipamentos_modelo(eficacia_luminosa_lm_w);

CREATE INDEX IF NOT EXISTS idx_equip_fator_potencia
  ON public.equipamentos_modelo(fator_potencia_fp);

CREATE INDEX IF NOT EXISTS idx_equip_grau_ik
  ON public.equipamentos_modelo(grau_ik);

CREATE INDEX IF NOT EXISTS idx_equip_tipo_conectividade
  ON public.equipamentos_modelo(tipo_conectividade);

-- ============================================================================
-- 3. Update RPC: ip_criar_modelo - add 9 new parameters
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
  -- TIER 2 FIELDS
  p_fluxo_luminoso_lm integer DEFAULT NULL,
  p_eficacia_luminosa_lm_w numeric DEFAULT NULL,
  p_fator_potencia_fp numeric DEFAULT NULL,
  p_thd_percentual numeric DEFAULT NULL,
  p_grau_ik text DEFAULT NULL,
  p_dps_especificacao text DEFAULT NULL,
  p_tipo_conectividade text DEFAULT NULL,
  p_arquivo_ies_url text DEFAULT NULL
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
    auth.uid()
  )
  RETURNING id INTO v_id;

  RETURN v_id;
END;
$$;

-- ============================================================================
-- 4. Update RPC: ip_atualizar_modelo - add 9 new parameters
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
  -- TIER 2 FIELDS
  p_fluxo_luminoso_lm integer DEFAULT NULL,
  p_eficacia_luminosa_lm_w numeric DEFAULT NULL,
  p_fator_potencia_fp numeric DEFAULT NULL,
  p_thd_percentual numeric DEFAULT NULL,
  p_grau_ik text DEFAULT NULL,
  p_dps_especificacao text DEFAULT NULL,
  p_tipo_conectividade text DEFAULT NULL,
  p_arquivo_ies_url text DEFAULT NULL
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
    updated_at = now()
  WHERE id = p_id;
END;
$$;

-- ============================================================================
-- 5. Update GRANT permissions for new RPC signatures
-- ============================================================================

GRANT EXECUTE ON FUNCTION public.ip_criar_modelo(
  text, text, integer, integer, text, text, text, text, text, text, text, text,
  integer, numeric, numeric, numeric, text, text, text, text
) TO authenticated;

GRANT EXECUTE ON FUNCTION public.ip_atualizar_modelo(
  uuid, text, text, integer, integer, text, text, text, text, text, text, text, text,
  integer, numeric, numeric, numeric, text, text, text, text
) TO authenticated;
