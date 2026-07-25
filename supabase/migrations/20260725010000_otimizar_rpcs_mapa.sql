-- Otimiza as duas RPCs mais custosas do mapa: ip_clusters_grid e ip_pontos_bbox.
--
-- Motivacao (medido em producao via pg_stat_statements):
--   ip_clusters_grid  25.561 chamadas · media 422 ms · max 2.970 ms · 3.761 s acumulados
--   ip_pontos_bbox     1.661 chamadas · media 102 ms · max 2.739 ms
-- O role anon tinha statement_timeout=3s, e o max colava no teto: sob a concorrencia
-- do carregamento inicial (8 RPCs simultaneas) alguma chamada era cancelada e o
-- usuario via "Erro ao carregar: canceling statement due to statement timeout".
--
-- Duas causas, ambas tratadas aqui:
--
-- 1) LANGUAGE sql faz a funcao ser INLINED na query externa. Com 20 parametros e 16
--    clausulas (p_X IS NULL OR ...), o planejamento custava ~185 ms A CADA CHAMADA
--    (medido: Planning Time 185 ms vs Execution Time 45 ms). Em plpgsql a funcao nao
--    e inlined: o plano vai para o cache da sessao e, como o PostgREST mantem pool de
--    conexoes, e reaproveitado entre requisicoes.
--
-- 2) GROUP BY ST_SnapToGrid(geom, grid_deg) criava uma geometria nova por linha
--    (42.764 alocacoes) e fazia hash de geometry. Extrair ST_X/ST_Y uma vez e agrupar
--    por dois numeros e equivalente: ST_SnapToGrid arredonda para o multiplo mais
--    proximo, exatamente o que round(coord/grid_deg) faz. A chave de agrupamento nao
--    e retornada, so as medias e contagens — a saida e identica.
--
-- Medicao de ip_clusters_grid (bbox do municipio, grid 0.01): 180 ms -> 79 ms (2,3x).
-- Equivalencia conferida: 141 celulas e 42.764 pontos antes e depois.
--
-- IMPORTANTE: as assinaturas sao mantidas caractere por caractere. Alterar a lista de
-- parametros criaria uma sobrecarga nova em vez de substituir a funcao — foi assim que
-- surgiram as variantes ambiguas que derrubaram a producao (PGRST202/203).

CREATE OR REPLACE FUNCTION public.ip_clusters_grid(
  min_lng double precision, min_lat double precision, max_lng double precision, max_lat double precision,
  grid_deg double precision,
  p_bairro text DEFAULT NULL::text, p_tipo text DEFAULT NULL::text, p_modernizado boolean DEFAULT NULL::boolean,
  p_pot_min integer DEFAULT NULL::integer, p_revisao boolean DEFAULT NULL::boolean, p_fonte_mod text DEFAULT NULL::text,
  p_suspeito boolean DEFAULT NULL::boolean, p_led_min integer DEFAULT NULL::integer, p_led_max integer DEFAULT NULL::integer,
  p_power_min integer DEFAULT NULL::integer, p_power_max integer DEFAULT NULL::integer,
  p_data_inicio date DEFAULT NULL::date, p_data_fim date DEFAULT NULL::date,
  p_health_status text DEFAULT NULL::text, p_nao_verificado boolean DEFAULT NULL::boolean)
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
$function$;

CREATE OR REPLACE FUNCTION public.ip_pontos_bbox(
  min_lng double precision, min_lat double precision, max_lng double precision, max_lat double precision,
  limite integer DEFAULT 4000,
  p_bairro text DEFAULT NULL::text, p_tipo text DEFAULT NULL::text, p_modernizado boolean DEFAULT NULL::boolean,
  p_pot_min integer DEFAULT NULL::integer, p_revisao boolean DEFAULT NULL::boolean, p_fonte_mod text DEFAULT NULL::text,
  p_suspeito boolean DEFAULT NULL::boolean, p_led_min integer DEFAULT NULL::integer, p_led_max integer DEFAULT NULL::integer,
  p_power_min integer DEFAULT NULL::integer, p_power_max integer DEFAULT NULL::integer,
  p_data_inicio date DEFAULT NULL::date, p_data_fim date DEFAULT NULL::date,
  p_health_status text DEFAULT NULL::text, p_nao_verificado boolean DEFAULT NULL::boolean)
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
$function$;

-- Leitura publica (o mapa funciona sem login). Reafirmado porque CREATE OR REPLACE
-- preserva grants, mas deixar explicito evita surpresa em recriacao do schema.
GRANT EXECUTE ON FUNCTION public.ip_clusters_grid(double precision,double precision,double precision,double precision,double precision,text,text,boolean,integer,boolean,text,boolean,integer,integer,integer,integer,date,date,text,boolean) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.ip_pontos_bbox(double precision,double precision,double precision,double precision,integer,text,text,boolean,integer,boolean,text,boolean,integer,integer,integer,integer,date,date,text,boolean) TO anon, authenticated, service_role;

-- O statement_timeout do role anon foi elevado de 3s para 8s, igualando authenticated:
--   ALTER ROLE anon SET statement_timeout = '8s';
-- Aplicado fora desta migration porque ALTER ROLE e configuracao de instancia, nao de
-- schema, e nao seria replicada por um db reset.
