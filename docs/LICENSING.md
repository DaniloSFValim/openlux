# Licenciamento do OpenLux: opções e consequências

**Nenhuma licença foi escolhida nem instalada.** Este documento serve para a decisão do autor.
Até lá, o repositório não tem arquivo `LICENSE`; sem licença, por padrão todos os direitos ficam
reservados e terceiros não têm permissão para reutilizar o código. Os campos `license` de
`CITATION.cff` e `.zenodo.json` estão omitidos de propósito e devem ser preenchidos junto com a
decisão. Este texto é uma análise técnica, não aconselhamento jurídico.

## 1. As três opções consideradas

| Aspecto | MIT | Apache-2.0 | GPL-3.0 |
|---|---|---|---|
| Tipo | Permissiva | Permissiva | Copyleft forte |
| Pode ser reutilizada em software proprietário? | Sim | Sim | Não: obras derivadas distribuídas devem ser publicadas sob GPL-3.0 |
| Obrigações ao redistribuir | Manter o aviso de copyright e o texto da licença | Idem, mais manter o arquivo `NOTICE` e indicar alterações | Código-fonte correspondente sob GPL-3.0, avisos e indicação de alterações |
| Concessão explícita de patentes | Não | Sim (com rescisão em caso de litígio) | Sim |
| Tamanho e simplicidade | Muito curta | Média | Longa |
| Compatibilidade | Compatível com GPL-3.0 e Apache-2.0 (pode ser incorporada a eles) | Compatível com GPL-3.0 (não com GPL-2.0-only) | Só pode ser combinada com código sob termos compatíveis |
| Efeito sobre a citação | Nenhum: a citação vem de `CITATION.cff` e do DOI, não da licença | Idem | Idem |

Consequências práticas:

- **MIT**: máxima facilidade de reuso por pesquisadores e instituições, sem exigir que
  trabalhos derivados sejam abertos. Não protege contra apropriação proprietária.
- **Apache-2.0**: igual à MIT no reuso, com proteção contratual de patentes e a obrigação de
  `NOTICE`. A proteção de patentes tem pouco peso para um software de análise espacial como este.
- **GPL-3.0**: garante que versões modificadas e distribuídas permaneçam abertas, ao custo de
  desencorajar o uso em projetos que combinam o código com componentes proprietários ou com
  licenças incompatíveis. Não impede o uso interno e a execução do software em pesquisa.

## 2. Recomendação (a decidir pelo autor)

**MIT**, pela simplicidade, pela compatibilidade com todas as dependências e pelo reuso mais
amplo; escolha **Apache-2.0** se quiser a cláusula explícita de patentes, e **GPL-3.0** se o
objetivo for garantir que derivados distribuídos permaneçam abertos. Qualquer das três atende a
publicação no GitHub e no Zenodo.

## 3. Compatibilidade com as dependências

Licenças verificadas nos metadados dos pacotes instalados:

| Pacote | Licença declarada |
|---|---|
| numpy, h5py, rasterio, geopandas, shapely, pandas, scipy | BSD (3 cláusulas) |
| pyproj, pytest | MIT |
| exactextract | Apache-2.0 |
| playwright (só testes opcionais) | Apache-2.0 |
| Leaflet 1.9.4 (copiado em `web/vendor/leaflet/`, com seu `LICENSE`) | BSD-2-Clause |

Todas são permissivas e compatíveis com as três opções. Se o autor escolher GPL-3.0, a
combinação com componentes Apache-2.0 é permitida pela GPL-3.0.

## 4. Código versus dados de terceiros

A licença do código **não** se estende aos dados. Os dados têm termos próprios:

| Dado | Termos | Consequência |
|---|---|---|
| Black Marble (NASA) | Política de dados abertos da NASA/LAADS; texto oficial **não confirmado** nesta pesquisa | Os arquivos brutos não são redistribuídos. `web/data/` contém **agregados municipais derivados**; a redistribuição deles depende dessa confirmação |
| Malha Municipal Digital 2024 (IBGE) | Licença compatível com CC BY 4.0 (Notas Metodológicas 01/2025), com crédito e isenção de responsabilidade | `web/data/municipios.geojson` é versão simplificada; exige crédito ao IBGE |
| Censo 2022, SIDRA (IBGE) | **Não verificado** | A população por município em `web/data/` depende dessa verificação |
| Atlas de Falchi et al. (2016) | CC BY-NC 4.0; não usado | Nunca incluir no repositório nem no Zenodo |

Para os produtos derivados do OpenLux (tabelas e documentação), uma licença de conteúdo separada,
como CC BY 4.0, é uma opção coerente com o crédito exigido pelo IBGE; ela não substitui a licença
do código e deve ser decidida com a confirmação dos termos de NASA e SIDRA.

## 5. Pontos que só o autor pode confirmar

1. Qual licença do código (e, se desejado, qual licença de conteúdo para a documentação e os produtos derivados).
2. Titular dos direitos autorais: o texto de uma licença permissiva usa nome e ano (por exemplo, "Danilo Valim, 2026").
   Se alguma parte do trabalho foi feita com recursos ou sob regras de propriedade intelectual de uma instituição, confirme que o autor pode licenciá-la.
3. Se os agregados de `web/data/` podem permanecer no repositório antes da confirmação dos termos de NASA e SIDRA.

## 6. O que muda quando a licença for escolhida

- Adicionar o `LICENSE` na raiz com o texto oficial da licença.
- Preencher `license` em `CITATION.cff` (identificador SPDX) e em `.zenodo.json` (identificador aceito pelo Zenodo; confirmar no formulário).
- Declarar a licença em `pyproject.toml` e no README (seção 1).
- O teste `tests/test_docs_consistency.py` falha se a licença for declarada em um arquivo e não nos outros.
