<div align="center">

# 💡 OpenLux

### Plataforma aberta de gestão de iluminação pública

**Inventário vivo, georreferenciado e versionado do parque de iluminação — para
qualquer cidade.** Mapa público, edição em campo, fotometria de instalação, análise
espacial e auditoria completa. Código MIT; os dados pertencem a cada município.

*Open platform for public lighting asset management — born in Niterói, Brazil, built for any city.*

<br/>

[![Netlify Status](https://api.netlify.com/api/v1/badges/fad767e1-972b-40e7-995d-f0c38b287c8e/deploy-status)](https://app.netlify.com/projects/iluminacao-niteroi)
[![E2E Tests](https://github.com/DaniloSFValim/openlux/actions/workflows/e2e-tests.yml/badge.svg?branch=main)](https://github.com/DaniloSFValim/openlux/actions/workflows/e2e-tests.yml)
[![API Tests](https://github.com/DaniloSFValim/openlux/actions/workflows/api-testing.yml/badge.svg?branch=main)](https://github.com/DaniloSFValim/openlux/actions/workflows/api-testing.yml)
[![Lighthouse CI](https://github.com/DaniloSFValim/openlux/actions/workflows/lighthouse-ci.yml/badge.svg?branch=main)](https://github.com/DaniloSFValim/openlux/actions/workflows/lighthouse-ci.yml)
[![Security Scanning](https://github.com/DaniloSFValim/openlux/actions/workflows/security-scan.yml/badge.svg?branch=main)](https://github.com/DaniloSFValim/openlux/actions/workflows/security-scan.yml)

![JavaScript](https://img.shields.io/badge/JavaScript-Vanilla_ES6+-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
![Leaflet](https://img.shields.io/badge/Leaflet-1.9.4-199900?style=for-the-badge&logo=leaflet&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL_+_PostGIS-3FCF8E?style=for-the-badge&logo=supabase&logoColor=white)
![Netlify](https://img.shields.io/badge/Netlify-Deploy_cont%C3%ADnuo-00C7B7?style=for-the-badge&logo=netlify&logoColor=white)

[![DOI](https://img.shields.io/badge/DOI-10.5281%2Fzenodo.21305310-blue.svg?style=flat-square)](https://doi.org/10.5281/zenodo.21305310)
[![License: MIT](https://img.shields.io/badge/Licen%C3%A7a-MIT-yellow.svg?style=flat-square)](LICENSE)
[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-FE5196?style=flat-square&logo=conventionalcommits&logoColor=white)](https://www.conventionalcommits.org)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](CONTRIBUTING.md)

<br/>

**[🌍 Visão do projeto](VISION.md)** ·
**[🌐 Demo (Niterói)](https://iluminacao-niteroi.netlify.app)** ·
**[🏙️ Implante na sua cidade](docs/DEPLOY_YOUR_CITY.md)** ·
**[🐛 Reportar Bug](https://github.com/DaniloSFValim/openlux/issues/new?template=bug.md)**

</div>

---

## 🌍 A plataforma

Quase toda cidade gerencia sua iluminação pública com planilhas, sistemas
proprietários caros e **dados mortos** — um censo que envelhece no dia seguinte.
O OpenLux propõe outro paradigma, detalhado no **[documento de visão](VISION.md)**:

- **Dado vivo e versionado** — campanhas de levantamento sucessivas; cada ponto sabe a
  idade e a proveniência do seu dado; nada é apagado, tudo é camada.
- **Instalação, não só inventário** — índices fotométricos (aproveitamento no piso,
  poluição luminosa) calculados a partir de atributos baratos coletados em campo.
- **Aberto e expansível** — cidade é configuração, não código: consórcios regionais
  multi-tenant ou instâncias soberanas, com federação de indicadores no horizonte.

## 🧪 Niterói — implantação de referência

A plataforma é a generalização de um sistema **em produção** em Niterói/RJ
(SECONSER · Diretoria de Iluminação Pública), que serve de **laboratório**: cada
recurso é validado com dados e equipes reais antes de virar plataforma. O marco está
congelado e citável no DOI [10.5281/zenodo.21305310](https://doi.org/10.5281/zenodo.21305310).

<div align="center">

| 🔦 Pontos mapeados | 🏘️ Bairros | ✅ Modernizados LED | ⚡ Potência instalada | 📋 Histórico |
|:---:|:---:|:---:|:---:|:---:|
| **42.765** | **52** | **39%** | **~5,8 MW** | **85.000+ registros** |

</div>

Outras implantações: ver o **[registro de cidades](cities/README.md)**.

## ✨ Funcionalidades

<table>
<tr>
<td width="50%" valign="top">

### 🗺️ Mapa Inteligente
- Clustering dinâmico por zoom (grid geohash)
- 4 mapas-base (escuro, claro, ruas, satélite)
- Coroplético por bairro e grid de densidade
- 🔥 **Heat maps**: % LED, densidade e idade
- ✏️ **Seleção por área** (polígono): contagem, densidade, % LED e export só da região (PostGIS)

</td>
<td width="50%" valign="top">

### 🎯 Filtros Avançados
- Bairro, tipo de lâmpada, potência, status
- Faixas de % LED e watts (min/max)
- 📅 Timeline por período de modernização
- Saúde do ponto (verde/amarelo/vermelho)

</td>
</tr>
<tr>
<td width="50%" valign="top">

### ✏️ Gestão em Campo
- Cadastro de ativos direto no mapa
- Luminárias, postes, caixas, relés e braços
- Edição com fila de aprovação opcional
- 📸 Upload de foto com compressão automática

</td>
<td width="50%" valign="top">

### 📊 Dados & Conformidade
- Exportação CSV, GeoJSON e PDF
- Catálogo de modelos com **fotometria Tier 2** (lumens, lm/W, FP, THD, IK, DPS, arquivo .IES)
- Histórico completo de alterações por ponto
- Auditoria de intervenções

</td>
</tr>
</table>

## 🔐 Perfis de Acesso

| Papel | Visualizar | Criar/Editar pontos | Excluir | Administração |
|-------|:---:|:---:|:---:|:---:|
| 👁️ `leitura` | ✅ | — | — | — |
| ✏️ `editor` | ✅ | ✅ | — | Modelos |
| 🛡️ `admin` | ✅ | ✅ | ✅ | Usuários, branding, aprovações |

> O mapa é **público** (sem login). Escrita exige autenticação + papel — validado por RLS
> e por RPCs `SECURITY DEFINER` com verificação de papel no banco, nunca no cliente.

## 🏗️ Arquitetura

```mermaid
flowchart LR
    U(["👤 Usuário"]) --> SPA["🖥️ SPA<br/>index.html único<br/>Leaflet + JS vanilla"]

    subgraph Supabase ["☁️ Supabase (por cidade ou consórcio)"]
        DB[("🐘 PostgreSQL + PostGIS<br/>RPCs ip_* · RLS")]
        AUTH["🔑 Auth<br/>leitura · editor · admin"]
        STG["🗂️ Storage<br/>branding · fotos · .IES"]
    end

    SPA -- "RPC (PostgREST)" --> DB
    SPA --> AUTH
    SPA --> STG

    GH["📦 GitHub (main)"] -- "deploy automático" --> NF["🌐 Netlify<br/>publica somente dist/"]
    NF --> SPA
```

**Decisões de projeto:** zero build step, zero framework — um único `index.html` autocontido
com dependências via CDN. Toda a lógica de permissão vive no banco (RLS + RPCs).
Simplicidade que uma prefeitura pequena opera e uma universidade audita.

## 📐 Fotometria de Instalação (Tier 3)

> **Do inventário ao modelo de engenharia.** Além de registrar *o que* está instalado, a
> plataforma captura **como** e **onde** — transformando o cadastro em base para análise
> luminotécnica e **objeto de artigo científico**.

Cada luminária pode ser classificada por dois parâmetros de instalação, coletados em
**opções pré-definidas** (sem digitação livre) e convertidos em índices exibidos no painel:

| Parâmetro | Captura | Alimenta |
|---|---|---|
| 📐 **Ângulo de apontamento** (0°–120°, nadir) | dropdown pré-classificado | Aproveitamento no piso · *uplight* |
| 🧱 **Material do piso** (asfalto, concreto, água…) | dropdown com refletância ρ tabelada | Luminância percebida · luz refletida ao céu |

A partir deles, três indicadores de primeira ordem são calculados e mostrados por ponto:

<div align="center">

| Indicador | Fórmula | Significado |
|---|:---:|---|
| **Aproveitamento no piso** | `η = max(0, cos θ)` | fração do fluxo útil no solo |
| **Poluição luminosa** | `P = (1−η) + ρ·η·0,5` | *skyglow* direto + refletido |
| **Luminância relativa** | `L = η·ρ` | o que o olho percebe |

</div>

📖 **Modelo completo, fórmulas, refletâncias e referências normativas (ABNT NBR 5101, CIE
144/150, IESNA BUG):** [`docs/FIELD_REFERENCE_TIER3_PHOTOMETRY.md`](docs/FIELD_REFERENCE_TIER3_PHOTOMETRY.md)

## 🏙️ Implante na sua cidade

O OpenLux é feito para ser replicado: backend gratuito/baixo custo (Supabase),
hospedagem estática, base de pontos importada de censo/KML ou cadastrada em campo.
A implantação hoje é manual (~1 dia); o roadmap a leva a ~1 hora.

➡️ **[Guia: implante o OpenLux na sua cidade](docs/DEPLOY_YOUR_CITY.md)** ·
[registro de cidades](cities/README.md) · [governança](GOVERNANCE.md)

## 🚀 Rodando localmente (instância de referência)

### Pré-requisitos

- Qualquer servidor HTTP estático (ou só abrir o arquivo no navegador)
- Node.js 18+ apenas para rodar os testes

```bash
# 1. Clone o repositório
git clone https://github.com/DaniloSFValim/openlux.git
cd openlux

# 2. Sirva o index.html
npx http-server .
# → http://localhost:8080
```

> 💡 O app aponta para o Supabase de produção de Niterói via chave *publishable*
> (pública por design). Para um backend próprio, veja
> [`supabase/README.md`](supabase/README.md) e [`.env.example`](.env.example).

### Rodando os testes

```bash
npm install
npx playwright test        # E2E (26 testes)
```

## 🧪 Qualidade & CI/CD

| Workflow | O que faz | Quando roda |
|----------|-----------|-------------|
| ⚙️ **CI** | Validação de HTML e migrations | push / PR |
| 🎭 **E2E Tests** | 26 testes Playwright contra o deploy preview | PR |
| 🔌 **API Tests** | 9 requisições Newman/Postman contra os RPCs | PR |
| 🔦 **Lighthouse CI** | Auditoria de performance | PR |
| 🛡️ **Security Scan** | npm audit + análise estática | push / PR |
| 💾 **Backup** | Dump diário do banco | cron 02:00 UTC |

## 🗄️ Banco de Dados

O schema é versionado em [`supabase/migrations/`](supabase/migrations/) — **leia o
[README de migrations](supabase/migrations/README.md)** antes de qualquer mudança:
o banco de produção é a fonte de verdade e *merge de PR não aplica migration*.

<details>
<summary><b>📂 Estrutura do projeto</b></summary>

```
openlux/
├── index.html                  # 🎯 A aplicação inteira (SPA autocontida)
├── netlify.toml                # Deploy: publica somente dist/index.html
├── VISION.md                   # 🌍 Visão e roadmap da plataforma
├── GOVERNANCE.md               # Como o projeto decide
├── cities/                     # Registro público de implantações
├── supabase/
│   ├── migrations/             # Schema versionado (espelho do banco) + README
│   └── migrations_archive/     # Migrations legadas (NÃO executar)
├── tests/                      # E2E Playwright
├── scripts/                    # Backup & restore
├── docs/                       # Guias e referências (deploy, Tier 2/3, PI)
├── paper/                      # 📄 Artigo científico (PT/EN), dados e figuras
├── .github/workflows/          # 7 pipelines de CI/CD
├── ARCHITECTURE.md             # Arquitetura detalhada
├── DEPLOYMENT_GUIDE.md         # Guia de deploy passo a passo
├── TROUBLESHOOTING.md          # Soluções para problemas comuns
└── CHANGELOG.md                # Histórico de versões
```

</details>

## 🗺️ Roadmap

O roadmap completo, por fases, vive na **[visão](VISION.md#6-roadmap-por-fases)**. Resumo:

- [x] **Fase −1 · Laboratório** — sistema de Niterói completo em produção (v1.3.0, DOI)
- [x] **Fase 0 · Identidade** — visão, governança, registro de cidades (OpenLux)
- [x] **Fase 1 · Desacoplar** — cidade vira configuração (`config/cities/` + bloco `CITY`)
- [x] **Fase 2 · Recenseamento** — campanhas versionadas, estado herdado/verificado, filtro de campo no mapa
- [ ] **Fase 3 · Multi-cidade** — RLS por município, onboarding "nova cidade em 1 hora"
- [ ] **Fase 4 · Região** — painel agregado multi-cidade, PWA offline para campo
- [ ] **Fase 5 · Comunidade** — federação de instâncias, datasets abertos

Veja as [issues abertas](https://github.com/DaniloSFValim/openlux/issues) para a lista completa.

## 🤝 Contribuindo

Contribuições são bem-vindas! Leia a [governança](GOVERNANCE.md), o
[guia de contribuição](CONTRIBUTING.md) e o [código de conduta](CODE_OF_CONDUCT.md). Em resumo:

1. Faça um fork e crie sua branch: `git checkout -b feature/minha-feature`
2. Commit seguindo [Conventional Commits](https://www.conventionalcommits.org): `feat: adicionar X`
3. Abra um PR — os templates de [bug](.github/ISSUE_TEMPLATE/bug.md) e
   [feature](.github/ISSUE_TEMPLATE/feature.md) ajudam a padronizar

Vulnerabilidades de segurança: siga a [política de segurança](SECURITY.md) — **não** abra issue pública.

## 📚 Documentação

| Documento | Conteúdo |
|-----------|----------|
| [VISION.md](VISION.md) | 🌍 A visão da plataforma: tese, modelo de expansão, fases |
| [GOVERNANCE.md](GOVERNANCE.md) | Como o projeto decide; como cidades aderem |
| [docs/DEPLOY_YOUR_CITY.md](docs/DEPLOY_YOUR_CITY.md) | 🏙️ Implante o OpenLux na sua cidade |
| [cities/README.md](cities/README.md) | Registro público de implantações |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Diagramas, fluxos e modelo de dados |
| [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) | Deploy do zero (Netlify + Supabase) |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | FAQ e diagnóstico de problemas |
| [APPROVAL_WORKFLOW.md](APPROVAL_WORKFLOW.md) | Fila de aprovação de alterações |
| [docs/FIELD_REFERENCE_TIER2.md](docs/FIELD_REFERENCE_TIER2.md) | Campos de fotometria e conformidade do modelo (Tier 2) |
| [docs/FIELD_REFERENCE_TIER3_PHOTOMETRY.md](docs/FIELD_REFERENCE_TIER3_PHOTOMETRY.md) | 📐 Fotometria de instalação: ângulo, material do piso e índices de poluição luminosa (Tier 3) |
| [paper/](paper/) | 📄 Rascunho de artigo científico (PT + EN), dados e figuras reprodutíveis |
| [docs/INTELLECTUAL_PROPERTY.md](docs/INTELLECTUAL_PROPERTY.md) | 🔒 Propriedade intelectual: DOI Zenodo, registro INPI, como citar |
| [CHANGELOG.md](CHANGELOG.md) | Histórico de versões |

## 📝 Como citar

**Autor:** Danilo Valim — ORCID [`0009-0009-7250-6151`](https://orcid.org/0009-0009-7250-6151)
· **DOI:** [`10.5281/zenodo.21305310`](https://doi.org/10.5281/zenodo.21305310)

Se você usar este software ou o método de índices fotométricos, cite:

> Valim, D. (2026). *Iluminação LED Niterói — sistema georreferenciado de gestão do
> parque de iluminação pública com índices fotométricos de instalação* (v1.3.0)
> [Software]. Zenodo. https://doi.org/10.5281/zenodo.21305310

O GitHub também gera a citação a partir do [`CITATION.cff`](CITATION.cff) (botão
*"Cite this repository"*, com o iD do ORCID e o DOI). O marco v1.3.0 (Niterói)
permanece o registro citável até o release `v2.0.0` da plataforma.

## 📄 Licença

Código sob licença MIT — veja [`LICENSE`](LICENSE). **Os dados de cada implantação
pertencem ao respectivo município** ([governança](GOVERNANCE.md)).

---

<div align="center">

**OpenLux** · concebido e mantido por [Danilo Valim](https://github.com/DaniloSFValim)

Nascido em Niterói/RJ (SECONSER · Diretoria de Iluminação Pública) · feito para qualquer cidade

Feito com 💛 para iluminar melhor — com menos poluição luminosa

⭐ Se este projeto te ajudou, deixe uma estrela!

</div>
