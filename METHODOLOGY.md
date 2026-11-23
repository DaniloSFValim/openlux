# OpenLux: metodologia

Documento técnico do software OpenLux (versão 0.1.0). Descreve os dados, as equações, os
parâmetros e os procedimentos com detalhe suficiente para que outro pesquisador reproduza os
resultados sem depender de informação não documentada. Decisões e achados em ordem
cronológica estão em [`docs/DECISIONS.md`](docs/DECISIONS.md); o texto de apresentação está em
[`README.md`](README.md).

> **Terminologia.** O OpenLux produz uma
> *estimativa de poluição luminosa baseada em sensoriamento remoto*. As grandezas calculadas
> derivam da radiância noturna observada pelo sensor VIIRS e **não são medições do brilho do céu**
> na superfície.

## 1. Escopo

Agregar a radiância noturna anual (NASA Black Marble) nos 92 municípios do Estado do Rio de
Janeiro, calcular indicadores por município e por ano (2012–2025), analisar sua evolução e a
sensibilidade a escolhas analíticas, registrando a proveniência de cada resultado. Niterói é
tratado como estudo de caso na interface, sem restringir a abrangência estadual.

## 2. Fundamentação científica

O canal Day/Night Band (DNB) do VIIRS mede radiância no visível e infravermelho próximo
(0,5–0,9 µm) à noite. O conjunto Black Marble corrige a radiância observada para efeitos
atmosféricos, de iluminação lunar (BRDF), de luz espúria e de terreno, antes de compor
valores mensais e anuais (Román et al., 2018; Wang et al., 2022). A radiância de superfície
resultante é uma grandeza distinta do brilho artificial do céu, que depende também do
espalhamento atmosférico; por isso este trabalho usa o termo *estimativa baseada em
sensoriamento remoto*.

Três propriedades do sensor condicionam a interpretação:

1. **Efeito angular.** A radiância retornada depende do ângulo de visada, sobretudo em centros
   urbanos densos (Wang et al., 2021; guia do usuário, seção 2.3). O OpenLux usa a camada que
   combina todos os ângulos como principal e a de visada próxima ao nadir como análise de
   sensibilidade.
2. **Sensibilidade espectral.** A banda DNB é pouco sensível à emissão azul de LEDs, o que pode
   subestimar áreas convertidas para essa tecnologia (Levin et al., 2020).
3. **Piso de ruído.** Valores de composto menores que 0,5 nW·cm⁻²·sr⁻¹ são zerados pelo produto
   (guia do usuário, seção 2.3). Variações do ruído de fundo que cruzam esse valor alteram
   indicadores sensíveis a ele (seção 9).

## 3. Produtos de sensoriamento remoto

| Item | VNP46A4 | VJ146A4 |
|---|---|---|
| Descrição | Radiância noturna anual, corrigida por BRDF lunar | Idem, outro satélite |
| Plataforma | Suomi NPP (S-NPP) | NOAA-20 (JPSS-1) |
| Cobertura usada | 2012–2025 | 2018–2025 (comparação entre sensores) |
| Instituição | NASA / LAADS DAAC | NASA / LAADS DAAC |
| DOI | 10.5067/VIIRS/VNP46A4.002 | 10.5067/VIIRS/VJ146A4.002 |
| Versão | Coleção 2.0 (versão 002) | Coleção 2.0 (versão 002) |
| Formato | HDF-EOS5 (`.h5`) | HDF-EOS5 (`.h5`) |
| Autenticação | Conta Earthdata Login, licença da LAADS aceita, token | idem |

Características comuns, confirmadas por inspeção dos arquivos do tile `h13v11` e pelo guia do
usuário (Black Marble User Guide v2.0, outubro de 2024):

- **Grade:** latitude/longitude regular de 15 arc-s (≈ 460 m), 2400 × 2400 pixels por tile de
  10° × 10°; o tile `h13v11` cobre lon −50° a −40° e lat −20° a −30° e contém todo o Estado do
  Rio de Janeiro. Origem no canto superior esquerdo (`GridOrigin=HE5_HDFE_GD_UL`); os vetores
  `lat`/`lon` do arquivo são as bordas superior-esquerdas dos pixels (ver seção 5).
