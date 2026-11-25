# OpenLux 2.0 — plano mestre de desenvolvimento

Arquivo central de acompanhamento. Atualizar a cada fase concluída. Antes de cada sessão, ler este
arquivo, `CHANGELOG.md` e `docs/DECISIONS.md` e continuar a partir da última tarefa concluída.

Data de referência deste diagnóstico: 2026-11-25. Branch de trabalho: `claude/happy-goodall-c12zd5`,
sincronizada com `main` em `9e8f11b` (PR #26 mergeado).

## 1. Objetivo

Transformar o OpenLux em um observatório científico de luminosidade noturna do Estado do Rio de
Janeiro (92 municípios, 2012–2025): dados reproduzíveis, metodologia transparente, interface
profissional e publicação acadêmica. Não é uma plataforma genérica de geoprocessamento.

Identificadores preservados (não alterar): DOI da versão 0.1.0 `10.5281/zenodo.24510755`; concept DOI
`10.5281/zenodo.24510754`; ORCID `0009-0009-7250-6151`.

## 2. Arquitetura atual (verificada no repositório)

| Área | Situação | Onde |
|---|---|---|
| Núcleo científico (Python) | Módulos de leitura HDF5, grade, máscaras, agregação zonal, tendência, qualidade, setores, proveniência | `src/openlux/` (18 módulos) |
| Scripts de aquisição e processamento | Download Black Marble, IBGE, setores; execução anual, setores, validação, geração da web | `scripts/` (18 scripts) |
| Dados brutos | 7,0 GB em `data/raw/` (VNP46A4, VJ146A4, VNP46A3, VJ146A3, IBGE). **Fora do git** (`.gitignore`) | local |
| Saídas intermediárias | `outputs/` (2,1 MB): anual, setores, sensores, mensal, validação. **Fora do git**, exceto `.gitkeep` | local |
| Metadados de proveniência | URL, tamanho e SHA-256 das entradas | `data/metadata/downloads/*.json` (versionado) |
| Dados publicados | Indicadores JSON, GeoJSON municipal, pixels por ano (classes 2–7), downloads CSV | `web/data/` (versionado, 16 MB) |
| Interface | HTML/CSS/JS estático, Leaflet 1.9.4 local, gráficos SVG próprios | `web/` |
| Publicação | Cloudflare Workers Static Assets, `assets.directory = ./web`, CSP e cabeçalhos em `web/_headers` | `wrangler.jsonc` |
| Testes | 27 arquivos; navegador via Playwright (Chromium do sistema) | `tests/` |
| Documentação | README, METHODOLOGY (546 linhas), DECISIONS (373), AUDITORIA_2_0, CHANGELOG, DICIONARIO_DE_DADOS, LICENSING, DEPLOYMENT, FIELD_VALIDATION, PUBLICATION, REFERENCES | raiz e `docs/` |

Seis áreas pedidas pela especificação (Observatório, Explorador, Laboratório, Ambiental, Dados
abertos, Ciência e metodologia). Situação atual:

| Área pedida | Situação |
|---|---|
| Observatório (página inicial) | Parcial: `index.html` com ranking e gráfico do NOAA-20 |
| Explorador geográfico | Parcial: `explorar.html` com camadas, sensor, animação, cartão e desenho de área |
| Laboratório de análises | Não existe |
| Observatório ambiental | Não iniciado (depende de fontes verificadas) |
| Dados abertos | Parcial: `dados.html` com CSV e metadados; sem GeoJSON, GeoPackage nem hashes na página |
| Ciência e metodologia | Parcial: `sobre.html`, `METHODOLOGY.md`, `DECISIONS.md` |

Navegação atual: Início, Explorar o mapa, Roteiros, Baixar dados, Sobre e métodos. **Diverge** da
estrutura de seis áreas da especificação (ver conflitos, seção 5).

## 3. Decisões técnicas vigentes

Fonte de verdade: `docs/DECISIONS.md`. Resumo das que governam o 2.0:

- **Sensor primário para análise:** NOAA-20 (VJ146A4), decisão do responsável em 2026-11-25 (DECISIONS §15).
- **Sensor de continuidade:** S-NPP (VNP46A4), 2012–2025. Mantido, com aviso de ruído a partir de 2022.
- **Mapa padrão:** NOAA-20, desde a sessão de 2026-11-25 (pedido do responsável). **Conflita com DECISIONS §15**, ver seção 5.
- **Camada municipal:** NOAA-20 por padrão (2018–2025); S-NPP por `?s=snpp`. Trocar de sensor recarrega a página.
- **Agregação:** cobertura fracionária por pixel (exactextract), sem reamostragem.
- **Área dos pixels:** elipsoide WGS84, fórmula exata.
- **Indicadores:** intensidade radiante aparente (nW·sr⁻¹), não emissão total; intensidade por habitante só em 2022.
- **Tendência:** Theil–Sen e Kendall, mínimo de 8 anos válidos, janelas declaradas.
- **Não implementado por decisão:** IMLN (proposta futura, sem fundamentação suficiente).

## 4. Fases

Estados: NÃO INICIADO · EM ANDAMENTO · CONCLUÍDO · BLOQUEADO · VALIDAR CIENTIFICAMENTE.

### Fase A — Diagnóstico consolidado

| Tarefa | Estado | Evidência |
|---|---|---|
| Ler README, METHODOLOGY, DECISIONS, AUDITORIA_2_0, CHANGELOG | CONCLUÍDO | Leitura integral do README e da auditoria; METHODOLOGY e DECISIONS lidos por seção |
| Ler CITATION.cff e .zenodo.json | CONCLUÍDO | Existem; ORCID e DOIs conferidos (seção 6) |
| Examinar pyproject.toml e wrangler.jsonc | CONCLUÍDO | `version = 0.1.0`; dependências sem versão mínima; `previews: {}` |
| Inspecionar módulos Python e scripts | CONCLUÍDO (estrutural) | Lista em seção 2; funções específicas não reauditadas nesta fase |
| Examinar dados publicados e metadados | CONCLUÍDO | 92 feições em `municipios.geojson`, `CD_MUN` único; CRS não declarado (padrão RFC 7946, WGS84) |
| Examinar interface web | CONCLUÍDO (estrutural) | 5 páginas, 9 módulos JS, `_headers` com CSP estrita |
| Examinar testes e rodar a suíte | CONCLUÍDO | `pytest tests`: 226 passam, 1 pulado (teste contra o site remoto, exige `OPENLUX_URL`) |
| Histórico e branches | CONCLUÍDO | `main` = `9e8f11b`; branch de trabalho sincronizada; PRs #1–#26 |
| Verificar produtos VIIRS na documentação da NASA | **EM ANDAMENTO / parcial** | Ver seção 5.2 |
| Classificar arquivos (preservar / corrigir / descartar) | CONCLUÍDO | Seção 6 |
| Criar este plano | CONCLUÍDO | Este arquivo |

### Fase B — Saneamento

| Tarefa | Estado |
|---|---|
| Remover `web/data/downloads/revisao_noaa20/` da pasta pública (P1) | CONCLUÍDO. Movido para `data/revisao/noaa20/` com `git mv`. Teste de guarda em `tests/test_web_noaa20.py` |
| Atualizar `docs/DECISIONS.md` §15 com addendum (K1) | CONCLUÍDO. Addendum §15.1 |
| Atualizar `docs/AUDITORIA_2_0.md`: A2 e A7 (K2, K3) | CONCLUÍDO |
| Verificar o build de produção a partir de `main` (P2) | BLOQUEADO. Sem acesso ao log do Cloudflare nesta sessão; pendência 3 do responsável |
| Gerar lock file de dependências Python (P5) | CONCLUÍDO. `requirements-lock.txt` (104 pacotes, ambiente de referência, Python 3.13.18) |
| Fixar versões mínimas em `pyproject.toml` (P5) | CONCLUÍDO. Mínimos = versões aprovadas na suíte |

### Fase C — Núcleo científico

| Tarefa | Estado |
|---|---|
| Confirmar unidades, máscaras e camadas do VJ146A4 e VNP46A4 no guia oficial | BLOQUEADO (guia em PDF retornou 403 ao acesso automatizado) |
| Verificar a nota da NASA sobre v1.0 do S-NPP (alerta 171686) | BLOQUEADO (a página do alerta não abriu; o índice mostra o título, sem escopo) |
| Investigar a degradação do DNB do S-NPP descrita nas notas da v2.0 | VALIDAR CIENTIFICAMENTE |
| Verificar se os valores VIIRS podem exceder 6553,5 nW·cm⁻²·sr⁻¹ (mudança para ponto flutuante na v2.0) e se o pipeline trata isso | NÃO INICIADO |
| Confirmar SIRGAS 2000 como referência e medir a diferença para WGS84 (hoje é premissa, DECISIONS §1) | NÃO INICIADO |
| Revisar agregação municipal (interseção de pixels com a malha) | NÃO INICIADO (há testes de agregação; revisão ainda não feita nesta fase) |
| Reprodutibilidade: executar o pipeline a partir de `data/raw/` e comparar hashes do Apêndice C | NÃO INICIADO |
| Percentis P75/P90/P95 e área acima de limiares | BLOQUEADO (exige aprovação prévia dos novos arquivos, pedido ao responsável) |

### Fase D — Nova interface

| Tarefa | Estado |
|---|---|
| Identidade visual (tema escuro, dourado, base do protótipo) | EM ANDAMENTO. Aplicada ao Observatório (`web/css/observatorio.css`) |
| Observatório (página inicial): KPIs estaduais, evolução NOAA-20 com S-NPP tracejado, mapa de 92 municípios com classes fixas, maiores e menores, distribuição, variação 2018→2025, busca | CONCLUÍDO (primeira versão). Testes: `tests/test_web_observatorio.py`. Capturas reais em `docs/screenshots/openlux-2.0/` |
| Explorador geográfico: navegação alinhada às seis áreas | CONCLUÍDO (só navegação). |
| Explorador geográfico: identidade visual do protótipo (tema escuro) | NÃO INICIADO. Exige trabalho de tema, porque os testes de navegador cobrem o tema claro e escuro |
| Lente de comparação entre dois anos (9.6), municipal: `web/comparar.html` | CONCLUÍDO (versão municipal). Lado a lado, controle deslizante, mapa de diferença absoluta, variação percentual com piso e URL. Testes: `tests/test_web_comparar.py`. **Pendente:** versão por pixel, que exige comparar os arquivos de pixels |
| Laboratório de análises | NÃO INICIADO |
| Observatório ambiental | NÃO INICIADO |
| Dados abertos (renovação) | NÃO INICIADO |
| Metodologia (renovação) | NÃO INICIADO |

### Fase E — Recursos avançados

Comparação temporal, comparação municipal (até três), relatórios PDF, URLs compartilháveis (parcial:
parâmetros existem), camadas GIS, galeria de screenshots: todos NÃO INICIADOS, exceto URLs parciais.

### Fase F — Qualidade e publicação

Testes automatizados existem (226). GitHub Actions: NÃO INICIADO (não há `.github/workflows`).
Proteção de branch: NÃO INICIADO (requer administrador). Screenshots reais: NÃO INICIADO.
Zenodo e nova versão: pendentes de decisão e de publicação manual pelo responsável.

## 5. Conflitos entre documentação e código, e problemas

### 5.1 Conflitos

| ID | Conflito | Verificação | Ação |
|---|---|---|---|
| K1 | DECISIONS §15 diz "S-NPP continua sendo o mapa padrão". O código e o CHANGELOG mostram NOAA-20 como padrão desde 2026-11-25. | `web/js/app.js` (`sk0` padrão `noaa20`), `web/explorar.html` | Fase B: addendum em §15 registrando a decisão do responsável |
| K2 | AUDITORIA A2 diz que não existe CHANGELOG. O arquivo existe. | `git ls-files CHANGELOG.md` | Fase B: atualizar a auditoria |
| K3 | AUDITORIA A7 diz que a gaveta do mapa não passa na suíte. Hoje a suíte passa (226). | pytest | Fase B: atualizar a auditoria |
| K4 | AUDITORIA §5 item 1 pede alinhar código e documentação após a decisão C1. K1 é o que falta disso. | — | Fase B (igual a K1) |
| K5 | Especificação de referência descrevia o VNP46A4 como 500 m. O produto e a grade são 15″ (≈ 460 m). | `web/data/pixels/meta.json` | Registrar no dicionário de dados (já listado na auditoria A1) |

### 5.2 Verificação na documentação da NASA

Fontes lidas por busca e pelo agente de leitura web (2026-11-25):

| Afirmação | Situação | Fonte |
|---|---|---|
| Produto VJ146A4: NOAA-20, anual, 15″, Linear Lat Lon Grid, Global | **Confirmado** | https://ladsweb.modaps.eosdis.nasa.gov/missions-and-measurements/products/VJ146A4 |
| Produto VNP46A4: Suomi-NPP, anual, 15″ | **Confirmado** | https://ladsweb.modaps.eosdis.nasa.gov/missions-and-measurements/products/VNP46A4 |
| Início da série: VJ146A4 em 2018-01-01; VNP46A4 em 2012-01-01 | **Confirmado** (fim da série não encontrado) | mesmas páginas |
| Versão 2.0 (DOI .002) usada pelo projeto | **Confirmado** nas páginas dos produtos | mesmas páginas; "NPP and JPSS1 VIIRS data 2.0 (ArchiveSet 5200)" |
| Ponto flutuante na v2.0; valores podem exceder 6553,5 nW·cm⁻²·sr⁻¹ | **Confirmado** (nota de mudanças) | páginas dos produtos |
| Degradação do DNB do S-NPP após o lançamento; NOAA-20 estável; correção espectral aplicada ao S-NPP na v2.0 | **Confirmado** como declaração da NASA; método e coeficientes **não encontrados** | página do VNP46A4, item 4 de mudanças |
| Unidade nW·cm⁻²·sr⁻¹ | **Não confirmado** em documento oficial. Só aparece em pôster da NASA | pendente do guia PDF |
| Nomes de camadas (`AllAngle_Composite_Snow_Free`), códigos de máscara de terra/água, códigos de qualidade do produto anual | **Não confirmados** | o guia PDF (Collection 2.0) retornou 403 |
| Alerta 171686 (produção do S-NPP v1.0 encerrada em 31/01/2025) se aplica à v2.0? | **Não resolvido**. A página do alerta não abriu; o índice mostra títulos de alertas v2.0 em 2025 | https://ladsweb.modaps.eosdis.nasa.gov/alerts-and-issues/171686 |

Consequência: as unidades, as máscaras e as camadas usadas pelo pipeline **não podem ser declaradas
confirmadas pela documentação oficial** até que o guia seja lido. Isto é um bloqueio de Fase C, não de
Fase A. Solução: o responsável baixa o PDF `BlackMarbleUserGuide_Collection2.0.pdf` e o envia, ou
abre o guia no navegador e confirma as três informações.

### 5.3 Problemas identificados (Fase A)

| ID | Gravidade | Problema | Onde |
|---|---|---|---|
| P1 | Alto | Pasta pública `web/` contém arquivos de revisão (`revisao_noaa20/`). Viola a Fase 8 e a Regra 9. | `web/data/downloads/revisao_noaa20/` |
| P2 | Alto | Build de produção não verificado. Uma sonda de `openlux.labdados.org` logo após o merge não encontrou `indicators_noaa20.json` (404). Pode ser atraso de deploy ou deploy não disparado por `main`. | Cloudflare |
| P3 | Alto | Unidades, máscaras e camadas não confirmadas na documentação oficial (seção 5.2). | pipeline e metodologia |
| P4 | Médio | Dependência de dados brutos de 7 GB fora do repositório, sem guia de reprodução executável. | `data/raw/`, `outputs/` |
| P5 | Médio | Sem lock file; `pyproject.toml` sem versões mínimas. | `pyproject.toml` |
| P6 | Médio | Sem GitHub Actions e sem proteção de branch. | `.github/` |
| P7 | Médio | Estrutura de navegação diverge das seis áreas da especificação. | `web/*.html` |
| P8 | Médio | Laboratório de análises, observatório ambiental e páginas municipais inexistentes. | — |
| P9 | Médio | A camada de pixels e a municipal estão no NOAA-20 por padrão; a documentação diz o contrário (K1). | docs |
| P10 | Baixo | Indicador `pop_lit` saturado (0,96–1,00). | `web/data/indicators.json` |
| P11 | Baixo | Bundle do Turf (≈ 530 KB) carregado em todas as visitas ao mapa. | `web/vendor/openlux-draw/` |

## 6. Classificação de arquivos

| Categoria | Arquivos | Tratamento |
|---|---|---|
| Preservar sem alteração | `LICENSE`, `CITATION.cff`, `.zenodo.json`, `docs/references.json`, `data/metadata/downloads/*.json`, `docs/RELEASE_NOTES_v0.1.0.md`, `docs/PHASE*_*.md` | histórico e proveniência |
| Preservar com atualização | `README.md`, `CHANGELOG.md`, `docs/DECISIONS.md`, `docs/AUDITORIA_2_0.md`, `METHODOLOGY.md`, `docs/DICIONARIO_DE_DADOS.md` | atualizar conforme K1–K5 e as fases seguintes |
| Mover para fora da pasta pública | `web/data/downloads/revisao_noaa20/` | P1 |
| Dados publicados (aprovados) | `web/data/indicators.json`, `web/data/indicators_noaa20.json`, `web/data/municipios.geojson`, `web/data/pixels/` | manter; validar cientificamente antes de tratar como definitivos (ver Fase C) |
| Dados internos (não publicados) | `data/raw/`, `outputs/` | manter fora do git |
| Scripts científicos | `scripts/*.py`, `src/openlux/*.py` | preservar; revisar na Fase C; nada descartado |
| Testes | `tests/*.py` | preservar; ampliar na Fase C e F |
| Configuração de publicação | `wrangler.jsonc`, `web/_headers` | preservar; documentar na Fase F |

Nenhum script ou dado foi descartado nesta fase.

## 7. Testes realizados

| Data | Comando | Resultado |
|---|---|---|
| 2026-11-25 | `OPENLUX_CHROMIUM=/opt/pw-browsers/chromium python3 -m pytest -q tests` (branch com o PR #26 mergeado) | 226 passam, 1 pulado (teste remoto, exige `OPENLUX_URL`) |
| 2026-11-25 | Sonda de produção `curl https://openlux.labdados.org/...` | `/data/indicators_noaa20.json`: 404 (ver P2) |
| 2026-11-25 | Fase B: `pytest -q tests` após mover a pasta de revisão, atualizar pyproject e criar o lock | 227 passam, 1 pulado (o pulado é o teste remoto) |
| 2026-11-25 | Prévia Cloudflare do commit `19afcc7` | Build e deploy com sucesso; `/explorar` 200, `indicators_noaa20.json` 200, `pixels/noaa20/2025.bin` 200 |
| 2026-11-25 | Capturas do navegador (desktop, 2x) da prévia local | Sem erros de console nas três visões; ver a sessão de verificação visual |

## 8. Pendências que dependem do responsável

1. **Guia da NASA:** enviar o PDF `BlackMarbleUserGuide_Collection2.0.pdf` ou confirmar unidades, máscaras e camadas no navegador (P3).
2. **Atualizar DECISIONS §15:** autorizar o addendum que registra o NOAA-20 como mapa padrão (K1).
3. **Cloudflare:** confirmar se a produção de `main` foi implantada (P2). Se não, enviar o trecho do log.
4. **Reprocessamento:** autorizar P75/P90/P95 e área acima de limiares a partir de `data/raw/`, com revisão antes de publicar.
5. **PDF:** aceitar dependência para gerar PDF ou preferir impressão pelo navegador.
6. **Camadas ambientais:** informar quais fontes oficiais usar (IBGE, INEA, ICMBio, MapBiomas). INEA respondeu 503 e IBGE 403 nas tentativas anteriores; ICMBio tem licença CC BY-ND 3.0 que proíbe derivados.
7. **Base do 2.0:** o prompt manda reconstruir a interface, mas também manda preservar o que funciona. Você disse que o protótipo é melhor; ele não está no repositório. Definir se o protótipo vira referência ou se a interface atual é a base.
8. **Tag `v0.1.0`:** criada pela interface do GitHub (push recusado com 403 nesta sessão).
9. **Zenodo:** nova versão só depois da conclusão do 2.0, publicada por você.

## 9. Problemas conhecidos

- Não há resultado validado cientificamente. Todos os indicadores são **não validados**, como declarado no README.
- O S-NPP tem ruído de fundo maior a partir de 2022; a causa não foi identificada (METHODOLOGY §13).
- O sinal da tendência depende da janela de anos.
- Não há comparação com valores publicados.
- A validação em campo com SQM não foi feita (`docs/FIELD_VALIDATION.md`).

## 10. Próximas ações

Fase A: concluída e mergeada (PR #27). Fase B: concluída, com a exceção do build de produção (P2), bloqueado pelo responsável.

1. Fase C: bloqueada no guia oficial da NASA (pendência 1) e na fonte INEA (nova tentativa agendada para 2026-11-26 01:58 UTC).
2. Enquanto isso, itens de Fase C que não dependem do guia: confirmar SIRGAS 2000 e medir a diferença para WGS84; revisar a agregação municipal; reproduzir o pipeline a partir de `data/raw/` e comparar com os hashes do Apêndice C de METHODOLOGY.
