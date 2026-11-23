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
- Interface web estática (`web/`) construída apenas a partir das saídas reais do pipeline, publicada em
  https://openlux.labdados.org/ (ver `docs/DEPLOYMENT.md`).
- Documentação: `README.md`, `METHODOLOGY.md`, `docs/DECISIONS.md`, `docs/LICENSING.md`, `CITATION.cff`.
- Licença do código: MIT.

## Limitações importantes

- A série S-NPP apresenta, a partir de 2022, aumento do piso de ruído em áreas escuras; há ainda um aumento
  comum aos dois sensores que não foi separado de um possível artefato do algoritmo compartilhado. O sinal
  das tendências depende da janela de anos.
- Não implementados: comparação com o Atlas de Falchi et al. (2016), mudança espacial pixel a pixel e
  comparação urbano × não urbano.
- Os dados brutos de terceiros não são redistribuídos. `web/data/` contém agregados municipais derivados
  (NASA) e a população do Censo 2022 (IBGE/SIDRA); a citação dos dados está no `README.md`.

## Como citar

Valim, D. (2026). *OpenLux* (versão 0.1.0) [Software]. https://github.com/DaniloSFValim/openlux
(ORCID do autor: https://orcid.org/0009-0009-7250-6151). O DOI será acrescentado após a publicação no Zenodo.
