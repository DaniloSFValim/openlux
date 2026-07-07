# Supabase Local Development

Guia para usar Supabase localmente com Docker e Supabase CLI.

## 🚀 Setup Inicial

### Pré-requisitos

- Node.js 18+ (para CLI)
- Docker & Docker Compose
- 4GB+ RAM disponível
- ~5GB espaço em disco

### 1. Instalar Supabase CLI

```bash
npm install -g supabase
# ou
brew install supabase/tap/supabase  # Mac
```

### 2. Inicializar Projeto (Primeira Vez)

```bash
cd supabase
supabase init

# Cria:
# - config.toml (configuração padrão)
# - migrations/ (diretório vazio para migrations)
# - functions/ (diretório para Edge Functions)
```

### 3. Iniciar Stack Local

```bash
supabase start

# Pode levar 2-3 min na primeira vez (Docker pull & build)

# Output será algo como:
# API URL: http://localhost:54321
# GraphQL URL: http://localhost:54321/graphql/v1
# DB URL: postgresql://postgres:postgres@localhost:54322/postgres
# Studio URL: http://localhost:54323
# Inbucket URL: http://localhost:54324
# Seed [secure_id]: <seed>
```

**Guardar URLs e keys — vão precisar para conectar frontend!**

### 4. Acessar Supabase Studio (Admin UI)

```
http://localhost:54323
```

Ali você pode:
- Ver e editar dados em tempo real
- Gerenciar usuários
- Criar/editar policies
- Executar SQL queries
- Ver logs

---

## 🔐 Credenciais Padrão

```
Banco de Dados (PostgreSQL):
  Host: localhost
  Port: 54322
  User: postgres
  Password: postgres
  Database: postgres

Supabase Client (Frontend):
  URL: http://localhost:54321
  Anon Key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9... (ver supabase start output)

Admin (Não usar no frontend):
  Service Role Key: eyJhbGc... (ver supabase start output)
```

Adicionar ao `.env.local`:
```bash
NEXT_PUBLIC_SUPABASE_URL=http://localhost:54321
NEXT_PUBLIC_SUPABASE_ANON_KEY=<anon_key_da_saída_acima>
```

---

## 📋 Migrations (Versionamento de Schema)

Migrations permitem versionar mudanças no banco de dados e sincronizar com produção.

### Listar Migrations

```bash
supabase migration list
```

### Criar Nova Migration

```bash
supabase migration new <nome_descritivo>

# Exemplos:
supabase migration new add_audit_table
supabase migration new add_rls_policies
supabase migration new create_indexes

# Cria arquivo em supabase/migrations/<timestamp>_<nome>.sql
```

### Editar e Aplicar

```bash
# Editar arquivo .sql que foi criado
nano supabase/migrations/20260707123456_add_audit_table.sql

# Ao salvar, Supabase local aplica automaticamente
# Ou aplicar manualmente:
supabase migration up
```

### Sincronizar com Produção

**Pull (trazer schema remoto para local):**
```bash
supabase db pull --linked

# Conecta ao Supabase produção
# Cria migration local com diffs
# Review e commit a migration nova
```

**Push (enviar migrations para remoto):**
```bash
supabase db push --linked

# Aplica todas migrations locais não-aplicadas
# ⚠️ Cuidado: pode deletar dados em produção!
# Sempre fazer backup primeiro
```

---

## 🌱 Seed Data (Dados de Teste)

Para popular banco local com dados de teste.

### Arquivo seed.sql

Editar `seed.sql` com INSERT statements:

