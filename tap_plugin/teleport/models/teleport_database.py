"""Teleport Database — A database registered with Teleport (PostgreSQL, MySQL, MongoDB, Redis, DynamoDB …) and served by a Database Service agent, reached with short-lived client certificates or IAM auth.

Spec: specs/spec-teleport-v0.md (req-teleport-resources).
Domain article: domain/teleport_database.md.
"""

from typing import Any, ClassVar

from django.db import models

from tap_grid.models import BaseModel


class TeleportDatabase(BaseModel):
    """A database registered with Teleport (PostgreSQL, MySQL, MongoDB, Redis, DynamoDB …) and served by a Database Service agent, reached with short-lived client certificates or IAM auth."""

    ENTITY_TYPE: ClassVar[str] = "teleport__teleport_database"
    ENTITY_NAME: ClassVar[str] = "Teleport Database"
    ENTITY_DESCRIPTION: ClassVar[str] = (
        "A database registered with Teleport (PostgreSQL, MySQL, MongoDB, Redis, DynamoDB \u2026) and served by a Database Service agent, reached with short-lived client certificates or IAM auth."
    )
    ENTITY_ICON: ClassVar[str] = "teleport-database"
    # The Teleport plane this type belongs to (domain/dimensions/teleport.plane.md). No dcom or
    # environment default: those belong to the observation, stamped by whoever writes the node.
    DEFAULT_DIMENSIONS: ClassVar[dict[str, str]] = {"teleport.plane": "resource"}
    # Database resource names are unique within the Teleport cluster and set at registration.
    NATURAL_KEY: ClassVar[tuple[str, ...]] = ('cluster_name', 'name')
    # Node constraints derived from this plugin's edge files (req-teleport-edges-5): the teleport
    # edges this type may start / receive. Foreign edge types whose own endpoint lists are open
    # (or name this type) stay permitted by the grid's permission union.
    OUTBOUND_EDGES: ClassVar[list[dict[str, Any]]] = [
        {"nodes": [{"type": "teleport__teleport_cluster"}], "edges": [{"type": "BELONGS_TO_CLUSTER__teleport"}]},
        {"edges": [{"type": "FRONTS_TARGET__teleport"}]},
    ]
    INBOUND_EDGES: ClassVar[list[dict[str, Any]]] = [
        {"nodes": [{"type": "teleport__teleport_agent"}], "edges": [{"type": "SERVES_RESOURCE__teleport"}]},
        {"nodes": [{"type": "teleport__teleport_role"}], "edges": [{"type": "GRANTS_RESOURCE_ACCESS__teleport"}]},
        {"nodes": [{"type": "teleport__teleport_access_request"}], "edges": [{"type": "REQUESTS_RESOURCE__teleport"}]},
    ]
    DEFAULT_DISPLAY: ClassVar[dict[str, Any]] = {
        "tap_viz": {
            "shape": "round-rectangle",
            "colors": {"fill": "#FFFFFF", "border": "#0F766E", "label": "#134E4A"},
            "label": {"valign": "bottom", "halign": "center", "position": "outside"},
        }
    }

    FIELD_CRUD_SCHEMA: ClassVar[dict[str, Any]] = {
        "name": {"type": "string", "minLength": 1},
        "cluster_name": {"type": "string", "minLength": 1},
        "protocol": {"type": "string"},
        "uri": {"type": "string"},
        "labels": {"type": "object"},
    }
    FIELD_VALIDATION_SCHEMA: ClassVar[dict[str, Any]] = {
        "name": {"validation": "jsonschema", "schema": {"type": "string", "minLength": 1}},
        "cluster_name": {"validation": "jsonschema", "schema": {"type": "string", "minLength": 1}},
        "protocol": {"validation": "jsonschema", "schema": {"type": "string"}},
        "uri": {"validation": "jsonschema", "schema": {"type": "string"}},
        "labels": {"validation": "jsonschema", "schema": {"type": "object"}},
    }
    CREATE_REQUIRED: ClassVar[list[str]] = ['name', 'cluster_name']

    name = models.CharField(max_length=512, blank=True, default="", db_index=True)
    cluster_name = models.CharField(max_length=512, blank=True, default="", db_index=True)
    protocol = models.CharField(max_length=512, blank=True, default="")
    uri = models.CharField(max_length=512, blank=True, default="")
    labels = models.JSONField(default=dict, blank=True)

    class Meta(BaseModel.Meta):
        db_table = "teleport__teleport_database"

    def get_name(self) -> str:
        return self.name or ""

    def __str__(self) -> str:
        return self.get_name()
