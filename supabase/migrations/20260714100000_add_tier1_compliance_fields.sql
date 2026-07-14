-- Tier 1: Conformidade Regulatória
-- Adiciona campos de registro INMETRO, vida útil, garantia e manutenção preventiva
-- ao catálogo de modelos de equipamentos

ALTER TABLE public.equipamentos_modelo
ADD COLUMN IF NOT EXISTS inmetro_registro TEXT,
ADD COLUMN IF NOT EXISTS vida_util_anos INTEGER CHECK (vida_util_anos > 0 OR vida_util_anos IS NULL),
ADD COLUMN IF NOT EXISTS garantia_anos INTEGER CHECK (garantia_anos > 0 OR garantia_anos IS NULL),
ADD COLUMN IF NOT EXISTS dias_manutencao_preventiva INTEGER CHECK (dias_manutencao_preventiva > 0 OR dias_manutencao_preventiva IS NULL);

-- Índices para queries por conformidade
CREATE INDEX IF NOT EXISTS idx_equip_inmetro ON equipamentos_modelo(inmetro_registro) WHERE inmetro_registro IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_equip_vida_util ON equipamentos_modelo(vida_util_anos) WHERE vida_util_anos IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_equip_garantia ON equipamentos_modelo(garantia_anos) WHERE garantia_anos IS NOT NULL;

-- Comentários para documentação
COMMENT ON COLUMN equipamentos_modelo.inmetro_registro IS 'Número do registro INMETRO (ex: 123456789)';
COMMENT ON COLUMN equipamentos_modelo.vida_util_anos IS 'Anos de vida útil esperada do equipamento';
COMMENT ON COLUMN equipamentos_modelo.garantia_anos IS 'Anos de garantia do fabricante';
COMMENT ON COLUMN equipamentos_modelo.dias_manutencao_preventiva IS 'Intervalo recomendado de manutenção preventiva em dias';

-- Atualizar RPC ip_criar_modelo para incluir novos parâmetros
-- (o RPC será atualizado via função SQL, veja abaixo)

-- Nova função auxiliar: calcular vida útil remanescente
CREATE OR REPLACE FUNCTION calcular_vida_util_remanescente(
  p_data_instalacao DATE,
  p_vida_util_anos INTEGER
)
RETURNS INTEGER AS $$
BEGIN
  IF p_data_instalacao IS NULL OR p_vida_util_anos IS NULL THEN
    RETURN NULL;
  END IF;
  -- Retornar anos restantes (pode ser negativo se vencido)
  RETURN p_vida_util_anos - EXTRACT(YEAR FROM AGE(CURRENT_DATE, p_data_instalacao))::INTEGER;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- View auxiliar: equipamentos fora da vida útil
CREATE OR REPLACE VIEW v_equipamentos_vencidos AS
SELECT
  p.id,
  p.codigo_seconser,
  em.fabricante,
  em.modelo,
  p.data_instalacao,
  em.vida_util_anos,
  calcular_vida_util_remanescente(p.data_instalacao, em.vida_util_anos) AS anos_remanescentes,
  CASE
    WHEN calcular_vida_util_remanescente(p.data_instalacao, em.vida_util_anos) < 0 THEN 'vencido'
    WHEN calcular_vida_util_remanescente(p.data_instalacao, em.vida_util_anos) < 2 THEN 'proximo_vencimento'
    ELSE 'ativo'
  END AS status_vida_util
FROM pontos_luminaria p
JOIN equipamentos_modelo em ON p.modelo_id = em.id
WHERE em.vida_util_anos IS NOT NULL
  AND p.data_instalacao IS NOT NULL
ORDER BY anos_remanescentes ASC;

-- RLS: permissões padrão (leitura pública para equipamentos_modelo)
-- (já existem; sem mudanças necessárias)
