# 🚀 Deployment Guide — OpenLux

**Status:** Fase 0–1 (Single + Multi-city planning) | **For:** DevOps engineers, city administrators, and platform maintainers

---

## Table of Contents

1. [Quick Start (Single City)](#quick-start-single-city)
2. [Production Checklist](#production-checklist)
3. [Multi-City Setup with RLS Isolation (Fase 3)](#multi-city-setup-with-rls-isolation-fase-3)
4. [Troubleshooting Multi-City Setups](#troubleshooting-multi-city-setups)
5. [Backup & Disaster Recovery](#backup--disaster-recovery)

---

## Quick Start (Single City)

For a complete step-by-step walkthrough, see [`DEPLOY_YOUR_CITY.md`](DEPLOY_YOUR_CITY.md).

**Minimal 6-step path:**

1. Fork this repository
2. Create a Supabase project and apply schema from `supabase/migrations/`
3. Import point data (geometry as SRID 4326) into `pontos_luminaria` table
4. Configure city in `config/cities/<cidade>.json` and `index.html` **CITY** block
5. Connect to Netlify (publishes `index.html` only)
6. Create users via Supabase Auth → assign roles in `profiles.role`

**Time estimate:** ~4–8 hours (data import is the long pole)

---

## Production Checklist

### Before Going Live

**Security**
- [ ] Supabase project: Enable RLS on all tables (`Settings → Schemas → [table] → Enable RLS`)
- [ ] Review `SECURITY DEFINER` RPCs in `supabase/migrations/` (should have `SET search_path = public` to avoid escalation)
- [ ] Test that `leitura` (viewer) role cannot edit points: `SELECT count(*) FROM pontos_luminaria;` should work, but `UPDATE` should fail
- [ ] Rotate Supabase service role key (see [Key Rotation](#key-rotation) below)
- [ ] Verify Netlify environment variables are set (ANON_KEY, URL)
- [ ] Review GitHub secrets used in CI/CD (should not expose SERVICE_ROLE_KEY in logs)

**Data**
- [ ] Point count audit: `SELECT COUNT(*) FROM pontos_luminaria;` matches source system
- [ ] Geometry validation: `SELECT COUNT(*) FROM pontos_luminaria WHERE geom IS NULL;` returns 0
- [ ] Bounding box check: `SELECT ST_Extent(geom) FROM pontos_luminaria;` falls within expected city bounds
- [ ] Neighborhoods loaded: `SELECT COUNT(*) FROM bairros;` > 0

**Performance**
- [ ] Spatial index exists: `SELECT indexname FROM pg_indexes WHERE tablename='pontos_luminaria' AND indexname LIKE '%geom%';`
- [ ] Test query response time: `SELECT count(*) FROM ip_pontos_bbox(...)` completes in <500ms at zoom 14
- [ ] PostGIS version: `SELECT postgis_version();` should be 3.1+

**Frontend**
- [ ] Logo + branding uploaded to Supabase Storage (`branding` bucket) if custom
- [ ] `index.html` **CITY** block points to correct Supabase URL + ANON_KEY (not SERVICE_ROLE)
- [ ] Map renders at configured center + zoom without errors
- [ ] Login works with a test editor account
- [ ] Export (CSV/PDF) works with sample data

**Monitoring**
- [ ] Database backups configured (see [Backup & Disaster Recovery](#backup--disaster-recovery))
- [ ] Netlify deploy notifications sent to team Slack/email
- [ ] Supabase monitoring enabled: Dashboard → Status → Monitor resources

### Launch Readiness Sign-Off

| Owner | Component | Status | Notes |
|-------|-----------|--------|-------|
| DevOps | Infrastructure | ✅ Ready | Supabase + Netlify + DNS |
| Data | Data import | ✅ Ready | Point count verified |
| Security | RLS + Keys | ✅ Ready | Policies tested, keys rotated |
| Product | Feature parity | ✅ Ready | Map, edit, export, campaigns working |

---

## Multi-City Setup with RLS Isolation (Fase 3)

> **Status:** Conceptual (not yet in `main`). This section documents the architecture and deployment steps for the multi-city tenant model arriving in **Fase 3**.

### Architecture Overview

Instead of one Supabase project per city, Fase 3 moves to:
- **One shared Supabase project** serving multiple cities via Row Level Security (RLS)
- **Tenant isolation** at the database level (not the application level)
- **Auth policies** tied to `city_id` on all major tables

**Benefits:**
- Single operational dashboard for all cities
- Easier data federation (aggregated API across cities)
- Cost savings on Supabase projects
- Consistent schema across all instances

**Trade-offs:**
- Requires careful RLS policy design (security-critical)
- Single database outage affects all cities
- Data residency complexity (if cities are in different countries)

### Schema Changes for Multi-City

#### 1. Add `city_id` Column to Core Tables

```sql
-- Add city_id to pontos_luminaria, bairros, equipamentos_modelo, etc.
ALTER TABLE public.pontos_luminaria ADD COLUMN city_id UUID NOT NULL REFERENCES public.cidades(id);
ALTER TABLE public.bairros ADD COLUMN city_id UUID NOT NULL REFERENCES public.cidades(id);
ALTER TABLE public.equipamentos_modelo ADD COLUMN city_id UUID;

-- Backfill existing data to city (e.g., all current points → Niterói)
UPDATE pontos_luminaria SET city_id = 'niteroi-uuid' WHERE city_id IS NULL;

-- Add constraints and indexes
ALTER TABLE public.pontos_luminaria ADD CONSTRAINT fk_pontos_city UNIQUE(id, city_id);
CREATE INDEX idx_pontos_city ON public.pontos_luminaria(city_id);
CREATE INDEX idx_bairros_city ON public.bairros(city_id);
```

#### 2. Create `cidades` (Cities) Table

```sql
CREATE TABLE public.cidades (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  nome TEXT NOT NULL UNIQUE,
  estado TEXT NOT NULL,
  criado_em TIMESTAMP DEFAULT NOW(),
  center_lat FLOAT,
  center_lng FLOAT,
  bbox_south FLOAT,
  bbox_west FLOAT,
  bbox_north FLOAT,
  bbox_east FLOAT
);

-- Insert reference cities
INSERT INTO public.cidades (nome, estado, center_lat, center_lng, bbox_south, bbox_west, bbox_north, bbox_east)
VALUES 
  ('Niterói', 'RJ', -22.885, -43.105, -23.05, -43.20, -22.80, -42.90),
  ('Rio de Janeiro', 'RJ', -22.903, -43.209, -23.05, -43.70, -22.75, -43.00);
```

#### 3. Add `city_id` to `profiles` (User → City Mapping)

```sql
ALTER TABLE public.profiles ADD COLUMN city_id UUID REFERENCES public.cidades(id);

-- A user can have multiple rows in profiles (one per city with different role)
-- OR single city + role (simpler for MVP)
-- Recommend: single city per user for MVP

-- Remove uniqueness on id, add composite key
ALTER TABLE public.profiles DROP CONSTRAINT profiles_pkey;
ALTER TABLE public.profiles ADD CONSTRAINT profiles_pkey PRIMARY KEY (id, city_id);

-- Example: editor for Niterói + admin for Rio
INSERT INTO profiles (id, city_id, role) VALUES 
  ('user-uuid-123', 'niteroi-uuid', 'editor'),
  ('user-uuid-123', 'rio-uuid', 'admin');
```

### Row Level Security (RLS) Policies

#### Enable RLS on All Multi-City Tables

```sql
ALTER TABLE public.pontos_luminaria ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.bairros ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cidades ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
```

#### Policy 1: Viewer Can See All Points in Their City

```sql
CREATE POLICY "viewers_can_read_own_city"
ON public.pontos_luminaria
FOR SELECT
USING (
  city_id IN (
    SELECT city_id FROM public.profiles WHERE id = auth.uid()
  )
);
```

**Test:**
```sql
-- Connect as viewer from Niterói
SELECT COUNT(*) FROM pontos_luminaria;
-- Should return only Niterói points, not Rio

-- Verify:
SELECT DISTINCT city_id FROM pontos_luminaria;
-- Should show only 'niteroi-uuid'
```

#### Policy 2: Editor Can Edit Points in Their City

```sql
CREATE POLICY "editors_can_update_own_city"
ON public.pontos_luminaria
FOR UPDATE
USING (
  city_id IN (
    SELECT city_id FROM public.profiles WHERE id = auth.uid() AND role IN ('editor', 'admin')
  )
);
```

#### Policy 3: Admins Can Manage Users in Their City

```sql
-- Allow admin to see profiles only from their city
CREATE POLICY "admins_manage_own_city_users"
ON public.profiles
FOR ALL
USING (
  city_id IN (
    SELECT city_id FROM public.profiles WHERE id = auth.uid() AND role = 'admin'
  )
);
```

#### Policy 4: Authenticated Users See Only Their City

```sql
CREATE POLICY "cities_visible_to_members"
ON public.cidades
FOR SELECT
USING (
  id IN (
    SELECT city_id FROM public.profiles WHERE id = auth.uid()
  )
);
```

### RPCs for Multi-City Context

#### Update RPC Signature: `ip_pontos_bbox`

Current (single-city):
```sql
CREATE OR REPLACE FUNCTION ip_pontos_bbox(
  p_bbox_south FLOAT, p_bbox_west FLOAT,
  p_bbox_north FLOAT, p_bbox_east FLOAT,
  p_zoom INT
) ...
```

Future (multi-city, Fase 3):
```sql
CREATE OR REPLACE FUNCTION ip_pontos_bbox(
  p_city_id UUID,
  p_bbox_south FLOAT, p_bbox_west FLOAT,
  p_bbox_north FLOAT, p_bbox_east FLOAT,
  p_zoom INT
) SECURITY DEFINER
SET search_path = public
LANGUAGE SQL
AS $$
  SELECT * FROM pontos_luminaria
  WHERE city_id = p_city_id
    AND geom && ST_MakeBBox(p_bbox_west, p_bbox_south, p_bbox_east, p_bbox_north)
    AND (p_zoom >= 16 OR _cluster_applies(p_zoom));
$$;
```

**Frontend change:**
```javascript
// Before
const { data } = await sb.rpc('ip_pontos_bbox', {
  p_bbox_south: -23.05,
  p_bbox_west: -43.20,
  p_bbox_north: -22.80,
  p_bbox_east: -42.90,
  p_zoom: 14
});

// After (Fase 3)
const { data } = await sb.rpc('ip_pontos_bbox', {
  p_city_id: state.currentCity.id,  // NEW
  p_bbox_south: -23.05,
  p_bbox_west: -43.20,
  p_bbox_north: -22.80,
  p_bbox_east: -42.90,
  p_zoom: 14
});
```

### Frontend: City Selector & Session Management

#### Add City Selector to Nav

```html
<select id="citySelector" onchange="switchCity(this.value)">
  <option value="niteroi-uuid">Niterói, RJ</option>
  <option value="rio-uuid">Rio de Janeiro, RJ</option>
</select>
```

#### Session State

```javascript
state.currentCity = {
  id: 'niteroi-uuid',
  nome: 'Niterói',
  role: 'editor'  // user's role in THIS city
};

async function switchCity(cityId) {
  // Fetch user's role in new city
  const { data } = await sb.rpc('get_user_role_for_city', { p_city_id: cityId });
  
  if (!data) {
    toast('You do not have access to this city', true);
    return;
  }
  
  state.currentCity = { id: cityId, role: data.role, ...data };
  
  // Reload map, re-run filters
  refresh();
  loadStatsChips();
}
```

### Multi-City Onboarding Flow (Future Admin UI)

**Current (Fase 1–2):** Manual setup

**Future (Fase 3):**
1. Admin logs in to central dashboard
2. Clicks "Add new city"
3. Fills form: nome, estado, center lat/lng, bbox
4. System creates entry in `cidades` table
5. Admin uploads CSV of points (automatically tagged with new city_id)
6. Invites city admin via email
7. City admin logs in, sees only their city's points
8. Done

---

## Troubleshooting Multi-City Setups

### Symptom: User A (Niterói editor) Can See Rio Points

**Diagnosis:**

1. Check user's city assignment:
```sql
SELECT id, city_id, role FROM profiles WHERE id = 'user-uuid-a';
-- If result is empty or city_id is NULL → problem found
```

2. Check RLS policy is enforced:
```sql
-- Switch to user A's session
SET ROLE authenticated;
SET jwt.claims.sub = 'user-uuid-a';

SELECT COUNT(*) FROM pontos_luminaria;
-- Should return 0 or only Niterói count, NOT Rio

-- Check what RLS sees:
EXPLAIN (ANALYZE, BUFFERS) SELECT COUNT(*) FROM pontos_luminaria;
-- Look for "Filter: (city_id = ...)" clause
```

3. Check if RLS is actually enabled:
```sql
SELECT tablename, rowsecurity FROM pg_tables WHERE tablename = 'pontos_luminaria';
-- Should show 't' (true) in rowsecurity column
```

**Fix:**
- Add profile row: `INSERT INTO profiles (id, city_id, role) VALUES ('user-uuid-a', 'niteroi-uuid', 'editor');`
- Refresh browser (JWT may be cached)
- Verify policy query with `EXPLAIN ANALYZE` above

### Symptom: RPC `ip_pontos_bbox` Returns Empty Despite Data Existing

**Diagnosis:**

1. Verify points have `city_id` set:
```sql
SELECT COUNT(*) FROM pontos_luminaria WHERE city_id IS NULL;
-- Should return 0
```

2. Check RPC includes city filtering:
```sql
SELECT pg_get_functiondef('public.ip_pontos_bbox'::regprocedure);
-- Should include "WHERE city_id = p_city_id"
```

3. Verify call passes correct city_id:
```javascript
// Check browser console for actual parameters
console.log('Calling ip_pontos_bbox with:', {
  p_city_id: state.currentCity.id,
  p_bbox_south: -23.05,
  ...
});
```

**Fix:**
- Backfill missing `city_id`: `UPDATE pontos_luminaria SET city_id = 'niteroi-uuid' WHERE city_id IS NULL;`
- Ensure RPC includes city_id parameter and filtering
- Verify state.currentCity.id is set on page load

### Symptom: Admin Can't See Users from Their City

**Diagnosis:**

1. Check profiles table structure:
```sql
SELECT * FROM information_schema.columns WHERE table_name = 'profiles';
-- Should have both `id` and `city_id` columns
```

2. Check admin's own profile entry:
```sql
SELECT id, city_id, role FROM profiles WHERE id = 'admin-uuid';
-- Should have role = 'admin'
```

3. Check RLS policy on profiles:
```sql
SELECT policyname, qual FROM pg_policies WHERE tablename = 'profiles' AND policyname LIKE '%manage%';
```

**Fix:**
- Create composite primary key: `ALTER TABLE profiles ADD PRIMARY KEY (id, city_id);`
- Add admin to profiles: `INSERT INTO profiles (id, city_id, role) VALUES ('admin-uuid', 'niteroi-uuid', 'admin');`
- Ensure policy includes city filtering

### Symptom: Performance Degrades with 10+ Cities

**Diagnosis:**

1. Check indexes:
```sql
SELECT indexname, tablename FROM pg_indexes WHERE tablename IN ('pontos_luminaria', 'bairros') AND indexname LIKE '%city%';
-- Should show index on city_id
```

2. Check query plan for bbox query:
```sql
EXPLAIN (ANALYZE) SELECT * FROM pontos_luminaria 
WHERE city_id = 'niteroi-uuid' 
  AND geom && ST_MakeBBox(...);
-- Should use index on city_id and geom (in that order)
```

3. Profile slow queries:
```sql
SELECT query, mean_time FROM pg_stat_statements 
WHERE query LIKE '%pontos_luminaria%' 
ORDER BY mean_time DESC;
```

**Fix:**
- Add composite index: `CREATE INDEX idx_city_geom ON pontos_luminaria(city_id, geom);`
- Enable query statistics: `CREATE EXTENSION pg_stat_statements;` (if not already)
- Consider partitioning by city_id if >1M points per city

---

## Backup & Disaster Recovery

### Automated Backups

**GitHub Actions (Daily at 02:00 UTC):**

See `.github/workflows/backup.yml` — runs `supabase db dump` and commits backup to `backups/` folder.

**Local Test:**
```bash
./scripts/backup.sh --prod
ls -lh backups/db_*.sql | head -5
```

### Manual Backup

```bash
# Single city (local Supabase)
supabase db dump -f backups/db_$(date +%Y-%m-%d).sql

# Production (linked Supabase)
supabase link --project-ref lrnmydrwzxxajylsmoih
supabase db dump --db-url "$SUPABASE_DB_URL" -f backups/prod_$(date +%Y-%m-%d).sql
```

### Restore from Backup

```bash
# Stop containers
supabase stop

# Restore data
supabase start
psql -f backups/db_2026-07-14.sql

# Verify
supabase status
SELECT COUNT(*) FROM pontos_luminaria;
```

### Disaster Recovery Plan

| Scenario | RTO | Steps |
|----------|-----|-------|
| **Point data corrupted** | 30 min | Restore from backup (steps above) → verify count matches → redeploy |
| **Schema broken** | 1 hour | Restore backup → run migrations from HEAD → test all RPCs |
| **Supabase project deleted** | 2 hours | Create new project → restore schema from `supabase/migrations/` → restore data from backup |
| **Netlify down** | 5 min | Deploy to alternative host (Vercel, GitHub Pages) with same Supabase URL |
| **Full infrastructure loss** | 4 hours | All source in Git + backups in S3/GitHub → re-provision from scratch |

### Key Rotation

When to rotate:
- Annually (security best practice)
- Immediately if key is exposed
- When employee leaves team

**Process:**
```bash
# 1. Generate new keys in Supabase Dashboard
#    Settings → API → Reveal new keys → copy

# 2. Update environment variables
#    Netlify: Settings → Build & Deploy → Environment
#    GitHub: Settings → Secrets → Actions
#    index.html: Update hardcoded values (if any)

# 3. Wait 10 minutes for cache propagation

# 4. Test with new key
#    Open site → login → check console for errors

# 5. Invalidate old key in Supabase Dashboard
#    (DO NOT DELETE until step 4 succeeds)

# 6. Monitor logs for failed auth attempts (Dashboard → Logs)
```

---

## See Also

- [DEPLOY_YOUR_CITY.md](DEPLOY_YOUR_CITY.md) — Step-by-step single-city setup
- [supabase/README.md](../supabase/README.md) — Local development environment
- [supabase/migrations/README.md](../supabase/migrations/README.md) — Database schema versioning
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) — Common issues and solutions
- [VISION.md](../VISION.md#6-roadmap-por-fases) — Multi-city Fase 3 roadmap
