# Auditoria técnico-científica do OpenLux (preparação para a versão 2.0)

Estado: **auditoria somente leitura.** Nenhum arquivo existente foi alterado. Este documento só registra
o que foi verificado, o que falta e o que depende de decisão do responsável. Data de referência: 2026-11-25.

## 1. Escopo e método

- Repositório: `DaniloSFValim/openlux`, branch de trabalho `claude/happy-goodall-c12zd5`, a partir de `main` (`0325e12`).
- Verificado por leitura de código, de metadados (`data/metadata/downloads/*.json`), de configuração
  (`pyproject.toml`, `wrangler.jsonc`, `web/_headers`) e de busca no conteúdo versionado (`git grep`).
- `data/raw/` (7,0 GB, produtos HDF5 da NASA e malhas do IBGE) existe no ambiente de trabalho, mas está
  fora do repositório (`.gitignore`), como deve ser. Não foi reprocessado nesta auditoria.
- Não foram executados: build de produção do Cloudflare, auditoria de vulnerabilidades de dependências
  (`pip-audit` não está disponível), nem testes de desempenho em rede real.

## 2. Diagnóstico (Fase 1)

Gravidade: **crítico** (afeta a validade científica ou a publicação), **alto**, **médio**, **baixo**.

| ID | Gravidade | Problema | Onde | Impacto | Correção proposta |
|---|---|---|---|---|---|
| C1 | Crítico (decidido em 2026-11-25: NOAA-20 para análise, S-NPP para o mapa padrão; ver `docs/DECISIONS.md` §15) | Sensor primário contraditório. A documentação diz que o NOAA-20 é o primário; o mapa padrão, os indicadores municipais e a página inicial usam o S-NPP (VNP46A4). | `docs/FIELD_VALIDATION.md` §2 e §7; `docs/DECISIONS.md` §7; `web/js/app.js` (`st.sensor = 'snpp'`); `web/js/inicio.js` | Leitor e revisor recebem uma leitura que contradiz a metodologia declarada. O S-NPP tem ruído maior em áreas escuras desde 2022. | **Decisão do responsável** (seção 5, item 1). Depois, alinhar código e documentação. |
| C2 | Crítico (publicação) | O build de preview do Cloudflare falhava por configuração: `npx wrangler preview` exige o bloco `previews`. | `wrangler.jsonc` | Nenhuma alteração chegava ao ar. | **Corrigido** no PR #22 (`"previews": {}`). O preview do PR #22 terminou com `success`. Falta confirmar o build de produção a partir de `main` (não tenho acesso ao log). |
| A1 | Alto | A especificação de referência descreve o VNP46A4 como "500 m". O produto e a grade do projeto são de 15 arco-segundos (≈ 460 m). | Metadados e `web/data/pixels/meta.json` (`pixel_deg` = 15″) | Nenhum erro na implementação; o erro estaria na descrição externa. | Manter a descrição atual e registrá-la no dicionário de dados. |
| A2 | Alto | Não existe `CHANGELOG.md`, exigido pela especificação. | raiz do repositório | Histórico de versões incompleto. | Criar na próxima alteração de código, com a versão 0.1.0 registrada. |
| A3 | Alto | Reprodutibilidade depende de `data/raw/`, que não é publicado. | `.gitignore`; `scripts/` | Terceiros não reproduzem os agregados sem baixar 7 GB da NASA e do IBGE. | Guia de reprodução: URLs, variável `EARTHDATA_TOKEN`, comandos e SHA-256 já registrados em `data/metadata/downloads/`. |
| A4 | Alto | Os indicadores pedidos (P75/P90/P95, área acima de limiares, percentual de área, densidade) não existem no pipeline. | `src/openlux/` | Não podem ser publicados sem reprocessar os pixels. | Reprocessar a partir de `data/raw/` depois da decisão C1 e com aprovação prévia dos novos arquivos. |
| A5 | Médio | `pop_lit` (fração da população em áreas iluminadas) fica entre 0,96 e 1,00 nos 92 municípios, até em 2021. Não discrimina. | `web/data/indicators.json` | Usar como manchete seria enganoso. | Mantida no JSON, sem uso em destaque. Documentar a saturação. |
| A6 | Médio | Páginas municipais permanentes (`/municipio/<nome>`) e relatórios PDF não existem. | — | Funcionalidade pedida, ausente. | Páginas estáticas são viáveis. PDF exige nova dependência (decisão, seção 5, item 3). |
| A7 | Médio | A gaveta de controles do mapa (branch WIP, commit `b34cca6`) não passa na suíte de navegador: um teste de animação trava e outros dependem de controles agora recolhidos. | `web/explorar.html`, `web/js/painel.js`, `tests/test_web_smoke.py` | Não há versão estável do mapa em tela cheia. | Corrigir os testes antes de qualquer merge. |
| A8 | Médio | Licença dos dados derivados (CC BY 4.0) é proposta, não confirmada. | `web/data/downloads/metadata.json` (`licenca.status`) | Risco de publicar com licença não decidida. | Decisão do responsável. |
| A9 | Médio | Bundle do Turf (`openlux-turf.min.js`, ≈ 530 KB sem compactação) é carregado em todas as visitas à página do mapa. | `web/vendor/openlux-draw/` | Desempenho em celular. | Carregar só quando o painel "Desenhe uma área" for aberto. |
| A10 | Baixo | Dependências Python sem arquivo de lock nem versões mínimas fixadas. | `pyproject.toml` | Reprodução pode variar entre ambientes. | Gerar lock file em ambiente controlado. |
| A11 | Baixo | Nenhum segredo versionado. O token da NASA é lido só de variável de ambiente. | `scripts/fetch_blackmarble.py`, `src/openlux/download.py` | — | Nenhuma ação. Registrado como verificado. |
| A12 | Baixo | Requisições externas do site: mapa-base OpenStreetMap (desligado por padrão), Leaflet, links de DOI/ORCID/NASA e o botão do WhatsApp. | `web/` | Privacidade e dependência de terceiros. | Manter; o OpenStreetMap só é contatado após opt-in. |

