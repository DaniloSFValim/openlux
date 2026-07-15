-- Adicionar configurações de painel descritivo ao site_config
-- Permite customizar design e campos exibidos no detail panel

ALTER TABLE public.site_config ADD COLUMN IF NOT EXISTS painel_design TEXT DEFAULT 'tabbed' CHECK (painel_design IN ('minimalist', 'card-grid', 'tabbed', 'status-highlighted', 'compact-dense'));

ALTER TABLE public.site_config ADD COLUMN IF NOT EXISTS painel_campos JSONB DEFAULT '[
  "codigo_seconser",
  "endereco",
  "bairro_nome",
  "tipo_luminaria",
  "potencia_w",
  "led_instalado",
  "status",
  "health_status",
  "data_ultima_intervencao",
  "lat",
  "lon"
]'::jsonb;

-- Tabela de metadados dos campos disponíveis (para o admin UI)
CREATE TABLE IF NOT EXISTS public.painel_campos_disponveis (
  id SERIAL PRIMARY KEY,
  nome TEXT NOT NULL UNIQUE,
  label TEXT NOT NULL,
  tipo TEXT CHECK (tipo IN ('text', 'number', 'date', 'boolean', 'status', 'other')),
  secao TEXT NOT NULL,
  descricao TEXT,
  criado_em TIMESTAMP DEFAULT NOW()
);

-- Inserir campos disponíveis
INSERT INTO public.painel_campos_disponveis (nome, label, tipo, secao, descricao) VALUES
  ('codigo_seconser', 'Código SECONSER', 'text', 'Localização', 'Identificador SECONSER'),
  ('numero_patrimonio', 'Número Patrimônio', 'text', 'Localização', 'ID do patrimônio'),
  ('endereco', 'Endereço', 'text', 'Localização', 'Rua e número'),
  ('bairro_nome', 'Bairro', 'text', 'Localização', 'Bairro da cidade'),
  ('municipio', 'Município', 'text', 'Localização', 'Município'),
  ('cep', 'CEP', 'text', 'Localização', 'Código de endereçamento'),
  ('lat', 'Latitude', 'number', 'Localização', 'Coordenada geográfica'),
  ('lon', 'Longitude', 'number', 'Localização', 'Coordenada geográfica'),

  ('tipo_ativo', 'Tipo de Ativo', 'text', 'Equipamento', 'Luminária, caixa, etc'),
  ('tipo_luminaria', 'Tipo de Luminária', 'text', 'Equipamento', 'Viária, globo, etc'),
  ('tipo_lampada', 'Tipo de Lâmpada', 'text', 'Equipamento', 'LED, vapor sódio, etc'),
  ('potencia_w', 'Potência (W)', 'number', 'Equipamento', 'Potência em watts'),
  ('classe_nbr', 'Classe NBR', 'text', 'Equipamento', 'Classificação NBR'),
  ('grau_ip', 'Grau IP', 'text', 'Equipamento', 'Proteção contra ingresso'),
  ('material_piso', 'Material do Piso', 'text', 'Equipamento', 'Tipo de piso onde está'),
  ('angulo_inclinacao_graus', 'Ângulo Inclinação', 'number', 'Equipamento', 'Graus de inclinação'),

  ('led_instalado', 'LED Instalado', 'boolean', 'Status', 'Se foi modernizado para LED'),
  ('modernizado_led', 'Modernizado LED', 'boolean', 'Status', 'Status de modernização'),
  ('status', 'Status', 'status', 'Status', 'Pendente, ativo, defeito, etc'),
  ('health_status', 'Status de Saúde', 'status', 'Status', 'Verde, amarelo, vermelho'),
  ('verificado_em', 'Verificado em', 'date', 'Status', 'Data última verificação'),
  ('data_ultima_intervencao', 'Última Intervenção', 'date', 'Status', 'Data da última manutenção'),
  ('observacoes', 'Observações', 'text', 'Status', 'Notas adicionais'),

  ('fonte_modernizacao', 'Fonte da Modernização', 'text', 'Análise Técnica', 'Como foi modernizado'),
  ('efficiency_score', 'Score de Eficiência', 'number', 'Análise Técnica', 'Nota de eficiência (0-100)')
ON CONFLICT DO NOTHING;

-- Criar índices
CREATE INDEX IF NOT EXISTS idx_painel_campos_secao ON painel_campos_disponveis(secao);

-- RPC para obter configuração de painel
CREATE OR REPLACE FUNCTION public.ip_obter_painel_config()
RETURNS TABLE (
  design TEXT,
  campos JSONB
) AS $$
BEGIN
  RETURN QUERY
  SELECT site_config.painel_design, site_config.painel_campos
  FROM public.site_config
  WHERE id = 1
  LIMIT 1;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- RPC para atualizar configuração de painel
CREATE OR REPLACE FUNCTION public.ip_atualizar_painel_config(
  p_design TEXT DEFAULT NULL,
  p_campos JSONB DEFAULT NULL
)
RETURNS TABLE (
  success BOOLEAN,
  message TEXT
) AS $$
BEGIN
  UPDATE public.site_config
  SET
    painel_design = COALESCE(p_design, painel_design),
    painel_campos = COALESCE(p_campos, painel_campos),
    atualizado_em = NOW()
  WHERE id = 1;

  RETURN QUERY SELECT TRUE::BOOLEAN, 'Configuração atualizada com sucesso'::TEXT;
EXCEPTION WHEN OTHERS THEN
  RETURN QUERY SELECT FALSE::BOOLEAN, SQLERRM::TEXT;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- RPC para obter lista de campos disponíveis
CREATE OR REPLACE FUNCTION public.ip_listar_campos_disponveis()
RETURNS TABLE (
  nome TEXT,
  label TEXT,
  tipo TEXT,
  secao TEXT,
  descricao TEXT
) AS $$
BEGIN
  RETURN QUERY
  SELECT pcd.nome, pcd.label, pcd.tipo, pcd.secao, pcd.descricao
  FROM public.painel_campos_disponveis pcd
  ORDER BY pcd.secao, pcd.label;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- RLS: permissões para admin
GRANT SELECT ON public.painel_campos_disponveis TO authenticated;
GRANT SELECT ON public.site_config TO authenticated;
GRANT EXECUTE ON FUNCTION public.ip_obter_painel_config TO authenticated;

-- Admin pode atualizar configuração
CREATE POLICY IF NOT EXISTS "admin_update_painel_config" ON public.site_config
  FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM public.profiles
      WHERE id = auth.uid() AND role = 'admin'
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.profiles
      WHERE id = auth.uid() AND role = 'admin'
    )
  );

GRANT UPDATE (painel_design, painel_campos, atualizado_em) ON public.site_config TO authenticated;
GRANT EXECUTE ON FUNCTION public.ip_atualizar_painel_config TO authenticated;
GRANT EXECUTE ON FUNCTION public.ip_listar_campos_disponveis TO authenticated;
