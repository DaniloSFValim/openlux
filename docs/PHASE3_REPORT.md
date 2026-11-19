# Fase 3: documentação acadêmica, identificação e licenciamento

Estado em 2026-11-19. Cada item cita a evidência; "pendente" indica decisão ou dado que só o autor pode fornecer.

| Item | Situação | Evidência e ressalvas |
|---|---|---|
| 3.1 `README.md` | Concluído | 18 seções na ordem especificada (verificado por teste). Descreve só o que está implementado e testado; o que não está consta como trabalho futuro. Sem as expressões "revolucionário", "inédito" ou "pioneiro" (verificado por teste). |
| 3.2 `METHODOLOGY.md` | Concluído | Fundamentação, produtos, equações, unidades, agregação, parâmetros, tratamento dos dados, qualidade, validação, limitações, reprodução passo a passo e apêndices de entradas (hashes), ambiente e saídas. Os hashes do Apêndice A são conferidos por teste contra `data/metadata/downloads/`. A igualdade byte a byte das saídas foi verificada só no ambiente de referência. |
| 3.3 `CITATION.cff` | Concluído, com pendências | Valida no esquema oficial CFF 1.2.0 (0 erros; esquema do pacote `cffconvert`, usado via `jsonschema`, porque o `cffconvert` não instalou por completo). Tipo software, autor Danilo Valim. **Pendentes:** ORCID, `license`, `date-released`. |
| 3.4 `.zenodo.json` | Preparado, não validado pelo Zenodo | JSON válido com `upload_type`, título, criador, descrição, palavras-chave, `access_right`, versão. ORCID, afiliação e `license` omitidos de propósito. Os vocabulários do Zenodo (`relation`, `resource_type`) **não foram validados** contra o validador do Zenodo; isso só é possível em um depósito de rascunho (Fase 4). |
| 3.5 Licença | Opções apresentadas; **nada instalado** | `docs/LICENSING.md` compara MIT, Apache-2.0 e GPL-3.0, separa código e dados e recomenda MIT sem impor. Um teste exige que a licença seja declarada em todos os arquivos ou em nenhum. |
| 3.6 Referências | Concluído | 10 DOIs resolvidos no Crossref, com ano e primeiro autor conferidos contra a citação no texto; bibliografia gerada de metadados do Crossref (`docs/REFERENCES.md`). Teste confirma que toda obra listada é citada no texto e toda citação autor-ano está na lista. |

## Desvios e decisões a confirmar

1. **Versão 0.1.0 em vez de 1.0.0.** A especificação cita a release `v1.0.0`. Mantive 0.1.0 em `pyproject.toml`, `CITATION.cff` e `.zenodo.json` porque 1.0.0 sugere
   um software estável e validado, e os resultados ainda não foram validados e há uma questão científica não resolvida (piso de ruído do S-NPP). A mudança para 1.0.0 é trivial se o autor preferir.
2. **Dependência removida.** `pyarrow` estava declarada e não era usada (GeoParquet previsto na Fase 1, não adotado); foi removida. Um teste impede dependências declaradas e não importadas.
3. **Licença das tabelas em `web/data/`.** Continua dependendo da confirmação dos termos de NASA e SIDRA.

## Pendências do autor

- Licença do código (e de conteúdo, se desejado) e titular dos direitos; ver `docs/LICENSING.md`.
- ORCID (e, se quiser declarar, afiliação).
- Prazo e exigências do edital PGC/UFF.
- Remover as credenciais antigas dos *Network secrets*.
- Decidir se os agregados de `web/data/` permanecem no repositório antes da confirmação das licenças.
