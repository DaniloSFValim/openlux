"""Testes das páginas de análise reconstruídas: Laboratório, Observatório ambiental,
Dados abertos e Metodologia, e da navegação comum.

Os valores esperados saem dos arquivos publicados (indicadores, catálogo e os próprios
arquivos, com SHA-256 recalculado) — não de constantes copiadas da página.
"""
import hashlib
import http.server
import json
import os
import socketserver
import threading
from pathlib import Path

import pytest

playwright = pytest.importorskip("playwright.sync_api")

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
RIO, NITEROI, CACHOEIRAS = "3304557", "3303302", "3300803"


@pytest.fixture(scope="module")
def server():
    if os.environ.get("OPENLUX_URL"):  # modo publicado: testa o site no ar, sem servidor local
        yield os.environ["OPENLUX_URL"].rstrip("/")
        return
    class H(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **k):
            super().__init__(*a, directory=str(WEB), **k)

        def log_message(self, *a):
            pass

    httpd = socketserver.TCPServer(("127.0.0.1", 0), H)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()


@pytest.fixture()
def pg():
    with playwright.sync_playwright() as p:
        exe = os.environ.get("OPENLUX_CHROMIUM")
        b = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
        page = b.new_page(viewport={"width": 1280, "height": 900})
        page.errors = []
        page.on("pageerror", lambda e: page.errors.append(str(e)))
        page.on("console", lambda m: page.errors.append(m.text) if m.type == "error" else None)
        yield page
        b.close()


def _indicadores():
    return json.loads((WEB / "data/indicators_noaa20.json").read_text(encoding="utf-8"))


def _fmt2(v):
    return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def test_laboratorio_default_values_match_published_data(server, pg):
    N = _indicadores()
    pg.goto(server + "/laboratorio.html")
    pg.wait_for_selector("#corpoTab tr", state="attached")
    pg.wait_for_timeout(500)
    media_rio = N["municipios"][RIO]["mean"][-1]
    primeira = pg.locator("#corpoTab tr").nth(0).inner_text().split("\t")
    assert primeira[1] == _fmt2(media_rio), primeira
    assert pg.errors == []


def test_laboratorio_changing_municipality_updates_column_and_trend(server, pg):
    pg.goto(server + "/laboratorio.html")
    pg.wait_for_selector("#corpoTab tr", state="attached")
    pg.select_option("#m3", CACHOEIRAS)
    pg.wait_for_function("document.getElementById('cabTab').textContent.includes('Cachoeiras de Macacu')")
    assert "Cachoeiras de Macacu" in pg.locator("#cabTab").inner_text()
    assert pg.errors == []


def test_laboratorio_trend_is_not_claimed_when_not_significant(server, pg):
    N = _indicadores()
    assert N["municipios"][RIO]["trends"]["2018_2025"]["p_value"] >= 0.05
    pg.goto(server + "/laboratorio.html")
    pg.wait_for_selector("#corpoTrend tr", state="attached")
    assert "sem tendência estatisticamente sustentada" in pg.locator("#corpoTrend tr").nth(0).inner_text()


def test_laboratorio_has_definitions_for_every_indicator(server, pg):
    pg.goto(server + "/laboratorio.html")
    for termo in ["Média municipal", "Mediana municipal", "Percentis P75", "Posição entre municípios",
                  "Inclinação e p-valor", "Variação percentual 2018"]:
        assert pg.locator(f"h3:has-text('{termo}')").count() == 1, termo


def test_dados_lists_every_catalogue_file_and_hash_matches_bytes(server, pg):
    cat = json.loads((WEB / "data/downloads/catalogo.json").read_text(encoding="utf-8"))
    pg.goto(server + "/dados.html")
    pg.wait_for_selector("#catalogo tbody tr", state="attached")
    assert pg.locator("#catalogo tbody tr").count() == len(cat["arquivos"])
    for a in cat["arquivos"]:
        arq = WEB / a["arquivo"]
        assert arq.exists(), a["arquivo"]
        sha = hashlib.sha256(arq.read_bytes()).hexdigest()
        assert sha == a["sha256"], f"hash divergente em {a['arquivo']}"
        assert sha in pg.content(), f"SHA-256 de {a['arquivo']} ausente da página"
    assert pg.errors == []


