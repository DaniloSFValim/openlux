-- Remove overloads mortas de RPCs. O frontend usa exatamente UMA assinatura de
-- cada função; as demais eram versões antigas que causavam risco de
-- ambiguidade (erro PGRST203 "Could not choose the best candidate function",
-- que já quebrou produção 1x) e divergência de regras de permissão.
--
-- APLICADA EM PRODUÇÃO em 2026-07-09 (versão 20260709183525).

-- ip_atualizar_ponto: manter apenas (…p_lat, p_lng, …p_requer_aprovacao)
DROP FUNCTION IF EXISTS public.ip_atualizar_ponto(p_id uuid, p_tipo text, p_potencia integer, p_status text, p_modernizado boolean, p_endereco text, p_patrimonio text, p_obs text, p_tipo_luminaria text, p_classe_nbr text);
DROP FUNCTION IF EXISTS public.ip_atualizar_ponto(p_id uuid, p_tipo text, p_potencia integer, p_status text, p_modernizado boolean, p_obs text, p_tipo_luminaria text, p_classe_nbr text, p_requer_aprovacao boolean);

-- ip_pontos_bbox: manter apenas a versão de 19 parâmetros (com p_health_status)
DROP FUNCTION IF EXISTS public.ip_pontos_bbox(min_lng double precision, min_lat double precision, max_lng double precision, max_lat double precision, limite integer, p_bairro text, p_tipo text, p_modernizado boolean, p_pot_min integer, p_revisao boolean, p_fonte_mod text, p_suspeito boolean);
DROP FUNCTION IF EXISTS public.ip_pontos_bbox(min_lng double precision, min_lat double precision, max_lng double precision, max_lat double precision, limite integer, p_bairro text, p_tipo text, p_modernizado boolean, p_pot_min integer, p_revisao boolean, p_fonte_mod text, p_suspeito boolean, p_led_min integer, p_led_max integer, p_power_min integer, p_power_max integer, p_data_inicio date, p_data_fim date);

-- ip_clusters_grid: manter apenas (grid_deg double precision, …, p_health_status)
DROP FUNCTION IF EXISTS public.ip_clusters_grid(min_lng double precision, min_lat double precision, max_lng double precision, max_lat double precision, grid_deg double precision, p_bairro text, p_tipo text, p_modernizado boolean, p_pot_min integer, p_revisao boolean, p_fonte_mod text, p_suspeito boolean);
DROP FUNCTION IF EXISTS public.ip_clusters_grid(min_lng double precision, min_lat double precision, max_lng double precision, max_lat double precision, grid_deg numeric, p_bairro text, p_tipo text, p_modernizado boolean, p_pot_min integer, p_revisao boolean, p_fonte_mod text, p_suspeito boolean, p_led_min integer, p_led_max integer, p_power_min integer, p_power_max integer, p_data_inicio date, p_data_fim date);
DROP FUNCTION IF EXISTS public.ip_clusters_grid(min_lng double precision, min_lat double precision, max_lng double precision, max_lat double precision, zoom_level integer, p_bairro text, p_tipo text, p_modernizado boolean, p_pot_min integer, p_revisao boolean, p_fonte_mod text, p_suspeito boolean, p_led_min integer, p_led_max integer, p_power_min integer, p_power_max integer, p_data_inicio date, p_data_fim date);
DROP FUNCTION IF EXISTS public.ip_clusters_grid(min_lng double precision, min_lat double precision, max_lng double precision, max_lat double precision, zoom_level integer, p_bairro text, p_tipo text, p_modernizado boolean, p_pot_min integer, p_revisao boolean, p_fonte_mod text, p_suspeito boolean, p_led_min integer, p_led_max integer, p_power_min integer, p_power_max integer, p_data_inicio date, p_data_fim date, p_health_status text);

-- ip_criar_modelo: manter apenas a versão Tier 2 (20 parâmetros, SECURITY DEFINER)
-- A de 12 parâmetros tinha SECURITY DEFINER=false — regra de permissão divergente
DROP FUNCTION IF EXISTS public.ip_criar_modelo(p_fabricante text, p_modelo text, p_potencia_w integer, p_temperatura_cor_k integer, p_tensao text, p_ip text, p_classe_nbr text, p_tecnologia text, p_tipo_luminaria text, p_tipo_lampada text, p_foto_url text, p_descricao text);

-- ip_atualizar_modelo: manter apenas a versão Tier 2 (21 parâmetros)
DROP FUNCTION IF EXISTS public.ip_atualizar_modelo(p_id uuid, p_fabricante text, p_modelo text, p_potencia_w integer, p_temperatura_cor_k integer, p_tensao text, p_ip text, p_classe_nbr text, p_tecnologia text, p_tipo_luminaria text, p_tipo_lampada text, p_foto_url text, p_descricao text);
