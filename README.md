# OpenLux

Software cientifico independente para **estimativa de poluicao luminosa baseada em
sensoriamento remoto** no Estado do Rio de Janeiro, a partir de dados publicos.

Autor: Danilo Valim. ORCID: *a ser informado*.

> Estado atual: **desenvolvimento inicial (Fase 2)**. Nenhum resultado cientifico
> foi produzido ou validado ainda. Este README descreve apenas o que esta implementado
> e testado.

## Implementado e testado

- Geometria da grade Black Marble (15 arc-s): transformacao afim por tile e area dos
  pixels no elipsoide WGS84 (formula exata; `openlux.geo`).
- Verificacao de integridade de downloads: SHA-256 e assinatura HDF5 (`openlux.io`).
- Leitor do produto Black Marble com mascaras de qualidade, contagem de observacoes e
  terra/agua (`openlux.io.read_blackmarble`). Testado em dados reais do VNP46A4 (S-NPP) e do
  VJ146A4 (NOAA-20); o VNP46A3 (mensal) **nao foi testado**.
- Agregacao zonal com cobertura fracionaria de pixels: media e mediana ponderadas,
  intensidade radiante aparente, fracao valida (`openlux.zonal`).
- Downloader verificado da LAADS (SHA-256, assinatura HDF5, tentativas com recuo) e
  registro de proveniencia (`openlux.download`, `openlux.provenance`).
- Populacao do Censo 2022 (SIDRA 4709/v93) e malha municipal IBGE 2024 (`openlux.ibge`).
- Indicadores temporais por municipio: tendencia (Theil-Sen + Kendall) em janelas separadas,
  variacao com piso declarado, controles de ruido de fundo e comparacao S-NPP x NOAA-20
  (`openlux.temporal`, `openlux.qa`, `openlux.pipeline`). Decisoes e achados: `docs/DECISIONS.md`.

- Interface web estatica (`web/`): mapa coropletico dos 92 municipios, indicadores, ranking,
  comparacao, painel estadual com controles de ruido de fundo, metodologia, fontes e
  limitacoes. Classes fixas entre anos, legenda com unidade, fonte e periodo, aviso
  metodologico permanente. Testada em navegador (Playwright).

## Resultados

Nenhum resultado cientifico validado esta disponivel ainda. O pipeline ja executa sobre a
serie VNP46A4 2012-2025, mas os produtos gerados nao foram validados nem interpretados.

## Estimativa, nao medicao

Os valores derivados de radiancia orbital (VIIRS Day/Night Band) **nao sao medicoes do
brilho do ceu**. Sao uma estimativa baseada em sensoriamento remoto.

## Desenvolvimento

```bash
pip install -e ".[dev]"
pytest
export EARTHDATA_TOKEN=...            # nunca versione o token
python scripts/fetch_blackmarble.py --years 2012-2025
python scripts/fetch_ibge.py
python scripts/run_annual.py          # saidas em outputs/annual/
python scripts/build_web_data.py      # gera web/data/ a partir das saidas reais
python -m http.server -d web 8000     # interface em http://localhost:8000
```

Credenciais (quando necessarias) devem ser fornecidas por variaveis de ambiente
(`EARTHDATA_TOKEN`) e nunca versionadas. Dados de terceiros nao sao redistribuidos
neste repositorio.

Licenca: **pendente de decisao do autor** (nenhum arquivo LICENSE adotado ainda).
