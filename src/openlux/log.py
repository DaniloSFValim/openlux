"""Log estruturado (JSON por linha) para scripts e pipeline.

Cada evento e um objeto JSON com ``ts`` (UTC), ``level``, ``event`` e campos livres, o que permite
auditar uma execucao (arquivos lidos, contagens, descartes) sem depender de texto livre.
Escreve em stderr e, opcionalmente, em um arquivo ``.jsonl``.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path


class JsonLogger:
    def __init__(self, path: str | Path | None = None, stream=None):
        self.stream = sys.stderr if stream is None else stream
        self.path = Path(path) if path else None
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text("", encoding="utf-8")

    def log(self, event: str, level: str = "INFO", **fields):
        rec = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), "level": level,
               "event": event, **fields}
        line = json.dumps(rec, ensure_ascii=False, default=str, sort_keys=False)
        print(line, file=self.stream)
        if self.path:
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")
        return rec

    def warn(self, event: str, **fields):
        return self.log(event, "WARNING", **fields)
