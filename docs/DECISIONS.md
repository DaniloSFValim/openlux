# Registro de decisoes metodologicas e achados (documento vivo)

Este documento registra decisoes tomadas durante a Fase 2, a evidencia que as sustenta e
o que permanece em aberto. Os numeros abaixo sao **diagnosticos de desenvolvimento**, nao
resultados cientificos validados.

## 1. Decisoes tecnicas

| Tema | Decisao | Evidencia |
|---|---|---|
| Georreferenciamento | Origem no canto superior esquerdo do tile; pixel de 15 arc-s; sem deslocamento de meio pixel. | `StructMetadata.0` do VNP46A4 h13v11: UpperLeft (-50, -20), LowerRight (-40, -30), `GridOrigin=HE5_HDFE_GD_UL`. |
| Area dos pixels | Elipsoide WGS84, formula exata (funcao q de Snyder). | A esfera authalica superestimava ~0,26% em 22 S; com a formula exata a area raster difere <= 0,0015% da area oficial do IBGE (soma 43.750,4 km2). |
| CRS da malha | SIRGAS 2000 (EPSG:4674) tratado como WGS84 (EPSG:4326). | Diferenca de poucos metros, muito menor que o pixel (~460 m). Premissa, nao medida aqui. |
| Agregacao | Cobertura fracionaria por pixel (exactextract); sem reamostragem. | Testes com valores calculados a mao. |
| Mascara padrao | Qualidade 0; terra = codigos 0, 1 e 5 do `Land_Water_Mask`; sem minimo de observacoes. | Variacoes (qualidade 0+1, n_min 5/10) mudam os postos municipais de forma desprezivel (Spearman ~1). |
| Camada principal | `AllAngle_Composite_Snow_Free`. `NearNadir` fica como sensibilidade. | NearNadir tem ~5x menos observacoes e concorda menos (Spearman da tendencia 0,86-0,96). |
| Soma de radiancia | Nao reportada. Reporta-se a **intensidade radiante aparente** (radiancia x area, nW/sr, direcao do sensor). | Evita confundir estatistica com emissao luminosa total. |
| Intensidade por habitante | So para 2022 (ano do Censo), em mW/sr/hab. | Evita misturar Censo com estimativas anuais. |
| Variacao percentual | Definida so quando a linha de base >= piso (quantil 0,25 das medias municipais, declarado em `run_record.json`). | Evita razoes explosivas em areas escuras. |
| Tendencia | Theil-Sen + Kendall, minimo de 8 anos validos, **duas janelas**: 2012-2021 e 2012-2025. | Ver secao 3. |

## 2. Fontes e licencas (estado da verificacao)

| Fonte | Termos | Situacao |
|---|---|---|
| NASA Black Marble VNP46A4 (DOI 10.5067/VIIRS/VNP46A4.002) e VJ146A4 (DOI 10.5067/VIIRS/VJ146A4.002) | Politica da NASA/LAADS: dados abertos, sem restricao a uso e redistribuicao; citacao esperada. | **Nao confirmado no texto oficial**: o PDF de politica do LAADS nao pode ser lido (503/reset); a afirmacao vem de resultados de busca. Conferir antes de publicar. |
| IBGE, Malha Municipal Digital 2024 | "Licenca compativel com Creative Commons BY 4.0", com isencao de responsabilidade (Notas Metodologicas 01/2025). | **Confirmado** no documento oficial. Exige credito ao IBGE. |
| IBGE, Censo 2022 (SIDRA 4709, v93) | Termos especificos do SIDRA nao verificados. | **Em aberto.** |
| EOG VNL V2.x | Catalogo do Earth Engine: dominio publico, sem restricao. A pagina do EOG menciona CC BY 4.0 para "muitos dados". | **Conflito nao resolvido**; fonte nao usada nos resultados atuais (exige login). |
| Falchi et al. (2016) | CC BY-NC 4.0; acesso por formulario. | Dados nao obtidos; nao podem ser redistribuidos. |

## 3. Investigacao do aumento apos 2022 (S-NPP)

Observacao inicial: a media estadual de radiancia (S-NPP, VNP46A4) caiu de 2012 a 2020 e
subiu de 2022 a 2025, com aumento em 90 dos 92 municipios entre 2022 e 2025.

