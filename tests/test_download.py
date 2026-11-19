"""Downloader e proveniencia. O servidor HTTP e LOCAL e os conteudos sao SINTETICOS."""
import hashlib
import io
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import h5py
import numpy as np
import pytest

from openlux.download import DownloadFailed, download_verified, laads_find_file
from openlux.io import InvalidDownload


def _h5_bytes():
    buf = io.BytesIO()
    with h5py.File(buf, "w") as f:
        f.create_dataset("x", data=np.arange(100))
    return buf.getvalue()


class Server:
    """Servidor com respostas programaveis por caminho: lista de (status, corpo, headers)."""

    def __init__(self):
        self.script = {}
        self.calls = []
        outer = self

        class H(BaseHTTPRequestHandler):
            def do_GET(self):
                outer.calls.append((self.path, self.headers.get("Authorization")))
                seq = outer.script[self.path]
                status, body, headers = seq.pop(0) if len(seq) > 1 else seq[0]
                self.send_response(status)
                for k, v in headers.items():
                    self.send_header(k, v)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *a):
                pass

        self.httpd = HTTPServer(("127.0.0.1", 0), H)
        self.url = f"http://127.0.0.1:{self.httpd.server_port}"
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def close(self):
        self.httpd.shutdown()


@pytest.fixture
def srv():
    s = Server()
    yield s
    s.close()


def test_success_returns_hash_and_sends_token(srv, tmp_path):
    body = _h5_bytes()
    srv.script["/f.h5"] = [(200, body, {})]
    dest = tmp_path / "f.h5"
    rec = download_verified(srv.url + "/f.h5", dest, token="TKN", sleep=lambda s: None)
    assert dest.read_bytes() == body
    assert rec["sha256"] == hashlib.sha256(body).hexdigest()
    assert rec["size_bytes"] == len(body)
    assert rec["url"] == srv.url + "/f.h5"
    assert srv.calls[0][1] == "Bearer TKN"
    assert "TKN" not in json.dumps(rec)  # o token nunca entra no registro


def test_html_login_page_is_rejected_and_no_file_left(srv, tmp_path):
    srv.script["/f.h5"] = [(200, b"<!DOCTYPE html><html>login</html>", {})]
    dest = tmp_path / "f.h5"
    with pytest.raises(InvalidDownload):
        download_verified(srv.url + "/f.h5", dest, token="T", retries=2, sleep=lambda s: None)
    assert not dest.exists()
    assert not list(tmp_path.glob("*.part"))


def test_retries_on_502_then_succeeds(srv, tmp_path):
    body = _h5_bytes()
    srv.script["/f.h5"] = [(502, b"upstream request failed", {}), (502, b"x", {}), (200, body, {})]
    dest = tmp_path / "f.h5"
    rec = download_verified(srv.url + "/f.h5", dest, token="T", retries=4, sleep=lambda s: None)
    assert dest.exists() and rec["attempts"] == 3


def test_gives_up_after_retries(srv, tmp_path):
    srv.script["/f.h5"] = [(502, b"upstream request failed", {})]
    with pytest.raises(DownloadFailed):
        download_verified(srv.url + "/f.h5", tmp_path / "f.h5", token="T", retries=3,
                          sleep=lambda s: None)
    assert not (tmp_path / "f.h5").exists()


def test_existing_valid_file_is_not_downloaded_again(srv, tmp_path):
    body = _h5_bytes()
    dest = tmp_path / "f.h5"
    dest.write_bytes(body)
    rec = download_verified(srv.url + "/f.h5", dest, token="T")
    assert srv.calls == []
    assert rec["sha256"] == hashlib.sha256(body).hexdigest() and rec["attempts"] == 0


def test_expected_sha256_mismatch_is_rejected(srv, tmp_path):
    srv.script["/f.h5"] = [(200, _h5_bytes(), {})]
    with pytest.raises(InvalidDownload):
        download_verified(srv.url + "/f.h5", tmp_path / "f.h5", token="T",
                          expected_sha256="0" * 64, retries=1, sleep=lambda s: None)
    assert not (tmp_path / "f.h5").exists()


def test_laads_listing_finds_tile(srv):
    listing = {"content": [
        {"name": "VNP46A4.A2023001.h12v11.002.2025161112706.h5"},
        {"name": "VNP46A4.A2023001.h13v11.002.2025161112706.h5"}]}
    srv.script["/api/v2/content/details/allData/5200/VNP46A4/2023/001?format=json"] = [
        (200, json.dumps(listing).encode(), {})]
    name, url = laads_find_file("VNP46A4", 2023, 1, "h13v11", base=srv.url, sleep=lambda s: None)
    assert name.startswith("VNP46A4.A2023001.h13v11.002")
    assert url == f"{srv.url}/api/v2/content/archives/allData/5200/VNP46A4/2023/001/{name}"


def test_laads_listing_missing_tile_raises(srv):
    srv.script["/api/v2/content/details/allData/5200/VNP46A4/2023/001?format=json"] = [
        (200, json.dumps({"content": []}).encode(), {})]
    with pytest.raises(DownloadFailed):
        laads_find_file("VNP46A4", 2023, 1, "h13v11", base=srv.url, sleep=lambda s: None)
