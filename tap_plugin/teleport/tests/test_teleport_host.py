"""Host link (req-teleport-host-link): a Teleport trusted device record points at computing_core's neutral host."""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest
from tap_plugin.teleport.models.teleport_trusted_device import TeleportTrustedDevice

from tap_grid.caller_context import CallerContext
from tap_grid.models import Edge
from tap_grid.services import WriteOperation, write_batch

REPRESENTS = "REPRESENTS_HOST__computing_core"
HOST = "computing_core__host"
PKG = Path(__file__).resolve().parents[1]


def _node(type_slug: str, payload: dict) -> str:
    result = write_batch(
        [WriteOperation(verb="create_node", type_slug=type_slug, payload=payload)], caller_context=CallerContext()
    ).results[0]
    assert result.success, result
    return str(result.entity_id)


def _edge(src: str, dst: str, edge_type: str, properties: dict | None = None):
    payload = {"properties": properties} if properties is not None else {}
    return write_batch(
        [WriteOperation(verb="create_edge", from_target=src, to_target=dst, edge_type=edge_type, payload=payload)],
        caller_context=CallerContext(),
    ).results[0]


def test_host_link_is_declared() -> None:
    """req-teleport-host-link-1: the device record names the edge and the host; the edge's owner is a declared dependency."""
    declared = {
        (e["type"], n["type"]) for entry in TeleportTrustedDevice.OUTBOUND_EDGES for e in entry["edges"] for n in entry.get("nodes", [])
    }
    assert (REPRESENTS, HOST) in declared
    manifest = tomllib.loads((PKG / "tap-plugin.toml").read_text())
    assert "computing_core" in {d["slug"] for d in manifest.get("depends_on", [])}


@pytest.mark.django_db
def test_record_represents_a_host() -> None:
    """req-teleport-host-link-2."""
    host = _node(HOST, {"asset_tag": "A-0001", "form_factor": "laptop"})
    record = _node("teleport__teleport_trusted_device", {"cluster_name": "stg", "asset_tag": "C02A"})
    result = _edge(record, host, REPRESENTS, {"matched_on": "serial number"})
    assert result.success, result
    assert Edge.objects.get(entity_id=result.entity_id).properties == {"matched_on": "serial number"}


@pytest.mark.django_db
def test_unknown_property_is_refused() -> None:
    """req-teleport-host-link-2: on a fresh pair, so the refusal is the closed property schema and nothing else."""
    host = _node(HOST, {"asset_tag": "A-0002"})
    record = _node("teleport__teleport_trusted_device", {"cluster_name": "stg", "asset_tag": "C02B"})
    refused = _edge(record, host, REPRESENTS, {"matched_by": "hostname"})
    assert not refused.success
    assert "matched_by" in " ".join(str(e) for e in refused.errors)


@pytest.mark.django_db
def test_record_keeps_its_own_edges() -> None:
    """req-teleport-host-link-1: declaring the link adds a permission and removes none (permission union)."""
    cluster = _node("teleport__teleport_cluster", {"name": "stg"})
    device = _node("teleport__teleport_trusted_device", {"cluster_name": "stg", "asset_tag": "C02C"})
    assert _edge(device, cluster, "BELONGS_TO_CLUSTER__teleport").success
