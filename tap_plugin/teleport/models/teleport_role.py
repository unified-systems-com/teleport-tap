"""Teleport Role — A Teleport role: allow and deny rules (logins, resource label selectors, Kubernetes groups, database users, resource verbs, request and review permissions) plus session options such as MFA-per-session and maximum TTL.

Spec: specs/spec-teleport-v0.md (req-teleport-policy).
Domain article: domain/teleport_role.md.
"""

from typing import Any, ClassVar

from django.db import models

from tap_grid.models import BaseModel


class TeleportRole(BaseModel):
    """A Teleport role: allow and deny rules (logins, resource label selectors, Kubernetes groups, database users, resource verbs, request and review permissions) plus session options such as MFA-per-session and maximum TTL."""

    ENTITY_TYPE: ClassVar[str] = "teleport__teleport_role"
    ENTITY_NAME: ClassVar[str] = "Teleport Role"
    ENTITY_DESCRIPTION: ClassVar[str] = (
        "A Teleport role: allow and deny rules (logins, resource label selectors, Kubernetes groups, database users, resource verbs, request and review permissions) plus session options such as MFA-per-session and maximum TTL."
    )
    ENTITY_ICON: ClassVar[str] = "teleport-role"
    # The Teleport plane this type belongs to (domain/dimensions/teleport.plane.md). No dcom or
    # environment default: those belong to the observation, stamped by whoever writes the node.
    DEFAULT_DIMENSIONS: ClassVar[dict[str, str]] = {"teleport.plane": "policy"}
    # Role names are unique within a cluster and are what users, connectors and access lists
    # reference, so `(cluster_name, name)` is Teleport's own identity.
    NATURAL_KEY: ClassVar[tuple[str, ...]] = ('cluster_name', 'name')
    # Node constraints derived from this plugin's edge files (req-teleport-edges-5): the teleport
    # edges this type may start / receive. Foreign edge types whose own endpoint lists are open
    # (or name this type) stay permitted by the grid's permission union.
    OUTBOUND_EDGES: ClassVar[list[dict[str, Any]]] = [
        {"nodes": [{"type": "teleport__teleport_cluster"}], "edges": [{"type": "BELONGS_TO_CLUSTER__teleport"}]},
        {"nodes": [{"type": "teleport__teleport_ssh_node"}, {"type": "teleport__teleport_kube_cluster"}, {"type": "teleport__teleport_database"}, {"type": "teleport__teleport_app"}, {"type": "teleport__teleport_windows_desktop"}], "edges": [{"type": "GRANTS_RESOURCE_ACCESS__teleport"}]},
        {"nodes": [{"type": "teleport__teleport_role"}], "edges": [{"type": "PERMITS_ROLE_REQUEST__teleport"}]},
    ]
    INBOUND_EDGES: ClassVar[list[dict[str, Any]]] = [
        {"nodes": [{"type": "teleport__teleport_user"}, {"type": "teleport__teleport_bot"}], "edges": [{"type": "HOLDS_ROLE__teleport"}]},
        {"nodes": [{"type": "teleport__teleport_sso_connector"}], "edges": [{"type": "MAPS_TO_ROLE__teleport"}]},
        {"nodes": [{"type": "teleport__teleport_access_list"}], "edges": [{"type": "GRANTS_ROLE__teleport"}]},
        {"nodes": [{"type": "teleport__teleport_role"}], "edges": [{"type": "PERMITS_ROLE_REQUEST__teleport"}]},
        {"nodes": [{"type": "teleport__teleport_access_request"}], "edges": [{"type": "REQUESTS_ROLE__teleport"}]},
    ]
    DEFAULT_DISPLAY: ClassVar[dict[str, Any]] = {
        "tap_viz": {
            "shape": "round-rectangle",
            "colors": {"fill": "#FFFFFF", "border": "#6B7280", "label": "#1F2937"},
            "label": {"valign": "bottom", "halign": "center", "position": "outside"},
        }
    }

    FIELD_CRUD_SCHEMA: ClassVar[dict[str, Any]] = {
        "name": {"type": "string", "minLength": 1},
        "cluster_name": {"type": "string", "minLength": 1},
        "role_version": {"type": "string"},
        "origin": {"type": "string"},
        "description": {"type": "string"},
        "allow": {"type": "object"},
        "deny": {"type": "object"},
        "options": {"type": "object"},
    }
    FIELD_VALIDATION_SCHEMA: ClassVar[dict[str, Any]] = {
        "name": {"validation": "jsonschema", "schema": {"type": "string", "minLength": 1}},
        "cluster_name": {"validation": "jsonschema", "schema": {"type": "string", "minLength": 1}},
        "role_version": {"validation": "jsonschema", "schema": {"type": "string"}},
        "origin": {"validation": "jsonschema", "schema": {"type": "string"}},
        "description": {"validation": "jsonschema", "schema": {"type": "string"}},
        "allow": {"validation": "jsonschema", "schema": {"type": "object"}},
        "deny": {"validation": "jsonschema", "schema": {"type": "object"}},
        "options": {"validation": "jsonschema", "schema": {"type": "object"}},
    }
    CREATE_REQUIRED: ClassVar[list[str]] = ['name', 'cluster_name']

    name = models.CharField(max_length=512, blank=True, default="", db_index=True)
    cluster_name = models.CharField(max_length=512, blank=True, default="", db_index=True)
    role_version = models.CharField(max_length=512, blank=True, default="")
    origin = models.CharField(max_length=512, blank=True, default="")
    description = models.TextField(blank=True, default="")
    allow = models.JSONField(default=dict, blank=True)
    deny = models.JSONField(default=dict, blank=True)
    options = models.JSONField(default=dict, blank=True)

    class Meta(BaseModel.Meta):
        db_table = "teleport__teleport_role"

    def get_name(self) -> str:
        return self.name or ""

    def __str__(self) -> str:
        return self.get_name()
