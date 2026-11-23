# OpenLux

**Estimativa de poluição luminosa baseada em sensoriamento remoto no Estado do Rio de Janeiro.**

Software científico independente, em desenvolvimento (versão 0.1.0). Não há resultado científico
validado ainda; leia as seções *Resultados efetivamente disponíveis* e *Limitações* antes de usar
qualquer número.

## 1. Identificação

| Campo | Valor |
|---|---|
| Nome | OpenLux |
| Natureza | Software científico e ferramenta de análise espacial |
| Autor | Danilo Valim |
| Áreas | Ciência de dados, geoprocessamento, sensoriamento remoto e ciências ambientais |
| Repositório | https://github.com/DaniloSFValim/openlux |
| Site | https://openlux.labdados.org/ (interface; ver [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md)) |
| Versão | 0.1.0 (pré-lançamento) |
| Licença do código | MIT (arquivo [`LICENSE`](LICENSE)). Não se aplica aos dados de terceiros (ver [`docs/LICENSING.md`](docs/LICENSING.md)) |
| DOI | A ser atribuído após a publicação no Zenodo |

O OpenLux é um projeto autônomo, com código, metodologia e histórico de versões próprios, e usa
exclusivamente dados públicos com procedência verificável.

## 2. Resumo científico

O OpenLux agrega a radiância noturna observada pelo sensor VIIRS (produtos NASA Black Marble
VNP46A4, Suomi NPP, 2012–2025, e VJ146A4, NOAA-20, 2018–2025) nos 92 municípios do Estado do Rio
de Janeiro, usando a malha municipal e a população do IBGE. Para cada município e ano calcula
radiância média e mediana, intensidade radiante aparente, fração da área iluminada, tendência
temporal (Theil–Sen e Kendall) e controles de ruído de fundo, além de análises de sensibilidade
às escolhas de máscara, de critério de agregação e de resolução. Toda execução registra
proveniência (versões, parâmetros, hashes de entradas e saídas, versão do código) e é
determinística. Os valores são *estimativas baseadas em sensoriamento remoto* da radiância
noturna de superfície, **não medições do brilho do céu**.

## 3. Pergunta de pesquisa

> Como a estimativa de poluição luminosa baseada em sensoriamento remoto (radiância noturna
> VIIRS) se distribui entre os 92 municípios do Estado do Rio de Janeiro e como evoluiu entre 2012
> e o último ano completo disponível, e quão robustos são esses resultados à escolha do produto,
> da máscara de qualidade e do método de agregação?

## 4. Objetivos

**Geral.** Construir uma ferramenta reproduzível e documentada para estimar e acompanhar a
poluição luminosa no Estado do Rio de Janeiro a partir de dados públicos de satélite.

**Específicos.** (i) Agregar a radiância anual por município com cobertura fracionária de
pixels; (ii) calcular indicadores com unidades e hipóteses explícitas; (iii) analisar a evolução
temporal e sua dependência da janela de anos; (iv) quantificar a sensibilidade a máscara,
sensor, critério de agregação e resolução; (v) registrar a proveniência de cada resultado;
(vi) disponibilizar os resultados em uma interface que distingua dado observado, indicador
derivado e classificação analítica.

## 5. Abrangência geográfica

Estado do Rio de Janeiro, 92 municípios (malha IBGE 2024). O município de Niterói pode ser
explorado como estudo de caso na interface, sem restringir a abrangência estadual.

## 6. Fontes de dados

| Fonte | Instituição | Uso | Termos |
|---|---|---|---|
| Black Marble VNP46A4 v2.0 (DOI 10.5067/VIIRS/VNP46A4.002) | NASA / LAADS DAAC | Radiância anual S-NPP (principal) | Política ESDIS da NASA: dados de missões lideradas pela NASA sem marcação de restrição são CC0; citação solicitada. Os arquivos não trazem marcação de restrição. Ressalva: o enquadramento como "missão liderada pela NASA" é interpretação do autor |
| Black Marble VJ146A4 v2.0 (DOI 10.5067/VIIRS/VJ146A4.002) | NASA / LAADS DAAC | Comparação entre sensores | Idem |
| Malha Municipal Digital 2024 (RJ) | IBGE | Limites municipais | Licença compatível com CC BY 4.0 (confirmada) |
| Censo Demográfico 2022, SIDRA tabela 4709, variável 93 | IBGE | População residente (2022) | Reuso permitido com citação da fonte (conferido pelo autor em 2026-11-19) |
| Malha de setores censitários 2022 com atributos (RJ) | IBGE | População por setor e situação urbana/rural | Mesma política de reuso do Censo 2022; o texto específico desta malha não foi lido por ferramenta (o IBGE bloqueia o acesso automatizado) |

