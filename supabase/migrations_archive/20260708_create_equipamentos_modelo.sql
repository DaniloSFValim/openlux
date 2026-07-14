-- Tabela de modelos de equipamentos (catálogo de luminárias LED)
create table if not exists public.equipamentos_modelo (
  id uuid primary key default gen_random_uuid(),

  -- Identificação do modelo
  fabricante text not null,
  modelo text not null,

  -- Especificações técnicas
  potencia_w integer not null check (potencia_w > 0 and potencia_w <= 2000),
  temperatura_cor_k integer, -- e.g., 3000, 4000, 5000, 6500
  tensao text, -- e.g., "110", "220", "110/220 (bivolt)"
  ip text, -- e.g., "IP65"
  classe_nbr text, -- e.g., "V3", "P2", "C4"
  tecnologia text not null default 'LED', -- e.g., "LED", "LED Smart", "vapor_sodio"

  -- Campos que alimentam o formulário de ponto
  tipo_luminaria text, -- viaria, globo, petala, projetor, balizador, orla, ornamental, piso, outro
  tipo_lampada text default 'led', -- led, vapor_sodio, metalico, vapor_mercurio, fluorescente

  -- Metadados
  foto_url text,
  descricao text,
  ativo boolean default true,

  -- Auditoria
  created_at timestamp default now(),
  updated_at timestamp default now(),
  created_by uuid references auth.users(id),

  -- Restrição de unicidade
  constraint unique_modelo unique(fabricante, modelo)
);

-- Index para busca rápida
create index idx_equipamentos_modelo_fabricante on public.equipamentos_modelo(fabricante);
create index idx_equipamentos_modelo_potencia on public.equipamentos_modelo(potencia_w);
create index idx_equipamentos_modelo_tecnologia on public.equipamentos_modelo(tecnologia);

-- Enable RLS
alter table public.equipamentos_modelo enable row level security;

-- RLS Policy: Todos podem ler modelos
create policy "modelos_readable" on public.equipamentos_modelo
  for select using (true);

-- RLS Policy: Apenas admin pode criar/editar/deletar
create policy "modelos_writable" on public.equipamentos_modelo
  for insert with check (
    exists (
      select 1 from public.profiles
      where id = auth.uid()
      and role = 'admin'
    )
  );

create policy "modelos_updatable" on public.equipamentos_modelo
  for update using (
    exists (
      select 1 from public.profiles
      where id = auth.uid()
      and role = 'admin'
    )
  )
  with check (
    exists (
      select 1 from public.profiles
      where id = auth.uid()
      and role = 'admin'
    )
  );

create policy "modelos_deletable" on public.equipamentos_modelo
  for delete using (
    exists (
      select 1 from public.profiles
      where id = auth.uid()
      and role = 'admin'
    )
  );

-- RPC: Listar modelos disponíveis
create or replace function ip_listar_modelos()
returns table (
  id uuid,
  fabricante text,
  modelo text,
  potencia_w integer,
  temperatura_cor_k integer,
  tensao text,
  ip text,
  classe_nbr text,
  tecnologia text,
  tipo_luminaria text,
  tipo_lampada text,
  foto_url text,
  descricao text
) language sql stable as $$
  select
    id,
    fabricante,
    modelo,
    potencia_w,
    temperatura_cor_k,
    tensao,
    ip,
    classe_nbr,
    tecnologia,
    tipo_luminaria,
    tipo_lampada,
    foto_url,
    descricao
  from public.equipamentos_modelo
  where ativo = true
  order by fabricante, modelo;
$$;

-- RPC: Criar novo modelo (admin only via RLS)
create or replace function ip_criar_modelo(
  p_fabricante text,
  p_modelo text,
  p_potencia_w integer,
  p_temperatura_cor_k integer default null,
  p_tensao text default null,
  p_ip text default null,
  p_classe_nbr text default null,
  p_tecnologia text default 'LED',
  p_tipo_luminaria text default null,
  p_tipo_lampada text default 'led',
  p_foto_url text default null,
  p_descricao text default null
)
returns uuid language plpgsql as $$
declare
  v_id uuid;
begin
  insert into public.equipamentos_modelo (
    fabricante, modelo, potencia_w,
    temperatura_cor_k, tensao, ip,
    classe_nbr, tecnologia,
    tipo_luminaria, tipo_lampada,
    foto_url, descricao, created_by
  ) values (
    p_fabricante, p_modelo, p_potencia_w,
    p_temperatura_cor_k, p_tensao, p_ip,
    p_classe_nbr, p_tecnologia,
    p_tipo_luminaria, p_tipo_lampada,
    p_foto_url, p_descricao, auth.uid()
  )
  returning id into v_id;
  return v_id;
end;
$$;

-- RPC: Atualizar modelo (admin only via RLS)
create or replace function ip_atualizar_modelo(
  p_id uuid,
  p_fabricante text default null,
  p_modelo text default null,
  p_potencia_w integer default null,
  p_temperatura_cor_k integer default null,
  p_tensao text default null,
  p_ip text default null,
  p_classe_nbr text default null,
  p_tecnologia text default null,
  p_tipo_luminaria text default null,
  p_tipo_lampada text default null,
  p_foto_url text default null,
  p_descricao text default null
)
returns boolean language plpgsql as $$
begin
  update public.equipamentos_modelo
  set
    fabricante = coalesce(p_fabricante, fabricante),
    modelo = coalesce(p_modelo, modelo),
    potencia_w = coalesce(p_potencia_w, potencia_w),
    temperatura_cor_k = coalesce(p_temperatura_cor_k, temperatura_cor_k),
    tensao = coalesce(p_tensao, tensao),
    ip = coalesce(p_ip, ip),
    classe_nbr = coalesce(p_classe_nbr, classe_nbr),
    tecnologia = coalesce(p_tecnologia, tecnologia),
    tipo_luminaria = coalesce(p_tipo_luminaria, tipo_luminaria),
    tipo_lampada = coalesce(p_tipo_lampada, tipo_lampada),
    foto_url = coalesce(p_foto_url, foto_url),
    descricao = coalesce(p_descricao, descricao),
    updated_at = now()
  where id = p_id;

  return found;
end;
$$;

-- RPC: Deletar modelo (admin only via RLS - soft delete)
create or replace function ip_deletar_modelo(p_id uuid)
returns boolean language plpgsql as $$
begin
  update public.equipamentos_modelo
  set ativo = false, updated_at = now()
  where id = p_id;

  return found;
end;
$$;

-- Hardening: fixar search_path (recomendação do Supabase advisor)
alter function public.ip_listar_modelos() set search_path = public;
alter function public.ip_criar_modelo(text,text,integer,integer,text,text,text,text,text,text,text,text) set search_path = public;
alter function public.ip_atualizar_modelo(uuid,text,text,integer,integer,text,text,text,text,text,text,text,text) set search_path = public;
alter function public.ip_deletar_modelo(uuid) set search_path = public;
