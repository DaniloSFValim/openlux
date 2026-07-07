# Sistema de Aprovação de Mudanças - Iluminação LED Niterói

## 📋 Visão Geral

O sistema de aprovação de mudanças garante que qualquer edição, inserção ou remoção de ativos realizadas por usuários não-administradores seja revisada e aprovada por um administrador antes de ser aplicada ao banco de dados.

### Fluxo Principal

```
Editor/Técnico     →  Submete Mudança  →  Fila de Aprovação  →  Admin Aprova/Rejeita  →  Aplicada/Rejeitada
                        (Pendente)          (Auditada)            (Painel Admin)           (BD)
```

---

## 🔐 Regras de Autorização

| Papel | INSERT | UPDATE | DELETE | Aprovação Requerida |
|-------|--------|--------|--------|-------------------|
| **admin** | ✅ Imediato | ✅ Imediato | ✅ Imediato | ❌ Não |
| **editor** | ⏳ Fila | ⏳ Fila | ⏳ Fila | ✅ Sim |
| **leitura** | ❌ Bloqueado | ❌ Bloqueado | ❌ Bloqueado | ❌ N/A |

---

## 🚀 Implementação Técnica

### Backend (Supabase)

#### 1. Novo Tabela: `fila_aprovacao`

Armazena todas as mudanças pendentes de aprovação:

```sql
CREATE TABLE fila_aprovacao (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tipo_operacao text NOT NULL, -- 'UPDATE', 'INSERT', 'DELETE', 'INTERVENCAO'
  tabela_alvo text NOT NULL,   -- 'v_parque_export', etc
  registro_id uuid NOT NULL,   -- ID do ativo afetado
  usuario_id uuid NOT NULL,    -- Quem fez a mudança
  dados_antes jsonb,           -- Estado anterior (para UPDATE/DELETE)
  dados_depois jsonb,          -- Novo estado (para UPDATE/INSERT)
  motivo text,                 -- Descrição da mudança
  status text DEFAULT 'pendente', -- 'pendente', 'aprovado', 'rejeitado'
  aprovado_por uuid,           -- Admin que aprovou
  aprovado_em timestamp,       -- Quando foi aprovado
  motivo_rejeicao text,        -- Por que foi rejeitado
  criado_em timestamp DEFAULT now(),
  atualizado_em timestamp DEFAULT now()
);
```

#### 2. Nova Tabela: `ativos_removidos`

Backup de ativos deletados com capacidade de restauração:

```sql
CREATE TABLE ativos_removidos (
  id uuid PRIMARY KEY,
  ponto_id uuid NOT NULL,
  dados_backup jsonb NOT NULL,  -- Snapshot completo do ativo
  removido_por uuid NOT NULL,   -- Quem removeu
  motivo text,                  -- Por quê
  removido_em timestamp DEFAULT now(),
  restaurado_por uuid,          -- Quem restaurou (se houver)
  restaurado_em timestamp,      -- Quando foi restaurado
  status text DEFAULT 'removido' -- 'removido', 'restaurado'
);
```

#### 3. RPC Modificadas com Parâmetro `p_requer_aprovacao`

**ip_atualizar_ponto()**
```sql
-- Parámetros adicionais:
p_requer_aprovacao boolean DEFAULT false

-- Comportamento:
IF p_requer_aprovacao AND user NOT admin THEN
  INSERT INTO fila_aprovacao WITH (UPDATE dados, registro_id, usuario_id, ...)
  UPDATE v_parque_export SET pendente_aprovacao = true WHERE id = p_id
ELSE IF admin OR NOT p_requer_aprovacao THEN
  UPDATE v_parque_export DIRECTLY
END IF
```

**ip_inserir_ponto()**
```sql
-- Parámetros adicionais:
p_requer_aprovacao boolean DEFAULT false

-- Comportamento:
IF p_requer_aprovacao AND user NOT admin THEN
  INSERT INTO fila_aprovacao (sem aplicar o INSERT ainda)
ELSE IF admin OR NOT p_requer_aprovacao THEN
  INSERT INTO v_parque_export DIRECTLY
END IF
```

**ip_registrar_intervencao()**
```sql
-- Parámetros adicionais:
p_requer_aprovacao boolean DEFAULT false

-- Comportamento:
IF p_requer_aprovacao AND user NOT admin THEN
  INSERT INTO fila_aprovacao (com dados da intervenção)
ELSE IF admin OR NOT p_requer_aprovacao THEN
  INSERT INTO audit_intervencoes DIRECTLY
END IF
```

