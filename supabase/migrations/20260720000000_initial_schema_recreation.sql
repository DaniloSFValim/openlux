-- OpenLux Initial Schema Creation (Recovered from exported data)
-- Recreates base schema from exported data + migration references
-- Applied: 2026-07-20 after project migration

-- ============ ENUMS (Tipos) ============
CREATE TYPE IF NOT EXISTS public.ativo_tipo AS ENUM (
  'luminaria', 'caixa_comando', 'chave_magnetica', 'rele_fotoeletrico', 'poste', 'braco', 'outro'
);

CREATE TYPE IF NOT EXISTS public.luminaria_tipo AS ENUM (
  'viaria', 'globo', 'petala', 'projetor', 'balizador', 'orla', 'ornamental', 'piso', 'outro'
);

CREATE TYPE IF NOT EXISTS public.tipo_lampada AS ENUM (
  'led', 'vapor_sodio', 'metalico', 'vapor_mercurio', 'fluorescente', 'sem_lampada', 'desconhecido'
);

CREATE TYPE IF NOT EXISTS public.status_luminaria AS ENUM (
  'led_instalado', 'pendente_troca', 'a_verificar'
);

CREATE TYPE IF NOT EXISTS public.fonte_ponto AS ENUM (
  'censo_enel', 'levantamento_campo', 'importacao', 'sistema'
);

-- ============ TABLES ============

-- Municipios
CREATE TABLE IF NOT EXISTS public.municipios (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  slug text UNIQUE NOT NULL,
  nome text NOT NULL,
  uf text,
  criado_em timestamptz NOT NULL DEFAULT now()
);

INSERT INTO public.municipios (slug, nome, uf)
VALUES ('niteroi', 'Niterói', 'RJ')
ON CONFLICT (slug) DO NOTHING;

-- Campanhas
CREATE TABLE IF NOT EXISTS public.campanhas (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  municipio_id uuid REFERENCES public.municipios(id),
  nome text NOT NULL,
  descricao text,
  status text NOT NULL DEFAULT 'ativa' CHECK (status IN ('ativa','encerrada')),
  criado_por uuid,
  criado_em timestamptz NOT NULL DEFAULT now(),
  encerrada_em timestamptz
);

-- Profiles (users/roles)
CREATE TABLE IF NOT EXISTS public.profiles (
  id uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  role text NOT NULL DEFAULT 'leitura' CHECK (role IN ('leitura', 'editor', 'admin')),
  criado_em timestamptz NOT NULL DEFAULT now()
);

-- Pontos Luminária (MAIN TABLE)
CREATE TABLE IF NOT EXISTS public.pontos_luminaria (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  geom geometry(Point, 4326),

  -- Identificação
  numero_patrimonio text,
  codigo_seconser text,
  endereco text,
  bairro_enel text,
  bairro_nome text,

  -- Tipo de ativo
  tipo_ativo ativo_tipo NOT NULL DEFAULT 'luminaria',
  tipo_luminaria luminaria_tipo,
  tipo_lampada tipo_lampada,
  potencia_w integer,

  -- Status
  status status_luminaria NOT NULL DEFAULT 'a_verificar',
  health_status text DEFAULT 'cinza',
  modernizado_led boolean DEFAULT false,

  -- Recenseamento
  censo_tipo_original text,
  censo_potencia_original integer,
  status_operacional_censo text,
  flag_revisao_censo boolean DEFAULT false,

  -- Modernização
  fonte_modernizacao text,
  data_modernizacao date,

  -- Especificação
  classe_nbr text,
  angulo_inclinacao_graus integer,
  material_piso text,

  -- Auditoria
  fonte fonte_ponto DEFAULT 'sistema',
  observacoes text DEFAULT '',
  criado_em timestamptz NOT NULL DEFAULT now(),
  criado_por uuid,
  atualizado_em timestamptz NOT NULL DEFAULT now(),

  -- Campanhas/Verificação
  campanha_id uuid REFERENCES public.campanhas(id),
  verificado_em timestamptz,
  verificado_por uuid,

  -- Municipio
  municipio_id uuid REFERENCES public.municipios(id),

  CONSTRAINT check_tipo_ativo CHECK (
    (tipo_ativo = 'luminaria' AND tipo_lampada IS NOT NULL AND potencia_w IS NOT NULL) OR
    (tipo_ativo != 'luminaria')
  )
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_pontos_geom ON public.pontos_luminaria USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_pontos_codigo ON public.pontos_luminaria(codigo_seconser);
CREATE INDEX IF NOT EXISTS idx_pontos_patrimonial ON public.pontos_luminaria(numero_patrimonio);
CREATE INDEX IF NOT EXISTS idx_pontos_bairro ON public.pontos_luminaria(bairro_nome);
CREATE INDEX IF NOT EXISTS idx_pontos_campanha ON public.pontos_luminaria(campanha_id);
CREATE INDEX IF NOT EXISTS idx_pontos_municipio ON public.pontos_luminaria(municipio_id);
CREATE INDEX IF NOT EXISTS idx_pontos_tipo_ativo ON public.pontos_luminaria(tipo_ativo);
CREATE INDEX IF NOT EXISTS idx_pontos_health ON public.pontos_luminaria(health_status);

-- ============ VIEWS ============

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

-- ============ RLS POLICIES ============

ALTER TABLE public.pontos_luminaria ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.municipios ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.campanhas ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS pontos_select ON public.pontos_luminaria;
DROP POLICY IF EXISTS pontos_update ON public.pontos_luminaria;
DROP POLICY IF EXISTS pontos_insert ON public.pontos_luminaria;
DROP POLICY IF EXISTS pontos_delete ON public.pontos_luminaria;

CREATE POLICY pontos_select ON public.pontos_luminaria FOR SELECT USING (true);
CREATE POLICY pontos_update ON public.pontos_luminaria FOR UPDATE
  USING (auth.jwt()->>'role' IN ('editor','admin'));
CREATE POLICY pontos_insert ON public.pontos_luminaria FOR INSERT
  WITH CHECK (auth.jwt()->>'role' IN ('editor','admin'));
CREATE POLICY pontos_delete ON public.pontos_luminaria FOR DELETE
  USING (auth.jwt()->>'role' = 'admin');

DROP POLICY IF EXISTS profiles_select ON public.profiles;
DROP POLICY IF EXISTS municipios_select ON public.municipios;
DROP POLICY IF EXISTS campanhas_select ON public.campanhas;

CREATE POLICY profiles_select ON public.profiles FOR SELECT USING (true);
CREATE POLICY municipios_select ON public.municipios FOR SELECT USING (true);
CREATE POLICY campanhas_select ON public.campanhas FOR SELECT USING (true);

GRANT SELECT ON public.pontos_luminaria TO anon, authenticated, service_role;
GRANT UPDATE ON public.pontos_luminaria TO authenticated, service_role;
GRANT INSERT ON public.pontos_luminaria TO authenticated, service_role;
GRANT DELETE ON public.pontos_luminaria TO authenticated, service_role;

GRANT SELECT ON public.profiles TO anon, authenticated, service_role;
GRANT SELECT ON public.municipios TO anon, authenticated, service_role;
GRANT SELECT ON public.campanhas TO anon, authenticated, service_role;

GRANT SELECT ON public.v_parque_export TO anon, authenticated, service_role;
