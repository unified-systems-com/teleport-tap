"""Teleport Auth Server — One Teleport process running the Auth Service: the cluster's certificate authority and API, which issues certificates, evaluates roles, and reads and writes the backend, audit log and session-recording storage.

Spec: specs/spec-teleport-v0.md (req-teleport-deployment).
Domain article: domain/teleport_auth_server.md.
"""

from typing import Any, ClassVar

from django.db import models

from tap_grid.models import BaseModel


class TeleportAuthServer(BaseModel):
    """One Teleport process running the Auth Service: the cluster's certificate authority and API, which issues certificates, evaluates roles, and reads and writes the backend, audit log and session-recording storage."""

    ENTITY_TYPE: ClassVar[str] = "teleport__teleport_auth_server"
    ENTITY_NAME: ClassVar[str] = "Teleport Auth Server"
    ENTITY_DESCRIPTION: ClassVar[str] = (
        "One Teleport process running the Auth Service: the cluster's certificate authority and API, which issues certificates, evaluates roles, and reads and writes the backend, audit log and session-recording storage."
    )
    ENTITY_ICON: ClassVar[str] = "teleport-auth-server"
    # The Teleport plane this type belongs to (domain/dimensions/teleport.plane.md). No dcom or
    # environment default: those belong to the observation, stamped by whoever writes the node.
    DEFAULT_DIMENSIONS: ClassVar[dict[str, str]] = {"teleport.plane": "deployment"}
    # A design knows an auth server only by the name it gives it; Teleport's own identity is the
    # host UUID (`host_id`), which exists only once the process first starts. Revisit to
    # `(cluster_name, host_id)` when the collector observes it.
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
        "configuration": {"type": "object"},
    }
    FIELD_VALIDATION_SCHEMA: ClassVar[dict[str, Any]] = {
        "name": {"validation": "jsonschema", "schema": {"type": "string", "minLength": 1}},
        "cluster_name": {"validation": "jsonschema", "schema": {"type": "string", "minLength": 1}},
        "host_id": {"validation": "jsonschema", "schema": {"type": "string"}},
        "teleport_version": {"validation": "jsonschema", "schema": {"type": "string"}},
        "configuration": {"validation": "jsonschema", "schema": {"type": "object"}},
    }
    CREATE_REQUIRED: ClassVar[list[str]] = ['name', 'cluster_name']

    name = models.CharField(max_length=512, blank=True, default="", db_index=True)
    cluster_name = models.CharField(max_length=512, blank=True, default="", db_index=True)
    host_id = models.CharField(max_length=512, blank=True, default="", db_index=True)
    teleport_version = models.CharField(max_length=512, blank=True, default="")
    configuration = models.JSONField(default=dict, blank=True)

    class Meta(BaseModel.Meta):
        db_table = "teleport__teleport_auth_server"

    def get_name(self) -> str:
        return self.name or ""

    def __str__(self) -> str:
        return self.get_name()
