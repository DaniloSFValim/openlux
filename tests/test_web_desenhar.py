"""Experimento "Desenhe uma área": arquivos locais, licença registrada e nenhum recurso externo."""
import re
from pathlib import Path

from helpers import WEB

EXPLORAR = (WEB / "explorar.html").read_text(encoding="utf-8")
DESENHAR = (WEB / "js" / "desenhar.js").read_text(encoding="utf-8")
VENDOR = WEB / "vendor" / "openlux-draw"


def test_turf_bundle_is_vendored_locally_with_its_license_notice():
    assert (VENDOR / "openlux-turf.min.js").is_file()
    texto = (VENDOR / "LICENSES.md").read_text(encoding="utf-8")
    assert "@turf/turf" in texto and "7.4.0" in texto and "MIT" in texto


def test_explorer_loads_turf_before_the_drawing_script_and_no_cdn():
    ordem = [m.group(1) for m in re.finditer(r'<script src="([^"]+)"', EXPLORAR)]
    assert ordem.index("vendor/openlux-draw/openlux-turf.min.js") < ordem.index("js/desenhar.js")
    assert ordem.index("js/app.js") < ordem.index("js/desenhar.js")
    assert not re.search(r"https?://[^\"']*\.js", EXPLORAR), "script externo na página do mapa"


def test_drawing_panel_has_the_controls_it_needs():
    for id_ in ("desenhar-iniciar", "desenhar-desfazer", "desenhar-concluir", "desenhar-limpar", "desenhar-resultado", "desenhar-status"):
        assert f'id="{id_}"' in EXPLORAR, id_


def test_drawing_counts_classes_and_never_publishes_values():
    assert "booleanPointInPolygon" in DESENHAR
    assert "code < 2 || code > 7" in DESENHAR          # 0 = fora do estado; 1 = sem dado válido
    assert "Mostra a contagem de classes, não a média de luz" in DESENHAR
    assert "terra" not in DESENHAR.lower()             # o desenho é próprio; Terra Draw não foi incluído


def test_bridge_exposes_only_read_only_state():
    app = (WEB / "js" / "app.js").read_text(encoding="utf-8")
    bloco = app.split("window.OpenLuxMapApi = {", 1)[1].split("};", 1)[0]
    assert "getGrid: (path) => pxGrid(path)" in bloco
    assert "currentPath" in bloco and "viewIsRadiance" in bloco
