"""Teleport Application — An application registered with Teleport — an internal web app, a TCP service, a cloud console (AWS/Azure/GCP) or an MCP server — served by an Application Service agent behind the proxy.

Spec: specs/spec-teleport-v0.md (req-teleport-resources).
Domain article: domain/teleport_app.md.
"""

from typing import Any, ClassVar

from django.db import models

from tap_grid.models import BaseModel


class TeleportApp(BaseModel):
    """An application registered with Teleport — an internal web app, a TCP service, a cloud console (AWS/Azure/GCP) or an MCP server — served by an Application Service agent behind the proxy."""

    ENTITY_TYPE: ClassVar[str] = "teleport__teleport_app"
    ENTITY_NAME: ClassVar[str] = "Teleport Application"
    ENTITY_DESCRIPTION: ClassVar[str] = (
        "An application registered with Teleport \u2014 an internal web app, a TCP service, a cloud console (AWS/Azure/GCP) or an MCP server \u2014 served by an Application Service agent behind the proxy."
    )
    ENTITY_ICON: ClassVar[str] = "teleport-app"
    # The Teleport plane this type belongs to (domain/dimensions/teleport.plane.md). No dcom or
    # environment default: those belong to the observation, stamped by whoever writes the node.
    DEFAULT_DIMENSIONS: ClassVar[dict[str, str]] = {"teleport.plane": "resource"}
    # Application names are unique within the Teleport cluster and set at registration.
    NATURAL_KEY: ClassVar[tuple[str, ...]] = ('cluster_name', 'name')
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
        "uri": {"type": "string"},
        "public_addr": {"type": "string"},
        "labels": {"type": "object"},
        "configuration": {"type": "object"},
    }
    FIELD_VALIDATION_SCHEMA: ClassVar[dict[str, Any]] = {
        "name": {"validation": "jsonschema", "schema": {"type": "string", "minLength": 1}},
        "cluster_name": {"validation": "jsonschema", "schema": {"type": "string", "minLength": 1}},
        "uri": {"validation": "jsonschema", "schema": {"type": "string"}},
        "public_addr": {"validation": "jsonschema", "schema": {"type": "string"}},
        "labels": {"validation": "jsonschema", "schema": {"type": "object"}},
        "configuration": {"validation": "jsonschema", "schema": {"type": "object"}},
    }
    CREATE_REQUIRED: ClassVar[list[str]] = ['name', 'cluster_name']

    name = models.CharField(max_length=512, blank=True, default="", db_index=True)
    cluster_name = models.CharField(max_length=512, blank=True, default="", db_index=True)
    uri = models.CharField(max_length=512, blank=True, default="")
    public_addr = models.CharField(max_length=512, blank=True, default="")
    labels = models.JSONField(default=dict, blank=True)
    configuration = models.JSONField(default=dict, blank=True)

    class Meta(BaseModel.Meta):
        db_table = "teleport__teleport_app"

    def get_name(self) -> str:
        return self.name or ""

    def __str__(self) -> str:
        return self.get_name()