## 3. Auditoria científica (Fase 2)

### 3.1 Produtos utilizados (verificado nos metadados)

| Produto | Plataforma | Sensor | Resolução | Período disponível | Coleção | DOI | Uso no projeto |
|---|---|---|---|---|---|---|---|
| VNP46A4 | Suomi-NPP | VIIRS (DNB) | 15″ (≈ 460 m) | 2012–2025 (14 arquivos anuais, tile h13v11) | 002 | 10.5067/VIIRS/VNP46A4.002 | Mapa padrão, indicadores municipais, série estadual |
| VJ146A4 | NOAA-20 (JPSS-1) | VIIRS (DNB) | 15″ (≈ 460 m) | 2018–2025 (8 arquivos anuais) | 002 | 10.5067/VIIRS/VJ146A4.002 | Comparação entre sensores |
| VNP46A3 | Suomi-NPP | VIIRS (DNB) | 15″ | Mensal, 2012–2025 | 002 | 10.5067/VIIRS/VNP46A3.002 | Comparação mensal/anual (`outputs/monthly`) |
| VJ146A3 | NOAA-20 (JPSS-1) | VIIRS (DNB) | 15″ | Mensal, 2018–2025 | 002 | 10.5067/VIIRS/VJ146A3.002 | Comparação mensal/anual |

Verificações:
- Os 14 anos do VNP46A4 e os 8 anos do VJ146A4 estão presentes. O ano de 2025 tem arquivo processado em 2026, portanto está completo.
- Não há produto NOAA-21 no projeto. Não foi verificada a disponibilidade de um produto equivalente.
- A grade do projeto (15″) confere com o produto. A especificação de referência (500 m) não confere.

### 3.2 Propriedades radiométricas e de qualidade (declaradas no projeto)

- Unidade: nW·cm⁻²·sr⁻¹ (declarada em `METHODOLOGY.md` e `web/data/indicators.json`). **Não reverificada na documentação da NASA nesta auditoria.**
- Máscara: qualidade 0 (boa) e 0+1 como análise de sensibilidade; máscara terra/água do produto; valores de preenchimento e negativos excluídos (`METHODOLOGY.md`, `web/js/app.js`).
- Limitações instrumentais declaradas no projeto: banda DNB pouco sensível à emissão azul de LEDs; piso de ruído do S-NPP maior desde 2022 (`docs/DECISIONS.md` §3 e §7).

### 3.3 Homogeneidade temporal

- O projeto não concatena séries de sensores diferentes: o municipal é S-NPP 2012–2025; o NOAA-20 aparece em série separada (`outputs/sensors/`).
- A mudança do sensor, do ruído e do processamento está documentada como quebra de comparabilidade em 2022 para o S-NPP (`docs/DECISIONS.md`).
- Interferências lunares, condições atmosféricas e fontes temporárias (queimadas, obras, focos industriais) **não foram quantificadas** por este projeto. Estão listadas como limitação nos textos existentes.

### 3.4 Indicadores

