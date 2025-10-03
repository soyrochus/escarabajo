"""Index management for Escarabajo."""

from __future__ import annotations

import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List

from . import __version__
from .fsutil import file_lock, isoformat, load_json, write_json

INDEX_FILE = "index.json"


@dataclass
class IndexRecord:
    src: str
    out: str
    status: str
    reason: str | None
    src_mtime: str | None
    out_mtime: str | None
    src_sha256: str | None
    out_sha256: str | None
    bytes_in: int
    bytes_out: int
    duration_ms: int


class IndexDatabase:
    """Simple JSON-backed index for synchronisation metadata."""

    def __init__(self, repo_root: Path, kb_dir: str):
        self.repo_root = repo_root
        self.kb_dir = kb_dir
        self.index_path = repo_root / ".Escarabajo" / INDEX_FILE
        self._records: Dict[str, IndexRecord] = {}
        self._load()

    def _load(self) -> None:
        data = load_json(self.index_path)
        entries = data.get("files", []) if isinstance(data, dict) else []
        for entry in entries:
            try:
                record = IndexRecord(
                    src=entry["src"],
                    out=entry.get("out", ""),
                    status=entry.get("status", "unknown"),
                    reason=entry.get("reason"),
                    src_mtime=entry.get("src_mtime"),
                    out_mtime=entry.get("out_mtime"),
                    src_sha256=entry.get("src_sha256"),
                    out_sha256=entry.get("out_sha256"),
                    bytes_in=int(entry.get("bytes_in", 0)),
                    bytes_out=int(entry.get("bytes_out", 0)),
                    duration_ms=int(entry.get("duration_ms", 0)),
                )
            except Exception:
                continue
            self._records[record.src] = record

    def update(self, record: IndexRecord) -> None:
        self._records[record.src] = record

    def write(self) -> None:
        files = [asdict(self._records[key]) for key in sorted(self._records)]
        payload = {
            "version": 1,
            "generated_at": isoformat(time.time()),
            "kb_dir": self.kb_dir,
            "server_version": __version__,
            "files": files,
        }
        with file_lock(self.index_path.with_suffix(self.index_path.suffix + ".lock")):
            write_json(self.index_path, payload)

    def list_records(self) -> List[IndexRecord]:
        return [self._records[key] for key in sorted(self._records)]


__all__ = ["IndexDatabase", "IndexRecord", "INDEX_FILE"]
