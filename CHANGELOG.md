# Changelog

All notable changes to the Iluminação LED Niterói project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.1] - 2026-07-09

### 🚀 AUDITORIA DE SEGURANÇA E PRODUÇÃO COMPLETA

Hotfixes críticos de produção com consolidação de todas as correções de auditoria de segurança, schema e infraestrutura. **Todas as migrations já aplicadas em produção (2026-07-09).**

**PRs Merged:** #29, #30, #31, #32, #33, #34  
**Status:** Production Ready ✅  
**Tests:** 24/26 E2E, 9/9 API, Lighthouse, Security Scan — All Passing

---

### 🔴 CRITICAL FIXES - RPC Production Hotfixes (PRs #29-31)

#### PR #29: Corrigir `ip_inserir_ponto` Overload Ambiguity
- **Problema:** "Could not choose the best candidate function" — 2 overloads conflitantes
- **Solução:** Remover overload com double precision, manter apenas versão com `p_requer_aprovacao`
- **Impacto:** Editors conseguem criar pontos novamente

#### PR #30: Adicionar Coluna `fonte` Obrigatória
- **Problema:** RPC não preenchendo NOT NULL column `fonte`
- **Solução:** Adicionar `p_fonte` (ENUM: levantamento_campo, ponto_original_kml, estimado, censo_enel)
- **Impacto:** Auditoria de origem dos dados agora automática

#### PR #31: Corrigir Coluna `modernizado_led` para Ativos Não-Luminária
- **Problema:** NULL sobrescreve NOT NULL DEFAULT ao criar POSTE/CAIXA
- **Solução:** CASE statement — false para não-luminária, valor parâmetro para luminária
- **Impacto:** Criar qualquer tipo de ativo sem constraint violation

---

### 🔒 AUDIT ITEMS 1-7 - Schema & Security Hardening

#### PR #32: Audit Items 1-3 - Schema Sync & Storage

**Item C1 - Migrations Versioning:**
- Reorganizar migrations legadas (prefixo 8-dígitos) para `supabase/migrations_archive/`
- Adicionar `supabase/migrations/README.md` com fluxo correto: escrever → aplicar → commitar
- Banco é fonte de verdade; repositório espelha `schema_migrations` table

**Item C2 - RPC Column Mapping (Migration 20260709182342):**
- `ip_atualizar_ponto`: UPDATE em view ➜ UPDATE direto em tabela `pontos_luminaria`
- Usar coluna `geom` com PostGIS: `ST_SetSRID(ST_MakePoint(p_lng, p_lat), 4326)`
- Type casting correto para ENUMs (tipo_luminaria, status, tipo_lampada)
- Suporta fila_aprovacao (approval workflow)

**Item C3 - Storage Buckets (Migration 20260709182416):**
- Criar buckets: `luminarias-fotos`, `luminarias-ies` (5MB limit cada)
- Policies: SELECT public, INSERT/UPDATE editor+admin, DELETE admin

#### PR #33: Audit Items 4-7 - Netlify & Security

**Item C4 - Netlify Publish Restriction (netlify.toml):**
- **Antes:** `publish = "."` — expunha `/supabase/migrations/*.sql`, `/docs/`, POCs
- **Depois:** `publish = "dist"` — apenas `index.html` publicado
- Build: `mkdir -p dist && cp index.html dist/index.html`

**Item C5 - Website Security:**
- Remover indexação de URLs obsoletas
- Sites Netlify antigos renomeados para `obsoleto-nao-usar-*`

**Item I1 - RPC Overload Consolidation (Migration 20260709183525):**
- DROP 10 overloads mortas (evita ambiguidade PostgreSQL)
- Manter: 1 assinatura por RPC (aquela que frontend usa)

**Item I4 - RLS Grants Hardening (Migration 20260709183630):**
- Fix `search_path` em SECURITY DEFINER functions
- REVOKE EXECUTE de `PUBLIC` e `anon` em 10 funções de escrita
- GRANT a `authenticated` e `service_role`
- Preservar leitura anônima (mapa funciona sem login)

