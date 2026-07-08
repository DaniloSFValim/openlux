# Guia de Integração HTMX - Filtros Dinâmicos

## 📌 Objetivo

Adicionar **filtros cascata** (bairro → tipo → estado) usando HTMX, sem quebrar o sistema atual.

## 🔄 Fluxo Atual vs HTMX

### Antes (Static)
```javascript
// index.html - Linha ~200
document.getElementById('fBairro').addEventListener('change', () => {
  refresh(); // Recarrega TUDO o mapa
});
```

### Depois (Dynamic com HTMX)
```html
<!-- Dropdown de bairros -->
<select id="fBairro" 
  hx-get="/api/v1/tipos?bairro={value}"
  hx-target="#fTipo"
  hx-trigger="change"
  hx-swap="innerHTML">
  <option value="">Todos</option>
  <!-- Options preenchidos -->
</select>

<!-- Dropdown de tipos (recarregado dinamicamente) -->
<select id="fTipo" hx-boost="true">
  <!-- HTMX preenche este conteúdo ao mudar bairro -->
</select>
```

## 🛠️ Setup Incremental

### Step 1: Adicionar HTMX ao Head
```html
<!-- Em index.html, após Supabase JS -->
<script src="https://unpkg.com/htmx.org@1.9.10"></script>

<!-- Configuração HTMX -->
<script>
  // Configurar base URL da API
  htmx.config.baseURL = 'https://seu-dominio.com/api'
  
  // Logging para debug
  htmx.config.logAll = false; // true para desenvolvimento
</script>
```

### Step 2: Criar Endpoint de API (Supabase)

Você pode usar Edge Functions do Supabase:

```sql
-- supabase/functions/tipos-por-bairro/index.ts
import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

serve(async (req) => {
  const { searchParams } = new URL(req.url)
  const bairro = searchParams.get('bairro')

  // Query para buscar tipos únicos por bairro
  const tipos = await supabase
    .from('v_parque_export')
    .select('tipo_luminaria')
    .eq('bairro_nome', bairro)
    .distinct()

  // Retornar HTML com <option> tags
  return new Response(`
    <option value="">Todos</option>
    ${tipos.data.map(t => `<option value="${t.tipo_luminaria}">${t.tipo_luminaria}</option>`).join('')}
  `, {
    headers: { 'Content-Type': 'text/html' }
  })
})
```

### Step 3: Refatorar Filtros

```html
<!-- Em index.html, linha ~90 -->

<!-- ANTES -->
<label>Tipo<select id="fTipo"><option value="">Todos</option></select></label>

<!-- DEPOIS (com HTMX) -->
<label>
  Tipo
  <select id="fTipo" 
    hx-trigger="load" 
    hx-swap="innerHTML swap:1s">
    <option value="" hx-indicator="#loading">Carregando…</option>
  </select>
</label>
```

## 📋 Exemplo Completo: Filtros Cascata

```html
<div class="filtro-container">
  <!-- 1. Bairro (dispara call para tipos) -->
  <label>
    🏢 Bairro
    <select id="fBairro" name="bairro"
      hx-get="/api/v1/tipos-por-bairro"
      hx-target="#fTipo"
      hx-trigger="change"
      hx-swap="innerHTML swap:200ms"
      hx-indicator="#loading">
      <option value="">Todos</option>
      <option value="Centro">Centro</option>
      <option value="Pendotiba">Pendotiba</option>
      <!-- ... -->
    </select>
  </label>

  <!-- 2. Tipo (preenchido dinamicamente) -->
  <label>
    💡 Tipo
    <select id="fTipo" name="tipo"
      hx-get="/api/v1/estados-por-tipo"
      hx-target="#fEstado"
      hx-trigger="change"
      hx-swap="innerHTML swap:200ms">
      <option value="">Todos</option>
      <!-- Preenchido por HTMX ao selecionar bairro -->
    </select>
  </label>

  <!-- 3. Estado (preenchido dinamicamente) -->
  <label>
    🔆 Estado
    <select id="fEstado" name="estado"
      hx-trigger="change"
      hx-post="/api/v1/aplicar-filtros"
      hx-swap="outerHTML"
      hx-target="#map-results">
      <option value="">Todos</option>
      <!-- Preenchido por HTMX ao selecionar tipo -->
    </select>
  </label>

  <!-- Loading indicator -->
  <div id="loading" class="htmx-request" style="display:none;">
    <span class="spinner"></span> Carregando...
  </div>
</div>
```

## 🔌 Eventos HTMX (JavaScript)