Cada fonte tem URL, versão, data de aquisição e SHA-256 registrados em
`data/metadata/downloads/`. Citação dos dados NASA (conforme a política da NASA, que solicita citar os
conjuntos de dados): VIIRS Land SIPS Processing Group, *VIIRS/NPP Lunar BRDF-Adjusted Nighttime Lights Yearly
L3 Global 15 arc second Linear Lat Lon Grid* [Dataset], NASA LAADS DAAC, https://doi.org/10.5067/VIIRS/VNP46A4.002,
e *VIIRS/JPSS1 Lunar BRDF-Adjusted Nighttime Lights Yearly L3 Global 15 arc second Linear Lat Lon Grid*,
https://doi.org/10.5067/VIIRS/VJ146A4.002 (acessos em 2026-11-19; títulos e DOI lidos dos atributos dos arquivos). Citação das fontes do IBGE: IBGE, *Malha Municipal Digital 2024* (UF RJ); IBGE, *Censo Demográfico 2022*,
população residente (SIDRA, tabela 4709, variável 93), acesso em 2026-11-19. Os termos do SIDRA foram conferidos
pelo autor (reuso permitido com citação da fonte); a forma de citação é redação do projeto.
Dados brutos não são redistribuídos neste repositório. Fontes
candidatas **não usadas**: EOG VIIRS Nighttime Lights (exige login; CC BY 4.0 conforme o documento oficial do EOG, com
atribuição e aviso obrigatórios) e o Atlas de Falchi et al. (2016) (dados não obtidos; licença CC BY-NC 4.0; baseado em
um único composto VIIRS de 6 meses de 2014 e em outra grandeza, luminância zenital modelada).

## 7. Metodologia

Resumo: leitura da camada `AllAngle_Composite_Snow_Free`; máscara por qualidade, número de
observações e terra/água; agregação por cobertura fracionária de pixels na grade nativa; área
dos pixels no elipsoide WGS84; indicadores por município e ano; tendência por Theil–Sen e
Kendall em duas janelas; controles de ruído de fundo; sensibilidade e estabilidade. Equações,
unidades, parâmetros, tratamento dos dados e reprodução passo a passo:
[`METHODOLOGY.md`](METHODOLOGY.md). Decisões e achados: [`docs/DECISIONS.md`](docs/DECISIONS.md).

## 8. Indicadores implementados

| Indicador | Unidade | Observação |
|---|---|---|
| Radiância média e mediana ponderadas | nW·cm⁻²·sr⁻¹ | Pixels válidos, cobertura fracionária |
| Intensidade radiante aparente | nW·sr⁻¹ | Radiância × área na direção do sensor; **não é emissão luminosa total** |
| Fração da área válida | adimensional | Controle de qualidade |
| Fração da área iluminada | adimensional | Limiar documentado 0,5 nW·cm⁻²·sr⁻¹; muito sensível ao piso de ruído do S-NPP após 2021 |
| Intensidade por habitante (2022) | mW·sr⁻¹ por habitante | Índice relativo, só 2022 |
| Variação absoluta e percentual | nW·cm⁻²·sr⁻¹ e % | Percentual só acima de um piso declarado |
| Tendência (Theil–Sen, Kendall) | nW·cm⁻²·sr⁻¹ por ano | Duas janelas: 2012–2021 e 2012–2025 |
| Controles de ruído de fundo | nW·cm⁻²·sr⁻¹ | Pixels persistentemente escuros, terra e mar; análise mensal 2021–2023 |
| Comparação municipal S-NPP × NOAA-20 (2018–2025) | vários | Níveis por ano, inclinações, variação 2021→2025; até 2021 os sensores concordam em nível, e a partir de 2022 o S-NPP lê mais alto |

