-- ============================================================================
-- OpenLux — baseline do schema (snapshot da producao)
-- ============================================================================
--
-- Gerado em 2026-07-28 a partir do banco de producao (projeto lrnmydrwzxxajylsmoih),
-- por introspeccao do catalogo do PostgreSQL.
--
-- POR QUE ESTE ARQUIVO EXISTE
--
-- O historico em supabase/migrations/ nao reconstroi o banco: sao 43 versoes
-- registradas na producao contra 21 arquivos versionados, e varias das primeiras
-- foram aplicadas pelo dashboard antes de o diretorio ser organizado. O README de
-- supabase/migrations/ ja mandava usar `supabase db pull` para reconstruir — este
-- arquivo e o resultado desse pull, versionado, para que o repositorio deixe de
-- depender de acesso a producao.
--
-- COMO USAR
--
--   psql "$DATABASE_URL" -f supabase/schema.sql
--
-- Destina-se a um banco VAZIO (Supabase recem-criado). Nao e idempotente em tudo:
-- CREATE TYPE e CREATE POLICY nao aceitam IF NOT EXISTS no PostgreSQL, entao
-- rodar duas vezes acusa erro nos tipos. As policies ja vem com DROP ... IF EXISTS
-- antes do CREATE.
--
-- ESTE ARQUIVO NAO E UMA MIGRATION
--
-- Ele fica fora de supabase/migrations/ de proposito, para que `supabase db push`
-- nunca tente aplica-lo sobre a producao. Mudancas de schema continuam sendo
-- feitas por migration, conforme o fluxo do README daquele diretorio; este
-- snapshot deve ser regenerado depois delas.
--
-- O QUE ESTA AQUI
--
--   6 extensoes                 12 tipos enumerados      10 sequences
--   18 tabelas                  18 chaves primarias       4 constraints UNIQUE
--   21 constraints CHECK        15 chaves estrangeiras   40 indices
--   4 views                     46 funcoes/RPCs           7 triggers
--   18 tabelas com RLS          35 policies              72 grants de tabela
--   125 grants de funcao         4 buckets de storage     11 policies de storage
--
-- O QUE NAO ESTA AQUI
--
--   - Dados. E so estrutura; nenhum INSERT alem dos buckets de storage.
--   - Objetos das extensoes (PostGIS traz ~744 funcoes e a spatial_ref_sys):
--     vem junto com CREATE EXTENSION.
--   - Schemas gerenciados pelo Supabase (auth, storage.objects, vault). A tabela
--     public.profiles referencia auth.users, que a plataforma cria sozinha.
--
-- ============================================================================
-- ============================================================================
-- 1. EXTENSOES
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS extensions;

CREATE EXTENSION IF NOT EXISTS "pg_stat_statements" WITH SCHEMA extensions;
CREATE EXTENSION IF NOT EXISTS "pgcrypto"           WITH SCHEMA extensions;
CREATE EXTENSION IF NOT EXISTS "postgis"            WITH SCHEMA public;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp"          WITH SCHEMA extensions;

-- pg_cron e supabase_vault sao fornecidos pela plataforma Supabase e nao existem
-- num PostgreSQL comum. Nenhum objeto deste schema depende deles, entao a falta
-- so gera um aviso — o arquivo continua valido fora da Supabase.
DO $$
BEGIN
  CREATE EXTENSION IF NOT EXISTS "pg_cron" WITH SCHEMA pg_catalog;
EXCEPTION WHEN OTHERS THEN
  RAISE NOTICE 'pg_cron indisponivel neste servidor — ignorado';
END $$;

DO $$
BEGIN
  CREATE EXTENSION IF NOT EXISTS "supabase_vault" WITH SCHEMA vault;
EXCEPTION WHEN OTHERS THEN
  RAISE NOTICE 'supabase_vault indisponivel neste servidor — ignorado';
END $$;

-- OBRIGATORIO: os DEFAULTs de 4 tabelas chamam uuid_generate_v4() sem qualificar,
-- e a funcao vive no schema `extensions`. Na Supabase o search_path do role ja
-- inclui esse schema; num banco novo, nao — e sem esta linha as tabelas
-- bairros_niteroi, lotes_substituicao, pontos_luminaria e registros_iluminacao
-- falham na criacao, derrubando todo o resto em cascata.
SET search_path TO public, extensions;

-- ============================================================================
-- 2. TIPOS ENUMERADOS
-- ============================================================================

CREATE TYPE public.ativo_tipo       AS ENUM ('luminaria', 'caixa_comando', 'chave_magnetica', 'rele_fotoeletrico', 'poste', 'braco', 'outro');
CREATE TYPE public.categoria_origem AS ENUM ('iluminacao_led_2024', 'led_implantado_2025', 'comunidades', 'iluminacao_esportiva', 'nao_classificado');
CREATE TYPE public.fonte_ponto      AS ENUM ('levantamento_campo', 'ponto_original_kml', 'estimado', 'censo_enel');
CREATE TYPE public.intervencao_tipo AS ENUM ('instalacao', 'substituicao', 'manutencao', 'vistoria', 'remocao');
CREATE TYPE public.luminaria_tipo   AS ENUM ('viaria', 'globo', 'petala', 'projetor', 'balizador', 'orla', 'ornamental', 'piso', 'outro');
CREATE TYPE public.nivel_confianca  AS ENUM ('alta', 'media', 'baixa', 'nao_parseado');
CREATE TYPE public.status_luminaria AS ENUM ('led_instalado', 'pendente_troca', 'a_verificar');
CREATE TYPE public.status_revisao   AS ENUM ('pendente', 'confirmado', 'corrigido', 'descartado');
CREATE TYPE public.tipo_equipamento AS ENUM ('luminaria', 'projetor');
CREATE TYPE public.tipo_geometria   AS ENUM ('segmento_via', 'ponto_real', 'area');
CREATE TYPE public.tipo_lampada     AS ENUM ('vapor_sodio', 'vapor_mercurio', 'metalico', 'desconhecido', 'led', 'fluorescente', 'sem_lampada');
CREATE TYPE public.user_role        AS ENUM ('admin', 'editor', 'leitura');



-- ============================================================================
-- 3. SEQUENCES
-- ============================================================================

CREATE SEQUENCE IF NOT EXISTS public.painel_campos_disponveis_id_seq;
CREATE SEQUENCE IF NOT EXISTS public.pontos_intervencoes_id_seq;
CREATE SEQUENCE IF NOT EXISTS public.pontos_luminaria_historico_id_seq;
CREATE SEQUENCE IF NOT EXISTS public.seq_ipnit_brc;
CREATE SEQUENCE IF NOT EXISTS public.seq_ipnit_chv;
CREATE SEQUENCE IF NOT EXISTS public.seq_ipnit_cmd;
CREATE SEQUENCE IF NOT EXISTS public.seq_ipnit_lum;
CREATE SEQUENCE IF NOT EXISTS public.seq_ipnit_out;
CREATE SEQUENCE IF NOT EXISTS public.seq_ipnit_pst;
CREATE SEQUENCE IF NOT EXISTS public.seq_ipnit_rfp;


-- ============================================================================
-- 4. TABELAS
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.ativos_removidos (
  id uuid DEFAULT gen_random_uuid() NOT NULL,
  ponto_id uuid NOT NULL,
  dados_backup jsonb NOT NULL,
  removido_por uuid NOT NULL,
  motivo text,
  removido_em timestamp without time zone DEFAULT now(),
  restaurado_por uuid,
  restaurado_em timestamp without time zone,
  status text DEFAULT 'removido'::text
);

