"""Roteiros da página: cada link tem de apontar para uma vista que o site consegue montar."""
import json
import re
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from helpers import WEB

HTML = (WEB / "roteiros.html").read_text(encoding="utf-8")
DATA = json.loads((WEB / "data" / "indicators.json").read_text(encoding="utf-8"))
PIX = json.loads((WEB / "data" / "pixels" / "meta.json").read_text(encoding="utf-8"))
YEARS = {str(y) for y in DATA["meta"]["years"]}
INDICATORS = {"mean", "valid", "lit", "percap", "urban", "rural"}  # chaves fixas de IND em app.js (ver teste de não-regressão)


def _links():
    return re.findall(r'<a href="index\.html\?([^"]+)">', HTML.replace("&amp;", "&"))


def test_there_are_six_guided_views():
    assert len(_links()) == 6


def test_every_link_points_to_a_valid_view():
    for query in _links():
        q = {k: v[0] for k, v in parse_qs(query).items()}
        assert q.get("l") in {"mun", "pixel"}, query
        if "i" in q:
            assert q["i"] in INDICATORS, query
        if "y" in q:
            assert q["y"] in YEARS, query
        if "s" in q:
            assert q["s"] in PIX["sensors"], query
        if "v" in q:
            assert q["v"] == "rad" or q["v"] in PIX["sensors"][q.get("s", "snpp")]["change"], query


def test_pixel_views_only_use_sensors_with_that_window():
    for query in _links():
        q = {k: v[0] for k, v in parse_qs(query).items()}
        if q.get("l") == "pixel" and "v" in q and q["v"] != "rad":
            assert q["v"] in PIX["sensors"][q["s"]]["change"], query


def test_notes_about_noise_are_on_the_page_next_to_the_roteiro():
    assert "ruído" in HTML
