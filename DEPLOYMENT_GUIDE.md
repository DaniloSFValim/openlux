# Guia de Deployment

## 📋 Visão Geral

Este guia descreve como fazer deploy do sistema de iluminação LED da cidade de Niterói em um ambiente de produção.

---

## Fase 1: Preparação Local

### 1.1 Verificar Arquivos Necessários

```bash
# Arquivos essenciais que devem estar presentes:
ls -la index.html wrangler.jsonc _headers .env.example
test -d .github && echo "✅ GitHub configuration found"
test -d supabase && echo "✅ Supabase configuration found"
```

### 1.2 Verificar Dependências

```bash
# Node.js 18+ é necessário para Supabase CLI
node --version  # deve ser v18+

# Supabase CLI para gerenciar schema
npm install -g supabase

# Verificar instalação
supabase --version
```

---

## Fase 2: Preparar Backend (Supabase)

### 2.1 Conectar ao Projeto Produção

```bash
# Fazer login no Supabase
supabase login

# Listar projetos disponíveis
supabase projects list

# Link ao projeto produção
supabase link --project-ref lrnmydrwzxxajylsmoih
```

### 2.2 Aplicar Migrations

```bash
# Fazer pull das migrations do projeto remoto
supabase db pull --linked

# Verificar migrations localmente
supabase migration list

# Se houver migrations novas locais, fazer push
supabase db push --linked
```

### 2.3 Verificar Schema

```bash
# Verificar tabelas principais
supabase projects describe

# Ou via SQL Editor em https://app.supabase.com:
# Executar query para validar schema
```

### 2.4 Verificar RLS Policies

```bash
# Acessar Supabase Dashboard:
# 1. https://app.supabase.com
# 2. Selecionar projeto
# 3. Database → Tables
# 4. Para cada tabela, verificar aba "RLS Policies"
# Garantir que policies existem e estão habilitadas
```

---

## Fase 3: Deploy Frontend (Cloudflare Workers — static assets)

