"""Command line interface for Escarabajo."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from .prompts import get_prompt, list_prompts
from .sync import SyncManager


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Escarabajo document synchroniser")
    sub = parser.add_subparsers(dest="command")

    scan = sub.add_parser("scan", help="Scan the repository for supported documents")
    scan.add_argument("--globs", nargs="*", help="Glob patterns to include")
    scan.add_argument("--exclude-globs", nargs="*", help="Glob patterns to exclude")

    sync = sub.add_parser("sync", help="Synchronise documents to Markdown")
    sync.add_argument("--globs", nargs="*", help="Glob patterns to include")
    sync.add_argument("--exclude-globs", nargs="*", help="Glob patterns to exclude")
    sync.add_argument("--ocr", action="store_true", help="Enable OCR when processing PDFs")

    sync_paths = sub.add_parser("sync-paths", help="Synchronise specific paths")
    sync_paths.add_argument("paths", nargs="+", help="Paths to process")
    sync_paths.add_argument("--ocr", action="store_true", help="Enable OCR when processing PDFs")

    get_path = sub.add_parser("get-path", help="Ensure Markdown exists and print its path")
    get_path.add_argument("--src", required=True, help="Source document path")
    get_path.add_argument("--ocr", action="store_true", help="Enable OCR when processing PDFs")

    list_kb = sub.add_parser("list-kb", help="List available Markdown outputs")
    list_kb.add_argument("--json", action="store_true", help="Emit machine readable JSON")

    purge = sub.add_parser("purge", help="Delete generated Markdown")
    purge.add_argument("--globs", nargs="*", help="Glob expressions to delete")

    cfg_get = sub.add_parser("config-get", help="Print the active configuration")

    cfg_set = sub.add_parser("config-set", help="Update configuration values")
    cfg_set.add_argument("--set", dest="items", action="append", default=[], help="key=value pairs to set")

    prompts = sub.add_parser("prompts", help="Interact with the prompt pack")
    prompts.add_argument("--list", action="store_true", help="List prompt names")
    prompts.add_argument("--get", metavar="NAME", help="Retrieve a prompt template")

    read_text = sub.add_parser("read-text", help="Read Markdown output when expose_content=true")
    read_text.add_argument("--out", required=True, help="Output path to read")
    read_text.add_argument("--max-bytes", type=int, help="Limit number of bytes returned")

    return parser


def _parse_set_items(items: list[str]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for item in items:
        if "=" not in item:
            raise ValueError(f"Invalid --set entry '{item}', expected key=value")
        key, value = item.split("=", 1)
        result[key.strip()] = _auto_cast(value.strip())
    return result


def _auto_cast(value: str) -> Any:
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 0

    manager = SyncManager(Path.cwd())

    try:
        if args.command == "scan":
            payload = manager.scan_repo(globs=args.globs, exclude_globs=args.exclude_globs)
            print(json.dumps(payload, indent=2))
            return 0
        if args.command == "sync":
            payload = manager.sync_all(globs=args.globs, exclude_globs=args.exclude_globs, ocr=args.ocr)
            print(json.dumps(payload, indent=2))
            return 0 if payload["errors"] == 0 else 3
        if args.command == "sync-paths":
            payload = manager.sync_paths(args.paths, ocr=args.ocr)
            print(json.dumps(payload, indent=2))
            errors = [item for item in payload["results"] if item.get("status") == "error"]
            return 0 if not errors else 3
        if args.command == "get-path":
            payload = manager.get_text_path(args.src, ocr=args.ocr)
            print(payload["out"])
            return 0
        if args.command == "list-kb":
            payload = manager.list_kb()
            if args.json:
                print(json.dumps(payload, indent=2))
            else:
                for item in payload["items"]:
                    print(item["out"])
            return 0
        if args.command == "purge":
            payload = manager.purge_outputs(globs=args.globs)
            print(json.dumps(payload, indent=2))
            return 0
        if args.command == "config-get":
            print(json.dumps(manager.config_get(), indent=2))
            return 0
        if args.command == "config-set":
            updates = _parse_set_items(args.items)
            payload = manager.config_set(updates)
            print(json.dumps(payload, indent=2))
            return 0
        if args.command == "prompts":
            if args.list:
                print(json.dumps(list_prompts(), indent=2))
                return 0
            if args.get:
                print(json.dumps(get_prompt(args.get), indent=2))
                return 0
            parser.error("prompts command requires --list or --get")
        if args.command == "read-text":
            payload = manager.read_text(args.out, max_bytes=args.max_bytes)
            print(json.dumps(payload, indent=2))
            return 0
    except Exception as exc:  # pragma: no cover - CLI path
        parser.error(str(exc))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