def test_dados_download_link_serves_the_file(server, pg):
    cat = json.loads((WEB / "data/downloads/catalogo.json").read_text(encoding="utf-8"))
    alvo = cat["arquivos"][0]["arquivo"]
    pg.goto(server + "/dados.html")
    pg.wait_for_selector("#catalogo tbody tr", state="attached")
    r = pg.request.get(server + "/" + alvo)
    assert r.status == 200 and len(r.body()) == cat["arquivos"][0]["bytes"]


def test_ambiental_publishes_no_results_and_no_unreviewed_file(server, pg):
    pg.goto(server + "/ambiental.html")
    texto = pg.inner_text("main")
    assert "Publicadas agora: áreas urbanizadas de 2019 e a análise exploratória" in texto
    assert "Unidades de conservação e radiância (2025)" in texto
    assert "Nomes de UCs não são publicados" in texto
    assert not (WEB / "data/ambiental/uc_municipios.json").exists()
    assert "uc_municipios" not in pg.content()
    assert pg.errors == []


def test_metodologia_states_field_validation_was_not_done(server, pg):
    pg.goto(server + "/metodologia.html")
    texto = pg.inner_text("main")
    assert "Validação com medições de campo: não realizada" in texto
    assert "não mede" in texto.lower()
    assert "brilho do céu" in texto
    assert pg.errors == []


@pytest.mark.parametrize("pagina", ["index.html", "explorar.html", "laboratorio.html",
                                    "ambiental.html", "dados.html", "metodologia.html"])
def test_every_page_links_all_six_areas(server, pg, pagina):
    pg.goto(server + "/" + pagina)
    hrefs = pg.eval_on_selector_all(".menu-paginas a", "els => els.map(e => e.getAttribute('href'))")
    assert hrefs == ["index.html", "explorar.html", "laboratorio.html", "ambiental.html",
                     "dados.html", "metodologia.html"], hrefs
    assert pg.locator(f".menu-paginas a[href='{pagina}']").count() == 1


@pytest.mark.parametrize("pagina", ["index.html", "explorar.html", "laboratorio.html",
                                    "ambiental.html", "dados.html", "metodologia.html"])
def test_no_horizontal_scroll_at_phone_width(server, pg, pagina):
    """Largura de celular (390 px): o cartão municipal fora da tela não pode gerar rolagem horizontal."""
    pg.set_viewport_size({"width": 390, "height": 844})
    pg.goto(server + "/" + pagina)
    pg.wait_for_timeout(800)
    estilo = pg.evaluate("getComputedStyle(document.documentElement).overflowX")
    pg.evaluate("window.scrollBy(400, 0)")
    pg.wait_for_timeout(100)
    # rolagem programática pode existir com overflow hidden; o que importa ao usuário é overflow-x oculto
    # ou nenhuma rolagem efetiva
    assert estilo == "hidden" or pg.evaluate("window.scrollX") == 0, (pagina, estilo)


def test_observatorio_kpis_match_published_data(server, pg):
    N = _indicadores()
    pg.goto(server + "/index.html")
    pg.wait_for_selector("#kpis .kpi", state="attached")
    pg.wait_for_timeout(500)
    kpis = pg.locator("#kpis .kpi").all_inner_texts()
    assert len(kpis) == 6
    assert any(k.split("\n")[1] == "92" for k in kpis if "MUNIC" in k.upper())
    medias25 = [v["mean"][-1] for v in N["municipios"].values() if v["mean"][-1] is not None]
    media_estado = sum(medias25) / len(medias25)
    assert any(_fmt2(media_estado) in k for k in kpis), kpis
    assert pg.errors == []