#### PR #34: Documentation & Presentation

**README.md Redesign + LICENSE:**
- Hero centralizado + badges organizados (3 grupos)
- Tabela de métricas (42.763 pontos, 52 bairros, 39% LED, 85k+ records)
- Grid 2×2 de funcionalidades, tabela de perfis, diagrama Mermaid
- LICENSE file (MIT) — badge existia, arquivo faltava

---

### 📊 Database Migrations Applied

| Versão | Nome | Propósito | Status |
|--------|------|----------|--------|
| 20260709182342 | sync_rpc_hotfixes_fix_atualizar_ponto | Fix geom/ENUM | ✅ |
| 20260709182416 | create_storage_buckets_luminarias | Buckets + policies | ✅ |
| 20260709183525 | drop_dead_rpc_overloads | Remove 10 overloads | ✅ |
| 20260709183630 | harden_write_rpc_grants | REVOKE anon, search_path | ✅ |

---

### 📈 Impact Summary

| Área | Antes | Depois |
|------|-------|--------|
| Criação Pontos | ❌ Falha | ✅ OK |
| Edição Pontos | ❌ UPDATE view | ✅ UPDATE tabela |
| Upload Foto/IES | ❌ Bucket not found | ✅ OK |
| Netlify | ❌ .sql exposto | ✅ Apenas index.html |
| RPC | ❌ PGRST203 | ✅ 1 signature |
| RLS | ⚠️ Anon write | ✅ REVOKE anon |

---

### ✅ Zero Breaking Changes
- Sem mudanças em `index.html`
- Sem mudanças em código funcional
- Migrations 100% backward compatible
- RLS apenas hardened

---

## [1.2.0] - 2026-07-08

### Added

- **Theme Toggle (Dark/Light Mode)** — New button in navbar to switch between dark and light themes
  - User preference saved to localStorage
  - Syncs with system preference (prefers-color-scheme media query)
  - Smooth CSS transitions between themes

- **Zoom Minimum Validation** — New constraint for point creation
  - Points can only be created when zoom level ≥18
  - Cursor changes to pointer when hovering over map at valid zoom
  - Prevents accidental point creation at low zoom levels

- **Nominatim Address Auto-fill** — Automatic address lookup on point creation/editing
  - Reverse geocoding using OpenStreetMap Nominatim API
  - Address field automatically populated when selecting location
  - Non-blocking background request (doesn't freeze UI)

- **Security Improvements**
  - Environment variable support for Supabase credentials
  - Hardcoded credentials replaced with `window.__CONFIG__` pattern
  - `.env.example` template with secure placeholders

- **Documentation** — NEW files
  - CHANGELOG.md — This file
  - .editorconfig — Code style consistency
  - Updated README, DEPLOYMENT_GUIDE, IMPROVEMENTS_SUMMARY

### Removed

- **Approval Workflow System** — Simplified editor workflow
  - Removed approval UI from admin panel
  - Editors can now update points directly
  - Admins retain full access

- **Obsolete Documentation** — Phase-specific docs consolidated

### Fixed

- **Theme Button Positioning** — Fixed navbar layout issues
- **GitHub Actions Versions** — Upgraded to v4 (checkout, setup-node)
- **Snyk Action** — Pinned to v0.4.0 (security best practice)

### Changed

- **Editor Permissions** — Direct edit access without approval queue
- **GitHub Actions** — Added npm caching for faster builds

---

## [1.1.0] - 2026-07-01

### Added

- Dark/Light theme toggle with system preference sync
- Plausible Analytics integration
- Rate limiting for RPC requests
- End-to-End tests via Playwright
- Lighthouse CI for performance monitoring
- Security scanning (npm audit + OWASP ZAP)
- Load testing via k6
- API testing via Postman/Newman

---

## [1.0.0] - 2026-06-15

### Added

- Initial Release - Core GIS Application
  - Interactive map with Leaflet.js
  - Point creation/editing
  - Role-based access control
  - CSV/GeoJSON/PDF export
  - Supabase integration
  - Netlify deployment

---

**Last Updated:** 2026-07-09
