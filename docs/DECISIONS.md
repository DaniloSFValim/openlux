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
| NASA Black Marble VNP46A4 (DOI 10.5067/VIIRS/VNP46A4.002) e VJ146A4 (DOI 10.5067/VIIRS/VJ146A4.002) | Politica ESDIS da NASA (https://www.earthdata.nasa.gov/learn/use-data/data-use-policy, lida em 2026-11-19): dados de missoes lideradas pela NASA, sem marcacao de restricao ou licenca, sao licenciados como CC0, sem restricao de uso; citacao fortemente solicitada. | **Confirmado com ressalva.** Os arquivos inspecionados nao tem atributo de licenca ou restricao (49 atributos; produtor "VIIRS Land SIPS Processing Group"). O enquadramento como "missao liderada pela NASA" e interpretacao minha; o texto tambem diz que dados nao NASA distribuidos pela ESDIS seguem a licenca da organizacao patrocinadora. |
| IBGE, Malha Municipal Digital 2024 | "Licenca compativel com Creative Commons BY 4.0", com isencao de responsabilidade (Notas Metodologicas 01/2025). | **Confirmado** no documento oficial. Exige credito ao IBGE. |
| IBGE, Censo 2022 (SIDRA 4709, v93) | Reuso permitido com citacao da fonte, conforme os termos do IBGE/SIDRA. | **Confirmado pelo autor** em 2026-11-19, em navegador. As paginas do IBGE retornaram 403 ao acesso automatizado, entao o texto nao foi lido por ferramenta; a forma de citacao no README e redacao do projeto. |
| EOG VNL V2.x | Documento oficial de licenca do EOG: CC BY 4.0, com atribuicao e o aviso do "Exhibit 1". O catalogo do Earth Engine a lista como dominio publico; o documento do proprio EOG prevalece. | **Confirmado no documento oficial do EOG** (lido nesta fase); fonte **nao usada** nos resultados (exige login). Se for usada, deve incluir a atribuicao e o aviso exigidos. |
| Falchi et al. (2016) | CC BY-NC 4.0; dados por formulario de solicitacao. | Dados nao obtidos; nao podem ser redistribuidos e o uso nao comercial limita derivados. O atlas usa **um unico composto VIIRS de 6 meses** (mai, jun, set, out, nov e dez de 2014, do EOG) com mascara DMSP de 2013, e traz luminancia artificial no zenite (mcd/m2) em 30 arcsec: outra grandeza e outra epoca. |
| IBGE, malha de setores censitarios 2022 com atributos (RJ, CD2022) | Mesma politica de reuso do IBGE para o Censo 2022 (citacao da fonte). | Termos do SIDRA conferidos pelo autor; a malha de setores esta no mesmo portal e **o texto especifico dela nao foi lido por ferramenta** (o IBGE retorna 403 a acesso automatizado). Dado bruto nao redistribuido. |

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

## 7. Análise mensal do piso de ruído (2021-2023)

Pergunta: *quando* o piso de ruído do S-NPP começa a subir e isso acompanha algo observável? Dados: VNP46A3 (S-NPP) e
VJ146A3 (NOAA-20), 36 meses de cada, tile h13v11 (hashes no Apêndice A.4/A.5 do `METHODOLOGY.md`). Método
(`scripts/analyze_monthly_noise.py`): mesma classe de pixels escuros da seção 3 (mediana zero na linha de base anual 2012-2021 do S-NPP),
camada `AllAngle_Composite_Snow_Free`, qualidade 0, terra; por mês, a radiância média e a fração de valores positivos
desses pixels, o número mediano de observações e a composição de qualidade. Resultados mensais completos: `outputs/monthly/monthly_noise_controls.csv` (não versionado).

**Meses de céu claro (junho a agosto; 13 a 18 observações por pixel nos dois sensores)**, fração de pixels escuros em terra com valor positivo:

| Sensor | 2021 | 2022 | 2023 | 2023 / 2021 |
|---|---|---|---|---|
| S-NPP | 0,012 | 0,065 | 0,146 | ×12,3 |
| NOAA-20 | 0,010 | 0,027 | 0,029 | ×2,8 |

A radiância média desses pixels tem a mesma forma: S-NPP 0,020 → 0,043 → 0,097 (×4,9); NOAA-20 0,008 → 0,019 → 0,020 (×2,5).

**Início no S-NPP** (fração positiva por mês, 2021 / 2022 / 2023): janeiro 0,016 / 0,032 / 0,683; fevereiro 0,015 / 0,240 / 0,346;
março 0,010 / 0,147 / 0,449; abril 0,032 / 0,133 / 0,440. Em 2022, março e abril (21 e 17 observações) já estão claramente acima de 2021, enquanto
o NOAA-20 nos mesmos meses fica em 0,053 e 0,067. O início cai, portanto, entre janeiro e março de 2022, com resolução mensal.

**O que isso diz e o que não diz**

1. Há um componente **específico do S-NPP**, que cresce de 2021 a 2023 e **não** aparece no NOAA-20 de 2022 para 2023.
2. Há também um aumento **de 2021 para 2022 nos dois sensores** (×2,6 no NOAA-20), compatível com o componente comum da seção 3; esta análise não o explica.
3. **Não é efeito de número de observações:** nos meses de céu claro as observações são comparáveis e a fração de qualidade ruim em terra permanece em 0,1 % nos três anos.
   O aumento **não é sinalizado** pelo campo de qualidade do produto.
4. O ruído é fortemente **sazonal** nos dois sensores e acompanha o número de observações (correlação de postos entre fração positiva e observações:
   NOAA-20 −0,68, S-NPP −0,41, 36 meses cada), com picos em meses de poucas observações (por exemplo, outubro de 2021 tem mediana de 2 observações e 63 % de pixels de qualidade ruim).
   Compor o ano com meses mais ou menos nublados também desloca o composto anual.
5. A classe de pixels **no mar** é muito irregular de mês para mês nos dois sensores (embarcações, plataformas e queimas intermitentes); o controle em terra é mais confiável.

**Limites:** três anos apenas; classe escura definida pelo S-NPP; um único tile; **a causa não foi identificada**. Possibilidades que esta análise **não testa**:
mudanças nas correções do produto, comportamento do instrumento, outros fatores atmosféricos ou de geometria. Não há afirmação sobre a causa.

**Consequências para o uso dos dados:** a série anual S-NPP a partir de 2022 não deve ser usada para tendência sem correção ou sem confronto com o NOAA-20 (disponível desde 2018);
o piso de ruído deve ser reportado junto de qualquer indicador sensível a ele (como a fração iluminada com limiar 0,5). Correção ou uso preferencial do NOAA-20 para os anos recentes ficam como próximo passo.

## 8. Série municipal do NOAA-20 e comparação com o S-NPP (2018-2025)

Método: o pipeline anual completo (`openlux.pipeline.run_annual`) sobre VJ146A4 2018-2025, mesma configuração principal, mesma malha e máscara
(`scripts/compare_sensors_municipal.py`); comparação por município com `openlux.pipeline.compare_municipal_series`. Saídas em `outputs/noaa20/` e
`outputs/sensors/` (não versionadas).

**Níveis municipais por ano** (92 municípios; NOAA-20 em relação ao S-NPP):

| Ano | Spearman | Razão mediana NOAA-20/S-NPP | |S-NPP − NOAA-20| mediano (nW·cm⁻²·sr⁻¹) |
|---|---|---|---|
| 2018 | 0,9994 | 0,981 | 0,024 |
| 2019 | 0,9996 | 0,986 | 0,015 |
| 2020 | 0,9996 | 1,012 | 0,024 |
| 2021 | 0,9990 | 0,979 | 0,033 |
| 2022 | 0,9990 | 0,913 | 0,105 |
| 2023 | 0,9973 | 0,794 | 0,363 |
| 2024 | 0,9982 | 0,853 | 0,283 |
| 2025 | 0,9987 | 0,829 | 0,351 |

**Forma da diferença** (ajuste robusto de Theil-Sen, NOAA-20 = α + β·S-NPP, 92 pontos por ano): β = 0,977; 0,975; 0,984; 0,952 (2018 a 2021) e 0,946; 0,916; 0,923; 0,887 (2022 a 2025),
com α passando de ≈ +0,01 a +0,07 para −0,11 a −0,22. O excesso do S-NPP (S-NPP − NOAA-20) é positivo na grande maioria dos municípios e cresce com o brilho (correlação de postos 0,95 a 0,98 em 2023-2025).
Em termos relativos, é maior nos municípios escuros (25 % a 35 % em Miguel Pereira, Piraí, Aperibé, Areal, Carapebus em 2025) e menor no núcleo urbano (≈ 10 % em Niterói e Itaboraí): a diferença
combina um componente **aditivo** (piso de ruído) e um **relativo** (ganho). Não é só um deslocamento constante.

**Tendência 2018-2025 por município** (Theil-Sen): S-NPP positiva em 89 de 92 (p < 0,05 em 59); NOAA-20 positiva em 72 de 92 (p < 0,05 em 53). Concordância entre sensores: Spearman das inclinações 0,80;
mesmo sinal em 81,5 % (17 municípios com sinal oposto, todos com inclinações próximas de zero: |inclinação| mediana 0,043 no S-NPP e 0,008 no NOAA-20 nW·cm⁻²·sr⁻¹ por ano).
Na janela 2018-2021, a concordância é maior (Spearman 0,91; mesmo sinal em 89 %). **Variação 2021 → 2025**: Spearman 0,97 entre sensores, mas a mediana é +0,52 no S-NPP contra +0,23 no NOAA-20.
Niterói: inclinação S-NPP +0,459 (p = 0,109) e NOAA-20 +0,149 (p = 0,275); variação 2021 → 2025 de +6,23 e +4,26.

**Leitura.** (i) Até 2021 os dois sensores concordam em nível (≈ 2 %) e em ordem dos municípios; a divergência começa em 2022, em linha com as seções 3 e 7. (ii) Mesmo no NOAA-20 há aumento positivo em 72 dos 92 municípios (2018-2025):
existe um componente comum aos dois sensores, que pode ser real ou artefato do algoritmo compartilhado; **esta análise não os separa**. (iii) O S-NPP superestima a variação recente em relação ao NOAA-20 (mediana +0,52 contra +0,23).

**Recomendação provisória para tendências recentes:** usar o NOAA-20 como referência para 2018-2025, o S-NPP até 2021 para a série longa, e **não** apresentar tendências do S-NPP que cruzem 2021 sem esse confronto.
Limites: o NOAA-20 tem só 8 anos; o ajuste usa 92 municípios por ano; um único tile; causa da divergência não identificada; não há verdade de campo.

## 9. Fechamento da Fase 1 e indicadores adicionais da Fase 2

### 9.1 Lacunas de fonte (Fase 1)

- **Falchi et al. (2016).** O atlas e derivado de um unico composto VIIRS de 6 meses (2014) com mascara DMSP; a
  grandeza e luminancia artificial zenital modelada (mcd/m2), nao radiancia no topo da atmosfera. Os dados nao
  foram obtidos. Uma comparacao, se vier a ser feita, seria de **ordenacao espacial** (correlacao de postos), nunca de
  valor absoluto, e nao validaria o OpenLux: seria uma conferencia de plausibilidade entre produtos relacionados.
- **EOG VNL.** Licenca CC BY 4.0 conforme o documento oficial do EOG (atribuicao e aviso do Exhibit 1). Exige login;
  nao usado. Continua sendo a candidata a cadeia de processamento independente.
- **Anual (A4) x mensal (A3).** Media dos 12 mensais municipais / anual, 2021-2023, 92 municipios (script
  `scripts/compare_monthly_annual.py`; mesmas mascaras e agregacao):

  | Sensor | Ano | Spearman | Razao mensal/anual: mediana [p10, p90] |
  |---|---|---|---|
  | S-NPP | 2021 | 0,995 | 1,007 [0,949; 1,150] |
  | S-NPP | 2022 | 0,999 | 1,025 [0,995; 1,143] |
  | S-NPP | 2023 | 0,995 | 1,021 [0,968; 1,354] |
  | NOAA-20 | 2021 | 0,997 | 1,017 [0,967; 1,157] |
  | NOAA-20 | 2022 | 0,998 | 1,025 [0,997; 1,112] |
  | NOAA-20 | 2023 | 0,997 | 1,005 [0,934; 1,101] |

  Os produtos concordam na ordenacao e em nivel (mediana de 0,5 % a 2,5 %), com dispersao maior nas caudas. A causa
  das diferencas nao foi isolada; o composto anual remove valores atipicos das observacoes do ano inteiro e zera
  valores < 0,5 nW uma vez, enquanto o mensal o faz por mes (descricao do guia do produto), mas essa explicacao nao foi testada.

### 9.2 Setores censitarios: exposicao populacional e urbano x rural

- **Duplicidade na malha.** A malha tem 42.270 linhas para 41.700 setores: 133 setores multipoligonais aparecem em varias
  linhas, **cada uma com a populacao inteira**. Somar linhas conta duas vezes. Agrupar por `CD_SETOR` (uma populacao por
  setor, geometrias unidas, 2 poligonos invalidos reparados) reproduz **exatamente** o total do SIDRA (16.055.174) em
  todos os 92 municipios. Setores de agua tem populacao 0.
- **Populacao repartida por cobertura.** A populacao de cada setor e dividida entre os pixels que ele cobre,
  proporcionalmente a fracao de cobertura (ponderacao areal simples, sem dasimetria; a populacao se conserva: 16.055.174
  dentro da grade, 0 fora). A radiancia ponderada pela populacao de um municipio e sum(pop*L)/sum(pop) nos pixels validos.
  **Isto nao e exposicao individual**: pessoas nao se distribuem uniformemente dentro do setor.
- **Populacao fixa (2022).** Nao ha populacao anual por setor. A serie anual muda so pela radiancia.
- **Urbano x rural.** Classificacao do IBGE (campo `SITUACAO`: Urbana/Rural) no Censo 2022; media e fracao iluminada
  ponderadas pela cobertura. O criterio exato do IBGE para a classificacao **nao foi verificado nesta fase**; sabe-se
  apenas que ela nao deriva de luminosidade (nao ha circularidade). 7 municipios nao tem area rural com pixels validos e
  ficam sem o indicador rural (NaN, nunca zero).
- **Setores menores que um pixel** (~0,21 km2) compartilham pixels; o ruido de um pixel afeta varios setores.
- **Heranca do ruido do S-NPP.** Estes indicadores usam o S-NPP e herdam o piso de ruido pos-2021. Verificacao: a razao
  NOAA-20/S-NPP da radiancia ponderada pela populacao (mediana entre municipios) e 1,002 em 2019, 0,988 em 2021, 0,957 em
  2023 e 0,920 em 2025, com Spearman >= 0,997 em todos esses anos; o NOAA-20 tambem foi calculado (2018-2025) e esta em `outputs/sectors/`.
- **SIRGAS 2000 ~ WGS84** (poucos metros), como no restante do projeto.

### 9.3 Mudanca significativa por pixel

- **Metodo.** Mann-Kendall com correcao de continuidade e de empates + inclinacao de Sen, por pixel; valores-p ajustados
  por controle da taxa de falsas descobertas (Benjamini-Hochberg, 5 %) sobre os pixels testados. Pixels testados: mediana
  anual >= 0,5 nW em terra (iluminados) e >= 8 anos validos. Participacao por municipio ponderada pela cobertura.
- **Limitacoes.** BH assume independencia ou dependencia positiva; pixels vizinhos sao correlacionados e nao ha correcao
  espacial dedicada. O teste detecta tendencia monotonica, nao mudanca de nivel. "Significativo" nao implica mudanca fisica.
- **Conjunto testado (corrigido).** Só pixels do estado (malha municipal) entram no teste e no controle de falsas descobertas. **Erratum:** a primeira
  versão deste texto (PR #5) citava 13,0 % e 12,5 % (2012-2021) e 38,9 % e 5,6 % (2012-2025); essas contagens vinham de um teste feito sobre a janela retangular
  inteira, que inclui terra de estados vizinhos e mar (20.605 pixels iluminados fora do estado), e eram relatadas como se fossem do estado. Refeito só com pixels do estado.
  **Os resultados por pixel e por município não mudaram:** dentro do estado, 0 de 72.003 pixels trocam de rótulo entre os dois conjuntos de teste, e os CSV municipais têm os mesmos hashes; o que estava errado eram só os totais citados.
- **Resultado e cautela (S-NPP).** Janela 2012-2021 (72.003 pixels testados): 8.231 com aumento (11,4 %) e 10.138 com redução (14,1 %) significativos, com reduções um
  pouco mais frequentes que aumentos. Janela 2012-2025 (77.176 testados): 28.375 aumentos (36,8 %) e 4.876 reduções (6,3 %). A assimetria da segunda janela coincide com o
  piso de ruido do S-NPP pos-2021.
- **NOAA-20, janela 2018-2025 (8 anos, o minimo exigido; 73.559 testados):** 28.522 aumentos (38,8 %) e 2.205 reducoes (3,0 %). Como o NOAA-20 tem piso de ruido bem menor, **o ruido
  do S-NPP nao explica sozinho a assimetria**; sobra um aumento comum aos dois sensores que nao foi separado de um possivel artefato do algoritmo compartilhado (secao 3).
  Nada disso deve ser lido como aumento real de iluminacao. As contagens saem de `outputs/sectors/run_sectors.jsonl` e de `web/data/pixels/meta.json` (iguais).

### 9.4 Registro estruturado

Os scripts novos escrevem eventos JSON por linha (`openlux.log.JsonLogger`) em `outputs/sectors/run_sectors.jsonl`:
arquivos lidos, linhas deduplicadas, populacao dentro e fora da grade, pixels testados. Os scripts anteriores continuam
com a saida de texto e o `run_record` de proveniencia.

## 10. Interface: camada de pixel e remoção do estudo de caso

- **Motivo.** O mapa só mostrava um valor por município (coroplético), o que esconde o que o produto tem de melhor (≈ 460 m) e sofre do
  problema da unidade espacial modificável: o mesmo dado muda de aspecto conforme a divisão territorial. Além disso, a primeira tela
  era ocupada por cabeçalho e aviso, e o mapa ficava abaixo da dobra. O destaque a Niterói foi retirado: nenhum município é privilegiado.
  Validação em campo, quando existir, define seus próprios locais.
- **Camada de pixel (padrão).** Grade de **classes** por ano, desenhada no navegador, ao lado da camada por município (que continua
  disponível, com seu seletor de indicador). Detalhes em `METHODOLOGY.md` 7.2.
- **Só a classe é publicada, não o valor.** Decisão minha, conservadora: publicar o valor de cada pixel seria redistribuir o dado da NASA
  (política ESDIS, com a ressalva de enquadramento já registrada na seção 2), o que muda a decisão anterior de publicar só agregados e
  amplia o repositório e o arquivo do Zenodo. Se o autor quiser consulta por valor, é decisão explícita dele.
- **Aviso de ruído no próprio mapa.** Em anos ≥ 2022 a legenda mostra, calculado a partir das grades, quanto a classe 0,5 a < 2 cresceu
  desde 2021: no estado, de 16,4 % para 32,4 % dos pixels válidos em 2025, enquanto a classe < 0,5 cai de 67,0 % para 46,8 %. Parte disso
  é o piso de ruído do S-NPP (seção 3), não luz nova; esses números não separam as duas causas.
- **Zoom máximo 12** (um pixel de ≈ 460 m ocupa ≈ 13 px); mapa-base de terceiros só como opção desligada por padrão (seção 12).
- **Limitações.** Classes, não valores; vizinhança mais próxima na tela; herda o ruído do S-NPP; não é brilho do céu.

## 11. Interface: link permanente, busca, contexto próprio e legenda em linguagem comum

Público declarado pelo autor: pesquisador e leigo. Motivação: comparação com um mapa de brilho do céu modelado (lightpollutionmap.app, lido em 2026-11-23), que
é bem mais fácil de consultar. Esse site mostra grandeza diferente (brilho do céu **modelado**, em mag/arcsec² e Bortle, a partir de entradas anuais do VIIRS da EOG);
os números dele e os do OpenLux (radiância observada, em nW) **não são comparáveis nem conversíveis**. Não foi avaliada a acurácia do método dele.

Implementado:
1. **Link permanente.** Parâmetros `lat`, `lng`, `z`, `y` (ano), `l` (camada: `pixel` ou `mun`), `i` (indicador) e `m` (código do município). Valores inválidos são ignorados
   (nunca quebram a página); a URL é atualizada a cada mudança de vista, ano, camada, indicador ou município; botão "Copiar link desta vista".
2. **Busca de município.** Só nos nossos dados (sem serviço de geocodificação de terceiros, sem enviar a consulta do visitante a ninguém). Ignora acentos e caixa;
   não busca endereços.
3. **Legenda em linguagem comum.** Nomes simples das faixas (“sem luz detectada” a “muitíssima luz”) **ao lado** das faixas numéricas, mais um bloco “O que isto significa”.
   Os nomes são rótulos de leitura: não são classes oficiais nem equivalem à escala Bortle.
4. **Contexto geográfico próprio.** Limites municipais e **nomes dos municípios** a partir de zoom 9,5 (desligável), posicionados no centro do retângulo envolvente
   (aproximado em formas irregulares). **Sem mapa-base de terceiros por padrão (ver seção 12 para a opção):** tiles externos exigiriam relaxar a política de segurança (CSP), expõem o IP do visitante a terceiros
   e têm termos de uso que não foram verificados. Hidrografia e vias do IBGE seriam o próximo passo e exigem verificar licença e peso dos arquivos.

**Não implementado (decisão registrada): escala Bortle/SQM, contagem de estrelas visíveis e “estimativa” do mês corrente.** Todas supõem um modelo de brilho do céu que o OpenLux não
tem nem validou: a relação entre radiância orbital e brilho do céu depende de atmosfera, espectro e luz de fontes distantes (`docs/FIELD_VALIDATION.md`). Mostrar “Bortle 9,0” ou
“< 200 estrelas” passaria precisão que os dados não sustentam. O composto anual do satélite para o ano corrente também não existe, então não há o que mostrar como “estimativa” do mês.
Caminho: executar a validação em campo; só então avaliar uma relação calibrada, apresentada com incerteza.

## 12. Interface: sensor, mudança por pixel, tema escuro e mapa-base opcional

Pedido do autor: aproximar o visual de um mapa de brilho do céu modelado (lightpollutionmap.app), mantendo o rigor.

**Implementado**
- **Sensor.** A camada de pixel passa a ter Suomi NPP (2012-2025) e NOAA-20 (2018-2025). O NOAA-20 tem piso de ruído bem menor desde 2022, o que permite comparar os dois no próprio mapa.
  Ao trocar para o NOAA-20, o ano é levado a 2018 se estiver antes.
- **Mudança por pixel como camada.** Mann-Kendall + Sen + FDR 5 % (seção 9.3), com legenda que mostra o percentual de aumentos e reduções, avisa o ruído quando a janela inclui 2022-2025
  e avisa a série curta do NOAA-20. Só os códigos (1 não testado, 2 sem mudança significativa, 3 aumento, 4 redução) são publicados.
- **Tema escuro** (automático, claro ou escuro) com paleta inferno para a radiância, feita para fundo escuro; opacidade ajustável; controles reunidos num painel lateral para o mapa ocupar a primeira tela
  no computador (no celular o mapa vem logo após o aviso).
- **Mapa-base do OpenStreetMap, OPCIONAL e desligado por padrão.** Ao ligar, o navegador baixa imagens de `tile.openstreetmap.org`, cujo servidor recebe o IP do visitante; a interface avisa isso, mostra a atribuição
  e **nunca** requisita o host antes do opt-in (há teste). A política de segurança (CSP) ganhou **uma única exceção**: `img-src https://tile.openstreetmap.org`. O estado do mapa-base não vai para o link permanente,
  para que abrir um link compartilhado não dispare requisições a terceiros sem consentimento.
  Termos do OSM consultados em 2026-11-24: servidores mantidos por doações, uso pesado proibido sem permissão, sem limite numérico oficial, acesso pode ser bloqueado sem aviso, exige `Referer`
  (a política `strict-origin-when-cross-origin` o envia). Risco assumido: um site de pesquisa de tráfego modesto; se o uso crescer, trocar por tiles próprios ou de um provedor contratado.
  O CARTO foi descartado: o acesso direto exige chave de API (cadastro do autor), e uma chave no JavaScript público contraria a regra de credenciais só em variável de ambiente.

**Não implementado, de propósito**
- **Hidrografia e vias do IBGE como contexto próprio.** A base contínua BC250 é um arquivo único de ≈ 864 MB para o Brasil, na escala 1:250.000 (grosseira para zoom 10-12), e o texto de
  licença do IBGE não é legível por ferramenta. O mapa-base opcional cobre a necessidade; o IBGE fica como alternativa se o autor quiser contexto 100 % sem terceiros.
- **Suavização/"halo" estilo brilho do céu.** Interpolar as classes criaria detalhe que o dado não tem, e imitar a propagação da luz seria um modelo de brilho do céu que o projeto não tem nem validou.
  A camada continua em pixels.
- **Escala Bortle/SQM, contagem de estrelas e estimativa do mês corrente:** mantido o que está na seção 11.

**Limitações.** Com o mapa-base ligado, a classe "sem luz" fica quase transparente para mostrar o mapa por baixo; o filtro de cor que escurece o mapa-base é um efeito de exibição e não altera o dado.

## 13. Interface: painel de camadas e animação da evolução

Pedido do autor: botão para acrescentar camadas (com o OpenStreetMap desligado por padrão) e animação da evolução ano a ano, para quem quiser.

- **Painel "Camadas"** (botão dentro do mapa, no canto superior direito): camada de pixel (com opacidade), limites municipais, nomes dos municípios, mapa-base do OpenStreetMap e tema. O que vem de terceiros
  (só o OpenStreetMap) **fica desligado por padrão** e só liga por escolha do visitante, com aviso de que o servidor recebe o IP.
- **Só o OpenStreetMap como camada externa.** Outros mapas-base não foram adicionados: o CARTO exige chave de API (seção 12) e os termos de uma camada de imagem de satélite (por exemplo, a Esri) **não foram verificados**.
  Qualquer camada nova de terceiros deve entrar com termos lidos, atribuição e a mesma regra de opt-in.
- **Animação.** Botão "Animar", velocidade (rápida 0,4 s, normal 1 s, lenta 2 s) e repetição. **Nunca inicia sozinha.** Percorre, na ordem, os anos do sensor escolhido (S-NPP 2012–2025; NOAA-20 2018–2025), funciona na
  camada de pixel (radiância por ano) e nos indicadores municipais anuais, e não existe para a mudança por pixel (não tem ano). Os anos são pré-carregados antes de começar, para não piscar.
  Para ao mexer em qualquer controle (ano, camada, sensor, visão, indicador) e quando a aba fica oculta; as classes de cor são as mesmas em todos os quadros.
- **Leitura científica da animação.** O ano aparece em destaque sobre o mapa e, **para o S-NPP a partir de 2022, um aviso fixo**: o salto de 2021 para 2022 que a animação mostra é, em boa parte, o piso de ruído do S-NPP em
  áreas escuras (a classe 0,5 a < 2 passa de 16,4 % para 32,4 % dos pixels válidos do estado entre 2021 e 2025), e **não deve ser lido como luz nova**. Para a série pós-2018 é preferível animar o NOAA-20, que tem
  piso de ruído bem menor (e que ainda assim mostra aumento comum aos dois sensores, seção 9.3).
- **Não implementado:** exportar a animação como vídeo/GIF (não foi pedido); quadros lado a lado dos dois sensores.

## 14. Piloto de campo com duas pessoas e ferramentas de apoio

Decisão do autor (2026-11-24): colaboração começa como **rede piloto de poucas pessoas treinadas, sem plataforma** (formulário/CSV, revisão pelo autor); depois, expansão para o Sudeste e o Brasil.
Equipe: o autor (RJ) e no máximo uma pessoa em SP. Detalhes em `docs/FIELD_VALIDATION.md` seção 10 e no desenho `docs/superpowers/specs/2026-11-24-field-pilot-design.md`.

- **Não foi feito de propósito:** plataforma de envio, contas, fotos e moderação (custo e riscos, entre eles a LGPD, desproporcionais para duas pessoas), expansão para o Sudeste e fotometria de câmera.
- **Entregue:** validador do CSV (`openlux.field.validate_measurements`, `scripts/check_measurements.py`); contexto de satélite que informa se o disco do raio ultrapassa a borda do tile (`complete`) e recusa
  locais com contexto incompleto; calibração cruzada entre aparelhos com níveis de instrumento (`colocated_offsets`, `split_validation_readings`); gerador de locais candidatos (`candidate_sites`,
  `scripts/suggest_sites.py`); download da malha de uma UF (`scripts/fetch_mesh.py`). Tudo testado só com dados sintéticos e com um teste de fumaça com dados circulares (que prova que o código roda, não a ciência).
- **Limiares de calibração e de sanidade são propostas do projeto**, sem base em norma ou literatura, a congelar na pré-especificação.
- **Achado de viabilidade:** o tile `h13v11` já cobre o leste de SP. A radiância de contexto do NOAA-20 em 2025 a 10 km vai de ≈ 0,2 (interior da Mantiqueira e do Vale do Paraíba) a ≈ 85 (centro de SP),
  cerca de 450 vezes, suficiente para o gradiente. Pontos costeiros têm só 39 % a 61 % do raio de 50 km com pixel válido (máscara de água); para o piloto convêm locais no interior.
- **Sudeste, depois:** 4 tiles (`h12v10`, `h12v11`, `h13v10`, `h13v11`), 3 novos, ≈ 6 GB para os dois sensores (estimativa a partir de ≈ 90 MB por tile-ano). O trabalho real é generalizar os scripts, hoje fixos no RJ,
  e juntar tiles nos municípios que cruzam a divisa; a grade do Sudeste teria ≈ 9 milhões de pixels por ano (≈ 15 vezes a do RJ), exigindo tiles de classes no site.

