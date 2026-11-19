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
    assert doc == recorded and len(recorded) == 14 + 8 + 2


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
    assert CFF["authors"] == [{"family-names": "Valim", "given-names": "Danilo"}]
    assert CFF["repository-code"] == "https://github.com/DaniloSFValim/openlux"


def test_zenodo_metadata_has_required_fields_and_no_invented_identity():
    assert ZEN["upload_type"] == "software" and ZEN["title"] == "OpenLux"
    assert ZEN["creators"] == [{"name": "Valim, Danilo"}]
    assert "orcid" not in json.dumps(ZEN).lower() and "affiliation" not in json.dumps(ZEN).lower()
    assert "orcid" not in yaml.safe_dump(CFF).lower()


def test_license_declared_consistently_or_nowhere():
    has_file = (ROOT / "LICENSE").exists()
    declared = ["license" in CFF, "license" in ZEN, "license" in PYPROJECT.split("[project.optional")[0]]
    assert all(declared) if has_file else not any(declared)


def test_declared_dependencies_are_all_imported_by_the_code():
    block = re.search(r"dependencies = \[(.*?)\]", PYPROJECT, flags=re.S).group(1)
    deps = re.findall(r'"([A-Za-z0-9_.-]+)"', block)
    code = "\n".join(p.read_text(encoding="utf-8") for p in list((ROOT / "src").rglob("*.py")) + list((ROOT / "scripts").glob("*.py")))
    for d in deps:
        assert re.search(rf"^\s*(import|from) {d}\b", code, flags=re.M), f"dependencia nao usada: {d}"


def test_required_terminology_is_used_and_pending_items_are_declared():
    phrase = "estimativa de poluição luminosa baseada em sensoriamento remoto"
    for name, text in (("README", README), ("METHODOLOGY", METH),
                       ("web/index.html", (ROOT / "web/index.html").read_text(encoding="utf-8"))):
        assert phrase in text.lower(), name
    low = README.lower()
    assert "não medições do brilho do céu" in low or "não medição do brilho do céu" in low
    assert "pendente de decisão do autor" in low and "a ser informado" in low