| Radiância ponderada pela população e população em áreas iluminadas | nW·cm⁻²·sr⁻¹ e fração | Setores do Censo 2022; **população fixa em 2022** em todos os anos; repartição areal simples; não é exposição individual |
| Radiância e fração iluminada urbana × rural | nW·cm⁻²·sr⁻¹ e fração | Classificação `SITUACAO` do IBGE (Censo 2022) |
| Mudança significativa por pixel | fração dos pixels iluminados | Mann–Kendall + Sen, FDR 5 %; sem correção de dependência espacial; as janelas com 2022–2025 herdam o ruído do S-NPP |

**Não implementado:** comparação com o Atlas de Falchi et al. (2016) (dados não obtidos). Consta como trabalho futuro.

## 9. Arquitetura tecnológica

Pipeline em Python, saídas em CSV/JSON e interface estática (HTML, CSS e JavaScript), sem banco de
dados, servidor ou serviço pago.

| Dependência | Justificativa |
|---|---|
| numpy, pandas | Arrays e tabelas |
| h5py | Leitura do HDF-EOS5 do Black Marble |
| rasterio | Transformações afins, rasterização e raster em memória |
| geopandas, shapely, pyproj | Vetores, geometrias e verificação de CRS |
| exactextract | Cobertura fracionária de pixels por polígono |
| scipy | Theil–Sen, Kendall e Spearman |
| pytest (opcional) | Testes |
| playwright (opcional) | Teste da interface em navegador |
| Leaflet 1.9.4 (copiado em `web/vendor/`, BSD-2-Clause) | Mapa, sem mapa-base de terceiros |

Os gráficos da interface são SVG próprio, sem biblioteca.

## 10. Instalação

```bash
git clone https://github.com/DaniloSFValim/openlux && cd openlux
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

Python 3.10 ou superior (testado em 3.13). O teste da interface exige
`pip install -e ".[web-tests]"` e um Chromium (variável `OPENLUX_CHROMIUM` se não for o do
Playwright). Para testar o site publicado: `OPENLUX_URL=https://openlux.labdados.org python -m pytest tests/test_web_smoke.py`
(confere também que os arquivos publicados são idênticos aos do repositório).

## 11. Reprodução

Requer conta Earthdata Login com a licença da LAADS aceita e um token em `EARTHDATA_TOKEN`
(nunca versione credenciais).

```bash
python scripts/fetch_blackmarble.py --years 2012-2025
python scripts/fetch_blackmarble.py --product VJ146A4 --years 2018-2025
python scripts/fetch_ibge.py
python scripts/fetch_sectors.py
python scripts/run_annual.py
python scripts/run_sectors.py
python scripts/validate_aggregation.py
python scripts/build_web_data.py
python -m http.server -d web 8000
```

Os hashes das entradas e das saídas de referência estão nos Apêndices A e C de
[`METHODOLOGY.md`](METHODOLOGY.md).

## 12. Validação

Verificações computacionais realizadas (detalhes e números em `METHODOLOGY.md`, seção 11):
testes automatizados com dados sintéticos rotulados; consistência da área raster × IBGE (diferença
máxima de 0,0015 % por município); estabilidade frente ao critério de agregação e à resolução;
sensibilidade à máscara e à camada; comparação entre sensores; determinismo (duas execuções
completas com hashes idênticos); clone limpo da branch com testes aprovados. **Não há comparação com
valores publicados** e não foi definido limite de aprovação a priori.

## 13. Limitações

- Estimativa de radiância orbital, não medição do brilho do céu; sem medições fotométricas de campo.
- Resolução de ≈ 460 m; a banda DNB é pouco sensível à emissão azul de LEDs (Levin et al., 2020).
- **Piso de ruído do S-NPP a partir de 2022** e um aumento comum aos dois sensores que não foi
  separado de um possível artefato do algoritmo compartilhado. A análise mensal (2021–2023) mostra um componente
  específico do S-NPP, com início entre janeiro e março de 2022 e não sinalizado pelo campo de qualidade. A causa não foi identificada.
- O sinal da tendência depende da janela de anos.
- A saturação do DNB em áreas muito iluminadas não foi avaliada.
- População residente não é população exposta; a intensidade por habitante é um índice relativo. Os indicadores por setor usam a população de 2022 em todos os anos.
- Mudança por pixel: a assimetria de aumentos na janela 2012–2025 coincide com o ruído do S-NPP e não deve ser lida como mudança real.
- NASA: política ESDIS lida no texto oficial, com a ressalva de enquadramento indicada na seção 6.