- **Camadas usadas:** `AllAngle_Composite_Snow_Free` (principal) e
  `NearNadir_Composite_Snow_Free` (sensibilidade), cada uma com `_Num` (observações),
  `_Quality` e `_Std`; mais `Land_Water_Mask`. O RJ não tem neve; as camadas
  `*_Snow_Covered` não são usadas.
- **Unidade:** nW·cm⁻²·sr⁻¹; `scale_factor = 1`, `offset = 0`.
- **Valores de preenchimento:** −999,9 (radiância e desvio), 65535 (`_Num`), 255 (qualidade e
  máscaras).
- **Qualidade (`_Quality`):** 0 = boa, 1 = ruim, 2 = preenchida com histórico, 255 = fill.
- **`Land_Water_Mask`:** 0 = terra e deserto, 1 = terra sem deserto, 2 = água interna,
  3 = mar, 5 = costeiro.
- **Composição (guia, seção 2.3):** observações diárias corrigidas passam por remoção de
  valores atípicos pelo critério de Tukey (fora de Q1 − 1,5·IQR a Q3 + 1,5·IQR) e o composto é
  a média das restantes; valores < 0,5 nW·cm⁻²·sr⁻¹ são zerados; pixels contaminados por
  aurora são preenchidos.
- **Versão do algoritmo:** os arquivos S-NPP de 2012 a 2025 usados declaram
  `NPP_PR46A3 2.0.0` / PGE 2.0.5 (atributos HDF5); isso não foi verificado para o NOAA-20.

O produto mensal VNP46A3 **não foi usado nem testado**; as diferenças metodológicas entre
os produtos mensal e anual não foram estudadas aqui.

## 4. Dados territoriais e populacionais

| Dado | Fonte | Detalhe |
|---|---|---|
| Municípios | IBGE, Malha Municipal Digital 2024 (RJ) | 92 municípios; SIRGAS 2000 (EPSG:4674); licença compatível com CC BY 4.0 (Notas Metodológicas 01/2025) |
| População | IBGE, Censo Demográfico 2022, SIDRA tabela 4709, variável 93 (população residente) | Nível município; total do RJ 16.055.174 |

A população é usada apenas em 2022 (ano do Censo). Os termos de uso do SIDRA foram
conferidos pelo autor em 2026-11-19 (reuso permitido com citação da fonte); o texto não foi lido por ferramenta
automatizada, porque as páginas do IBGE bloquearam o acesso automatizado. Os dados da NASA seguem a política
ESDIS (CC0 sem marcação de restrição, citação solicitada), com a ressalva de enquadramento descrita em
`docs/DECISIONS.md`.

## 5. Tratamento dos dados

1. **Aquisição e integridade.** Cada arquivo é baixado para `.part`, tem a assinatura HDF5
   conferida (8 bytes iniciais), o SHA-256 calculado e só então é renomeado. Páginas de login e
   respostas de erro nunca são gravadas como dados. URL, data, tamanho e SHA-256 ficam em
   `data/metadata/downloads/*.json` (Apêndice A).
2. **Leitura.** Cada camada de radiância é lida com sua `_Quality`, `_Num` e a
   `Land_Water_Mask`.
3. **Máscara de validade.** Um pixel é *válido* se e somente se: radiância ≠ −999,9 e ≥ 0;
   qualidade ∈ {0} (principal; {0, 1} na sensibilidade); `_Num` ≠ 65535 e ≥ `n_min`
   (principal: 1); e `Land_Water_Mask` ∈ {0, 1, 5}. Pixels inválidos viram NaN e saem do
   numerador e do denominador de todo indicador.
4. **Georreferenciamento.** `from_origin(lon₀, lat₀, 15″, 15″)` com `(lon₀, lat₀)` = canto
   superior esquerdo do tile, sem deslocamento de meio pixel, conforme o `StructMetadata` do
   arquivo (UpperLeft = −50, −20; LowerRight = −40, −30).
