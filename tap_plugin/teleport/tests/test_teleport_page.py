"""The /teleport page bundle (req-teleport-page, req-teleport-layout-deployment): schema-valid,
hotlink-exact, importable, every scene search runs and names the edge type it draws, and the layout
module names only edge types this plugin ships."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from tap_grid.grift.importer import validate_grift_document

PKG = Path(__file__).resolve().parents[1]
BUNDLE = PKG / "grift" / "page.grift.json"
LAYOUT_JS = PKG / "static" / "teleport" / "js" / "projections" / "teleport-deployment.js"


def _doc() -> dict:
    return json.loads(BUNDLE.read_text())


def _nodes(doc: dict, etype: str) -> list[dict]:
    return [n for b in doc["batches"] for n in b["nodes"] if n["entity"]["entity_type"] == etype]


def test_bundle_validates() -> None:
    assert validate_grift_document(_doc()) == []


def test_slots_match_uses_panel_edges_exactly() -> None:
    doc = _doc()
    (page,) = _nodes(doc, "page")
    slots = {row["panel-id"] for col in page["node"]["layout"]["columns"].values() for row in col["rows"].values()}
    values = {e["edge"]["properties"]["hotlink"]["value"] for b in doc["batches"] for e in b["edges"] if e["edge"]["edge_type"] == "USES_PANEL"}
    assert slots == values
    assert page["node"]["slug"] == "/teleport"


def test_scene_searches_name_their_edge_types() -> None:
    """No unfiltered edge search: every search that draws an edge names its type, and every edge type
    the layout draws has a search."""
    manifest = (PKG / "tap-plugin.toml").read_text()
    shipped = set(re.findall(r"^([A-Z_]+__teleport) =", manifest, re.M))
    searched = set()
    for s in _nodes(_doc(), "search"):
        query = " ".join(s["node"]["definition"]["query"])
        searched |= set(re.findall(r"\[:([A-Z_]+__teleport)\]", query))
        assert "[]" not in query and "-[e]-" not in query
    drawn = set(re.findall(r'"([A-Z_]+__teleport)"', LAYOUT_JS.read_text()))
    assert drawn <= shipped, drawn - shipped
    assert drawn <= searched, drawn - searched
    assert (PKG / "static" / "teleport" / "js" / "projections" / "teleport-deployment.js").exists()


def test_board_panels_name_known_sections() -> None:
    from tap_plugin.teleport.panels.board import SECTIONS

    sections = [p["node"]["config"]["section"] for p in _nodes(_doc(), "panel") if p["node"]["view"] == "teleport/panels/board.html"]
    assert sorted(sections) == sorted(SECTIONS)


@pytest.mark.django_db(transaction=True, databases=["default", "search_readonly"])
def test_bundle_imports_and_scene_searches_run() -> None:
    from tap_plugin.teleport.tests import _design

    from tap_auth.actors import BOOTLOADER, get_builtin_actor
    from tap_grid.grift import grift_import
    from tap_grid.gryphon.executor import execute_gryphon_raw

    result = grift_import(_doc(), dangling_edge_mode="strict", actor=get_builtin_actor(BOOTLOADER))
    assert result.success, [(e.phase, e.path, e.message) for e in result.errors]
    ids = _design.seed()
    counts = {}
    for s in _nodes(_doc(), "search"):
        env = execute_gryphon_raw("\n".join(s["node"]["definition"]["query"]), {}, layer="full")
        counts[s["entity"]["name"]] = (len(env.get("nodes", [])), len(env.get("edges", [])))
    # Two clusters; the members search leaves the identity and policy planes out.
    assert counts["teleport — clusters"][0] == 2
    member_nodes, member_edges = counts["teleport — members"]
    assert member_edges == member_nodes - 1  # every member + the one cluster they belong to
    assert counts["teleport — calls-auth-api"] == (4, 4)
    assert counts["teleport — serves-resource"] == (3, 2)
    assert ids