CREATE TABLE IF NOT EXISTS public.bairros_niteroi (
  id uuid DEFAULT uuid_generate_v4() NOT NULL,
  nome_bairro text NOT NULL,
  geom geometry(Geometry,4326),
  fonte text DEFAULT 'SIGeo/PMN - Lei Urbanística 3905/2024'::text NOT NULL,
  criado_em timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS public.campanhas (
  id uuid DEFAULT gen_random_uuid() NOT NULL,
  municipio_id uuid DEFAULT '615d06f5-feca-48b3-ab71-72ca12b65e72'::uuid,
  nome text NOT NULL,
  descricao text,
  status text DEFAULT 'ativa'::text NOT NULL,
  criado_por uuid,
  criado_em timestamp with time zone DEFAULT now() NOT NULL,
  encerrada_em timestamp with time zone
);

CREATE TABLE IF NOT EXISTS public.comunidades_zeis (
  id uuid DEFAULT gen_random_uuid() NOT NULL,
  nome text NOT NULL,
  bairro text,
  sigla_regiao text,
  geom geometry(MultiPolygon,4326) NOT NULL,
  criado_em timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS public.equipamentos_modelo (
  id uuid DEFAULT gen_random_uuid() NOT NULL,
  fabricante text NOT NULL,
  modelo text NOT NULL,
  potencia_w integer NOT NULL,
  temperatura_cor_k integer,
  tensao text,
  ip text,
  classe_nbr text,
  tecnologia text DEFAULT 'LED'::text NOT NULL,
  tipo_luminaria text,
  tipo_lampada text DEFAULT 'led'::text,
  foto_url text,
  descricao text,
  ativo boolean DEFAULT true,
  created_at timestamp without time zone DEFAULT now(),
  updated_at timestamp without time zone DEFAULT now(),
  created_by uuid,
  fluxo_luminoso_lm integer,
  eficacia_luminosa_lm_w numeric(5,2),
  fator_potencia_fp numeric(3,2),
  thd_percentual numeric(5,2),
  grau_ik text,
  dps_especificacao text,
  tipo_conectividade text,
  arquivo_ies_url text,
  inmetro_registro text,
  vida_util_anos integer,
  garantia_anos integer,
  dias_manutencao_preventiva integer
);

CREATE TABLE IF NOT EXISTS public.ip_eficacia_luminosa (
  tipo text NOT NULL,
  lm_w numeric NOT NULL,
  observacao text,
  atualizado_em timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS public.lotes_substituicao (
  id uuid DEFAULT uuid_generate_v4() NOT NULL,
  registro_id uuid NOT NULL,
  texto_origem text NOT NULL,
  quantidade integer,
  equipamento tipo_equipamento DEFAULT 'luminaria'::tipo_equipamento NOT NULL,
  tipo_lampada_antiga tipo_lampada,
  potencia_antiga_w integer,
  potencia_led_nova_w integer,
  confianca nivel_confianca DEFAULT 'alta'::nivel_confianca NOT NULL,
  motivo_revisao text[] DEFAULT '{}'::text[],
  criado_em timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS public.metricas_diarias (
  data date NOT NULL,
  total integer,
  led integer,
  led_censo integer,
  led_seconser integer,
  pendente integer,
  pct_led numeric,
  potencia_kw_led numeric,
  por_bairro jsonb,
  criado_em timestamp with time zone DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.municipios (
  id uuid DEFAULT gen_random_uuid() NOT NULL,
  slug text NOT NULL,
  nome text NOT NULL,
  uf text,
  criado_em timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS public.painel_campos_disponveis (
  id integer DEFAULT nextval('painel_campos_disponveis_id_seq'::regclass) NOT NULL,
  nome text NOT NULL,
  label text NOT NULL,
  tipo text,
  secao text NOT NULL,
  descricao text,
  criado_em timestamp without time zone DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.pontos_intervencoes (
  id bigint DEFAULT nextval('pontos_intervencoes_id_seq'::regclass) NOT NULL,
  ponto_id uuid NOT NULL,
  tipo intervencao_tipo NOT NULL,
  data date DEFAULT CURRENT_DATE NOT NULL,
  descricao text,
  responsavel text,
  tipo_lampada_nova tipo_lampada,
  potencia_nova_w integer,
  registrado_por text,
  criado_em timestamp with time zone DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.pontos_luminaria (
  id uuid DEFAULT uuid_generate_v4() NOT NULL,
  registro_pai_id uuid,
  geom geometry(Point,4326) NOT NULL,
  tipo_lampada tipo_lampada,
  potencia_w integer,
  status status_luminaria DEFAULT 'a_verificar'::status_luminaria NOT NULL,
  fonte fonte_ponto NOT NULL,
  data_instalacao date,
  observacoes text,
  criado_por text,
  criado_em timestamp with time zone DEFAULT now() NOT NULL,
  atualizado_em timestamp with time zone DEFAULT now() NOT NULL,
  endereco text,
  numero_patrimonio text,
  bairro_id uuid,
  bairro_nome text,
  modernizado_led boolean DEFAULT false NOT NULL,
  fonte_modernizacao text,
  data_modernizacao date,
  censo_tipo_original tipo_lampada,
  censo_potencia_original integer,
  bairro_enel text,
  status_operacional_censo text,
  flag_revisao_censo boolean DEFAULT false NOT NULL,
  codigo_seconser text,
  tipo_ativo ativo_tipo DEFAULT 'luminaria'::ativo_tipo NOT NULL,
  tipo_luminaria luminaria_tipo,
  classe_nbr text,
  motivo_remocao text,
  health_status text DEFAULT 'cinza'::text,
  angulo_inclinacao_graus smallint,
  material_piso text,
  municipio_id uuid DEFAULT '615d06f5-feca-48b3-ab71-72ca12b65e72'::uuid,
  verificado_em timestamp with time zone,
  verificado_por uuid,
  campanha_id uuid
);

CREATE TABLE IF NOT EXISTS public.pontos_luminaria_historico (
  id bigint DEFAULT nextval('pontos_luminaria_historico_id_seq'::regclass) NOT NULL,
  ponto_id uuid NOT NULL,
  operacao text NOT NULL,
  alterado_por text,
  alterado_em timestamp with time zone DEFAULT now() NOT NULL,
  dados_antes jsonb,
  dados_depois jsonb
);

CREATE TABLE IF NOT EXISTS public.profiles (
  id uuid NOT NULL,
  email text,
  role user_role DEFAULT 'leitura'::user_role NOT NULL,
  criado_em timestamp with time zone DEFAULT now(),
  atualizado_em timestamp with time zone DEFAULT now(),
  created_at timestamp with time zone DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.ref_material_piso (
  material text NOT NULL,
  rotulo text NOT NULL,
  refletancia numeric(3,2) NOT NULL,
  fonte text
);

CREATE TABLE IF NOT EXISTS public.registros_iluminacao (
  id uuid DEFAULT uuid_generate_v4() NOT NULL,
  kml_id_original text NOT NULL,
  nome_original text,
  categoria categoria_origem DEFAULT 'nao_classificado'::categoria_origem NOT NULL,
  tipo_registro tipo_geometria NOT NULL,
  geom geometry(Geometry,4326) NOT NULL,
  descricao_bruta text,
  observacoes_livres text[] DEFAULT '{}'::text[],
  infraestrutura_fisica jsonb DEFAULT '{}'::jsonb,
  cor_linha_original_hex text,
  flag_revisao boolean DEFAULT false NOT NULL,
  status_revisao status_revisao DEFAULT 'pendente'::status_revisao NOT NULL,
  revisado_por text,
  revisado_em timestamp with time zone,
  criado_em timestamp with time zone DEFAULT now() NOT NULL,
  atualizado_em timestamp with time zone DEFAULT now() NOT NULL,
  bairro_id uuid,
  bairro_nome text,
  ano_referencia integer
);

CREATE TABLE IF NOT EXISTS public.site_config (
  id smallint DEFAULT 1 NOT NULL,
  dados jsonb DEFAULT '{}'::jsonb NOT NULL,
  atualizado_em timestamp with time zone DEFAULT now(),
  painel_design text DEFAULT 'tabbed'::text,
  painel_campos jsonb DEFAULT '["codigo_seconser", "endereco", "bairro_nome", "tipo_luminaria", "potencia_w", "led_instalado", "status", "health_status", "data_ultima_intervencao", "lat", "lon"]'::jsonb
);


-- ============================================================================
-- 5. SEQUENCES OWNED BY
-- ============================================================================

ALTER SEQUENCE public.painel_campos_disponveis_id_seq OWNED BY public.painel_campos_disponveis.id;
ALTER SEQUENCE public.pontos_intervencoes_id_seq OWNED BY public.pontos_intervencoes.id;
ALTER SEQUENCE public.pontos_luminaria_historico_id_seq OWNED BY public.pontos_luminaria_historico.id;


-- ============================================================================
-- 6. CHAVES PRIMARIAS
-- ============================================================================

ALTER TABLE public.ativos_removidos ADD CONSTRAINT ativos_removidos_pkey PRIMARY KEY (id);
ALTER TABLE public.bairros_niteroi ADD CONSTRAINT bairros_niteroi_pkey PRIMARY KEY (id);
ALTER TABLE public.campanhas ADD CONSTRAINT campanhas_pkey PRIMARY KEY (id);
ALTER TABLE public.comunidades_zeis ADD CONSTRAINT comunidades_zeis_pkey PRIMARY KEY (id);
ALTER TABLE public.equipamentos_modelo ADD CONSTRAINT equipamentos_modelo_pkey PRIMARY KEY (id);
ALTER TABLE public.ip_eficacia_luminosa ADD CONSTRAINT ip_eficacia_luminosa_pkey PRIMARY KEY (tipo);
ALTER TABLE public.lotes_substituicao ADD CONSTRAINT lotes_substituicao_pkey PRIMARY KEY (id);
ALTER TABLE public.metricas_diarias ADD CONSTRAINT metricas_diarias_pkey PRIMARY KEY (data);
ALTER TABLE public.municipios ADD CONSTRAINT municipios_pkey PRIMARY KEY (id);
ALTER TABLE public.painel_campos_disponveis ADD CONSTRAINT painel_campos_disponveis_pkey PRIMARY KEY (id);
ALTER TABLE public.pontos_intervencoes ADD CONSTRAINT pontos_intervencoes_pkey PRIMARY KEY (id);
ALTER TABLE public.pontos_luminaria ADD CONSTRAINT pontos_luminaria_pkey PRIMARY KEY (id);
ALTER TABLE public.pontos_luminaria_historico ADD CONSTRAINT pontos_luminaria_historico_pkey PRIMARY KEY (id);
ALTER TABLE public.profiles ADD CONSTRAINT profiles_pkey PRIMARY KEY (id);
ALTER TABLE public.ref_material_piso ADD CONSTRAINT ref_material_piso_pkey PRIMARY KEY (material);
ALTER TABLE public.registros_iluminacao ADD CONSTRAINT registros_iluminacao_pkey PRIMARY KEY (id);
ALTER TABLE public.site_config ADD CONSTRAINT site_config_pkey PRIMARY KEY (id);


-- ============================================================================
-- 7. CONSTRAINTS UNIQUE
-- ============================================================================

ALTER TABLE public.equipamentos_modelo ADD CONSTRAINT unique_modelo UNIQUE (fabricante, modelo);
ALTER TABLE public.municipios ADD CONSTRAINT municipios_slug_key UNIQUE (slug);
ALTER TABLE public.painel_campos_disponveis ADD CONSTRAINT painel_campos_disponveis_nome_key UNIQUE (nome);
ALTER TABLE public.registros_iluminacao ADD CONSTRAINT registros_iluminacao_kml_id_original_key UNIQUE (kml_id_original);


-- ============================================================================
-- 8. CONSTRAINTS CHECK
-- ============================================================================

ALTER TABLE public.ativos_removidos ADD CONSTRAINT valid_removal_status CHECK ((status = ANY (ARRAY['removido'::text, 'restaurado'::text])));
ALTER TABLE public.campanhas ADD CONSTRAINT campanhas_status_check CHECK ((status = ANY (ARRAY['ativa'::text, 'encerrada'::text])));
ALTER TABLE public.equipamentos_modelo ADD CONSTRAINT equipamentos_modelo_dias_manutencao_preventiva_check CHECK (((dias_manutencao_preventiva > 0) OR (dias_manutencao_preventiva IS NULL)));
ALTER TABLE public.equipamentos_modelo ADD CONSTRAINT equipamentos_modelo_eficacia_luminosa_lm_w_check CHECK (((eficacia_luminosa_lm_w IS NULL) OR (eficacia_luminosa_lm_w > (0)::numeric)));
ALTER TABLE public.equipamentos_modelo ADD CONSTRAINT equipamentos_modelo_fator_potencia_fp_check CHECK (((fator_potencia_fp IS NULL) OR ((fator_potencia_fp >= 0.90) AND (fator_potencia_fp <= 1.0))));
ALTER TABLE public.equipamentos_modelo ADD CONSTRAINT equipamentos_modelo_fluxo_luminoso_lm_check CHECK (((fluxo_luminoso_lm IS NULL) OR (fluxo_luminoso_lm > 0)));
ALTER TABLE public.equipamentos_modelo ADD CONSTRAINT equipamentos_modelo_garantia_anos_check CHECK (((garantia_anos > 0) OR (garantia_anos IS NULL)));
ALTER TABLE public.equipamentos_modelo ADD CONSTRAINT equipamentos_modelo_grau_ik_check CHECK (((grau_ik IS NULL) OR (grau_ik = ANY (ARRAY['IK08'::text, 'IK09'::text, 'IK10'::text]))));
ALTER TABLE public.equipamentos_modelo ADD CONSTRAINT equipamentos_modelo_potencia_w_check CHECK (((potencia_w > 0) AND (potencia_w <= 2000)));
ALTER TABLE public.equipamentos_modelo ADD CONSTRAINT equipamentos_modelo_thd_percentual_check CHECK (((thd_percentual IS NULL) OR ((thd_percentual >= (0)::numeric) AND (thd_percentual <= (100)::numeric))));
ALTER TABLE public.equipamentos_modelo ADD CONSTRAINT equipamentos_modelo_tipo_conectividade_check CHECK (((tipo_conectividade IS NULL) OR (tipo_conectividade = ANY (ARRAY['sem_tomada'::text, 'ansi_3pin'::text, 'ansi_7pin'::text, 'zhaga'::text]))));
ALTER TABLE public.equipamentos_modelo ADD CONSTRAINT equipamentos_modelo_vida_util_anos_check CHECK (((vida_util_anos > 0) OR (vida_util_anos IS NULL)));
ALTER TABLE public.ip_eficacia_luminosa ADD CONSTRAINT ip_eficacia_luminosa_lm_w_check CHECK ((lm_w >= (0)::numeric));
ALTER TABLE public.painel_campos_disponveis ADD CONSTRAINT painel_campos_disponveis_tipo_check CHECK ((tipo = ANY (ARRAY['text'::text, 'number'::text, 'date'::text, 'boolean'::text, 'status'::text, 'other'::text])));
ALTER TABLE public.pontos_luminaria ADD CONSTRAINT chk_potencia_w CHECK (((potencia_w IS NULL) OR ((potencia_w >= 0) AND (potencia_w <= 2000))));
ALTER TABLE public.pontos_luminaria ADD CONSTRAINT pontos_luminaria_angulo_inclinacao_graus_check CHECK (((angulo_inclinacao_graus IS NULL) OR (angulo_inclinacao_graus = ANY (ARRAY[0, 15, 30, 45, 60, 75, 90, 120]))));
ALTER TABLE public.pontos_luminaria ADD CONSTRAINT pontos_luminaria_health_status_check CHECK ((health_status = ANY (ARRAY['verde'::text, 'amarelo'::text, 'vermelho'::text, 'cinza'::text])));
ALTER TABLE public.ref_material_piso ADD CONSTRAINT ref_material_piso_refletancia_check CHECK (((refletancia >= (0)::numeric) AND (refletancia <= (1)::numeric)));
ALTER TABLE public.site_config ADD CONSTRAINT single_row CHECK ((id = 1));
ALTER TABLE public.site_config ADD CONSTRAINT site_config_painel_design_check CHECK ((painel_design = ANY (ARRAY['minimalist'::text, 'card-grid'::text, 'tabbed'::text, 'status-highlighted'::text, 'compact-dense'::text])));


-- ============================================================================
-- 9. INDICES
-- ============================================================================

CREATE INDEX idx_bairros_geom ON public.bairros_niteroi USING gist (geom);
CREATE INDEX idx_comunidades_zeis_geom ON public.comunidades_zeis USING gist (geom);
CREATE INDEX idx_comunidades_zeis_nome ON public.comunidades_zeis USING btree (nome);
CREATE INDEX idx_equip_eficacia_lm_w ON public.equipamentos_modelo USING btree (eficacia_luminosa_lm_w);
CREATE INDEX idx_equip_fator_potencia ON public.equipamentos_modelo USING btree (fator_potencia_fp);
CREATE INDEX idx_equip_fluxo_lm ON public.equipamentos_modelo USING btree (fluxo_luminoso_lm);
CREATE INDEX idx_equip_garantia ON public.equipamentos_modelo USING btree (garantia_anos) WHERE (garantia_anos IS NOT NULL);
CREATE INDEX idx_equip_grau_ik ON public.equipamentos_modelo USING btree (grau_ik);
CREATE INDEX idx_equip_inmetro ON public.equipamentos_modelo USING btree (inmetro_registro) WHERE (inmetro_registro IS NOT NULL);
CREATE INDEX idx_equip_tipo_conectividade ON public.equipamentos_modelo USING btree (tipo_conectividade);
CREATE INDEX idx_equip_vida_util ON public.equipamentos_modelo USING btree (vida_util_anos) WHERE (vida_util_anos IS NOT NULL);
CREATE INDEX idx_equipamentos_modelo_fabricante ON public.equipamentos_modelo USING btree (fabricante);
CREATE INDEX idx_equipamentos_modelo_potencia ON public.equipamentos_modelo USING btree (potencia_w);
CREATE INDEX idx_equipamentos_modelo_tecnologia ON public.equipamentos_modelo USING btree (tecnologia);
CREATE INDEX idx_hist_ponto ON public.pontos_luminaria_historico USING btree (ponto_id, alterado_em DESC);
CREATE INDEX idx_interv_ponto ON public.pontos_intervencoes USING btree (ponto_id, data DESC);
CREATE INDEX idx_lotes_registro ON public.lotes_substituicao USING btree (registro_id);
CREATE INDEX idx_painel_campos_secao ON public.painel_campos_disponveis USING btree (secao);
CREATE INDEX idx_pontos_bairro_id ON public.pontos_luminaria USING btree (bairro_id);
CREATE INDEX idx_pontos_bairro_nome ON public.pontos_luminaria USING btree (bairro_nome);
CREATE INDEX idx_pontos_campanha ON public.pontos_luminaria USING btree (campanha_id);
CREATE INDEX idx_pontos_fonte ON public.pontos_luminaria USING btree (fonte);
CREATE INDEX idx_pontos_geom ON public.pontos_luminaria USING gist (geom);
CREATE INDEX idx_pontos_health_status ON public.pontos_luminaria USING btree (health_status);
CREATE INDEX idx_pontos_modernizado ON public.pontos_luminaria USING btree (modernizado_led);
CREATE INDEX idx_pontos_municipio ON public.pontos_luminaria USING btree (municipio_id);
CREATE INDEX idx_pontos_registro_pai ON public.pontos_luminaria USING btree (registro_pai_id);
CREATE INDEX idx_registros_bairro_id ON public.registros_iluminacao USING btree (bairro_id);
CREATE INDEX idx_registros_categoria ON public.registros_iluminacao USING btree (categoria);
CREATE INDEX idx_registros_flag_revisao ON public.registros_iluminacao USING btree (flag_revisao) WHERE (flag_revisao = true);
CREATE INDEX idx_registros_geom ON public.registros_iluminacao USING gist (geom);
CREATE INDEX idx_registros_status_revisao ON public.registros_iluminacao USING btree (status_revisao);
CREATE INDEX idx_removidos_ponto ON public.ativos_removidos USING btree (ponto_id);
CREATE INDEX idx_removidos_removido_em ON public.ativos_removidos USING btree (removido_em DESC);
CREATE INDEX idx_removidos_status ON public.ativos_removidos USING btree (status);
CREATE UNIQUE INDEX ux_codigo_seconser ON public.pontos_luminaria USING btree (codigo_seconser);


-- ============================================================================
-- 10. VIEWS
-- ============================================================================

CREATE OR REPLACE VIEW public.v_parque_export AS
 SELECT id,
    numero_patrimonio,
    codigo_seconser,
    endereco,
    bairro_nome,
    bairro_enel,
    tipo_ativo,
    tipo_luminaria,
    tipo_lampada,
    potencia_w,
    status,
    health_status,
    modernizado_led,
    classe_nbr,
    fonte,
    fonte_modernizacao,
    data_modernizacao,
    censo_tipo_original,
    censo_potencia_original,
    status_operacional_censo,
    flag_revisao_censo,
    observacoes,
    st_y(geom) AS lat,
    st_x(geom) AS lon,
    criado_em,
    atualizado_em,
    criado_por,
    angulo_inclinacao_graus,
    material_piso,
    campanha_id,
    verificado_em,
    verificado_por,
    municipio_id
   FROM pontos_luminaria p
  ORDER BY criado_em DESC;

CREATE OR REPLACE VIEW public.vw_mapa_pontos AS
 SELECT id,
    registro_pai_id,
    tipo_lampada,
    potencia_w,
    status,
    fonte,
    data_instalacao,
    observacoes,
    endereco,
    numero_patrimonio,
    criado_por,
    criado_em,
    st_asgeojson(geom)::jsonb AS geometria_geojson
   FROM pontos_luminaria;

CREATE OR REPLACE VIEW public.vw_mapa_registros AS
 SELECT id,
    kml_id_original,
    nome_original,
    categoria,
    tipo_registro,
    status_revisao,
    flag_revisao,
    descricao_bruta,
    cor_linha_original_hex,
    bairro_id,
    bairro_nome,
    ano_referencia,
    st_asgeojson(geom)::jsonb AS geometria_geojson
   FROM registros_iluminacao;

CREATE OR REPLACE VIEW public.vw_totais_por_registro AS
 SELECT r.id,
    r.nome_original,
    r.categoria,
    r.tipo_registro,
    r.status_revisao,
    count(l.id) AS qtd_lotes,
    COALESCE(sum(l.quantidade) FILTER (WHERE l.confianca = 'alta'::nivel_confianca), 0::bigint) AS total_confianca_alta,
    COALESCE(sum(l.quantidade), 0::bigint) AS total_qualquer_confianca
   FROM registros_iluminacao r
     LEFT JOIN lotes_substituicao l ON l.registro_id = r.id
  GROUP BY r.id, r.nome_original, r.categoria, r.tipo_registro, r.status_revisao;


-- ============================================================================
-- 11. FUNCOES E RPCs
-- ============================================================================

CREATE OR REPLACE FUNCTION public.atribuir_bairro_ponto()
 RETURNS trigger
 LANGUAGE plpgsql
 SET search_path TO 'public'
AS $function$
begin
  select b.id, b.nome_bairro into new.bairro_id, new.bairro_nome
  from bairros_niteroi b
  where ST_Intersects(b.geom, new.geom)
  limit 1;
  return new;
end;
$function$
;

CREATE OR REPLACE FUNCTION public.atribuir_bairro_registro()
 RETURNS trigger
 LANGUAGE plpgsql
 SET search_path TO 'public'
AS $function$
begin
  select b.id, b.nome_bairro into new.bairro_id, new.bairro_nome
  from bairros_niteroi b
  where ST_Intersects(b.geom, ST_PointOnSurface(new.geom))
  limit 1;
  return new;
end;
$function$
;

CREATE OR REPLACE FUNCTION public.calc_health_status(p_idade_anos integer, p_modernizado_led boolean, p_potencia_w integer, p_flag_revisao boolean)
 RETURNS text
 LANGUAGE sql
 IMMUTABLE
AS $function$
  SELECT CASE
    WHEN p_idade_anos IS NULL THEN 'cinza'
    WHEN p_idade_anos > 12 THEN 'vermelho'
    WHEN p_modernizado_led = false AND p_potencia_w > 400 THEN 'vermelho'
    WHEN p_idade_anos >= 8 AND p_idade_anos <= 12 THEN 'amarelo'
    WHEN p_flag_revisao = true THEN 'amarelo'
    WHEN p_idade_anos < 8 THEN 'verde'
    ELSE 'cinza'
  END;
$function$
;

CREATE OR REPLACE FUNCTION public.handle_new_user()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
BEGIN
  INSERT INTO public.profiles (id, email, role) VALUES (NEW.id, NEW.email, 'leitura')
  ON CONFLICT (id) DO NOTHING;
  RETURN NEW;
END $function$
;

CREATE OR REPLACE FUNCTION public.ip_atualizar_modelo(p_id uuid, p_fabricante text DEFAULT NULL::text, p_modelo text DEFAULT NULL::text, p_potencia_w integer DEFAULT NULL::integer, p_temperatura_cor_k integer DEFAULT NULL::integer, p_tensao text DEFAULT NULL::text, p_ip text DEFAULT NULL::text, p_classe_nbr text DEFAULT NULL::text, p_tecnologia text DEFAULT NULL::text, p_tipo_luminaria text DEFAULT NULL::text, p_tipo_lampada text DEFAULT NULL::text, p_foto_url text DEFAULT NULL::text, p_descricao text DEFAULT NULL::text, p_fluxo_luminoso_lm integer DEFAULT NULL::integer, p_eficacia_luminosa_lm_w numeric DEFAULT NULL::numeric, p_fator_potencia_fp numeric DEFAULT NULL::numeric, p_thd_percentual numeric DEFAULT NULL::numeric, p_grau_ik text DEFAULT NULL::text, p_dps_especificacao text DEFAULT NULL::text, p_tipo_conectividade text DEFAULT NULL::text, p_arquivo_ies_url text DEFAULT NULL::text, p_inmetro_registro text DEFAULT NULL::text, p_vida_util_anos integer DEFAULT NULL::integer, p_garantia_anos integer DEFAULT NULL::integer, p_dias_manutencao_preventiva integer DEFAULT NULL::integer)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
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
    fluxo_luminoso_lm = COALESCE(p_fluxo_luminoso_lm, fluxo_luminoso_lm),
    eficacia_luminosa_lm_w = COALESCE(p_eficacia_luminosa_lm_w, eficacia_luminosa_lm_w),
    fator_potencia_fp = COALESCE(p_fator_potencia_fp, fator_potencia_fp),
    thd_percentual = COALESCE(p_thd_percentual, thd_percentual),
    grau_ik = COALESCE(p_grau_ik, grau_ik),
    dps_especificacao = COALESCE(p_dps_especificacao, dps_especificacao),
    tipo_conectividade = COALESCE(p_tipo_conectividade, tipo_conectividade),
    arquivo_ies_url = COALESCE(p_arquivo_ies_url, arquivo_ies_url),
    inmetro_registro = COALESCE(p_inmetro_registro, inmetro_registro),
    vida_util_anos = COALESCE(p_vida_util_anos, vida_util_anos),
    garantia_anos = COALESCE(p_garantia_anos, garantia_anos),
    dias_manutencao_preventiva = COALESCE(p_dias_manutencao_preventiva, dias_manutencao_preventiva),
    updated_at = now()
  WHERE id = p_id;
END;
$function$
;

CREATE OR REPLACE FUNCTION public.ip_atualizar_painel_config(p_design text DEFAULT NULL::text, p_campos jsonb DEFAULT NULL::jsonb)
 RETURNS TABLE(success boolean, message text)
 LANGUAGE plpgsql
 SECURITY DEFINER
AS $function$
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
$function$
;

CREATE OR REPLACE FUNCTION public.ip_atualizar_ponto(p_id uuid, p_tipo text DEFAULT NULL::text, p_potencia integer DEFAULT NULL::integer, p_status text DEFAULT NULL::text, p_modernizado boolean DEFAULT NULL::boolean, p_obs text DEFAULT NULL::text, p_lat numeric DEFAULT NULL::numeric, p_lng numeric DEFAULT NULL::numeric, p_tipo_luminaria text DEFAULT NULL::text, p_classe_nbr text DEFAULT NULL::text, p_angulo integer DEFAULT NULL::integer, p_material text DEFAULT NULL::text)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
DECLARE v_user_id uuid; v_role text; v_camp uuid;
BEGIN
  v_user_id := auth.uid();
  IF v_user_id IS NULL THEN RETURN jsonb_build_object('error','Não autenticado'); END IF;
  SELECT role INTO v_role FROM public.profiles WHERE id = v_user_id;
  IF v_role IS NULL OR v_role NOT IN ('editor','admin') THEN
    RETURN jsonb_build_object('error','Sem permissão para editar');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM public.pontos_luminaria WHERE id = p_id) THEN
    RETURN jsonb_build_object('error','Ponto não encontrado');
  END IF;
  SELECT id INTO v_camp FROM public.campanhas WHERE status='ativa' ORDER BY criado_em DESC LIMIT 1;
  UPDATE public.pontos_luminaria SET
    tipo_lampada = COALESCE(p_tipo::tipo_lampada, tipo_lampada),
    potencia_w = COALESCE(p_potencia, potencia_w),
    status = COALESCE(p_status::status_luminaria, status),
    modernizado_led = COALESCE(p_modernizado, modernizado_led),
    observacoes = COALESCE(p_obs, observacoes),
    geom = CASE WHEN p_lat IS NOT NULL AND p_lng IS NOT NULL
                THEN ST_SetSRID(ST_MakePoint(p_lng::double precision, p_lat::double precision), 4326)
                ELSE geom END,
    tipo_luminaria = CASE WHEN p_tipo_luminaria IS NOT NULL THEN p_tipo_luminaria::luminaria_tipo ELSE tipo_luminaria END,
    classe_nbr = COALESCE(p_classe_nbr, classe_nbr),
    angulo_inclinacao_graus = COALESCE(p_angulo, angulo_inclinacao_graus),
    material_piso = COALESCE(p_material, material_piso),
    verificado_em  = CASE WHEN v_camp IS NOT NULL THEN now() ELSE verificado_em END,
    verificado_por = CASE WHEN v_camp IS NOT NULL THEN v_user_id ELSE verificado_por END,
    campanha_id    = CASE WHEN v_camp IS NOT NULL THEN v_camp ELSE campanha_id END,
    atualizado_em = now()
  WHERE id = p_id;
  RETURN jsonb_build_object('success', true, 'message', 'Ponto atualizado');
END; $function$
;

CREATE OR REPLACE FUNCTION public.ip_bairro_geojson(p_bairro text)
 RETURNS json
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  SELECT ST_AsGeoJSON(geom)::json FROM bairros_niteroi WHERE nome_bairro = p_bairro LIMIT 1;
$function$
;

CREATE OR REPLACE FUNCTION public.ip_bairros_choropleth()
 RETURNS json
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  WITH agg AS (
    SELECT bairro_nome,
           count(*) total,
           count(*) FILTER (WHERE modernizado_led) led,
           count(*) FILTER (WHERE NOT modernizado_led) pendente,
           round(100.0*count(*) FILTER (WHERE modernizado_led)/nullif(count(*),0),1) pct_led
    FROM pontos_luminaria
    GROUP BY bairro_nome
  )
  SELECT json_build_object('type','FeatureCollection','features',
    coalesce(json_agg(json_build_object(
      'type','Feature',
      'properties', json_build_object('bairro',b.nome_bairro,
                                      'total',    coalesce(a.total,0),
                                      'led',      coalesce(a.led,0),
                                      'pendente', coalesce(a.pendente,0),
                                      'pct_led',  a.pct_led),
      'geometry', ST_AsGeoJSON(b.geom)::json)),'[]'::json))
  FROM bairros_niteroi b
  LEFT JOIN agg a ON a.bairro_nome = b.nome_bairro;
$function$
;

CREATE OR REPLACE FUNCTION public.ip_clusters_grid(min_lng double precision, min_lat double precision, max_lng double precision, max_lat double precision, grid_deg double precision, p_bairro text DEFAULT NULL::text, p_tipo text DEFAULT NULL::text, p_modernizado boolean DEFAULT NULL::boolean, p_pot_min integer DEFAULT NULL::integer, p_revisao boolean DEFAULT NULL::boolean, p_fonte_mod text DEFAULT NULL::text, p_suspeito boolean DEFAULT NULL::boolean, p_led_min integer DEFAULT NULL::integer, p_led_max integer DEFAULT NULL::integer, p_power_min integer DEFAULT NULL::integer, p_power_max integer DEFAULT NULL::integer, p_data_inicio date DEFAULT NULL::date, p_data_fim date DEFAULT NULL::date, p_health_status text DEFAULT NULL::text, p_nao_verificado boolean DEFAULT NULL::boolean)
 RETURNS json
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
DECLARE resultado json;
BEGIN
  SELECT coalesce(json_agg(row_to_json(t)),'[]'::json) INTO resultado FROM (
    SELECT count(*) n, count(*) FILTER (WHERE modernizado_led) led,
           avg(x) lon, avg(y) lat
    FROM (
      SELECT modernizado_led, ST_X(geom) x, ST_Y(geom) y
      FROM pontos_luminaria
      WHERE geom && ST_MakeEnvelope(min_lng,min_lat,max_lng,max_lat,4326)
        AND (p_bairro IS NULL OR bairro_nome=p_bairro)
        AND (p_tipo IS NULL OR tipo_lampada::text=p_tipo)
        AND (p_modernizado IS NULL OR modernizado_led=p_modernizado)
        AND (p_pot_min IS NULL OR potencia_w>=p_pot_min)
        AND (p_revisao IS NULL OR flag_revisao_censo=p_revisao)
        AND (p_fonte_mod IS NULL OR fonte_modernizacao=p_fonte_mod)
        AND (p_suspeito IS NULL OR (modernizado_led AND potencia_w>400))
        AND (p_led_min IS NULL OR potencia_w >= p_led_min)
        AND (p_led_max IS NULL OR potencia_w <= p_led_max)
        AND (p_power_min IS NULL OR potencia_w >= p_power_min)
        AND (p_power_max IS NULL OR potencia_w <= p_power_max)
        AND (p_data_inicio IS NULL OR data_modernizacao >= p_data_inicio)
        AND (p_data_fim IS NULL OR data_modernizacao <= p_data_fim)
        AND (p_health_status IS NULL OR health_status = p_health_status)
        AND (p_nao_verificado IS NULL OR (p_nao_verificado AND verificado_em IS NULL) OR (NOT p_nao_verificado AND verificado_em IS NOT NULL))
    ) s
    GROUP BY round(x/grid_deg), round(y/grid_deg)) t;
  RETURN resultado;
END
$function$
;

CREATE OR REPLACE FUNCTION public.ip_comunidade_geom(p_nome text)
 RETURNS json
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  SELECT ST_AsGeoJSON(ST_Multi(ST_Union(geom)))::json
  FROM comunidades_zeis
  WHERE nome = p_nome;
$function$
;

CREATE OR REPLACE FUNCTION public.ip_comunidades_lista()
 RETURNS json
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  SELECT coalesce(json_agg(row_to_json(t) ORDER BY t.nome), '[]'::json) FROM (
    SELECT nome,
           string_agg(DISTINCT coalesce(bairro, '-'), ' / ') AS bairro,
           count(*)::int AS n_poligonos
    FROM comunidades_zeis
    GROUP BY nome
  ) t;
$function$
;

CREATE OR REPLACE FUNCTION public.ip_confirmar_ponto(p_id uuid)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
DECLARE v_user uuid; v_role text; v_camp uuid; v_nome text;
BEGIN
  v_user := auth.uid();
  IF v_user IS NULL THEN RETURN jsonb_build_object('error','Não autenticado'); END IF;
  SELECT role INTO v_role FROM public.profiles WHERE id = v_user;
  IF v_role IS NULL OR v_role NOT IN ('editor','admin') THEN
    RETURN jsonb_build_object('error','Sem permissão para verificar pontos');
  END IF;
  SELECT id, nome INTO v_camp, v_nome FROM public.campanhas
  WHERE status='ativa' ORDER BY criado_em DESC LIMIT 1;
  IF v_camp IS NULL THEN
    RETURN jsonb_build_object('error','Nenhuma campanha de recenseamento ativa — crie uma em Admin → Campanhas');
  END IF;
  UPDATE public.pontos_luminaria
  SET verificado_em=now(), verificado_por=v_user, campanha_id=v_camp, atualizado_em=now()
  WHERE id = p_id;
  IF NOT FOUND THEN RETURN jsonb_build_object('error','Ponto não encontrado'); END IF;
  RETURN jsonb_build_object('success', true, 'campanha', v_nome);
END $function$
;

CREATE OR REPLACE FUNCTION public.ip_criar_campanha(p_nome text, p_descricao text DEFAULT NULL::text)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
DECLARE v_role text; v_id uuid;
BEGIN
  SELECT role INTO v_role FROM public.profiles WHERE id = auth.uid();
  IF v_role IS NULL OR v_role NOT IN ('editor','admin') THEN
    RETURN jsonb_build_object('error','Sem permissão para criar campanhas');
  END IF;
  IF coalesce(trim(p_nome),'') = '' THEN RETURN jsonb_build_object('error','Informe o nome da campanha'); END IF;
  IF EXISTS (SELECT 1 FROM public.campanhas WHERE status='ativa') THEN
    RETURN jsonb_build_object('error','Já existe uma campanha ativa — encerre-a antes de criar outra');
  END IF;
  INSERT INTO public.campanhas (nome, descricao, criado_por)
  VALUES (trim(p_nome), nullif(trim(coalesce(p_descricao,'')),''), auth.uid()) RETURNING id INTO v_id;
  RETURN jsonb_build_object('success', true, 'id', v_id);
END $function$
;

CREATE OR REPLACE FUNCTION public.ip_criar_modelo(p_fabricante text, p_modelo text, p_potencia_w integer, p_temperatura_cor_k integer DEFAULT NULL::integer, p_tensao text DEFAULT NULL::text, p_ip text DEFAULT NULL::text, p_classe_nbr text DEFAULT NULL::text, p_tecnologia text DEFAULT 'LED'::text, p_tipo_luminaria text DEFAULT NULL::text, p_tipo_lampada text DEFAULT 'led'::text, p_foto_url text DEFAULT NULL::text, p_descricao text DEFAULT NULL::text, p_fluxo_luminoso_lm integer DEFAULT NULL::integer, p_eficacia_luminosa_lm_w numeric DEFAULT NULL::numeric, p_fator_potencia_fp numeric DEFAULT NULL::numeric, p_thd_percentual numeric DEFAULT NULL::numeric, p_grau_ik text DEFAULT NULL::text, p_dps_especificacao text DEFAULT NULL::text, p_tipo_conectividade text DEFAULT NULL::text, p_arquivo_ies_url text DEFAULT NULL::text, p_inmetro_registro text DEFAULT NULL::text, p_vida_util_anos integer DEFAULT NULL::integer, p_garantia_anos integer DEFAULT NULL::integer, p_dias_manutencao_preventiva integer DEFAULT NULL::integer)
 RETURNS uuid
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
DECLARE
  v_id uuid;
BEGIN
  INSERT INTO public.equipamentos_modelo (
    fabricante, modelo, potencia_w, temperatura_cor_k, tensao, ip, classe_nbr,
    tecnologia, tipo_luminaria, tipo_lampada, foto_url, descricao,
    fluxo_luminoso_lm, eficacia_luminosa_lm_w, fator_potencia_fp, thd_percentual,
    grau_ik, dps_especificacao, tipo_conectividade, arquivo_ies_url,
    inmetro_registro, vida_util_anos, garantia_anos, dias_manutencao_preventiva,
    created_by
  )
  VALUES (
    p_fabricante, p_modelo, p_potencia_w, p_temperatura_cor_k, p_tensao, p_ip,
    p_classe_nbr, p_tecnologia, p_tipo_luminaria, p_tipo_lampada, p_foto_url,
    p_descricao, p_fluxo_luminoso_lm, p_eficacia_luminosa_lm_w, p_fator_potencia_fp,
    p_thd_percentual, p_grau_ik, p_dps_especificacao, p_tipo_conectividade,
    p_arquivo_ies_url, p_inmetro_registro, p_vida_util_anos, p_garantia_anos,
    p_dias_manutencao_preventiva, auth.uid()
  )
  RETURNING id INTO v_id;
  RETURN v_id;
END;
$function$
;

CREATE OR REPLACE FUNCTION public.ip_deletar_modelo(p_id uuid)
 RETURNS boolean
 LANGUAGE plpgsql
 SET search_path TO 'public'
AS $function$
begin
  update public.equipamentos_modelo
  set ativo = false, updated_at = now()
  where id = p_id;

  return found;
end;
$function$
;

CREATE OR REPLACE FUNCTION public.ip_encerrar_campanha(p_id uuid)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
DECLARE v_role text;
BEGIN
  SELECT role INTO v_role FROM public.profiles WHERE id = auth.uid();
  IF v_role IS NULL OR v_role NOT IN ('editor','admin') THEN
    RETURN jsonb_build_object('error','Sem permissão para encerrar campanhas');
  END IF;
  UPDATE public.campanhas SET status='encerrada', encerrada_em=now() WHERE id=p_id AND status='ativa';
  IF NOT FOUND THEN RETURN jsonb_build_object('error','Campanha não encontrada ou já encerrada'); END IF;
  RETURN jsonb_build_object('success', true);
END $function$
;

CREATE OR REPLACE FUNCTION public.ip_estatisticas(p_bairro text DEFAULT NULL::text)
 RETURNS json
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  SELECT json_build_object(
    'total', count(*),
    'led', count(*) FILTER (WHERE modernizado_led),
    'led_censo', count(*) FILTER (WHERE modernizado_led AND fonte_modernizacao='censo_enel'),
    'led_seconser', count(*) FILTER (WHERE modernizado_led AND fonte_modernizacao='seconser_pos_censo'),
    'pendente', count(*) FILTER (WHERE NOT modernizado_led),
    'pct_led', round(100.0*count(*) FILTER (WHERE modernizado_led)/nullif(count(*),0),1),
    'potencia_kw', round((sum(potencia_w) FILTER (WHERE modernizado_led))::numeric/1000,1),
    'flag_revisao', count(*) FILTER (WHERE flag_revisao_censo)
  )
  FROM pontos_luminaria
  WHERE (p_bairro IS NULL OR bairro_nome = p_bairro);
$function$
;

CREATE OR REPLACE FUNCTION public.ip_estatisticas_gerais()
 RETURNS json
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  SELECT json_build_object(
    'total_luminas', COUNT(*),
    'led_total', ROUND(100.0 * COUNT(*) FILTER (WHERE modernizado_led) / NULLIF(COUNT(*), 0), 1),
    'potencia_media', ROUND((AVG(potencia_w) FILTER (WHERE potencia_w > 0))::numeric, 1),
    'eficacia_media', 80
  )
  FROM pontos_luminaria;
$function$
;

CREATE OR REPLACE FUNCTION public.ip_gera_codigo(p_tipo ativo_tipo)
 RETURNS text
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
DECLARE pre text; n bigint;
BEGIN
  pre := CASE p_tipo
    WHEN 'luminaria' THEN 'LUM' WHEN 'caixa_comando' THEN 'CMD'
    WHEN 'chave_magnetica' THEN 'CHV' WHEN 'rele_fotoeletrico' THEN 'RFP'
    WHEN 'poste' THEN 'PST' WHEN 'braco' THEN 'BRC' ELSE 'OUT' END;
  n := nextval('seq_ipnit_'||lower(pre));
  RETURN 'IPNIT-'||pre||'-'||lpad(n::text,6,'0');
END $function$
;

CREATE OR REPLACE FUNCTION public.ip_grid_densidade(p_cell_m integer DEFAULT 250)
 RETURNS TABLE(gj jsonb, n integer, n_led integer, kw numeric, klm numeric, lm_w numeric, cobertura_pot numeric, pct_led numeric)
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  with prm as (
    select greatest(100, least(2000, coalesce(p_cell_m, 250))) as c
  ),
  lum as (
    select st_transform(p.geom, 31983) as g,
           p.potencia_w, p.modernizado_led, e.lm_w
    from pontos_luminaria p
    left join ip_eficacia_luminosa e on e.tipo = p.tipo_lampada::text
    where p.geom is not null
      and p.potencia_w is not null
  ),
  cel as (
    select floor(st_x(l.g) / prm.c)::int as cx,
           floor(st_y(l.g) / prm.c)::int as cy,
           prm.c as c,
           count(*) as n,
           count(*) filter (where l.modernizado_led) as n_led,
           sum(l.potencia_w) as w_total,
           sum(l.potencia_w * l.lm_w) filter (where l.lm_w is not null) as lm_total,
           count(l.potencia_w) as n_pot
    from lum l cross join prm
    group by 1, 2, 3
  )
  select
    st_asgeojson(
      st_transform(
        st_makeenvelope(cx*c, cy*c, (cx+1)*c, (cy+1)*c, 31983), 4326), 6)::jsonb,
    n::int,
    n_led::int,
    round(coalesce(w_total,0) / 1000.0, 2),
    round(coalesce(lm_total,0) / 1000.0, 0),
    case when w_total > 0 and lm_total is not null
         then round(lm_total / w_total, 0) end,
    round(100.0 * n_pot / n, 0),
    round(100.0 * n_led / n, 0)
  from cel;
$function$
;

CREATE OR REPLACE FUNCTION public.ip_grid_densidade_completo(p_cell_m integer DEFAULT 250)
 RETURNS TABLE(gj jsonb, n integer, n_led integer, kw numeric, klm numeric, lm_w numeric, cobertura_pot numeric, pct_led numeric)
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  with prm as (
    select greatest(100, least(2000, coalesce(p_cell_m, 250))) as c
  ),
  lum as (
    select st_transform(p.geom, 31983) as g,
           p.potencia_w, p.modernizado_led, e.lm_w
    from pontos_luminaria p
    left join ip_eficacia_luminosa e on e.tipo = p.tipo_lampada::text
    where p.geom is not null and p.potencia_w is not null
  ),
  cel_com_dados as (
    select floor(st_x(l.g) / prm.c)::int as cx,
           floor(st_y(l.g) / prm.c)::int as cy,
           prm.c as c,
           count(*) as n,
           count(*) filter (where l.modernizado_led) as n_led,
           sum(l.potencia_w) as w_total,
           sum(l.potencia_w * l.lm_w) filter (where l.lm_w is not null) as lm_total,
           count(l.potencia_w) as n_pot
    from lum l cross join prm
    group by 1, 2, 3
  )
  select
    st_asgeojson(
      st_transform(
        st_makeenvelope(cx*c, cy*c, (cx+1)*c, (cy+1)*c, 31983), 4326), 6)::jsonb,
    n::int,
    n_led::int,
    round(coalesce(w_total,0) / 1000.0, 2),
    round(coalesce(lm_total,0) / 1000.0, 0),
    case when w_total > 0 and lm_total is not null then round(lm_total / w_total, 0) end,
    case when n > 0 then round(100.0 * n_pot / n, 0) else 0 end,
    case when n > 0 then round(100.0 * n_led / n, 0) else 0 end
  from cel_com_dados;
$function$
;

CREATE OR REPLACE FUNCTION public.ip_grid_densidade_json(p_cell_m integer DEFAULT 250)
 RETURNS jsonb
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  with prm as (
    select greatest(100, least(2000, coalesce(p_cell_m, 250))) as c
  ),
  lum as (
    select st_transform(p.geom, 31983) as g,
           p.potencia_w, p.modernizado_led, e.lm_w
    from pontos_luminaria p
    left join ip_eficacia_luminosa e on e.tipo = p.tipo_lampada::text
    where p.geom is not null and p.potencia_w is not null
  ),
  cel as (
    select floor(st_x(l.g) / prm.c)::int as cx,
           floor(st_y(l.g) / prm.c)::int as cy,
           prm.c as c,
           count(*) as n,
           count(*) filter (where l.modernizado_led) as n_led,
           sum(l.potencia_w) as w_total,
           sum(l.potencia_w * l.lm_w) filter (where l.lm_w is not null) as lm_total,
           count(l.potencia_w) as n_pot
    from lum l cross join prm
    group by 1, 2, 3
  )
  select jsonb_agg(jsonb_build_object(
    'gj', st_asgeojson(st_transform(
            st_makeenvelope(cx*c, cy*c, (cx+1)*c, (cy+1)*c, 31983), 4326), 6)::jsonb,
    'n', n,
    'n_led', n_led,
    'kw', round(coalesce(w_total,0) / 1000.0, 2),
    'klm', round(coalesce(lm_total,0) / 1000.0, 0),
    'lm_w', case when w_total > 0 and lm_total is not null then round(lm_total / w_total, 0) end,
    'cobertura_pot', case when n > 0 then round(100.0 * n_pot / n, 0) else 0 end,
    'pct_led', case when n > 0 then round(100.0 * n_led / n, 0) else 0 end
  ))
  from cel;
$function$
;

CREATE OR REPLACE FUNCTION public.ip_health_status_summary(min_lng double precision, min_lat double precision, max_lng double precision, max_lat double precision)
 RETURNS json
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  SELECT json_build_object(
    'verde', COUNT(*) FILTER (WHERE health_status = 'verde'),
    'amarelo', COUNT(*) FILTER (WHERE health_status = 'amarelo'),
    'vermelho', COUNT(*) FILTER (WHERE health_status = 'vermelho'),
    'cinza', COUNT(*) FILTER (WHERE health_status = 'cinza'),
    'total', COUNT(*)
  )
  FROM pontos_luminaria
  WHERE geom && ST_MakeEnvelope(min_lng,min_lat,max_lng,max_lat,4326);
$function$
;

CREATE OR REPLACE FUNCTION public.ip_historico_ponto(p_id uuid)
 RETURNS json
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  SELECT coalesce(json_agg(json_build_object(
    'operacao', operacao,
    'alterado_por', alterado_por,
    'alterado_em', alterado_em,
    'tipo_antes', dados_antes->>'tipo_lampada',
    'tipo_depois', dados_depois->>'tipo_lampada',
    'status_antes', dados_antes->>'status',
    'status_depois', dados_depois->>'status',
    'pot_antes', dados_antes->>'potencia_w',
    'pot_depois', dados_depois->>'potencia_w',
    'led_antes', dados_antes->>'modernizado_led',
    'led_depois', dados_depois->>'modernizado_led'
  ) ORDER BY alterado_em DESC), '[]'::json)
  FROM pontos_luminaria_historico
  WHERE ponto_id = p_id
    AND EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid());  -- só usuários logados
$function$
;

CREATE OR REPLACE FUNCTION public.ip_inserir_ponto(p_lat numeric, p_lng numeric, p_tipo text, p_potencia integer, p_status text, p_modernizado boolean, p_endereco text, p_patrimonio text, p_obs text, p_tipo_ativo text, p_tipo_luminaria text, p_classe_nbr text, p_angulo integer DEFAULT NULL::integer, p_material text DEFAULT NULL::text)
 RETURNS text
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
DECLARE v_role TEXT; v_id UUID; v_camp uuid;
BEGIN
  SELECT role INTO v_role FROM public.profiles WHERE id = auth.uid();
  IF v_role IS NULL THEN v_role := 'leitura'; END IF;
  IF v_role NOT IN ('editor','admin') THEN
    RAISE EXCEPTION 'Permissão negada: apenas editores e administradores podem criar pontos';
  END IF;
  v_id := gen_random_uuid();
  SELECT id INTO v_camp FROM public.campanhas WHERE status='ativa' ORDER BY criado_em DESC LIMIT 1;
  INSERT INTO public.pontos_luminaria (
    id, geom, tipo_ativo, tipo_luminaria, potencia_w, modernizado_led, tipo_lampada, status,
    observacoes, endereco, numero_patrimonio, criado_em, criado_por, classe_nbr, fonte,
    angulo_inclinacao_graus, material_piso, verificado_em, verificado_por, campanha_id
  ) VALUES (
    v_id, ST_SetSRID(ST_MakePoint(p_lng::double precision, p_lat::double precision), 4326),
    p_tipo_ativo::ativo_tipo,
    CASE WHEN p_tipo_ativo='luminaria' AND p_tipo_luminaria IS NOT NULL THEN p_tipo_luminaria::luminaria_tipo ELSE NULL END,
    CASE WHEN p_tipo_ativo='luminaria' THEN p_potencia ELSE NULL END,
    CASE WHEN p_tipo_ativo='luminaria' THEN COALESCE(p_modernizado,false) ELSE false END,
    CASE WHEN p_tipo_ativo='luminaria' THEN p_tipo::tipo_lampada ELSE NULL END,
    COALESCE(p_status,'a_verificar')::status_luminaria, COALESCE(p_obs,''),
    p_endereco, p_patrimonio, NOW(), auth.uid(), p_classe_nbr, 'levantamento_campo'::fonte_ponto,
    CASE WHEN p_tipo_ativo='luminaria' THEN p_angulo ELSE NULL END,
    CASE WHEN p_tipo_ativo='luminaria' THEN p_material ELSE NULL END,
    now(), auth.uid(), v_camp
  );
  RETURN v_id::TEXT;
END; $function$
;

CREATE OR REPLACE FUNCTION public.ip_intervencoes(p_id uuid)
 RETURNS json
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  SELECT coalesce(json_agg(json_build_object(
    'id',id,'tipo',tipo,'data',data,'descricao',descricao,'responsavel',responsavel,
    'lampada_nova',tipo_lampada_nova,'potencia_nova',potencia_nova_w,'registrado_por',registrado_por
  ) ORDER BY data DESC, id DESC),'[]'::json)
  FROM pontos_intervencoes
  WHERE ponto_id=p_id AND EXISTS(SELECT 1 FROM profiles WHERE id=auth.uid());
$function$
;

CREATE OR REPLACE FUNCTION public.ip_listar_campanhas()
 RETURNS json
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  SELECT coalesce(json_agg(row_to_json(t)),'[]'::json) FROM (
    SELECT c.id, c.nome, c.descricao, c.status, c.criado_em, c.encerrada_em,
           (SELECT count(*) FROM pontos_luminaria pl WHERE pl.campanha_id = c.id) AS verificados,
           (SELECT count(*) FROM pontos_luminaria) AS total_parque
    FROM campanhas c
    ORDER BY c.criado_em DESC) t;
$function$
;

CREATE OR REPLACE FUNCTION public.ip_listar_campos_disponveis()
 RETURNS TABLE(nome text, label text, tipo text, secao text, descricao text)
 LANGUAGE plpgsql
 SECURITY DEFINER
AS $function$
BEGIN
  RETURN QUERY
  SELECT pcd.nome, pcd.label, pcd.tipo, pcd.secao, pcd.descricao
  FROM public.painel_campos_disponveis pcd
  ORDER BY pcd.secao, pcd.label;
END;
$function$
;

CREATE OR REPLACE FUNCTION public.ip_listar_modelos()
 RETURNS TABLE(id uuid, fabricante text, modelo text, potencia_w integer, temperatura_cor_k integer, tensao text, ip text, classe_nbr text, tecnologia text, tipo_luminaria text, tipo_lampada text, foto_url text, descricao text, fluxo_luminoso_lm integer, eficacia_luminosa_lm_w numeric, fator_potencia_fp numeric, thd_percentual numeric, grau_ik text, dps_especificacao text, tipo_conectividade text, arquivo_ies_url text, inmetro_registro text, vida_util_anos integer, garantia_anos integer, dias_manutencao_preventiva integer)
 LANGUAGE sql
 STABLE
 SET search_path TO 'public'
AS $function$
  SELECT DISTINCT ON (em.id)
    em.id, em.fabricante, em.modelo, em.potencia_w, em.temperatura_cor_k,
    em.tensao, em.ip, em.classe_nbr, em.tecnologia, em.tipo_luminaria,
    em.tipo_lampada, em.foto_url, em.descricao, em.fluxo_luminoso_lm,
    em.eficacia_luminosa_lm_w, em.fator_potencia_fp, em.thd_percentual,
    em.grau_ik, em.dps_especificacao, em.tipo_conectividade, em.arquivo_ies_url,
    em.inmetro_registro, em.vida_util_anos, em.garantia_anos,
    em.dias_manutencao_preventiva
  FROM public.equipamentos_modelo em
  WHERE em.ativo IS NOT FALSE
  ORDER BY em.id, em.updated_at DESC
$function$
;

CREATE OR REPLACE FUNCTION public.ip_obter_painel_config()
 RETURNS TABLE(design text, campos jsonb)
 LANGUAGE plpgsql
 SECURITY DEFINER
AS $function$
BEGIN
  RETURN QUERY
  SELECT site_config.painel_design, site_config.painel_campos
  FROM public.site_config
  WHERE id = 1
  LIMIT 1;
END;
$function$
;

CREATE OR REPLACE FUNCTION public.ip_pontos_bbox(min_lng double precision, min_lat double precision, max_lng double precision, max_lat double precision, limite integer DEFAULT 4000, p_bairro text DEFAULT NULL::text, p_tipo text DEFAULT NULL::text, p_modernizado boolean DEFAULT NULL::boolean, p_pot_min integer DEFAULT NULL::integer, p_revisao boolean DEFAULT NULL::boolean, p_fonte_mod text DEFAULT NULL::text, p_suspeito boolean DEFAULT NULL::boolean, p_led_min integer DEFAULT NULL::integer, p_led_max integer DEFAULT NULL::integer, p_power_min integer DEFAULT NULL::integer, p_power_max integer DEFAULT NULL::integer, p_data_inicio date DEFAULT NULL::date, p_data_fim date DEFAULT NULL::date, p_health_status text DEFAULT NULL::text, p_nao_verificado boolean DEFAULT NULL::boolean)
 RETURNS json
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
DECLARE resultado json;
BEGIN
  SELECT coalesce(json_agg(row_to_json(t)),'[]'::json) INTO resultado FROM (
    SELECT id, ST_Y(geom) lat, ST_X(geom) lon, modernizado_led, tipo_lampada,
           potencia_w, status, bairro_nome, numero_patrimonio, endereco, fonte,
           fonte_modernizacao, censo_tipo_original, observacoes, flag_revisao_censo,
           codigo_seconser, tipo_ativo, tipo_luminaria, classe_nbr, health_status,
           angulo_inclinacao_graus, material_piso, verificado_em, campanha_id
    FROM pontos_luminaria
    WHERE geom && ST_MakeEnvelope(min_lng,min_lat,max_lng,max_lat,4326)
      AND (p_bairro IS NULL OR bairro_nome=p_bairro)
      AND (p_tipo IS NULL OR tipo_lampada::text=p_tipo)
      AND (p_modernizado IS NULL OR modernizado_led=p_modernizado)
      AND (p_pot_min IS NULL OR potencia_w>=p_pot_min)
      AND (p_revisao IS NULL OR flag_revisao_censo=p_revisao)
      AND (p_fonte_mod IS NULL OR fonte_modernizacao=p_fonte_mod)
      AND (p_suspeito IS NULL OR (modernizado_led AND potencia_w>400))
      AND (p_led_min IS NULL OR potencia_w >= p_led_min)
      AND (p_led_max IS NULL OR potencia_w <= p_led_max)
      AND (p_power_min IS NULL OR potencia_w >= p_power_min)
      AND (p_power_max IS NULL OR potencia_w <= p_power_max)
      AND (p_data_inicio IS NULL OR data_modernizacao >= p_data_inicio)
      AND (p_data_fim IS NULL OR data_modernizacao <= p_data_fim)
      AND (p_health_status IS NULL OR health_status = p_health_status)
      AND (p_nao_verificado IS NULL OR (p_nao_verificado AND verificado_em IS NULL) OR (NOT p_nao_verificado AND verificado_em IS NOT NULL))
    LIMIT limite) t;
  RETURN resultado;
END
$function$
;

CREATE OR REPLACE FUNCTION public.ip_pontos_poligono(p_geojson text, limite integer DEFAULT 5000)
 RETURNS json
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  WITH poly AS (SELECT ST_MakeValid(ST_SetSRID(ST_GeomFromGeoJSON(p_geojson), 4326)) AS g)
  SELECT coalesce(json_agg(row_to_json(t)),'[]'::json) FROM (
    SELECT pl.id, ST_Y(pl.geom) lat, ST_X(pl.geom) lon, pl.modernizado_led, pl.tipo_lampada,
           pl.potencia_w, pl.status, pl.bairro_nome, pl.numero_patrimonio, pl.endereco, pl.fonte,
           pl.fonte_modernizacao, pl.censo_tipo_original, pl.observacoes, pl.flag_revisao_censo,
           pl.codigo_seconser, pl.tipo_ativo, pl.tipo_luminaria, pl.classe_nbr, pl.health_status,
           pl.angulo_inclinacao_graus, pl.material_piso
    FROM pontos_luminaria pl, poly
    WHERE pl.geom && poly.g AND ST_Contains(poly.g, pl.geom)
    LIMIT limite) t;
$function$
;

CREATE OR REPLACE FUNCTION public.ip_por_bairro()
 RETURNS json
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  SELECT coalesce(json_agg(row_to_json(t) ORDER BY t.pendente DESC), '[]'::json) FROM (
    SELECT bairro_nome, count(*) AS total,
           count(*) FILTER (WHERE modernizado_led) AS led,
           count(*) FILTER (WHERE NOT modernizado_led) AS pendente,
           round(100.0*count(*) FILTER (WHERE modernizado_led)/count(*),1) AS pct_led
    FROM pontos_luminaria GROUP BY bairro_nome
  ) t;
$function$
;

CREATE OR REPLACE FUNCTION public.ip_qualidade_dado()
 RETURNS json
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  SELECT json_build_object(
    'revisao', (SELECT count(*) FROM pontos_luminaria WHERE flag_revisao_censo),
    'suspeito', (SELECT count(*) FROM pontos_luminaria WHERE modernizado_led AND potencia_w>400),
    'pendente', (SELECT count(*) FROM pontos_luminaria WHERE NOT modernizado_led),
    'residuo', (
      (SELECT coalesce(sum(quantidade),0) FROM lotes_substituicao WHERE quantidade>0)
      - (SELECT count(*) FROM pontos_luminaria WHERE fonte_modernizacao='seconser_pos_censo'))
  );
$function$
;

CREATE OR REPLACE FUNCTION public.ip_registrar_intervencao(p_ponto uuid, p_tipo text, p_data text DEFAULT NULL::text, p_descricao text DEFAULT NULL::text, p_responsavel text DEFAULT NULL::text, p_lampada_nova text DEFAULT NULL::text, p_potencia_nova integer DEFAULT NULL::integer)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
DECLARE v_user_id uuid; v_role text;
BEGIN
  v_user_id := auth.uid();
  IF v_user_id IS NULL THEN RETURN jsonb_build_object('error','Não autenticado'); END IF;
  SELECT role INTO v_role FROM public.profiles WHERE id = v_user_id;
  IF v_role IS NULL OR v_role NOT IN ('editor','admin') THEN
    RETURN jsonb_build_object('error','Sem permissão');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM public.pontos_luminaria WHERE id = p_ponto) THEN
    RETURN jsonb_build_object('error','Ponto não encontrado');
  END IF;
  INSERT INTO public.pontos_intervencoes (
    ponto_id, tipo, data, descricao, responsavel, tipo_lampada_nova, potencia_nova_w, registrado_por
  ) VALUES (
    p_ponto, p_tipo::intervencao_tipo, COALESCE(p_data::date, CURRENT_DATE),
    p_descricao, p_responsavel, NULLIF(p_lampada_nova,'')::tipo_lampada, p_potencia_nova,
    COALESCE((SELECT email FROM public.profiles WHERE id = v_user_id), v_user_id::text)
  );
  RETURN jsonb_build_object('success', true, 'message', 'Intervenção registrada');
END; $function$
;

CREATE OR REPLACE FUNCTION public.ip_remover_ponto(p_id uuid, p_motivo text DEFAULT NULL::text)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare
  v_user_id uuid;
  v_ponto jsonb;
  v_role text;
begin
  v_user_id := auth.uid();
  if v_user_id is null then
    return jsonb_build_object('error', 'Não autenticado');
  end if;

  select role into v_role from profiles where id = v_user_id;
  if v_role is null or v_role = 'leitura' then
    return jsonb_build_object('error', 'Sem permissão para remover ativos');
  end if;

  select to_jsonb(p.*) into v_ponto from v_parque_export p where id = p_id;
  if v_ponto is null then
    return jsonb_build_object('error', 'Ponto não encontrado');
  end if;

  -- Backup completo antes da exclusão (permite restauração futura)
  insert into ativos_removidos (ponto_id, dados_backup, removido_por, motivo)
  values (p_id, v_ponto, v_user_id, p_motivo);

  delete from v_parque_export where id = p_id;

  return jsonb_build_object('success', true, 'message', 'Ativo removido');
end;
$function$
;

CREATE OR REPLACE FUNCTION public.ip_serie_metricas()
 RETURNS json
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  SELECT coalesce(json_agg(json_build_object(
    'data',data,'pct_led',pct_led,'led',led,'pendente',pendente,'total',total
  ) ORDER BY data),'[]'::json) FROM metricas_diarias;
$function$
;

CREATE OR REPLACE FUNCTION public.ip_snapshot_metricas()
 RETURNS void
 LANGUAGE sql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  INSERT INTO metricas_diarias(data,total,led,led_censo,led_seconser,pendente,pct_led,potencia_kw_led,por_bairro)
  SELECT current_date, count(*),
    count(*) FILTER (WHERE modernizado_led),
    count(*) FILTER (WHERE modernizado_led AND fonte_modernizacao='censo_enel'),
    count(*) FILTER (WHERE modernizado_led AND fonte_modernizacao='seconser_pos_censo'),
    count(*) FILTER (WHERE NOT modernizado_led),
    round(100.0*count(*) FILTER (WHERE modernizado_led)/nullif(count(*),0),1),
    round((sum(potencia_w) FILTER (WHERE modernizado_led)/1000.0)::numeric,1),
    (SELECT jsonb_object_agg(bairro_nome, jsonb_build_object('t',t,'l',l)) FROM (
       SELECT bairro_nome, count(*) t, count(*) FILTER (WHERE modernizado_led) l
       FROM pontos_luminaria GROUP BY bairro_nome) s)
  FROM pontos_luminaria
  ON CONFLICT (data) DO UPDATE SET
    total=EXCLUDED.total, led=EXCLUDED.led, led_censo=EXCLUDED.led_censo,
    led_seconser=EXCLUDED.led_seconser, pendente=EXCLUDED.pendente,
    pct_led=EXCLUDED.pct_led, potencia_kw_led=EXCLUDED.potencia_kw_led,
    por_bairro=EXCLUDED.por_bairro, criado_em=now();
$function$
;

CREATE OR REPLACE FUNCTION public.ip_stats_poligono(p_geojson text)
 RETURNS json
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  WITH poly AS (SELECT ST_MakeValid(ST_SetSRID(ST_GeomFromGeoJSON(p_geojson), 4326)) AS g),
  ar AS (SELECT GREATEST(ST_Area(g::geography)/1e6, 0.000001) AS km2 FROM poly),
  sel AS (
    SELECT pl.* FROM pontos_luminaria pl, poly
    WHERE pl.geom && poly.g AND ST_Contains(poly.g, pl.geom)
  )
  SELECT json_build_object(
    'total',        (SELECT count(*) FROM sel),
    'area_km2',     (SELECT round(km2::numeric, 4) FROM ar),
    'densidade_km2',(SELECT round((count(*) / (SELECT km2 FROM ar))::numeric, 1) FROM sel),
    'led',          (SELECT count(*) FROM sel WHERE modernizado_led),
    'pendente',     (SELECT count(*) FROM sel WHERE NOT modernizado_led AND tipo_ativo = 'luminaria'),
    'pct_led',      (SELECT CASE WHEN count(*) FILTER (WHERE tipo_ativo='luminaria') > 0
                            THEN round(100.0 * count(*) FILTER (WHERE modernizado_led)
                                       / count(*) FILTER (WHERE tipo_ativo='luminaria'), 1)
                            ELSE 0 END FROM sel),
    'potencia_kw',  (SELECT round((coalesce(sum(potencia_w),0)/1000.0)::numeric, 1) FROM sel),
    'por_tipo_lampada', (SELECT coalesce(json_object_agg(tl, n), '{}'::json) FROM (
        SELECT coalesce(tipo_lampada::text,'—') tl, count(*) n FROM sel
        WHERE tipo_ativo='luminaria' GROUP BY 1 ORDER BY 2 DESC) x),
    'por_tipo_ativo', (SELECT coalesce(json_object_agg(ta, n), '{}'::json) FROM (
        SELECT tipo_ativo::text ta, count(*) n FROM sel GROUP BY 1 ORDER BY 2 DESC) x),
    'classificados_foto', (SELECT count(*) FROM sel
        WHERE angulo_inclinacao_graus IS NOT NULL AND material_piso IS NOT NULL),
    'aproveitamento_medio', (SELECT round(avg(GREATEST(0, cosd(angulo_inclinacao_graus)))::numeric, 3)
        FROM sel WHERE angulo_inclinacao_graus IS NOT NULL AND material_piso IS NOT NULL),
    'poluicao_media', (SELECT round(avg(LEAST(1,
          (1 - GREATEST(0, cosd(sel.angulo_inclinacao_graus)))
          + r.refletancia * GREATEST(0, cosd(sel.angulo_inclinacao_graus)) * 0.5))::numeric, 3)
        FROM sel JOIN ref_material_piso r ON r.material = sel.material_piso
        WHERE sel.angulo_inclinacao_graus IS NOT NULL)
  );
$function$
;

CREATE OR REPLACE FUNCTION public.is_admin()
 RETURNS boolean
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  SELECT EXISTS(SELECT 1 FROM public.profiles WHERE id=auth.uid() AND role='admin');
$function$
;

CREATE OR REPLACE FUNCTION public.log_ponto_hist()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
BEGIN
  INSERT INTO pontos_luminaria_historico(ponto_id, operacao, alterado_por, dados_antes, dados_depois)
  VALUES (
    coalesce(NEW.id, OLD.id), TG_OP, coalesce(auth.email(),'sistema'),
    CASE WHEN TG_OP IN ('UPDATE','DELETE') THEN to_jsonb(OLD) - 'geom' END,
    CASE WHEN TG_OP IN ('UPDATE','INSERT') THEN to_jsonb(NEW) - 'geom' END
  );
  RETURN NULL;
END $function$
;

CREATE OR REPLACE FUNCTION public.pode_escrever()
 RETURNS boolean
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  SELECT EXISTS(SELECT 1 FROM public.profiles WHERE id=auth.uid() AND role IN ('admin','editor'));
$function$
;

CREATE OR REPLACE FUNCTION public.set_atualizado_em()
 RETURNS trigger
 LANGUAGE plpgsql
 SET search_path TO 'public'
AS $function$
BEGIN NEW.atualizado_em = now(); RETURN NEW; END $function$
;

CREATE OR REPLACE FUNCTION public.update_health_status()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
  NEW.health_status := public.calc_health_status(
    EXTRACT(YEAR FROM AGE(NEW.data_instalacao))::integer,
    NEW.modernizado_led,
    NEW.potencia_w,
    NEW.flag_revisao_censo
  );
  RETURN NEW;
END;
$function$
;


-- ============================================================================
-- 12. TRIGGERS
-- ============================================================================

CREATE TRIGGER trg_atribuir_bairro_ponto BEFORE INSERT OR UPDATE OF geom ON public.pontos_luminaria FOR EACH ROW EXECUTE FUNCTION atribuir_bairro_ponto();
CREATE TRIGGER trg_atribuir_bairro_registro BEFORE INSERT OR UPDATE OF geom ON public.registros_iluminacao FOR EACH ROW EXECUTE FUNCTION atribuir_bairro_registro();
CREATE TRIGGER trg_atualizado_em BEFORE UPDATE ON public.pontos_luminaria FOR EACH ROW EXECUTE FUNCTION set_atualizado_em();
CREATE TRIGGER trg_log_ponto AFTER INSERT OR DELETE OR UPDATE ON public.pontos_luminaria FOR EACH ROW EXECUTE FUNCTION log_ponto_hist();
CREATE TRIGGER trg_pontos_atualizado_em BEFORE UPDATE ON public.pontos_luminaria FOR EACH ROW EXECUTE FUNCTION set_atualizado_em();
CREATE TRIGGER trg_registros_atualizado_em BEFORE UPDATE ON public.registros_iluminacao FOR EACH ROW EXECUTE FUNCTION set_atualizado_em();
CREATE TRIGGER trg_update_health_status BEFORE INSERT OR UPDATE ON public.pontos_luminaria FOR EACH ROW EXECUTE FUNCTION update_health_status();


-- ============================================================================
-- 13. CHAVES ESTRANGEIRAS (por ultimo: dependem das tabelas todas existirem)
-- ============================================================================

ALTER TABLE public.ativos_removidos ADD CONSTRAINT ativos_removidos_removido_por_fkey FOREIGN KEY (removido_por) REFERENCES auth.users(id) ON DELETE SET NULL;
ALTER TABLE public.ativos_removidos ADD CONSTRAINT ativos_removidos_restaurado_por_fkey FOREIGN KEY (restaurado_por) REFERENCES auth.users(id) ON DELETE SET NULL;
ALTER TABLE public.campanhas ADD CONSTRAINT campanhas_municipio_id_fkey FOREIGN KEY (municipio_id) REFERENCES municipios(id);
ALTER TABLE public.equipamentos_modelo ADD CONSTRAINT equipamentos_modelo_created_by_fkey FOREIGN KEY (created_by) REFERENCES auth.users(id);
ALTER TABLE public.lotes_substituicao ADD CONSTRAINT lotes_substituicao_registro_id_fkey FOREIGN KEY (registro_id) REFERENCES registros_iluminacao(id) ON DELETE CASCADE;
ALTER TABLE public.pontos_intervencoes ADD CONSTRAINT pontos_intervencoes_ponto_id_fkey FOREIGN KEY (ponto_id) REFERENCES pontos_luminaria(id) ON DELETE CASCADE;
ALTER TABLE public.pontos_luminaria ADD CONSTRAINT pontos_luminaria_bairro_id_fkey FOREIGN KEY (bairro_id) REFERENCES bairros_niteroi(id);
ALTER TABLE public.pontos_luminaria ADD CONSTRAINT pontos_luminaria_campanha_id_fkey FOREIGN KEY (campanha_id) REFERENCES campanhas(id);
ALTER TABLE public.pontos_luminaria ADD CONSTRAINT pontos_luminaria_material_piso_fkey FOREIGN KEY (material_piso) REFERENCES ref_material_piso(material);
ALTER TABLE public.pontos_luminaria ADD CONSTRAINT pontos_luminaria_municipio_id_fkey FOREIGN KEY (municipio_id) REFERENCES municipios(id);
ALTER TABLE public.pontos_luminaria ADD CONSTRAINT pontos_luminaria_registro_pai_id_fkey FOREIGN KEY (registro_pai_id) REFERENCES registros_iluminacao(id) ON DELETE SET NULL;
ALTER TABLE public.profiles ADD CONSTRAINT profiles_id_fkey FOREIGN KEY (id) REFERENCES auth.users(id) ON DELETE CASCADE;
ALTER TABLE public.registros_iluminacao ADD CONSTRAINT registros_iluminacao_bairro_id_fkey FOREIGN KEY (bairro_id) REFERENCES bairros_niteroi(id);


-- ============================================================================
-- 14. ROW LEVEL SECURITY
-- ============================================================================

ALTER TABLE public.ativos_removidos ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.bairros_niteroi ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.campanhas ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.comunidades_zeis ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.equipamentos_modelo ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ip_eficacia_luminosa ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.lotes_substituicao ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.metricas_diarias ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.municipios ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.painel_campos_disponveis ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.pontos_intervencoes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.pontos_luminaria ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.pontos_luminaria_historico ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ref_material_piso ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.registros_iluminacao ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.site_config ENABLE ROW LEVEL SECURITY;


-- ============================================================================
-- 15. POLICIES
-- ============================================================================

DROP POLICY IF EXISTS removidos_admin_all ON public.ativos_removidos;

CREATE POLICY removidos_admin_all ON public.ativos_removidos AS PERMISSIVE FOR ALL TO public
  USING ((EXISTS ( SELECT 1
   FROM profiles
  WHERE ((profiles.id = auth.uid()) AND (profiles.role = ANY (ARRAY['admin'::user_role, 'editor'::user_role]))))))
  WITH CHECK ((EXISTS ( SELECT 1
   FROM profiles
  WHERE ((profiles.id = auth.uid()) AND (profiles.role = ANY (ARRAY['admin'::user_role, 'editor'::user_role]))))));

DROP POLICY IF EXISTS removidos_user_own ON public.ativos_removidos;

CREATE POLICY removidos_user_own ON public.ativos_removidos AS PERMISSIVE FOR SELECT TO public
  USING ((removido_por = auth.uid()));

DROP POLICY IF EXISTS removidos_view ON public.ativos_removidos;

CREATE POLICY removidos_view ON public.ativos_removidos AS PERMISSIVE FOR SELECT TO public
  USING ((EXISTS ( SELECT 1
   FROM profiles
  WHERE ((profiles.id = auth.uid()) AND (profiles.role = ANY (ARRAY['admin'::user_role, 'editor'::user_role]))))));

DROP POLICY IF EXISTS "leitura publica" ON public.bairros_niteroi;

CREATE POLICY "leitura publica" ON public.bairros_niteroi AS PERMISSIVE FOR SELECT TO public
  USING (true);

DROP POLICY IF EXISTS campanhas_read ON public.campanhas;

CREATE POLICY campanhas_read ON public.campanhas AS PERMISSIVE FOR SELECT TO public
  USING (true);

DROP POLICY IF EXISTS comunidades_zeis_leitura_publica ON public.comunidades_zeis;

CREATE POLICY comunidades_zeis_leitura_publica ON public.comunidades_zeis AS PERMISSIVE FOR SELECT TO public
  USING (true);

DROP POLICY IF EXISTS modelos_deletable ON public.equipamentos_modelo;

CREATE POLICY modelos_deletable ON public.equipamentos_modelo AS PERMISSIVE FOR DELETE TO public
  USING ((EXISTS ( SELECT 1
   FROM profiles
  WHERE ((profiles.id = auth.uid()) AND (profiles.role = ANY (ARRAY['admin'::user_role, 'editor'::user_role]))))));

DROP POLICY IF EXISTS modelos_readable ON public.equipamentos_modelo;

CREATE POLICY modelos_readable ON public.equipamentos_modelo AS PERMISSIVE FOR SELECT TO public
  USING (true);

DROP POLICY IF EXISTS modelos_updatable ON public.equipamentos_modelo;

CREATE POLICY modelos_updatable ON public.equipamentos_modelo AS PERMISSIVE FOR UPDATE TO public
  USING ((EXISTS ( SELECT 1
   FROM profiles
  WHERE ((profiles.id = auth.uid()) AND (profiles.role = ANY (ARRAY['admin'::user_role, 'editor'::user_role]))))))
  WITH CHECK ((EXISTS ( SELECT 1
   FROM profiles
  WHERE ((profiles.id = auth.uid()) AND (profiles.role = ANY (ARRAY['admin'::user_role, 'editor'::user_role]))))));

DROP POLICY IF EXISTS modelos_writable ON public.equipamentos_modelo;

CREATE POLICY modelos_writable ON public.equipamentos_modelo AS PERMISSIVE FOR INSERT TO public
  WITH CHECK ((EXISTS ( SELECT 1
   FROM profiles
  WHERE ((profiles.id = auth.uid()) AND (profiles.role = ANY (ARRAY['admin'::user_role, 'editor'::user_role]))))));

DROP POLICY IF EXISTS eficacia_select ON public.ip_eficacia_luminosa;

CREATE POLICY eficacia_select ON public.ip_eficacia_luminosa AS PERMISSIVE FOR SELECT TO anon, authenticated
  USING (true);

DROP POLICY IF EXISTS "escrita autenticada" ON public.lotes_substituicao;

CREATE POLICY "escrita autenticada" ON public.lotes_substituicao AS PERMISSIVE FOR INSERT TO public
  WITH CHECK ((( SELECT auth.role() AS role) = 'authenticated'::text));

DROP POLICY IF EXISTS "leitura publica" ON public.lotes_substituicao;

CREATE POLICY "leitura publica" ON public.lotes_substituicao AS PERMISSIVE FOR SELECT TO public
  USING (true);

DROP POLICY IF EXISTS "metricas leitura publica" ON public.metricas_diarias;

CREATE POLICY "metricas leitura publica" ON public.metricas_diarias AS PERMISSIVE FOR SELECT TO public
  USING (true);

DROP POLICY IF EXISTS municipios_read ON public.municipios;

CREATE POLICY municipios_read ON public.municipios AS PERMISSIVE FOR SELECT TO public
  USING (true);

DROP POLICY IF EXISTS "interv leitura autenticada" ON public.pontos_intervencoes;

CREATE POLICY "interv leitura autenticada" ON public.pontos_intervencoes AS PERMISSIVE FOR SELECT TO authenticated
  USING (true);

DROP POLICY IF EXISTS "leitura publica" ON public.pontos_luminaria;

CREATE POLICY "leitura publica" ON public.pontos_luminaria AS PERMISSIVE FOR SELECT TO public
  USING (true);

DROP POLICY IF EXISTS pontos_delete ON public.pontos_luminaria;

CREATE POLICY pontos_delete ON public.pontos_luminaria AS PERMISSIVE FOR DELETE TO public
  USING ((EXISTS ( SELECT 1
   FROM profiles
  WHERE ((profiles.id = auth.uid()) AND (profiles.role = ANY (ARRAY['admin'::user_role, 'editor'::user_role]))))));

DROP POLICY IF EXISTS pontos_insert ON public.pontos_luminaria;

CREATE POLICY pontos_insert ON public.pontos_luminaria AS PERMISSIVE FOR INSERT TO public
  WITH CHECK ((EXISTS ( SELECT 1
   FROM profiles
  WHERE ((profiles.id = auth.uid()) AND (profiles.role = ANY (ARRAY['admin'::user_role, 'editor'::user_role]))))));

DROP POLICY IF EXISTS pontos_update ON public.pontos_luminaria;

CREATE POLICY pontos_update ON public.pontos_luminaria AS PERMISSIVE FOR UPDATE TO public
  USING ((EXISTS ( SELECT 1
   FROM profiles
  WHERE ((profiles.id = auth.uid()) AND (profiles.role = ANY (ARRAY['admin'::user_role, 'editor'::user_role]))))));

DROP POLICY IF EXISTS "hist leitura autenticada" ON public.pontos_luminaria_historico;

CREATE POLICY "hist leitura autenticada" ON public.pontos_luminaria_historico AS PERMISSIVE FOR SELECT TO authenticated
  USING (true);

DROP POLICY IF EXISTS "admin atualiza" ON public.profiles;

CREATE POLICY "admin atualiza" ON public.profiles AS PERMISSIVE FOR UPDATE TO authenticated
  USING (is_admin())
  WITH CHECK (is_admin());

DROP POLICY IF EXISTS "admin insere" ON public.profiles;

CREATE POLICY "admin insere" ON public.profiles AS PERMISSIVE FOR INSERT TO authenticated
  WITH CHECK (is_admin());

DROP POLICY IF EXISTS "admin le todos" ON public.profiles;

CREATE POLICY "admin le todos" ON public.profiles AS PERMISSIVE FOR SELECT TO authenticated
  USING (is_admin());

DROP POLICY IF EXISTS "admin remove" ON public.profiles;

CREATE POLICY "admin remove" ON public.profiles AS PERMISSIVE FOR DELETE TO authenticated
  USING (is_admin());

DROP POLICY IF EXISTS "perfil proprio leitura" ON public.profiles;

CREATE POLICY "perfil proprio leitura" ON public.profiles AS PERMISSIVE FOR SELECT TO authenticated
  USING ((id = auth.uid()));

DROP POLICY IF EXISTS ref_material_piso_read ON public.ref_material_piso;

CREATE POLICY ref_material_piso_read ON public.ref_material_piso AS PERMISSIVE FOR SELECT TO public
  USING (true);

DROP POLICY IF EXISTS "atualizacao autenticada" ON public.registros_iluminacao;

CREATE POLICY "atualizacao autenticada" ON public.registros_iluminacao AS PERMISSIVE FOR UPDATE TO public
  USING ((( SELECT auth.role() AS role) = 'authenticated'::text));

DROP POLICY IF EXISTS "escrita autenticada" ON public.registros_iluminacao;

CREATE POLICY "escrita autenticada" ON public.registros_iluminacao AS PERMISSIVE FOR INSERT TO public
  WITH CHECK ((( SELECT auth.role() AS role) = 'authenticated'::text));

DROP POLICY IF EXISTS "leitura publica" ON public.registros_iluminacao;

CREATE POLICY "leitura publica" ON public.registros_iluminacao AS PERMISSIVE FOR SELECT TO public
  USING (true);

DROP POLICY IF EXISTS admin_update_painel_config ON public.site_config;

CREATE POLICY admin_update_painel_config ON public.site_config AS PERMISSIVE FOR UPDATE TO public
  USING ((EXISTS ( SELECT 1
   FROM profiles
  WHERE ((profiles.id = auth.uid()) AND (profiles.role = ANY (ARRAY['admin'::user_role, 'editor'::user_role]))))))
  WITH CHECK ((EXISTS ( SELECT 1
   FROM profiles
  WHERE ((profiles.id = auth.uid()) AND (profiles.role = ANY (ARRAY['admin'::user_role, 'editor'::user_role]))))));

DROP POLICY IF EXISTS "config admin escreve" ON public.site_config;

CREATE POLICY "config admin escreve" ON public.site_config AS PERMISSIVE FOR UPDATE TO public
  USING ((EXISTS ( SELECT 1
   FROM profiles
  WHERE ((profiles.id = auth.uid()) AND (profiles.role = ANY (ARRAY['admin'::user_role, 'editor'::user_role]))))));

DROP POLICY IF EXISTS "config leitura publica" ON public.site_config;

CREATE POLICY "config leitura publica" ON public.site_config AS PERMISSIVE FOR SELECT TO public
  USING (true);


-- ============================================================================
-- 16. GRANTS — TABELAS
-- ============================================================================

GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.ativos_removidos TO anon;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.ativos_removidos TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.ativos_removidos TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.bairros_niteroi TO anon;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.bairros_niteroi TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.bairros_niteroi TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.campanhas TO anon;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.campanhas TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.campanhas TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.comunidades_zeis TO anon;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.comunidades_zeis TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.comunidades_zeis TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.equipamentos_modelo TO anon;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.equipamentos_modelo TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.equipamentos_modelo TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.geography_columns TO anon;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.geography_columns TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.geography_columns TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.geometry_columns TO anon;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.geometry_columns TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.geometry_columns TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.ip_eficacia_luminosa TO anon;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.ip_eficacia_luminosa TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.ip_eficacia_luminosa TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.lotes_substituicao TO anon;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.lotes_substituicao TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.lotes_substituicao TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.metricas_diarias TO anon;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.metricas_diarias TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.metricas_diarias TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.municipios TO anon;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.municipios TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.municipios TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.painel_campos_disponveis TO anon;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.painel_campos_disponveis TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.painel_campos_disponveis TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.pontos_intervencoes TO anon;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.pontos_intervencoes TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.pontos_intervencoes TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.pontos_luminaria TO anon;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.pontos_luminaria TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.pontos_luminaria TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.pontos_luminaria_historico TO anon;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.pontos_luminaria_historico TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.pontos_luminaria_historico TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.profiles TO anon;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.profiles TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.profiles TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.ref_material_piso TO anon;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.ref_material_piso TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.ref_material_piso TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.registros_iluminacao TO anon;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.registros_iluminacao TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.registros_iluminacao TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.site_config TO anon;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.site_config TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.site_config TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.v_parque_export TO anon;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.v_parque_export TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.v_parque_export TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.vw_mapa_pontos TO anon;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.vw_mapa_pontos TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.vw_mapa_pontos TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.vw_mapa_registros TO anon;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.vw_mapa_registros TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.vw_mapa_registros TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.vw_totais_por_registro TO anon;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.vw_totais_por_registro TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.vw_totais_por_registro TO service_role;


-- ============================================================================
-- 17. GRANTS — FUNCOES
-- ============================================================================

GRANT EXECUTE ON FUNCTION public.atribuir_bairro_ponto() TO anon;
GRANT EXECUTE ON FUNCTION public.atribuir_bairro_ponto() TO authenticated;
GRANT EXECUTE ON FUNCTION public.atribuir_bairro_ponto() TO service_role;
GRANT EXECUTE ON FUNCTION public.atribuir_bairro_registro() TO anon;
GRANT EXECUTE ON FUNCTION public.atribuir_bairro_registro() TO authenticated;
GRANT EXECUTE ON FUNCTION public.atribuir_bairro_registro() TO service_role;
GRANT EXECUTE ON FUNCTION public.calc_health_status(p_idade_anos integer, p_modernizado_led boolean, p_potencia_w integer, p_flag_revisao boolean) TO anon;
GRANT EXECUTE ON FUNCTION public.calc_health_status(p_idade_anos integer, p_modernizado_led boolean, p_potencia_w integer, p_flag_revisao boolean) TO authenticated;
GRANT EXECUTE ON FUNCTION public.calc_health_status(p_idade_anos integer, p_modernizado_led boolean, p_potencia_w integer, p_flag_revisao boolean) TO service_role;
GRANT EXECUTE ON FUNCTION public.handle_new_user() TO anon;
GRANT EXECUTE ON FUNCTION public.handle_new_user() TO authenticated;
GRANT EXECUTE ON FUNCTION public.handle_new_user() TO service_role;
GRANT EXECUTE ON FUNCTION public.ip_atualizar_modelo(p_id uuid, p_fabricante text, p_modelo text, p_potencia_w integer, p_temperatura_cor_k integer, p_tensao text, p_ip text, p_classe_nbr text, p_tecnologia text, p_tipo_luminaria text, p_tipo_lampada text, p_foto_url text, p_descricao text, p_fluxo_luminoso_lm integer, p_eficacia_luminosa_lm_w numeric, p_fator_potencia_fp numeric, p_thd_percentual numeric, p_grau_ik text, p_dps_especificacao text, p_tipo_conectividade text, p_arquivo_ies_url text, p_inmetro_registro text, p_vida_util_anos integer, p_garantia_anos integer, p_dias_manutencao_preventiva integer) TO authenticated;
GRANT EXECUTE ON FUNCTION public.ip_atualizar_modelo(p_id uuid, p_fabricante text, p_modelo text, p_potencia_w integer, p_temperatura_cor_k integer, p_tensao text, p_ip text, p_classe_nbr text, p_tecnologia text, p_tipo_luminaria text, p_tipo_lampada text, p_foto_url text, p_descricao text, p_fluxo_luminoso_lm integer, p_eficacia_luminosa_lm_w numeric, p_fator_potencia_fp numeric, p_thd_percentual numeric, p_grau_ik text, p_dps_especificacao text, p_tipo_conectividade text, p_arquivo_ies_url text, p_inmetro_registro text, p_vida_util_anos integer, p_garantia_anos integer, p_dias_manutencao_preventiva integer) TO service_role;
GRANT EXECUTE ON FUNCTION public.ip_atualizar_painel_config(p_design text, p_campos jsonb) TO anon;
GRANT EXECUTE ON FUNCTION public.ip_atualizar_painel_config(p_design text, p_campos jsonb) TO authenticated;
GRANT EXECUTE ON FUNCTION public.ip_atualizar_painel_config(p_design text, p_campos jsonb) TO service_role;
GRANT EXECUTE ON FUNCTION public.ip_atualizar_ponto(p_id uuid, p_tipo text, p_potencia integer, p_status text, p_modernizado boolean, p_obs text, p_lat numeric, p_lng numeric, p_tipo_luminaria text, p_classe_nbr text, p_angulo integer, p_material text) TO anon;
GRANT EXECUTE ON FUNCTION public.ip_atualizar_ponto(p_id uuid, p_tipo text, p_potencia integer, p_status text, p_modernizado boolean, p_obs text, p_lat numeric, p_lng numeric, p_tipo_luminaria text, p_classe_nbr text, p_angulo integer, p_material text) TO authenticated;
GRANT EXECUTE ON FUNCTION public.ip_atualizar_ponto(p_id uuid, p_tipo text, p_potencia integer, p_status text, p_modernizado boolean, p_obs text, p_lat numeric, p_lng numeric, p_tipo_luminaria text, p_classe_nbr text, p_angulo integer, p_material text) TO service_role;
GRANT EXECUTE ON FUNCTION public.ip_bairro_geojson(p_bairro text) TO anon;
GRANT EXECUTE ON FUNCTION public.ip_bairro_geojson(p_bairro text) TO authenticated;
GRANT EXECUTE ON FUNCTION public.ip_bairro_geojson(p_bairro text) TO service_role;
GRANT EXECUTE ON FUNCTION public.ip_bairros_choropleth() TO anon;
GRANT EXECUTE ON FUNCTION public.ip_bairros_choropleth() TO authenticated;
GRANT EXECUTE ON FUNCTION public.ip_bairros_choropleth() TO service_role;
GRANT EXECUTE ON FUNCTION public.ip_clusters_grid(min_lng double precision, min_lat double precision, max_lng double precision, max_lat double precision, grid_deg double precision, p_bairro text, p_tipo text, p_modernizado boolean, p_pot_min integer, p_revisao boolean, p_fonte_mod text, p_suspeito boolean, p_led_min integer, p_led_max integer, p_power_min integer, p_power_max integer, p_data_inicio date, p_data_fim date, p_health_status text, p_nao_verificado boolean) TO anon;
GRANT EXECUTE ON FUNCTION public.ip_clusters_grid(min_lng double precision, min_lat double precision, max_lng double precision, max_lat double precision, grid_deg double precision, p_bairro text, p_tipo text, p_modernizado boolean, p_pot_min integer, p_revisao boolean, p_fonte_mod text, p_suspeito boolean, p_led_min integer, p_led_max integer, p_power_min integer, p_power_max integer, p_data_inicio date, p_data_fim date, p_health_status text, p_nao_verificado boolean) TO authenticated;
GRANT EXECUTE ON FUNCTION public.ip_clusters_grid(min_lng double precision, min_lat double precision, max_lng double precision, max_lat double precision, grid_deg double precision, p_bairro text, p_tipo text, p_modernizado boolean, p_pot_min integer, p_revisao boolean, p_fonte_mod text, p_suspeito boolean, p_led_min integer, p_led_max integer, p_power_min integer, p_power_max integer, p_data_inicio date, p_data_fim date, p_health_status text, p_nao_verificado boolean) TO service_role;
GRANT EXECUTE ON FUNCTION public.ip_comunidade_geom(p_nome text) TO anon;
GRANT EXECUTE ON FUNCTION public.ip_comunidade_geom(p_nome text) TO authenticated;
GRANT EXECUTE ON FUNCTION public.ip_comunidade_geom(p_nome text) TO service_role;
GRANT EXECUTE ON FUNCTION public.ip_comunidades_lista() TO anon;
GRANT EXECUTE ON FUNCTION public.ip_comunidades_lista() TO authenticated;
GRANT EXECUTE ON FUNCTION public.ip_comunidades_lista() TO service_role;
GRANT EXECUTE ON FUNCTION public.ip_confirmar_ponto(p_id uuid) TO authenticated;
GRANT EXECUTE ON FUNCTION public.ip_confirmar_ponto(p_id uuid) TO service_role;
GRANT EXECUTE ON FUNCTION public.ip_criar_campanha(p_nome text, p_descricao text) TO authenticated;
GRANT EXECUTE ON FUNCTION public.ip_criar_campanha(p_nome text, p_descricao text) TO service_role;
GRANT EXECUTE ON FUNCTION public.ip_criar_modelo(p_fabricante text, p_modelo text, p_potencia_w integer, p_temperatura_cor_k integer, p_tensao text, p_ip text, p_classe_nbr text, p_tecnologia text, p_tipo_luminaria text, p_tipo_lampada text, p_foto_url text, p_descricao text, p_fluxo_luminoso_lm integer, p_eficacia_luminosa_lm_w numeric, p_fator_potencia_fp numeric, p_thd_percentual numeric, p_grau_ik text, p_dps_especificacao text, p_tipo_conectividade text, p_arquivo_ies_url text, p_inmetro_registro text, p_vida_util_anos integer, p_garantia_anos integer, p_dias_manutencao_preventiva integer) TO authenticated;
GRANT EXECUTE ON FUNCTION public.ip_criar_modelo(p_fabricante text, p_modelo text, p_potencia_w integer, p_temperatura_cor_k integer, p_tensao text, p_ip text, p_classe_nbr text, p_tecnologia text, p_tipo_luminaria text, p_tipo_lampada text, p_foto_url text, p_descricao text, p_fluxo_luminoso_lm integer, p_eficacia_luminosa_lm_w numeric, p_fator_potencia_fp numeric, p_thd_percentual numeric, p_grau_ik text, p_dps_especificacao text, p_tipo_conectividade text, p_arquivo_ies_url text, p_inmetro_registro text, p_vida_util_anos integer, p_garantia_anos integer, p_dias_manutencao_preventiva integer) TO service_role;
GRANT EXECUTE ON FUNCTION public.ip_deletar_modelo(p_id uuid) TO authenticated;
GRANT EXECUTE ON FUNCTION public.ip_deletar_modelo(p_id uuid) TO service_role;
GRANT EXECUTE ON FUNCTION public.ip_encerrar_campanha(p_id uuid) TO authenticated;
GRANT EXECUTE ON FUNCTION public.ip_encerrar_campanha(p_id uuid) TO service_role;
GRANT EXECUTE ON FUNCTION public.ip_estatisticas(p_bairro text) TO anon;
GRANT EXECUTE ON FUNCTION public.ip_estatisticas(p_bairro text) TO authenticated;
GRANT EXECUTE ON FUNCTION public.ip_estatisticas(p_bairro text) TO service_role;
GRANT EXECUTE ON FUNCTION public.ip_estatisticas_gerais() TO anon;
GRANT EXECUTE ON FUNCTION public.ip_estatisticas_gerais() TO authenticated;
GRANT EXECUTE ON FUNCTION public.ip_estatisticas_gerais() TO service_role;
GRANT EXECUTE ON FUNCTION public.ip_gera_codigo(p_tipo ativo_tipo) TO authenticated;
GRANT EXECUTE ON FUNCTION public.ip_gera_codigo(p_tipo ativo_tipo) TO service_role;
GRANT EXECUTE ON FUNCTION public.ip_grid_densidade(p_cell_m integer) TO anon;
GRANT EXECUTE ON FUNCTION public.ip_grid_densidade(p_cell_m integer) TO authenticated;
GRANT EXECUTE ON FUNCTION public.ip_grid_densidade(p_cell_m integer) TO service_role;
GRANT EXECUTE ON FUNCTION public.ip_grid_densidade_completo(p_cell_m integer) TO anon;
GRANT EXECUTE ON FUNCTION public.ip_grid_densidade_completo(p_cell_m integer) TO authenticated;
GRANT EXECUTE ON FUNCTION public.ip_grid_densidade_completo(p_cell_m integer) TO service_role;
GRANT EXECUTE ON FUNCTION public.ip_grid_densidade_json(p_cell_m integer) TO anon;
GRANT EXECUTE ON FUNCTION public.ip_grid_densidade_json(p_cell_m integer) TO authenticated;
GRANT EXECUTE ON FUNCTION public.ip_grid_densidade_json(p_cell_m integer) TO service_role;
GRANT EXECUTE ON FUNCTION public.ip_health_status_summary(min_lng double precision, min_lat double precision, max_lng double precision, max_lat double precision) TO anon;
GRANT EXECUTE ON FUNCTION public.ip_health_status_summary(min_lng double precision, min_lat double precision, max_lng double precision, max_lat double precision) TO authenticated;
GRANT EXECUTE ON FUNCTION public.ip_health_status_summary(min_lng double precision, min_lat double precision, max_lng double precision, max_lat double precision) TO service_role;
GRANT EXECUTE ON FUNCTION public.ip_historico_ponto(p_id uuid) TO anon;
GRANT EXECUTE ON FUNCTION public.ip_historico_ponto(p_id uuid) TO authenticated;
GRANT EXECUTE ON FUNCTION public.ip_historico_ponto(p_id uuid) TO service_role;
GRANT EXECUTE ON FUNCTION public.ip_inserir_ponto(p_lat numeric, p_lng numeric, p_tipo text, p_potencia integer, p_status text, p_modernizado boolean, p_endereco text, p_patrimonio text, p_obs text, p_tipo_ativo text, p_tipo_luminaria text, p_classe_nbr text, p_angulo integer, p_material text) TO anon;
GRANT EXECUTE ON FUNCTION public.ip_inserir_ponto(p_lat numeric, p_lng numeric, p_tipo text, p_potencia integer, p_status text, p_modernizado boolean, p_endereco text, p_patrimonio text, p_obs text, p_tipo_ativo text, p_tipo_luminaria text, p_classe_nbr text, p_angulo integer, p_material text) TO authenticated;
GRANT EXECUTE ON FUNCTION public.ip_inserir_ponto(p_lat numeric, p_lng numeric, p_tipo text, p_potencia integer, p_status text, p_modernizado boolean, p_endereco text, p_patrimonio text, p_obs text, p_tipo_ativo text, p_tipo_luminaria text, p_classe_nbr text, p_angulo integer, p_material text) TO service_role;
GRANT EXECUTE ON FUNCTION public.ip_intervencoes(p_id uuid) TO anon;
GRANT EXECUTE ON FUNCTION public.ip_intervencoes(p_id uuid) TO authenticated;
GRANT EXECUTE ON FUNCTION public.ip_intervencoes(p_id uuid) TO service_role;
GRANT EXECUTE ON FUNCTION public.ip_listar_campanhas() TO anon;
GRANT EXECUTE ON FUNCTION public.ip_listar_campanhas() TO authenticated;
GRANT EXECUTE ON FUNCTION public.ip_listar_campanhas() TO service_role;
GRANT EXECUTE ON FUNCTION public.ip_listar_campos_disponveis() TO anon;
GRANT EXECUTE ON FUNCTION public.ip_listar_campos_disponveis() TO authenticated;
GRANT EXECUTE ON FUNCTION public.ip_listar_campos_disponveis() TO service_role;
GRANT EXECUTE ON FUNCTION public.ip_listar_modelos() TO anon;
GRANT EXECUTE ON FUNCTION public.ip_listar_modelos() TO authenticated;
GRANT EXECUTE ON FUNCTION public.ip_listar_modelos() TO service_role;
GRANT EXECUTE ON FUNCTION public.ip_obter_painel_config() TO anon;
GRANT EXECUTE ON FUNCTION public.ip_obter_painel_config() TO authenticated;
GRANT EXECUTE ON FUNCTION public.ip_obter_painel_config() TO service_role;
GRANT EXECUTE ON FUNCTION public.ip_pontos_bbox(min_lng double precision, min_lat double precision, max_lng double precision, max_lat double precision, limite integer, p_bairro text, p_tipo text, p_modernizado boolean, p_pot_min integer, p_revisao boolean, p_fonte_mod text, p_suspeito boolean, p_led_min integer, p_led_max integer, p_power_min integer, p_power_max integer, p_data_inicio date, p_data_fim date, p_health_status text, p_nao_verificado boolean) TO anon;
GRANT EXECUTE ON FUNCTION public.ip_pontos_bbox(min_lng double precision, min_lat double precision, max_lng double precision, max_lat double precision, limite integer, p_bairro text, p_tipo text, p_modernizado boolean, p_pot_min integer, p_revisao boolean, p_fonte_mod text, p_suspeito boolean, p_led_min integer, p_led_max integer, p_power_min integer, p_power_max integer, p_data_inicio date, p_data_fim date, p_health_status text, p_nao_verificado boolean) TO authenticated;
GRANT EXECUTE ON FUNCTION public.ip_pontos_bbox(min_lng double precision, min_lat double precision, max_lng double precision, max_lat double precision, limite integer, p_bairro text, p_tipo text, p_modernizado boolean, p_pot_min integer, p_revisao boolean, p_fonte_mod text, p_suspeito boolean, p_led_min integer, p_led_max integer, p_power_min integer, p_power_max integer, p_data_inicio date, p_data_fim date, p_health_status text, p_nao_verificado boolean) TO service_role;
GRANT EXECUTE ON FUNCTION public.ip_pontos_poligono(p_geojson text, limite integer) TO anon;
GRANT EXECUTE ON FUNCTION public.ip_pontos_poligono(p_geojson text, limite integer) TO authenticated;
GRANT EXECUTE ON FUNCTION public.ip_pontos_poligono(p_geojson text, limite integer) TO service_role;
GRANT EXECUTE ON FUNCTION public.ip_por_bairro() TO anon;
GRANT EXECUTE ON FUNCTION public.ip_por_bairro() TO authenticated;
GRANT EXECUTE ON FUNCTION public.ip_por_bairro() TO service_role;
GRANT EXECUTE ON FUNCTION public.ip_qualidade_dado() TO anon;
GRANT EXECUTE ON FUNCTION public.ip_qualidade_dado() TO authenticated;
GRANT EXECUTE ON FUNCTION public.ip_qualidade_dado() TO service_role;
GRANT EXECUTE ON FUNCTION public.ip_registrar_intervencao(p_ponto uuid, p_tipo text, p_data text, p_descricao text, p_responsavel text, p_lampada_nova text, p_potencia_nova integer) TO anon;
GRANT EXECUTE ON FUNCTION public.ip_registrar_intervencao(p_ponto uuid, p_tipo text, p_data text, p_descricao text, p_responsavel text, p_lampada_nova text, p_potencia_nova integer) TO authenticated;
GRANT EXECUTE ON FUNCTION public.ip_registrar_intervencao(p_ponto uuid, p_tipo text, p_data text, p_descricao text, p_responsavel text, p_lampada_nova text, p_potencia_nova integer) TO service_role;
GRANT EXECUTE ON FUNCTION public.ip_remover_ponto(p_id uuid, p_motivo text) TO authenticated;
GRANT EXECUTE ON FUNCTION public.ip_remover_ponto(p_id uuid, p_motivo text) TO service_role;
GRANT EXECUTE ON FUNCTION public.ip_serie_metricas() TO anon;
GRANT EXECUTE ON FUNCTION public.ip_serie_metricas() TO authenticated;
GRANT EXECUTE ON FUNCTION public.ip_serie_metricas() TO service_role;
GRANT EXECUTE ON FUNCTION public.ip_snapshot_metricas() TO authenticated;
GRANT EXECUTE ON FUNCTION public.ip_snapshot_metricas() TO service_role;
GRANT EXECUTE ON FUNCTION public.ip_stats_poligono(p_geojson text) TO anon;
GRANT EXECUTE ON FUNCTION public.ip_stats_poligono(p_geojson text) TO authenticated;
GRANT EXECUTE ON FUNCTION public.ip_stats_poligono(p_geojson text) TO service_role;
GRANT EXECUTE ON FUNCTION public.is_admin() TO anon;
GRANT EXECUTE ON FUNCTION public.is_admin() TO authenticated;
GRANT EXECUTE ON FUNCTION public.is_admin() TO service_role;
GRANT EXECUTE ON FUNCTION public.log_ponto_hist() TO anon;
GRANT EXECUTE ON FUNCTION public.log_ponto_hist() TO authenticated;
GRANT EXECUTE ON FUNCTION public.log_ponto_hist() TO service_role;
GRANT EXECUTE ON FUNCTION public.pode_escrever() TO anon;
GRANT EXECUTE ON FUNCTION public.pode_escrever() TO authenticated;
GRANT EXECUTE ON FUNCTION public.pode_escrever() TO service_role;
GRANT EXECUTE ON FUNCTION public.set_atualizado_em() TO anon;
GRANT EXECUTE ON FUNCTION public.set_atualizado_em() TO authenticated;
GRANT EXECUTE ON FUNCTION public.set_atualizado_em() TO service_role;
GRANT EXECUTE ON FUNCTION public.update_health_status() TO anon;
GRANT EXECUTE ON FUNCTION public.update_health_status() TO authenticated;
GRANT EXECUTE ON FUNCTION public.update_health_status() TO service_role;


-- ============================================================================
-- 18. STORAGE — BUCKETS
-- ============================================================================

INSERT INTO storage.buckets (id, name, public, file_size_limit) VALUES ('branding', 'branding', true, NULL) ON CONFLICT (id) DO NOTHING;
INSERT INTO storage.buckets (id, name, public, file_size_limit) VALUES ('equipamentos-fotos', 'equipamentos-fotos', true, NULL) ON CONFLICT (id) DO NOTHING;
INSERT INTO storage.buckets (id, name, public, file_size_limit) VALUES ('luminarias-fotos', 'luminarias-fotos', true, 5242880) ON CONFLICT (id) DO NOTHING;
INSERT INTO storage.buckets (id, name, public, file_size_limit) VALUES ('luminarias-ies', 'luminarias-ies', true, 5242880) ON CONFLICT (id) DO NOTHING;


-- ============================================================================
-- 19. STORAGE — POLICIES
-- ============================================================================

DROP POLICY IF EXISTS "Authenticated can delete equipment photos" ON storage.objects;

CREATE POLICY "Authenticated can delete equipment photos" ON storage.objects AS PERMISSIVE FOR DELETE TO public
  USING (((bucket_id = 'equipamentos-fotos'::text) AND (auth.role() = 'authenticated'::text)));

DROP POLICY IF EXISTS "Authenticated users can upload equipment photos" ON storage.objects;

CREATE POLICY "Authenticated users can upload equipment photos" ON storage.objects AS PERMISSIVE FOR INSERT TO public
  WITH CHECK (((bucket_id = 'equipamentos-fotos'::text) AND (auth.role() = 'authenticated'::text)));

DROP POLICY IF EXISTS "Public can read equipment photos" ON storage.objects;

CREATE POLICY "Public can read equipment photos" ON storage.objects AS PERMISSIVE FOR SELECT TO public
  USING ((bucket_id = 'equipamentos-fotos'::text));

DROP POLICY IF EXISTS "branding admin atualiza" ON storage.objects;

CREATE POLICY "branding admin atualiza" ON storage.objects AS PERMISSIVE FOR UPDATE TO authenticated
  USING (((bucket_id = 'branding'::text) AND is_admin()));

DROP POLICY IF EXISTS "branding admin insere" ON storage.objects;

CREATE POLICY "branding admin insere" ON storage.objects AS PERMISSIVE FOR INSERT TO authenticated
  WITH CHECK (((bucket_id = 'branding'::text) AND is_admin()));

DROP POLICY IF EXISTS "branding admin remove" ON storage.objects;

CREATE POLICY "branding admin remove" ON storage.objects AS PERMISSIVE FOR DELETE TO authenticated
  USING (((bucket_id = 'branding'::text) AND is_admin()));

DROP POLICY IF EXISTS "branding leitura publica" ON storage.objects;

CREATE POLICY "branding leitura publica" ON storage.objects AS PERMISSIVE FOR SELECT TO public
  USING ((bucket_id = 'branding'::text));

DROP POLICY IF EXISTS "luminarias admin remove" ON storage.objects;

CREATE POLICY "luminarias admin remove" ON storage.objects AS PERMISSIVE FOR DELETE TO public
  USING (((bucket_id = ANY (ARRAY['luminarias-fotos'::text, 'luminarias-ies'::text])) AND is_admin()));

DROP POLICY IF EXISTS "luminarias editor atualiza" ON storage.objects;

CREATE POLICY "luminarias editor atualiza" ON storage.objects AS PERMISSIVE FOR UPDATE TO public
  USING (((bucket_id = ANY (ARRAY['luminarias-fotos'::text, 'luminarias-ies'::text])) AND (EXISTS ( SELECT 1
   FROM profiles
  WHERE ((profiles.id = auth.uid()) AND (profiles.role = ANY (ARRAY['admin'::user_role, 'editor'::user_role])))))));

DROP POLICY IF EXISTS "luminarias editor insere" ON storage.objects;

CREATE POLICY "luminarias editor insere" ON storage.objects AS PERMISSIVE FOR INSERT TO public
  WITH CHECK (((bucket_id = ANY (ARRAY['luminarias-fotos'::text, 'luminarias-ies'::text])) AND (EXISTS ( SELECT 1
   FROM profiles
  WHERE ((profiles.id = auth.uid()) AND (profiles.role = ANY (ARRAY['admin'::user_role, 'editor'::user_role])))))));

DROP POLICY IF EXISTS "luminarias leitura publica" ON storage.objects;

CREATE POLICY "luminarias leitura publica" ON storage.objects AS PERMISSIVE FOR SELECT TO public
  USING ((bucket_id = ANY (ARRAY['luminarias-fotos'::text, 'luminarias-ies'::text])));
