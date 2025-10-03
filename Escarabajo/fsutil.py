"""Filesystem utilities used by Escarabajo."""

from __future__ import annotations

import contextlib
import fnmatch
import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator, List, Sequence


def repo_relative(path: Path, repo_root: Path) -> Path:
    """Return a normalized repo-relative path, rejecting traversal."""

    absolute = (repo_root / path).resolve() if not path.is_absolute() else path.resolve()
    try:
        relative = absolute.relative_to(repo_root.resolve())
    except ValueError as exc:  # path outside repo
        raise ValueError(f"Path '{path}' escapes repository root") from exc
    if any(part == ".." for part in relative.parts):
        raise ValueError(f"Path '{path}' is not allowed to traverse upwards")
    return relative


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def atomic_write(path: Path, data: str, encoding: str = "utf-8") -> None:
    """Write data atomically to disk."""

    ensure_parent(path)
    with tempfile.NamedTemporaryFile("w", delete=False, encoding=encoding, dir=str(path.parent)) as tmp:
        tmp.write(data)
        temp_path = Path(tmp.name)
    temp_path.replace(path)


def sha256_of(path: Path) -> str:
    """Compute the SHA-256 digest of a file."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def isoformat(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def selection_matches(path: Path, exclude_globs: Sequence[str]) -> bool:
    """Return True if the given path matches any exclusion pattern."""

    path_str = str(path.as_posix())
    return any(fnmatch.fnmatch(path_str, pattern) for pattern in exclude_globs)


def scan_with_globs(repo_root: Path, globs: Sequence[str], exclude: Sequence[str]) -> List[Path]:
    """Return matching file paths according to include/exclude globs."""

    matches: List[Path] = []
    seen: set[Path] = set()
    for pattern in globs:
        for match in repo_root.glob(pattern):
            if not match.is_file():
                continue
            relative = match.relative_to(repo_root)
            if selection_matches(relative, exclude):
                continue
            if relative in seen:
                continue
            seen.add(relative)
            matches.append(relative)
    matches.sort()
    return matches


@contextlib.contextmanager
def file_lock(lock_path: Path) -> Iterator[None]:
    """Simple advisory file lock using fcntl/msvcrt when available."""

    ensure_parent(lock_path)
    handle = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        try:
            import fcntl  # type: ignore

            fcntl.flock(handle, fcntl.LOCK_EX)
            yield
        except ModuleNotFoundError:  # pragma: no cover - Windows fallback
            import msvcrt  # type: ignore

            msvcrt.locking(handle, msvcrt.LK_LOCK, 1)
            try:
                yield
            finally:
                msvcrt.locking(handle, msvcrt.LK_UNLCK, 1)
    finally:
        os.close(handle)


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text("utf-8"))
    except json.JSONDecodeError:
        return {}


def write_json(path: Path, payload: dict) -> None:
    atomic_write(path, json.dumps(payload, indent=2, ensure_ascii=False))


def readable_size(path: Path) -> int:
    try:
        return path.stat().st_size
    except FileNotFoundError:
        return 0


def ensure_repo_root(path: Path) -> Path:
    return path.resolve()


__all__ = [
    "repo_relative",
    "ensure_parent",
    "atomic_write",
    "sha256_of",
    "isoformat",
    "selection_matches",
    "scan_with_globs",
    "file_lock",
    "load_json",
    "write_json",
    "readable_size",
    "ensure_repo_root",
]
