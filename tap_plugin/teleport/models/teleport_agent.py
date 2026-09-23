"""Teleport Agent — A Teleport process that joined the cluster to serve protected resources: it runs one or more of the SSH, Kubernetes, Database, Application, Windows Desktop and Discovery services and dials the proxy over a reverse tunnel.

Spec: specs/spec-teleport-v0.md (req-teleport-deployment).
Domain article: domain/teleport_agent.md.
"""

from typing import Any, ClassVar

from django.db import models

from tap_grid.models import BaseModel


class TeleportAgent(BaseModel):
    """A Teleport process that joined the cluster to serve protected resources: it runs one or more of the SSH, Kubernetes, Database, Application, Windows Desktop and Discovery services and dials the proxy over a reverse tunnel."""

    ENTITY_TYPE: ClassVar[str] = "teleport__teleport_agent"
    ENTITY_NAME: ClassVar[str] = "Teleport Agent"
    ENTITY_DESCRIPTION: ClassVar[str] = (
        "A Teleport process that joined the cluster to serve protected resources: it runs one or more of the SSH, Kubernetes, Database, Application, Windows Desktop and Discovery services and dials the proxy over a reverse tunnel."
    )
    ENTITY_ICON: ClassVar[str] = "teleport-agent"
    # The Teleport plane this type belongs to (domain/dimensions/teleport.plane.md). No dcom or
    # environment default: those belong to the observation, stamped by whoever writes the node.
    DEFAULT_DIMENSIONS: ClassVar[dict[str, str]] = {"teleport.plane": "deployment"}
    # The design knows a name; the host UUID arrives when the agent joins. Revisit to
    # `(cluster_name, host_id)` when observed.
    NATURAL_KEY: ClassVar[tuple[str, ...]] = ('cluster_name', 'name')
    DEFAULT_DISPLAY: ClassVar[dict[str, Any]] = {
        "tap_viz": {
            "shape": "round-rectangle",
            "colors": {"fill": "#FFFFFF", "border": "#512FC9", "label": "#2B1A6E"},
            "label": {"valign": "bottom", "halign": "center", "position": "outside"},
        }
    }

    FIELD_CRUD_SCHEMA: ClassVar[dict[str, Any]] = {
        "name": {"type": "string", "minLength": 1},
        "cluster_name": {"type": "string", "minLength": 1},
        "host_id": {"type": "string"},
        "teleport_version": {"type": "string"},
        "services": {"type": "array", "items": {"type": "string", "enum": ["ssh", "kube", "db", "app", "windows_desktop", "discovery"]}},
        "configuration": {"type": "object"},
    }
    FIELD_VALIDATION_SCHEMA: ClassVar[dict[str, Any]] = {
        "name": {"validation": "jsonschema", "schema": {"type": "string", "minLength": 1}},
        "cluster_name": {"validation": "jsonschema", "schema": {"type": "string", "minLength": 1}},
        "host_id": {"validation": "jsonschema", "schema": {"type": "string"}},
        "teleport_version": {"validation": "jsonschema", "schema": {"type": "string"}},
        "services": {"validation": "jsonschema", "schema": {"type": "array", "items": {"type": "string", "enum": ["ssh", "kube", "db", "app", "windows_desktop", "discovery"]}}},
        "configuration": {"validation": "jsonschema", "schema": {"type": "object"}},
    }
    CREATE_REQUIRED: ClassVar[list[str]] = ['name', 'cluster_name']

    name = models.CharField(max_length=512, blank=True, default="", db_index=True)
    cluster_name = models.CharField(max_length=512, blank=True, default="", db_index=True)
    host_id = models.CharField(max_length=512, blank=True, default="", db_index=True)
    teleport_version = models.CharField(max_length=512, blank=True, default="")
    services = models.JSONField(default=list, blank=True)
    configuration = models.JSONField(default=dict, blank=True)

    class Meta(BaseModel.Meta):
        db_table = "teleport__teleport_agent"

    def get_name(self) -> str:
        return self.name or ""

    def __str__(self) -> str:
        return self.get_name()
