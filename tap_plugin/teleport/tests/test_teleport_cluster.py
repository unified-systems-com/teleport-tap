"""Behaviour tests for teleport__teleport_cluster (req-teleport-model)."""

from __future__ import annotations

import pytest
from tap_plugin.teleport.models import TeleportCluster

from tap_grid.caller_context import CallerContext
from tap_grid.services import WriteOperation, write_batch

TYPE = "teleport__teleport_cluster"


@pytest.mark.django_db
class TestTeleportCluster:
    def test_create_with_name_only(self) -> None:
        """req-teleport-model-1: a design-phase node needs only its name."""
        result = write_batch(
            [WriteOperation(verb="create_node", type_slug=TYPE, payload={"name": "staging"})],
            caller_context=CallerContext(),
        )
        assert result.results[0].success
        row = TeleportCluster.all_objects.get(entity_id=result.results[0].entity_id)
        assert row.name == "staging"
        assert row.proxy_address == ""

    def test_name_required(self) -> None:
        """req-teleport-model-2: a write without a name is refused."""
        result = write_batch(
            [WriteOperation(verb="create_node", type_slug=TYPE, payload={"proxy_address": "x"})],
            caller_context=CallerContext(),
        )
        assert not result.results[0].success

    def test_the_sentinel_is_not_a_cluster_name(self) -> None:
        """req-teleport-model-5: the /teleport page's every-cluster sentinel can never be a real cluster's name."""
        result = write_batch(
            [WriteOperation(verb="create_node", type_slug=TYPE, payload={"name": TYPE})],
            caller_context=CallerContext(),
        )
        assert not result.results[0].success
        assert not TeleportCluster.all_objects.filter(name=TYPE).exists()


def test_keyed_by_name() -> None:
    """req-teleport-model-3: the key rests only on a field the model carries."""
    assert TeleportCluster.NATURAL_KEY == ("name",)
    names = {f.name for f in TeleportCluster._meta.get_fields()}
    assert all(k in names for k in TeleportCluster.NATURAL_KEY)