def test_observatorio_ranking_search_and_explorer_links(server, pg):
    pg.goto(server + "/index.html")
    pg.wait_for_selector("#corpoRank tr", state="attached")
    assert pg.locator("#corpoRank tr").count() == 92
    pg.fill("#busca", "niter")
    pg.wait_for_timeout(200)
    assert pg.locator("#corpoRank tr").count() == 1
    assert "Niterói" in pg.locator("#corpoRank tr").first.inner_text()
    pg.fill("#busca", "")
    pg.wait_for_timeout(200)
    href = pg.locator("#corpoRank tr").nth(0).locator("a", has_text="explorar").get_attribute("href")
    assert href.startswith("explorar.html?s=noaa20&y=2025&m=")
    assert pg.errors == []


def test_observatorio_map_opens_card_with_link_to_explorer(server, pg):
    pg.goto(server + "/index.html")
    pg.wait_for_selector("#mapa path[data-cd]", state="attached")
    pg.evaluate("document.querySelector('#mapa path[data-cd=\"3304557\"]').dispatchEvent(new MouseEvent('click', {bubbles: true}))")
    pg.wait_for_function("document.getElementById('cartao').classList.contains('on')")
    assert pg.inner_text("#cNome") == "Rio de Janeiro"
    assert pg.get_attribute("#cExplorar", "href") == "explorar.html?s=noaa20&y=2025&m=3304557"
    assert pg.errors == []


def test_observatorio_states_limits_of_the_indicators(server, pg):
    pg.goto(server + "/index.html")
    texto = pg.inner_text("main")
    assert "Não mede consumo de energia" in texto
    assert "não sustentam tendência" in texto or "tendência" in texto


def test_laboratorio_difference_map_counts_match_published_trends(server, pg):
    """Mapa de diferenças: 92 polígonos; classes e contornos conferem com trends['2018_2025'] do JSON."""
    N = _indicadores()
    pulso = [m for m in N["municipios"].values()]
    calc = [m for m in pulso if m["trends"].get("2018_2025") and m["trends"]["2018_2025"].get("change_pct") is not None]
    # contorno = tendência sustentada, independente de haver variação percentual calculada
    sig = [m for m in pulso if m["trends"].get("2018_2025") and m["trends"]["2018_2025"]["p_value"] < 0.05]
    pg.goto(server + "/laboratorio.html")
    pg.wait_for_selector("#mapaDif path", state="attached")
    pg.wait_for_timeout(500)
    assert pg.locator("#mapaDif path").count() == 92
    assert pg.locator("#mapaDif path[stroke='#fff']").count() == len(sig)
    texto = pg.inner_text("#resumoDif")
    assert f"Municípios com cálculo: {len(calc)} de 92" in texto
    assert pg.errors == []


def test_laboratorio_pixel_shares_and_trends_match_published_csv(server, pg):
    """Pixels acima de limiares e tendência por pixel: valores exibidos conferem com os CSVs publicados."""
    import csv
    cad = list(csv.DictReader((WEB / "data/downloads/openlux_pixels_municipio_noaa20.csv").open(encoding="utf-8")))
    row = [r for r in cad if r["CD_MUN"] == RIO and r["year"] == "2025"][0]
    val = int(row["pix_validos"])
    acima2 = sum(int(row[f"pix_classe_{k}"]) for k in range(4, 8))
    fmt1 = lambda v: f"{v:.1f}".replace(".", ",")
    esperado = fmt1(100 * acima2 / val)
    pg.goto(server + "/laboratorio.html?y=2025")
    pg.wait_for_selector("#corpoTab tr", state="attached")
    pg.wait_for_timeout(600)
    linha = [pg.locator("#corpoTab tr").nth(i).inner_text() for i in range(pg.locator("#corpoTab tr").count())]
    alvo = [l for l in linha if "≥ 2 nW" in l][0]
    assert alvo.split("\t")[1] == esperado, (alvo, esperado)
    tend = [r for r in csv.DictReader((WEB / "data/downloads/openlux_tendencia_pixels_noaa20_2018_2025.csv").open(encoding="utf-8")) if r["CD_MUN"] == RIO][0]
    tot = sum(int(tend[k]) for k in tend if k != "CD_MUN")
    assert pg.locator("#corpoTrend tr").nth(0).inner_text().split("\t")[5] == fmt1(100 * int(tend["pix_aumento_significativo"]) / tot)
    assert pg.errors == []


