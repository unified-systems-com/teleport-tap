"""Teleport Proxy Server — One Teleport process running the Proxy Service: the stateless public front door (web UI, TLS routing, reverse tunnels) that users and agents dial, which calls the Auth Service for every decision.

Spec: specs/spec-teleport-v0.md (req-teleport-deployment).
Domain article: domain/teleport_proxy_server.md.
"""

from typing import Any, ClassVar

from django.db import models

from tap_grid.models import BaseModel


class TeleportProxyServer(BaseModel):
    """One Teleport process running the Proxy Service: the stateless public front door (web UI, TLS routing, reverse tunnels) that users and agents dial, which calls the Auth Service for every decision."""

    ENTITY_TYPE: ClassVar[str] = "teleport__teleport_proxy_server"
    ENTITY_NAME: ClassVar[str] = "Teleport Proxy Server"
    ENTITY_DESCRIPTION: ClassVar[str] = (
        "One Teleport process running the Proxy Service: the stateless public front door (web UI, TLS routing, reverse tunnels) that users and agents dial, which calls the Auth Service for every decision."
    )
    ENTITY_ICON: ClassVar[str] = "teleport-proxy-server"
    # The Teleport plane this type belongs to (domain/dimensions/teleport.plane.md). No dcom or
    # environment default: those belong to the observation, stamped by whoever writes the node.
    DEFAULT_DIMENSIONS: ClassVar[dict[str, str]] = {"teleport.plane": "deployment"}
    # As for the auth server: the design knows a name; Teleport's host UUID arrives on first start.
    # Revisit to `(cluster_name, host_id)` when observed.
    NATURAL_KEY: ClassVar[tuple[str, ...]] = ('cluster_name', 'name')
    # Node constraints derived from this plugin's edge files (req-teleport-edges-5): the teleport
    # edges this type may start / receive. Foreign edge types whose own endpoint lists are open
    # (or name this type) stay permitted by the grid's permission union.
    OUTBOUND_EDGES: ClassVar[list[dict[str, Any]]] = [
        {"nodes": [{"type": "teleport__teleport_cluster"}], "edges": [{"type": "BELONGS_TO_CLUSTER__teleport"}]},
        {"edges": [{"type": "RUNS_ON_COMPUTE__teleport"}]},
        {"nodes": [{"type": "teleport__teleport_auth_server"}], "edges": [{"type": "CALLS_AUTH_API__teleport"}]},
        {"nodes": [{"type": "teleport__teleport_join_token"}], "edges": [{"type": "JOINS_WITH_TOKEN__teleport"}]},
    ]
    INBOUND_EDGES: ClassVar[list[dict[str, Any]]] = [
        {"nodes": [{"type": "teleport__teleport_agent"}], "edges": [{"type": "DIALS_REVERSE_TUNNEL__teleport"}]},
    ]
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
        "public_addr": {"type": "string"},
    }
    FIELD_VALIDATION_SCHEMA: ClassVar[dict[str, Any]] = {
        "name": {"validation": "jsonschema", "schema": {"type": "string", "minLength": 1}},
        "cluster_name": {"validation": "jsonschema", "schema": {"type": "string", "minLength": 1}},
        "host_id": {"validation": "jsonschema", "schema": {"type": "string"}},
        "teleport_version": {"validation": "jsonschema", "schema": {"type": "string"}},
        "public_addr": {"validation": "jsonschema", "schema": {"type": "string"}},
    }
    CREATE_REQUIRED: ClassVar[list[str]] = ['name', 'cluster_name']

    name = models.CharField(max_length=512, blank=True, default="", db_index=True)
    cluster_name = models.CharField(max_length=512, blank=True, default="", db_index=True)
    host_id = models.CharField(max_length=512, blank=True, default="", db_index=True)
    teleport_version = models.CharField(max_length=512, blank=True, default="")
    public_addr = models.CharField(max_length=512, blank=True, default="")

    class Meta(BaseModel.Meta):
        db_table = "teleport__teleport_proxy_server"

    def get_name(self) -> str:
        return self.name or ""

    def __str__(self) -> str:
        return self.get_name()
