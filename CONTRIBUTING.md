# Contribuindo para Iluminação LED Niterói

Obrigado por considerar contribuir! Este documento fornece guidelines para contribuir ao projeto.

## 🎯 Código de Conduta

Somos comprometidos com um ambiente respeitoso e inclusivo. Veja [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md).

## 🚀 Como Contribuir

### 1. Report de Bug

Se encontrar um bug, abra uma [issue](https://github.com/DaniloSFValim/iluminacao-led-niteroi/issues/new?template=bug.md):

**Inclua:**
- Descrição clara do problema
- Steps para reproduzir
- Comportamento esperado vs atual
- Screenshots (se relevante)
- Ambiente (navegador, SO, versão)

### 2. Feature Request

Tem uma ideia? Abra uma [issue de feature](https://github.com/DaniloSFValim/iluminacao-led-niteroi/issues/new?template=feature.md):

**Inclua:**
- Descrição da feature
- Caso de uso / por que é necessário
- Solução proposta
- Alternativas consideradas

### 3. Pull Request

Pronto para contribuir com código?

#### Setup Local

```bash
# 1. Fork e clone
git clone https://github.com/seu-usuario/iluminacao-led-niteroi.git
cd iluminacao-led-niteroi

# 2. Criar branch
git checkout -b feature/meu-recurso

# 3. Frontend local
npx http-server

# 4. Supabase local
supabase start
```

#### Desenvolvimento

- **Não altere** `index.html` sem necessidade (arquivo grande)
- Se mexer em Supabase, crie migration em `supabase/migrations/`
- Adicione testes se possível (E2E via Playwright)
- Documente mudanças significativas

#### Commits

Siga [Conventional Commits](https://www.conventionalcommits.org/):

```bash
git commit -m "feat: adicionar novo recurso"
git commit -m "fix: corrigir bug em renderização"
git commit -m "docs: atualizar README"
git commit -m "chore: atualizar dependências"
```

#### Push & PR

```bash
git push -u origin feature/meu-recurso
```

Depois abra PR no GitHub. Use o [template](./.github/pull_request_template.md).

**Na PR:**
- Descreva o que foi feito e por quê
- Link issues relacionadas
- Preencha o checklist
- Aguarde review

## 📋 Guidelines

### Código

- ✅ Mantenha simplicidade (sem abstrações prematuras)
- ✅ Escape HTML para evitar XSS
- ✅ Teste localmente antes de PR
- ✅ Sem hardcoded credentials
- ❌ Não altere `index.html` desnecessariamente (muito grande)
- ❌ Não remova testes existentes

### Documentação

- ✅ Atualize README se mudar setup
- ✅ Documente RPC functions novas em ARCHITECTURE.md
- ✅ Adicione troubleshooting para problemas conhecidos
- ❌ Não adicione bloat ao repo

### Segurança

- 🔒 Nunca commite `.env`, credentials, ou secrets
- 🔒 Valide input do usuário
- 🔒 Use prepared statements (PostgREST protege automaticamente)
- 🔒 Reporte vulnerabilidades em privado (ver SECURITY.md)

## 🔍 Review Process

1. **Automatic Checks:** CI/CD workflow valida
2. **Code Review:** Revisor(es) comentam
3. **Fixes:** Você faz ajustes se solicitado
4. **Approval:** Revisor aprova
5. **Merge:** Mantainer faz merge

Tipicamente leva **1-3 dias**.

## 📚 Referências

- [README.md](./README.md) — Setup e uso
- [ARCHITECTURE.md](./ARCHITECTURE.md) — Design técnico
- [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) — FAQ
- [GitHub Issues](https://github.com/DaniloSFValim/iluminacao-led-niteroi/issues)

## ❓ Dúvidas?

- 💬 Abra uma [discussion](https://github.com/DaniloSFValim/iluminacao-led-niteroi/discussions)
- 📧 Contate o maintainer

---

**Obrigado por contribuir!** 🙏
