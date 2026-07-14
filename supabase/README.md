# Supabase Local Setup

Guia para configurar e gerenciar Supabase localmente.

## Pré-requisitos

- Docker & Docker Compose instalados
- Supabase CLI: `npm install -g supabase`
- Node.js 18+

## Inicializar Projeto Local

### 1. Primeira Vez

```bash
cd supabase
supabase init  # Cria config.toml
```

### 2. Iniciar Stack

```bash
supabase start

# Output exemplo:
# API URL: http://localhost:54321
# Anon Key: eyJ...
# Service Role Key: eyJ...
# Database URL: postgresql://postgres:postgres@localhost:54322/postgres
```

### 3. Verificar Status

```bash
supabase status
```

### 4. Parar Stack

```bash
supabase stop
```

## Migrations

### Listar Migrations

```bash
supabase migration list
```

### Criar Nova Migration

```bash
supabase migration new add_audit_table
# Editar: supabase/migrations/20260709123456_add_audit_table.sql
```

### Aplicar Migrations

```bash
supabase migration up
# Ou automático ao fazer supabase start
```

### Pull Schema do Remoto

```bash
# Sincronizar com Supabase produção
supabase db pull --linked
# Cria migration nova com diffs
```

## Seeding (Dados de Teste)

### Executar Seed

```bash
supabase seed run
# Executa seed.sql
```

### Editar Seed

Editar `seed.sql` com dados de teste:

```sql
INSERT INTO profiles (id, role) VALUES
  ('user-1-uuid', 'leitura'),
  ('user-2-uuid', 'editor'),
  ('user-3-uuid', 'admin');
```

## Troubleshooting

### Docker não inicia

```bash
docker ps
docker logs supabase_db_1
```

### Porta já em uso

```bash
# Mudar port em config.toml
[api]
port = 54321  # Mudar para outro número
```

### Reset completo

```bash
supabase stop
supabase start --force-pull
```
