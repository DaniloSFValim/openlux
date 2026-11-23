"""Download verificado (LAADS DAAC e outras fontes HTTP).

Regras: o token vem de variavel de ambiente (EARTHDATA_TOKEN) e nunca e gravado em
registros; todo arquivo e escrito em ``.part``, verificado (assinatura HDF5 e, se
informado, SHA-256 esperado) e so entao renomeado; erros transitorios (502/503/504,
falhas de rede) sao repetidos com recuo exponencial; paginas de login/erro nunca
ficam gravadas como se fossem dados.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

from openlux.io import InvalidDownload, sha256_file, verify_hdf5

LAADS_BASE = "https://ladsweb.modaps.eosdis.nasa.gov"
#: Colecao 5200 = Black Marble Colecao 2.0 (VNP46A*, versao 002) no arquivo da LAADS.
LAADS_COLLECTION = 5200
TRANSIENT_HTTP = {429, 500, 502, 503, 504}


class DownloadFailed(Exception):
    """Falha de rede/servidor depois de esgotadas as tentativas."""


def _request(url, token, timeout):
    headers = {"User-Agent": "openlux-downloader"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=timeout)


def _get_with_retries(url, token, retries, timeout, sleep):
    last = None
    for attempt in range(1, retries + 1):
        try:
            return _request(url, token, timeout), attempt
        except urllib.error.HTTPError as e:
            if e.code not in TRANSIENT_HTTP:
                raise DownloadFailed(f"HTTP {e.code} em {url}") from e
            last = f"HTTP {e.code}"
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            last = repr(e)
        if attempt < retries:
            sleep(min(60, 2 ** attempt))
    raise DownloadFailed(f"{retries} tentativas esgotadas para {url}: {last}")


def download_verified(url, dest, *, token=None, expected_sha256=None, retries=5, timeout=300,
                      sleep=time.sleep):
    """Baixa ``url`` para ``dest`` (HDF5) e devolve o registro de proveniencia do arquivo."""
    dest = Path(dest)
    if dest.exists():
        try:
            verify_hdf5(dest)
            digest = sha256_file(dest)
            if expected_sha256 is None or digest == expected_sha256:
                return dict(url=url, path=str(dest), sha256=digest, size_bytes=dest.stat().st_size,
                            attempts=0, downloaded_utc=None)
        except InvalidDownload:
            pass
        dest.unlink()
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_suffix(dest.suffix + ".part")
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            resp, _ = _get_with_retries(url, token, 1, timeout, sleep)
            with resp, open(part, "wb") as out:
                while block := resp.read(1 << 20):
                    out.write(block)
            verify_hdf5(part)
            digest = sha256_file(part)
            if expected_sha256 is not None and digest != expected_sha256:
                raise InvalidDownload(f"SHA-256 diverge: {digest} != {expected_sha256}")
            part.replace(dest)
            return dict(url=url, path=str(dest), sha256=digest, size_bytes=dest.stat().st_size,
                        attempts=attempt,
                        downloaded_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
        except (DownloadFailed, InvalidDownload, OSError) as e:
            last_err = e
            part.unlink(missing_ok=True)
            if attempt < retries:
                sleep(min(60, 2 ** attempt))
    if isinstance(last_err, InvalidDownload):
        raise last_err
    raise DownloadFailed(f"{retries} tentativas esgotadas para {url}: {last_err}")


def laads_find_file(product, year, doy, tile, *, base=LAADS_BASE, token=None, retries=5,
                    sleep=time.sleep):
    """Localiza o arquivo do ``tile`` na listagem da LAADS. Retorna ``(nome, url_download)``."""
    path = f"allData/{LAADS_COLLECTION}/{product}/{year}/{doy:03d}"
    resp, _ = _get_with_retries(f"{base}/api/v2/content/details/{path}?format=json", token,
                                retries, 60, sleep)
    with resp:
        listing = json.load(resp)
    names = [d["name"] for d in listing.get("content", []) if f".{tile}." in d["name"]]
    if not names:
        raise DownloadFailed(f"tile {tile} nao encontrado em {product} {year}/{doy:03d}")
    name = sorted(names)[-1]  # mais recente em caso de reprocessamento
    return name, f"{base}/api/v2/content/archives/{path}/{name}"


def laads_list_days(product, year, *, base=LAADS_BASE, token=None, retries=5, sleep=time.sleep):
    """Dias do ano (inteiros, ordenados) com diretorio de dados para ``product`` em ``year``.

    Produtos anuais tem so o dia 1; os mensais tem o primeiro dia de cada mes (001, 032, 060, ...).
    """
    path = f"allData/{LAADS_COLLECTION}/{product}/{year}"
    resp, _ = _get_with_retries(f"{base}/api/v2/content/details/{path}?format=json", token,
                                retries, 60, sleep)
    with resp:
        listing = json.load(resp)
    return sorted(int(d["name"]) for d in listing.get("content", [])
                  if d.get("resourceType") == "Directory" and d["name"].isdigit())


def token_from_env(var="EARTHDATA_TOKEN"):
    return os.environ.get(var) or None