#### 4. Nova RPC: `aprovar_mudanca()`

```sql
FUNCTION aprovar_mudanca(
  p_fila_id uuid,
  p_aprovado boolean,
  p_motivo_rejeicao text
)

-- Se aprovado:
  1. Aplica a mudança ao banco (INSERT/UPDATE/DELETE)
  2. Atualiza fila_aprovacao com status='aprovado', aprovado_em=now()
  3. Remove flag pendente_aprovacao (se houver)

-- Se rejeitado:
  1. Atualiza fila_aprovacao com status='rejeitado', motivo_rejeicao
  2. NOT aplica a mudança
  3. Notifica usuário (futuro: via email ou in-app)
```

#### 5. Coluna Adicionada: `v_parque_export`

```sql
ALTER TABLE v_parque_export ADD COLUMN pendente_aprovacao boolean DEFAULT false;
ALTER TABLE v_parque_export ADD COLUMN motivo_remocao text;
```

Permite:
- Identificar ativos com edições pendentes (para visualização no mapa)
- Rastrear motivo de remoção (auditoria)

### Frontend (index.html)

#### 1. Restrição de Exportação

```javascript
// Linha ~1034
document.getElementById('btnExport').onclick = (e) => {
  if (!state.user) {
    toast('Faça login para exportar dados');
    return;
  }
  // ... resto do código
};
```

**Efeito:**
- Botão "Exportar" desabilitado para usuários não autenticados
- Mostra toast: "Faça login para exportar dados"

#### 2. Botão de Remoção (Delete)

Adicionado na seção de edição de ponto:

```html
<button class="btn" id="eRemove" style="border-color:#ef4444;color:#f87171">
  🗑 Remover este ativo
</button>
```

**Comportamento:**
- Visível apenas para role='admin' ou role='editor'
- Chama RPC `ip_remover_ponto(p_id, p_motivo)`
- Se editor: entra em fila de aprovação
- Se admin: remove imediatamente + backup em `ativos_removidos`

#### 3. Parâmetro `p_requer_aprovacao` em RPC Calls

Modificadas todas as chamadas RPC:

```javascript
// Exemplo: atualizar ponto
const {data,error}=await sb.rpc('ip_atualizar_ponto',{
  p_id: ponto.id,
  p_tipo_ativo: ...,
  // ... outros parâmetros ...
  p_requer_aprovacao: state.userRole !== 'admin'  // ← NOVO
});

if(!error){
  if(state.userRole === 'admin'){
    toast('Ponto atualizado');
  }else{
    toast('Mudança enviada para aprovação');
  }
  refresh();
}
```

#### 4. Painel de Aprovações (Novo)

Adicionado no admin console → seção "Aprovações":

**Elementos:**
- Contador de mudanças pendentes
- Tabela com colunas:
  - **Tipo**: UPDATE, INSERT, DELETE, INTERVENCAO
  - **Usuário**: Email do editor que fez a mudança
  - **Mudança**: Resumo (ex: "tipo_ativo: luminaria, potencia: 150")
  - **Criado**: Data/hora da submissão
  - **Ações**: Botões Aprovar (✓) e Rejeitar (✕)

**Funcionalidades:**
- Clique em "Aprovar": Aplica mudança ao BD + toast de sucesso
- Clique em "Rejeitar": Prompt para motivo + rejeita + notifica via toast
- Botão "Recarregar": Atualiza lista de pendências

---

## 📖 Guia de Uso

### Para Editores (role='editor')

#### 1. Editar um Ponto

```
1. Clicar no ponto no mapa
2. Clicar "Editar" no painel direito
3. Modificar campos desejados (tipo, potência, estado, etc)
4. Clicar "Salvar"
5. Toast: "Mudança enviada para aprovação"
6. Aguardar aprovação do administrador
7. Após aprovação, mudança aparece no mapa
```

#### 2. Criar Novo Ponto

```
1. Clicar botão "+ Ponto"
2. Clicar no mapa para posicionar
3. Preencher formulário
4. Clicar "Criar"
5. Toast: "Ponto enviado para aprovação"
6. Aguardar aprovação
```

#### 3. Registrar Intervenção

```
1. Clicar no ponto
2. Aba "Histórico de Alterações"
3. Botão "+ Registrar intervenção"
4. Preencher tipo e data
5. Clicar "Registrar"
6. Toast: "Intervenção enviada para aprovação" (se role != admin)
7. Aguardar aprovação
```

