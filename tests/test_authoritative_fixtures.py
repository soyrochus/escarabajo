"""Regression tests anchored to the authoritative Escarabajo fixtures."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from Escarabajo.config import ensure_config, load_config
from Escarabajo.extract import extract_to_markdown
from Escarabajo.fsutil import sha256_of

REPO_ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = REPO_ROOT / ".Escarabajo/index.json"


def _load_authoritative_records() -> list[dict]:
    data = json.loads(INDEX_PATH.read_text("utf-8"))
    records = [entry for entry in data.get("files", []) if entry.get("status") == "ok"]
    return records


_skip_reason: str | None = None
if not INDEX_PATH.exists():
    _skip_reason = "Authoritative index.json is missing"
else:
    try:
        _records = _load_authoritative_records()
    except json.JSONDecodeError as exc:  # pragma: no cover - hard fail environment
        _skip_reason = f"Unable to parse index.json: {exc}"  # type: ignore[str-format]
    else:
        if not _records:
            _skip_reason = "Authoritative index.json contains no successful records"

if _skip_reason:
    pytestmark = pytest.mark.skip(reason=_skip_reason)
    RECORDS: list[dict] = []
else:
    RECORDS = _records


@pytest.fixture(scope="session")
def repo_config() -> dict:
    """Return the resolved Escarabajo configuration for the repository."""

    ensure_config(REPO_ROOT)
    return load_config(REPO_ROOT)


@pytest.mark.parametrize("record", RECORDS, ids=lambda record: record.get("src", "<unknown>"))
def test_index_metadata_alignment(record: dict) -> None:
    """Ensure metadata in index.json matches the on-disk authoritative artefacts."""

    src_path = REPO_ROOT / record["src"]
    out_path = REPO_ROOT / record["out"]

    assert src_path.is_file(), f"Missing source fixture: {record['src']}"
    assert out_path.is_file(), f"Missing Markdown fixture: {record['out']}"

    assert sha256_of(src_path) == record["src_sha256"], "Source SHA mismatch"
    assert sha256_of(out_path) == record["out_sha256"], "Output SHA mismatch"

    assert src_path.stat().st_size == record["bytes_in"], "Source size mismatch"
    assert out_path.stat().st_size == record["bytes_out"], "Output size mismatch"


@pytest.mark.parametrize("record", RECORDS, ids=lambda record: record.get("src", "<unknown>"))
def test_extraction_reproduces_authoritative_output(record: dict, repo_config: dict) -> None:
    """Re-run extraction for each authoritative fixture and compare with cached Markdown."""

    src_path = REPO_ROOT / record["src"]
    out_path = REPO_ROOT / record["out"]

    expected = out_path.read_text("utf-8")
    try:
        actual = extract_to_markdown(src_path, repo_config)
    except RuntimeError as exc:
        if "No PDF extraction backend available" in str(exc):  # pragma: no cover - environment guard
            pytest.skip(str(exc))
        raise

    assert actual == expected
