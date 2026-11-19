# Fechamento da Fase 2: verificacao dos criterios de aceitacao

Verificado em 2026-11-19 sobre a branch `claude/happy-goodall-c12zd5`. Cada linha cita a
evidencia. "Parcial" e "Nao atendido" indicam lacunas reais, nao ressalvas de forma.

| # | Criterio (secao 2.5) | Situacao | Evidencia e ressalvas |
|---|---|---|---|
| 1 | Pipeline executavel | **Atendido, com ressalva** | `fetch_blackmarble.py` -> `fetch_ibge.py` -> `run_annual.py` -> `build_web_data.py` executados de ponta a ponta no dado real. Depende de conta Earthdata com a licenca da LAADS aceita. Nao ha registro estruturado de logs (so saida padrao). |
| 2 | Indicadores implementados | **Parcial** | Implementados: A (media, mediana, intensidade radiante aparente), B (intensidade por habitante, so 2022), C (serie anual, variacao, tendencia Theil-Sen/Kendall), E (fracao da area acima de limiar; ver `docs/DECISIONS.md` secao 6), sensibilidade. **Nao implementados:** C "alteracoes espaciais significativas" (mudanca pixel a pixel), D (comparacao com o Atlas de Falchi; dados nao obtidos), E "urbano x nao urbano" (sem camada publica adequada verificada). A fracao acima de 0,5 do S-NPP e muito sensivel ao piso de ruido pos-2021. |
| 3 | Testes automatizados aprovados | **Atendido** | 73 testes passam (72 sem navegador). Clone limpo: 66 passam, 1 ignorado. Cobrem funcoes matematicas, agregacao zonal, dados ausentes, CRS (rejeita CRS divergente), integridade de arquivos, reprodutibilidade. Testes usam dados sinteticos rotulados. |
| 4 | Mapa com dados efetivamente processados | **Atendido** | `web/data/` e gerado de `outputs/annual/` por `build_web_data.py`; teste em navegador compara cores desenhadas com classificacao independente. Os resultados exibidos **nao sao validados** (aviso permanente). |
| 5 | Fontes identificadas | **Atendido, com ressalva** | Painel "Fontes de dados" com instituicao, URL, versao/DOI e status de licenca. NASA e SIDRA: licenca **nao confirmada** no texto oficial. |
| 6 | Resultados reproduziveis | **Atendido** | Duas execucoes completas no dado real geram 8 saidas com SHA-256 identico. Entradas fixadas por nome e SHA-256 em `data/metadata/downloads/`. Ressalva: depende de a NASA manter os arquivos disponiveis. |
| 7 | Sem credenciais nem dados nao publicos | **Atendido** | Varredura de arquivos e de todo o historico: sem token, senha ou chave; sem `.h5`, `.zip` ou `data/raw`. Token usado apenas via `EARTHDATA_TOKEN`/proxy. Ressalva: `web/data/` contem agregados derivados da NASA e populacao do SIDRA com licenca pendente. |
| 8 | Documentacao corresponde ao funcionamento real | **Atendido apos correcao** | Revisao achou uma afirmacao nao sustentada (suporte ao VNP46A3, nunca testado em dado real); README corrigido. `METHODOLOGY.md`, `CITATION.cff`, `.zenodo.json` e `LICENSE` **nao existem ainda** (Fase 3). |

## Lacunas conhecidas que nao bloqueiam o fechamento, mas devem ser decididas

1. Indicador D (Falchi) e as partes nao implementadas de C e E (ver linha 2): o autor decide adiar ou retirar do escopo. A fracao acima do limiar foi implementada depois do fechamento original, a pedido do autor.
2. Aumento de radiancia apos 2022: investigado, nao resolvido (`docs/DECISIONS.md`, secao 3).
3. Licencas de NASA, EOG e SIDRA nao confirmadas no texto oficial.
4. Prazo e exigencias do edital PGC/UFF nao informados.
5. Licenca do codigo pendente (Fase 3). ORCID pendente.
6. Credenciais antigas ainda salvas em *Network secrets* do ambiente (acao do autor).
