# Dicionário de dados — arquivos publicados em `web/data/downloads/`

Estado em 2026-11-25. Os arquivos abaixo são agregados municipais derivados de produtos da NASA e do IBGE.
Não contêm dados brutos de radiância por pixel. Os metadados completos (licença, citação, somas SHA-256) estão em
`web/data/downloads/metadata.json`.

**Atenção:** os arquivos publicados atualmente são do **S-NPP (VNP46A4), 2012–2025**. O sensor primário de análise
definido em `docs/DECISIONS.md` §15 é o **NOAA-20 (VJ146A4), 2018–2025**. Os arquivos do NOAA-20 ainda **não foram
publicados**; esta lacuna está registrada na auditoria (`docs/AUDITORIA_2_0.md`).

## 1. `openlux_municipios_snpp_serie.csv`

Uma linha por município e ano. 92 municípios × 14 anos = 1.288 linhas. Codificação UTF-8 com BOM.

| Campo | Tipo | Unidade | Definição |
|---|---|---|---|
| `cod_municipio` | texto | código IBGE (7 dígitos) | Código do município na malha IBGE 2024 |
| `municipio` | texto | — | Nome do município (malha IBGE 2024) |
| `ano` | inteiro | ano | Ano do produto anual (2012–2025) |
| `radiancia_media_nW_cm-2_sr-1` | decimal | nW·cm⁻²·sr⁻¹ | Média dos pixels válidos, ponderada pela fração de área do pixel dentro do município |
| `radiancia_mediana_nW_cm-2_sr-1` | decimal | nW·cm⁻²·sr⁻¹ | Mediana dos pixels válidos, com os mesmos pesos |
| `fracao_area_valida` | decimal, 0–1 | adimensional | Fração da área municipal com pixels válidos (excluídos mar, lagoas e valores inválidos) |
| `fracao_area_iluminada_limiar_0.5_nW_cm-2_sr-1` | decimal, 0–1 | adimensional | Fração da área válida com radiância ≥ 0,5 nW·cm⁻²·sr⁻¹ |
| `intensidade_radiante_aparente_nW_sr-1` | decimal | nW·sr⁻¹ | Soma ponderada da radiância × área elipsoidal do pixel. **Não é emissão luminosa total.** |

Valores ausentes aparecem como campo vazio. `0.0` é valor medido (mediana zero), não ausência.

## 2. `openlux_municipios_snpp_resumo.csv`

Uma linha por município. 92 linhas.

| Campo | Tipo | Unidade | Definição |
|---|---|---|---|
| `cod_municipio`, `municipio` | texto | — | Como no arquivo de série |
| `populacao_2022` | inteiro | habitantes | População residente do Censo 2022 (SIDRA, tabela 4709, variável 93). **Fixa em todos os anos.** |
| `intensidade_por_habitante_mW_sr-1_hab-1` | decimal | mW·sr⁻¹ por habitante | Intensidade radiante aparente de 2022 dividida pela população de 2022. **Índice relativo, não exposição individual.** |
| `tendencia_2012_2021_inclinacao_nW_cm-2_sr-1_por_ano` | decimal | nW·cm⁻²·sr⁻¹ por ano | Inclinação de Theil–Sen da radiância média anual, janela 2012–2021 |
| `tendencia_2012_2021_p_valor_kendall` | decimal, 0–1 | adimensional | p-valor do teste de Kendall sobre a mesma série. **Sem correção para múltiplas janelas.** |
| `tendencia_2012_2021_mudanca_pct` | decimal | % | 100 × (média(t2) − média(t1)) / média(t1). Só definido com linha de base ≥ piso declarado |
| `tendencia_2012_2025_*` | — | — | Mesmas definições para a janela 2012–2025 |

Requisito mínimo: 8 anos válidos por janela; caso contrário o campo fica vazio.

## 3. `metadata.json`

Contém: título, versão do software (0.1.0), DOI da versão (`10.5281/zenodo.24510755`), DOI do conceito
(`10.5281/zenodo.24510754`), commit do código, data de processamento, cobertura, licença (**CC BY 4.0, confirmada
pelo autor em 2026-11-25**), citação, unidades, ressalvas e somas SHA-256 dos arquivos.

## 4. Reprodução

1. Obter os produtos VNP46A4 e VJ146A4 (tile h13v11, coleção 002) pelo LAADS DAAC, com o token em `EARTHDATA_TOKEN`
   (`scripts/fetch_blackmarble.py`). Os SHA-256 de cada arquivo estão em `data/metadata/downloads/`.
2. Gerar as saídas com `scripts/run_annual.py` e `scripts/run_sectors.py`.
3. Gerar os agregados do site com `scripts/build_web_data.py` (S-NPP) ou `scripts/build_web_data_noaa20.py` (NOAA-20).
4. Gerar os arquivos de download com `scripts/build_web_downloads.py`.

Os dados brutos (`data/raw/`) não são publicados; estão no `.gitignore`.

## 5. Limitações

Ver `METHODOLOGY.md` e `docs/DECISIONS.md`. Em especial: piso de ruído do S-NPP a partir de 2022; os dois sensores
mostram comportamento comum em áreas escuras a partir de 2022, ainda não separado de um artefato do algoritmo; a
população é fixa em 2022.
