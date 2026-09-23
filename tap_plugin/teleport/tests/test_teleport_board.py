"""teleport-board (req-teleport-panel-board): the pure folds, then every section rendered against a
seeded design through the real Gryphon reads."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from django.template.loader import render_to_string
from django.test import RequestFactory
from tap_plugin.teleport.panels.board import (
    NOT_OBSERVED,
    SECTIONS,
    TeleportBoardPanelType,
    choose_cluster,
    posture_tiles,
)
from tap_plugin.teleport.tests import _design

NOW = datetime(2026, 9, 22, 12, 0, tzinfo=UTC)


def test_choose_cluster_three_ways() -> None:
    a = {"entity_id": "a", "name": "alpha"}
    b = {"entity_id": "b", "name": "beta"}
    assert choose_cluster([a], "").cluster is a
    assert choose_cluster([a, b], "b").cluster is b
    many = choose_cluster([a, b], "")
    assert many.cluster is None and "2 Teleport clusters" in many.message and len(many.others) == 2
    assert choose_cluster([], "").cluster is None
    assert choose_cluster([a], "zzz").cluster is None


def test_posture_blank_is_not_observed_never_a_verdict() -> None:
    tiles = {t.label: t for t in posture_tiles({"fips": "enabled", "local_auth": "enabled", "device_trust_mode": "optional"})}
    assert tiles["FIPS build"].tone == "good"
    assert tiles["Local auth"].tone == "bad"
    assert tiles["Device trust"].tone == "warn"
    assert posture_tiles({"second_factor": "on"})[3].tone == "warn"  # `on` admits OTP
    assert tiles["Second factor"].tone == "unknown" and tiles["Second factor"].value == NOT_OBSERVED
    assert tiles["Version"].tone == "unknown"


def _panel(section: str) -> SimpleNamespace:
    return SimpleNamespace(entity_id="panel", config={"section": section, "title": section})


@pytest.mark.django_db(transaction=True, databases=["default", "search_readonly"])
def test_every_section_renders_against_a_design() -> None:
    ids = _design.seed()
    rf = RequestFactory()
    contexts = {}
    for section in SECTIONS:
        # Two clusters on the grid: without ?cluster= the board refuses to guess.
        unpicked = TeleportBoardPanelType.get_view_context(_panel(section), rf.get("/teleport"))
        assert unpicked["cluster"] is None and unpicked["clusters"], section
        ctx = TeleportBoardPanelType.get_view_context(_panel(section), rf.get("/teleport", {"cluster": ids["cluster"]}))
        assert ctx["board_error"] is None, (section, ctx["board_error"])
        assert ctx["cluster"]["name"] == "stg" and ctx["cluster"]["design"] is True
        html = render_to_string(TeleportBoardPanelType.view, ctx)
        assert "tpb--" + section in html
        contexts[section] = ctx

    inv = {i["label"]: i for i in contexts["posture"]["inventory"]}
    assert inv["Auth servers"]["count"] == 2 and inv["Proxies"]["count"] == 2
    assert inv["Users"]["detail"] == "1 SSO · 1 local" and inv["Users"]["tone"] == "bad"
    assert inv["Pending requests"]["count"] == 1

    roles = {r.name: r for r in contexts["roles"]["roles"]}
    assert roles["access"].reach == {"SSH node": 1}
    assert roles["access"].requestable == ["admin (2 approvals)"]
    assert roles["access"].mapped_from == ["okta: groups=engineers"]
    assert roles["admin"].via_lists == ["Admins"]
    assert roles["admin"].observed is False and roles["admin"].has_deny is None

    ident = contexts["identity"]
    assert ident["local_users"] == ["breakglass"]
    assert ident["access_lists"][0]["due_tone"] == "bad"

    groups = {g["kind"]: g for g in contexts["resources"]["groups"]}
    assert groups["SSH node"]["rows"][0]["reached_by"] == ["access as ec2-user"]
    assert groups["Database"]["rows"][0]["served_by"] == "agent-1"

    reqs = contexts["requests"]["requests"]
    assert [r["id"] for r in reqs] == ["req-1"] and reqs[0]["requester"] == "alice"

    machines = contexts["machines"]
    assert machines["bots"][0]["static"] is True and machines["tokens"][0]["static"] is True

    trust = contexts["trust"]
    cas = {c["type"]: c for c in trust["cas"]}
    assert cas["host"]["storage_tone"] == "good" and cas["db"]["phase"] == NOT_OBSERVED
    assert trust["trusts"][0]["direction"] == "leaf" and trust["trusts"][0]["peer"] == "leaf"


@pytest.mark.django_db(transaction=True, databases=["default", "search_readonly"])
def test_single_cluster_is_chosen_without_a_parameter() -> None:
    _design.node("teleport__teleport_cluster", {"name": "only"})
    ctx = TeleportBoardPanelType.get_view_context(_panel("posture"), RequestFactory().get("/teleport"))
    assert ctx["cluster"]["name"] == "only"
    assert all(t.tone == "unknown" for t in ctx["tiles"])