5. **Sistema de referência.** O raster está em lat/lon (EPSG:4326). A malha do IBGE está em
   SIRGAS 2000 (EPSG:4674). A diferença entre os dois é de poucos metros, muito menor que o pixel
   (≈ 460 m); a malha é tratada como EPSG:4326 por declaração explícita no código. Essa
   equivalência é uma premissa, não uma medição feita neste trabalho. O software rejeita
   polígonos sem CRS ou com CRS diferente do declarado para o raster.
6. **Sem reamostragem.** Todos os indicadores usam a grade nativa; a agregação 2 × 2 e 4 × 4 só
   existe como teste de estabilidade (seção 11).

## 6. Agregação zonal

Para o município $m$ e o pixel $i$:

$$ w_i = \frac{\lvert P_i \cap M \rvert}{\lvert P_i \rvert} $$

é a fração do pixel $P_i$ coberta pelo polígono $M$ (cobertura fracionária, calculada no plano
lat/lon com a biblioteca `exactextract`; dentro de um pixel de ≈ 460 m a diferença para a
cobertura geodésica é desprezível). Seja $V$ o conjunto de pixels válidos com $w_i > 0$.

**Área do pixel.** No elipsoide WGS84, para o pixel entre as latitudes $\varphi_S$ e $\varphi_N$ e
largura $\Delta\lambda$ (rad):

$$ A_i = \frac{a^2}{2}\,\Delta\lambda\,\big[q(\varphi_N) - q(\varphi_S)\big],
\qquad
q(\varphi) = (1-e^2)\left[\frac{\sin\varphi}{1-e^2\sin^2\varphi}
- \frac{1}{2e}\ln\frac{1-e\sin\varphi}{1+e\sin\varphi}\right] $$

com $a = 6\,378\,137$ m e $e^2 = 0{,}00669437999014$ (Snyder, 1987). A esfera authalica não é
usada: ela só conserva a área no total global e superestima ≈ 0,26 % em 22° S.

## 7. Indicadores por município e ano

Seja $L_i$ a radiância (nW·cm⁻²·sr⁻¹) do pixel válido $i$.

| Indicador | Definição | Unidade |
|---|---|---|
| Radiância média | $\bar L_m = \sum_{i\in V} w_i L_i \big/ \sum_{i\in V} w_i$ | nW·cm⁻²·sr⁻¹ |
| Radiância mediana | Menor $L_{(k)}$ cujo peso acumulado atinge $\ge 0{,}5\sum w_i$ (mediana ponderada inferior) | nW·cm⁻²·sr⁻¹ |
| Intensidade radiante aparente | $S_m = \sum_{i\in V} w_i L_i A_i$, com $A_i$ em cm² | nW·sr⁻¹ |
| Fração da área válida | $\sum_{i\in V} w_i \big/ \sum_{\text{todos}} w_i$ | adimensional |
| Fração iluminada | $F_m(\tau) = \sum_{i\in V} w_i\,[L_i \ge \tau] \big/ \sum_{i\in V} w_i$ | adimensional |
| Intensidade por habitante | $S_m \cdot 10^{-6} / P_m$ (2022) | mW·sr⁻¹ por habitante |

**Observações de interpretação.**

- $S_m$ é radiância × área: uma intensidade na direção observada pelo sensor. **Não é a emissão
  luminosa total** do município. A soma bruta dos valores de pixel não é calculada.
- $P_m$ é a população residente do Censo 2022. A razão $S_m/P_m$ é um índice relativo; não
  representa consumo nem emissão individual, e ignora iluminação de turismo, indústria e vias.
  É calculada só para 2022 para não misturar Censo com estimativas.
- Limiares $\tau$ de $F_m$: o valor **documentado** é 0,5 nW·cm⁻²·sr⁻¹ (limite de zeragem do
  produto). Os valores **analíticos** são os quantis 0,5 e 0,9 da radiância dos pixels de terra
  com $L \ge 0{,}5$ no ano de referência (2012), na caixa dos municípios (resultaram 1,49 e
  27,8), fixos para todos os anos; são parâmetros do pesquisador, não limiares físicos.