Lista completa: `METHODOLOGY.md`, seção 13.

## 14. Resultados efetivamente disponíveis

Estão disponíveis, e **não validados**: (i) tabelas anuais por município (92 × 14 anos) para a
configuração principal e quatro variações; (ii) tendências por janela e variação; (iii) controles
de ruído de fundo, comparação S-NPP × NOAA-20 e estabilidade; (iv) a interface em `web/`,
construída apenas a partir dessas saídas. Os dados da interface estão em `web/data/`.

O único resultado interpretável com segurança hoje é metodológico: pixels persistentemente
escuros do S-NPP, que tinham radiância média de 0,002–0,015 nW·cm⁻²·sr⁻¹ em 2012–2021, passam a
0,059 em 2022 e 0,13–0,18 em 2023–2025 em terra, bem acima do NOAA-20. Mudanças reais de iluminação
não devem ser inferidas da série S-NPP de 2022–2025 sem essa ressalva.

## 15. Referências

- Falchi, F. et al. (2016). The new world atlas of artificial night sky brightness. *Science Advances*, 2, e1600377. https://doi.org/10.1126/sciadv.1600377
- Kendall, M. G. (1938). A new measure of rank correlation. *Biometrika*, 30, 81–93. https://doi.org/10.1093/biomet/30.1-2.81
- Levin, N. et al. (2020). Remote sensing of night lights: A review and an outlook for the future. *Remote Sensing of Environment*, 237, 111443. https://doi.org/10.1016/j.rse.2019.111443
- Mann, H. B. (1945). Nonparametric Tests Against Trend. *Econometrica*, 13, 245. https://doi.org/10.2307/1907187
- Román, M. O. et al. (2018). NASA's Black Marble nighttime lights product suite. *Remote Sensing of Environment*, 210, 113–143. https://doi.org/10.1016/j.rse.2018.03.017
- Sen, P. K. (1968). Estimates of the Regression Coefficient Based on Kendall's Tau. *Journal of the American Statistical Association*, 63, 1379–1389. https://doi.org/10.1080/01621459.1968.10480934
- Snyder, J. P. (1987). Map projections: A working manual. *Professional Paper*. https://doi.org/10.3133/pp1395
- Virtanen, P. et al. (2020). SciPy 1.0: fundamental algorithms for scientific computing in Python. *Nature Methods*, 17, 261–272. https://doi.org/10.1038/s41592-019-0686-2
- Wang, Z., Román, M. O., Kalb, V. L., Miller, S. D., Zhang, J., Shrestha, R. M. (2021). Quantifying uncertainties in nighttime light retrievals from Suomi-NPP and NOAA-20 VIIRS Day/Night Band data. *Remote Sensing of Environment*, 263, 112557. https://doi.org/10.1016/j.rse.2021.112557
- Wang, Z., Shrestha, R. M., Roman, M. O., Kalb, V. L. (2022). NASA’s Black Marble Multiangle Nighttime Lights Temporal Composites. *IEEE Geoscience and Remote Sensing Letters*, 19, 1–5. https://doi.org/10.1109/LGRS.2022.3176616

Lista gerada e verificada por `scripts/verify_references.py` (arquivo [`docs/REFERENCES.md`](docs/REFERENCES.md)).
A mesma lista sustenta [`METHODOLOGY.md`](METHODOLOGY.md), onde cada obra é citada no ponto de uso.

## 16. Como citar

> Valim, D. (2026). *OpenLux* (versão 0.1.0) [Software]. https://github.com/DaniloSFValim/openlux

O DOI do Zenodo será acrescentado após a publicação da release. Os metadados de citação estão em
[`CITATION.cff`](CITATION.cff).

## 17. Autor e ORCID

Danilo Valim. ORCID: [https://orcid.org/0009-0009-7250-6151](https://orcid.org/0009-0009-7250-6151). Nenhuma afiliação
institucional foi declarada nos metadados.

## 18. DOI

A ser atribuído após a publicação efetiva do registro no Zenodo. Um DOI identifica a versão
arquivada e não comprova avaliação científica nem validação independente do software.