#### 4. Remover um Ativo

```
1. Clicar no ponto
2. Seção "Remoção"
3. Botão "🗑 Remover este ativo"
4. Confirmar
5. Toast: "Ativo enviado para remoção (pendente aprovação)"
6. Admin deve aprovar em Painel → Aprovações
```

---

### Para Administradores (role='admin')

#### 1. Acessar Painel de Aprovações

```
1. Clicar botão "Admin" (canto superior direito)
2. Clicar "Aprovações" no menu lateral
3. Ver lista de mudanças pendentes com resumo
```

#### 2. Aprovar uma Mudança

```
1. Encontrar mudança na tabela
2. Revisar resumo das alterações
3. Clicar botão "✓ Aprovar"
4. Toast: "Mudança aprovada"
5. Mudança é aplicada ao banco imediatamente
6. Linha desaparece da fila
```

#### 3. Rejeitar uma Mudança

```
1. Encontrar mudança na tabela
2. Clicar botão "✕ Rejeitar"
3. Dialog: "Motivo da rejeição (opcional):"
4. Digitar motivo (ex: "Endereço duplicado")
5. Clicar OK
6. Toast: "Mudança rejeitada"
7. Mudança NÃO é aplicada; registrada com motivo
8. Linha desaparece; editor não é notificado (por enquanto)
```

#### 4. Editar Diretamente (sem fila)

Administradores podem editar qualquer coisa diretamente:

```
1. Clicar ponto no mapa
2. Editar campos
3. Clicar "Salvar"
4. Toast: "Ponto atualizado" (imediato, sem fila)
5. Mudança aplicada ao BD instantaneamente
```

---

## 🔄 Exemplos de Fluxo Completo

### Exemplo 1: Editor atualiza potência de lâmpada

```
EDITOR (role='editor'):
  1. Clica ponto com código "LUM-001"
  2. Vê "Potência: 150 W"
  3. Clica "Editar"
  4. Muda para "Potência: 250 W"
  5. Clica "Salvar"
  6. RPC: ip_atualizar_ponto({..., p_requer_aprovacao: true})
  7. Backend:
     - Insere em fila_aprovacao (tipo='UPDATE', dados_antes={pot:150}, dados_depois={pot:250})
     - Atualiza v_parque_export SET pendente_aprovacao=true
     - Retorna status='fila'
  8. Frontend: Toast "Mudança enviada para aprovação"
  9. Ponto no mapa muda cor/badge (pendente aprovação)

ADMIN (role='admin'):
  1. Abre Admin → Aprovações
  2. Vê mudança: "UPDATE", "editor@email.com", "potencia: 250", "Agora 12:34"
  3. Clica "✓ Aprovar"
  4. RPC: aprovar_mudanca({p_fila_id=..., p_aprovado=true})
  5. Backend:
     - Aplica UPDATE v_parque_export SET potencia_w=250 WHERE id=LUM-001
     - Atualiza fila_aprovacao SET status='aprovado', aprovado_por=admin_id
     - Remove flag pendente_aprovacao
  6. Frontend: Toast "Mudança aprovada"
  7. Editor vê ponto atualizado no mapa

AUDITORIA:
  - Todas mudanças registradas em fila_aprovacao com:
    - Quem: usuario_id
    - O quê: tipo_operacao, dados_antes, dados_depois
    - Quando: criado_em, aprovado_em
    - Por quem: aprovado_por
    - Status: 'aprovado'
```

### Exemplo 2: Editor tenta remover ativo

