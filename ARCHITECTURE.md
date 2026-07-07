# Arquitetura - Iluminação LED Niterói

Documentação técnica da arquitetura, fluxos de dados e componentes do sistema.

## 🏗️ Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────┐
│              FRONTEND (SPA - Netlify)                   │
│  ┌───────────────────────────────────────────────────┐  │
│  │  index.html (1.125 linhas, HTML5 + Vanilla JS)   │  │
│  │                                                   │  │
│  │  📍 Leaflet 1.9.4 — Mapas interativos            │  │
│  │  📊 jsPDF 2.5.1 — Relatórios em PDF              │  │
│  │  🔐 Supabase JS 2.x — Cliente de backend         │  │
│  │                                                   │  │
│  │  State Management:                               │  │
│  │  • state object centralizado (global)            │  │
│  │  • Sem frameworks (React/Vue/etc)                │  │
│  │  • Comunicação via eventos (map.on, etc)         │  │
│  └───────────────────────────────────────────────────┘  │
│                                                          │
│  🎨 UI Components:                                      │
│  • Mapa interativo (Leaflet)                           │
│  • Painel de detalhe (right sidebar)                   │
│  • Estatísticas (left sidebar)                         │
│  • Filtros (popup)                                     │
│  • Tabela paginada (modal)                             │
│  • Admin console (full-screen)                         │
│                                                          │
│  🔑 Autenticação:                                       │
│  • Email/Password (Supabase Auth)                      │
│  • JWT token no localStorage                          │
│  • 3 Roles: leitura, editor, admin                     │
└─────────────────────────────────────────────────────────┘
                           │
                    (RPC + REST API)
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│        BACKEND (Supabase Cloud)                         │
│  ┌───────────────────────────────────────────────────┐  │
│  │  PostgreSQL Database (14+)                        │  │
│  │  • Tables: v_parque_export, profiles, ...         │  │
│  │  • RPC Functions: 16+ ip_* functions              │  │
│  │  • Row-Level Security: policies por role          │  │
│  │                                                   │  │
│  │  Principais Tabelas:                             │  │
│  │  ├─ v_parque_export — View de leitura (pontos)  │  │
│  │  ├─ profiles — Usuários e roles                  │  │
│  │  ├─ site_config — Configuração visual            │  │
│  │  └─ [audit_logs] — Histórico de alterações       │  │
│  └───────────────────────────────────────────────────┘  │
│                                                          │
│  🔐 Authentication (Supabase Auth)                      │
│  ├─ Email/Password strategy                            │
│  ├─ JWT tokens (TTL: 3600s)                            │
│  ├─ Refresh tokens para sessão persistente             │
│  └─ Role-based access control (RBAC)                   │
│                                                          │
│  💾 Storage                                             │
│  └─ Bucket "branding" — logos, imagens                │
│                                                          │
│  🌐 PostgREST API                                       │
│  ├─ Direct SELECT/INSERT/UPDATE/DELETE                │
│  └─ RPC function calls                                │
└─────────────────────────────────────────────────────────┘
```

## 🔄 Fluxos Principais

### 1. Visualização de Mapa (Inicial & Navegação)

```
Usuário abre site
    ↓
loadConfig() — busca configuração visual
    ↓
loadBairroOptions() — popula dropdown de bairros
    ↓
loadStatsChips() — carrega KPIs (% LED, média potência, etc)
    ↓
map.on('moveend', refresh) — setup listener
    ↓
refresh = debounce(_refresh, 120ms)
    ↓
_refresh() — lógica de renderização
    ├─ if zoom >= 16:
    │    └─ RPC 'ip_pontos_bbox' — pontos individuais
    │         └─ Renderizar marcadores
    │
    └─ if zoom < 16:
         └─ RPC 'ip_clusters_grid' — clusters gridificados
              └─ Renderizar círculos com contagem

Usuário pan/zoom
    ↓
map.on('moveend') dispara
    ↓
refresh() chamada (debounced)
    ↓
_refresh() re-executa com novas coordenadas
    ↓
UI atualizada
```

### 2. Edição de Ponto

```
Usuário clica em marcador
    ↓
openDetail(ponto)
    ├─ Renderiza painel direito
    ├─ Mostra dados atuais
    ├─ RPC 'ip_intervencoes' — histórico de intervenções
    └─ RPC 'ip_historico_ponto' — auditoria de alterações

Usuário clica "Editar"
    ↓
Renderiza FORM com inputs
    ├─ Campo: tipo (select)
    ├─ Campo: potência (number)
    ├─ Campo: LED instalado (checkbox)
    ├─ Campo: mapa mini (para coordenadas)
    └─ Botões: Salvar, Cancelar

