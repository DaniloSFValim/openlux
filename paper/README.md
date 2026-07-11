# 📄 Artigo científico — materiais

Rascunho de artigo sobre o sistema e o método de índices fotométricos de instalação,
com os dados reais do parque e figuras reprodutíveis.

## Conteúdo

| Arquivo | Descrição |
|---|---|
| [`artigo_pt.md`](artigo_pt.md) | Manuscrito em **português** (IMRaD) |
| [`paper_en.md`](paper_en.md) | Manuscrito em **inglês** (IMRaD) |
| [`references.bib`](references.bib) | Referências (BibTeX) |
| [`data/parque_stats_2026-07-11.csv`](data/parque_stats_2026-07-11.csv) | Estatísticas reais usadas (consulta em produção) |
| [`figures/gen_figures.py`](figures/gen_figures.py) | Gera as figuras SVG a partir dos dados |
| `figures/fig1..4_*.svg` | Figuras vetoriais do artigo |

## Regenerar as figuras

```bash
python3 paper/figures/gen_figures.py
```

Sem dependências externas — emite SVG diretamente. A paleta é CVD-safe (Okabe–Ito).

## Método (referência canônica)

O modelo de índices (η, P, L), premissas, tabela de refletâncias e enquadramento
normativo estão detalhados em
[`../docs/FIELD_REFERENCE_TIER3_PHOTOMETRY.md`](../docs/FIELD_REFERENCE_TIER3_PHOTOMETRY.md).

## Veículos-alvo

- **PT:** CBEE (Congresso Brasileiro de Eficiência Energética), ENCAC,
  *Ambiente Construído* (ANTAC).
- **EN:** *Sustainable Cities and Society*, *LEUKOS*, *Lighting Research & Technology*
  (estes últimos requerem a validação radiométrica da Fase 3).
- **Preprint:** SciELO Preprints ou OSF, para registrar prioridade rapidamente.

## Propriedade intelectual e citação

Ver [`../docs/INTELLECTUAL_PROPERTY.md`](../docs/INTELLECTUAL_PROPERTY.md)
(DOI Zenodo, registro INPI, tag/release, como citar).

> **Nota:** os números do parque refletem a consulta de 2026-07-11 e podem mudar com
> a operação. A classificação fotométrica (ângulo/material) está em coleta inicial;
> as figuras do modelo (Fig. 3) são teóricas até haver amostra empírica suficiente.