| Indicador | Situação | Observação |
|---|---|---|
| Radiância média municipal | Implementado | Média ponderada por cobertura fracionária. |
| Radiância mediana municipal | Implementado | Ponderada pelos mesmos pesos. |
| Intensidade radiante aparente | Implementado | Soma ponderada pela área elipsoidal; não é emissão total. |
| Fração da área iluminada (limiar 0,5) | Implementado | Limiar documentado. |
| Luz onde as pessoas vivem (ponderada pela população) | Implementado | Censo 2022, peso por setor; não é exposição individual. |
| Fração da população em áreas iluminadas | Implementado, **saturado** | 0,96–1,00; não usar como manchete (A5). |
| Percentis P75, P90, P95 | Não implementado | Exige reprocessamento de pixels (A4). |
| Área acima de limiares | Não implementado | Exige reprocessamento (A4). |
| Densidade de radiância | Não definido | Precisa de definição matemática antes da implementação. |
| Variação temporal (absoluta e percentual) | Implementado | Entre janelas comparáveis; Δ% só com linha de base acima do piso. |
| IMLN (Índice Municipal de Luminosidade Noturna) | **Proposta futura** | Não há fundamentação matemática, normalização nem análise de sensibilidade. Não implementar. |

### 3.5 Distinções científicas

O projeto já separa radiância orbital, poluição luminosa e brilho do céu (`docs/FIELD_VALIDATION.md` §1, `METHODOLOGY.md`). Não há afirmação de impacto em fauna, flora ou saúde na interface. Verificado por busca nos textos da página.

## 4. Situação das demais fases

| Fase | Situação | Motivo |
|---|---|---|
| 3 — Interface (observatório, mapa, comparação, roteiros) | Parcial | Página inicial, roteiros, dados e sobre foram reformulados. Gaveta do mapa em WIP (A7). Comparação de até três municípios não existe ainda. |
| 4 — Metodologia e indicadores | Parcial | Seção 3 deste documento. Novos indicadores bloqueados por A4 e C1. |
| 5 — Dados abertos e licenciamento | Parcial | CSV, JSON e metadados existem. GeoJSON e GeoPackage não foram gerados. Dicionário de dados não existe. Licença CC BY 4.0 pendente (A8). |
| 6 — Análise ambiental | Não iniciado | Depende de fontes verificadas (ICMBio, INEA, CNUC) e aprovação. |
| 7 — GitHub, Zenodo, ORCID | Verificado, sem alteração | Ver seção 6. |
| 8 — Arquitetura, desempenho, segurança | Parcial | Sem segredos (A11). CSP estrita em `web/_headers`. Turf pesado (A9). Auditoria de dependências pendente. |
| 9 — Testes | Parcial | Suíte da `main` passava (220 testes, 1 pulado) antes do WIP. A suíte do branch WIP não passa (A7). |
| 10 — Documentação e entrega | Parcial | Este relatório. CHANGELOG não existe (A2). |

## 5. Decisões do responsável (bloqueantes)

1. **Sensor primário:** S-NPP (o que o site usa hoje) ou NOAA-20 (o que a documentação declara)? Isto muda o mapa padrão, a página inicial e o texto metodológico.
2. **Reprocessamento:** autorizo calcular P75/P90/P95 e área acima de limiares a partir de `data/raw/` localmente, gerando novos arquivos de dados que só serão publicados após sua revisão?
3. **PDF:** aceita uma dependência para gerar PDF, ou prefere impressão pelo navegador?
4. **Camadas ambientais:** quais fontes oficiais podem ser usadas, e com que procedência verificada?
5. **Build de produção:** confirme se o Cloudflare publica `main` sem falha. Se não, envie o trecho do log.
6. **Licença dos dados derivados:** confirma CC BY 4.0?

## 6. DOI, ORCID e licença (verificado)

- DOI da versão 0.1.0: `10.5281/zenodo.24510755`. Concept DOI: `10.5281/zenodo.24510754`. Presentes em `README.md`, `CITATION.cff` e `docs/PUBLICATION.md`. **Não foi criado novo DOI.**
- ORCID `0009-0009-7250-6151` presente em `README.md`, `CITATION.cff`, rodapé e `web/`.
- Licença do código: MIT (`LICENSE`, `pyproject.toml`). Licença dos dados derivados: CC BY 4.0, proposta (A8).
- Tag `v0.1.0`: **não existe no GitHub**. O push é recusado com HTTP 403 nesta sessão. Precisa ser criada pela interface.

## 7. Limitações deste documento

- Nada foi executado em produção nem no Cloudflare nesta auditoria.
- Números de unidades e de DOI foram verificados nos arquivos do projeto. A correspondência com as páginas da NASA não foi reverificada.
- Vulnerabilidades de dependências não foram auditadas.
