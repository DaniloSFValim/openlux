# Changelog

Formato: versões em ordem cronológica inversa. Datas no formato AAAA-MM-DD.

## Não lançado (preparação para a 2.0)

Reconstrução do front-end a partir do protótipo aprovado (`docs/referencia/`). A versão anterior do front-end foi removida no commit `7d31fb0`; as entradas abaixo descrevem o estado atual.

### Adicionado
- Página inicial (Observatório): mapa dos 92 municípios em tela cheia e, abaixo, indicadores estaduais, evolução NOAA-20 com S-NPP tracejado, maiores e menores médias, distribuição municipal, variação 2018→2025, pixels iluminados, ranking com busca (`web/index.html`, `web/js/observatorio.js`).
- Lente por pixel no explorador: com a camada de pixels ligada, mostra as classes do ano da lente.
- Explorador geográfico (`web/explorar.html`, `web/js/explorador.js`, `web/css/explorador.css`): mapa por município e por pixel (classes de luz, sem radiância por pixel), gaveta de camadas, cartão municipal, lente de comparação entre dois anos e link compartilhável.
- Laboratório de análises (`web/laboratorio.html`): até três municípios comparados com o estado; médias, medianas, percentis dos pixels, posição, evolução, distribuição, caixa e tendência de Theil–Sen, com a definição de cada indicador.
- Observatório ambiental (`web/ambiental.html`): estado de cada camada e de cada licença. Nenhum resultado ambiental é publicado.
- Dados abertos (`web/dados.html`): catálogo com SHA-256, licença, sistema de referência, unidade e período; citação.
- Metodologia (`web/metodologia.html`): o que o OpenLux mede e não mede, processamento, limitações; validação em campo marcada como não realizada.
- Páginas municipais e relatórios em PDF para os 92 municípios (`web/municipio/`, `web/municipios.html`), gerados por `scripts/build_web_municipios.py`.
- Capturas reais das páginas em `docs/screenshots/openlux-2.0/`.
- Testes de navegador em `tests/test_web_explorador.py`, `tests/test_web_paginas.py` e `tests/test_web_municipios.py`.

### Alterado
- Laboratório: percentual de pixels acima de 2, 8, 30 e 100 nW·cm⁻²·sr⁻¹ e tendência por pixel 2018–2025 (contagens em `openlux_pixels_municipio_noaa20.csv` e `openlux_tendencia_pixels_noaa20_2018_2025.csv`, gerados por `scripts/build_web_pixel_stats.py`).
- Pixels regerados a partir de commit limpo (`db2676b`): os 25 arquivos `.bin` têm SHA-256 idêntico ao anterior; só os metadados mudaram.
- Explorador: a área do cartão usa a área oficial do IBGE (`AREA_KM2`), e não a área geodésica calculada.
- Troca de sensor no explorador mantém ano e lente.

### Removido
- Páginas e funções fora do plano: `comparar.html` (a lente passou ao explorador), `roteiros.html`, `desenhar` (área desenhada), `observatorio.js` antigo, `laboratorio` antigo e o smoke test do mapa antigo.
- `web/data/ambiental/uc_municipios.json`: análise exploratória não revisada, que estava em pasta pública. Permanece no histórico do git.
- Capturas da interface anterior.
- Bloco `exposure` (população e radiância por setor censitário, classificação urbano/rural) dos JSONs publicados: a licença da malha de setores e o critério urbano/rural do IBGE não estão verificados. Nenhuma página o usava.

### Pendente
- Observatório ambiental: camadas bloqueadas por licença não verificada (áreas urbanizadas do IBGE, MapBiomas) ou por fonte inacessível (INEA). ICMBio tem licença que proíbe derivados.
- Relatório de qualidade dos dados (Fase 8).
- Validação em campo com SQM: protocolo proposto, nenhuma medição feita.
- Build de produção do Cloudflare sem confirmação.
- Republicar o bloco `exposure` só depois de verificar a licença da malha de setores censitários e o critério urbano/rural do IBGE.
- Decisão de publicação (Zenodo, nova versão).

### Alterado (Fase B, OpenLux 2.0)
- Arquivos de revisão do NOAA-20 saem da pasta pública `web/` e vão para `data/revisao/noaa20/` (histórico preservado com `git mv`). `scripts/build_web_downloads.py` e `tests/test_web_noaa20.py` atualizados. Novo teste impede arquivos de revisão em `web/`.
- `pyproject.toml`: versões mínimas das dependências = versões aprovadas na suíte. `requirements-lock.txt` registra o ambiente de referência.
- `docs/DECISIONS.md` §15.1: addendum com o NOAA-20 como mapa padrão, conforme a decisão do responsável em 2026-11-25.
- `docs/AUDITORIA_2_0.md`: itens A2 (CHANGELOG) e A7 (gaveta) atualizados para a situação atual.
- Mapa de pixels: o sensor padrão passa a ser o NOAA-20 (VJ146A4, 2018–2025), conforme `docs/DECISIONS.md` §15.
  O S-NPP continua disponível no seletor, com aviso de ruído a partir de 2022.
- Página inicial: indicadores do NOAA-20 (`web/data/indicators_noaa20.json`), 2018–2025.
- Página inicial: textos atualizados; o sombreado do S-NPP saiu do gráfico.
- Página Sobre: bloco de contexto ambiental com link oficial do ICMBio, sem hospedar dados derivados.
- Roteiros: quiz removido.
- Camada municipal: passa a usar o NOAA-20 (2018–2025) por padrão. O S-NPP (2012–2025) fica disponível pelo
  seletor de sensor (`?s=snpp`), com aviso de ruído a partir de 2022 e os indicadores só do S-NPP.
  Trocar de sensor recarrega a página, pois cada sensor tem seu próprio conjunto municipal.
- Link com ano fora da série do sensor (ex.: `y=2013` com NOAA-20) vai para o ano disponível mais próximo.
- Licença dos dados derivados (CC BY 4.0): status confirmado pelo autor em 2026-11-25.

### Adicionado
- `scripts/build_web_data_noaa20.py` e `web/data/indicators_noaa20.json`.
- Faixa "Onde você está entre os 92 municípios?" na página inicial.
- Cartão ancorado ao clicar num município e viagem no tempo sobre o mapa.
- Desenho de área com contagem de pixels por classe (Turf, empacotado localmente).
- `docs/AUDITORIA_2_0.md`, `docs/DICIONARIO_DE_DADOS.md` e este `CHANGELOG.md`.

### Corrigido
- Build de preview do Cloudflare: bloco `previews` adicionado ao `wrangler.jsonc`.
- Página inicial: o script de entrada não era carregado (conteúdo invisível).
- Mapa: duplicidade de navegação removida.

### Pendente
- Arquivos de download do NOAA-20 ainda não publicados.
- Camada municipal ainda no S-NPP.
- Fontes ambientais estaduais (INEA) indisponíveis no momento.
- Build de produção do Cloudflare sem confirmação.

## 0.1.0 — 2026-11-24

Primeira versão citável (`10.5281/zenodo.24510755`). Pipeline reprodutível de indicadores municipais e por setor
censitário a partir do VIIRS/VNP46A4 (S-NPP), 2012–2025, com interface web estática. Resultados não validados em campo.
