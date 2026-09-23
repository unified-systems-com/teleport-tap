"""Behaviour tests for every teleport node type (req-teleport-model and the per-type requirements).

Each type is exercised through the service layer: it is created from only the fields a design can
know, a write missing any of those is refused, its natural key rests on fields it carries, and its
plane dimension is stamped.
"""

from __future__ import annotations

from typing import Any

import pytest
from django.apps import apps

from tap_grid.caller_context import CallerContext
from tap_grid.services import WriteOperation, write_batch

#: type slug -> the minimal design payload (exactly CREATE_REQUIRED) and the expected plane.
MINIMAL: dict[str, tuple[dict[str, Any], str]] = {
    "teleport__teleport_cluster": ({"name": "stg"}, "deployment"),
    "teleport__teleport_auth_server": ({"name": "auth-a", "cluster_name": "stg"}, "deployment"),
    "teleport__teleport_proxy_server": ({"name": "proxy-a", "cluster_name": "stg"}, "deployment"),
    "teleport__teleport_agent": ({"name": "agent-a", "cluster_name": "stg"}, "deployment"),
    "teleport__teleport_certificate_authority": ({"cluster_name": "stg", "ca_type": "host"}, "trust"),
    "teleport__teleport_role": ({"name": "access", "cluster_name": "stg"}, "policy"),
    "teleport__teleport_user": ({"name": "alice", "cluster_name": "stg"}, "identity"),
    "teleport__teleport_sso_connector": ({"name": "okta", "cluster_name": "stg", "kind": "saml"}, "identity"),
    "teleport__teleport_bot": ({"name": "ci", "cluster_name": "stg"}, "identity"),
    "teleport__teleport_join_token": ({"name": "github-ci", "cluster_name": "stg", "join_method": "github"}, "policy"),
    "teleport__teleport_access_list": ({"name": "admins", "cluster_name": "stg"}, "policy"),
    "teleport__teleport_access_request": ({"name": "0190-req", "cluster_name": "stg"}, "policy"),
    "teleport__teleport_trusted_device": ({"asset_tag": "C02XYZ", "cluster_name": "stg"}, "identity"),
    "teleport__teleport_ssh_node": ({"hostname": "bastion", "cluster_name": "stg"}, "resource"),
    "teleport__teleport_kube_cluster": ({"name": "eks-stg", "cluster_name": "stg"}, "resource"),
    "teleport__teleport_database": ({"name": "rds-app", "cluster_name": "stg"}, "resource"),
    "teleport__teleport_app": ({"name": "aws-console", "cluster_name": "stg"}, "resource"),
    "teleport__teleport_windows_desktop": ({"name": "win-jump", "cluster_name": "stg"}, "resource"),
}


def _model(type_slug: str) -> Any:
    from tap_grid.registry import get_model_class

    return get_model_class(type_slug)


def _create(type_slug: str, payload: dict[str, Any]) -> Any:
    return write_batch(
        [WriteOperation(verb="create_node", type_slug=type_slug, payload=payload)],
        caller_context=CallerContext(),
    ).results[0]


def test_every_manifest_model_is_covered() -> None:
    """Every registered teleport type has a row here, so a new type cannot ship untested."""
    registered = {m._meta.db_table for m in apps.get_app_config("teleport").get_models() if not m.__name__.startswith("Historical")}
    assert registered == set(MINIMAL)


@pytest.mark.parametrize("type_slug", sorted(MINIMAL))
def test_required_fields_are_what_a_design_knows(type_slug: str) -> None:
    """CREATE_REQUIRED is exactly the minimal design payload — no observed identifier is required."""
    payload, _plane = MINIMAL[type_slug]
    assert sorted(_model(type_slug).CREATE_REQUIRED) == sorted(payload)


@pytest.mark.parametrize("type_slug", sorted(MINIMAL))
def test_natural_key_rests_on_carried_fields(type_slug: str) -> None:
    """req-grid-entity-natural-key: every key field is a model field, and a design can fill it."""
    model = _model(type_slug)
    names = {f.name for f in model._meta.get_fields()}
    assert model.NATURAL_KEY and all(k in names for k in model.NATURAL_KEY)
    assert set(model.NATURAL_KEY) <= set(model.CREATE_REQUIRED)


@pytest.mark.django_db
@pytest.mark.parametrize("type_slug", sorted(MINIMAL))
def test_created_from_design_payload(type_slug: str) -> None:
    """A design node is created with only its required fields; the plane dimension is stamped and the
    display name is projected."""
    payload, plane = MINIMAL[type_slug]
    result = _create(type_slug, payload)
    assert result.success, result
    row = _model(type_slug).all_objects.get(entity_id=result.entity_id)
    assert row.entity.dimensions.get("teleport.plane") == plane
    assert row.entity.name == row.get_name() != ""


@pytest.mark.django_db
@pytest.mark.parametrize("type_slug", sorted(MINIMAL))
def test_each_required_field_is_enforced(type_slug: str) -> None:
    payload, _plane = MINIMAL[type_slug]
    for missing in payload:
        partial = {k: v for k, v in payload.items() if k != missing}
        assert not _create(type_slug, partial).success, f"{type_slug} accepted a write without {missing}"


@pytest.mark.django_db
def test_enum_refuses_an_unknown_value() -> None:
    """Three states: blank (not observed) and the vocabulary are accepted; anything else is refused."""
    ok = _create("teleport__teleport_cluster", {"name": "a", "fips": ""})
    assert ok.success
    assert _create("teleport__teleport_cluster", {"name": "b", "fips": "enabled"}).success
    assert not _create("teleport__teleport_cluster", {"name": "c", "fips": "yes"}).success