Evidencias (regiao: caixa dos municipios do RJ; classes definidas so pela mediana 2012-2021):

1. **Piso de ruido.** O guia do produto informa que valores de composto < 0,5 nW cm-2 sr-1
   sao zerados para remover ruido residual. Pixels persistentemente escuros (mediana = 0) tiveram
   radiancia media de ~0,002-0,015 em 2012-2021 e 0,059 (2022), 0,182 (2023), 0,141 (2024) e
   0,134 (2025) em terra; no mar, de ~0,001-0,009 para 0,039, 0,076, 0,049 e 0,052. A fracao
   de pixels escuros com valor positivo foi de ~0,4-2,7% ate 2021 para 9,6% (2022) e 19-28% depois.
2. **Excesso especifico do S-NPP.** No NOAA-20 (VJ146A4, 2018-2025), nos mesmos pixels escuros,
   os valores sobem bem menos (mar: 0,001 em 2021 para 0,012-0,017 em 2022-2025; S-NPP: 0,003 para
   0,038-0,075). A razao entre a media estadual NOAA-20/S-NPP cai de ~0,98 (2018-2020) para
   0,87-0,90 (2023-2025).
3. **Componente comum aos dois sensores.** Ambos aumentam de 2021 a 2025 em todas as classes de
   brilho (media em terra: +33% S-NPP, +19,7% NOAA-20); a mudanca pixel a pixel tem correlacao
   r = 0,93 entre os sensores, e o numero de pixels com >= 5 nW cresce em ambos
   (S-NPP 29,1 mil para 35,0 mil; NOAA-20 28,7 mil para 32,4 mil). Isto e coerente com aumento real
   da iluminacao, mas **os dois produtos compartilham o mesmo algoritmo**, entao um artefato comum
   nao esta excluido.
4. **Descartado:** troca de plataforma (so S-NPP no RJ em todos os anos), degradacao de qualidade
   (flag != 0 em ~0,1% dos pixels), mudanca de versao de algoritmo (NPP_PR46A3 2.0.0 / PGE 2.0.5 em
   todos os anos) e mudanca na geometria de observacao (fracao de observacoes proximas ao nadir
   estavel em 0,20-0,23 nos dois sensores).

**Nao resolvido:** a causa do aumento do piso de ruido do S-NPP a partir de 2022 e a parcela real do
aumento comum aos dois sensores. Uma cadeia de processamento independente (EOG) nao foi usada.

**Consequencias adotadas:** (a) tendencias reportadas em duas janelas; (b) controles de ruido de
fundo publicados a cada execucao (`qa_background_controls.csv`); (c) nenhuma interpretacao de
tendencia que dependa de 2022-2025 do S-NPP sem a ressalva acima. O sinal da tendencia depende
da janela: em 2012-2021, 64 de 92 municipios tem inclinacao negativa; em 2012-2025, 74 tem
inclinacao positiva.

**Hipotese nao testada** para a queda em 2012-2021: a banda DNB e pouco sensivel a emissao azul dos
LEDs (Levin et al., 2020), o que pode subestimar areas convertidas para LED.

## 4. Interface (decisoes de cartografia e comunicacao)

| Tema | Decisao |
|---|---|
| Classificacao | Radiancia media: quantis (5 classes) da distribuicao agrupada de todos os anos e municipios, **limites fixos entre anos** para que o controle de ano seja comparavel. Tendencia e variacao: limites em torno de zero (± mediana e ± percentil 90 de \|valor\|, agrupando as janelas). Intensidade por habitante: quantis dos 92 municipios. Todas rotuladas como "classificacao analitica", nao limiares fisicos. |
| Cores | Sequencial YlOrRd e divergente PuOr (ColorBrewer, marcadas como seguras para daltonismo). Nao executei simulacao de daltonismo. Sem dado: cinza neutro com entrada propria na legenda. |
| Significancia | Contorno espesso para p < 0,05 (Kendall) nos mapas de tendencia; tambem informada no tooltip (nao so por cor/borda). |
| Tipos de dado | Selos distinguem "observado (agregado)", "derivado" e "controle de qualidade"; a classificacao e sempre rotulada como analitica. |
| Mapa-base | Nenhum: so os poligonos do IBGE (evita dependencia e termos de tiles de terceiros). Projecao de exibicao Web Mercator; a escala e aproximada para a latitude do estado. |
| Aviso | Resumo sempre visivel + numeros calculados a partir dos controles de ruido (`indicators.json`), nunca digitados. |
| Verificacao | Teste em navegador compara a cor desenhada de municipios selecionados com uma classificacao reimplementada de forma independente em Python. |
| Geometria | Simplificada (0,001 grau, ~110 m) so para exibicao; calculos usaram a malha completa. |

