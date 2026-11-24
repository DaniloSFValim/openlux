# Fase 5: relatório de encerramento (rascunho)

Estado em 2026-11-23, no branch `claude/happy-goodall-c12zd5` (PR #4 aberto). **As seções que dependem da publicação no Zenodo
(DOI, Concept DOI, release, registro) estão pendentes**; nada foi publicado. Este relatório não declara conformidade com nenhum
requisito externo: cada linha cita a evidência ou diz o que falta. O edital PGC/UFF foi deixado fora do escopo por decisão do autor.

## 1. Relatório de implementação

| Item | Estado | Onde |
|---|---|---|
| Pipeline de aquisição com verificação de integridade (SHA-256, assinatura HDF5, tentativas) e proveniência | Implementado e testado | `openlux.download`, `openlux.provenance`, `scripts/fetch_*.py` |
| Leitura do Black Marble com máscaras (fill, negativos, qualidade, observações, terra/água) | Implementado e testado em dados reais (VNP46A4, VJ146A4, e os mensais VNP46A3/VJ146A3 só na análise de ruído) | `openlux.io` |
| Agregação zonal com cobertura fracionária, área elipsoidal exata, rejeição de CRS divergente | Implementado e testado | `openlux.zonal`, `openlux.geo` |
| Indicadores: radiância média e mediana, intensidade radiante aparente, fração da área válida, fração iluminada (limiar documentado 0,5 e quantis analíticos), intensidade por habitante (2022), variação, tendência (Theil-Sen + Kendall) em duas janelas | Implementado e testado | `openlux.pipeline`, `openlux.temporal` |
| Sensibilidade (qualidade 0+1, near-nadir, `n_min` 5 e 10), controles de ruído (anuais e mensais), comparação S-NPP × NOAA-20 (estado e município) | Implementado e executado nos dados reais | `openlux.pipeline`, `openlux.qa`, `scripts/analyze_monthly_noise.py`, `scripts/compare_sensors_municipal.py` |
| Validação de estabilidade (critério de agregação, resolução) e consistência de área com o IBGE | Implementado e executado | `openlux.validation`, `scripts/validate_aggregation.py` |
| Interface web estática (mapa, painéis, informações científicas, aviso permanente) | Implementada e testada em navegador; publicada em https://openlux.labdados.org/ (verificado em 2026-11-23) | `web/` |
| Documentação acadêmica, metadados de citação, licença MIT, verificação de referências | Concluída | `README.md`, `METHODOLOGY.md`, `CITATION.cff`, `.zenodo.json`, `LICENSE`, `docs/` |

Dimensão: 17 módulos Python (~1,6 mil linhas em `src/`), 13 scripts, ~2,3 mil linhas de teste, 175 testes (148 sem os de navegador).

**Implementado após o fechamento original da Fase 2** (a pedido do autor, em branch própria, ainda não publicada em release): radiância ponderada pela
população e população em áreas iluminadas (setores do Censo 2022, população fixa), radiância e fração iluminada urbano × rural, mudança significativa por pixel
(Mann–Kendall + Sen + FDR) e registro estruturado dos scripts novos. Ver `docs/DECISIONS.md`, seção 9. Depois, a interface ganhou a camada de pixel (classes fixas, sem publicar valores) e o destaque a Niterói foi removido (seção 10). Todos herdam o ruído do S-NPP pós-2021 e **não estão validados**.

**Não implementado** (constam como trabalho futuro): comparação com o Atlas de Falchi et al. (2016) (dados não obtidos; licença CC BY-NC 4.0; grandeza e época diferentes),
indicadores municipais mensais.

## 2. Relatório de validação

Os resultados científicos **não foram validados**: não houve comparação com valores publicados (nenhum estudo comparável foi identificado) nem verdade de campo. As verificações
realizadas descrevem estabilidade e consistência; **nenhum limite de aprovação foi definido a priori** (ver `METHODOLOGY.md`, seção 11).

| Verificação | Resultado resumido | Detalhe |
|---|---|---|
| Área raster × IBGE | Diferença máxima 0,0015 % por município | `docs/DECISIONS.md` §1 e §5 |
| Estabilidade: centro do pixel, grade 2×2 e 4×4 | Spearman ≥ 0,9988; mediana das diferenças 0,3 % a 1,8 % | §5 |
| Sensibilidade a máscara e camada | Spearman ≈ 1 (máscara); 0,86 a 0,96 (near-nadir, inclinações) | §1 |
| Determinismo | 8 arquivos de saída com SHA-256 idêntico em duas execuções completas | `METHODOLOGY.md` §11 |
| Clone limpo da branch com ambiente novo | Testes aprovados (ver `docs/PHASE4_AUDIT.md`) | |
| Piso de ruído do S-NPP | Aumento específico do S-NPP a partir de 2022 (início entre jan e mar), não sinalizado pelo campo de qualidade; causa **não identificada** | §3, §7 |
| S-NPP × NOAA-20 | Até 2021, concordância em nível (razão 0,98 a 1,01) e em ordem (ρ ≥ 0,999); de 2022 a 2025 o S-NPP lê mais alto (razão 0,79 a 0,91) | §8 |
| Aumento comum aos dois sensores (2018–2025) | NOAA-20 com tendência positiva em 72 de 92 municípios; **não separado** de um possível artefato do algoritmo compartilhado | §8 |

## 3. Relatório de publicação (pendente)

| Etapa | Situação |
|---|---|
| Repositório público | Concluído (verificado pela API em 2026-11-19) |
| `main` completa e branch padrão `main` | Concluído até o PR #3; o PR #4 (cabeçalhos, Cloudflare, ruído mensal e comparação de sensores) está **aberto** |
| Licença MIT | Concluído |
| ORCID e autoria nos metadados | Concluído (ORCID informado pelo autor; formato e dígito verificador validados localmente) |
| Release `v0.1.0` | **Pendente** (ação do autor) |
| Registro no Zenodo, DOI da versão, Concept DOI | **Pendente** |
| Conferência dos metadados do registro | **Pendente** (depende do registro) |

## 4. Links permanentes

| Item | Endereço |
|---|---|
| Repositório | https://github.com/DaniloSFValim/openlux |
| Site | https://openlux.labdados.org/ |
| ORCID do autor | https://orcid.org/0009-0009-7250-6151 |
| DOI da versão v0.1.0 | _a preencher após a publicação_ |
| Concept DOI | _a preencher após a publicação_ |
| Registro no Zenodo | _a preencher após a publicação_ |

## 5. Checklist de documentos comprobatórios

| Documento | Situação |
|---|---|
| Código-fonte e histórico Git (repositório público) | Disponível |
| `README.md` e `METHODOLOGY.md` | Disponíveis |
| `CITATION.cff` (válido no esquema CFF 1.2.0) e `.zenodo.json` | Disponíveis (o `.zenodo.json` não foi validado pelo Zenodo) |
| `LICENSE` (MIT) e `docs/LICENSING.md` | Disponíveis |
| Hashes das entradas e das saídas de referência | `METHODOLOGY.md`, Apêndices A e C |
| Página do registro no Zenodo (cópia em PDF) | **Pendente** |
| Página da release no GitHub (cópia em PDF) | **Pendente** |

## 6. Matriz de conformidade do software

| Requisito | Evidência | Situação |
|---|---|---|
| Software desenvolvido | Repositório GitHub, 175 testes | Concluído |
| Autoria identificada | `CITATION.cff`, `.zenodo.json`, `LICENSE` | Concluído nos arquivos; conferir no registro publicado |
| Repositório público | API do GitHub | Concluído |
| DOI | Registro no Zenodo | **Pendente** |
| Concept DOI | Registro no Zenodo | **Pendente** |
| Release versionada | GitHub | **Pendente** |
| Documentação científica | `README.md`, `METHODOLOGY.md` | Concluído |
| Licenciamento | `LICENSE`, metadados | Concluído |
| ORCID | `CITATION.cff`, `.zenodo.json` | Concluído nos arquivos |
| Adequação a edital | Fora do escopo por decisão do autor | Não avaliado |

## 7. Pendências

1. Mergear o PR #4 e resolver o check **Workers Builds** da Cloudflare (falha na etapa de criação de prévia; causa não identificada; ver `docs/DEPLOYMENT.md`).
2. Criar a release `v0.1.0` e depositar no Zenodo (`docs/PUBLICATION.md`); depois preencher DOIs, README (seção 18) e `CITATION.cff`, e rodar a auditoria 4.4.
3. Decidir o tratamento do Cloudflare Web Analytics (desativar ou permitir) e remover as credenciais antigas dos *Network secrets*.
4. Validar o campo `license` e as relações do `.zenodo.json` em um depósito de ensaio (Zenodo Sandbox).

## 8. Recomendações para a evolução científica

1. **Resolver ou contornar a divergência do S-NPP.** Obter uma cadeia de processamento independente (por exemplo, o produto anual do EOG, que exige login) e comparar com Black Marble; testar correções do piso de ruído.
2. **Série harmonizada.** Usar o S-NPP até 2021 e o NOAA-20 de 2018 em diante, calibrando a sobreposição 2018–2021, e quantificar a incerteza da junção.
3. **Estender as análises mensais** a todos os anos e a indicadores municipais mensais, para separar sazonalidade (nuvens, observações) de deriva do instrumento.
4. **Validação externa.** Procurar estudos comparáveis, medições fotométricas de campo (por exemplo, fotômetros em redes de monitoramento do céu) e comparar com o Atlas de Falchi et al. (2016), respeitando a licença CC BY-NC 4.0.
5. **Efeito do LED.** Investigar a subestimação por insensibilidade ao azul (Levin et al., 2020) com dados de conversão da iluminação pública, se houver dados públicos.
6. **Indicadores territoriais.** O urbano × rural por setor do Censo 2022 já existe (`docs/DECISIONS.md` 9.2). Falta a fração iluminada por classe de uso do solo, com uma camada pública verificada, e verificar o critério de classificação urbano/rural do IBGE.
7. **Avaliar a saturação** do DNB em núcleos urbanos, não avaliada neste trabalho.