Usuário preencheFORM e clica "Salvar"
    ↓
Validação JavaScript local
    ├─ Tipo não vazio
    ├─ Potência > 0
    └─ Coordenadas válidas

RPC 'ip_atualizar_ponto' (transação)
    ├─ UPDATE ponto
    ├─ INSERT audit_log
    └─ Validação RLS

Backend retorna sucesso
    ↓
refresh() — atualiza mapa
    ↓
loadStatsChips() — atualiza KPIs
    ↓
Painel de detalhe fecha
    ↓
toast('Ponto atualizado com sucesso')
```

### 3. Criação de Novo Ponto

```
Usuário clica "Novo Ponto"
    ↓
Renderiza form vazio
    ├─ Mapa mini para pintar localização
    ├─ Campos: tipo, potência, LED, bairro
    └─ Botões: Criar, Cancelar

Usuário clica no mapa mini
    ↓
Coordenadas capturadas
    ↓
Usuário preenche form
    ↓
Clica "Criar"
    ↓
RPC 'ip_inserir_ponto' (transação)
    ├─ INSERT novo ponto
    ├─ INSERT audit_log ("created")
    ├─ Incrementar contadores
    └─ Retorna novo ID

Backend retorna sucesso
    ↓
state.current = novo ponto
    ↓
refresh() + loadStatsChips()
    ↓
Mapa atualizado com novo marcador
    ↓
Painel de detalhe exibe ponto novo
```

### 4. Filtros & Busca

```
Usuário altera filtro (bairro, tipo, estado, etc)
    ↓
state.bairro/tipo/estado/etc atualizado
    ↓
updateFCount() — atualiza contador de resultados
    ↓
loadStatsChips() — recarrega KPIs com filtro
    ↓
highlightBairro(bairro) — se filtrar por bairro
    ↓
refresh() chamada
    ↓
RPC com filtros aplicados
    ├─ ip_pontos_bbox(filtros)
    └─ Retorna apenas pontos que matchem

Renderização filtrada no mapa
```

### 5. Exportação de Dados

```
Usuário clica "Exportar"
    ↓
Modal aparece com opções
    ├─ CSV
    ├─ GeoJSON
    ├─ PNG (screenshot do mapa)
    └─ PDF (relatório estruturado)

Usuário seleciona formato
    ↓
Aplicar filtros ao RPC
    ↓
RPC retorna dados
    ↓
if CSV:
    └─ toCSV(dados) → conversion object[] → CSV string
         └─ download('export.csv', csv)

if GeoJSON:
    └─ toGeoJSON(dados) → conversion → GeoJSON
         └─ download('export.geojson', geojson)

if PNG:
    └─ map.getContainer() screenshot
         └─ download('mapa.png', image)

if PDF:
    └─ jsPDF + autotable
         ├─ Header: configuração, data
         ├─ Table: dados estruturados
         ├─ Gráficos: sparklines, estatísticas
         └─ download('relatorio.pdf', pdf)

Download iniciado no browser
```

### 6. Admin Console

```
Usuário com role='admin' clica "Configurações"
    ↓
Admin console abre (full-screen)
    ├─ Tab 1: Usuários
    │   ├─ Listar usuários (RPC 'ip_usuarios'?)
    │   ├─ Criar usuário (RPC admin-users)
    │   ├─ Editar role
    │   └─ Deletar usuário
    │
    ├─ Tab 2: Configuração Visual
    │   ├─ Título do site
    │   ├─ Cor principal
    │   ├─ Logo (upload → Storage)
    │   └─ Font (select)
    │       └─ applyConfig() atualiza UI
    │
    ├─ Tab 3: Fila de Auditoria
    │   ├─ RPC 'ip_qualidade_dado'
    │   └─ Lista de pontos pendentes de verificação
    │
    └─ Tab 4: Backups
        ├─ Botão para baixar backup
        └─ Histórico de backups

UPDATE site_config (ou CREATE user, etc)
    ↓
RPC success
    ↓
loadConfig() re-executa
    ↓
applyConfig() aplica mudanças visuais
    ↓
toast('Configuração atualizada')
```

## 📊 Modelo de Dados

### Principais Tabelas/Views

#### v_parque_export (View)
```sql
-- View de leitura (SELECT only)
-- Baseada em tabelas internas (schema não exposte)
SELECT 
  id,                        -- uuid
  codigo_seconser,           -- string (código único)
  latitude, longitude,       -- float8
  tipo_ativo,                -- "luminaria" | "caixa" | ...
  tipo_luminaria,            -- "viaria" | "globo" | "sinaleira" | ...
  tipo_lampada,              -- "led" | "vapor_sodio" | "vapor_mercurio" | ...
  potencia,                  -- int (watts)
  led_instalado,             -- boolean
  data_ultima_intervencao,   -- date
  bairro_nome,               -- string
  bairro_id,                 -- uuid (foreign key)
  estado,                    -- "ativo" | "inativo" | "manutenção" | ...
  criado_em, atualizado_em,  -- timestamp
  -- ... (~35 colunas total)
