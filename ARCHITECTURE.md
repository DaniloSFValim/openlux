# Arquitetura - Iluminação LED Niterói

## 🏗️ Diagrama de Componentes

```
┌─────────────────────────────────────────────┐
│           FRONTEND (SPA - Netlify)          │
│  ┌───────────────────────────────────────┐  │
│  │  index.html (1.125 linhas)            │  │
│  │  - Leaflet (Mapas)                    │  │
│  │  - jsPDF (Relatórios)                 │  │
│  │  - State object centralizado          │  │
│  │  - Autenticação Supabase              │  │
│  │  - Tailwind CSS + Alpine.js + HTMX    │  │
│  └───────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
                      │
                      │ RPC Calls
                      │
┌─────────────────────────────────────────────┐
│         BACKEND (Supabase Cloud)            │
│  ┌───────────────────────────────────────┐  │
│  │  PostgreSQL Database                  │  │
│  │  - Tables: v_parque_export, profiles  │  │
│  │  - RPC Functions (ip_*)               │  │
│  │  - Row Level Security (RLS)           │  │
│  │  - Audit logging                      │  │
│  └───────────────────────────────────────┘  │
│  ┌───────────────────────────────────────┐  │
│  │  Authentication                       │  │
│  │  - Supabase Auth (email/password)     │  │
│  │  - 3 Roles: leitura, editor, admin    │  │
│  │  - Password leak protection           │  │
│  └───────────────────────────────────────┘  │
│  ┌───────────────────────────────────────┐  │
│  │  Storage                              │  │
│  │  - Bucket: branding (logos)           │  │
│  └───────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

## 🔄 Fluxos Principais

### 1. Visualização de Mapa
```
Usuário navega mapa
  ↓
map.on('moveend') dispara
  ↓
refresh() (debounced 120ms)
  ↓
_refresh() verifica zoom
  ↓
Se zoom >= 16: RPC 'ip_pontos_bbox' (pontos individuais)
Se zoom < 16: RPC 'ip_clusters_grid' (clusters)
  ↓
state.layer atualizado com marcadores/clusters
  ↓
Renderização Leaflet
```

### 2. Edição de Ponto
```
Clique no marcador
  ↓
openDetail(ponto)
  ↓
Renderiza painel direito com dados atuais
  ↓
Clique "Editar" → form com inputs
  ↓
Clique "Salvar"
  ↓
RPC 'ip_atualizar_ponto'
  ↓
refresh() + loadStatsChips()
  ↓
UI atualizada
```

### 3. Exportação de Dados
```
Clique "Exportar CSV"
  ↓
Aplicar filtros (bairro, tipo, estado, etc)
  ↓
RPC com filtros
  ↓
toCSV() converte dados
  ↓
download() salva arquivo
```

### 4. Filtros Dinâmicos (HTMX)
```
Usuário seleciona Bairro
  ↓
HTMX dispara hx-get para /api/v1/tipos-por-bairro
  ↓
Fetch interceptor retorna HTML com opções de Tipo
  ↓
HTMX atualiza dropdown de Tipo
  ↓
state.bairro, state.tipo sincronizados
  ↓
Mapa re-renderiza com novos filtros
```

## 📊 Modelo de Dados (simplificado)

### Tabelas Principais

**v_parque_export** (View - leitura de pontos)
```
- id: uuid
- codigo_seconser: string
- latitude, longitude: float
- tipo_ativo: "luminaria" | "caixa"
- tipo_luminaria: "viaria" | "globo" | etc
- potencia: int
- led_instalado: boolean
- data_ultima_intervencao: date
- bairro_nome: string
- ... (35+ colunas)
```

**profiles** (Autenticação)
```
- id: uuid (foreign key → auth.users)
- role: "leitura" | "editor" | "admin"
- criado_em: timestamp
```

**audit_log** (Compliance)
```
- id: bigserial
- user_id: uuid
- action: string
- table_name: string
- changes: jsonb
- created_at: timestamp
```

**site_config** (Configuração)
```
- id: int (sempre 1)
- titulo: string
- cor_principal: string (hex)
- logo_url: string
- fonte: string
- ... (configurações visuais)
```

## 🔐 Security

### Row Level Security (RLS)
- Tabelas com policies por role
- Usuarios 'leitura' veem todos dados
- Usuarios 'editor' podem editar com restrictions
- Usuarios 'admin' acesso total + gestão

### Autenticação
- Supabase Auth handles JWT
- Cookies HTTP-only (automático)
- PKCE flow para SPA
- Password leak protection (manual setup required)

### Inputs
- Escape HTML em todos `.innerHTML` (função `esc()`)
- RPC validação no Supabase (stored procedures)
- Sem SQL injection risk (PostgREST)
- HTTPS obrigatório em produção

## 📁 Estrutura de Arquivos

```
openlux/
├── index.html              (Aplicação principal SPA)
├── index-poc-working.html  (POC com modernizações)
├── netlify.toml            (Configuração deploy Netlify)
├── .env.example            (Template de env)
├── .gitignore              (Git ignorar)
├── README.md               (Este arquivo)
├── ARCHITECTURE.md         (Documentação arquitetura)
├── TROUBLESHOOTING.md      (FAQ e soluções)
├── .github/
│   ├── workflows/
│   │   ├── ci.yml         (Linting, validação)
│   │   └── backup.yml     (Backup automático)
│   ├── pull_request_template.md
│   └── ISSUE_TEMPLATE/
│       ├── bug.md
│       └── feature.md
├── supabase/
│   ├── config.toml        (Config local)
│   ├── README.md          (Guia Supabase)
│   ├── migrations/        (Versioned schema)
│   │   ├── 00000000000001_initial_schema.sql
│   │   ├── 00000000000002_add_audit_tables.sql
│   │   └── 20260708_security_hardening_phase_1.sql
│   ├── seed.sql           (Dados teste)
│   └── functions/         (Edge functions)
└── scripts/
    ├── backup.sh          (Backup manual)
    ├── restore.sh         (Restore manual)
    └── backups/           (Diretório de backups)
        └── db_*.sql
```

## 🚀 Stack Tecnológico

| Layer | Tecnologia | Versão |
|-------|-----------|--------|
| Hospedagem Frontend | Netlify | Latest |
| Frontend | HTML5 + Vanilla JS | ES6+ |
| Mapas | Leaflet | 1.9.4 |
| Styling | Tailwind CSS | Latest (CDN) |
| Interatividade | Alpine.js | Latest (CDN) |
| Dinâmica | HTMX | Latest (CDN) |
| Relatórios | jsPDF + autotable | 2.5.1 + 3.8.2 |
| Backend | Supabase | 2.x |
| Database | PostgreSQL | 14+ |
| Auth | Supabase Auth | Built-in |
| Versionamento | Git | 2.x |
| CI/CD | GitHub Actions | Latest |
