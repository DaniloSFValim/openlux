# Publicação: GitHub, Zenodo e DOI (Fase 4)

Guia para a publicação da versão **0.1.0** do OpenLux. A criação da release e o depósito no Zenodo são
feitos pelo autor: dependem da conta dele no GitHub e no Zenodo, e **o DOI gerado é permanente** (o
registro pode ter os metadados corrigidos depois, mas um DOI emitido não pode ser apagado). Os
passos abaixo marcam o que foi verificado e o que precisa ser conferido na interface atual dos serviços.

## 1. Antes de criar a release (checklist)

- [x] O PR com as Fases 3 e 4 foi mergeado em `main` (verificado: `main` contém `LICENSE`, `CITATION.cff`, `.zenodo.json`, `METHODOLOGY.md` e a documentação de publicação).
- [x] A branch padrão do repositório é `main` (verificado pela API do GitHub).
- [x] Decisão sobre `web/data/`: **mantido**. NASA: política ESDIS (CC0 sem marcação de restrição, com a ressalva de enquadramento em `docs/DECISIONS.md`). IBGE malha: licença compatível com CC BY 4.0. IBGE/SIDRA (população): reuso permitido com citação, conferido pelo autor em 2026-11-19; as citações estão no README.
- [ ] A versão é 0.1.0 em `pyproject.toml`, `CITATION.cff`, `.zenodo.json` e `openlux.__version__` (verificado por teste). A tag deve ser `v0.1.0`.
- [ ] Os testes passam em um clone limpo (ver `docs/PHASE4_AUDIT.md`).
- [ ] Opcional e recomendado: ensaiar todo o fluxo no **Zenodo Sandbox** (`sandbox.zenodo.org`, serviço separado, com seu próprio vínculo ao GitHub e DOIs de teste), para conferir os metadados antes do registro definitivo. O campo `license` do `.zenodo.json` (`mit`) **não foi validado contra o Zenodo**; o ensaio confirma isso.

## 2. Integração com o Zenodo (passo a passo)

1. **Acessar o Zenodo.** Entrar em https://zenodo.org com a conta do autor (o login com GitHub facilita o vínculo).
2. **Autorizar a integração com o GitHub.** Em *Account → GitHub* (`https://zenodo.org/account/settings/github/`, confirmar o caminho na interface), conectar a conta do GitHub e conceder acesso ao repositório.
3. **Ativar o repositório OpenLux.** Na lista de repositórios, ligar a chave de `DaniloSFValim/openlux`. **Faça isto antes de criar a release:** o Zenodo só arquiva as releases criadas depois da ativação.
4. **Criar a release `v0.1.0`.** No GitHub: *Releases → Draft a new release*; tag `v0.1.0` criada a partir de `main`; título "OpenLux v0.1.0"; descrição a partir de `docs/RELEASE_NOTES_v0.1.0.md`; publicar a release (rascunhos não disparam o arquivamento).
5. **Verificar a geração automática do registro.** Na página do GitHub do Zenodo, a release deve aparecer com um registro associado (pode levar alguns minutos). Se falhar, a mesma página mostra o erro e permite reenviar.
6. **Conferir os metadados.** Tipo "Software", título "OpenLux", versão 0.1.0, idioma português.
7. **Conferir a autoria.** Criador "Valim, Danilo" com o ORCID `0009-0009-7250-6151` vinculado; nenhuma afiliação foi declarada (não inventar).
8. **Conferir a licença.** MIT. Se o Zenodo mostrar outra, corrigir no registro e investigar a precedência (`.zenodo.json`, depois `CITATION.cff`, depois a licença detectada no GitHub, segundo a ajuda do Zenodo).
9. **Conferir a descrição.** Deve manter a expressão *estimativa de poluição luminosa baseada em sensoriamento remoto* e a ressalva de que os resultados não são validados.
10. **Conferir os arquivos depositados.** O arquivo `.zip` do repositório na tag `v0.1.0`. Verificar que **não** há `data/raw/`, arquivos `.h5`, `outputs/`, credenciais ou dados de terceiros além de `web/data/` (decisão da seção 1).
11. **Confirmar a publicação.** Abrir a página pública do registro, confirmar o estado "publicado" e que o DOI resolve em `https://doi.org/<doi>`. **Não cite o DOI antes dessa confirmação.** (Se a integração criar o registro como publicado automaticamente ou como rascunho deve ser conferido na interface; o ensaio no Sandbox elimina a dúvida.)

## 3. DOI específico da versão e Concept DOI

| | DOI específico da versão | Concept DOI |
|---|---|---|
| Identifica | Uma versão exata arquivada (por exemplo, v0.1.0) | O conjunto de todas as versões do software |
| Resolve para | O registro daquela versão | Sempre a versão mais recente |
| Quando citar | Para reproduzir ou referenciar exatamente os resultados daquela versão | Para citar o projeto como um todo, sem fixar versão |
| Muda a cada release? | Sim, um novo DOI por release | Não, permanece o mesmo |

Um DOI prova que o arquivo existe, com aquele conteúdo e data, em um repositório com preservação de
longo prazo. **Não** comprova revisão por pares, avaliação científica nem validação independente do software.

O DOI de uma versão só é conhecido depois de a release ser arquivada, então **não pode estar dentro do
arquivo daquela mesma versão**. Para registrar os DOIs sem criar nova release, faça um commit
posterior em `main` (selo/DOI no README, identificador em `CITATION.cff`); ele entra na próxima release.

### Registro a preencher após a publicação

| Campo | Valor |
|---|---|
| DOI específico da versão v0.1.0 | _preencher após a publicação_ |
| Concept DOI do projeto | _preencher após a publicação_ |
| URL permanente do registro Zenodo | _preencher_ |
| URL do repositório | https://github.com/DaniloSFValim/openlux |
| Data da publicação | _preencher_ |

## 4. Depois da publicação

1. Preencher a tabela acima e a seção 18 do `README.md` (DOI); acrescentar o identificador em `CITATION.cff` (`identifiers`).
2. Rodar a auditoria final (4.4) com os valores reais: `docs/PHASE4_AUDIT.md`.
3. Para qualquer correção de conteúdo, criar uma nova versão (nova release, novo DOI de versão); o Concept DOI se mantém.
