# Guia de Deployment - Sistema de Aprovação

## 📋 Checklist de Deployment

Siga estes passos **na ordem exata** para evitar problemas:

---

## Fase 1: Preparação (Local)

### 1.1 Verificar Arquivos

```bash
# Você deve ter recebido:
# 1. index.html (modificado com interface de aprovações)
# 2. supabase_audit_migration_001.sql (schema do BD)
# 3. Este guia (DEPLOYMENT_GUIDE.md)
# 4. APPROVAL_WORKFLOW.md (documentação)

ls -la index.html
# -rw-r--r-- 1 user staff 45678 Nov 7 12:34 index.html

wc -l index.html
# 1215 (deve ser > 1200)
```

### 1.2 Criar Backup Atual

```bash
# ANTES de modificar nada:
cp index.html index.html.backup.$(date +%Y%m%d_%H%M%S)
git add index.html.backup.*
git commit -m "chore: backup de index.html antes de approval workflow"
```

---

## Fase 2: Supabase Backend

### 2.1 Abrir SQL Editor

```
1. Ir em https://app.supabase.com
2. Selecionar seu projeto (iluminacao-led-niteroi)
3. No menu esquerdo: SQL Editor
4. Clique em "+ New query"
```

### 2.2 Executar Migrações

```bash
# Abrir arquivo: supabase_audit_migration_001.sql
# Copiar TODO o conteúdo

# No SQL Editor do Supabase:
# 1. Colar conteúdo
# 2. Botão "▶ Run" (ou Ctrl+Enter)
# 3. Aguardar execução
```

**Resultado esperado:**
```
Query executed successfully. X rows affected.

(Sem errors)
```

### 2.3 Verificar Tabelas

```sql
-- No SQL Editor, executar:
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' AND table_name IN ('fila_aprovacao', 'ativos_removidos')
ORDER BY table_name;
```

**Resultado:**
```
table_name
─────────────────
ativos_removidos
fila_aprovacao
```

### 2.4 Verificar RLS Policies

```sql
SELECT policyname, tablename FROM pg_policies 
WHERE tablename IN ('fila_aprovacao', 'ativos_removidos')
ORDER BY tablename;
```

**Resultado:**
```
policyname                         tablename
────────────────────────────────   ──────────────────
Usuários veem suas mudanças         fila_aprovacao
Admins gerenciam aprovações         fila_aprovacao
(... etc, total ~4 policies)
```

### 2.5 Verificar RPC Functions

```sql
SELECT routine_name, routine_type FROM information_schema.routines 
WHERE routine_schema = 'public' AND routine_name LIKE 'ip_%'
ORDER BY routine_name;
```

**Resultado esperado:**
```
routine_name                  routine_type
────────────────────────────  ────────────
ip_atualizar_ponto            FUNCTION    ← MODIFICADA
ip_clusters_grid              FUNCTION
ip_estadisticas               FUNCTION
...
ip_inserir_ponto              FUNCTION    ← MODIFICADA
ip_pontos_bbox                FUNCTION
ip_registrar_intervencao      FUNCTION    ← MODIFICADA
ip_remover_ponto              FUNCTION    ← NOVA
aprovar_mudanca               FUNCTION    ← NOVA
...
```

### 2.6 Testar RPC (Opcional)

```sql
-- Testar se ip_remover_ponto existe:
SELECT 1 FROM information_schema.routines 
WHERE routine_name = 'ip_remover_ponto';

-- Resultado: 1 row (se existir)
```

---

## Fase 3: Deploy Frontend

### 3.1 Fazer Upload do index.html Modificado

**Opção A: Via Git (Recomendado)**

```bash
# No seu repositório local:
git checkout main  # ou branch de produção

# Se recebeu arquivo novo:
cp /path/to/novo/index.html ./

# Verificar mudanças:
git diff index.html | head -50
# Deve mostrar seção "Aprovações" adicionada

# Commit:
git add index.html
git commit -m "feat: deploy approval workflow interface (production)"

# Push:
git push origin main
```

**Resultado:** Netlify detecta push, rebuilda automaticamente em ~2 min.

