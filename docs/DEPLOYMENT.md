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
definidos, e `OPENLUX_URL=http://127.0.0.1:8788 python -m pytest tests/test_web_smoke.py` passou (10 testes). Esse teste foi removido na reconstrução; a verificação equivalente é `tests/test_deploy_publicado.py`.

**Resultado na Cloudflare (2026-11-23).** Antes do `wrangler.jsonc`, o check falhava cedo, sem mensagem: era o erro documentado
pela Cloudflare ("Missing Wrangler configuration file / Missing entry-point", na página *Troubleshooting builds*). Depois de adicioná-lo, o build
**passa** e o check passa a falhar numa etapa posterior, com a mensagem: **"Preview creation failed: This Worker does not exist on your account."**
Essa mensagem **não consta** da página de solução de problemas da Cloudflare e a causa **não foi identificada**. O que se sabe: o `name` coincide com o
Worker (`Script: openlux`; um nome divergente geraria outro erro, documentado), e a data de compatibilidade não é a causa (o build passou). O que verificar no
painel (a confirmar na interface atual): se o Worker `openlux` tem as *Preview URLs* habilitadas e se o build de produção (push em `main`) conclui. Uma falha
de build **não retira do ar** a implantação atual. Se a criação de prévias não for necessária, desative os builds de branches que não são a de produção.

A `compatibility_date` é irrelevante para um Worker só de arquivos estáticos; usei 2026-11-19, a data mais recente que o `wrangler` 4.166 sugere.
As reproduções locais (`deploy --dry-run`, `versions upload --dry-run`, `wrangler dev`) passam.

**O nome deve coincidir com o Worker existente** (`openlux`); se o Worker tiver outro nome, ajuste o arquivo, senão a
Cloudflare criaria um Worker novo em vez de atualizar o atual.

## 2. Verificação pós-implantação

```bash
OPENLUX_URL=https://openlux.labdados.org python -m pytest tests/test_deploy_publicado.py
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

## 7. Processo de deploy reproduzível (OpenLux 2.0)

A publicação é feita pela Cloudflare a partir da branch `main`. Antes de mergear, o processo exige:

1. **Testes:** o workflow `.github/workflows/testes.yml` roda `pytest` em cada push e em cada PR para `main`. Localmente, o mesmo comando é `pytest -q tests`.
2. **Build de prévia:** o check `Workers Builds: openlux` precisa estar verde no PR. A prévia aparece como comentário do bot da Cloudflare, com URL própria do commit.
3. **Verificação de arquivos:** `python scripts/build_catalogo.py` regenera `web/data/downloads/catalogo.json`, e `pytest tests/test_catalogo.py` confere os hashes e tamanhos contra os arquivos publicados.
4. **Verificação dos dados:** o NOAA-20 precisa ter `code_dirty: false` em `web/data/indicators_noaa20.json` (rodar a partir de commit limpo).
5. **Testes de navegação, acessibilidade e links:** `tests/test_web_paginas.py`, `tests/test_web_explorador.py` e `tests/test_web_municipios.py` abrem as páginas no Chromium e conferem valores contra os dados publicados. `tests/test_web_acessibilidade.py` confere idioma, nomes de botões e campos, texto alternativo. `tests/test_web_links.py` confere que todo link interno aponta para um arquivo existente. Responsividade: `tests/test_web_paginas.py` confere rolagem horizontal em 390 px.
6. **Merge:** só depois de os checks passarem no head do PR. O merge usa o `expectedHeadSha` para não mergear um commit que não foi verificado.

**Verificação do site publicado:** com `OPENLUX_URL` definido, `tests/test_deploy_publicado.py` compara o SHA-256 de cada arquivo de `web/` com o que o servidor entrega (em HTML, descontando as injeções da Cloudflare). Um arquivo diferente aparece como falha com o nome dele. Os demais testes de navegação também aceitam `OPENLUX_URL`. Exemplo: `OPENLUX_URL=https://openlux.labdados.org pytest tests/test_deploy_publicado.py`. Enquanto a branch não é publicada, o preview do branch mostra a versão do último commit implantado, e o teste aponta os arquivos alterados que ainda não estão no ar.

**Verificação depois do deploy:** a Cloudflare pode servir uma cópia em cache. Para confirmar a publicação de `main`, conferir `https://openlux.labdados.org/index.html` em janela anônima e comparar o título da página com o do commit.

**Não verificado daqui:** o log do build de produção de `main` (o painel da Cloudflare não é acessível pela sessão). Quando esse log estiver disponível, anotar aqui o commit publicado.

## 8. Revisão da configuração (2026-11-26)

**Conferido no repositório:**
- `wrangler.jsonc`: Worker estático `openlux`, pasta `./web`, sem código de servidor, sem `vars`, `routes` nem `env`. Nenhum segredo está versionado (varredura de padrões de chaves e tokens nos arquivos rastreados: nada encontrado).
- `web/_headers`: CSP com `script-src 'self'` (sem script inline), `X-Frame-Options: DENY`, `nosniff`, `Referrer-Policy` e `Permissions-Policy`. Todas as páginas publicadas passam no teste de script inline (`tests/test_web_links.py`).
- Não há `web/_redirects`. Não há variáveis de ambiente nem chaves no repositório.
- Arquivos internos: `web/` não contém código Python, dados brutos, `.h5`, `.shp`, logs nem arquivos temporários.

**Observado no ar:** `https://…/index.html` responde 307 com destino `/`, no preview e na produção. É o comportamento de URLs limpas da Cloudflare, e não quebra nenhum link interno (o teste `tests/test_web_links.py` confere todos).

**Não verificado (exige acesso ao painel da Cloudflare):**
- Log do build de produção de `main`.
- Regras de cache e de redirecionamento configuradas no painel, fora do repositório.
- Variáveis de ambiente e configurações do painel, e DNS (não alterados, conforme o prompt).
- Política de acesso do domínio `openlux.labdados.org`.
