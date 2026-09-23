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


READS_THROUGH_GRYPHON = pytest.mark.django_db(transaction=True, databases=["default", "search_readonly"])
SENTINEL = "teleport__teleport_cluster"


def _import_bundle() -> None:
    from tap_auth.actors import BOOTLOADER, get_builtin_actor
    from tap_grid.grift import grift_import

    result = grift_import(_doc(), dangling_edge_mode="strict", actor=get_builtin_actor(BOOTLOADER))
    assert result.success, [(e.phase, e.path, e.message) for e in result.errors]


def _run(spec: dict, inputs: dict) -> dict:
    """One bundle search through the real search path, as the graph panel runs it."""
    from tap_grid.models import Search
    from tap_grid.search import execute_search

    env = execute_search(Search.objects.get(entity_id=spec["entity"]["entity_id"]), inputs=inputs)
    return env.get("results", env)


def _touched(env: dict) -> set[str]:
    """Every entity id an envelope draws: its nodes and both ends of its edges."""
    ids = {str(n["entity_id"]) for n in env.get("nodes", [])}
    for e in env.get("edges", []):
        ed = e.get("data") or e
        ids |= {str(ed["from_entity_id"]), str(ed["to_entity_id"])}
    return ids


def test_every_search_takes_the_cluster_name_with_the_every_cluster_default() -> None:
    """req-teleport-page-6: one input, `cluster`, defaulting to the type slug; every search filters on it."""
    for s in _nodes(_doc(), "search"):
        schema = s["node"]["input_schema"]
        assert set(schema["properties"]) == {"cluster"}, s["entity"]["name"]
        assert schema["properties"]["cluster"]["default"] == SENTINEL
        assert "$cluster" in " ".join(s["node"]["definition"]["query"]), s["entity"]["name"]


@READS_THROUGH_GRYPHON
def test_bundle_imports_and_scene_searches_run() -> None:
    from tap_plugin.teleport.tests import _design

    _import_bundle()
    ids = _design.seed()
    counts = {}
    for s in _nodes(_doc(), "search"):
        env = _run(s, {"cluster": _design.CLUSTER})
        # Count the edge the search is named for; a path routed through the cluster also carries
        # the BELONGS_TO_CLUSTER edges it walked, which the members search draws anyway.
        drawn = [e for e in env.get("edges", []) if (e.get("data") or e)["edge_type"] != "BELONGS_TO_CLUSTER__teleport"]
        counts[s["entity"]["name"]] = (len(env.get("nodes", [])), len(drawn or env.get("edges", [])))
    # stg and the leaf that trusts it; the clusters search returns only the one asked for.
    assert counts["teleport — clusters"][0] == 1
    assert counts["teleport — trusts-root-cluster"] == (2, 1)
    member_nodes, member_edges = counts["teleport — members"]
    assert member_edges == member_nodes - 1  # every member + the one cluster they belong to
    assert counts["teleport — calls-auth-api"] == (4, 4)
    assert counts["teleport — serves-resource"] == (3, 2)
    assert ids


@READS_THROUGH_GRYPHON
def test_every_search_answers_for_one_cluster() -> None:
    """req-teleport-page-6: with two clusters and an edge of every drawn type crossing between them,
    each search returns the chosen cluster's records and none of the other's, in both directions."""
    from tap_plugin.teleport.tests import _design

    _import_bundle()
    ids = _design.seed()
    prod = set(_design.seed_second(ids).values())
    stg = set(ids.values()) - prod - {ids["leaf"]}
    for s in _nodes(_doc(), "search"):
        name = s["entity"]["name"]
        env = _run(s, {"cluster": _design.CLUSTER})
        assert env.get("nodes"), f"{name}: nothing for {_design.CLUSTER}"
        assert not _touched(env) & prod, f"{name}: drew prod records on stg's page"
        other = _run(s, {"cluster": _design.OTHER})
        if name != "teleport — trusts-root-cluster":  # prod trusts nothing
            assert other.get("nodes"), f"{name}: nothing for {_design.OTHER}"
        assert not _touched(other) & stg, f"{name}: drew stg records on prod's page"


@READS_THROUGH_GRYPHON
def test_absent_cluster_means_every_cluster() -> None:
    """req-teleport-page-6: ?cluster absent falls back to the schema default, which matches every cluster."""
    from tap_plugin.teleport.tests import _design

    _import_bundle()
    ids = _design.seed()
    _design.seed_second(ids)
    specs = {s["entity"]["name"]: s for s in _nodes(_doc(), "search")}
    every = _run(specs["teleport — clusters"], {})
    assert {n["name"] for n in every["nodes"]} == {"stg", "leaf", "prod"}
    members = _run(specs["teleport — members"], {})
    assert {ids["auth-a"], ids["prod-auth"]} <= _touched(members)
    assert {n["name"] for n in _run(specs["teleport — clusters"], {"cluster": "prod"})["nodes"]} == {"prod"}


@READS_THROUGH_GRYPHON
def test_cluster_name_is_matched_exactly() -> None:
    """req-teleport-page-6: ?cluster=a does not also match a cluster named aba."""
    from tap_plugin.teleport.tests import _design

    _import_bundle()
    a = _design.node("teleport__teleport_cluster", {"name": "a"})
    aba = _design.node("teleport__teleport_cluster", {"name": "aba"})
    a_auth = _design.member("teleport__teleport_auth_server", {"name": "a-auth"}, a, "a")
    aba_auth = _design.member("teleport__teleport_auth_server", {"name": "aba-auth"}, aba, "aba")
    specs = {s["entity"]["name"]: s for s in _nodes(_doc(), "search")}
    assert {n["name"] for n in _run(specs["teleport — clusters"], {"cluster": "a"})["nodes"]} == {"a"}
    got = _touched(_run(specs["teleport — members"], {"cluster": "a"}))
    assert a_auth in got and aba_auth not in got


def test_graph_nav_rule_encodes_the_cluster_name() -> None:
    """req-teleport-page-6: the picker tile's link carries the name percent-encoded, so a name with
    `&`, `#` or a space opens that cluster's page and adds no other parameter."""
    from tap_viz.panels.graph_panel import _fill_url_template

    (panel,) = [p for p in _nodes(_doc(), "panel") if p["node"]["slug"] == "teleport-deployment"]
    (rule,) = panel["node"]["config"]["nav_rules"]
    url = _fill_url_template(rule["url_template"], {"entity_id": "x", "data": {"name": "a&b #c"}})
    assert url == "/teleport?cluster=a%26b%20%23c"