- Um polígono sem pixels válidos retorna NaN, nunca zero.

## 8. Análise temporal

Para cada município e janela de anos, sobre a série de $\bar L_m$ dos anos válidos:

- **Tendência:** inclinação de Theil–Sen, a mediana das inclinações entre todos os pares de
  anos (Sen, 1968), e teste de Kendall sobre a mesma série (Kendall, 1938; Mann, 1945), como
  implementados em SciPy (`scipy.stats.theilslopes`, `kendalltau`; Virtanen et al., 2020). Exige
  `min_years = 8` anos válidos, caso contrário a saída é NaN.
- **Variação:** $\Delta = \bar L(t_2) - \bar L(t_1)$ e $\Delta\% = 100\,\Delta/\bar L(t_1)$,
  esta última definida somente se $\bar L(t_1) \ge$ piso e $> 0$. O piso é o quantil 0,25 das
  médias municipais do ano inicial da janela e é gravado em `run_record.json`.
- **Janelas:** 2012–2021 e 2012–2025, calculadas separadamente. O sinal da tendência depende da
  janela (seção 9).

## 9. Controles de ruído de fundo

Como a série S-NPP apresenta aumento de radiância em pixels persistentemente escuros a partir de
2022, o pipeline calcula, a cada execução, a radiância média e a fração de valores positivos
nos pixels cuja **mediana em 2012–2021 é zero**, separadamente para terra e mar (caixa dos
municípios). A classe é definida somente pelos anos de linha de base, para não selecionar
pixels olhando o período avaliado. Se a média desses pixels sobe, o piso de ruído mudou, o que
não é crescimento de iluminação.

Resultado desta execução (S-NPP, pixels escuros em terra): média de 0,002–0,015 nW·cm⁻²·sr⁻¹ em
2012–2021, 0,059 em 2022 e 0,13–0,18 em 2023–2025; no NOAA-20, bem menor. Os números completos e
a investigação estão em `docs/DECISIONS.md` (seções 3 e 6).

## 10. Parâmetros

| Parâmetro | Valor | Natureza |
|---|---|---|
| Camada principal | `AllAngle_Composite_Snow_Free` | Escolha analítica |
| Qualidade permitida | {0} | Escolha analítica |
| `n_min` (observações) | 1 | Escolha analítica |
| Códigos de terra | {0, 1, 5} | Escolha analítica |
| `min_years` | 8 | Escolha analítica |
| Janelas de tendência | 2012–2021; 2012–2025 | Escolha analítica |
| Quantil do piso de variação | 0,25 | Escolha analítica |
| Ano da população | 2022 | Censo |
| Limiar iluminado | 0,5 nW·cm⁻²·sr⁻¹ | Documentado no produto |
| Quantis dos limiares analíticos | 0,5 e 0,9 (ano de referência 2012) | Escolha analítica |
| Anos de linha de base dos controles | 2012–2021 | Escolha analítica |
| Sensibilidade | qualidade {0,1}; near-nadir; `n_min` 5 e 10 | Teste de robustez |
| Simplificação da geometria exibida | 0,001° (≈ 110 m), só na interface | Visualização |

Todos os parâmetros efetivamente usados em uma execução ficam em `run_record.json`.

## 11. Validação e análise de sensibilidade

Nenhum resultado foi comparado a valores publicados, porque não se identificou estudo
comparável. As verificações realizadas descrevem estabilidade e consistência; **não há limite de
aprovação definido a priori**.

