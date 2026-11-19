# Fase 4: preparação da publicação e auditoria de coerência

Estado em 2026-11-19, no commit `880ac27` (branch `claude/happy-goodall-c12zd5`). Itens que dependem de
ações do autor no GitHub e no Zenodo constam como **pendentes**; nada foi publicado.

## 4.1 Preparação do GitHub

| Verificação | Situação | Evidência |
|---|---|---|
| Repositório público | Atendido | API do GitHub: `private: false`, `visibility: public` |
| Histórico Git independente | Atendido | Um único commit-raiz (`42b3243`, do próprio OpenLux); nenhuma referência ao projeto anterior, a RBAC, concessionária ou dados operacionais (busca no repositório inteiro) |
| README completo | Atendido | 18 seções na ordem especificada, conferidas por teste |
| Licença aprovada | Atendido | `LICENSE` MIT instalado; declarada em `CITATION.cff`, `.zenodo.json` e `pyproject.toml` (teste confere o texto e a consistência) |
| Arquivos de citação | Atendido, com pendência | `CITATION.cff` valida no esquema CFF 1.2.0 (0 erros). `.zenodo.json` é JSON válido, mas **não foi validado pelo Zenodo** (só um depósito de ensaio valida `license` e `related_identifiers`) |
| Testes aprovados | Atendido | 110 no ambiente de trabalho; clone limpo com ambiente virtual novo: 101 passam, 2 ignorados (navegador e esquema CFF) |
| Ausência de credenciais | Atendido | Busca de padrões de token, chaves e senhas em todos os arquivos e no histórico completo: nenhuma ocorrência |
| Ausência de arquivos indevidos | Atendido | 64 arquivos versionados em 880ac27; nenhum `.h5`, `.zip`, `.tif`, `data/raw/`, `outputs/` ou credencial; maior arquivo 368 KB |
| Ausência de dados com redistribuição incompatível | Atendido, com ressalvas | NASA: política ESDIS lida (CC0 sem marcação de restrição; citação solicitada), com ressalva de enquadramento. Malha IBGE: licença compatível com CC BY 4.0 confirmada. SIDRA: reuso com citação, **conferido pelo autor** (texto não lido por ferramenta). Falchi: não usado. Citações dos dados no README |
| `main` contém todo o trabalho | Atendido | PR #2 mergeado; `main` (`f3b6754`) contém todos os commits; clone limpo da `main`: 101 testes passam, 2 ignorados |
| Branch padrão do repositório | Atendido | API do GitHub: `default_branch: main` |
| Release correspondente à versão | **Pendente (autor)** | Tag `v0.1.0` a partir de `main`; ver `docs/PUBLICATION.md` |

## 4.4 Auditoria de coerência (antes da publicação)

| Entre | Verificado | Como | Situação |
|---|---|---|---|
| Código-fonte e funcionalidades declaradas | Sim | Cada indicador do README existe no código e tem teste; os não implementados constam como trabalho futuro; dependência declarada e não usada foi removida e um teste a impede | Coerente |
| Testes e resultados | Sim | Suíte e reexecução determinística da série real (8 arquivos com SHA-256 idêntico) | Coerente |
| README e metodologia | Sim | Citações texto × bibliografia nos dois sentidos; hashes do Apêndice A conferidos contra os metadados de download; expressão obrigatória e versão presentes | Coerente |
| Metadados (CITATION, Zenodo, pyproject, `__version__`, LICENSE) | Sim | Versão 0.1.0, nome do autor, ORCID e licença idênticos nos arquivos (testes) | Coerente |
| Identificação do autor | Sim, parcialmente | ORCID `0009-0009-7250-6151` informado pelo autor e com dígito verificador válido (verificação local). **Não consultei o ORCID para confirmar que a página pertence ao autor**; confira em https://orcid.org/0009-0009-7250-6151. Sem afiliação declarada | Coerente |
| Release, registro no Zenodo, DOI | **Não** | Dependem da publicação | Pendente |

Itens da auditoria final que só podem ser fechados **depois** da publicação: release `v0.1.0` com a tag
correta, metadados do registro do Zenodo (título, versão, autoria, licença, descrição, arquivos), DOI
da versão e Concept DOI resolvendo em `doi.org`, e correspondência entre o registro e o repositório.

## Questões científicas e legais que permanecem

- Os resultados **não são validados** e há um problema científico não resolvido (aumento do piso de
  ruído do S-NPP a partir de 2022, mais um componente comum aos dois sensores não separado de um possível
  artefato do algoritmo compartilhado). A publicação de uma versão com DOI não resolve isso.
- Ressalva de enquadramento da política da NASA; termos do SIDRA conferidos pelo autor, não por ferramenta.
- Credenciais antigas ainda salvas em *Network secrets* do ambiente (ação do autor).
