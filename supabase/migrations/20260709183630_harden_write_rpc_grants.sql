-- Hardening: funções de ESCRITA não devem ser executáveis pelo role anon.
-- Todas já validam a role internamente (via profiles), mas defesa em
-- profundidade: remove o vetor no nível de GRANT. Funções de leitura
-- continuam executáveis por anon (o mapa funciona sem login).
--
-- APLICADA EM PRODUÇÃO em 2026-07-09 (versão 20260709183630).

-- Fixa search_path nas 2 SECURITY DEFINER que ainda não tinham
ALTER FUNCTION public.aprovar_mudanca(p_fila_id uuid, p_aprovado boolean, p_motivo_rejeicao text) SET search_path = public;
ALTER FUNCTION public.ip_registrar_intervencao(p_ponto uuid, p_tipo text, p_data text, p_descricao text, p_responsavel text, p_lampada_nova text, p_potencia_nova integer, p_requer_aprovacao boolean) SET search_path = public;

-- Revoga EXECUTE de PUBLIC e anon nas funções de escrita; garante authenticated
DO $$
DECLARE
  fn text;
BEGIN
  FOREACH fn IN ARRAY ARRAY[
    'public.ip_inserir_ponto(numeric, numeric, text, integer, text, boolean, text, text, text, text, text, text, boolean)',
    'public.ip_atualizar_ponto(uuid, text, integer, text, boolean, text, numeric, numeric, text, text, boolean)',
    'public.ip_remover_ponto(uuid, text)',
    'public.ip_registrar_intervencao(uuid, text, text, text, text, text, integer, boolean)',
    'public.ip_criar_modelo(text, text, integer, integer, text, text, text, text, text, text, text, text, integer, numeric, numeric, numeric, text, text, text, text)',
    'public.ip_atualizar_modelo(uuid, text, text, integer, integer, text, text, text, text, text, text, text, text, integer, numeric, numeric, numeric, text, text, text, text)',
    'public.ip_deletar_modelo(uuid)',
    'public.ip_snapshot_metricas()',
    'public.aprovar_mudanca(uuid, boolean, text)',
    'public.ip_gera_codigo(ativo_tipo)'
  ]
  LOOP
    EXECUTE format('REVOKE EXECUTE ON FUNCTION %s FROM PUBLIC', fn);
    EXECUTE format('REVOKE EXECUTE ON FUNCTION %s FROM anon', fn);
    EXECUTE format('GRANT EXECUTE ON FUNCTION %s TO authenticated', fn);
    EXECUTE format('GRANT EXECUTE ON FUNCTION %s TO service_role', fn);
  END LOOP;
END $$;
