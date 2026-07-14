-- Cria os buckets que o frontend já referencia (upload de foto e arquivo .IES
-- de modelos de luminária) e as policies de acesso.
-- Antes desta migration só existia o bucket 'branding'; os uploads falhavam
-- com "Bucket not found".
--
-- APLICADA EM PRODUÇÃO em 2026-07-09 (versão 20260709182416).

INSERT INTO storage.buckets (id, name, public, file_size_limit)
VALUES
  ('luminarias-fotos', 'luminarias-fotos', true, 5242880),
  ('luminarias-ies',   'luminarias-ies',   true, 5242880)
ON CONFLICT (id) DO NOTHING;

-- Leitura pública (frontend usa getPublicUrl)
DROP POLICY IF EXISTS "luminarias leitura publica" ON storage.objects;
CREATE POLICY "luminarias leitura publica" ON storage.objects
  FOR SELECT
  USING (bucket_id IN ('luminarias-fotos', 'luminarias-ies'));

-- Upload: apenas editor e admin
DROP POLICY IF EXISTS "luminarias editor insere" ON storage.objects;
CREATE POLICY "luminarias editor insere" ON storage.objects
  FOR INSERT
  WITH CHECK (
    bucket_id IN ('luminarias-fotos', 'luminarias-ies')
    AND EXISTS (SELECT 1 FROM public.profiles
                WHERE id = auth.uid() AND role IN ('admin', 'editor'))
  );

-- Atualização: apenas editor e admin
DROP POLICY IF EXISTS "luminarias editor atualiza" ON storage.objects;
CREATE POLICY "luminarias editor atualiza" ON storage.objects
  FOR UPDATE
  USING (
    bucket_id IN ('luminarias-fotos', 'luminarias-ies')
    AND EXISTS (SELECT 1 FROM public.profiles
                WHERE id = auth.uid() AND role IN ('admin', 'editor'))
  );

-- Remoção: apenas admin
DROP POLICY IF EXISTS "luminarias admin remove" ON storage.objects;
CREATE POLICY "luminarias admin remove" ON storage.objects
  FOR DELETE
  USING (
    bucket_id IN ('luminarias-fotos', 'luminarias-ies')
    AND public.is_admin()
  );