FROM parque;                 -- tabela real interna
```

#### profiles (Table)
```sql
-- Autenticação e roles
CREATE TABLE profiles (
  id                uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  role              varchar(20) NOT NULL DEFAULT 'leitura',
                    -- "leitura" | "editor" | "admin"
  email             varchar(255),
  nome              varchar(255),
  ativo             boolean DEFAULT true,
  criado_em         timestamp DEFAULT now(),
  atualizado_em     timestamp DEFAULT now()
);

-- Row-Level Security Policies
-- SELECT: todos podem ler própis dados
-- UPDATE: admin pode editar qualquer um
-- DELETE: admin pode deletar
```

#### site_config (Table)
```sql
-- Configuração visual do site
CREATE TABLE site_config (
  id                int PRIMARY KEY DEFAULT 1,  -- sempre 1 (singleton)
  titulo            varchar(255) DEFAULT 'Iluminação LED Niterói',
  cor_principal     varchar(7) DEFAULT '#4CAF50',  -- hex color
  cor_secundaria    varchar(7) DEFAULT '#2196F3',
  logo_url          text,                         -- URL no Storage
  fonte             varchar(50) DEFAULT 'Roboto',
  atualizado_em     timestamp DEFAULT now()
);
```

#### [audit_logs] (Opcional - para rastreabilidade)
```sql
-- Histórico de alterações
CREATE TABLE audit_logs (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  ponto_id          uuid REFERENCES v_parque_export(id),
  usuario_id        uuid REFERENCES auth.users(id),
  acao              varchar(50),  -- "created" | "updated" | "deleted"
  dados_anteriores  jsonb,        -- snapshot antes
  dados_novos       jsonb,        -- snapshot depois
  criado_em         timestamp DEFAULT now()
);
```

### RPC Functions (PostgREST)

| Função | Parâmetros | Retorno | Descrição |
|--------|-----------|---------|-----------|
| `ip_pontos_bbox` | bbox (south, west, north, east), zoom, limite, filtros | GeoJSON | Pontos em bounding box com filtros |
| `ip_clusters_grid` | bbox, zoom, resolução | GeoJSON | Clusters gridificados |
| `ip_bairros_choropleth` | bbox | GeoJSON | Bairros com % LED colorido |
| `ip_grid_densidade` | bbox, métrica (fluxo/potência/eficiência) | GeoJSON | Grade 250m com densidade |
| `ip_atualizar_ponto` | id, tipo, potência, LED, estado, ... | {ok: bool, message: string} | Update + audit |
| `ip_inserir_ponto` | lat, lng, tipo, potência, LED, bairro | {id: uuid} | Insert + audit |
| `ip_intervencoes` | ponto_id | Array<intervencao> | Histórico de intervenções |
| `ip_registrar_intervencao` | ponto_id, tipo, descricao, data | {ok: bool} | Registra intervenção |
| `ip_historico_ponto` | ponto_id | Array<audit_log> | Histórico completo (audit) |
| `ip_estatisticas` | filtros | {total, led_pct, media_potencia, ...} | KPIs gerais |
| `ip_por_bairro` | filtros | Array<bairro_stats> | Agregação por bairro |
| `ip_serie_metricas` | metrica, data_inicio, data_fim | Array<{data, valor}> | Série temporal |
| `ip_grid_densidade` | sem GeoJSON | Array<grid_cell> | Dados para visualização |
| `ip_qualidade_dado` | (sem params) | Array<quality_issue> | Fila de verificação |
| `ip_bairro_geojson` | (sem params) | GeoJSON | Limites dos bairros |

## 🔐 Security & RLS

### Row-Level Security Policies

```sql
-- v_parque_export (leitura pública)
ALTER TABLE v_parque_export ENABLE ROW LEVEL SECURITY;

-- Política: todos podem ler
CREATE POLICY read_all ON v_parque_export
  FOR SELECT
  USING (true);

-- Política: apenas editor/admin podem editar
CREATE POLICY update_editor ON v_parque_export
  FOR UPDATE
  USING (auth.jwt() ->> 'role' IN ('editor', 'admin'))
  WITH CHECK (auth.jwt() ->> 'role' IN ('editor', 'admin'));

