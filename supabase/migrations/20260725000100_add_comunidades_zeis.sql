-- Comunidades / Zonas de Especial Interesse Social (ZEIS) — Mapa 8 do Plano Diretor.
-- Fonte: SIGEO Niteroi, ArcGIS FeatureServer camada 430 (owner pmngeo), reprojetada para 4326.
-- Recarga dos dados: scripts/import-comunidades-zeis.sh
--
-- O filtro por comunidade REUSA ip_pontos_poligono/ip_stats_poligono
-- (20260710191925_add_polygon_selection_rpcs.sql). Nenhuma RPC existente e alterada aqui:
-- adicionar parametro a ip_pontos_bbox/ip_clusters_grid/ip_estatisticas cria assinatura nova
-- em vez de substituir, gerando sobrecargas ambiguas (PGRST202/203).

CREATE TABLE IF NOT EXISTS public.comunidades_zeis (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  nome          text NOT NULL,
  bairro        text,
  sigla_regiao  text,
  geom          geometry(MultiPolygon, 4326) NOT NULL,
  criado_em     timestamptz NOT NULL DEFAULT now()
);

-- Sem UNIQUE(nome): a fonte traz nomes repetidos legitimamente (6x "Nao identificada",
-- 2x "Morro da Bela Vista", 2x "Sao Jose/D.Zinha/ Jardim Alvorada"). As RPCs agregam por nome.
CREATE INDEX IF NOT EXISTS idx_comunidades_zeis_geom ON public.comunidades_zeis USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_comunidades_zeis_nome ON public.comunidades_zeis(nome);

ALTER TABLE public.comunidades_zeis ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS comunidades_zeis_leitura_publica ON public.comunidades_zeis;
CREATE POLICY comunidades_zeis_leitura_publica ON public.comunidades_zeis FOR SELECT USING (true);

GRANT SELECT ON public.comunidades_zeis TO anon, authenticated, service_role;

-- Lista para o dropdown. Agrupa por nome; bairro concatenado quando o mesmo nome
-- aparece em bairros diferentes, para o rotulo ficar desambiguado na UI.
CREATE OR REPLACE FUNCTION public.ip_comunidades_lista()
RETURNS json
LANGUAGE sql STABLE SECURITY DEFINER SET search_path TO 'public'
AS $function$
  SELECT coalesce(json_agg(row_to_json(t) ORDER BY t.nome), '[]'::json) FROM (
    SELECT nome,
           string_agg(DISTINCT coalesce(bairro, '—'), ' / ') AS bairro,
           count(*)::int AS n_poligonos
    FROM comunidades_zeis
    GROUP BY nome
  ) t;
$function$;

-- Geometria pura (nao FeatureCollection) no formato que ip_pontos_poligono consome.
-- ST_Union resolve os nomes repetidos, unindo os poligonos homonimos numa geometria so.
CREATE OR REPLACE FUNCTION public.ip_comunidade_geom(p_nome text)
RETURNS json
LANGUAGE sql STABLE SECURITY DEFINER SET search_path TO 'public'
AS $function$
  SELECT ST_AsGeoJSON(ST_Multi(ST_Union(geom)))::json
  FROM comunidades_zeis
  WHERE nome = p_nome;
$function$;

-- Leitura publica (o mapa funciona sem login), igual as RPCs de poligono.
GRANT EXECUTE ON FUNCTION public.ip_comunidades_lista()      TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.ip_comunidade_geom(text)    TO anon, authenticated, service_role;
