"""Teleport Bot — A Machine ID bot: a non-human identity whose `tbot` agent joins the cluster (by token or a delegated join method) and renews short-lived certificates for the roles it holds.

Spec: specs/spec-teleport-v0.md (req-teleport-identity).
Domain article: domain/teleport_bot.md.
"""

from typing import Any, ClassVar

from django.db import models

from tap_grid.models import BaseModel


class TeleportBot(BaseModel):
    """A Machine ID bot: a non-human identity whose `tbot` agent joins the cluster (by token or a delegated join method) and renews short-lived certificates for the roles it holds."""

    ENTITY_TYPE: ClassVar[str] = "teleport__teleport_bot"
    ENTITY_NAME: ClassVar[str] = "Teleport Bot"
    ENTITY_DESCRIPTION: ClassVar[str] = (
        "A Machine ID bot: a non-human identity whose `tbot` agent joins the cluster (by token or a delegated join method) and renews short-lived certificates for the roles it holds."
    )
    ENTITY_ICON: ClassVar[str] = "teleport-bot"
    # The Teleport plane this type belongs to (domain/dimensions/teleport.plane.md). No dcom or
    # environment default: those belong to the observation, stamped by whoever writes the node.
    DEFAULT_DIMENSIONS: ClassVar[dict[str, str]] = {"teleport.plane": "identity"}
    # Bot names are unique within a cluster (Teleport creates a `bot-<name>` user and role from it).
    NATURAL_KEY: ClassVar[tuple[str, ...]] = ('cluster_name', 'name')
    # Node constraints derived from this plugin's edge files (req-teleport-edges-5): the teleport
    # edges this type may start / receive. Foreign edge types whose own endpoint lists are open
    # (or name this type) stay permitted by the grid's permission union.
    OUTBOUND_EDGES: ClassVar[list[dict[str, Any]]] = [
        {"nodes": [{"type": "teleport__teleport_cluster"}], "edges": [{"type": "BELONGS_TO_CLUSTER__teleport"}]},
        {"nodes": [{"type": "teleport__teleport_join_token"}], "edges": [{"type": "JOINS_WITH_TOKEN__teleport"}]},
        {"nodes": [{"type": "teleport__teleport_role"}], "edges": [{"type": "HOLDS_ROLE__teleport"}]},
    ]
    # No teleport edge ends here, so INBOUND_EDGES stays undeclared: an empty list would block
    # every inbound edge, foreign ones included.
    DEFAULT_DISPLAY: ClassVar[dict[str, Any]] = {
        "tap_viz": {
            "shape": "round-rectangle",
            "colors": {"fill": "#FFFFFF", "border": "#7C5CE0", "label": "#2B1A6E"},
            "label": {"valign": "bottom", "halign": "center", "position": "outside"},
        }
    }

    FIELD_CRUD_SCHEMA: ClassVar[dict[str, Any]] = {
        "name": {"type": "string", "minLength": 1},
        "cluster_name": {"type": "string", "minLength": 1},
        "max_session_ttl": {"type": "string"},
        "traits": {"type": "object"},
        "configuration": {"type": "object"},
    }
    FIELD_VALIDATION_SCHEMA: ClassVar[dict[str, Any]] = {
        "name": {"validation": "jsonschema", "schema": {"type": "string", "minLength": 1}},
        "cluster_name": {"validation": "jsonschema", "schema": {"type": "string", "minLength": 1}},
        "max_session_ttl": {"validation": "jsonschema", "schema": {"type": "string"}},
        "traits": {"validation": "jsonschema", "schema": {"type": "object"}},
        "configuration": {"validation": "jsonschema", "schema": {"type": "object"}},
    }
    CREATE_REQUIRED: ClassVar[list[str]] = ['name', 'cluster_name']

    name = models.CharField(max_length=512, blank=True, default="", db_index=True)
    cluster_name = models.CharField(max_length=512, blank=True, default="", db_index=True)
    max_session_ttl = models.CharField(max_length=512, blank=True, default="")
    traits = models.JSONField(default=dict, blank=True)
    configuration = models.JSONField(default=dict, blank=True)

    class Meta(BaseModel.Meta):
        db_table = "teleport__teleport_bot"

    def get_name(self) -> str:
        return self.name or ""

    def __str__(self) -> str:
        return self.get_name()
