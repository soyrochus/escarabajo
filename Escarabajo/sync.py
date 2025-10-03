"""High level synchronisation orchestrator for Escarabajo."""

from __future__ import annotations

from pathlib import Path
from time import perf_counter
from typing import Dict, Iterable, List

from .config import ensure_config, load_config, resolve_paths, update_config
from .extract import SUPPORTED_TYPES, extract_to_markdown
from .fsutil import (
    atomic_write,
    file_lock,
    isoformat,
    readable_size,
    repo_relative,
    scan_with_globs,
    sha256_of,
)
from .indexdb import IndexDatabase, IndexRecord


class SyncManager:
    """Handles repository scanning, extraction, and bookkeeping."""

    def __init__(self, repo_root: Path):
        self.root = repo_root.resolve()
        self.config = ensure_config(self.root)
        self.paths = resolve_paths(self.root, self.config)
        self.lock_dir = self.paths.config_dir / "locks"
        self.lock_dir.mkdir(parents=True, exist_ok=True)
        self.index = IndexDatabase(self.root, self.config.get("kb_dir", ".Escarabajo/kb"))

    # ------------------------------------------------------------------
    # Configuration helpers
    def reload_config(self) -> Dict[str, object]:
        self.config = load_config(self.root)
        self.paths = resolve_paths(self.root, self.config)
        self.lock_dir = self.paths.config_dir / "locks"
        self.lock_dir.mkdir(parents=True, exist_ok=True)
        self.index = IndexDatabase(self.root, self.config.get("kb_dir", ".Escarabajo/kb"))
        return self.config

    def apply_config_update(self, updates: Dict[str, object]) -> Dict[str, object]:
        new_config = update_config(self.root, updates)
        self.config = new_config
        self.paths = resolve_paths(self.root, self.config)
        self.index = IndexDatabase(self.root, self.config.get("kb_dir", ".Escarabajo/kb"))
        return new_config

    def config_get(self) -> Dict[str, object]:
        return dict(self.config)

    def config_set(self, updates: Dict[str, object]) -> Dict[str, object]:
        return self.apply_config_update(updates)

    # ------------------------------------------------------------------
    # Core operations
    def scan_repo(self, *, globs: List[str] | None = None, exclude_globs: List[str] | None = None) -> List[Dict[str, str]]:
        config_globs = globs or list(self.config.get("globs", []))
        config_excludes = exclude_globs or list(self.config.get("exclude_globs", []))
        matches = scan_with_globs(self.root, config_globs, config_excludes)
        return [{"src": str(path.as_posix())} for path in matches]

    def sync_all(
        self,
        *,
        globs: List[str] | None = None,
        exclude_globs: List[str] | None = None,
        ocr: bool | None = None,
    ) -> Dict[str, object]:
        candidates = [entry["src"] for entry in self.scan_repo(globs=globs, exclude_globs=exclude_globs)]
        results = self.sync_paths(candidates, ocr=ocr)
        processed = len(results["results"])
        ok = sum(1 for item in results["results"] if item.get("status") == "ok")
        skipped = sum(1 for item in results["results"] if item.get("status") == "skipped")
        errors = sum(1 for item in results["results"] if item.get("status") == "error")
        out_paths = [item["out"] for item in results["results"] if item.get("out")]
        return {
            "processed": processed,
            "ok": ok,
            "skipped": skipped,
            "errors": errors,
            "out_paths": out_paths,
        }

    def sync_paths(self, paths: Iterable[str], *, ocr: bool | None = None) -> Dict[str, List[Dict[str, object]]]:
        seen: set[str] = set()
        results: List[Dict[str, object]] = []
        for path in paths:
            if path in seen:
                continue
            seen.add(path)
            result = self._sync_single(path, ocr=ocr)
            results.append(result)
        self.index.write()
        return {"results": results}

    def get_text_path(self, src: str, *, ocr: bool | None = None) -> Dict[str, str]:
        result = self._sync_single(src, ocr=ocr)
        self.index.write()
        if result.get("status") != "ok" and result.get("status") != "skipped":
            raise RuntimeError(result.get("reason") or f"Failed to extract {src}")
        return {"out": result["out"]}

    def list_kb(self) -> Dict[str, List[Dict[str, str]]]:
        items: List[Dict[str, str]] = []
        kb_root = self.paths.kb_root
        if not kb_root.exists():
            return {"items": []}
        for markdown_path in sorted(kb_root.rglob("*.md")):
            out_rel = markdown_path.relative_to(self.root).as_posix()
            items.append({"out": out_rel})
        return {"items": items}

    def purge_outputs(self, *, globs: List[str] | None = None) -> Dict[str, List[str]]:
        kb_root = self.paths.kb_root
        patterns = globs or ["**/*.md"]
        deleted: List[str] = []
        for pattern in patterns:
            for path in kb_root.glob(pattern):
                if path.is_file():
                    path.unlink()
                    deleted.append(path.relative_to(self.root).as_posix())
        return {"deleted": sorted(set(deleted))}

    def read_text(self, out: str, *, max_bytes: int | None = None) -> Dict[str, object]:
        if not self.config.get("expose_content", False):
            raise RuntimeError("Content exposure disabled by configuration")
        relative = repo_relative(Path(out), self.root)
        target = self.root / relative
        if not target.exists() or not target.is_file():
            raise FileNotFoundError(f"Output {out} does not exist")
        data = target.read_bytes()
        truncated = False
        if max_bytes is not None and len(data) > max_bytes:
            data = data[:max_bytes]
            truncated = True
        return {
            "content": data.decode("utf-8", errors="replace"),
            "truncated": truncated,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    def _lock_path(self, relative: Path) -> Path:
        safe_name = relative.as_posix().replace("/", "__")
        return self.lock_dir / f"{safe_name}.lock"

    def _output_path(self, relative: Path) -> Path:
        if len(relative.parts) > 1:
            target_dir = Path(*relative.parts[:-1])
        else:
            target_dir = Path()
        filename = relative.name + ".md"
        if str(target_dir):
            return self.paths.kb_root / target_dir / filename
        return self.paths.kb_root / filename

    def _output_relpath(self, relative: Path) -> str:
        kb_dir = Path(self.config.get("kb_dir", ".Escarabajo/kb"))
        if len(relative.parts) > 1:
            target_dir = Path(*relative.parts[:-1])
        else:
            target_dir = Path()
        filename = relative.name + ".md"
        if str(target_dir):
            rel = kb_dir / target_dir / filename
        else:
            rel = kb_dir / filename
        return rel.as_posix()

    def _sync_single(self, src: str, *, ocr: bool | None = None) -> Dict[str, object]:
        try:
            relative = repo_relative(Path(src), self.root)
        except Exception as exc:
            return {
                "src": src,
                "out": "",
                "status": "error",
                "reason": str(exc),
            }

        src_path = self.root / relative
        if not src_path.exists():
            return {
                "src": relative.as_posix(),
                "out": "",
                "status": "error",
                "reason": "Source file does not exist",
            }

        if src_path.suffix.lower() not in SUPPORTED_TYPES:
            return {
                "src": relative.as_posix(),
                "out": "",
                "status": "error",
                "reason": f"Unsupported extension {src_path.suffix}",
            }

        out_path = self._output_path(relative)
        out_rel = self._output_relpath(relative)
        lock_path = self._lock_path(relative)
        skip_unchanged = bool(self.config.get("skip_unchanged", False))

        status = "ok"
        reason = None
        duration_ms = 0
        start = perf_counter()

        with file_lock(lock_path):
            try:
                if skip_unchanged and out_path.exists():
                    src_mtime = src_path.stat().st_mtime
                    out_mtime = out_path.stat().st_mtime
                    if src_mtime <= out_mtime:
                        status = "skipped"
                if status != "skipped":
                    markdown = extract_to_markdown(src_path, self.config, ocr=ocr)
                    atomic_write(out_path, markdown)
                duration_ms = int((perf_counter() - start) * 1000)
            except Exception as exc:  # capture extraction error
                status = "error"
                reason = str(exc)
                duration_ms = int((perf_counter() - start) * 1000)

        bytes_in = readable_size(src_path)
        bytes_out = readable_size(out_path)
        src_mtime_iso = isoformat(src_path.stat().st_mtime)
        out_mtime_iso = isoformat(out_path.stat().st_mtime) if out_path.exists() else None
        src_hash = sha256_of(src_path) if src_path.exists() else None
        out_hash = sha256_of(out_path) if out_path.exists() else None

        record = IndexRecord(
            src=relative.as_posix(),
            out=out_rel,
            status=status,
            reason=reason,
            src_mtime=src_mtime_iso,
            out_mtime=out_mtime_iso,
            src_sha256=src_hash,
            out_sha256=out_hash,
            bytes_in=bytes_in,
            bytes_out=bytes_out,
            duration_ms=duration_ms,
        )
        self.index.update(record)

        return {
            "src": relative.as_posix(),
            "out": out_rel,
            "status": status,
            "reason": reason,
        }


__all__ = ["SyncManager"]
