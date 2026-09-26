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
    end names teleport types only, so no edge file is a vocabulary dependency (the one dependency,
    identity_core, comes from a node declaration: req-teleport-person-link)."""
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
def test_off_vocabulary_endpoints_are_refused() -> None:
    """req-teleport-edges-5: every model declares OUTBOUND_EDGES (and INBOUND_EDGES where a teleport
    edge ends), its teleport edges derived from the edge files, so the permission union refuses a
    teleport edge from or to a type its definition does not name — a forged grant path cannot be
    written."""
    cluster = _node("teleport__teleport_cluster", {"name": "stg"})
    role = _node("teleport__teleport_role", {"name": "r", "cluster_name": "stg"})
    user = _node("teleport__teleport_user", {"name": "u", "cluster_name": "stg"})
    assert not _edge(role, role, "HOLDS_ROLE__teleport").success  # a role holds no role
    assert not _edge(user, cluster, "HOLDS_ROLE__teleport").success  # a cluster is not a role
    assert not _edge(role, cluster, "FRONTS_TARGET__teleport").success  # a role fronts nothing
    assert _edge(user, role, "HOLDS_ROLE__teleport").success


#: The only declared edges that are not this plugin's: (source type, edge type, target types).
FOREIGN_DECLARATIONS = {
    ("teleport__teleport_user", "HELD_BY_HUMAN__identity_core", ("identity_core__human",)),
    ("teleport__teleport_trusted_device", "REPRESENTS_HOST__computing_core", ("computing_core__host",)),
}


def test_node_constraints_match_the_edge_files() -> None:
    """The declared teleport-edge node constraints are exactly the edge files' endpoints, and the only
    foreign declarations are teleport_user's HELD_BY_HUMAN to identity_core's human and
    teleport_trusted_device's REPRESENTS_HOST to computing_core's host, so neither can drift."""
    from tap_grid.registry import get_model_class

    defs = _defs()
    manifest = (PKG / "tap-plugin.toml").read_text()
    # Every model the manifest registers, not only edge-file sources, so a foreign permission on a type
    # that starts no teleport edge is still caught.
    all_types = set(re.findall(r'^(teleport__[a-z_]+) = "', manifest, re.M))
    sources = {t for d in defs.values() for t in d["sources"]}
    assert sources <= all_types
    foreign: set[tuple[str, str, tuple[str, ...]]] = set()
    for type_slug in sorted(all_types):
        model = get_model_class(type_slug)
        declared = {e["type"] for entry in (getattr(model, "OUTBOUND_EDGES", None) or []) for e in entry["edges"]}
        own = {slug for slug in declared if slug.endswith("__teleport")}
        assert own == {slug for slug, d in defs.items() if type_slug in d["sources"]}, type_slug
        for entry in getattr(model, "OUTBOUND_EDGES", None) or []:
            for e in entry["edges"]:
                if not e["type"].endswith("__teleport"):
                    targets = tuple(sorted(n["type"] for n in entry.get("nodes", [])))
                    foreign.add((type_slug, e["type"], targets))
    assert foreign == FOREIGN_DECLARATIONS
