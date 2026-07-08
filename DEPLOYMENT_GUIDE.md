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

## Fase 3: Deploy Frontend (Netlify)

### 3.1 Conectar Repositório

```bash
# 1. Ir em https://app.netlify.com
# 2. Clique em "New site from Git"
# 3. Selecionar GitHub
# 4. Localizar repositório: DaniloSFValim/iluminacao-led-niteroi
# 5. Conectar
```

### 3.2 Configurar Build Settings

```
Netlify Dashboard → Settings → Build & deploy

Build command:         (deixar em branco - arquivos estáticos)
Publish directory:     .
Base directory:        (deixar em branco)
Node version:          18
```

### 3.3 Configurar Environment Variables

```
Netlify Dashboard → Site settings → Environment

Adicionar:
NEXT_PUBLIC_SUPABASE_URL    = https://lrnmydrwzxxajylsmoih.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY = sb_publishable_w3UmLsmcDtT81S3MDdDJjw_rEWckoVl
```

### 3.4 Deploy Automático

```bash
# Uma vez conectado, push para main dispara deploy automático
git push origin main

# Verificar status em:
# https://app.netlify.com → seu site → Deploys
# Aguardar status "Published" (verde)
```

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
  https://github.com/DaniloSFValim/iluminacao-led-niteroi/actions
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

- **GitHub Issues:** https://github.com/DaniloSFValim/iluminacao-led-niteroi/issues
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
