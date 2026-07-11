<div align="center">

# 🌍 OpenLux — Visão

### Uma plataforma aberta de gestão de iluminação pública, para qualquer cidade

*Niterói é o laboratório. A ideia é maior.*

</div>

---

## 1. O problema

Toda cidade tem um parque de iluminação pública — dezenas de milhares de pontos que
consomem uma fatia enorme do orçamento de energia. E quase toda cidade o gerencia com
alguma combinação de planilhas, sistemas proprietários caros e **dados mortos**: um
censo feito uma vez, que envelhece no dia seguinte e nunca mais reflete a rua.

As consequências são as mesmas em qualquer lugar: modernização LED sem priorização
técnica, poluição luminosa invisível ao gestor, manutenção reativa, e nenhuma memória
do que foi feito, quando e por quem.

## 2. A tese

O OpenLux nasce de três convicções, todas já provadas no laboratório de Niterói:

1. **O dado de iluminação deve ser vivo e versionado.** Não existe "o censo" — existem
   **campanhas de levantamento** sucessivas. Cada ponto carrega a idade e a proveniência
   do seu dado (herdado vs. verificado em campo), e nada é apagado: a história do parque
   é parte do parque.

2. **Inventário não basta — a instalação importa.** Duas luminárias idênticas produzem
   resultados opostos conforme o ângulo de apontamento e a superfície que iluminam.
   O método de **índices fotométricos de instalação** (aproveitamento no piso, poluição
   luminosa, luminância relativa — [doc do modelo](docs/FIELD_REFERENCE_TIER3_PHOTOMETRY.md))
   transforma o cadastro em ferramenta de engenharia e ciência, com dado barato de coletar.

3. **Infraestrutura pública pede software aberto.** Sem licença por ponto, sem
   aprisionamento tecnológico. Uma pilha deliberadamente simples (uma página HTML +
   PostgreSQL/PostGIS), que uma prefeitura pequena consegue operar e uma universidade
   consegue auditar. Código MIT; **os dados pertencem a cada município**.

## 3. Niterói — o laboratório

A plataforma não é uma promessa: é a generalização de um sistema **em produção**, que
gerencia **42.765 pontos em 52 bairros** (~5,8 MW instalados, 39% LED), com edição em
campo, fila de aprovação, catálogo fotométrico de modelos (Tier 2), índices de
instalação (Tier 3), análise espacial por polígono e CI/CD completo.

Esse marco está congelado e citável: **DOI
[10.5281/zenodo.21305310](https://doi.org/10.5281/zenodo.21305310)** (v1.3.0, 2026).
Niterói segue como implantação de referência — o lugar onde cada recurso novo é
testado com dados e equipes reais antes de virar plataforma.

## 4. O modelo de expansão

**Cidade é configuração, não código.** Limites geográficos, bairros, identidade visual
e credenciais viverão em `config/cities/<cidade>.json` + na entidade `municipio` do
banco. O core é um só.

Dois modos de implantação, combináveis:

| Modo | Para quem | Como |
|---|---|---|
| **Consórcio regional** (multi-tenant) | Região metropolitana, municípios pequenos | Várias cidades no mesmo banco, isoladas por RLS; custo e operação compartilhados; indicadores regionais nativos |
| **Instância soberana** | Cidades com equipe/exigência própria | Cada cidade roda seu próprio backend a partir do template de implantação |

E, no horizonte, uma **camada de federação**: API pública de indicadores agregados
(quantos pontos, % LED, poluição estimada) que costura instâncias independentes num
painel regional/nacional — sem centralizar o dado bruto de ninguém.

## 5. Colaboração

- **Entre cidades:** quem implanta contribui — correções, recursos e aprendizado voltam
  para o core. O registro público de implantações vive em [`cities/`](cities/README.md).
- **Com a academia:** o método fotométrico é documentado, reprodutível e citável;
  campanhas de campo geram datasets abertos para pesquisa (poluição luminosa,
  eficiência energética, políticas públicas).
- **Com o cidadão:** *em avaliação.* A arquitetura fica preparada (fila de triagem de
  reportes já existe como conceito na fila de aprovação), mas o reporte cidadão só
  entra no roadmap quando houver decisão e capacidade de triagem.

## 6. Roadmap por fases

- [x] **Fase −1 — Laboratório** · Sistema de Niterói completo, em produção, auditado e com DOI *(concluída, v1.3.0)*
- [x] **Fase 0 — Identidade** · Visão, governança, registro de cidades, rebranding OpenLux *(este documento)*
- [x] **Fase 1 — Desacoplar** · Cidade vira configuração (`config/cities/` + bloco `CITY`), entidade `municipio` no banco; Niterói continua idêntica
- [x] **Fase 2 — Recenseamento** · Campanhas de levantamento versionadas, estado herdado/verificado por ponto, confirmação e edição em campo carimbam a campanha ativa, filtro "não verificados" no mapa (coleta Tier 3 já embutida no fluxo de edição)
- [ ] **Fase 3 — Multi-cidade** · RLS por município, onboarding "nova cidade em 1 hora", [guia de implantação](docs/DEPLOY_YOUR_CITY.md) completo
- [ ] **Fase 4 — Região** · Painel agregado multi-cidade, PWA offline para equipes de campo
- [ ] **Fase 5 — Comunidade** · Federação de instâncias, datasets abertos, rede de cidades

Cada fase é útil por si só — nenhuma depende de "terminar tudo".

## 7. Princípios inegociáveis

1. **Nada se perde.** Histórico Git, DOIs, dados herdados: tudo é camada, nunca descarte.
2. **O banco é a fonte de verdade** — de dados e de permissões (RLS + RPCs).
3. **Simplicidade operável**: zero build, zero framework, dependências mínimas.
4. **Dado público, código aberto, soberania municipal.**
5. **Ciência aberta**: todo método publicado com premissas explícitas e dados de reprodução.

---

<div align="center">

**OpenLux** · concebido e mantido por [Danilo Valim](https://orcid.org/0009-0009-7250-6151) ·
nascido em Niterói/RJ, feito para qualquer cidade

</div>
