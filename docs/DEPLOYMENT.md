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
