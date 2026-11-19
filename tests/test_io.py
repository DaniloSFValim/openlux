"""Testes de integridade de arquivos. Arquivos aqui sao SINTETICOS (apenas para teste)."""
import hashlib

import h5py
import numpy as np
import pytest

from openlux.io import InvalidDownload, is_hdf5, sha256_file, verify_hdf5


def test_sha256_matches_hashlib(tmp_path):
    p = tmp_path / "a.bin"
    p.write_bytes(b"openlux" * 1000)
    assert sha256_file(p) == hashlib.sha256(b"openlux" * 1000).hexdigest()


def test_real_hdf5_is_accepted(tmp_path):
    p = tmp_path / "ok.h5"
    with h5py.File(p, "w") as f:
        f.create_dataset("x", data=np.arange(4))
    assert is_hdf5(p)
    verify_hdf5(p)


def test_html_login_page_is_rejected(tmp_path):
    # Caso real observado: a LAADS devolve a pagina de login (HTML) em vez do dado.
    p = tmp_path / "fake.h5"
    p.write_text("<!DOCTYPE html><html>login</html>")
    assert not is_hdf5(p)
    with pytest.raises(InvalidDownload):
        verify_hdf5(p)


def test_proxy_error_body_is_rejected(tmp_path):
    p = tmp_path / "err.h5"
    p.write_bytes(b"upstream request failed")
    with pytest.raises(InvalidDownload):
        verify_hdf5(p)


def test_missing_file_is_rejected(tmp_path):
    with pytest.raises(InvalidDownload):
        verify_hdf5(tmp_path / "nao_existe.h5")
