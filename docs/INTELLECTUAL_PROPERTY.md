<div align="center">

# 🔒 Propriedade Intelectual & Citação

*Como comprovar autoria (com data) e tornar o trabalho citável academicamente*

</div>

> **Aviso:** este documento é uma orientação prática, **não é parecer jurídico**.
> Para o registro formal, confirme com a Procuradoria do Município e/ou um
> advogado especializado em propriedade intelectual — especialmente a questão de
> **titularidade** (§4).

---

## 1. Camada imediata (grátis, já configurada no repositório)

| Mecanismo | O que prova | Status |
|---|---|---|
| **Histórico Git** | Autoria + cronologia (commits datados, encadeados por hash SHA) | ✅ contínuo |
| **`CITATION.cff`** | Metadados de citação (botão "Cite this repository" no GitHub) | ✅ neste repo |
| **`.zenodo.json`** | Metadados para arquivamento/DOI | ✅ neste repo |
| **Tag + GitHub Release** | Marco versionado e citável (`v1.3.0`) | ⏳ criar no merge |
| **DOI no Zenodo** | Arquivo permanente + citação acadêmica + **data comprovada** | ⏳ passo manual (§2) |
| **OpenTimestamps** | Carimbo de tempo do hash em blockchain | ⏳ opcional (§3) |

## 2. Emitir o DOI no Zenodo (10 min, grátis) — recomendado

O DOI é o "dois em um": **prova de autoria datada** e **citação acadêmica**.

1. Acesse <https://zenodo.org> e faça login **com a conta do GitHub**.
2. Em **Account → GitHub**, ligue o *toggle* do repositório
   `DaniloSFValim/iluminacao-led-niteroi`.
3. No GitHub, publique um **Release** a partir da tag `v1.3.0` (ver §5).
4. O Zenodo captura o release automaticamente e **emite um DOI**.
5. Copie o DOI e adicione em `CITATION.cff` (campo `doi:`) e no `README`.

> O Zenodo gera um DOI *versionado* (cada release) e um DOI *conceitual* (sempre
> aponta para a versão mais recente). Cite o conceitual em textos gerais.

## 3. Carimbo de tempo independente (opcional, reforça a data)

```bash
# hash do estado atual do repositório
git rev-parse HEAD
# ou hash de um pacote .zip do código, carimbado em blockchain:
#   https://opentimestamps.org  (arraste o arquivo, guarde o .ots)
```

## 4. Registro formal (certificado oficial) — quando quiser blindar

| Órgão | Protege | Quando vale a pena |
|---|---|---|
| **INPI — Registro de Programa de Computador** | O **código-fonte** (Lei 9.609/98) | Certificado datado e sigiloso; recomendável se houver interesse comercial/institucional |
| **Biblioteca Nacional / EDA** | A **documentação e o artigo** como obra científica (Lei 9.610/98) | Para o texto do artigo e o modelo descrito |
| **Cartório (RTD)** | "Data certa" de código ou texto | Alternativa simples e barata |

**Patente:** em geral **não se aplica** — a LPI (Lei 9.279/96, art. 10) exclui
"programas de computador em si" e métodos matemáticos. Não recomendado aqui.

### ⚠️ Titularidade — resolver antes de registrar
A Lei 9.609/98 (art. 4º) tende a atribuir a titularidade de software ao
**empregador/Administração** quando desenvolvido no exercício da função, salvo
disposição em contrário. Hoje o `LICENSE` e o `CITATION.cff` atribuem a autoria a
**Danilo Valim (pessoa física)**. Confirme se isso reflete o vínculo real; se o
Município for cotitular, ajuste `LICENSE`, `CITATION.cff` e `.zenodo.json` antes
de qualquer registro no INPI.

## 5. Criar a tag/release do marco citável

```bash
git tag -a v1.3.0 -m "Marco citável: gestão georreferenciada + fotometria Tier 2/3 + análise por polígono"
git push origin v1.3.0
# depois publique o Release no GitHub a partir da tag (dispara o Zenodo)
```

## 6. Como citar (enquanto o DOI não sai)

> Valim, D. (2026). *Iluminação LED Niterói — sistema georreferenciado de gestão
> do parque de iluminação pública com índices fotométricos de instalação* (v1.3.0)
> [Software]. GitHub. https://github.com/DaniloSFValim/iluminacao-led-niteroi

Após o Zenodo, troque a URL pelo DOI.

---

<div align="center">
SECONSER · Diretoria de Iluminação Pública · Prefeitura de Niterói
</div>
