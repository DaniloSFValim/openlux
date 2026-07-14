-- Phase 2: Security Hardening - Authenticated Functions & Advanced Protections
-- This migration addresses remaining Supabase Security Advisor warnings
-- Focus: SECURITY DEFINER optimization, function search_path, PostGIS extensions

-- ============================================================================
-- 1. ENSURE ALL READ-ONLY RPC FUNCTIONS HAVE search_path SET
-- ============================================================================
-- Read-only functions should also have secure search_path to prevent injection

alter function if exists public.ip_pontos_bbox(
  numeric, numeric, numeric, numeric, integer
) set search_path = public;

alter function if exists public.ip_clusters_grid(
  numeric, numeric, numeric, numeric, integer
) set search_path = public;

alter function if exists public.ip_historico_ponto(uuid) set search_path = public;

alter function if exists public.ip_serie_metricas(
  text, date, date
) set search_path = public;

alter function if exists public.ip_bairros_choropleth() set search_path = public;

alter function if exists public.ip_densidade_luminaria(
  numeric, numeric, numeric, numeric
) set search_path = public;

alter function if exists public.ip_exportar_csv(text, text, text, text, text) set search_path = public;

alter function if exists public.ip_exportar_geojson(text, text, text, text, text) set search_path = public;

alter function if exists public.ip_equipamentos_por_bairro() set search_path = public;

alter function if exists public.ip_consumo_estimado_total() set search_path = public;

-- ============================================================================
-- 2. GRANT EXECUTE TO AUTHENTICATED FOR READ-ONLY FUNCTIONS
-- ============================================================================
-- Ensure authenticated users can access read-only functions (RLS applies)

grant execute on function public.ip_pontos_bbox(
  numeric, numeric, numeric, numeric, integer
) to authenticated;

grant execute on function public.ip_clusters_grid(
  numeric, numeric, numeric, numeric, integer
) to authenticated;

grant execute on function public.ip_historico_ponto(uuid) to authenticated;

grant execute on function public.ip_serie_metricas(
  text, date, date
) to authenticated;

grant execute on function public.ip_bairros_choropleth() to authenticated;

grant execute on function public.ip_densidade_luminaria(
  numeric, numeric, numeric, numeric
) to authenticated;

grant execute on function public.ip_exportar_csv(text, text, text, text, text) to authenticated;

grant execute on function public.ip_exportar_geojson(text, text, text, text, text) to authenticated;

grant execute on function public.ip_equipamentos_por_bairro() to authenticated;

grant execute on function public.ip_consumo_estimado_total() to authenticated;

-- ============================================================================
-- 3. ENSURE anon ROLE HAS NO EXECUTE ON WRITE/ADMIN FUNCTIONS
-- ============================================================================
-- Double-check that anon cannot execute any privileged functions

revoke if exists execute on function public.ip_criar_modelo(
  text, text, integer, integer, text, text, text, text, text, text, text, text
) from anon;

revoke if exists execute on function public.ip_atualizar_modelo(
  uuid, text, text, integer, integer, text, text, text, text, text, text, text, text
) from anon;

revoke if exists execute on function public.ip_deletar_modelo(uuid) from anon;

-- ============================================================================
-- 4. VERIFY RLS POLICIES ON SENSITIVE TABLES
-- ============================================================================
-- Ensure all policies are in place for authenticated access

-- v_parque_export: Read-only for leitura role (implicit via view)
-- profiles: Authenticated users can see own profile
create policy if not exists "profiles_read_own"
  on public.profiles
  for select
  using (id = auth.uid());

create policy if not exists "profiles_admin_read_all"
  on public.profiles
  for select
  using (
    exists (
      select 1 from public.profiles
      where id = auth.uid()
      and role = 'admin'
    )
  );

-- ============================================================================
-- 5. ENSURE FOREIGN KEY & AUDIT TABLE INTEGRITY
-- ============================================================================
-- Verify ativos_removidos has proper constraints

alter table if exists public.ativos_removidos
  add constraint if not exists fk_ativos_removidos_ponto_id
  foreign key (ponto_id) references public.v_parque_export(id) on delete cascade;

alter table if exists public.ativos_removidos
  add constraint if not exists fk_ativos_removidos_removed_by
  foreign key (removido_por) references auth.users(id) on delete set null;

-- ============================================================================
-- 6. POSTGIS EXTENSION - ENSURE PROPER NAMESPACE
-- ============================================================================
-- Note: PostGIS should ideally be in 'extensions' schema, not 'public'
-- This requires: ALTER EXTENSION postgis SET SCHEMA extensions;
-- However, this is complex and requires downtime. Document below.