**Opção B: Manual (Netlify UI)**

```
1. Ir em https://app.netlify.com
2. Selecionar seu site (iluminacao-led-niteroi)
3. Seção "Deploys" → "Deploy settings"
4. Opção "Drag and drop to deploy" ou "Connect to Git"
5. Arrastar o arquivo index.html para a área
6. Aguardar "Published" (verde)
```

### 3.2 Verificar Deploy

```
1. Ir em https://seu-site.netlify.app
2. Abrir DevTools (F12)
3. Console: Não deve haver erros em vermelho
4. Procurar pelo botão "Admin" (canto superior direito)
5. Se aparecer "Aprovações" no menu admin, OK!
```

---

## Fase 4: Testes Funcionais

### 4.1 Teste como EDITOR

```
Usuário: editor@seu-dominio.com
Senha: (a que foi criada)

PASSOS:
1. Fazer login
2. Clicar em um ponto no mapa
3. Clicar "Editar"
4. Mudar um campo (ex: potência)
5. Clicar "Salvar"

RESULTADO ESPERADO:
✓ Toast: "Mudança enviada para aprovação"
✓ Ponto ainda visível no mapa
✓ Mudança NÃO é aplicada imediatamente

VERIFICAÇÃO NO BANCO:
SELECT COUNT(*) FROM fila_aprovacao WHERE status = 'pendente';
# Resultado: 1 (ou mais)
```

### 4.2 Teste como ADMIN (Visualizar Fila)

```
Usuário: admin@seu-dominio.com
Senha: (a que foi criada)

PASSOS:
1. Fazer login
2. Clicar botão "Admin" (vermelho, canto direito)
3. Clicar menu "Aprovações"
4. Deve aparecer a mudança criada acima

RESULTADO ESPERADO:
✓ Tabela mostra: "UPDATE", "editor@seu-dominio.com", resumo, timestamp
✓ Contador no topo mostra 1 (ou mais) mudanças pendentes
✓ Botões "✓ Aprovar" e "✕ Rejeitar" são clicáveis
```

### 4.3 Teste APROVAR Mudança

```
PASSOS (continuando do teste anterior):
1. Clicar "✓ Aprovar"
2. Aguardar ~2 segundos

RESULTADO ESPERADO:
✓ Toast: "Mudança aprovada"
✓ Linha desaparece da tabela
✓ Contador diminui para 0 (ou anterior-1)

VERIFICAÇÃO NO BANCO:
SELECT COUNT(*) FROM fila_aprovacao WHERE status = 'aprovado';
# Resultado: 1

SELECT * FROM v_parque_export WHERE id = 'ponto_modificado_id'
# Campo modificado agora tem o novo valor
```

### 4.4 Teste REJEITAR Mudança

```
PASSOS:
1. Editor: Editar outro ponto, mudar algo, Salvar
2. Admin: Abrir Admin → Aprovações
3. Ver nova mudança
4. Clicar "✕ Rejeitar"
5. Dialog: "Motivo da rejeição:"
6. Digitar: "Valor inconsistente"
7. Clicar OK

RESULTADO ESPERADO:
✓ Toast: "Mudança rejeitada"
✓ Linha desaparece
✓ Ponto NO MAPA não é atualizado

VERIFICAÇÃO NO BANCO:
SELECT * FROM fila_aprovacao 
WHERE status = 'rejeitado' AND motivo_rejeicao = 'Valor inconsistente';
# Resultado: 1 row
```

### 4.5 Teste ADMIN EDITA (Sem Fila)

```
PASSOS:
1. Admin: Clicar ponto qualquer
2. Clicar "Editar"
3. Mudar um campo
4. Clicar "Salvar"

RESULTADO ESPERADO:
✓ Toast: "Ponto atualizado" (imediato)
✓ Mudança aplicada ao mapa INSTANTANEAMENTE
✓ NÃO entra em fila_aprovacao

VERIFICAÇÃO NO BANCO:
SELECT COUNT(*) FROM fila_aprovacao WHERE status = 'pendente';
# Resultado: 0 (nenhuma nova entrada)
```

