-- Duas correcoes na mesma area: sobrecargas duplicadas e permissao indevida.
--
-- ============================================================================
-- 1. Remover as sobrecargas antigas de ip_criar_modelo e ip_atualizar_modelo
-- ============================================================================
--
-- O banco tinha DUAS versoes de cada uma:
--   ip_criar_modelo      -> 20 parametros (antiga) e 24 (com os campos Tier 1)
--   ip_atualizar_modelo  -> 21 parametros (antiga) e 25 (com os campos Tier 1)
--
-- A migration 20260709183525_drop_dead_rpc_overloads.sql ja previa essa limpeza,
-- mas as funcoes antigas continuavam no banco em 2026-07-28 — ou seja, ela nao
-- chegou a ser aplicada. Divergencia entre migrations e banco.
--
-- Impacto observado: a versao antiga de ip_atualizar_modelo IGNORA em silencio os
-- 4 campos Tier 1 (inmetro_registro, vida_util_anos, garantia_anos,
-- dias_manutencao_preventiva). Quando o PostgREST resolve para ela, o update
-- conclui sem erro, o painel mostra "modelo atualizado" e esses campos nao mudam.
-- Foi o sintoma relatado: "diz que editou, mas nao editou".
--
-- Manter duas sobrecargas tambem arrisca o erro PGRST203 do PostgREST
-- ("Could not choose the best candidate function"), que ja atingiu este projeto
-- antes (PR #29).

DROP FUNCTION IF EXISTS public.ip_criar_modelo(
  text, text, integer, integer, text, text, text, text, text, text, text, text,
  integer, numeric, numeric, numeric, text, text, text, text
);

DROP FUNCTION IF EXISTS public.ip_atualizar_modelo(
  uuid, text, text, integer, integer, text, text, text, text, text, text, text,
  text, integer, numeric, numeric, numeric, text, text, text, text
);

-- ============================================================================
-- 2. Revogar EXECUTE de anon e PUBLIC nas assinaturas que permanecem
-- ============================================================================
--
-- ip_criar_modelo e ip_atualizar_modelo sao SECURITY DEFINER, portanto contornam
-- o RLS da tabela equipamentos_modelo. Elas estavam com EXECUTE concedido a
-- `anon` e a PUBLIC, entao qualquer visitante NAO AUTENTICADO podia criar e
-- alterar modelos do catalogo via /rest/v1/rpc/.
--
-- A politica de RLS `modelos_writable` expressa a intencao correta (somente
-- admin), mas nunca e consultada nesse caminho, justamente por serem SECURITY
-- DEFINER com a tabela sem FORCE ROW LEVEL SECURITY.
--
-- Confirmado pelo proacl das funcoes e pelo advisor do Supabase
-- (anon_security_definer_function_executable).
--
-- authenticated e service_role seguem com acesso: o painel administrativo
-- depende disso e o usuario ja precisa estar logado para chegar la.

REVOKE EXECUTE ON FUNCTION public.ip_criar_modelo(
  text, text, integer, integer, text, text, text, text, text, text, text, text,
  integer, numeric, numeric, numeric, text, text, text, text,
  text, integer, integer, integer
) FROM anon, PUBLIC;

REVOKE EXECUTE ON FUNCTION public.ip_atualizar_modelo(
  uuid, text, text, integer, integer, text, text, text, text, text, text, text,
  text, integer, numeric, numeric, numeric, text, text, text, text,
  text, integer, integer, integer
) FROM anon, PUBLIC;

GRANT EXECUTE ON FUNCTION public.ip_criar_modelo(
  text, text, integer, integer, text, text, text, text, text, text, text, text,
  integer, numeric, numeric, numeric, text, text, text, text,
  text, integer, integer, integer
) TO authenticated, service_role;

GRANT EXECUTE ON FUNCTION public.ip_atualizar_modelo(
  uuid, text, text, integer, integer, text, text, text, text, text, text, text,
  text, integer, numeric, numeric, numeric, text, text, text, text,
  text, integer, integer, integer
) TO authenticated, service_role;
