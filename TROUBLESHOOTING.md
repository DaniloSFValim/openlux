# Troubleshooting - Iluminação LED Niterói

Guia de solução de problemas comuns.

## 🚀 Startup & Inicialização

### Página não carrega (branca ou erro)

**Sintomas:**
- Tela branca ao abrir site
- Erro "Cannot read property X of undefined"
- Mensagem "Failed to fetch"

**Investigação:**
1. Abrir DevTools (F12)
2. Aba "Console" — há mensagens de erro (vermelho)?
3. Aba "Network" — quais requisições falharam?
4. Aba "Sources" — código está carregando?

**Soluções:**
1. Limpar cache: Ctrl+Shift+Del (selecionar "Tudo" e período)
2. Hard refresh: Ctrl+Shift+R (Mac: Cmd+Shift+R)
3. Abrir em modo incógnito/privado (evita cache)
4. Testar em outro navegador

**Se persistir:**
- Verificar console para erro específico
- Ver seção "Última Opção: Debug Completo" abaixo

---

### Supabase não conecta (API inacessível)

**Sintomas:**
- "Error connecting to database"
- "Failed to load RPC function"
- Mapa vazio (sem dados)
- Login não funciona

**Causas Comuns:**
- URL do Supabase errada em `index.html` (linhas 260-262)
- Anon key expirada ou inválida
- Projeto Supabase deletado/suspenso
- Network issues (proxy corporativo, VPN)

**Investigação:**
```javascript
// Abrir DevTools Console e executar:
console.log(URL_SB);     // Deve ser https://lrnmydrwzxxajylsmoih.supabase.co
console.log(ANON);       // Deve ser sb_publishable_...
console.log(sb);         // Deve ser objeto Supabase client
```