-- profiles (apenas admin)
CREATE POLICY admin_only ON profiles
  FOR ALL
  USING (auth.jwt() ->> 'role' = 'admin')
  WITH CHECK (auth.jwt() ->> 'role' = 'admin');
```

### Autenticação (JWT)

```javascript
// No frontend:
// 1. Login cria JWT token
const { data, error } = await sb.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'password'
});
// Token armazenado no localStorage (via Supabase)

// 2. Cada RPC call inclui JWT automaticamente
const { data } = await sb.rpc('ip_pontos_bbox', {...});
// Supabase valida JWT no backend

// 3. Backend extrai role do JWT
// SELECT * FROM profiles WHERE id = (JWT_PAYLOAD.sub)::uuid
```

### Input Validation

| Layer | Técnica |
|-------|---------|
| Frontend | HTML escaping via `esc()`, validação de inputs |
| Backend (RPC) | Validação no stored procedure, casting |
| Storage | Bucket policies |

## 📁 Estrutura de Arquivos

```
iluminacao-led-niteroi/
├── index.html                    # SPA principal (1.125 linhas)
├── netlify.toml                  # Configuração Netlify
├── README.md                     # Documentação principal
├── ARCHITECTURE.md               # Este arquivo
├── TROUBLESHOOTING.md            # FAQ e troubleshooting
│
├── .env.example                  # Template de variáveis
├── .gitignore                    # Regras de versionamento
│
├── .github/
│   ├── workflows/
│   │   ├── ci.yml               # Linting, validação, security scan
│   │   └── backup.yml           # Backup automático diário
│   ├── pull_request_template.md # Template de PR
│   └── ISSUE_TEMPLATE/
│       ├── bug.md               # Template bug report
│       └── feature.md           # Template feature request
│
├── supabase/
│   ├── config.toml              # Configuração local (Docker)
│   ├── README.md                # Guia de setup Supabase local
│   ├── migrations/
│   │   ├── 20260707000000_initial_schema.sql
│   │   └── ... (migrations futuras)
│   ├── seed.sql                 # Dados de teste
│   └── .gitkeep
│
└── scripts/
    ├── backup.sh                # Backup manual
    ├── restore.sh               # Restore manual
    └── .gitkeep
```

## 🚀 Stack Tecnológico

| Camada | Tecnologia | Versão | Propósito |
|--------|-----------|--------|-----------|
| **Hospedagem** | Netlify | Latest | Deploy automático, CDN |
| **Frontend** | HTML5 | ES6+ | SPA estrutura e UI |
| **Mapas** | Leaflet | 1.9.4 | Renderização interativa georreferenciada |
| **Relatórios** | jsPDF + autotable | 2.5.1 + 3.8.2 | Exportação PDF estruturada |
| **Backend** | Supabase | 2.x | PostgreSQL + Auth + Storage |
| **Database** | PostgreSQL | 14+ | Dados georreferenciados (PostGIS implícito) |
| **Autenticação** | Supabase Auth | JWT | Email/password, RBAC |
| **Storage** | Supabase Storage | - | Logos, imagens |
| **Versionamento** | Git | 2.x | Controle de versão |

## 🔍 Performance & Otimizações

### Frontend

- **Debounce:** `refresh()` debounced 120ms ao fazer pan/zoom (evita requisições excessivas)
- **Cache:** `state.tCache` armazena dados da tabela (reutilização)
- **Lazy loading:** Dados carregados conforme necessário (on-demand)
- **CDN:** Todas bibliotecas via CDN (sem bundler local)

### Backend

- **Indexes:** Críticos em `latitude`, `longitude`, `bairro_id`, `tipo_ativo`
- **Views Materializadas:** `v_parque_export` pode ser materializada se muitos dados
- **Connection Pooling:** Supabase gerencia automaticamente
- **RLS:** Policies compiladas (sem overhead significativo)

## 🛠️ Desenvolvimento & Deploy

### Local

```bash
# 1. Frontend
npx http-server
# http://localhost:8080

# 2. Backend
supabase start
# http://localhost:54321
```

### Produção

```bash
# Push para main
git push origin main

# Netlify redeploya automaticamente
# 1-2 min para estar online
```

## 📚 Referências

- [Leaflet Documentation](https://leafletjs.com/)
- [Supabase Reference](https://supabase.com/docs)
- [PostgreSQL PostGIS](https://postgis.net/)
- [Conventional Commits](https://www.conventionalcommits.org/)

---

**Última atualização:** 2026-07-07  
**Mantido por:** [@danilosfvalim](https://github.com/danilosfvalim)