## 5. Validacao computacional (Fase 2.3), estado no fechamento

Produzida por `scripts/validate_aggregation.py` sobre a serie real (14 anos, 92 municipios);
saida em `outputs/validation/aggregation_stability.json` (nao versionada). Os numeros abaixo
descrevem diferencas; **nao ha limite de aprovacao definido a priori**, e o leitor deve julgar
se a estabilidade e suficiente para o uso pretendido.

| Verificacao | Resultado |
|---|---|
| Consistencia raster x vetor (area dos pixels ponderada pela cobertura vs `AREA_KM2` do IBGE) | diferenca maxima por municipio 0,0015%; soma 43.750,425 km2 (raster) vs 43.750,427 km2 (IBGE) |
| Criterio de agregacao: centro do pixel vs cobertura fracionaria | Spearman >= 0,9998; diferenca relativa da media: mediana 0,3-0,4%, percentil 95 1,2-1,9%, maxima 3,4-6,6% |
| Resolucao: grade agregada 2x2 (~920 m) vs original | Spearman >= 0,9996; mediana 0,4-0,5%, p95 2,4-3,0%, maxima 6,6-11,5% |
| Resolucao: grade agregada 4x4 (~1,8 km) vs original | Spearman >= 0,9988; mediana 1,3-1,8%, p95 5,7-8,0%, maxima 14,5-21,7% |
| Configuracoes de mascara (qualidade 0+1, n_min 5 e 10) | Spearman ~ 1 (secao 1); near-nadir: 0,86-0,96 na tendencia |
| Determinismo (serie real, duas execucoes completas) | os 8 arquivos de saida tem SHA-256 identico; entradas identicas |
| Clone limpo da branch publicada + ambiente virtual novo | 66 testes passam, 1 ignorado (teste de navegador sem Playwright) |

Verificacoes **ainda nao feitas**: comparacao com valores publicados (nao se identificou estudo
comparavel); unidades e CRS verificados por teste apenas nas funcoes (nao ha teste automatizado
sobre dado real, que nao e redistribuivel); casos de maior diferenca nao foram investigados por
municipio.

## 6. Fracao da area acima de limiar (indicador E)

F(tau) = sum(w * [L >= tau]) / sum(w) sobre os pixels validos de cada municipio.

| Limiar | Natureza | Fundamento |
|---|---|---|
| 0,5 nW cm-2 sr-1 (`lit_0p5`) | **Documentado** | O guia do Black Marble (secao 2.3) informa que valores de composto < 0,5 sao zerados para remover ruido de fundo; F(0,5) e, portanto, a fracao da area com radiancia detectada no composto. |
| `q50_ref` = 1,49 e `q90_ref` = 27,8 | **Parametro analitico do pesquisador** | Quantis 0,5 e 0,9 da radiancia dos pixels de terra ja iluminados (>= 0,5) em 2012, na caixa dos municipios; fixos para todos os anos. Gravados em `run_record.json`. |

**Achado:** por usar o mesmo valor em que o produto zera ruido, F(0,5) e muito sensivel ao aumento do
piso de ruido do S-NPP apos 2021. Fracao estadual (media ponderada pela area valida): S-NPP 0,329
(2021), 0,441 (2022), 0,612 (2023), 0,531 (2025); NOAA-20 0,327, 0,375, 0,381 e 0,394. A diferenca
entre sensores (0,15 em 2023) tem a mesma origem descrita na secao 3. **F(0,5) do S-NPP nao deve ser
interpretado como expansao da area iluminada apos 2021 sem essa ressalva.** Em municipios muito
urbanos a fracao satura em 1,0 (24 de 92 em 2025), o que limita sua capacidade de discriminar entre eles.
