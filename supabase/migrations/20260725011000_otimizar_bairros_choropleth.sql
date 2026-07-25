-- ip_bairros_choropleth fazia um LEFT JOIN LATERAL por bairro, ou seja, 52 agregacoes
-- separadas sobre pontos_luminaria (42.764 linhas). Um unico GROUP BY produz o mesmo
-- resultado com um scan so.
--
-- Medido em producao: 289 ms -> 58 ms (5x), sem introduzir defasagem de dados.
-- Equivalencia comprovada por hash: md5 do JSON identico antes e depois
-- (68dbbc607cf164d512c8e051bcb91024, 127.992 caracteres).
--
-- Os coalesce preservam o comportamento anterior para bairro sem pontos: o LATERAL
-- devolvia total=0/led=0/pendente=0 (count de zero linhas), enquanto um LEFT JOIN
-- puro traria NULL. pct_led continua NULL nesse caso, como antes.
--
-- Esta funcao e chamada no carregamento inicial (renderMunicipioLimites) e ao ativar
-- o coropletico; era a mais lenta do bloco de inicializacao depois da otimizacao de
-- ip_clusters_grid.

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
$function$;

GRANT EXECUTE ON FUNCTION public.ip_bairros_choropleth() TO anon, authenticated, service_role;