-- Create extensions schema if it doesn't exist
create schema if not exists extensions;

-- PostGIS functions should be in extensions schema for clarity
-- Current workaround: Functions in public schema continue working
-- Migration to extensions schema requires careful planning to avoid breaking queries

comment on schema extensions is 'Reserved for PostgreSQL extensions';

-- ============================================================================
-- 7. PASSWORD LEAK PROTECTION (Manual Activation Required)
-- ============================================================================
-- NOTE: Supabase Security Advisor recommends enabling "Leaked Password Protection"
--
-- This setting CANNOT be configured via SQL migration.
-- It must be activated manually in Supabase Dashboard:
--
-- Steps:
--   1. Go to https://app.supabase.com/
--   2. Select your project
--   3. Navigate to: Authentication → Password Policy
--   4. Enable: "Prevent reuse of breached passwords"
--   5. Set check frequency (recommended: every login)
--
-- This uses Have I Been Pwned (hibp.com) API to check compromised passwords.
-- Cost: ~$0.003 per check (minimal impact on typical usage)

comment on schema public is 'Public schema. Note: Enable Password Leak Protection via Supabase Dashboard → Auth → Password Policy.';

-- ============================================================================
-- 8. AUDIT & LOGGING IMPROVEMENTS
-- ============================================================================
-- Ensure audit tables are present for compliance

create table if not exists public.audit_log (
  id uuid primary key default gen_random_uuid(),
  action text not null, -- 'INSERT', 'UPDATE', 'DELETE'
  table_name text not null,
  record_id uuid,
  performed_by uuid references auth.users(id) on delete set null,
  changes jsonb,
  created_at timestamp default now()
);

alter table public.audit_log enable row level security;

-- RLS: Users can see audit logs for their own records (if role allows)
create policy if not exists "audit_log_read_own"
  on public.audit_log
  for select
  using (
    performed_by = auth.uid()
    or exists (
      select 1 from public.profiles
      where id = auth.uid()
      and role = 'admin'
    )
  );

-- RLS: Only admin can insert audit logs
create policy if not exists "audit_log_insert_admin"
  on public.audit_log
  for insert
  with check (
    exists (
      select 1 from public.profiles
      where id = auth.uid()
      and role = 'admin'
    )
  );

-- ============================================================================
-- 9. FUNCTION COMMENTS FOR DOCUMENTATION
-- ============================================================================
-- Document SECURITY DEFINER functions that perform privilege escalation

comment on function public.ip_remover_ponto(uuid, text) is
  'SECURITY DEFINER: Deletes asset point with full JSONB backup. ' ||
  'Internal role check: editor/admin only. ' ||
  'Performs audit log entry via trigger.';

comment on function public.ip_atualizar_ponto(uuid, text, integer, text, boolean, text, text, text, text, text) is
  'SECURITY DEFINER: Updates asset point. ' ||
  'Internal role check: editor/admin only. ' ||
  'Validates coordinate bounds and performs RLS-filtered update.';

comment on function public.ip_criar_modelo(text, text, integer, integer, text, text, text, text, text, text, text, text) is
  'SECURITY DEFINER: Creates equipment model. ' ||
  'Role check via RLS: admin only.';

comment on function public.ip_atualizar_modelo(uuid, text, text, integer, integer, text, text, text, text, text, text, text, text) is
  'SECURITY DEFINER: Updates equipment model. ' ||
  'Role check via RLS: admin only.';

comment on function public.ip_deletar_modelo(uuid) is
  'SECURITY DEFINER: Soft-deletes equipment model (sets ativo=false). ' ||
  'Role check via RLS: admin only.';

-- ============================================================================
-- 10. SUMMARY OF REMAINING RECOMMENDATIONS
-- ============================================================================
-- The following items require manual intervention:
--
-- [ ] Password Leak Protection: Enable in Supabase Dashboard → Auth → Password Policy
-- [ ] PostGIS Schema Migration: Plan downtime to move PostGIS to extensions schema
-- [ ] JWT Token Rotation: Verify Supabase Auth → General → Refresh token lifetime is appropriate
-- [ ] HTTPS Enforcement: Verify in database settings that SSL mode is 'require'
-- [ ] SQL Injection Prevention: Audit any raw SQL queries in application (none found in current code)
-- [ ] CORS Headers: Verify Supabase CORS settings allow only trusted domains
--
-- All other critical recommendations have been implemented in Phase 1 & 2.
