# Licenciamento do OpenLux: opções e consequências

**Decisão do autor (2026-11-19): MIT.** O arquivo `LICENSE` foi instalado na raiz (Copyright (c) 2026
Danilo Valim) e declarada em `CITATION.cff` (`MIT`), `.zenodo.json` (`mit`) e `pyproject.toml`. A análise
abaixo foi feita antes da decisão e foi mantida como registro. Este texto é uma análise técnica, não
aconselhamento jurídico.

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
| Black Marble (NASA) | Política ESDIS da NASA (lida no texto oficial): dados de missões lideradas pela NASA sem marcação de restrição são CC0; citação solicitada. **Confirmado com ressalva** de enquadramento | Os arquivos brutos não são redistribuídos. `web/data/` contém **agregados municipais derivados**, com citação dos conjuntos de dados |
| Malha Municipal Digital 2024 (IBGE) | Licença compatível com CC BY 4.0 (Notas Metodológicas 01/2025), com crédito e isenção de responsabilidade | `web/data/municipios.geojson` é versão simplificada; exige crédito ao IBGE |
| Censo 2022, SIDRA (IBGE) | Reuso permitido com citação da fonte (**conferido pelo autor** em 2026-11-19; texto não lido por ferramenta, pois as páginas do IBGE bloquearam o acesso automatizado) | A população por município em `web/data/` permanece, com citação do IBGE no README |
| Atlas de Falchi et al. (2016) | CC BY-NC 4.0; não usado | Nunca incluir no repositório nem no Zenodo |

Para os produtos derivados do OpenLux (tabelas e documentação), uma licença de conteúdo separada,
como CC BY 4.0, é uma opção coerente com o crédito exigido pelo IBGE; ela não substitui a licença
do código e ainda não foi decidida; os termos de NASA (CC0 com ressalva) e SIDRA (reuso com citação) não a impedem.

## 5. Pontos ainda abertos

1. Licença dos produtos derivados (agregados em `web/data/downloads/`): **CC BY 4.0, confirmada pelo autor em 2026-11-25.** O `LICENSE` MIT cobre o código.
2. Titular dos direitos: se alguma parte do trabalho foi feita com recursos ou sob regras de propriedade intelectual de uma instituição, confirme que o autor pode licenciá-la.

## 6. Efeitos da decisão MIT

- O Zenodo usa, para a licença do registro, nesta ordem, o `.zenodo.json`, o `CITATION.cff` e a licença detectada no GitHub. Como os três declaram MIT, não há conflito. O identificador do `.zenodo.json` seguiu o exemplo da ajuda do Zenodo (`mit`, minúsculas); outros repositórios usam `MIT`. **Não foi validado contra o Zenodo**: confira no formulário do rascunho.
- O teste `tests/test_docs_consistency.py` falha se a licença for declarada em um arquivo e não nos outros, e confere o texto do `LICENSE`.

## 7. Áreas urbanizadas do IBGE (2019): verificação de licença

Status: **publicada como derivados, sob CC BY 4.0, com atribuição ao IBGE.** Decisão do responsável em 2026-11-26, com base legal abaixo. A licença não foi declarada pelo IBGE para este produto específico.

| Verificação | Resultado |
|---|---|
| Produto "Áreas Urbanizadas do Brasil 2019" (`AreasUrbanizadas2019_Brasil.zip`, `geoftp.ibge.gov.br`) | Acessível. Pastas `Mapas/`, `Shapefile/` e `Tabelas/`. Nenhum arquivo de leia-me ou metadados com licença. O PDF do mapa e os arquivos `.qml` e `.xlsx` não trazem termo de licença. |
| Termo de Uso e Política de Privacidade do Portal do IBGE (versão 1, 11/03/2024) | Trata de uso do portal, dados pessoais e cookies. Não trata de licença de reuso de produtos geoespaciais. |
| Plano de Dados Abertos do IBGE (julho/2020–julho/2022) | Define "licença aberta" como a que permite utilizar, reutilizar e redistribuir, exigindo no máximo crédito de autoria e compartilhamento pela mesma licença. O produto "Áreas Urbanizadas" não aparece na lista de conjuntos a publicar. |
| dados.gov.br | Busca pelo produto: **não encontrado**. Sem licença declarada na fonte. |
| Manual GGIBPM 2.0 (IBGE, 2025) | Manual metodológico; sem termo de licença de dados. |

