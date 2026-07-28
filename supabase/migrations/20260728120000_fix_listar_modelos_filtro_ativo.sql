-- Corrige: "nao e possivel remover modelo" no painel administrativo.
--
-- Na verdade a remocao SEMPRE funcionou. ip_deletar_modelo faz soft delete
-- (set ativo = false), mas ip_listar_modelos nao filtrava por ativo e devolvia
-- tudo. O usuario clicava em remover, via o toast "Modelo removido", a lista
-- recarregava e o modelo continuava la.
--
-- Evidencia no banco em 2026-07-28: dos 2 modelos cadastrados, 1 ja estava com
-- ativo = false e mesmo assim aparecia na listagem.
--
-- Usa `ativo IS NOT FALSE` em vez de `ativo IS TRUE` para tratar NULL como
-- ativo, coerente com o DEFAULT true da coluna. Hoje nao ha NULLs, mas isso
-- evita que linhas antigas sumam caso apareçam.
--
-- Aproveita para fixar o search_path, que o advisor do Supabase sinalizava
-- (function_search_path_mutable).

CREATE OR REPLACE FUNCTION public.ip_listar_modelos()
RETURNS TABLE(
  id uuid, fabricante text, modelo text, potencia_w integer,
  temperatura_cor_k integer, tensao text, ip text, classe_nbr text,
  tecnologia text, tipo_luminaria text, tipo_lampada text, foto_url text,
  descricao text, fluxo_luminoso_lm integer, eficacia_luminosa_lm_w numeric,
  fator_potencia_fp numeric, thd_percentual numeric, grau_ik text,
  dps_especificacao text, tipo_conectividade text, arquivo_ies_url text,
  inmetro_registro text, vida_util_anos integer, garantia_anos integer,
  dias_manutencao_preventiva integer
)
LANGUAGE sql
STABLE
SET search_path TO 'public'
AS $function$
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
  WHERE em.ativo IS NOT FALSE
  ORDER BY em.id, em.updated_at DESC
$function$;