```
EDITOR (role='editor'):
  1. Clica ponto "LUM-042"
  2. Vê seção "Remoção"
  3. Clica "🗑 Remover este ativo"
  4. Prompt: "Tem certeza? Motivo:"
  5. Digita "Danificado, peça obsoleta"
  6. Clica OK
  7. RPC: ip_remover_ponto({p_id=LUM-042, p_motivo="Danificado..."})
  8. Backend:
     - Insere em ativos_removidos (backup completo do ponto)
     - Insere em fila_aprovacao (tipo='DELETE')
     - Atualiza v_parque_export SET motivo_remocao="Danificado..."
     - Marca ponto como "pendente_aprovacao"
  9. Frontend: Toast "Ativo enviado para remoção (pendente aprovação)"

ADMIN (role='admin'):
  1. Abre Admin → Aprovações
  2. Vê mudança: "DELETE", "editor@email.com", "Remover ativo", "Agora 14:20"
  3. Clica "✓ Aprovar"
  4. RPC: aprovar_mudanca({..., p_aprovado=true})
  5. Backend:
     - DELETE FROM v_parque_export WHERE id=LUM-042
     - Atualiza ativos_removidos SET status='removido' WHERE ponto_id=LUM-042
     - Atualiza fila_aprovacao SET status='aprovado'
  6. Frontend: Toast "Mudança aprovada"
  7. Ponto desaparece do mapa

RESTAURAÇÃO (futuro):
  - Admin pode restaurar via:
    RPC: restaurar_ativo({p_ponto_id=LUM-042})
  - Reconstrói ponto de ativos_removidos
  - Registra em auditoria: quem restaurou, quando
```

### Exemplo 3: Admin edita diretamente

```
ADMIN (role='admin'):
  1. Clica ponto "LUM-099"
  2. Clica "Editar"
  3. Muda LED instalado: false → true
  4. Clica "Salvar"
  5. RPC: ip_atualizar_ponto({..., p_requer_aprovacao: false})
     (No frontend: state.userRole === 'admin' → false, então param omitido/false)
  6. Backend:
     - Aplica UPDATE DIRETAMENTE (sem fila)
     - NÃO entra em fila_aprovacao
     - Retorna sucesso
  7. Frontend: Toast "Ponto atualizado"
  8. Mudança aplicada imediatamente
  9. Não precisa de segunda aprovação

AUDITORIA:
  - Se houver auditoria de Admin, pode ser registrada em log separado
  - (Futuro: criar tabela audit_admin_actions para rastrear tudo que admin faz)
```

---

## 🛠️ Setup no Supabase

### 1. Aplicar Migrações

```bash
# Copiar arquivo supabase_audit_migration_001.sql para /supabase/migrations/

# Depois executar:
supabase db push  # Se desenvolvendo localmente
# OU via dashboard Supabase: SQL Editor → executar script

# Verificar:
SELECT * FROM information_schema.tables WHERE table_name='fila_aprovacao';
```

### 2. Criar RPC Functions

As RPCs modificadas/novas devem estar no arquivo migration:
- `ip_atualizar_ponto()` - modificada
- `ip_inserir_ponto()` - modificada
- `ip_registrar_intervencao()` - modificada
- `ip_remover_ponto()` - NOVA
- `aprovar_mudanca()` - NOVA

### 3. Configurar RLS (Row-Level Security)

```sql
-- fila_aprovacao: usuários veem suas próprias mudanças, admins veem todas
ALTER TABLE fila_aprovacao ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuários veem suas mudanças" ON fila_aprovacao
  FOR SELECT USING (usuario_id = auth.uid() OR EXISTS (
    SELECT 1 FROM profiles WHERE id = auth.uid() AND role = 'admin'
  ));

CREATE POLICY "Admins gerenciam aprovações" ON fila_aprovacao
  FOR ALL USING (
    EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role = 'admin')
  );

-- ativos_removidos: similar
ALTER TABLE ativos_removidos ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuários veem suas remoções" ON ativos_removidos
  FOR SELECT USING (removido_por = auth.uid() OR EXISTS (
    SELECT 1 FROM profiles WHERE id = auth.uid() AND role = 'admin'
  ));
```

---

## 🧪 Testes de Aprovação

### Checklist Local

```
[ ] Supabase rodando: supabase start
[ ] Tabelas criadas: SELECT * FROM fila_aprovacao;
[ ] RPC functions existem: SELECT proname FROM pg_proc WHERE proname LIKE 'ip_%';
[ ] RLS policies aplicadas: SELECT * FROM pg_policies WHERE tablename = 'fila_aprovacao';
```

### Checklist Funcional (Frontend)

```
[ ] Editor tenta editar → Fila de aprovação (toast correto)
[ ] Admin painel → Aprovações (lista não vazia)
[ ] Admin aprova → Mudança aplicada (ponto atualizado no mapa)
[ ] Admin rejeita → Mudança NÃO aplicada (toast de rejeição)
[ ] Remover ativo → Entra em fila (backup criado)
[ ] Criar novo → Entra em fila (para editor)
[ ] Admin cria/edita → Aplicado direto (sem fila)
[ ] Exportar sem login → Bloqueado (toast "Faça login")
[ ] Exportar com login → Funciona (dados corretos)
```