| Verificação | Resultado |
|---|---|
| Testes unitários e de integração (dados sintéticos rotulados) | 119 testes (109 sem os testes de navegador): funções matemáticas, agregação zonal com valores calculados à mão, dados ausentes, CRS, integridade de arquivos, reprodutibilidade, dados e interface |
| Consistência raster × vetor: área dos pixels ponderada vs `AREA_KM2` do IBGE | Diferença máxima por município de 0,0015 %; soma 43.750,425 km² vs 43.750,427 km² |
| Critério de agregação: centro do pixel vs cobertura fracionária | Spearman ≥ 0,9998; diferença relativa da média: mediana 0,3–0,4 %, p95 1,2–1,9 %, máxima 3,4–6,6 % |
| Resolução: agregação 2 × 2 | Spearman ≥ 0,9996; mediana 0,4–0,5 %, p95 2,4–3,0 %, máxima 6,6–11,5 % |
| Resolução: agregação 4 × 4 | Spearman ≥ 0,9988; mediana 1,3–1,8 %, p95 5,7–8,0 %, máxima 14,5–21,7 % |
| Configurações de máscara (qualidade 0+1, `n_min` 5 e 10) | Spearman ≈ 1 nos postos e nas inclinações |
| Camada near-nadir | Spearman das inclinações 0,86–0,96 |
| Determinismo | Duas execuções completas sobre os dados reais geram 8 arquivos com SHA-256 idêntico |
| Comparação S-NPP × NOAA-20 (2018–2025) | Spearman das inclinações municipais 0,80; mesmo sinal em 81,5 % dos municípios |

Verificações **não realizadas**: comparação com valores publicados; investigação por município dos
casos de maior diferença na estabilidade; teste com dados reais em integração contínua (os dados
não são redistribuídos).

## 12. Reprodução passo a passo

