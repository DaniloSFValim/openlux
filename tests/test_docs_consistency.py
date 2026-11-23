"""Consistencia da documentacao academica com o codigo, os metadados e os dados registrados."""
import importlib.util
import json
import re
from pathlib import Path

import pytest
import yaml

from openlux.references import check_citations

ROOT = Path(__file__).resolve().parent.parent
README = (ROOT / "README.md").read_text(encoding="utf-8")
METH = (ROOT / "METHODOLOGY.md").read_text(encoding="utf-8")
CFF = yaml.safe_load((ROOT / "CITATION.cff").read_text(encoding="utf-8"))
ZEN = json.loads((ROOT / ".zenodo.json").read_text(encoding="utf-8"))
REFS = json.loads((ROOT / "docs/references.json").read_text(encoding="utf-8"))
PYPROJECT = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

SECTIONS = ["Identificação", "Resumo científico", "Pergunta de pesquisa", "Objetivos",
            "Abrangência geográfica", "Fontes de dados", "Metodologia", "Indicadores implementados",
            "Arquitetura tecnológica", "Instalação", "Reprodução", "Validação", "Limitações",
            "Resultados efetivamente disponíveis", "Referências", "Como citar", "Autor e ORCID", "DOI"]


def test_readme_has_the_18_required_sections_in_order():
    heads = re.findall(r"^## (\d+)\. (.+)$", README, flags=re.M)
    assert [(int(n), t) for n, t in heads] == list(enumerate(SECTIONS, start=1))


def test_versions_are_consistent_everywhere():
    import openlux
    pv = re.search(r'^version = "([^"]+)"', PYPROJECT, flags=re.M).group(1)
    assert openlux.__version__ == pv == CFF["version"] == ZEN["version"]
    assert pv in README and pv in METH


def test_no_unsupported_superlatives():
    banned = re.compile(r"revolucion|inédit|inedit|pioneir", re.I)
    for f in ["README.md", "METHODOLOGY.md", "docs/DECISIONS.md", "docs/LICENSING.md", "web/index.html", "web/js/app.js"]:
        assert not banned.search((ROOT / f).read_text(encoding="utf-8")), f


def test_citations_match_bibliography_both_ways():
    r = check_citations(README + "\n" + METH, REFS)
    assert r == {"uncited_references": [], "unknown_citations": []}


def test_every_reference_doi_is_listed_in_all_bibliographies():
    refs_md = (ROOT / "docs/REFERENCES.md").read_text(encoding="utf-8")
    for r in REFS:
        for name, text in (("REFERENCES.md", refs_md), ("README", README), ("METHODOLOGY", METH)):
            assert f"https://doi.org/{r['doi']}" in text, (name, r["doi"])


def test_methodology_input_hashes_match_recorded_metadata():
    recorded = set()
    for f in (ROOT / "data/metadata/downloads").glob("*.json"):
        for item in json.loads(f.read_text(encoding="utf-8"))["files"]:
            recorded.add(item["sha256"])
    appendix_a = METH.split("## Apêndice A")[1].split("## Apêndice B")[0]
    doc = set(re.findall(r"\b[0-9a-f]{64}\b", appendix_a))
    assert doc == recorded and len(recorded) == 14 + 8 + 2 + 36 + 36 + 1


def test_citation_cff_is_valid_against_official_schema_if_available():
    spec = importlib.util.find_spec("cffconvert")
    jsonschema = pytest.importorskip("jsonschema")
    if spec is None:
        pytest.skip("cffconvert (esquema CFF 1.2.0) nao instalado")
    schema = json.loads((Path(spec.origin).parent / "schemas/1.2.0/schema.json").read_text(encoding="utf-8"))
    errors = list(jsonschema.Draft7Validator(schema).iter_errors(CFF))
    assert errors == [], [e.message for e in errors]


def test_citation_cff_structure_without_external_schema():
    assert CFF["cff-version"] == "1.2.0" and CFF["type"] == "software" and CFF["title"] == "OpenLux"
    assert CFF["authors"] == [{"family-names": "Valim", "given-names": "Danilo", "orcid": f"https://orcid.org/{ORCID}"}]
    assert CFF["repository-code"] == "https://github.com/DaniloSFValim/openlux"


ORCID = "0009-0009-7250-6151"  # informado pelo autor; nao inventado


def _orcid_checksum_ok(o: str) -> bool:
    """ISO 7064 mod 11-2, como nos identificadores ORCID."""
    d = o.replace("-", "")
    total = 0
    for ch in d[:15]:
        total = (total + int(ch)) * 2
    r = (12 - total % 11) % 11
    return d[15] == ("X" if r == 10 else str(r))


def test_orcid_is_valid_and_identical_in_every_file():
    assert re.fullmatch(r"\d{4}-\d{4}-\d{4}-\d{3}[\dX]", ORCID) and _orcid_checksum_ok(ORCID)
    assert CFF["authors"][0]["orcid"] == f"https://orcid.org/{ORCID}"
    assert ZEN["creators"][0]["orcid"] == ORCID
    assert ORCID in README and ORCID in (ROOT / "web/index.html").read_text(encoding="utf-8")