### 4.6 Teste REMOVER ATIVO

```
PASSOS (Editor):
1. Editor faz login
2. Clicar ponto qualquer
3. Procurar seção "Remoção"
4. Clica "🗑 Remover este ativo"
5. Confirma

RESULTADO ESPERADO:
✓ Toast: "Ativo enviado para remoção (pendente aprovação)"
✓ Ponto ainda visível no mapa

VERIFICAÇÃO NO BANCO:
SELECT COUNT(*) FROM fila_aprovacao 
WHERE tipo_operacao = 'DELETE' AND status = 'pendente';
# Resultado: 1

SELECT * FROM ativos_removidos 
WHERE status = 'removido' ORDER BY removido_em DESC LIMIT 1;
# Resultado: dados do ponto em backup
```

### 4.7 Teste EXPORTAR (Autenticado)

```
PASSOS (não-autenticado):
1. NÃO fazer login
2. Clicar "Exportar"

RESULTADO ESPERADO:
✓ Toast: "Faça login para exportar dados"
✓ Menu de exportação NÃO abre

PASSOS (autenticado):
1. Fazer login (qualquer role)
2. Clicar "Exportar"

RESULTADO ESPERADO:
✓ Menu de exportação abre
✓ Botões CSV, GeoJSON, etc aparecem
✓ Exportação funciona
```

---

## Fase 5: Produção - Monitoramento

### 5.1 Verificar Logs

```bash
# Netlify Deploy Logs:
# https://app.netlify.com → seu-site → Deploys → último

# Supabase Logs:
# https://app.supabase.com → seu-projeto → Logs → PostgreSQL

# Frontend Console:
# https://seu-site.netlify.app → F12 → Console
# (Não deve haver erros em vermelho)
```

### 5.2 Monitoramento Periódico

```sql
-- Executar a cada semana (no SQL Editor):

-- 1. Quantas mudanças ficam muito tempo pendentes?
SELECT 
  COUNT(*) as pendentes_agora,
  AVG(EXTRACT(EPOCH FROM (now() - criado_em))/3600) as media_horas_pendente
FROM fila_aprovacao 
WHERE status = 'pendente';

-- 2. Qual editor faz mais mudanças?
SELECT 
  u.email, COUNT(*) as total_mudancas
FROM fila_aprovacao f
JOIN auth.users u ON u.id = f.usuario_id
GROUP BY u.email
ORDER BY total_mudancas DESC
LIMIT 5;

-- 3. Taxa de rejeição:
SELECT 
  status, COUNT(*) as quantidade
FROM fila_aprovacao
GROUP BY status;
```

### 5.3 Alertas (Opcional)

Se usar serviço de monitoramento (Sentry, New Relic):

```
Configurar alerta se:
- Erro em aprovar_mudanca() (catch exception)
- Query lenta em fila_aprovacao (>1s)
- Mais de 50 mudanças pendentes há >24h
```

---

## Fase 6: Rollback (Se necessário)

### 6.1 Rollback Frontend

```bash
# Se algo dar errado no frontend:
git revert HEAD
git push origin main

# Ou restaurar backup:
cp index.html.backup.20241107_123456 index.html
git add index.html
git commit -m "revert: approval workflow (rollback)"
git push origin main

# Netlify rebilda automaticamente (~2 min)
```

### 6.2 Rollback Backend (Supabase)

```sql
-- Para remover approval workflow COMPLETAMENTE:

-- 1. Deletar tabelas:
DROP TABLE IF EXISTS fila_aprovacao CASCADE;
DROP TABLE IF EXISTS ativos_removidos CASCADE;

-- 2. Remover funções novas:
DROP FUNCTION IF EXISTS ip_remover_ponto(uuid, text) CASCADE;
DROP FUNCTION IF EXISTS aprovar_mudanca(uuid, boolean, text) CASCADE;

-- 3. Remover parâmetros das funções antigas:
-- (Isto requer recrear as funções inteiras - ver migration para sintaxe exata)

-- 4. Remover colunas adicionadas:
ALTER TABLE v_parque_export DROP COLUMN IF EXISTS pendente_aprovacao;
ALTER TABLE v_parque_export DROP COLUMN IF EXISTS motivo_remocao;
```

