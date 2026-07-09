# Troubleshooting - Iluminação LED Niterói

## 🚀 Startup

### Página não carrega

**Sintoma:** Página branca ou erro no console

**Solução:**
1. Abrir DevTools (F12)
2. Verificar aba Console para erros
3. Verificar Network (há requisições à Supabase?)
4. Verificar se Supabase URL é acessível
5. Limpar cache: Ctrl+Shift+Del

### Supabase não conecta

**Sintoma:** "Error connecting to database"

**Causas comuns:**
- URL errada no `index.html` (linhas 260-262)
- Anon key expirada
- Supabase projeto deletado
- Firewall bloqueando conexão

**Solução:**
1. Ir em https://app.supabase.com
2. Copiar URL e Anon key corretos
3. Atualizar `index.html` (linhas 260-262)
4. Fazer hard refresh: Ctrl+Shift+R

### Mapa não renderiza

**Sintoma:** Div vazio, sem tiles

**Causas:**
- Leaflet CDN não carregou
- RPC `ip_pontos_bbox` retorna null
- Erro de permissão (RLS)
- Bounds do mapa inválidos

**Solução:**
1. Verificar DevTools → Network → leaflet.js carregou?
2. Verificar RPC no Supabase Dashboard:
   ```sql
   SELECT * FROM ip_pontos_bbox(
     p_bbox_south => -23.03,
     p_bbox_west => -43.2,
     p_bbox_north => -22.8,
     p_bbox_east => -42.9,
     p_zoom => 12
   );
   ```
3. Testar RLS policies

## 🔐 Autenticação

### Login não funciona

**Sintoma:** Erro ao submeter email/senha

**Causas:**
- Usuário não existe
- Supabase Auth desabilitado
- CORS configurado errado

**Solução:**
1. Criar usuário em Supabase Dashboard → Auth → Users
2. Garantir profile existe em `profiles` com role
3. Testar no SQL:
   ```sql
   SELECT * FROM auth.users WHERE email = 'seu@email.com';
   SELECT * FROM public.profiles WHERE id = 'user-id';
   ```

### Role não reconhecido

**Sintoma:** Menu admin não aparece, não consegue editar

**Causas:**
- Coluna `role` em `profiles` não preenchida
- Typo no role ('adimin' vs 'admin')
- Cache do browser

**Solução:**
1. Verificar banco:
   ```sql
   SELECT id, role FROM profiles WHERE id = auth.uid();
   ```
2. Corrigir role:
   ```sql
   UPDATE profiles SET role = 'admin' WHERE id = '...';
   ```
3. Logout + login novamente
4. Limpar cache: Ctrl+Shift+Del

## 📊 Dados & Exportação

### Tabela vazia

**Sintoma:** Nenhum resultado em "Ver Tabela"

**Causas:**
- RLS blocking queries
- Filtros muito restritivos
- Dados não existem no período

**Solução:**
1. Remover filtros
2. Testar query:
   ```sql
   SELECT COUNT(*) FROM v_parque_export;
   ```
3. Verificar RLS policies:
   ```sql
   SELECT * FROM pg_policies WHERE tablename='v_parque_export';
   ```

### Exportação falha

**Sintoma:** Download não inicia ou arquivo vazio

**Causas:**
- Muitos dados (limite ~4000 pontos)
- Erro em RPC
- jsPDF não carregou (CDN)

**Solução:**
1. Remover filtros para reduzir dados
2. Verificar DevTools → Network → jspdf.umd.min.js
3. Testar RPC com filtros menores

## ⚙️ Edição & Atualização

### Editar ponto não salva

**Sintoma:** Clica "Salvar" mas nada acontece

**Causas:**
- Erro silencioso no RPC
- Falta de permissão (role='leitura')
- Conexão perdida

**Solução:**
1. Verificar DevTools Console (há erro?)
2. Verificar role:
   ```sql
   SELECT role FROM profiles WHERE id = auth.uid();
   -- Deve retornar 'editor' ou 'admin'
   ```
