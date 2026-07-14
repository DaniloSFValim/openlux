# Migrations — regras e estado

## ⚠️ Fato operacional importante

**Mergear um PR neste repositório NÃO aplica migrations no Supabase.**
Não existe pipeline automático (GitHub Action, webhook ou `supabase db push` em CI).
Todo SQL só chega em produção quando aplicado explicitamente — via
`supabase db push`, MCP `apply_migration`, ou SQL Editor do dashboard.

Isso causou os incidentes de 2026-07-09: três PRs de hotfix foram mergeados
com CI verde e o banco continuou quebrado, porque as migrations nunca foram
executadas.

## Fonte de verdade

O **banco de produção é a fonte de verdade** do schema. O histórico oficial é
a tabela `supabase_migrations.schema_migrations` (consultável via
`supabase migration list` ou MCP `list_migrations`).

Este diretório contém **apenas** arquivos cujo nome corresponde exatamente a
uma versão registrada nesse histórico (formato `YYYYMMDDHHMMSS_nome.sql`,
timestamp de 14 dígitos).

## Como aplicar uma mudança de schema (fluxo correto)

1. Escreva a migration com timestamp completo de 14 dígitos:
   `supabase migration new minha_mudanca` (gera o nome correto).
2. Aplique em produção: `supabase db push` (ou MCP `apply_migration`,
   que registra a versão automaticamente).
3. Só então commite o arquivo aqui, com o nome idêntico à versão registrada.
4. Confirme com `supabase migration list` que repositório e banco batem.

**Nunca** commite uma migration sem aplicá-la, e nunca aplique SQL manual
sem registrar a migration correspondente — as duas coisas juntas é que
mantêm este diretório confiável.

## Sobre `../migrations_archive/`

Contém os arquivos antigos com prefixo de data incompleto (8 dígitos,
ex.: `20260709_fix_...`). Eles foram movidos para fora deste diretório porque:

- O prefixo curto quebra a ordenação do Supabase CLI (arquivos do mesmo dia
  ordenam alfabeticamente pelo nome, não pela ordem real de aplicação);
- Vários **nunca foram aplicados** ao banco, ou foram substituídos por
  hotfixes manuais posteriores;
- Alguns são **regressivos**: se executados em ordem alfabética, recriam
  funções quebradas (ex.: `20260709_fix_rpc_enum_type_casting.sql` recria
  `ip_inserir_ponto` com colunas `latitude`/`longitude` que não existem).

**Não execute os arquivos do archive.** Eles estão preservados apenas como
registro histórico das intenções de cada PR.

## Estado em 2026-07-10

Últimas versões aplicadas e espelhadas aqui:

| Versão | Nome | Conteúdo |
|--------|------|----------|
| `20260709182342` | `sync_rpc_hotfixes_fix_atualizar_ponto` | Estado final de `ip_inserir_ponto` (geom/fonte/modernizado_led), fix de `ip_atualizar_ponto` (UPDATE na tabela, não na view), `v_parque_export` com `health_status` |
| `20260709182416` | `create_storage_buckets_luminarias` | Buckets `luminarias-fotos` / `luminarias-ies` + policies |
| `20260709183525` | `drop_dead_rpc_overloads` | Remove 10 overloads mortas (clusters_grid ×4, pontos_bbox ×2, atualizar_ponto ×2, criar/atualizar_modelo ×1 cada) |
| `20260709183630` | `harden_write_rpc_grants` | REVOKE EXECUTE de `anon`/`PUBLIC` nas 10 funções de escrita; `search_path` fixado em `aprovar_mudanca` e `ip_registrar_intervencao` |
| `20260710160356` | `expand_pontos_tier3_photometry` | Tier 3 fotometria: tabela `ref_material_piso` + colunas `angulo_inclinacao_graus`/`material_piso`; `ip_inserir_ponto` (15 args) e `ip_atualizar_ponto` (13 args) recriadas com `p_angulo`/`p_material` (assinatura única, grants re-hardened); `v_parque_export` e `ip_pontos_bbox` expõem as 2 colunas |
| `20260710191925` | `add_polygon_selection_rpcs` | Seleção por polígono: `ip_pontos_poligono(geojson,limite)` e `ip_stats_poligono(geojson)` (ST_Contains sobre índice GIST); leitura pública. Contagem/densidade/%LED/potência/fotometria média restritos à área desenhada |
| `20260711155442` | `add_municipio_and_recenseamento` | OpenLux Fases 1+2: tabelas `municipios` (Niterói seed) e `campanhas`; colunas `municipio_id`/`verificado_em`/`verificado_por`/`campanha_id` em pontos; RPCs `ip_criar/encerrar/listar_campanhas` + `ip_confirmar_ponto`; carimbo de verificação em `ip_inserir/atualizar_ponto` (mesmas assinaturas); `p_nao_verificado` em bbox/clusters (re-grant) e view com `verificado_em` |
| `20260712215601` | `fix_aprovar_mudanca_and_stamp_verification` | Fase 2.1 + conserto latente: `aprovar_mudanca` operava sobre a view com casts de enum errados (classe C2); agora UPDATE/INSERT/DELETE em `pontos_luminaria` (geom via ST_MakePoint, casts corretos, Tier 3) e aprovação carimba verificação (campanha ativa em `fila.criado_em`, `verificado_por` = editor original) |

Versões anteriores a essas existem no histórico do banco mas não têm arquivo
neste diretório (foram aplicadas pelo dashboard/MCP antes desta organização).
Para reconstruir o schema do zero, use `supabase db pull` a partir da
produção em vez de reexecutar este diretório.
