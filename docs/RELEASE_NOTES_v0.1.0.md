# OpenLux v0.1.0

Primeira versão citável do OpenLux, software científico independente para **estimativa de poluição
luminosa baseada em sensoriamento remoto** no Estado do Rio de Janeiro. Pré-lançamento: o software é
reprodutível e testado, mas os **resultados científicos não foram validados**.

## O que contém

- Pipeline em Python: leitura do NASA Black Marble (VNP46A4, S-NPP, 2012–2025; VJ146A4, NOAA-20, 2018–2025),
  máscaras de qualidade, agregação por município com cobertura fracionária de pixels (92 municípios do RJ,
  malha IBGE 2024), indicadores (radiância média e mediana, intensidade radiante aparente, fração da área
  iluminada, intensidade por habitante em 2022), tendência por janela, controles de ruído de fundo,
  análises de sensibilidade e estabilidade, proveniência e determinismo.
- Indicadores por setor censitário do Censo 2022 (IBGE): radiância ponderada pela população, população em
  áreas iluminadas e radiância média e fração iluminada urbano × rural (classificação `SITUACAO` do IBGE).
  A população é a de 2022 em todos os anos, com repartição areal simples.
- Mudança significativa por pixel (Mann–Kendall + Sen, FDR de Benjamini–Hochberg a 5 %), com participação
  de pixels com aumento e redução por município.
- Registro estruturado (JSON por linha) nos scripts de setores; comparação entre o produto anual e a média
  dos mensais (2021–2023).
- Interface web estática (`web/`) construída apenas a partir das saídas reais do pipeline, publicada em
  https://openlux.labdados.org/ (ver `docs/DEPLOYMENT.md`).
- Documentação: `README.md`, `METHODOLOGY.md`, `docs/DECISIONS.md`, `docs/LICENSING.md`, `CITATION.cff`.
- Licença do código: MIT.

## Limitações importantes

- A série S-NPP apresenta, a partir de 2022, aumento do piso de ruído em áreas escuras; há ainda um aumento
  comum aos dois sensores que não foi separado de um possível artefato do algoritmo compartilhado. O sinal
  das tendências depende da janela de anos.
- Os indicadores por setor e por pixel usam o S-NPP e herdam esse piso de ruído. Na mudança por pixel, a
  janela 2012–2021 dá 13,0 % de aumentos e 12,5 % de reduções entre os pixels testados; a janela 2012–2025 dá
  38,9 % e 5,6 %. Essa assimetria coincide com o ruído do S-NPP e **não deve ser lida como mudança real de
  iluminação**. O controle de falsas descobertas não corrige a dependência espacial.
- A população por setor é fixa (Censo 2022) e não é exposição individual; o critério de classificação
  urbano/rural do IBGE não foi verificado aqui, e o texto específico dos termos da malha de setores não foi
  lido por ferramenta (o IBGE bloqueia acesso automatizado).
- Não implementado: comparação com o Atlas de Falchi et al. (2016) (dados não obtidos; outra grandeza e outra
  época).
- Os dados brutos de terceiros não são redistribuídos. `web/data/` contém agregados municipais derivados
  (NASA) e a população do Censo 2022 (IBGE/SIDRA); a citação dos dados está no `README.md`.

## Como citar

Valim, D. (2026). *OpenLux* (versão 0.1.0) [Software]. https://github.com/DaniloSFValim/openlux
(ORCID do autor: https://orcid.org/0009-0009-7250-6151). O DOI será acrescentado após a publicação no Zenodo.
