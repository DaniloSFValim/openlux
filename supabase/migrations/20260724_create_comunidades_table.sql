-- Migration: Create comunidades_geojson table for community zones
-- Purpose: Store SIGEO community geometry data for spatial joins
-- Date: 2026-07-24

-- Create table to store community/zone geometries from SIGEO dataset
CREATE TABLE IF NOT EXISTS public.comunidades_geojson (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  nome text NOT NULL UNIQUE,
  geojson geometry(Geometry, 4326),
  descricao text,
  criado_em timestamptz NOT NULL DEFAULT now(),
  atualizado_em timestamptz NOT NULL DEFAULT now()
);

-- Create index for spatial operations (ST_Intersects)
CREATE INDEX IF NOT EXISTS idx_comunidades_geom ON public.comunidades_geojson USING GIST(geojson);

-- Create index for name lookups
CREATE INDEX IF NOT EXISTS idx_comunidades_nome ON public.comunidades_geojson(nome);

-- Enable RLS on the table
ALTER TABLE public.comunidades_geojson ENABLE ROW LEVEL SECURITY;

-- Create select policy (everyone can read)
DROP POLICY IF EXISTS comunidades_select ON public.comunidades_geojson;
CREATE POLICY comunidades_select ON public.comunidades_geojson FOR SELECT USING (true);

-- Grant permissions
GRANT SELECT ON public.comunidades_geojson TO anon, authenticated, service_role;
GRANT INSERT, UPDATE, DELETE ON public.comunidades_geojson TO authenticated, service_role;