> O host anterior cobrava como build o que aqui é copiar três arquivos, e quando os
> créditos acabaram produção parou de atualizar **em silêncio**. A lição está em
> [TROUBLESHOOTING.md](TROUBLESHOOTING.md#-deploy-cloudflare-workers).

O deploy usa **Workers Builds**: a Cloudflare lê este repositório e faz build e deploy
a cada push em `main`, sem token, sem secret e sem GitHub Actions.

> **Por que Workers e não Pages.** O fluxo "Import a repository" do dashboard cria um
> Worker com static assets, não um projeto Pages — foi o que aconteceu na prática. Em
> vez de refazer como Pages, ficamos no Worker: `_headers` funciona igual, e a
> configuração passa a viver em `wrangler.jsonc`, **versionado**, em vez de campos do
> dashboard. Para auditoria isso é melhor do que o plano original.

### 3.1 A configuração fica em `wrangler.jsonc`

O arquivo [`wrangler.jsonc`](wrangler.jsonc) na raiz define o essencial:

```jsonc
"assets": { "directory": "./dist" }
```

> **Esse campo é um controle de segurança, não uma conveniência.**
>
> Sem o `wrangler.jsonc`, o `wrangler deploy` gera configuração automática com
> `"directory": "."` e publica a **raiz inteira** do repositório: as 128 entradas
> versionadas, incluindo `supabase/migrations/*.sql` (schema do banco), docs internos,
> a coleção Postman e POCs antigas.
>
> Foi exatamente o que ocorreu no primeiro build (2026-07-27): o wrangler leu 4560
> arquivos de `/opt/buildhome/repo` e **só não publicou porque abortou** ao encontrar
> `node_modules/workerd/bin/workerd` com 122 MiB, acima do limite de 25 MiB por asset.
> A única coisa que impediu o vazamento foi um acidente de tamanho.
>
> Mantém a decisão da auditoria de 2026-07-09, item C4, antes garantida pelo
> `publish = "dist"` da configuração anterior. **Nunca trocar `./dist` por `.`**

### 3.2 Configurar o build (uma vez, no dashboard)

Em **Workers & Pages → openlux → Settings → Builds**:

| Campo              | Valor                                                              |
| ------------------ | ------------------------------------------------------------------ |
| **Root directory** | `/`                                                                |
| Build command      | `mkdir -p dist && cp index.html design-tokens.css _headers dist/`  |
| Deploy command     | `npx wrangler deploy`                                              |
| Production branch  | `main`                                                             |

O build monta `dist/` com os três arquivos; o `wrangler.jsonc` garante que só `dist/`
suba. `dist/` está no `.gitignore` — é gerado a cada build, não versionado.

> **Não coloque `dist` em Root directory.** É a confusão natural para quem vem de
> outros hosts ou do fluxo Pages, onde existe um campo "Build output directory" que recebe
> `dist`. No Workers Builds esse campo não existe: `Root directory` é a pasta *dentro
> do repositório* onde o build roda, e apontá-la para `dist` faz o build morrer no
> clone, antes de qualquer comando:
>
> ```
> Cloning repository...
> Failed: root directory not found
> ```
>
> O motivo é que `dist/` não existe no repositório — está no `.gitignore` e só é
> criado durante o build. Quem define o que sobe é o `wrangler.jsonc`, não o
> dashboard.

Não há variáveis de ambiente de Supabase a configurar: as credenciais públicas
(`URL` e `anon key`) estão no próprio `index.html`, como antes.

### 3.3 Sobre o `npm ci` no build

O repositório tem `package.json` e `package-lock.json`, então a Cloudflare instala as
`devDependencies` (`@playwright/test`, `html-validate`, `http-server`) antes do build.
Acrescenta cerca de um minuto e o build não usa nenhuma delas.

Dá para pular com a variável de build `SKIP_DEPENDENCY_INSTALL = 1`
(*Settings → Variables and Secrets*).

> **Não faça isso antes de o `wrangler.jsonc` estar em `main`.** Enquanto a
> configuração automática com `"directory": "."` estiver em uso, o `node_modules`
> pesado é o que faz o deploy abortar. Removê-lo faria o upload passar no limite de
> tamanho e publicar o repositório inteiro. Com o `wrangler.jsonc` no lugar, a
> variável é segura — e apenas uma otimização.

### 3.4 Domínio próprio: `openlux.labdados.org`

O domínio está declarado no `wrangler.jsonc`, não no dashboard:

```jsonc
"routes": [
  { "pattern": "openlux.labdados.org", "custom_domain": true }
]
```

Como `labdados.org` é uma zona Cloudflare, o `custom_domain: true` faz a Cloudflare
**criar o registro DNS e emitir o certificado TLS sozinha** — sem passo manual e sem
gerenciar certificado. O vínculo é criado no primeiro `wrangler deploy` que rodar com
essa configuração.

A escolha de *Custom Domain* em vez de *Route* é deliberada: um Custom Domain aponta
**todos** os caminhos do subdomínio para o Worker, que é o comportamento desejado
para um site. Uma Route casaria apenas padrões específicos.

Equivalente pelo dashboard, se algum dia for necessário: *Worker → Settings →
Domains & Routes → Add → Custom Domain*. Preferir o arquivo, para a configuração
seguir versionada.

### 3.5 Verificar

```bash
# codigo novo no ar
curl -s https://openlux.labdados.org | grep -c abrirPainel      # > 0

# headers de seguranca aplicados (prova que o _headers foi lido)
curl -sI https://openlux.labdados.org | grep -i x-frame-options

# cache imutavel do CSS
curl -sI https://openlux.labdados.org/design-tokens.css | grep -i cache-control

# a raiz do repositorio NAO e publicada (auditoria C4)
curl -s -o /dev/null -w '%{http_code}\n' \
  https://openlux.labdados.org/supabase/migrations/20260720000000_initial_schema_recreation.sql
# esperado: 404
```

### 3.6 Sobre a troca de domínio

O site responde em `openlux.labdados.org`. Duas consequências da troca de domínio,
já tratadas no código:

- **Analytics:** o Plausible lista os dois domínios separados por vírgula
  (`index.html`), então o histórico não se perde na transição. Lembre de adicionar
  `openlux.labdados.org` como site no painel do Plausible.
- **Autenticação:** o login usa `signInWithPassword`, sem `redirectTo` — a troca de
  domínio **não** afeta o acesso. Se um dia houver login por OAuth ou magic link,
  será preciso incluir o domínio novo em Supabase → Authentication → URL
  Configuration.

O `_headers` é agnóstico de domínio (todas as regras são por caminho: `/*`, `/*.css`),
então nada muda ali.

### 3.7 Previews de pull request

A Git integration repete build e deploy para cada PR, gerando uma URL de preview —
a mesma capacidade que se perdeu quando os créditos do host anterior
acabaram. Útil para revisar mudança visual antes do merge.

### 3.7 Migração concluída

O site está no ar em `openlux.labdados.org`, verificado em 2026-07-27:

| Verificação | Resultado |
| ----------- | --------- |
| Código atual em produção | `abrirPainel` presente, zero classes `z-[N]` |
| `_headers` aplicado | `X-Frame-Options`, `nosniff`, `X-XSS-Protection`, `Referrer-Policy` |
| Cache do CSS | `max-age=31536000, immutable` |
| `/supabase/migrations/*.sql` | **404** — a raiz não é publicada |
| `/package.json`, `/wrangler.jsonc`, `/docs/*` | 404 |
| TLS | certificado emitido automaticamente pela Cloudflare |

---

## Fase 4: Testes End-to-End

### 4.1 Teste de Conectividade Frontend

```
1. Acessar site: https://openlux.labdados.org
2. Abrir DevTools (F12)
3. Verificar aba Console — não deve haver erros em vermelho
4. Verificar Network — requisições para Supabase devem retornar 200
```

### 4.2 Teste de Autenticação

```
1. Criar usuário de teste em Supabase Dashboard:
   - Auth → Users → Add user
   - Email: teste@seu-dominio.com
   - Password: senha segura

2. No site:
   - Clicar "Login"
   - Preencher email e senha
   - Clicar "Entrar"

RESULTADO ESPERADO:
✓ Login bem-sucedido
✓ Perfil de usuário carregado
✓ Mapa renderiza com dados
```

### 4.3 Teste de Funcionalidades

```
TESTE: Visualização de Mapa
1. Mapa carrega com marcadores/clusters
2. Zoom funciona (scroll mouse)
3. Pan funciona (arrastar mapa)
4. Marcadores atualizam ao fazer zoom

TESTE: Edição de Ponto (como editor)
1. Clicar em um marcador
2. Painel direito abre com dados
3. Clicar "Editar"
4. Modificar um campo
5. Clicar "Salvar"
✓ RESULTADO: Toast de confirmação, ponto atualizado

TESTE: Exportação
1. Clicar botão "Exportar"
2. Selecionar formato (CSV, GeoJSON, PDF)
3. Clicar "Exportar"
✓ RESULTADO: Download iniciado

TESTE: Tema (Dark/Light)
1. Clicar botão tema (🌙/☀️)
2. Interface muda para tema escuro/claro
3. Recarregar página
✓ RESULTADO: Tema persiste
```

### 4.4 Teste de Performance

```bash
# Lighthouse CI é executado automaticamente em GitHub Actions
# Verificar score em: https://github.com/seu-repo/actions/workflows/lighthouse-ci.yml

Targets mínimos:
- Performance: ≥75%
- Accessibility: ≥80%
- Best Practices: ≥75%
- SEO: ≥85%
```

---

## Fase 5: Monitoramento Contínuo

### 5.1 Verificar Logs

```
Cloudflare Workers Logs:
  dash.cloudflare.com → Workers & Pages → openlux → Deployments → último → build log

Supabase Logs:
  https://app.supabase.com → seu projeto → Logs → PostgreSQL

GitHub Actions:
  https://github.com/DaniloSFValim/openlux/actions
  Verificar status dos workflows (CI, Security, E2E Tests)
```

### 5.2 Configurar Alertas (Recomendado)

```bash
# GitHub → Repository → Settings → Notifications
# Habilitar notificações para:
# - Workflow failures
# - Security alerts
```

### 5.3 Backup Regular

```bash
# GitHub Actions executa backup automático (diariamente 02:00 UTC)
# Backups salvos em: /backups/db_YYYY-MM-DD_HH-MM-SS.sql

# Para restaurar manualmente:
supabase db reset --linked
psql -f backups/db_YYYY-MM-DD_HH-MM-SS.sql
```

---

## Fase 6: Rollback (Se Necessário)

### 6.1 Rollback Frontend

```bash
# Opção A: Revert via GitHub
git log --oneline -5
git revert <commit-id>
git push origin main
# Workers Builds reconstroi automaticamente (~2 min)

# Opção B: Via dashboard da Cloudflare
# Workers & Pages → openlux → Deployments → deploy anterior → "Rollback to this deployment"
```

### 6.2 Rollback Backend (Supabase)

```bash
# Via Supabase local
supabase db reset --linked

# Restaurar de backup
psql -f backups/db_<timestamp>.sql

# Depois sincronizar com produção
supabase db push --linked
```

---

## 🎯 Checklist Final

```
PRÉ-DEPLOYMENT:
[ ] index.html pronto
[ ] wrangler.jsonc válido (assets.directory = ./dist)
[ ] .env.example preenchido com placeholders (sem credenciais reais)
[ ] .github/workflows funcionando localmente

SUPABASE:
[ ] Supabase CLI instalado
[ ] Conectado ao projeto produção
[ ] Migrations aplicadas com sucesso
[ ] RLS policies habilitadas
[ ] Backups configurados

CLOUDFLARE WORKERS:
[ ] Repositório conectado (Workers Builds)
[ ] Root directory = / (nao dist)
[ ] Build command e Deploy command corretos
[ ] Custom domain openlux.labdados.org ativo
[ ] Domain/SSL certificado

TESTES:
[ ] Frontend carrega sem erros
[ ] Autenticação funciona
[ ] Mapa renderiza com dados
[ ] Edição de pontos funciona
[ ] Exportação funciona
[ ] Tema toggle funciona
[ ] Zoom mínimo (≥18) respeitado
[ ] Endereço via Nominatim preenchido

MONITORAMENTO:
[ ] Build log da Cloudflare verificado (3 arquivos em dist/)
[ ] Supabase logs verificados
[ ] GitHub Actions status (todas passando)
[ ] Performance scores adequados (Lighthouse)
[ ] Backups sendo feitos
```

---

## 📞 Suporte

- **GitHub Issues:** https://github.com/DaniloSFValim/openlux/issues
- **Documentação:** README.md, ARCHITECTURE.md, TROUBLESHOOTING.md
- **Email:** danilosfvalim@gmail.com

---

## 🎉 Próximos Passos

Após deployment bem-sucedido:

1. ✅ Monitorar logs pelos próximos dias
2. ✅ Coletar feedback dos usuários
3. ✅ Resolver qualquer issue que surja
4. ✅ Otimizar performance baseado em Lighthouse/Analytics
5. ✅ Planejar próximas features

Que a força esteja com você! 🚀
