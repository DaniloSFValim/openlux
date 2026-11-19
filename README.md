# OpenLux

Software cientifico independente para **estimativa de poluicao luminosa baseada em
sensoriamento remoto** no Estado do Rio de Janeiro, a partir de dados publicos.

Autor: Danilo Valim. ORCID: *a ser informado*.

> Estado atual: **desenvolvimento inicial (Fase 2)**. Nenhum resultado cientifico
> foi produzido ou validado ainda. Este README descreve apenas o que esta implementado
> e testado.

## Implementado e testado

- Geometria da grade Black Marble (15 arc-s): transformacao afim por tile e area dos
  pixels na esfera authalica (`openlux.geo`).
- Verificacao de integridade de downloads: SHA-256 e assinatura HDF5 (`openlux.io`).
- Agregacao zonal com cobertura fracionaria de pixels: media e mediana ponderadas,
  intensidade radiante aparente, fracao valida (`openlux.zonal`).

## Estimativa, nao medicao

Os valores derivados de radiancia orbital (VIIRS Day/Night Band) **nao sao medicoes do
brilho do ceu**. Sao uma estimativa baseada em sensoriamento remoto.

## Desenvolvimento

```bash
pip install -e ".[dev]"
pytest
```

Credenciais (quando necessarias) devem ser fornecidas por variaveis de ambiente
(`EARTHDATA_TOKEN`) e nunca versionadas. Dados de terceiros nao sao redistribuidos
neste repositorio.

Licenca: **pendente de decisao do autor** (nenhum arquivo LICENSE adotado ainda).
