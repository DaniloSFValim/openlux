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
  https://openlux.labdados.org/ (ver `docs/DEPLOYMENT.md`). Camada de radiância **por pixel** (≈ 460 m, 6 classes fixas, iguais em
  todos os anos) e camada por município; link permanente (URL com vista, ano, camada, indicador e município), busca de município,
  nomes dos municípios e legenda em linguagem comum. A interface publica só a **classe** de cada pixel, não o valor da radiância.
  Nenhum município é tratado como estudo de caso. Seletor de sensor (Suomi NPP 2012–2025 e NOAA-20 2018–2025), camada de **mudança por pixel**, tema claro/escuro e opacidade ajustável. Botão **Camadas** dentro do mapa e **animação** ano a ano, que só roda a pedido, mostra o ano e avisa o ruído do S-NPP desde 2022. O mapa-base do OpenStreetMap é **opcional e vem desligado**: só ao ligá-lo o navegador contata o servidor deles (que recebe o IP do visitante).
- **Validação em campo (preparada, sem medições):** protocolo **proposto** com SQM (`docs/FIELD_VALIDATION.md`), pré-especificação em rascunho
  (`docs/field/preregistration.json`) e código de análise (`openlux.field`), para um piloto de **duas pessoas** (RJ e leste de SP) sem plataforma de envio. Inclui conferência do
  CSV de medições (`scripts/check_measurements.py`), proteção contra contexto de satélite cortado na borda do tile, **calibração cruzada** entre aparelhos com níveis de instrumento
  (o SQM do autor é a referência; celular e câmera sem calibração ficam sempre como dado exploratório) e sugestão de locais candidatos estratificados pela radiância de satélite
  (`scripts/suggest_sites.py`, com a malha municipal de SP). Tudo testado só com dados sintéticos. **Nenhuma medição foi feita.**
- Documentação: `README.md`, `METHODOLOGY.md`, `docs/DECISIONS.md`, `docs/LICENSING.md`, `CITATION.cff`.
- Licença do código: MIT.

## Limitações importantes

- A série S-NPP apresenta, a partir de 2022, aumento do piso de ruído em áreas escuras; há ainda um aumento
  comum aos dois sensores que não foi separado de um possível artefato do algoritmo compartilhado. O sinal
  das tendências depende da janela de anos.
- Os indicadores por setor e por pixel usam o S-NPP e herdam esse piso de ruído. Na mudança por pixel, a
  janela S-NPP 2012–2021 dá 11,4 % de aumentos e 14,1 % de reduções entre os pixels do estado testados; a janela 2012–2025 dá
  36,8 % e 6,3 %; e o NOAA-20 (2018–2025, 8 anos) dá 38,8 % e 3,0 %. Essa assimetria coincide com o ruído do S-NPP, mas o NOAA-20 também a mostra, então a causa não foi separada e **não deve ser lida como mudança real de
  iluminação**. O controle de falsas descobertas não corrige a dependência espacial.
- A população por setor é fixa (Censo 2022) e não é exposição individual; o critério de classificação
  urbano/rural do IBGE não foi verificado aqui, e o texto específico dos termos da malha de setores não foi
  lido por ferramenta (o IBGE bloqueia acesso automatizado).
- A camada de pixel mostra a classe, não o valor, e herda o piso de ruído do S-NPP: a classe 0,5 a < 2 passa de 16,4 % dos pixels
  válidos do estado em 2021 para 32,4 % em 2025, e parte disso pode ser ruído, não luz nova. A interface avisa nos anos ≥ 2022.
- Os nomes simples das faixas (“sem luz detectada” a “muitíssima luz”) são rótulos de leitura, sem equivalência com a escala Bortle.
  **Não há** escala Bortle/SQM, contagem de estrelas nem previsão de brilho do céu: isso exige um modelo validado em campo
  (`docs/DECISIONS.md`, seção 11).
- Os nomes dos municípios no mapa ficam no centro do retângulo envolvente (aproximado em formas irregulares) e podem se sobrepor.
- Não implementado: comparação com o Atlas de Falchi et al. (2016) (dados não obtidos; outra grandeza e outra
  época) e validação em campo (protocolo e ferramentas escritos, sem medições). Os limiares de calibração e de sanidade do piloto são **propostas do projeto**,
  sem base em norma ou literatura, e a pré-especificação ainda não foi congelada; o instrumento da segunda pessoa não está definido. Expansão para o Sudeste e o Brasil: não feita (`docs/DECISIONS.md`, seção 14).
- Os dados brutos de terceiros não são redistribuídos. `web/data/` contém agregados municipais derivados
  (NASA), a população do Censo 2022 (IBGE/SIDRA) e grades de **classes** por pixel (só o código da classe, nunca o valor da radiância); a citação dos dados está no `README.md`.

## Como citar

Valim, D. (2026). *OpenLux* (versão 0.1.0) [Software]. https://github.com/DaniloSFValim/openlux
(ORCID do autor: https://orcid.org/0009-0009-7250-6151). O DOI será acrescentado após a publicação no Zenodo.
