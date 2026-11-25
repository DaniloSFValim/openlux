# Changelog

Formato: versões em ordem cronológica inversa. Datas no formato AAAA-MM-DD.

## Não lançado (preparação para a 2.0)

### Adicionado (Fase D, OpenLux 2.0)
- Observatório como página inicial (`web/index.html`, `web/js/observatorio.js`, `web/css/observatorio.css`): indicadores estaduais, evolução anual NOAA-20 com S-NPP, mapa de 92 municípios, ranking, distribuição e variação 2018→2025. Todos os números são calculados a partir de `data/indicators_noaa20.json`, `data/indicators.json` e `data/municipios.geojson`.
- Testes `tests/test_web_observatorio.py`, incluindo conferência independente da média estadual e da variação.

### Adicionado (Fase D, lente de comparação)
- `web/comparar.html`: compara dois anos municipais do NOAA-20 ou do S-NPP, com mapas lado a lado, controle deslizante, diferença absoluta B − A (classes simétricas), variação percentual com piso declarado e URL compartilhável. Módulo comum de mapa em `web/js/mapa-svg.js`, usado também pelo Observatório.
- Testes `tests/test_web_comparar.py`.

### Adicionado (Fase D, laboratório)
- `web/laboratorio.html`: até três municípios, tabela comparativa (média, mediana dos pixels, fração ≥ 0,5, posição e percentil entre municípios, tendência e p-valor, variação do pipeline), evolução anual, distribuição estadual com histograma e caixa, e tendências significativas (p < 0,05).
- `web/js/graficos-svg.js`: gráficos SVG próprios compartilhados pelo Observatório e pelo laboratório.
- Testes `tests/test_web_laboratorio.py`.

### Adicionado (Fase 8, dados abertos)
- `web/data/downloads/catalogo.json` (gerado por `scripts/build_catalogo.py`): inventário dos 7 arquivos publicados, com SHA-256, tamanho, unidade, período, sistema de referência, licença e registro de execução.
- `web/data/downloads/openlux_limites_municipais_rj.gpkg`: limites dos 92 municípios em GeoPackage (EPSG:4326 declarado).
- Página de dados mostra o catálogo; licença corrigida (confirmada em 2026-11-25).
- Testes `tests/test_catalogo.py`.

### Removido (Fase D)
- `web/js/inicio.js` e `tests/test_web_inicio.py`: substituídos pelo Observatório.

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
