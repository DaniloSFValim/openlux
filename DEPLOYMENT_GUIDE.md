# Guia de Deployment

## 📋 Visão Geral

Este guia descreve como fazer deploy do sistema de iluminação LED da cidade de Niterói em um ambiente de produção.

---

## Fase 1: Preparação Local

### 1.1 Verificar Arquivos Necessários

```bash
# Arquivos essenciais que devem estar presentes:
ls -la index.html netlify.toml .env.example
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

## Fase 3: Deploy Frontend (Cloudflare Pages)

> **Por que não Netlify.** O "build" deste projeto é copiar três arquivos
> (`index.html`, `design-tokens.css`, `_headers`) para `dist/`, e o Netlify cobrava
> isso como build a cada merge. Quando os créditos acabaram, produção parou de
> atualizar silenciosamente — deploys de preview continuavam, mas nenhum deploy de
> produção era criado, e o site ficou servindo um commit antigo sem qualquer erro
> visível. O Cloudflare Pages tem bandwidth ilimitado no plano gratuito e lê o
> **mesmo formato** de `_headers`, então as regras de segurança seguem valendo.

O deploy é feito pelo workflow `.github/workflows/deploy-cloudflare.yml`, que roda no
GitHub Actions (gratuito em repositório público) e publica com `wrangler`.

### 3.1 Criar o token de API na Cloudflare

```
1. https://dash.cloudflare.com → ícone do perfil → API Tokens
2. "Create Token" → template "Edit Cloudflare Workers"
   (ou Custom Token com a permissão: Account → Cloudflare Pages → Edit)
3. Copiar o token gerado (aparece só uma vez)
4. Anotar o Account ID, visível na barra lateral do dashboard
```

### 3.2 Cadastrar os dois secrets no GitHub

```
Repositório → Settings → Secrets and variables → Actions → New repository secret

CLOUDFLARE_API_TOKEN   = <token da etapa 3.1>
CLOUDFLARE_ACCOUNT_ID  = <account id da etapa 3.1>
```

Não há variáveis de ambiente de Supabase a configurar: as credenciais públicas
(`URL` e `anon key`) estão no próprio `index.html`, como antes.

### 3.3 Deploy

O workflow dispara sozinho em push para `main` que altere `index.html`,
`design-tokens.css` ou `_headers`. Para publicar sob demanda:

```
Repositório → Actions → "Deploy (Cloudflare Pages)" → Run workflow
```

No primeiro deploy o `wrangler` cria o projeto `openlux` automaticamente, e o site
passa a responder em `https://openlux.pages.dev`.

### 3.4 Verificar

```bash
# codigo novo no ar
curl -s https://openlux.pages.dev | grep -c abrirPainel      # > 0

# headers de seguranca aplicados (prova que o _headers foi lido)
curl -sI https://openlux.pages.dev | grep -i x-frame-options

# a raiz do repositorio NAO e publicada (auditoria C4)
curl -s -o /dev/null -w '%{http_code}\n' \
  https://openlux.pages.dev/supabase/migrations/20260720000000_initial_schema_recreation.sql
# esperado: 404
```

### 3.5 Sobre o domínio e as métricas

A URL passa de `iluminacao-niteroi.netlify.app` para `openlux.pages.dev`. Duas
consequências já tratadas no código:

- **Analytics:** o Plausible está configurado com os dois domínios separados por
  vírgula (`index.html`), então o histórico não se perde na transição.
- **Autenticação:** o login usa `signInWithPassword`, sem `redirectTo` — a troca de
  domínio **não** afeta o acesso. Se um dia houver login por OAuth ou magic link,
  será preciso incluir o domínio novo em Supabase → Authentication → URL
  Configuration.

Para usar domínio próprio: Cloudflare Pages → projeto → Custom domains.

---

## Fase 4: Testes End-to-End

### 4.1 Teste de Conectividade Frontend

```
1. Acessar site: https://seu-site.netlify.app
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
Netlify Logs:
  https://app.netlify.com → seu site → Deploys → último → Deploy logs

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
# Netlify rebuilda automaticamente (~2 min)

# Opção B: Via Netlify Dashboard
# Netlify → Deploys → clique em deploy anterior → "Publish deploy"
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
[ ] netlify.toml válido
[ ] .env.example preenchido com placeholders (sem credenciais reais)
[ ] .github/workflows funcionando localmente

SUPABASE:
[ ] Supabase CLI instalado
[ ] Conectado ao projeto produção
[ ] Migrations aplicadas com sucesso
[ ] RLS policies habilitadas
[ ] Backups configurados

NETLIFY:
[ ] Repositório conectado
[ ] Build settings corretos
[ ] Environment variables configuradas
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
[ ] Netlify logs verificados
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
