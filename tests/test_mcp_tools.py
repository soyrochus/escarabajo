"""Integration smoke tests for the Escarabajo MCP surface."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.mcp_client import MiniMCPClient


REPO_ROOT = Path(__file__).resolve().parents[1]
AUTHORITATIVE_SRCS = {
    "tests/data/RNGenius_Functional_Spec.docx",
    "tests/data/RNGenius_Philosophy.pptx",
    "tests/data/RNGenius_User_Manual.pdf",
}


@pytest.fixture(scope="session")
def client() -> MiniMCPClient:
    return MiniMCPClient(REPO_ROOT)


def test_scan_repo_returns_expected_sources(client: TestMCPClient) -> None:
    payload = client.call("scan_repo")
    discovered = {item["src"] for item in payload}
    assert AUTHORITATIVE_SRCS <= discovered


@pytest.mark.parametrize("src", sorted(AUTHORITATIVE_SRCS))
def test_get_text_path_returns_existing_markdown(client: TestMCPClient, src: str) -> None:
    response = client.call("get_text_path", {"src": src})
    out_path = REPO_ROOT / response["out"]
    assert out_path.is_file()


def test_list_kb_reports_generated_markdown(client: TestMCPClient) -> None:
    payload = client.call("list_kb")
    outputs = {item["out"] for item in payload["items"]}
    expected = {f".Escarabajo/kb/{path}.md" for path in AUTHORITATIVE_SRCS}
    assert expected <= outputs


def test_sync_paths_reports_success(client: TestMCPClient) -> None:
    response = client.call("sync_paths", {"paths": sorted(AUTHORITATIVE_SRCS)})
    statuses = {item["status"] for item in response["results"]}
    assert statuses <= {"ok", "skipped"}


def test_prompts_are_available(client: TestMCPClient) -> None:
    payload = client.call("list_prompts")
    prompts = set(payload["names"])
    expected = {
        "doc.summarize",
        "doc.extract_requirements",
        "ppt.to_outline",
        "pdf.policy_risk",
        "kb.crosslink",
    }
    assert expected <= prompts
    template = client.call("get_prompt", {"name": "doc.summarize"})
    assert "TL;DR" in template["template"]
