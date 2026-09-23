"""Edge-type tests (req-teleport-edges): every shipped edge is declared, closed where it names teleport
types, open where it reaches another platform, carries a closed property schema, and stamps its plane."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from tap_grid.caller_context import CallerContext
from tap_grid.services import WriteOperation, write_batch

PKG = Path(__file__).resolve().parents[1]
EDGE_FILES = sorted((PKG / "edges").glob("*.edge.json"))
#: Edges whose far end is another platform's type and is therefore left open (no targets).
OPEN_TARGETS = {
    "RUNS_ON_COMPUTE__teleport", "STORES_CLUSTER_STATE__teleport", "WRITES_AUDIT_EVENTS__teleport",
    "UPLOADS_SESSION_RECORDINGS__teleport", "ADMITS_IDENTITY__teleport", "SIGNS_WITH_KEY__teleport",
    "FRONTS_TARGET__teleport", "DELEGATES_LOGIN__teleport",
}
PLANES = {"deployment", "trust", "identity", "policy", "resource"}


def _defs() -> dict[str, dict]:
    return {json.loads(p.read_text())["slug"]: json.loads(p.read_text()) for p in EDGE_FILES}


def test_every_edge_file_is_in_the_manifest_and_articled() -> None:
    """req-teleport-edges-1."""
    manifest = (PKG / "tap-plugin.toml").read_text()
    declared = dict(re.findall(r'^([A-Z_]+__teleport) = "(edges/[A-Z_]+\.edge\.json)"', manifest, re.M))
    defs = _defs()
    assert set(declared) == set(defs)
    for slug in defs:
        assert declared[slug] == f"edges/{slug.split('__')[0]}.edge.json"
        assert (PKG / "domain" / f"{slug.split('__')[0]}.md").exists(), slug


def test_open_ends_are_exactly_the_cross_platform_edges() -> None:
    """req-teleport-edges-2: an end is open only where it reaches another plugin's types; every closed
    end names teleport types only, so the plugin declares no vocabulary dependency."""
    for slug, d in _defs().items():
        assert all(t.startswith("teleport__") for t in d.get("sources", [])), slug
        assert all(t.startswith("teleport__") for t in d.get("targets", [])), slug
        assert ("targets" not in d) == (slug in OPEN_TARGETS), slug
        assert "sources" in d, slug


def test_property_schemas_are_closed_and_planes_stamped() -> None:
    """req-teleport-edges-3 / -4."""
    for slug, d in _defs().items():
        if "property_schema" in d:
            assert d["property_schema"].get("additionalProperties") is False, slug
            assert "hotlink" not in d["property_schema"].get("properties", {}), slug
        assert d["default_dimensions"].get("teleport.plane") in PLANES, slug


def _node(t: str, payload: dict) -> str:
    r = write_batch([WriteOperation(verb="create_node", type_slug=t, payload=payload)], caller_context=CallerContext()).results[0]
    assert r.success, r
    return str(r.entity_id)


def _edge(src: str, dst: str, et: str, props: dict | None = None):
    payload = {"properties": props} if props else {}
    return write_batch(
        [WriteOperation(verb="create_edge", from_target=src, to_target=dst, edge_type=et, payload=payload)],
        caller_context=CallerContext(),
    ).results[0]


@pytest.mark.django_db
def test_endpoints_and_properties_are_enforced() -> None:
    """req-teleport-edges-2 / -3 / -4 through the service layer."""
    from tap_grid.models import Entity

    cluster = _node("teleport__teleport_cluster", {"name": "stg"})
    role = _node("teleport__teleport_role", {"name": "access", "cluster_name": "stg"})
    user = _node("teleport__teleport_user", {"name": "alice", "cluster_name": "stg"})
    ok = _edge(user, cluster, "BELONGS_TO_CLUSTER__teleport")
    assert ok.success, ok
    assert Entity.objects.get(id=ok.entity_id).dimensions.get("teleport.plane") == "deployment"
    assert _edge(user, role, "HOLDS_ROLE__teleport", {"granted_by": "static"}).success
    assert not _edge(user, role, "HOLDS_ROLE__teleport", {"granted_by": "magic"}).success
    assert not _edge(user, role, "HOLDS_ROLE__teleport", {"why": "x"}).success
    # An open end takes any node type: here a cluster stands in for the cloud target.
    db = _node("teleport__teleport_database", {"name": "db", "cluster_name": "stg"})
    assert _edge(db, cluster, "FRONTS_TARGET__teleport").success


@pytest.mark.django_db
def test_closed_endpoint_lists_are_declarative_for_unconstrained_nodes() -> None:
    """req-teleport-edges-5: teleport's models declare no OUTBOUND_EDGES (the estate convention), and
    the grid's permission union lets an unconstrained node create any edge — so an edge file's
    closed sources/targets document the vocabulary but do not refuse a write. This test pins that
    behaviour so the day the grid tightens it, the spec's statement is revisited, not silently wrong."""
    role = _node("teleport__teleport_role", {"name": "r", "cluster_name": "stg"})
    assert _edge(role, role, "HOLDS_ROLE__teleport").success