**Soluções:**
1. Verificar credenciais em [app.supabase.com](https://app.supabase.com)
   - Ir em Settings → API
   - Copiar "Project URL" e "anon public key" corretos
   
2. Atualizar `index.html`:
   ```javascript
   const URL_SB = "https://lrnmydrwzxxajylsmoih.supabase.co";  // Seu projeto
   const ANON = "sb_publishable_w3UmLsmcDtT81S3MDdDJjw_rEWckoVl";  // Sua key
   ```

3. Se recém-criado, aguardar 2-3 min para DNS propagar

4. Testar conectividade:
   ```bash
   curl -i https://lrnmydrwzxxajylsmoih.supabase.co/rest/v1/
   # Deve retornar 200 ou 401 (não connection refused)
   ```

---

### Mapa não renderiza (branco ou vazio)

**Sintomas:**
- Div do mapa vazio (sem tiles, sem marcadores)
- Console erro "Leaflet is not defined"
- Tiles de OpenStreetMap não carregam

**Causas:**
- CDN do Leaflet não carregou
- RPC `ip_pontos_bbox` retorna null/error
- RLS blocking requisições
- Coordinates não estão em bounds válidos (Niterói)

**Investigação:**
```javascript
// DevTools Console:
console.log(L);          // Deve ser objeto Leaflet (não undefined)
console.log(map);        // Deve ser objeto Map
map.getCenter();          // Deve retornar lat/lng
map.getZoom();            // Deve retornar número
```

**Soluções:**
1. Verificar Leaflet CDN:
   - DevTools → Network → buscar `leaflet.js`
   - Deve estar com status 200 (não 404 ou 0)
   - Se 0, problema de rede (DNS, proxy, etc)

2. Testar RPC manualmente (Supabase Dashboard → SQL Editor):
   ```sql
   SELECT * FROM ip_pontos_bbox(
     p_bbox_south := -23.03,
     p_bbox_west := -43.2,
     p_bbox_north := -22.8,
     p_bbox_east := -42.9,
     p_zoom := 12,
     p_limite := 100,
     p_filtros := '{}'::jsonb
   );
   ```
   - Se erro, há problema no banco
   - Se null, a função não retorna dados

3. Verificar RLS:
   - Ir em Supabase Dashboard
   - Tabela `v_parque_export` → Policies
   - Deve haver policy SELECT para role do usuário

4. Testar com coordinates de Niterói:
   - Bounds corretos: -23.03 a -22.80 (lat), -43.20 a -42.90 (lng)
   - Se fora, mapa carrega mas está em local errado

---

## 🔐 Autenticação & Acesso

### Login não funciona (erro na submissão)

**Sintomas:**
- Erro ao clicar "Login"
- "Invalid login credentials"
- "User not found"
- Form fica carregando infinitamente

**Investigação:**
1. Email existe? Verificar em Supabase Dashboard:
   - Ir em Authentication → Users
   - Buscar email do teste

2. Role foi criada? Verificar `profiles`:
   ```sql
   SELECT id, role FROM profiles WHERE email = 'seu@email.com';
   ```

3. Há erro no console?
   ```javascript
   // DevTools Console:
   sb.auth.signInWithPassword({
     email: 'seu@email.com',
     password: 'password'
   }).then(r => console.log(r)).catch(e => console.log(e));
   ```

**Soluções:**
1. Criar usuário de teste:
   - Supabase Dashboard → Authentication → Users → Create new user
   - Email, Password
   - Confirmar email (ou Skip confirmation)

2. Criar profile com role:
   ```sql
   INSERT INTO profiles (id, role, email) VALUES
   ('user-uuid-aqui', 'editor', 'seu@email.com')
   ON CONFLICT DO NOTHING;
   ```

3. Verificar RLS em `profiles`:
   - Deve permitir SELECT/INSERT para role específico

4. Se tiver proxy corporativo:
   - Testar em rede diferente (mobile hotspot)
   - Pode bloquear requisições a Supabase

---

### Role não reconhecido (admin/editor features não aparecem)

**Sintomas:**
- Botão "Admin Console" não aparece
- Não consegue editar ponto (mesmo com permissão)
- Sempre vê como "leitura"

**Investigação:**
```javascript
// DevTools Console:
console.log(state.userRole);    // Deve ser 'admin' ou 'editor'
console.log(state.user);        // Deve ter id do usuário
```

```sql
-- Supabase SQL:
SELECT id, role FROM profiles WHERE id = auth.uid();
```

**Causas Comuns:**
- Coluna `role` em `profiles` vazia ou NULL
- Typo no role ('adimin' vs 'admin')
- RLS blocking SELECT em `profiles`
- Cache do browser (localStorage com role antigo)

**Soluções:**
1. Verificar role no banco:
   ```sql
   UPDATE profiles SET role = 'admin' WHERE id = 'user-uuid';
   ```

2. Forçar re-fetch do role:
   - Logout: clicar botão logout
   - Limpar localStorage: DevTools → Application → Storage → Delete All
   - Login novamente

3. Hard refresh: Ctrl+Shift+R

4. Verificar policies de `profiles`:
   ```sql
   SELECT * FROM pg_policies WHERE tablename = 'profiles';
   -- Deve permitir SELECT por auth.uid()
   ```

---

## 📊 Dados & Visualização

### Tabela está vazia (nenhum resultado)

**Sintomas:**
- Modal da tabela abre mas está vazia
- Contador mostra "0 de 0"
- Mesmo removendo filtros, vazio

**Investigação:**
```sql
-- Supabase SQL:
SELECT COUNT(*) as total FROM v_parque_export;
SELECT COUNT(*) as total FROM v_parque_export WHERE bairro_nome = 'Centro';
```

**Causas:**
- RLS policies bloqueando SELECT
- Filtros muito restritivos
- Dados não existem no banco
- RPC retorna null ao invés de array vazio

**Soluções:**
1. Verificar se há dados:
   ```sql
   SELECT * FROM v_parque_export LIMIT 10;
   ```

2. Remover filtros e recarregar
   - Retirar filtro de bairro, tipo, estado
   - Clicar "Atualizar"

3. Verificar RLS no `v_parque_export`:
   ```sql
   SELECT * FROM pg_policies WHERE tablename = 'v_parque_export';
   ```
   - Deve permitir SELECT (USING clause sem restrições ou true)

4. Verificar coluna `bairro_nome`:
   ```sql
   SELECT DISTINCT bairro_nome FROM v_parque_export LIMIT 20;
   -- Deve retornar pelo menos alguns nomes
   ```

---

### Mapa mostra pontos mas filtro não funciona

**Sintomas:**
- Selecionar filtro (bairro) mas pontos não desaparecem
- Contador não atualiza
- Dados brutos estão corretos, mas filtro não aplica

**Investigação:**
```javascript
// DevTools Console:
console.log(state.bairro);     // Deve ter valor do filtro
console.log(filtros());        // Deve retornar {bairro: 'Centro'}
```

**Causas:**
- Evento de mudança (onchange) não disparando
- Refresh não está sendo chamado
- RPC recebendo filtros mas ignorando

**Soluções:**
1. Verificar se evento dispara:
   ```javascript
   document.getElementById('fBairro').onchange = e => {
     console.log('Filtro mudou:', e.target.value);
   };
   ```

2. Forçar refresh manual:
   - Abrir DevTools Console
   - Executar: `refresh()`

3. Verificar função `filtros()`:
   - Deve retornar objeto com filtros aplicados
   - Exemplo: `{bairro_nome: 'Centro'}`

4. Testar RPC com filtro:
   ```sql
   SELECT * FROM ip_pontos_bbox(
     p_bbox_south := -23.03,
     p_bbox_west := -43.2,
     p_bbox_north := -22.8,
     p_bbox_east := -42.9,
     p_zoom := 12,
     p_limite := 100,
     p_filtros := '{"bairro_nome": "Centro"}'::jsonb
   ) LIMIT 10;
   ```

---

### Exportação falha ou arquivo está vazio

**Sintomas:**
- Clicar "Exportar CSV" mas download não inicia
- Arquivo baixa mas está vazio
- Erro "jsPDF is not defined"
- PDF não tem tabelas

**Investigação:**
```javascript
// DevTools Console:
console.log(jsPDF);              // Deve ser função (não undefined)
console.log(window.jspdfautotable);  // Deve existir
```

**Causas Comuns:**
- Muitos dados (limite de 4.000 pontos)
- jsPDF CDN não carregou
- RPC com filtro retorna dados vazios
- Erro na função `toCSV()` ou `toPDF()`

**Soluções:**
1. Verificar CDN do jsPDF:
   - DevTools → Network → buscar `jspdf.umd.min.js`
   - Deve estar 200 (não 404)

2. Reduzir dados:
   - Aplicar filtros para menos de 1.000 pontos
   - Testar exportação

3. Verificar tamanho dos dados:
   ```javascript
   // DevTools Console:
   const data = await rpc('ip_pontos_bbox', {...});
   console.log('Pontos:', data.length);
   ```

4. Testar conversão CSV:
   ```javascript
   const csv = toCSV([{id: 1, nome: 'teste'}]);
   console.log(csv);  // Deve ter CSV válido
   ```

5. Se PDF falhar:
   - Verificar que jsPDF + autotable carregaram
   - Testar com menos dados (10-50 pontos)

---

## ⚙️ Edição & Atualização

### Editar ponto não salva (sem erro)

**Sintomas:**
- Clicar "Salvar" mas nada acontece
- Sem mensagem de sucesso/erro
- Painel não fecha

**Investigação:**
```javascript
// DevTools Console:
console.log(state.current);     // Deve ter ponto selecionado
console.log(podeEditar());      // Deve retornar true
```

**Causas:**
- Erro silencioso no RPC (tratado em try/catch)
- Falta de permissão (role='leitura')
- Conexão perdida durante submissão
- Validação falhou

**Soluções:**
1. Verificar console para erro:
   - Pode estar em try/catch que não mostra
   - Tentar salvar novamente e observar network

2. Verificar role:
   ```sql
   SELECT role FROM profiles WHERE id = auth.uid();
   -- Deve retornar 'editor' ou 'admin' (não 'leitura')
   ```

3. Verificar RLS em ponto:
   ```sql
   SELECT * FROM pg_policies 
   WHERE tablename = 'v_parque_export' AND cmd = 'UPDATE';
   ```

4. Testar RPC manualmente:
   ```sql
   SELECT * FROM ip_atualizar_ponto(
     p_id := 'uuid-do-ponto',
     p_tipo := 'luminaria',
     p_potencia := 150,
     p_led_instalado := true,
     ...
   );
   ```

5. Verificar validação JavaScript:
   - Campos obrigatórios preenchidos?
   - Potência > 0?
   - Coordenadas válidas?

---

### Histórico de alterações não aparece

**Sintomas:**
- Aba "Histórico de Alterações" vazia
- Aba "Intervenções" vazia
- Mesmo pontos antigos não mostram história

**Investigação:**
```javascript
// DevTools Console:
const point = state.current;
const history = await rpc('ip_historico_ponto', {p_id: point.id});
console.log(history);  // Deve ter array de alterações
```

**Causas:**
- Ponto é recém-criado (sem histórico)
- Tabela de auditoria vazia ou não preenchida
- RPC não retorna dados
- RLS blocking SELECT em audit_logs

**Soluções:**
1. Verificar se ponto tem data_atualizado recente:
   ```sql
   SELECT id, criado_em, atualizado_em FROM v_parque_export 
   WHERE id = 'uuid-do-ponto';
   ```

2. Testar RPC de histórico:
   ```sql
   SELECT * FROM ip_historico_ponto(p_id := 'uuid-do-ponto');
   ```
   - Se vazio, histórico não foi registrado

3. Testar RPC de intervenções:
   ```sql
   SELECT * FROM ip_intervencoes(p_id := 'uuid-do-ponto');
   ```

4. Se tabela audit_logs está vazia:
   - RPC pode estar criando registros em outra tabela
   - Verificar no banco qual tabela guarda histórico

---

## 📱 Mapa & UI

### Mapa não responde ao zoom/pan (congelado)

**Sintomas:**
- Mapa lento ao fazer zoom in/out
- Marcadores demoram a atualizar
- CPU/memória alta no DevTools

**Causas:**
- RPC `ip_pontos_bbox` muito lento (muitos dados)
- Muitos marcadores no mapa (>4.000)
- Browser thread está bloqueado

**Investigação:**
```javascript
// DevTools Console:
console.time('refresh');
await refresh();
console.timeEnd('refresh');  // Quanto tempo demora?
```

**Soluções:**
1. Aplicar filtros para reduzir dados:
   - Selecionar bairro único
   - Selecionar tipo único
   - Fazer zoom in

2. Usar visualização agregada:
   - Coroplético (por bairro)
   - Densidade (grade 250m)

3. Verificar performance do RPC:
   - Supabase Dashboard → Logs
   - Ver query time

4. Testar em browser diferente:
   - Firefox vs Chrome vs Safari

---

### Gráficos/Sparklines não aparecem

**Sintomas:**
- Aba de estatísticas vazia
- Sparkline não renderiza
- Coroplético não colore bairros

**Investigação:**
```javascript
// DevTools Console:
console.log(state.config);      // Deve ter configuração
const stats = await rpc('ip_estatisticas', {});
console.log(stats);             // Deve ter dados
```

**Causas:**
- RPC retorna null/error
- Dados vazios
- Erro na renderização SVG

**Soluções:**
1. Testar RPC de estatísticas:
   ```sql
   SELECT * FROM ip_estatisticas();
   ```

2. Verificar se há dados:
   ```sql
   SELECT COUNT(*) FROM v_parque_export;
   ```

3. Forçar re-render:
   - Clicar filtro e remover
   - Fazer zoom diferente
   - Hard refresh: Ctrl+Shift+R

---

## 💾 Netlify Deploy

### Deploy falha no Netlify

**Sintomas:**
- "Build failed" no dashboard
- Erro ao fazer git push
- Site não atualiza após push

**Investigação:**
1. Ir em Netlify Dashboard → seu site → Deploys
2. Clicar em deploy com erro
3. Ver "Deploy log"

**Causas Comuns:**
- Arquivo `index.html` corrompido (syntax erro)
- Variáveis de ambiente não configuradas
- GitHub webhook erro

**Soluções:**
1. Verificar arquivo HTML:
   ```bash
   tidy -q index.html  # Verificar syntax
   ```

2. Verificar variáveis em Netlify Dashboard:
   - Site settings → Build & Deploy → Environment
   - NEXT_PUBLIC_SUPABASE_URL
   - NEXT_PUBLIC_SUPABASE_ANON_KEY

3. Trigger rebuild manual:
   - Dashboard → Deploys → Trigger deploy

4. Ver logs detalhados:
   - Clicar deploy → "View logs"
   - Copiar erro específico

---

### Produção mostra versão antiga

**Sintomas:**
- Mudanças não aparecem após push
- Site mostra conteúdo antigo
- CSS/JS não atualizam

**Causas:**
- Cache do browser (local)
- CDN cache (Netlify)
- Deploy ainda em progresso

**Soluções:**
1. Hard refresh no browser:
   - Ctrl+Shift+R (Windows)
   - Cmd+Shift+R (Mac)

2. Limpar cache local:
   - Ctrl+Shift+Del → Tudo → Period (Tudo o tempo)

3. Aguardar deploy completar:
   - Netlify leva 1-2 min para redeployar
   - Ver Dashboard → Deploy status

4. Limpar cache Netlify:
   - Site settings → Build & Deploy → Clear cache & redeploy

5. Verificar que push foi bem-sucedido:
   ```bash
   git log -1  # Ver último commit
   git status  # Deve estar clean
   ```

---

## 🔄 Supabase Local

### Docker não inicia (supabase start falha)

**Sintomas:**
- `supabase start` retorna erro
- Docker container morre
- "Cannot connect to Docker daemon"

**Investigação:**
```bash
docker ps                          # Docker está rodando?
docker logs supabase_db_1          # Ver logs do container
supabase status                    # Ver status
```

**Causas:**
- Docker não instalado ou não rodando
- Porta 54321/54322 já em uso
- Disco cheio
- Memória insuficiente

**Soluções:**
1. Verificar Docker:
   ```bash
   docker --version              # Deve ter versão
   docker ps                      # Deve funcionar
   ```

2. Se Docker não está rodando:
   ```bash
   # Mac
   open /Applications/Docker.app

   # Linux
   sudo systemctl start docker
   
   # Windows
   # Abrir Docker Desktop
   ```

3. Se porta em uso:
   ```bash
   lsof -i :54321                 # Ver processo
   kill -9 <PID>                  # Matar processo
   supabase start                 # Tentar novamente
   ```

4. Limpar e reiniciar:
   ```bash
   supabase stop
   docker system prune            # Limpar volumes antigos
   supabase start --force-pull
   ```

---

### Porta já em uso

**Sintomas:**
- "Address already in use"
- Cannot bind to port 54321

**Soluções:**
1. Mudar port em `supabase/config.toml`:
   ```toml
   [api]
   port = 54321  # Mudar para 54325 ou outro
   ```

2. Ou liberar porta:
   ```bash
   # Mac/Linux
   lsof -i :54321
   kill -9 <PID>

   # Windows
   netstat -ano | findstr :54321
   taskkill /PID <PID> /F
   ```

---

### Reset do Supabase local

**Se tudo está quebrado:**
```bash
# Parar
supabase stop

# Remover volumes Docker (cuidado!)
docker volume prune

# Reiniciar
supabase start --force-pull
```

**Isso vai:**
- Deletar banco local
- Reaplicar todas migrations
- Reexecutar seed.sql

---

## 🆘 Última Opção: Debug Completo

Se nada funcionar acima:

### 1. Coletar Informações

```javascript
// DevTools Console:
console.log({
  url: window.location.href,
  userAgent: navigator.userAgent,
  localStorage: localStorage.getItem('sb-lrnmydrwzxxajylsmoih-auth-token'),
  state: state,
  map: map ? map.getCenter() : null
});
```

```bash
# Terminal:
git log -1 --format="%H %s"  # Último commit
git status                    # Working tree
netlify status                # Deploy status (se netlify CLI instalado)
```

### 2. Criar Issue no GitHub

Ir em https://github.com/danilosfvalim/iluminacao-led-niteroi/issues/new

Incluir:
- Descrição clara do problema
- Steps para reproduzir (1, 2, 3...)
- Erro exato do console (copiar/colar)
- Versão do navegador
- Screenshots
- Ambiente (produção vs local)

Exemplo:
```
## Problema
Mapa não renderiza após fazer login.

## Steps
1. Abrir site
2. Login com seu@email.com
3. Aguardar 2 seg
4. Mapa continua vazio

## Erro no Console
TypeError: Cannot read property 'getCenter' of undefined at _refresh (index.html:365)

## Navegador
Chrome 121.0.6167.160, Mac OS 14.2

## Supabase
Produção: lrnmydrwzxxajylsmoih.supabase.co
```

### 3. Contatos & Referências

- **GitHub Issues:** https://github.com/danilosfvalim/iluminacao-led-niteroi/issues
- **Supabase Docs:** https://supabase.com/docs
- **Leaflet Docs:** https://leafletjs.com/docs.html
- **Netlify Docs:** https://docs.netlify.com
- **PostgreSQL Docs:** https://www.postgresql.org/docs/

---

## 📋 Checklist de Diagnostico Rápido

Se tiver problema, execute isso:

- [ ] Abrir DevTools Console (F12)
- [ ] Procurar por erros (vermelho)
- [ ] Hard refresh: Ctrl+Shift+R
- [ ] Se problema persiste: copiar erro do console
- [ ] Verificar Network (há 404? timeout?)
- [ ] Testar em outro navegador
- [ ] Se local: `supabase status`
- [ ] Se produção: ver Netlify Dashboard logs
- [ ] Ler TROUBLESHOOTING.md (este arquivo) seção relevante
- [ ] Se ainda preso: criar issue no GitHub com contexto

---

**Última atualização:** 2026-07-07  
**Versão:** 1.0.0
