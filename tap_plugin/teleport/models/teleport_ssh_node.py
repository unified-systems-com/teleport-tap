"""Teleport SSH Node — A server reachable over SSH through Teleport: a host running the Teleport SSH Service, or an agentless OpenSSH host registered with the cluster.

Spec: specs/spec-teleport-v0.md (req-teleport-resources).
Domain article: domain/teleport_ssh_node.md.
"""

from typing import Any, ClassVar

from django.db import models

from tap_grid.models import BaseModel


class TeleportSshNode(BaseModel):
    """A server reachable over SSH through Teleport: a host running the Teleport SSH Service, or an agentless OpenSSH host registered with the cluster."""

    ENTITY_TYPE: ClassVar[str] = "teleport__teleport_ssh_node"
    ENTITY_NAME: ClassVar[str] = "Teleport SSH Node"
    ENTITY_DESCRIPTION: ClassVar[str] = (
        "A server reachable over SSH through Teleport: a host running the Teleport SSH Service, or an agentless OpenSSH host registered with the cluster."
    )
    ENTITY_ICON: ClassVar[str] = "teleport-ssh-node"
    # The Teleport plane this type belongs to (domain/dimensions/teleport.plane.md). No dcom or
    # environment default: those belong to the observation, stamped by whoever writes the node.
    DEFAULT_DIMENSIONS: ClassVar[dict[str, str]] = {"teleport.plane": "resource"}
    # A design knows a host by its hostname; Teleport's node resource is named by host UUID, which
    # exists only after the host joins. Revisit to `(cluster_name, host_id)` when observed.
    NATURAL_KEY: ClassVar[tuple[str, ...]] = ('cluster_name', 'hostname')
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
        "hostname": {"type": "string", "minLength": 1},
        "cluster_name": {"type": "string", "minLength": 1},
        "host_id": {"type": "string"},
        "addr": {"type": "string"},
        "sub_kind": {"type": "string", "enum": ["teleport", "openssh", "openssh-ec2-ice", ""]},
        "labels": {"type": "object"},
        "configuration": {"type": "object"},
    }
    FIELD_VALIDATION_SCHEMA: ClassVar[dict[str, Any]] = {
        "hostname": {"validation": "jsonschema", "schema": {"type": "string", "minLength": 1}},
        "cluster_name": {"validation": "jsonschema", "schema": {"type": "string", "minLength": 1}},
        "host_id": {"validation": "jsonschema", "schema": {"type": "string"}},
        "addr": {"validation": "jsonschema", "schema": {"type": "string"}},
        "sub_kind": {"validation": "jsonschema", "schema": {"type": "string", "enum": ["teleport", "openssh", "openssh-ec2-ice", ""]}},
        "labels": {"validation": "jsonschema", "schema": {"type": "object"}},
        "configuration": {"validation": "jsonschema", "schema": {"type": "object"}},
    }
    CREATE_REQUIRED: ClassVar[list[str]] = ['hostname', 'cluster_name']

    hostname = models.CharField(max_length=512, blank=True, default="", db_index=True)
    cluster_name = models.CharField(max_length=512, blank=True, default="", db_index=True)
    host_id = models.CharField(max_length=512, blank=True, default="", db_index=True)
    addr = models.CharField(max_length=512, blank=True, default="")
    sub_kind = models.CharField(max_length=64, blank=True, default="")
    labels = models.JSONField(default=dict, blank=True)
    configuration = models.JSONField(default=dict, blank=True)

    class Meta(BaseModel.Meta):
        db_table = "teleport__teleport_ssh_node"

    def get_name(self) -> str:
        return self.hostname or ""

    def __str__(self) -> str:
        return self.get_name()
