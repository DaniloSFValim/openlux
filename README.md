# Iluminação LED Niterói 💡

[![E2E Tests](https://github.com/DaniloSFValim/iluminacao-led-niteroi/actions/workflows/e2e-tests.yml/badge.svg?branch=main)](https://github.com/DaniloSFValim/iluminacao-led-niteroi/actions/workflows/e2e-tests.yml)
[![Lighthouse CI](https://github.com/DaniloSFValim/iluminacao-led-niteroi/actions/workflows/lighthouse-ci.yml/badge.svg?branch=main)](https://github.com/DaniloSFValim/iluminacao-led-niteroi/actions/workflows/lighthouse-ci.yml)
[![Security Scanning](https://github.com/DaniloSFValim/iluminacao-led-niteroi/actions/workflows/security-scan.yml/badge.svg?branch=main)](https://github.com/DaniloSFValim/iluminacao-led-niteroi/actions/workflows/security-scan.yml)
[![API Tests](https://github.com/DaniloSFValim/iluminacao-led-niteroi/actions/workflows/api-testing.yml/badge.svg?branch=main)](https://github.com/DaniloSFValim/iluminacao-led-niteroi/actions/workflows/api-testing.yml)
[![Netlify Status](https://api.netlify.com/api/v1/badges/8e1c5730-5e9e-4c8b-82f1-a1b1c2d3e4f5/deploy-status)](https://app.netlify.com/projects/iluminacao-niteroi)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-%23FE5196?logo=conventionalcommits&logoColor=white)](https://www.conventionalcommits.org)

Sistema georreferenciado de gestão de infraestrutura de iluminação pública da cidade de Niterói.

## 📊 Visão Geral

- **Descrição:** Sistema web para visualizar, gerenciar e auditar a infraestrutura de iluminação pública
- **Stack:** Leaflet (mapas) + Supabase (backend) + Netlify (hospedagem)
- **Usuários:** Técnicos de campo, editores, administradores
- **Funcionalidades:** Mapa interativo, edição de pontos, exportação de dados, relatórios, auditoria

## 🏗️ Arquitetura

### Frontend (Cliente)
- **Tipo:** Single-page application (SPA)
- **Tecnologia:** HTML5 + JavaScript vanilla (ES6+)
- **Dependências via CDN:**
  - Leaflet 1.9.4 — mapas interativos
  - Supabase JS 2.x — cliente backend
  - jsPDF 2.5.1 + autotable 3.8.2 — geração de relatórios PDF
- **Estado:** Object `state` centralizado (filtros, seleção, cache)
- **Autenticação:** Supabase Auth (email/password)
- **Roles:** `leitura` | `editor` | `admin`

### Backend (Supabase)
- **Database:** PostgreSQL 14+
- **API:** PostgREST (RPC functions)
- **Autenticação:** Supabase Auth com JWT
- **Storage:** Bucket `branding` para logos/configuração visual
- **Security:** Row-Level Security (RLS) por role
- **RPC Functions:** 16+ funções para operações georreferenciadas

### Deploy
- **Frontend:** Netlify (arquivos estáticos, deploy automático)
- **Backend:** Supabase Cloud
- **Build:** Zero — arquivos estáticos, nenhum build step necessário
- **Headers de Segurança:** X-Frame-Options: SAMEORIGIN, X-Content-Type-Options: nosniff

### Fluxos Críticos
1. **Visualização:** Mapa interativo com renderização zoom-dependent (pontos < zoom 16, clusters >= zoom 16)
2. **Edição:** Seleção de ponto → form → RPC `ip_atualizar_ponto` → refresh automático
3. **Exportação:** Aplicar filtros → RPC com filtros → toCSV/toGeoJSON/toPDF → download
4. **Admin:** Gestão de usuários, configuração visual, visualização de filas de auditoria

## 🚀 Setup Local

### Pré-requisitos
- Node.js 18+ (apenas para Supabase CLI)
- Git
- Docker & Docker Compose (para Supabase local)
- Editor de código (VS Code recomendado)
- Terminal bash/zsh

### 1️⃣ Frontend Local

```bash
git clone https://github.com/danilosfvalim/iluminacao-led-niteroi.git
cd iluminacao-led-niteroi

# Não há build step — servidor estático é suficiente
# Opção A: Usar http-server (recomendado para desenvolvimento)
npx http-server
# Acessar http://localhost:8080

# Opção B: Abrir index.html diretamente (sem live reload)
open index.html

# Opção C: VS Code Live Server
# Instalar extensão "Live Server" e clicar "Go Live"
```

### 2️⃣ Supabase Local

Supabase local permite desenvolvimento offline e testes sem afetar produção.

```bash
# Instalar CLI (primeira vez)
npm install -g supabase

# Inicializar projeto (primeira vez)
cd supabase
supabase init
# Isso cria config.toml

# Iniciar stack (Docker necessário)
supabase start

# Output será similar a:
# API URL: http://localhost:54321
# Anon Key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
# Service Role Key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
# Database URL: postgresql://postgres:postgres@localhost:54322/postgres

# Verificar status
supabase status

# Parar stack
supabase stop
```

### 3️⃣ Configurar Variáveis de Ambiente

```bash
# Criar arquivo local (não será commitado)
cp .env.example .env.local

# Editar com valores do Supabase local
nano .env.local

# Conteúdo (adaptar com valores reais):
NEXT_PUBLIC_SUPABASE_URL=http://localhost:54321
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGc...
```

### 4️⃣ Conectar Frontend ao Backend Local

O `index.html` detecta automaticamente:
- Se `window.location.hostname === 'localhost'` → busca credenciais em `.env.local`
- Se produção → usa credenciais hardcoded

**Para usar local:**
1. Adicionar `.env.local` com credenciais do Supabase local
2. Modificar `index.html` (linhas 260-262) para ler do `.env.local`

## 🔐 Variáveis de Ambiente

| Variável | Escopo | Descrição | Exemplo |
|----------|--------|-----------|---------|
| `NEXT_PUBLIC_SUPABASE_URL` | Public | URL da API Supabase | `https://lrnmydrwzxxajylsmoih.supabase.co` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Public | Anon key (seguro para frontend) | `sb_publishable_w3UmLsmcDtT81S3MDdDJjw_rEWckoVl` |
| `SUPABASE_SERVICE_ROLE_KEY` | Private | Admin key (nunca no frontend/git) | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` |
| `SUPABASE_LOCAL_URL` | Local | URL do Supabase local | `http://localhost:54321` |

**Armazenamento:**
- **Local:** `.env.local` (git-ignored)
- **Produção:** Netlify → Site Settings → Build & Deploy → Environment
- **CI/CD:** GitHub → Settings → Secrets and variables

## 📦 Deploy

### Deploy Frontend (Netlify)

1. Conectar repositório GitHub ao Netlify
2. Configurar build:
   - **Build command:** (deixar vazio)
   - **Publish directory:** `.` (raiz)
3. Variáveis de ambiente (Site Settings → Environment):
   ```
   NEXT_PUBLIC_SUPABASE_URL = https://lrnmydrwzxxajylsmoih.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY = sb_publishable_...
   ```
4. Deploy automático ao fazer push para `main`

### Deploy Backend (Supabase)

Supabase é gerenciado via dashboard web e migrations versionadas:

```bash
# Ver status do projeto
supabase projects list

# Fazer pull das mudanças remoto
supabase db pull --linked

# Fazer push de migrations locais
supabase db push --linked

# Ver logs de erro
supabase functions serve
```

## 🧪 Verificação End-to-End

### Checklist Local
- [ ] `supabase start` executa sem erro
- [ ] Abrir http://localhost:8080 e página carrega
- [ ] Login funciona com credenciais de teste
- [ ] Mapa renderiza com dados (pontos/clusters)
- [ ] Editar um ponto e salvamento funciona
- [ ] Exportar CSV/PDF funciona
- [ ] Filtros (bairro, tipo, estado) funcionam

### Checklist Produção
- [ ] `git push origin main` completa com sucesso
- [ ] Netlify mostra "Published" (2-3 min após push)
- [ ] Site carrega em https://seu-site.netlify.app
- [ ] Login com credenciais reais funciona
- [ ] Mapa renderiza com dados reais
- [ ] Edição e exportação funcionam

## 🔄 Backup & Restore

### Backup Automático

GitHub Actions executa backup diário (02:00 UTC):

```bash
# Ver backups
ls -lh backups/

# Backup é feito automaticamente via GitHub Actions
# Arquivos salvos em /backups/db_YYYY-MM-DD_HH-MM-SS.sql
```

### Restore Manual

```bash
# Listar backups disponíveis
ls -lh backups/

# Restaurar de um backup específico
./scripts/restore.sh backups/db_2026-07-07_14-30-00.sql

# Ou via Supabase local
supabase db reset
psql -f backups/db_2026-07-07_14-30-00.sql
```

## 📊 Observabilidade

### Logs & Debugging

| Camada | Ferramenta | Como Acessar |
|--------|-----------|--------------|
| **Frontend** | Browser DevTools | F12 → Console, Network, Sources |
| **Backend** | Supabase Dashboard | https://app.supabase.com → Logs |
| **Deploy** | Netlify Dashboard | https://app.netlify.com → Deploys → View logs |

### Monitoramento Recomendado (Futuro)

- **Sentry:** Error tracking e crash reports
- **LogRocket:** Session replay e debugging
- **Datadog:** APM e performance monitoring

## 🧱 Governança de Código

### Conventional Commits

Use mensagens estruturadas:

```bash
# Feature
git commit -m "feat: adicionar visualização de densidade"

# Bug fix
git commit -m "fix: corrigir renderização de clusters"

# Documentation
git commit -m "docs: atualizar guia de setup"

# Chore
git commit -m "chore: atualizar dependências CDN"

# Refactor
git commit -m "refactor: simplificar lógica de filtros"
```

### Branch Strategy

- `main` — produção (sempre estável, deploy automático)
- `develop` — staging
- `feature/*` — novas features (`feature/mapa-densidade`)
- `fix/*` — correções (`fix/cluster-zoom`)
- `docs/*` — documentação (`docs/setup-local`)

### Pull Request Workflow

1. Criar feature branch (`git checkout -b feature/meu-recurso`)
2. Fazer commits com Conventional Commits
3. Fazer push (`git push -u origin feature/meu-recurso`)
4. Abrir PR no GitHub
5. Preencher template de PR (descrição, testes, checklist)
6. Aguardar review + CI passar
7. Merge via GitHub (GitHub faz o rebase automático)

## 🆘 Plano de Recuperação

### Cenário 1: Perda Total do Supabase Produção

**Tempo de Recuperação:** 15-30 minutos

```bash
# 1. Restaurar dados do backup
supabase db reset --linked
psql -f backups/db_<latest>.sql

# 2. Verificar schema
supabase db pull --linked
git status  # revisar migrations em supabase/migrations/

# 3. Recriar usuários (se necessário)
# Via Supabase Dashboard → Auth → Users

# 4. Frontend já está correto (Netlify pull automático)
# Apenas limpar cache e aguardar DNS

# 5. Validar
# - Login funciona
# - Mapa carrega dados
# - Edição funciona
# - Exportação funciona
```

### Cenário 2: Código Corrompido no Git

**Tempo de Recuperação:** 2 minutos

```bash
# Ver histórico
git log --oneline -20

# Revert commit específico
git revert <commit-id>
git push origin main

# Ou reset (cuidado com força)
git reset --hard <commit-id>
git push --force-with-lease origin main
```

### Cenário 3: Netlify Deploy Quebrado

**Tempo de Recuperação:** 3 minutos

```bash
# Opção A: Trigger rebuild no dashboard
# Ir em app.netlify.com → seu site → Deploys → Trigger deploy

# Opção B: Push corrigido
git push origin main
# Netlify rebuilda automaticamente em 1-2 min

# Ver logs de erro
# app.netlify.com → Deploy logs → ver erro específico
```

## 📚 Documentação Adicional

- **[ARCHITECTURE.md](./ARCHITECTURE.md)** — Diagramas, fluxos de dados, modelo de dados
- **[TROUBLESHOOTING.md](./TROUBLESHOOTING.md)** — FAQ e soluções para 20+ problemas comuns
- **[supabase/README.md](./supabase/README.md)** — Guia de Supabase local, migrations, seed

## 🔗 Links Úteis

- **GitHub:** https://github.com/danilosfvalim/iluminacao-led-niteroi
- **Netlify Dashboard:** https://app.netlify.com
- **Supabase Dashboard:** https://app.supabase.com
- **Leaflet Documentation:** https://leafletjs.com
- **Supabase JS Client:** https://supabase.com/docs/reference/javascript

## ❓ FAQ

**P: Como adicionar novo usuário?**  
R: Via Supabase Dashboard → Authentication → Users → Add user. Depois criar perfil em `profiles` com role.

**P: Como mudar configuração visual (título, cor, logo)?**  
R: Opção A (UI): Admin console no site → "Configurações"  
   Opção B (SQL): `UPDATE site_config SET titulo='Novo Título' WHERE id=1;`

**P: Como restaurar dados de um backup?**  
R: Ver seção "Backup & Restore" acima. Execute: `./scripts/restore.sh backups/db_*.sql`

**P: Posso rodar frontend e backend em máquinas diferentes?**  
R: Sim! Frontend é SPA estática. Apenas aponte URL remota do Supabase em `index.html` (linhas 260-262).

**P: Supabase local está muito lento ou travado?**  
R: Tente: `supabase stop && supabase start --force-pull`. Se persistir, verificar espaço em disco e Docker.

**P: Como debugar problemas de Row-Level Security (RLS)?**  
R: 
1. Supabase Dashboard → SQL Editor
2. Verificar policies da tabela: `SELECT * FROM pg_policies WHERE tablename='v_parque_export';`
3. Verificar role do usuário: `SELECT role FROM profiles WHERE id = auth.uid();`
4. Testar query com `EXPLAIN ANALYZE`

**P: Posso usar este código em outro município?**  
R: Sim! Código é agnóstico ao município. Adapte: URLs Supabase, bounds do mapa (Niterói: -23.03 a -22.80 lat, -43.20 a -42.90 lng), dados de entrada.

## 📝 Licença

[A definir — adicionar licença do projeto]

## 👥 Contribuindo

Veja [CONTRIBUTING.md](./CONTRIBUTING.md) para guidelines de contribuição.

---

**Última atualização:** 2026-07-07  
**Versão:** 1.0.0  
**Mantido por:** [@danilosfvalim](https://github.com/danilosfvalim)