**Base legal adotada (confirmada pelo responsável):** Instrução Normativa nº 47, de 23/04/2025 (INDA), publicada no DOU.
- Art. 4º, III e VII: dados abertos são os acessíveis ao público, disponibilizados sob **licença aberta**, que permite utilizar, reutilizar e redistribuir, exigindo **no máximo** a atribuição de autoria ou fonte.
- Art. 3º, III e IV: os órgãos federais devem franquear ao público, em formato aberto, os dados que produzem, respeitadas a LAI e a LGPD.
- Art. 5º, II e art. 6º, IX: o IBGE, autarquia federal, integra a INDA e o seu Comitê Gestor.

**Aplicação:** a licença CC BY 4.0 cumpre o mínimo exigido pela norma. O produto é acessível ao público e não está sob sigilo. Por isso os derivados são publicados com atribuição: "IBGE, Diretoria de Geociências, Coordenação de Meio Ambiente, Áreas Urbanizadas do Brasil 2019".

**Limite:** a norma define a licença aberta, mas não declara uma licença específica para este produto. O produto também não está catalogado no dados.gov.br, o que o art. 3º, IV exige. Se o IBGE declarar outra licença, este registro deve ser revisto.

**Publicado:** `openlux_area_urbana_municipio_2019.csv` (fração urbana por município) e `openlux_areas_urbanizadas_rj_2019.geojson` (camada simplificada para mapa). Ambos gerados por `scripts/build_areas_urbanizadas_rj.py`.

**Não publicado:** os polígonos originais do Brasil inteiro (o shapefile completo). Os derivados não reproduzem o conjunto original.

## 8. Unidades de conservação (CNUC 2025-08)

- **Fonte:** Ministério do Meio Ambiente, Cadastro Nacional de Unidades de Conservação, conjunto 2025-08 (dados.mma.gov.br).
- **Licença:** Creative Commons Atribuição (CC BY 4.0), lida na página do conjunto em 2026-11-26.
- **O que é publicado:** polígonos das UCs que tocam o Rio de Janeiro, recortados pelos limites estaduais e simplificados em 0,001°. Campos: nome, código CNUC, categoria, grupo, esfera, ano de criação e situação.
- **Nomes:** o .dbf do cadastro tem codificação dupla (UTF-8 lido como Latin-1), desfeita pelo script. Os nomes foram conferidos em 2026-11-27 contra o relatório oficial do CNUC (cnuc-backend.mma.gov.br) para quatro UCs, todas idênticas, e a decodificação funciona em todos os 3.122 registros.
- **Atribuição obrigatória:** "Unidades de conservação: MMA, CNUC 2025-08, CC BY 4.0. Processamento: OpenLux (scripts/build_uc_poligonos_rj.py)."
- **Limitação:** a sobreposição com áreas urbanizadas e com a radiância é análise exploratória, não causal (ver docs/ANALISE_AMBIENTAL_EXPLORATORIA.md).

## 9. Cobertura do solo (MapBiomas Brasil, Coleção 11): estatísticas do estado

- **Fonte:** MapBiomas Brasil, Coleção 11 (30 m), tabela COVERAGE_11 do arquivo de estatísticas por estado (brasil.mapbiomas.org/downloads/estatisticas/).
- **Licença:** o site declara "Os dados do MapBiomas são de uso público, aberto e gratuito mediante referência" e exibe a marca CC BY 4.0. Verificado em 2026-11-27 na página de estatísticas e de códigos de legenda.
- **O que é publicado:** área em hectares do estado do Rio de Janeiro, por classe de nível 1 e ano (1985–2025). Não é mapa.
- **O que não é publicado:** mapas GeoTIFF. O site informa que o download de mapas está temporariamente suspenso, e a coleção do Amazonas usa outra licença (CC BY-SA), que não é usada aqui.
- **Atribuição obrigatória:** "Cobertura do solo: MapBiomas Brasil, Coleção 11, CC BY 4.0 (mediante referência)."
- **Limitação:** estatística do estado, sem detalhe municipal. Mapa municipal depende da reabertura do download no site do MapBiomas.