Requisitos: Python 3.10 ou superior (testado em 3.13.18, pacotes do Apêndice B); conta
Earthdata Login com a licença da LAADS aceita; ≈ 2,5 GB livres.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
export EARTHDATA_TOKEN="..."        # gerado na conta Earthdata; nunca versione
python scripts/fetch_blackmarble.py --years 2012-2025                        # VNP46A4
python scripts/fetch_blackmarble.py --product VJ146A4 --years 2018-2025      # NOAA-20
python scripts/fetch_ibge.py                                                 # malha + população
python scripts/run_annual.py                    # saídas em outputs/annual/
python scripts/validate_aggregation.py          # saídas em outputs/validation/
python scripts/build_web_data.py                # web/data/
pytest                                          # testes
python -m http.server -d web 8000               # interface
```

Conferências: (1) o SHA-256 de cada arquivo baixado deve coincidir com o Apêndice A (e com
`data/metadata/downloads/*.json`); se a NASA reprocessar a coleção, os hashes mudam e os
resultados podem mudar; (2) `outputs/annual/run_record.json` registra o commit do código, os
parâmetros, os hashes das entradas e os das saídas, que devem coincidir com o Apêndice C quando
o ambiente for o do Apêndice B. A igualdade byte a byte foi verificada **apenas** neste ambiente;
em outra plataforma, diferenças nos últimos dígitos são possíveis (os CSV usam 10 algarismos
significativos).

## 13. Limitações

1. Estimativa de radiância orbital, não medição do brilho do céu; sem medições fotométricas de campo.
2. Resolução de ≈ 460 m; municípios pequenos têm poucas centenas de pixels.
3. A banda DNB é pouco sensível à emissão azul de LEDs (Levin et al., 2020).
4. **Piso de ruído do S-NPP a partir de 2022** e um componente de aumento comum aos dois sensores
   que não foi separado de um possível artefato do algoritmo compartilhado; não houve cadeia
   de processamento independente (o EOG exige login e não foi usado). A fração iluminada com
   limiar 0,5 é especialmente afetada.
5. O sinal da tendência depende da janela de anos (2012–2021: 64 de 92 municípios com
   inclinação negativa; 2012–2025: 74 com inclinação positiva).
6. A saturação do DNB em áreas muito iluminadas não foi avaliada.
7. Máscara de água: municípios com lagoa ou mar na malha perdem área válida (menos de 90 % em
   Arraial do Cabo, Iguaba Grande e São Pedro da Aldeia em 2023).
8. População residente não é população exposta; a intensidade por habitante é um índice relativo.
9. Premissa SIRGAS 2000 ≈ WGS84 (poucos metros); geometria exibida simplificada só para
   visualização.
10. Mesmo algoritmo em S-NPP e NOAA-20: a concordância entre eles não prova ausência de artefato comum.
11. Indicadores não implementados: comparação com o Atlas de Falchi et al. (2016), alterações espaciais
    pixel a pixel e comparação urbano × não urbano.

## 14. Referências

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

Documentação técnica: Black Marble User Guide, Version 2.0 (NASA, outubro de 2024);
Notas Metodológicas 01/2025, Malha Municipal Digital e Áreas Territoriais 2024 (IBGE).

## Apêndice A. Entradas (nome, tamanho e SHA-256 dos arquivos usados)

### A.1 VNP46A4 v2.0 (Suomi NPP), tile h13v11

DOI 10.5067/VIIRS/VNP46A4.002. Adquirido em 2026-11-19T17:35:04Z (UTC).

| year | name | tamanho_bytes | sha256 |
|---|---|---|---|
| 2012 | VNP46A4.A2012001.h13v11.002.2025086170108.h5 | 84168826 | 772689356c6cb25bca37ff8b2e59c4e8e812184a004f5b8c7f576117325fa070 |
| 2013 | VNP46A4.A2013001.h13v11.002.2025087045253.h5 | 85703451 | 20b9e00ce1ab4e5353fe3bb2d59a6e26e71663826a83ad5a738debcf870008ef |
| 2014 | VNP46A4.A2014001.h13v11.002.2025091134728.h5 | 85692140 | 3a695f053526595f54eb9a02ecf8b678de6efeac5718a2643ce325367db5a93f |
| 2015 | VNP46A4.A2015001.h13v11.002.2025093111829.h5 | 86837522 | f273c18ef66a3a036046536f7b2aeefe96b7f17890ad4402158cf65de9112201 |
| 2016 | VNP46A4.A2016001.h13v11.002.2025101113318.h5 | 84968880 | 96bb40714fb78d4633c6e5eb09797ee49c8f86d22b52dabd36f275eaac8dbdbd |
| 2017 | VNP46A4.A2017001.h13v11.002.2025105144552.h5 | 84903894 | 4251ec1c192699945c2cc5e6e2330ce35afefeb6908ed93284990185094356d5 |
| 2018 | VNP46A4.A2018001.h13v11.002.2025113133713.h5 | 85859763 | dce0bade4be67167b141d69361c4d204de77d7fbececec0626c56c98dca4e4d1 |
| 2019 | VNP46A4.A2019001.h13v11.002.2025133143159.h5 | 85083900 | 1a88900ecc1c7fb5f8abcb1eda65a9efca91e7b14343357e50f94878b461e0cc |
| 2020 | VNP46A4.A2020001.h13v11.002.2025134014932.h5 | 86034959 | ee478977631a201d92ee050549242f7a537b5c87dab1494a9602102b15125b50 |
| 2021 | VNP46A4.A2021001.h13v11.002.2025149104007.h5 | 86743531 | a4d061a7dbfca7c5957c027fa52d82752776894c8841b55b3849032e9ec26ded |
| 2022 | VNP46A4.A2022001.h13v11.002.2025156103312.h5 | 88731153 | d8a5045101d874cbb4dfe11f7555a03229efc90ce67dd487bf03c95a6256c508 |
| 2023 | VNP46A4.A2023001.h13v11.002.2025161112706.h5 | 94717389 | 3426db53c89d08da7d769a95aae5fc9ca38beb4ffe38a94490afa3a441ea2129 |
| 2024 | VNP46A4.A2024001.h13v11.002.2025161225303.h5 | 94284560 | 8bfcba95fa3cf1b20b3b43bf0f01b19f1855abbb4ec55987f9c0c5e25a3f56d1 |
| 2025 | VNP46A4.A2025001.h13v11.002.2026076174035.h5 | 93487015 | 088c1b07cc0acafb8a6d02d364136dc7a2b48f6234b55b0951053af306df6f2a |

### A.2 VJ146A4 v2.0 (NOAA-20), tile h13v11

DOI 10.5067/VIIRS/VJ146A4.002. Adquirido em 2026-11-19T17:43:10Z (UTC).

| year | name | tamanho_bytes | sha256 |
|---|---|---|---|
| 2018 | VJ146A4.A2018001.h13v11.002.2025086180402.h5 | 84244406 | 3b0ab77ecf644292b4af90873f55e9e4cdb5caf7fa6f176527a42612507c72c9 |
| 2019 | VJ146A4.A2019001.h13v11.002.2025087053528.h5 | 83913481 | 735111d8347d009c80538f882b7164fb30aa145e0b1d3f2be484ad4a9d07c076 |
| 2020 | VJ146A4.A2020001.h13v11.002.2025090181443.h5 | 85392611 | 9493a2e4f215834371ab39cba2c0e4ea97870b514aa20a25feb7f688996a521e |
| 2021 | VJ146A4.A2021001.h13v11.002.2025111202644.h5 | 85632767 | 4634de2fbaad0e733477bb34321b1c7fce275c6714473b32c6bce4a8a4efafe9 |
| 2022 | VJ146A4.A2022001.h13v11.002.2025133144451.h5 | 86366447 | c3bf3cc3fde616cf0af87d931e38c68bfeaa7a8115d88488f832a0ee00e01884 |
| 2023 | VJ146A4.A2023001.h13v11.002.2025148165106.h5 | 86886356 | c8a5ebef1afd90bd60f9e2d09e848e0702d746c11c0eae2d08fead20c026b778 |
| 2024 | VJ146A4.A2024001.h13v11.002.2025149035628.h5 | 88812862 | c147da230a7685ed8c53061eb212de01266d453e15d6656479cbae474824e0f1 |
| 2025 | VJ146A4.A2025001.h13v11.002.2026072175707.h5 | 88696240 | 1d7c66db4bccd568a89aba4cc4ff5ddec59444cf8f0eca70af4aeadd844e29aa |

### A.3 IBGE

Adquirido em 2026-11-19T17:34:13Z (UTC).

| name | size_bytes | sha256 |
|---|---|---|
| RJ_Municipios_2024.zip | 5127653 | 30881e67e483fca5a0682118fbd5b5d20b3487806cd9cf18a27732d68080d314 |
| sidra_4709_v93_RJ_2022.json | 24316 | 2e12a003210a1bca5a4291ba3bbd3ec02fc981d987f27ba77dba089f067b9aa6 |

## Apêndice B. Ambiente de referência

Python 3.13.18, Linux. Pacotes (versões efetivamente usadas nos resultados e testes):

| Pacote | Versão |
|---|---|
| numpy | 2.5.3 |
| pandas | 3.0.5 |
| h5py | 3.16.0 |
| rasterio | 1.5.2 |
| geopandas | 1.2.0 |
| scipy | 1.18.1 |
| exactextract | 0.3.0 |
| shapely | 2.2.0 |
| pyproj | 3.8.0 |
| pytest | 9.1.1 |
| playwright | 1.65.2 |

## Apêndice C. Saídas de referência

Execução `scripts/run_annual.py` com o commit `2889bb9` (árvore sem alterações,
`dirty = false`) e as entradas do Apêndice A. SHA-256 de `outputs/annual/`:

| Arquivo | SHA-256 |
|---|---|
| annual_main.csv | d24a9ac2bfab663a58a6b168740ee152de2464c3eb9cff23d4c7182a87d67002 |
| annual_n_min_10.csv | e887508773e6ea2ba8eac155d9b51845121ef8d9c9793b228534b5065d12d52e |
| annual_n_min_5.csv | d24a9ac2bfab663a58a6b168740ee152de2464c3eb9cff23d4c7182a87d67002 |
| annual_near_nadir.csv | 09e08b2eb0577f47bd04d79d45144f1f3b3f53f0e2468b7b86047cb6403634be |
| annual_quality_0_1.csv | 660dc300d4a260c5850a8661fd4179470c71d55a51fd273b7daf8860a1a268fc |
| qa_background_controls.csv | 9ca617f1b24614f2cd395c530e566b5a646c2edcacb411b4b73fa6aed75f87cd |
| sensitivity.json | b66919731f5ca8dc26ea6d06764f855e55f5e30c3a37b52359301e6f8ac4dd75 |
| trends_main.csv | 7c5912e4278f41a0f26fd9cc13d0490441e6bbfd428f1be0e15d49e047a45666 |