**Nota:** Rollback de backend é mais complexo. Recomenda-se fazer em staging primeiro.

---

## 🎯 Pós-Deployment

### Comunicação ao Time

Depois que tudo estiver rodando, comunicar:

```
📢 Comunicado ao Time:

A partir de agora, mudanças de dados realizadas por Editores
entrarão em uma fila de aprovação antes de serem aplicadas.

📋 Impacto:
- Editores: Mudanças levam ~(tempo até admin aprovar) para ser aplicadas
- Admins: Novo menu "Aprovações" no painel Admin
- Leitura: Sem impacto (apenas leitura)

🆘 Se houver problema, reportar para admin@seu-email.com
Ou: https://github.com/danilosfvalim/iluminacao-led-niteroi/issues
```

### Treinamento Rápido (15 min)

Reunir o time e mostrar:

```
1. Onde fica o painel de aprovações (Admin menu)
2. Como aprovar/rejeitar
3. O que significa "Mudança enviada para aprovação"
4. Como remover um ativo (e que entra em fila)
5. FAQ: "Por quê minha mudança não apareceu?"
```

---

## ✅ Checklist Final

```
PRÉ-DEPLOYMENT:
[ ] Backup local: git branch -a
[ ] Backup index.html: *.backup.*
[ ] Leitura completa deste guia

SUPABASE:
[ ] Migrações aplicadas (sem erros)
[ ] Tabelas criadas: fila_aprovacao, ativos_removidos
[ ] RLS policies aplicadas
[ ] RPC functions modificadas/criadas
[ ] Testes SQL executados com sucesso

FRONTEND:
[ ] index.html enviado (Git ou Netlify)
[ ] Netlify deploy completo (status verde)
[ ] Site carrega sem erros (F12 console)
[ ] Botão Admin visível (logado como admin)
[ ] Menu "Aprovações" aparece

TESTES FUNCIONAIS:
[ ] Editor: edita, vê "enviado para aprovação"
[ ] Admin: vê mudança na fila
[ ] Admin: aprova, mudança é aplicada
[ ] Admin: rejeita, mudança não é aplicada
[ ] Admin: edita, aplicado imediatamente (sem fila)
[ ] Remover: entra em fila (backup criado)
[ ] Exportar sem login: bloqueado
[ ] Exportar com login: funciona

MONITORAMENTO:
[ ] Logs Netlify sem erros
[ ] Console browser sem erros em vermelho
[ ] Queries SQL retornam dados esperados
[ ] Fila está vazia (ou com quantidade esperada)

PÓS-DEPLOYMENT:
[ ] Time informado sobre mudanças
[ ] Treinamento rápido realizado
[ ] Contato para suporte comunicado
[ ] Documentação acessível (README, APPROVAL_WORKFLOW.md)
```

---

## 📞 Suporte Técnico

### Contatos

- **Desenvolvedor:** Danilo Valim
- **Email:** danilosfvalim@gmail.com
- **Issues:** https://github.com/DaniloSFValim/iluminacao-led-niteroi/issues
- **Documentação:** APPROVAL_WORKFLOW.md (neste repositório)

### Problemas Comuns

| Problema | Causa Provável | Solução |
|----------|---|---|
| "Mudança enviada..." mas não aparece na fila | Migrações não aplicadas | Reexecutar supabase_audit_migration_001.sql |
| Admin aprova mas mudança não aparece | RPC não encontrada | Verificar nome/parâmetros em Supabase |
| Botão "Remover" não aparece | Role não é admin/editor | Verificar role em profiles table |
| Exportar bloqueado mesmo com login | Cache browser | F5 ou Ctrl+Shift+Del |

---

## 🎉 Conclusão

Após seguir este guia, você terá:

✅ Backend seguro com auditoria completa
✅ Interface intuitiva para aprovações
✅ Rastreabilidade de todas mudanças
✅ Proteção de dados contra edições não autorizadas
✅ Capacidade de recuperação (soft delete)

Que a força esteja com você! 🚀
