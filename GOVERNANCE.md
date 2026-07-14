# Governança do OpenLux

Como o projeto decide, quem decide, e como cidades e pessoas participam.

## Papéis

| Papel | Quem | Responsabilidade |
|---|---|---|
| **Mantenedor** | [Danilo Valim](https://github.com/DaniloSFValim) ([ORCID 0009-0009-7250-6151](https://orcid.org/0009-0009-7250-6151)) | Direção técnica e científica, merge em `main`, releases/DOIs |
| **Caso de estudo** | Parque urbano com 42.765 pontos | Validação de recursos com dados reais antes de lançamento em plataforma |
| **Cidades implantadoras** | Registradas em [`cities/`](cities/README.md) | Operam suas instâncias/tenants; reportam problemas; propõem recursos |
| **Contribuidores** | Qualquer pessoa | Issues, PRs, documentação, tradução, pesquisa |

Enquanto o projeto tem um mantenedor único, o modelo é *maintainer-led*: decisões
técnicas são tomadas em público (issues/PRs), com palavra final do mantenedor. Se a
comunidade crescer, este documento evolui para um comitê (meta declarada na Fase 5).

## Como as decisões acontecem

- **Mudanças pequenas** (bug fix, doc, refactor local): direto por PR.
- **Mudanças estruturais** (schema do banco, modelo multi-cidade, API pública): abrir
  uma **issue de proposta** antes do código, descrevendo motivação, alternativas e
  impacto nas cidades implantadas. Registro público da discussão é obrigatório.
- **Quebra de compatibilidade**: exige plano de migração documentado. Princípio nº 1
  da [visão](VISION.md): *nada se perde*.

## Como uma cidade adere

1. Abrir uma issue `[cidade] <nome>` manifestando interesse.
2. Escolher o modo: **tenant** num consórcio existente ou **instância soberana**
   (ver [guia de implantação](docs/DEPLOY_YOUR_CITY.md)).
3. Registrar-se em [`cities/README.md`](cities/README.md) via PR.
4. Compromissos mínimos: manter o mapa público, creditar o projeto (citação com DOI)
   e reportar problemas que encontrar.

## Propriedade e licenças

- **Código**: MIT ([LICENSE](LICENSE)) — uso livre, inclusive comercial, com atribuição.
- **Dados**: pertencem a **cada município**. O projeto nunca centraliza dado bruto sem
  consentimento; a federação (Fase 5) agrega apenas indicadores.
- **Método científico**: publicado e citável — DOI
  [10.5281/zenodo.21305310](https://doi.org/10.5281/zenodo.21305310). Ver
  [docs/INTELLECTUAL_PROPERTY.md](docs/INTELLECTUAL_PROPERTY.md).

## Segurança e conduta

- Vulnerabilidades: [SECURITY.md](SECURITY.md) — nunca em issue pública.
- Convivência: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
- Contribuição: [CONTRIBUTING.md](CONTRIBUTING.md) (Conventional Commits, CI verde).

## Releases e citação

Releases seguem SemVer e são arquivados no Zenodo (DOI por versão + DOI-conceito).
Marcos: `v1.3.0` = sistema Niterói completo (laboratório); `v2.0.0` (planejado) =
primeira versão multi-cidade da plataforma.
