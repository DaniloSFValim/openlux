"""Arquivo web/_headers: estrutura e politica de seguranca (sem navegador)."""
from helpers import WEB, has_cloudflare_injection, headers_for, parse_headers_file, strip_cloudflare_injections

TEXT = (WEB / "_headers").read_text(encoding="utf-8")
RULES = parse_headers_file(TEXT)


def test_parser_handles_patterns_comments_and_indentation():
    r = parse_headers_file("# c\n/*\n  A: 1\n  B: x: y\n\n/data/*\n  C: 2\n")
    assert r == [("/*", {"A": "1", "B": "x: y"}), ("/data/*", {"C": "2"})]
    assert headers_for("/data/a.json", r) == {"A": "1", "B": "x: y", "C": "2"}
    assert headers_for("/index.html", r) == {"A": "1", "B": "x: y"}


def test_every_path_gets_the_baseline_security_headers():
    h = headers_for("/index.html", RULES)
    assert h["X-Content-Type-Options"] == "nosniff"
    assert h["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert h["X-Frame-Options"] == "DENY"
    assert "geolocation=()" in h["Permissions-Policy"]


def test_csp_is_strict_for_scripts_and_same_origin_only():
    csp = headers_for("/", RULES)["Content-Security-Policy"]
    directives = {d.split()[0]: d.split()[1:] for d in (x.strip() for x in csp.split(";")) if d}
    assert directives["script-src"] == ["'self'"]           # sem 'unsafe-inline' nem 'unsafe-eval'
    assert "'unsafe-eval'" not in csp
    assert directives["default-src"] == ["'self'"]
    assert directives["connect-src"] == ["'self'"]           # so os dados do proprio site
    # unica excecao a "so do proprio dominio": imagens do mapa-base opcional do OpenStreetMap (um unico host, so imagens)
    assert directives["img-src"] == ["'self'", "data:", "https://tile.openstreetmap.org"]
    assert directives["style-src"] == ["'self'", "'unsafe-inline'"] and directives["font-src"] == ["'self'"]
    assert directives["frame-ancestors"] == ["'none'"] and directives["object-src"] == ["'none'"]
    assert "http:" not in csp and "*" not in csp.replace("'self'", "")


def test_data_and_vendor_have_explicit_cache_and_html_does_not():
    assert headers_for("/data/indicators.json", RULES)["Cache-Control"] == "public, max-age=300"
    assert headers_for("/vendor/leaflet/leaflet.js", RULES)["Cache-Control"] == "public, max-age=86400"
    assert "Cache-Control" not in headers_for("/index.html", RULES)  # HTML segue o padrao (revalidar)


def test_known_cloudflare_injections_are_detected_and_stripped_exactly():
    page = "<html><body><p>x</p></body></html>"
    bots = "<script>window.__CF$cv$params={r:'a',t:'b'};(function(){var l=1;})();</script>"
    beacon = ('<script type="module" src="https://static.cloudflareinsights.com/beacon.min.js/vabc" '
              'integrity="sha512-x" data-cf-beacon=\'{"token":"t"}\' crossorigin="anonymous"></script>')
    injected = page.replace("</body>", bots + beacon + "\n</body>")  # formato real: \n apos o beacon
    assert has_cloudflare_injection(injected) and not has_cloudflare_injection(page)
    assert strip_cloudflare_injections(injected) == page
    # um script qualquer do proprio site NAO e removido
    own = page.replace("</body>", "<script src='js/app.js'></script></body>")
    assert strip_cloudflare_injections(own) == own and not has_cloudflare_injection(own)
