# 🏙️ Implante o OpenLux na sua cidade

> **Estado atual (Fase 0):** a implantação já é possível, porém **manual** — o core
> ainda carrega configurações de Niterói no código, que a Fase 1 extrairá para
> `config/cities/`. Este guia mostra o caminho de hoje, honestamente, e o que vai
> mudar. Acompanhe o [roadmap na visão](../VISION.md#6-roadmap-por-fases).

## O que você precisa

| Recurso | Custo típico | Observação |
|---|---|---|
| Conta [Supabase](https://supabase.com) | Grátis → ~US$ 25/mês | PostgreSQL + PostGIS + Auth + Storage |
| Conta [Netlify](https://netlify.com) (ou similar) | Grátis | Hospeda 1 arquivo HTML |
| Base inicial de pontos | — | Censo da distribuidora, KML/planilha própria, ou cadastro do zero em campo |
| Uma pessoa técnica | — | Para a implantação inicial (≈ 1 dia hoje; meta da Fase 3: 1 hora) |

## Caminho de implantação (hoje, manual)

1. **Fork/clone** deste repositório.
2. **Backend**: crie um projeto Supabase e aplique o schema seguindo
   [`supabase/README.md`](../supabase/README.md) e o
   [README de migrations](../supabase/migrations/README.md)
   (o banco é a fonte de verdade — leia antes).
3. **Dados**: importe seus pontos para `pontos_luminaria`
   (geometria em SRID 4326; campos mínimos: `geom`, `tipo_ativo`, `status`, `fonte`).
4. **Frontend**: copie `config/cities/niteroi.json` para `config/cities/<sua-cidade>.json`,
   ajuste os valores e replique-os no bloco **`CITY`** no topo do script do `index.html`
   (nome, centro, zoom, limites geográficos) — é o único ponto do código com dados da
   cidade. Credenciais do Supabase ficam logo acima (`URL_SB`/`ANON`); título e
   identidade visual são configuráveis pelo painel Admin → Aparência.
5. **Deploy**: conecte o repositório ao Netlify (o `netlify.toml` já publica somente
   o `dist/index.html`).
6. **Papéis**: crie os usuários (leitura/editor/admin) — ver
   [DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md) e
   [TROUBLESHOOTING.md](../TROUBLESHOOTING.md).
7. **Registre-se** em [`cities/`](../cities/README.md) via PR. 🎉

## O que a plataforma entrega de saída

Mapa público com clustering e heat maps · edição em campo com papéis e fila de
aprovação · catálogo fotométrico de modelos (Tier 2) · índices de instalação
ângulo/material (Tier 3) · análise por polígono · exportação CSV/GeoJSON/PDF ·
histórico e auditoria · CI/CD e backups.

## O que muda nas próximas fases

| Fase | O passo manual que desaparece |
|---|---|
| ~~**1 — Desacoplar**~~ ✅ | Feito: dados da cidade concentrados no bloco `CITY` + `config/cities/` |
| ~~**2 — Recenseamento**~~ ✅ | Feito: campanhas versionadas (Admin → 🧭 Campanhas), estado herdado/verificado |
| **3 — Multi-cidade** | Projeto Supabase próprio → opção de entrar num consórcio (tenant) com onboarding guiado |

## Precisa de ajuda?

Abra uma issue `[cidade] <nome>` — implantar cidades novas é exatamente o que o
projeto quer aprender a fazer bem. Ver também a [governança](../GOVERNANCE.md).
