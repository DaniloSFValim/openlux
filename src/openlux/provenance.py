"""Registro de proveniencia: versao do codigo e escrita deterministica de JSON."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path


def write_json(path, record) -> None:
    """Escreve JSON com chaves ordenadas (saida byte-a-byte reprodutivel)."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                 encoding="utf-8")


def code_version(repo_dir=".") -> dict:
    """Commit atual e se ha alteracoes nao commitadas. ``None`` fora de um repositorio git."""
    def run(*args):
        return subprocess.run(["git", "-C", str(repo_dir), *args], capture_output=True,
                              text=True, check=True).stdout
    try:
        commit = run("rev-parse", "HEAD").strip()
        dirty = bool(run("status", "--porcelain").strip())
        return {"commit": commit, "dirty": dirty}
    except (subprocess.CalledProcessError, FileNotFoundError, NotADirectoryError):
        return {"commit": None, "dirty": None}
