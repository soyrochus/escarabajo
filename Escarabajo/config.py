"""Configuration helpers for Escarabajo."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

try:  # pragma: no-cover - exercised indirectly
    import yaml  # type: ignore
except Exception:  # pragma: no-cover - we fall back to json representation
    yaml = None  # type: ignore

CONFIG_DIR_NAME = ".Escarabajo"
CONFIG_FILE_NAME = "config.yaml"
DEFAULT_KB_DIR = "kb"

_DEFAULT_CONFIG: Dict[str, Any] = {
    "kb_dir": f"{CONFIG_DIR_NAME}/{DEFAULT_KB_DIR}",
    "globs": ["**/*.docx", "**/*.pptx", "**/*.pdf"],
    "exclude_globs": [
        ".git/**",
        ".Escarabajo/**",
        "node_modules/**",
        "**/~$*",
        "**/*.tmp",
    ],
    "ocr": False,
    "expose_content": False,
    "skip_unchanged": False,
    "pdf": {
        "keep_figures_as_captions": True,
        "page_delimiter": "--- page {n} ---",
    },
    "pptx": {
        "slide_delimiter": "--- slide {n} ---",
    },
    "docx": {
        "keep_tables": True,
    },
}


@dataclass(frozen=True)
class ConfigPaths:
    """Resolved configuration-related paths for a repository."""

    root: Path
    config_dir: Path
    config_file: Path
    kb_root: Path


def resolve_paths(repo_root: Path, config: Dict[str, Any] | None = None) -> ConfigPaths:
    """Resolve important filesystem paths for the given repository."""

    root = repo_root.resolve()
    config_dir = root / CONFIG_DIR_NAME
    kb_rel = (config or {}).get("kb_dir") or _DEFAULT_CONFIG["kb_dir"]
    kb_root = (root / kb_rel).resolve()
    return ConfigPaths(root=root, config_dir=config_dir, config_file=config_dir / CONFIG_FILE_NAME, kb_root=kb_root)


def ensure_config(repo_root: Path) -> Dict[str, Any]:
    """Ensure the config directory and file exist; return the loaded config."""

    paths = resolve_paths(repo_root)
    paths.config_dir.mkdir(parents=True, exist_ok=True)
    if not paths.config_file.exists():
        save_config(paths.config_file, _DEFAULT_CONFIG)
    return load_config(repo_root)


def load_config(repo_root: Path) -> Dict[str, Any]:
    """Load configuration, overlaying defaults for missing values."""

    paths = resolve_paths(repo_root)
    config: Dict[str, Any] = {}
    if paths.config_file.exists():
        raw = paths.config_file.read_text("utf-8")
        config = _parse_config_text(raw)
    merged = _merge_dicts(_DEFAULT_CONFIG, config)
    kb_paths = resolve_paths(repo_root, merged)
    # ensure kb directory exists so sync tools have a target
    kb_paths.kb_root.mkdir(parents=True, exist_ok=True)
    return merged


def save_config(path: Path, config: Dict[str, Any]) -> None:
    """Persist configuration to the given path using YAML when available."""

    serialized = _dump_config_text(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialized, encoding="utf-8")


def update_config(repo_root: Path, updates: Dict[str, Any]) -> Dict[str, Any]:
    """Apply partial updates and persist the resulting configuration."""

    config = load_config(repo_root)
    merged = _merge_dicts(config, updates)
    paths = resolve_paths(repo_root, merged)
    save_config(paths.config_file, merged)
    paths.kb_root.mkdir(parents=True, exist_ok=True)
    return merged


def _merge_dicts(base: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge dictionaries."""

    result: Dict[str, Any] = {}
    for key in set(base) | set(overrides):
        if key in overrides:
            override_value = overrides[key]
            base_value = base.get(key)
            if isinstance(base_value, dict) and isinstance(override_value, dict):
                result[key] = _merge_dicts(base_value, override_value)
            else:
                result[key] = override_value
        else:
            result[key] = base[key]
    return result


def _parse_config_text(text: str) -> Dict[str, Any]:
    if not text.strip():
        return {}
    if yaml is not None:
        data = yaml.safe_load(text)
        return data or {}
    # Fall back to JSON for environments without PyYAML.
    return json.loads(text)


def _dump_config_text(data: Dict[str, Any]) -> str:
    if yaml is not None:
        # sort keys for stability
        return yaml.safe_dump(data, sort_keys=True)
    return json.dumps(data, indent=2)


def config_dir(repo_root: Path) -> Path:
    """Return the Escarabajo configuration directory."""

    return resolve_paths(repo_root).config_dir


def kb_dir(repo_root: Path) -> Path:
    """Return the knowledge base directory."""

    config = load_config(repo_root)
    return resolve_paths(repo_root, config).kb_root


__all__ = [
    "CONFIG_DIR_NAME",
    "CONFIG_FILE_NAME",
    "DEFAULT_KB_DIR",
    "ConfigPaths",
    "ensure_config",
    "load_config",
    "save_config",
    "update_config",
    "config_dir",
    "kb_dir",
    "resolve_paths",
]
