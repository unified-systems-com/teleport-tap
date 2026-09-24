"""Person link (req-teleport-person-link): a Teleport user resolves to identity_core's human."""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest
from tap_plugin.teleport.models.teleport_bot import TeleportBot
from tap_plugin.teleport.models.teleport_user import TeleportUser

from tap_grid.caller_context import CallerContext
from tap_grid.models import Edge
from tap_grid.services import WriteOperation, write_batch

HELD = "HELD_BY_HUMAN__identity_core"
HUMAN = "identity_core__human"
PKG = Path(__file__).resolve().parents[1]


def _declared(model) -> set[tuple[str, str]]:
    return {
        (e["type"], n["type"]) for entry in model.OUTBOUND_EDGES for e in entry["edges"] for n in entry.get("nodes", [])
    }


def _node(type_slug: str, payload: dict) -> str:
    result = write_batch(
        [WriteOperation(verb="create_node", type_slug=type_slug, payload=payload)], caller_context=CallerContext()
    ).results[0]
    assert result.success, result
    return str(result.entity_id)


def _held(src: str, dst: str, properties: dict | None = None):
    payload = {"properties": properties} if properties is not None else {}
    return write_batch(
        [WriteOperation(verb="create_edge", from_target=src, to_target=dst, edge_type=HELD, payload=payload)],
        caller_context=CallerContext(),
    ).results[0]


def test_person_link_is_declared() -> None:
    """req-teleport-person-link-1: the user names the edge and the human, a bot does not, and the edge's
    owner is a declared dependency, floored at the release that ships the human."""
    assert (HELD, HUMAN) in _declared(TeleportUser)
    assert not any(edge == HELD for edge, _ in _declared(TeleportBot))
    manifest = tomllib.loads((PKG / "tap-plugin.toml").read_text())
    deps = {d["slug"]: d for d in manifest.get("depends_on", [])}
    # The floor is the first identity_core release that ships identity_core__human.
    assert deps["identity_core"].get("min_version") == "0.1.3"


@pytest.mark.django_db
def test_user_is_held_by_a_human() -> None:
    """req-teleport-person-link-2."""
    human = _node(HUMAN, {"handle": "t-0001", "name": "Test Person"})
    user = _node("teleport__teleport_user", {"name": "tperson", "cluster_name": "stg", "user_type": "sso"})
    result = _held(user, human, {"matched_on": "operator seed"})
    assert result.success, result
    assert Edge.objects.get(entity_id=result.entity_id).properties == {"matched_on": "operator seed"}
    assert not _held(user, human, {"matched_by": "username"}).success


@pytest.mark.django_db
def test_shared_account_is_recorded() -> None:
    """req-teleport-person-link-3: a shared login held by two people keeps both edges."""
    first = _node(HUMAN, {"handle": "t-0001"})
    second = _node(HUMAN, {"handle": "t-0002"})
    shared = _node("teleport__teleport_user", {"name": "break-glass", "cluster_name": "stg", "user_type": "local"})
    assert _held(shared, first, {"matched_on": "operator seed"}).success
    assert _held(shared, second, {"matched_on": "operator seed"}).success
    targets = set(Edge.objects.filter(from_entity_id=shared, edge_type=HELD).values_list("to_entity_id", flat=True))
    assert {str(t) for t in targets} == {first, second}
