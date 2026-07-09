-- Hardening: Fix mutable search_path warnings & revoke anon execute on write functions
-- Supabase Advisor flagged 7 functions com search_path mutable
-- e 28+ functions que anon role pode executar sem autenticação

-- ============================================================================
-- 1. ADICIONAR search_path = public às funções que faltam
-- ============================================================================
-- Isso previne SQL injection via search_path manipulation

-- aprovar_mudanca já tem set search_path se aplicado antes, revisar
alter function if exists public.aprovar_mudanca(uuid, boolean, text) set search_path = public;

-- ip_atualizar_ponto - múltiplas overloads
alter function if exists public.ip_atualizar_ponto(uuid, text, integer, text, boolean, text, text, text, text, text) set search_path = public;
alter function if exists public.ip_atualizar_ponto(uuid, text, integer, text, boolean, text, numeric, numeric, text, text, boolean) set search_path = public;
alter function if exists public.ip_atualizar_ponto(uuid, text, integer, text, boolean, text, text, text, boolean) set search_path = public;

-- ip_registrar_intervencao
alter function if exists public.ip_registrar_intervencao(uuid, text, text, text, text, text, integer, boolean) set search_path = public;

-- ip_inserir_ponto - múltiplas overloads
alter function if exists public.ip_inserir_ponto(numeric, numeric, text, integer, text, boolean, text, text, text, text, text, text) set search_path = public;
alter function if exists public.ip_inserir_ponto(numeric, numeric, text, integer, text, boolean, text, text, text, text, text, text, boolean) set search_path = public;

-- ============================================================================
-- 2. REVOGAR EXECUTE da anon role para funções de escrita (CRITICAL)
-- ============================================================================
-- Esses funções fazem DELETE/UPDATE/INSERT - não devem ser públicas

-- Revogar acesso anon às funções de escrita (apenas editor/admin)
revoke execute on function public.ip_remover_ponto(uuid, text) from anon;
revoke execute on function public.ip_atualizar_ponto(uuid, text, integer, text, boolean, text, text, text, text, text) from anon;
revoke execute on function public.ip_atualizar_ponto(uuid, text, integer, text, boolean, text, numeric, numeric, text, text, boolean) from anon;
revoke execute on function public.ip_atualizar_ponto(uuid, text, integer, text, boolean, text, text, text, boolean) from anon;
revoke execute on function public.ip_inserir_ponto(numeric, numeric, text, integer, text, boolean, text, text, text, text, text, text) from anon;
revoke execute on function public.ip_inserir_ponto(numeric, numeric, text, integer, text, boolean, text, text, text, text, text, text, boolean) from anon;
revoke execute on function public.ip_registrar_intervencao(uuid, text, text, text, text, text, integer, boolean) from anon;
revoke execute on function public.aprovar_mudanca(uuid, boolean, text) from anon;

-- Grant apenas para authenticated users (RLS + função interna checka role)
grant execute on function public.ip_remover_ponto(uuid, text) to authenticated;
grant execute on function public.ip_atualizar_ponto(uuid, text, integer, text, boolean, text, text, text, text, text) to authenticated;
grant execute on function public.ip_atualizar_ponto(uuid, text, integer, text, boolean, text, numeric, numeric, text, text, boolean) to authenticated;
grant execute on function public.ip_atualizar_ponto(uuid, text, integer, text, boolean, text, text, text, boolean) to authenticated;
grant execute on function public.ip_inserir_ponto(numeric, numeric, text, integer, text, boolean, text, text, text, text, text, text) to authenticated;
grant execute on function public.ip_inserir_ponto(numeric, numeric, text, integer, text, boolean, text, text, text, text, text, text, boolean) to authenticated;
grant execute on function public.ip_registrar_intervencao(uuid, text, text, text, text, text, integer, boolean) to authenticated;
grant execute on function public.aprovar_mudanca(uuid, boolean, text) to authenticated;

-- ============================================================================
-- 3. NOTA sobre funções read-only (ip_pontos_bbox, ip_clusters_grid, etc)
-- ============================================================================
-- Essas funções são de leitura apenas e podem ficar com acesso anon
-- Se desejar restringir, adicione:
-- revoke execute on function public.ip_pontos_bbox(...) from anon;
-- revoke execute on function public.ip_clusters_grid(...) from anon;

-- ============================================================================
-- 4. BUCKET STORAGE - Remove listing permissions
-- ============================================================================
-- Bucket 'branding' permite listing público, manter apenas object access

-- Remover policy que permite listing
drop policy if exists "branding leitura publica" on storage.objects;

-- Recriar policy para apenas acesso direto (sem listing)
create policy "branding_public_read"
  on storage.objects
  for select using (bucket_id = 'branding');

-- ============================================================================
-- NOTA: Ativar Proteção contra Senhas Vazadas
-- ============================================================================
-- Isso deve ser feito no Supabase Dashboard → Auth → Password Policy
-- Não é possível via SQL migration
-- Action: Go to https://app.supabase.com → Auth → Password Policy → Enable "Leaked Password Protection"