```sql
-- Exemplo: criar usuários de teste
INSERT INTO auth.users (id, email, encrypted_password, confirmed_at)
VALUES 
  ('00000000-0000-0000-0000-000000000001', 'teste@example.com', 'hashed_password', now()),
  ('00000000-0000-0000-0000-000000000002', 'admin@example.com', 'hashed_password', now());

INSERT INTO public.profiles (id, role, email)
VALUES 
  ('00000000-0000-0000-0000-000000000001', 'editor', 'teste@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'admin', 'admin@example.com');

-- Exemplo: dados de teste para tabela parque
INSERT INTO public.parque (id, tipo_ativo, tipo_luminaria, potencia, led_instalado, latitude, longitude)
VALUES 
  (gen_random_uuid(), 'luminaria', 'viaria', 150, true, -22.905, -43.055),
  (gen_random_uuid(), 'luminaria', 'globo', 250, false, -22.910, -43.050),
  (gen_random_uuid(), 'caixa', 'viaria', 400, true, -22.900, -43.060);
```

### Executar Seed

```bash
# Modo automático (ao fazer supabase start)
# Se descomentar nos scripts do config.toml

# Modo manual:
supabase seed run

# Ou via psql direto:
psql $DATABASE_URL -f seed.sql
```

---

## 🛠️ Comandos Úteis

### Status & Info

```bash
# Ver status da stack
supabase status

# Ver logs (útil para debug)
supabase logs --all
supabase logs supabase_db_1
supabase logs supabase_rest_1

# Ver config
supabase projects list
```

### Parar & Reiniciar

```bash
# Parar (dados permanecem)
supabase stop

# Reiniciar
supabase start

# Parar e deletar dados
supabase stop --no-backup

# Força re-sincronização (pull remoto inteiro)
supabase start --force-pull
```

### Database

```bash
# Conectar direto ao PostgreSQL local
psql postgresql://postgres:postgres@localhost:54322/postgres

# Ver tabelas
\dt

# Ver policies
\dP

# Sair
\q
```

---

## 🔄 Workflow Típico

### Desenvolvimento de Feature

```bash
# 1. Criar migration
supabase migration new add_new_feature

# 2. Escrever SQL na migration
nano supabase/migrations/20260707_add_new_feature.sql

# 3. Aplicar localmente (automático ou manual)
supabase migration up

# 4. Testar no Studio
http://localhost:54323

# 5. Conectar frontend
# Frontend pega dados via RPC/SELECT

# 6. Quando ready, enviar para produção
git add supabase/migrations/
git commit -m "feat: add new feature"
git push origin feature/branch

# 7. Depois do merge, fazer push para produção
supabase db push --linked  # ⚠️ Produção!
```

### Sincronizar Com Produção

```bash
# 1. Garantir que está no commit correto
git status  # deve estar clean

# 2. Pull schema remoto
supabase db pull --linked

# 3. Revisar migration criada
git diff supabase/migrations/

# 4. Testar localmente
supabase start
# ... testes ...

# 5. Commitar migration
git add supabase/migrations/
git commit -m "chore: sync with production schema"
git push
```

---

## 🐛 Troubleshooting

### Docker não inicia

```bash
# Ver logs
docker logs supabase_db_1

# Reiniciar Docker
docker restart supabase_db_1

# Reset completo
supabase stop
docker system prune
supabase start --force-pull
```

### Porta em uso

```bash
# Ver processo
lsof -i :54321

# Matar
kill -9 <PID>

# Ou mudar em config.toml
[api]
port = 54325  # mudar para porta diferente
```

### Seed não funciona

```bash
# Verificar sintaxe
psql postgresql://postgres:postgres@localhost:54322/postgres -f seed.sql

# Ver erros específicos
supabase seed run  # vê output
```

### Dados não sincronizam com produção

```bash
# Pull remoto
supabase db pull --linked

# Revisar quais migrations faltam
supabase migration list

# Aplicar
supabase migration up
```

---

## 📚 Referências

- [Supabase Local Development](https://supabase.com/docs/guides/local-development)
- [Supabase CLI](https://supabase.com/docs/reference/cli/introduction)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [PostgREST Documentation](https://postgrest.org/en/stable/)

---

**Última atualização:** 2026-07-07
