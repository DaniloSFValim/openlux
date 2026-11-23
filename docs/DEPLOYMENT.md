# Implantação do site

O site é estático (`web/`), sem etapa de build. URL pública: **https://openlux.labdados.org/**
(hospedagem na Cloudflare). Verificado em 2026-11-23: os arquivos servidos são idênticos aos de
`web/` na `main`, exceto por trechos que a própria Cloudflare injeta (seção 3).

## 1. Configuração (Cloudflare)

| Campo | Valor |
|---|---|
| Repositório | `DaniloSFValim/openlux`, branch `main` |
| Comando de build | nenhum |
| Diretório de saída (arquivos estáticos) | `web` |
| Domínio personalizado | `openlux.labdados.org` |

Use um projeto separado do sistema anterior de iluminação pública (o OpenLux é independente dele).
Os nomes exatos dos campos mudam com a interface da Cloudflare: confira no painel.

## 1.1. Configuração do Worker no repositório (`wrangler.jsonc`)

A primeira prévia (PR #4) falhou no check **Workers Builds** da Cloudflare. O log do build só existe no
painel (exige login), mas a causa foi **reproduzida localmente**: sem arquivo de configuração e sem
`--assets`, os dois comandos padrão da Cloudflare falham com `Missing entry-point to Worker script or to
assets directory`:

```bash
npx wrangler deploy --dry-run            # falha sem wrangler.jsonc
npx wrangler versions upload --dry-run   # idem (comando padrão das branches de prévia)
```

O `wrangler.jsonc` na raiz declara o Worker de arquivos estáticos (`name: openlux`, `assets.directory: ./web`).
Com ele, os dois comandos passam, e o `_headers` é honrado: `npx wrangler dev` serviu a pasta com todos os cabeçalhos
definidos, e `OPENLUX_URL=http://127.0.0.1:8788 python -m pytest tests/test_web_smoke.py` passou (10 testes).
A `compatibility_date` é irrelevante para um Worker só de arquivos estáticos; usei 2026-11-19, a data mais recente
que o `wrangler` 4.166 sugere (uma data posterior à conhecida pelo runtime é uma causa possível de recusa, **não confirmada**).
Mesmo com essa configuração o check **Workers Builds continuou falhando** em 2026-11-23 e o log do build só está no painel da Cloudflare:
a causa real **ainda não foi identificada**. As reproduções locais (`deploy --dry-run`, `versions upload --dry-run`, `wrangler dev`) passam.
**O nome deve coincidir com o Worker existente** (`openlux`); se o Worker tiver outro nome, ajuste o arquivo, senão a
Cloudflare criaria um Worker novo em vez de atualizar o atual.

## 2. Verificação pós-implantação

```bash
OPENLUX_URL=https://openlux.labdados.org python -m pytest tests/test_web_smoke.py
```

(Se o Chromium do Playwright não estiver instalado, defina `OPENLUX_CHROMIUM` com o caminho de um.)
Com `OPENLUX_URL`, o teste abre o site real e confere: 92 municípios desenhados, sem erros de console,
cores desenhadas iguais à classificação independente, legenda, aviso metodológico, painéis,
**cabeçalhos de segurança** de `web/_headers` e que **os arquivos publicados são idênticos aos do
repositório** (descontadas só as injeções conhecidas da Cloudflare).

## 3. Cabeçalhos (`web/_headers`)

| Cabeçalho | Efeito |
|---|---|
| `Content-Security-Policy` | Só recursos do próprio domínio; `script-src 'self'` (sem scripts inline); sem objetos, formulários e frames externos |
| `X-Content-Type-Options: nosniff` | Impede que o navegador adivinhe o tipo de arquivo |
| `Referrer-Policy: strict-origin-when-cross-origin` | Não vaza o caminho completo em links externos (DOI, fontes) |
| `X-Frame-Options: DENY` | O site não pode ser embutido em outras páginas |
| `Permissions-Policy` | Desativa câmera, microfone, geolocalização, pagamento e USB |
| `Cache-Control` em `/data/*` (5 min) e `/vendor/*` (1 dia) | Dados regenerados a cada implantação; HTML segue o padrão de revalidação |

O teste local do repositório aplica `web/_headers` ao servidor, então qualquer violação da política
pelo próprio site aparece como erro de console. Que a Cloudflare honre o arquivo `_headers` na sua
forma de implantação **deve ser conferido** com o teste da seção 2 (o teste de cabeçalhos falha se não for honrado).

## 4. O que a Cloudflare injeta no HTML

Em 2026-11-23, a resposta de `/` no domínio personalizado traz, antes de `</body>`, dois trechos que
**não estão no repositório**:

1. um script inline de **detecção de bots** (`window.__CF$cv$params`);
2. o beacon do **Cloudflare Web Analytics** (`static.cloudflareinsights.com/beacon.min.js`), que mede visitas.

Com a política estrita de `_headers`, ambos são **bloqueados** (o site funciona igual; aparece só um
aviso de CSP no console). Escolha uma opção:

- **A. Manter a política estrita e desativar as injeções** no painel da Cloudflare (detecção de JavaScript e Web
  Analytics/Browser Insights; confira os nomes dos menus). O site volta a carregar apenas recursos do próprio domínio.
- **B. Manter o Web Analytics.** Acrescente à CSP `https://static.cloudflareinsights.com` em `script-src` e
  `https://cloudflareinsights.com` em `connect-src` (endereços a confirmar na documentação da Cloudflare). O script de
  detecção de bots, por ser inline, continua bloqueado. Se mantiver a análise de visitantes, avalie informar isso aos visitantes.

O teste remoto ignora **apenas** o aviso de CSP causado por essas duas injeções; qualquer outro erro de console falha o teste.

## 5. Fora do repositório

- **HSTS** e demais opções de TLS se configuram no painel da Cloudflare (SSL/TLS), não em `_headers`.
- O site exibe resultados **não validados**, com aviso permanente na página.

## 6. Se a URL mudar

Atualize `README.md`, `CITATION.cff` (`url`) e este documento; um teste confere que a URL é a mesma nos três.
