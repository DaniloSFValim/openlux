-- Tabela de modelos de equipamentos (LED lamps repository)
create table if not exists public.equipamentos_modelo (
  id uuid primary key default gen_random_uuid(),

  -- Identificação do modelo
  fabricante text not null,
  modelo text not null,

  -- Especificações técnicas
  potencia_w integer not null check (potencia_w > 0 and potencia_w <= 2000),
  temperatura_cor_k integer, -- e.g., 3000, 4000, 5000, 6500
  tensao_v integer, -- e.g., 110, 220
  ip text, -- e.g., "IP65"
  classe_nbr text, -- e.g., "V3", "P2", "C4"
  tecnologia text not null, -- e.g., "LED", "LED RGB", "LED Smart"

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

-- RLS Policy: Todos podem ler modelos ativos
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
  tensao_v integer,
  ip text,
  classe_nbr text,
  tecnologia text,
  foto_url text,
  descricao text
) language sql stable as $$
  select
    id,
    fabricante,
    modelo,
    potencia_w,
    temperatura_cor_k,
    tensao_v,
    ip,
    classe_nbr,
    tecnologia,
    foto_url,
    descricao
  from public.equipamentos_modelo
  where ativo = true
  order by fabricante, modelo;
$$;

-- RPC: Obter modelo por ID
create or replace function ip_obter_modelo(p_id uuid)
returns table (
  id uuid,
  fabricante text,
  modelo text,
  potencia_w integer,
  temperatura_cor_k integer,
  tensao_v integer,
  ip text,
  classe_nbr text,
  tecnologia text,
  foto_url text,
  descricao text
) language sql stable as $$
  select
    id,
    fabricante,
    modelo,
    potencia_w,
    temperatura_cor_k,
    tensao_v,
    ip,
    classe_nbr,
    tecnologia,
    foto_url,
    descricao
  from public.equipamentos_modelo
  where id = p_id and ativo = true;
$$;

-- RPC: Criar novo modelo (admin only)
create or replace function ip_criar_modelo(
  p_fabricante text,
  p_modelo text,
  p_potencia_w integer,
  p_temperatura_cor_k integer default null,
  p_tensao_v integer default null,
  p_ip text default null,
  p_classe_nbr text default null,
  p_tecnologia text default 'LED',
  p_foto_url text default null,
  p_descricao text default null
)
returns uuid language plpgsql as $$
declare
  v_id uuid;
begin
  insert into public.equipamentos_modelo (
    fabricante, modelo, potencia_w,
    temperatura_cor_k, tensao_v, ip,
    classe_nbr, tecnologia, foto_url,
    descricao, created_by
  ) values (
    p_fabricante, p_modelo, p_potencia_w,
    p_temperatura_cor_k, p_tensao_v, p_ip,
    p_classe_nbr, p_tecnologia, p_foto_url,
    p_descricao, auth.uid()
  )
  returning id into v_id;
  return v_id;
end;
$$;

-- RPC: Atualizar modelo (admin only)
create or replace function ip_atualizar_modelo(
  p_id uuid,
  p_fabricante text default null,
  p_modelo text default null,
  p_potencia_w integer default null,
  p_temperatura_cor_k integer default null,
  p_tensao_v integer default null,
  p_ip text default null,
  p_classe_nbr text default null,
  p_tecnologia text default null,
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
    tensao_v = coalesce(p_tensao_v, tensao_v),
    ip = coalesce(p_ip, ip),
    classe_nbr = coalesce(p_classe_nbr, classe_nbr),
    tecnologia = coalesce(p_tecnologia, tecnologia),
    foto_url = coalesce(p_foto_url, foto_url),
    descricao = coalesce(p_descricao, descricao),
    updated_at = now()
  where id = p_id;

  return found;
end;
$$;

-- RPC: Deletar modelo (admin only - soft delete)
create or replace function ip_deletar_modelo(p_id uuid)
returns boolean language plpgsql as $$
begin
  update public.equipamentos_modelo
  set ativo = false, updated_at = now()
  where id = p_id;

  return found;
end;
$$;