def test_zenodo_metadata_has_required_fields_and_no_invented_identity():
    assert ZEN["upload_type"] == "software" and ZEN["title"] == "OpenLux"
    assert ZEN["creators"] == [{"name": "Valim, Danilo", "orcid": ORCID}]  # sem afiliacao inventada
    assert "affiliation" not in json.dumps(ZEN).lower() and "affiliation" not in yaml.safe_dump(CFF).lower()
    assert ZEN["access_right"] == "open"


def test_mit_license_is_installed_and_declared_consistently():
    text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    assert text.startswith("MIT License") and "Copyright (c) 2026 Danilo Valim" in text
    assert "Permission is hereby granted, free of charge" in text
    assert CFF["license"] == "MIT" and ZEN["license"].lower() == "mit"
    head = PYPROJECT.split("[project.optional")[0]
    assert 'license = { text = "MIT" }' in head and "MIT License" in head
    assert "Licença do código | MIT" in README


def test_declared_dependencies_are_all_imported_by_the_code():
    block = re.search(r"dependencies = \[(.*?)\]", PYPROJECT, flags=re.S).group(1)
    deps = re.findall(r'"([A-Za-z0-9_.-]+)"', block)
    code = "\n".join(p.read_text(encoding="utf-8") for p in list((ROOT / "src").rglob("*.py")) + list((ROOT / "scripts").glob("*.py")))
    for d in deps:
        assert re.search(rf"^\s*(import|from) {d}\b", code, flags=re.M), f"dependencia nao usada: {d}"


def test_required_terminology_is_used():
    phrase = "estimativa de poluição luminosa baseada em sensoriamento remoto"
    for name, text in (("README", README), ("METHODOLOGY", METH),
                       ("web/index.html", (ROOT / "web/index.html").read_text(encoding="utf-8"))):
        assert phrase in text.lower(), name
    low = README.lower()
    assert "não medições do brilho do céu" in low or "não medição do brilho do céu" in low


def test_release_notes_and_publication_guide_are_consistent():
    notes = (ROOT / "docs/RELEASE_NOTES_v0.1.0.md").read_text(encoding="utf-8")
    pub = (ROOT / "docs/PUBLICATION.md").read_text(encoding="utf-8")
    assert "v0.1.0" in notes and ORCID in notes and "não foram validados" in notes
    steps = re.findall(r"^(\d+)\. \*\*", pub.split("## 2.")[1].split("## 3.")[0], flags=re.M)
    assert steps == [str(i) for i in range(1, 12)]  # os 11 passos da integracao com o Zenodo
    assert "Concept DOI" in pub and "não pode estar dentro" in pub and "v0.1.0" in pub


def test_no_data_source_is_left_unverified():
    from openlux.webdata import SOURCES
    pend = [x["name"] for x in SOURCES if x["license_status"] == "nao_confirmado"]
    assert pend == []
    sidra = next(x for x in SOURCES if "SIDRA" in x["name"])
    assert sidra["license_status"] == "confirmado" and "autor" in sidra["note"]
    assert "Citação das fontes do IBGE" in README


def test_site_url_is_the_same_everywhere_and_verification_is_documented():
    url = "https://openlux.labdados.org/"
    dep = (ROOT / "docs/DEPLOYMENT.md").read_text(encoding="utf-8")
    assert CFF["url"] == url and url in README and url.rstrip("/") in dep
    assert "OPENLUX_URL" in README and "OPENLUX_URL" in dep
    assert "Web Analytics" in dep and "detecção de bots" in dep  # injecoes da Cloudflare documentadas


def test_wrangler_config_matches_the_deployed_worker_and_assets_folder():
    import re as _re
    raw = (ROOT / "wrangler.jsonc").read_text(encoding="utf-8")
    cfg = json.loads(_re.sub(r"^\s*//.*$", "", raw, flags=_re.M))
    assert cfg["name"] == "openlux"                       # Worker existente na Cloudflare
    assert cfg["assets"]["directory"] == "./web" and (ROOT / "web" / "index.html").exists()
    assert "main" not in cfg                              # so arquivos estaticos, sem codigo de servidor


def test_phase5_report_does_not_claim_publication_or_unlisted_dois():
    """Enquanto nao ha release, o relatorio nao pode afirmar DOIs; depois, so DOIs presentes no README e no CITATION."""
    rep = (ROOT / "docs/PHASE5_REPORT.md").read_text(encoding="utf-8")
    zen = set(re.findall(r"10\.5281/zenodo\.\d+", rep))
    assert zen <= set(re.findall(r"10\.5281/zenodo\.\d+", README))
    assert zen <= set(re.findall(r"10\.5281/zenodo\.\d+", (ROOT / "CITATION.cff").read_text(encoding="utf-8")))
    if not zen:
        assert "Registro no Zenodo, DOI da versão, Concept DOI | **Pendente**" in rep
        assert "Release `v0.1.0` | **Pendente**" in rep
    assert "não declara conformidade" in rep and "não foram validados" in rep