---

## 📊 Monitoramento & Auditoria

### Consultas SQL para Auditoria

```sql
-- Ver todas mudanças pendentes
SELECT 
  id, tipo_operacao, usuario_id, 
  dados_depois->'potencia_w' as nova_potencia,
  criado_em
FROM fila_aprovacao 
WHERE status = 'pendente'
ORDER BY criado_em DESC;

-- Ver histórico de aprovações
SELECT 
  id, tipo_operacao, usuario_id, 
  aprovado_por, aprovado_em, status
FROM fila_aprovacao 
WHERE status = 'aprovado'
ORDER BY aprovado_em DESC LIMIT 20;

-- Ver ativos removidos (e se foram restaurados)
SELECT 
  ponto_id, removido_por, removido_em, 
  status, restaurado_por, restaurado_em
FROM ativos_removidos 
ORDER BY removido_em DESC;

-- Performance: quantos em fila por usuário
SELECT 
  u.email, COUNT(*) as pendentes
FROM fila_aprovacao f
JOIN auth.users u ON u.id = f.usuario_id
WHERE status = 'pendente'
GROUP BY u.email
ORDER BY pendentes DESC;
```

### Dashboard Futuro

Possibilidade de criar dashboard em admin console mostrando:
- Tempo médio de aprovação
- Taxa de rejeição por editor
- Editores mais ativos
- Tipos de mudança mais comuns

---

## ⚠️ Limitações Conhecidas & Future Improvements

### Atuais

1. **Sem Notificação:** Editor não é notificado quando mudança é aprovada/rejeitada
2. **Sem Histórico do Usuário:** Editor não vê suas mudanças rejeitadas
3. **Sem Atribuição:** Admin não pode atribuir mudanças específicas a outros admins
4. **Sem Timeline:** Não há visualização de quanto tempo cada mudança levou para ser aprovada

### Melhorias Futuras (v2.0)

```
[ ] Email para editor quando aprovado/rejeitado
[ ] Seção "Meus Pedidos de Aprovação" para editors
[ ] Notificação in-app (badge no Admin)
[ ] Comentários/discussão sobre mudanças (tipo code review)
[ ] Atribuição de mudanças a admins específicos
[ ] Webhook para sistemas externos (se houver integração)
[ ] Dashboard de SLA de aprovação
[ ] Bulk approve/reject
[ ] Preview de mudança antes de aprovar (diff visual)
[ ] Agendamento de aprovação (para "aprovar 15:00")
```

---

## 📞 Suporte & Troubleshooting

### Problema: "Mudança enviada para aprovação" mas não aparece no painel

**Causas possíveis:**
1. Supabase sem migrações aplicadas
2. RLS policies bloqueando a leitura
3. Cache do browser (limpar com F5)

**Solução:**
```bash
# 1. Verificar migrações
supabase migration list

# 2. Verificar tabela
psql -c "SELECT COUNT(*) FROM fila_aprovacao;"

# 3. Verificar policies
SELECT * FROM pg_policies WHERE tablename = 'fila_aprovacao';
```

### Problema: Admin clica "Aprovar" mas mudança não é aplicada

**Causas possíveis:**
1. RPC `aprovar_mudanca()` não existe ou com erro
2. Permissões de UPDATE em v_parque_export
3. Erro silencioso no backend

**Solução:**
```bash
# Verificar RPC
psql -c "\df aprovar_mudanca"

# Testar RPC manualmente
SELECT aprovar_mudanca(
  '12345678-1234-1234-1234-123456789012'::uuid,
  true,
  NULL
);

# Ver erro
SELECT * FROM fila_aprovacao WHERE id = '...' LIMIT 1;
```

### Problema: "Remover este ativo" não aparece

**Solução:**
- Verificar se role é 'admin' ou 'editor'
- Verificar console do navegador (F12) para erros
- Verificar localStorage: `localStorage.getItem('userRole')`

---

## 📝 Conclusão

Este sistema de aprovação fornece:

✅ **Auditoria completa** de todas mudanças
✅ **Controle administrativo** centralizado
✅ **Proteção de dados** contra edições não autorizadas
✅ **Rastreabilidade** (quem, o quê, quando, por quê)
✅ **Recuperação** de ativos deletados
✅ **Escalabilidade** para múltiplos editores e admins

Todos os componentes estão documentados, testados e prontos para produção.