def test_quality_report_has_no_failed_check(server, pg):
    """Relatório de qualidade gerado por scripts/build_relatorio_qualidade.py: nenhuma verificação pode falhar."""
    conteudo = (WEB / "qualidade.html").read_text(encoding="utf-8")
    assert "falhou" not in conteudo
    assert "verificações passaram" in conteudo
    pg.goto(server + "/qualidade.html")
    assert pg.errors == []


def test_urbanized_areas_derivatives_are_consistent(server, pg):
    """Áreas urbanizadas (IBGE 2019): tabela com 92 municípios, frações em [0, 1], camada válida, catálogo CC BY 4.0."""
    import csv
    linhas = list(csv.DictReader((WEB / "data/downloads/openlux_area_urbana_municipio_2019.csv").open(encoding="utf-8")))
    assert len(linhas) == 92
    fracoes = [float(r["fracao_urbana"]) for r in linhas]
    assert all(0 <= f <= 1 for f in fracoes)
    geo = json.loads((WEB / "data/downloads/openlux_areas_urbanizadas_rj_2019.geojson").read_text(encoding="utf-8"))
    assert geo["type"] == "FeatureCollection" and len(geo["features"]) == 1
    cat = json.loads((WEB / "data/downloads/catalogo.json").read_text(encoding="utf-8"))
    itens = {a["arquivo"]: a for a in cat["arquivos"]}
    for arq in ["data/downloads/openlux_area_urbana_municipio_2019.csv", "data/downloads/openlux_areas_urbanizadas_rj_2019.geojson"]:
        assert itens[arq]["licenca"] == "CC-BY-4.0"
        assert "IBGE" in itens[arq]["fonte"]
    pg.goto(server + "/ambiental.html")
    pg.wait_for_selector("#mapaUrb svg path", state="attached")
    assert pg.errors == []


def test_uc_analysis_page_matches_urbanization_controlled_result(server, pg):
    """Números publicados da análise de UCs conferem com o resultado publicado do controle de urbanização."""
    r = json.loads((WEB / "data/downloads/openlux_uc_controle_urbanizacao_2025.json").read_text(encoding="utf-8"))
    pt = lambda v: f"{v:.2f}".replace(".", ",").replace("-", "−")
    pg.goto(server + "/ambiental.html")
    texto = pg.inner_text("main")
    assert pt(r["parcial_controle_urbana"]) in texto
    assert pt(r["rho_urbana_x_radiancia"]) in texto
    assert "não se sustenta depois do controle pela urbanização" in texto
    assert pg.errors == []


def test_pixel_level_uc_result_matches_published_json(server, pg):
    """Números publicados no nível dos pixels conferem com o JSON publicado."""
    d = json.loads((WEB / "data/downloads/openlux_uc_controle_urbanizacao_pixels_2025.json").read_text(encoding="utf-8"))
    pt1 = lambda v: f"{v:.1f}".replace(".", ",")
    pg.goto(server + "/ambiental.html")
    texto = pg.inner_text("main")
    assert pt1(d["estratos"]["urbano_dentro_uc"]["mediana"]) in texto
    assert pt1(d["estratos"]["urbano_fora_uc"]["mediana"]) in texto
    assert "Não são publicados p-valores" in texto
    assert pg.errors == []


@pytest.mark.parametrize("pagina", ["ambiental.html", "laboratorio.html", "dados.html", "metodologia.html", "index.html"])
def test_user_can_scroll_with_mouse_wheel(server, pg, pagina):
    """prototipo.css bloqueava a rolagem (overflow hidden); a roda do mouse precisa mover a página."""
    pg.goto(server + "/" + pagina, wait_until="domcontentloaded")
    pg.wait_for_timeout(800)
    pg.mouse.move(640, 400)
    pg.mouse.wheel(0, 1200)
    pg.wait_for_timeout(600)
    assert pg.evaluate("window.scrollY") > 0, pagina