```javascript
// Ao carregar os filtros
document.body.addEventListener('htmx:afterSwap', (event) => {
  if (event.detail.xhr.responseURL.includes('/tipos')) {
    console.log('✅ Tipos carregados dinamicamente')
  }
})

// Antes de enviar requisição
document.body.addEventListener('htmx:beforeRequest', (event) => {
  // Validação ou logging
  console.log('📤 Enviando:', event.detail.path)
})

// Após erro
document.body.addEventListener('htmx:responseError', (event) => {
  console.error('❌ Erro HTMX:', event.detail)
})
```

## 🚀 Implementação Incremental (Low Risk)

### Semana 1: Teste Local
```bash
# 1. Copiar index.html para index-htmx-test.html
# 2. Adicionar HTMX CDN
# 3. Testar um dropdown (ex: fBairro → fTipo)
# 4. Não fazer merge ainda
```

### Semana 2: Validação
```bash
# 1. Se funcionar: testar cascata completa
# 2. Testes E2E (Playwright)
# 3. Performance test (Lighthouse)
# 4. Compatibilidade browser
```

### Semana 3: Merge
```bash
# 1. Fazer PR com HTMX integrado
# 2. Code review
# 3. Merge para main
# 4. Monitor produção
```

## ⚠️ Considerações

### Não Break Things
- ✅ HTMX é **progressive enhancement**
- ✅ Se HTMX não carregar, forms funcionam normalmente
- ✅ Sem mudanças no Supabase ou backend

### Performance
- ✅ HTMX 13KB gzip (negligível)
- ✅ Menos requisições ao mapa (só refresh quando necessário)
- ✅ Smooth transitions (~200ms)

### Browser Support
- ✅ Chrome, Firefox, Safari, Edge (all modern versions)
- ❌ IE 11 (não importa, EOL)

## 📊 Diagrama de Fluxo

```
┌─────────────────────────────────────────┐
│ Usuário clica dropdown Bairro           │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ HTMX: hx-get /api/v1/tipos-por-bairro  │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ Supabase Edge Function                  │
│ - Query v_parque_export                 │
│ - Filter by bairro_nome                 │
│ - Select distinct tipo_luminaria        │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ Retorna HTML <option> tags              │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ HTMX: hx-swap="innerHTML swap:200ms"   │
│ Insere opções em #fTipo com transição  │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ Usuário seleciona tipo                  │
│ Cascata continua → fEstado              │
└─────────────────────────────────────────┘
```

## 🔗 Exemplo Real (Supabase Edge Function)

```typescript
// supabase/functions/api/tipos-por-bairro/index.ts

import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from "https://esm.sh/@supabase/supabase-js@2"

const supabaseUrl = Deno.env.get('SUPABASE_URL')
const supabaseKey = Deno.env.get('SUPABASE_ANON_KEY')

const supabase = createClient(supabaseUrl, supabaseKey)

serve(async (req) => {
  // CORS headers
  if (req.method === 'OPTIONS') {
    return new Response(null, {
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
      }
    })
  }

  const { searchParams } = new URL(req.url)
  const bairro = searchParams.get('bairro')

  if (!bairro) {
    return new Response(`
      <option value="">Todos</option>
    `, { headers: { 'Content-Type': 'text/html; charset=utf-8' } })
  }

  try {
    const { data, error } = await supabase
      .from('v_parque_export')
      .select('tipo_luminaria')
      .eq('bairro_nome', bairro)
      .order('tipo_luminaria', { ascending: true })

    if (error) throw error

    const tipos = [...new Set(data.map(d => d.tipo_luminaria).filter(Boolean))]

    const html = `
      <option value="">Todos</option>
      ${tipos.map(t => `<option value="${t}">${t}</option>`).join('')}
    `

    return new Response(html, {
      headers: {
        'Content-Type': 'text/html; charset=utf-8',
        'Access-Control-Allow-Origin': '*'
      }
    })
  } catch (error) {
    console.error('Erro:', error)
    return new Response(`<option value="">Erro ao carregar</option>`, {
      status: 500,
      headers: { 'Content-Type': 'text/html; charset=utf-8' }
    })
  }
})
```

## ✅ Checklist de Integração

- [ ] HTMX adicionado ao HEAD
- [ ] Edge Functions criadas (tipos-por-bairro, estados-por-tipo)
- [ ] Selects refatorados com hx-* attributes
- [ ] Eventos HTMX vinculados (afterSwap, responseError)
- [ ] Testes funcionais locais
- [ ] Testes E2E (Playwright)
- [ ] Lighthouse test
- [ ] Compatibilidade browser
- [ ] Code review
- [ ] Merge com feature flag (opcional)

## 📞 Support

- HTMX Docs: https://htmx.org/
- Supabase Edge Functions: https://supabase.com/docs/guides/functions
- Browser DevTools (F12) → Network para debugar requisições HTMX

---

**Complexidade:** Média  
**Tempo de implementação:** 2-3 horas  
**Risk:** Baixo (progressive enhancement)  
**Ganho:** Dinâmica melhorada, menos page reloads
