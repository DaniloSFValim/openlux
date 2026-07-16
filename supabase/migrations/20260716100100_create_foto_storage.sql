-- Migration: Create Storage bucket for equipment photos
-- Purpose: Store equipment model photos in Supabase Storage
-- Date: 2026-07-16

-- Create bucket for equipment photos
INSERT INTO storage.buckets (id, name, public)
VALUES ('equipamentos-fotos', 'equipamentos-fotos', true)
ON CONFLICT (id) DO NOTHING;

-- RLS Policy: Authenticated users can upload photos
CREATE POLICY "Authenticated users can upload equipment photos"
ON storage.objects
FOR INSERT
WITH CHECK (
  bucket_id = 'equipamentos-fotos'
  AND auth.role() = 'authenticated'
);

-- RLS Policy: Public can read photos (for public URLs)
CREATE POLICY "Public can read equipment photos"
ON storage.objects
FOR SELECT
USING (bucket_id = 'equipamentos-fotos');

-- RLS Policy: Authenticated can delete their own uploads
CREATE POLICY "Authenticated can delete equipment photos"
ON storage.objects
FOR DELETE
USING (
  bucket_id = 'equipamentos-fotos'
  AND auth.role() = 'authenticated'
);
