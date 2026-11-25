# Changelog

Formato: versões em ordem cronológica inversa. Datas no formato AAAA-MM-DD.

## Não lançado (preparação para a 2.0)

### Alterado
- Mapa de pixels: o sensor padrão passa a ser o NOAA-20 (VJ146A4, 2018–2025), conforme `docs/DECISIONS.md` §15.
  O S-NPP continua disponível no seletor, com aviso de ruído a partir de 2022.
- Página inicial: indicadores do NOAA-20 (`web/data/indicators_noaa20.json`), 2018–2025.
- Página inicial: textos atualizados; o sombreado do S-NPP saiu do gráfico.
- Página Sobre: bloco de contexto ambiental com link oficial do ICMBio, sem hospedar dados derivados.
- Roteiros: quiz removido.
- Mapa do S-NPP e camada municipal: a camada municipal continua com dados do S-NPP (2012–2025), com nota explícita.
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