3. Testar RPC manualmente

### Histórico não aparece

**Sintoma:** Aba "Histórico de Alterações" vazia

**Causas:**
- Ponto é novo (sem histórico)
- Tabela de auditoria vazia
- RPC não retorna dados

**Solução:**
1. Verificar se ponto existe há mais tempo
2. Testar RPC em Supabase Dashboard
3. Verificar se há trigger de auditoria

## 🔄 Backup & Restore

### Backup falha

**Sintoma:** `supabase db dump` retorna erro

**Causas:**
- PostgreSQL não rodando
- Sem permissão de dump
- Disco cheio

**Solução:**
```bash
# Verificar se Supabase está rodando
supabase status

# Se local, reiniciar
supabase stop
supabase start

# Verificar espaço
df -h
```

### Restore não funciona

**Sintoma:** Erro ao restaurar .sql

**Causas:**
- Arquivo SQL corrompido
- Versão PostgreSQL diferente
- Falta de permissões

**Solução:**
```bash
# Verificar arquivo
file backups/db_*.sql
head -20 backups/db_*.sql

# Restaurar com verbosidade
psql -f backups/db_*.sql -v ON_ERROR_STOP=1
```

## 📱 Frontend / UI

### Mapa não responde ao zoom/pan

**Sintoma:** Mapa congelado ou lag extremo

**Causas:**
- RPC `ip_pontos_bbox` lento
- Muitos marcadores (>4000)
- Browser sem suporte WebGL

**Solução:**
1. Verificar Network timing (DevTools)
2. Aplicar filtros para reduzir dados
3. Usar zoom de densidade
4. Testar em outro navegador

### Gráficos não aparecem

**Sintoma:** Sparkline vazio ou coroplético não renderiza

**Causas:**
- RPC retorna dados null
- D3/SVG não carregou
- Erro JavaScript

**Solução:**
1. Verificar DevTools Console
2. Testar RPC em Supabase Dashboard
3. Hard reload: Ctrl+Shift+R

### Filtros cascata não funcionam

**Sintoma:** Selecionar Bairro não atualiza Tipo

**Causas:**
- HTMX não carregou
- Fetch interceptor não funcionando
- Erro em JavaScript

**Solução:**
1. Verificar DevTools → Network → htmx.org
2. Verificar console para erros de fetch
3. Testar seleção manual de Tipo

## 💾 Netlify Deploy

### Deploy falha no Netlify

**Sintoma:** "Build failed" no dashboard

**Causas:**
- Arquivo corrompido
- Variáveis de ambiente não configuradas
- GitHub webhook erro

**Solução:**
1. Ir em Netlify Dashboard → Deploys → View logs
2. Verificar se `index.html` está correto
3. Verificar Environment variables
4. Trigger rebuild manual

### Produção mostra versão antiga

**Sintoma:** Mudanças não aparecem após push

**Causas:**
- Cache do browser
- CDN cache (Netlify)
- Deploy ainda em progresso

**Solução:**
1. Hard refresh: Ctrl+Shift+R
2. Aguardar 2-3 min
3. Ver status em https://app.netlify.com
4. Limpar cache Netlify: Settings → Build & Deploy → Clear cache

## 🆘 Última Opção: Debug Completo

Se nada funcionar:

1. **Coletar informações:**
   ```bash
   # URL atual
   echo $LOCATION

   # Versão browser
   navigator.userAgent (DevTools Console)

   # Supabase status
   curl https://lrnmydrwzxxajylsmoih.supabase.co/

   # Se local
   supabase status
   docker ps
   ```

2. **Criar issue no GitHub:**
   - Incluir erro exato do console
   - Steps para reproduzir
   - Versão browser
   - Screenshots

3. **Contatos:**
   - Supabase docs: https://supabase.com/docs
   - Leaflet docs: https://leafletjs.com/docs.html
   - GitHub Issues: https://github.com/danilosfvalim/iluminacao-led-niteroi/issues
