"""Teleport Cluster — A Teleport cluster: the access service (Auth Service + Proxy Service and the backend they share) that brokers SSH, Kubernetes, database, application and desktop access, and the cluster-wide settings that govern it.

Spec: specs/spec-teleport-v0.md (req-teleport-model).
Domain article: domain/teleport_cluster.md.
"""

from typing import Any, ClassVar

from django.db import models

from tap_grid.models import BaseModel


class TeleportCluster(BaseModel):
    """A Teleport cluster: the access service (Auth Service + Proxy Service and the backend they share) that brokers SSH, Kubernetes, database, application and desktop access, and the cluster-wide settings that govern it."""

    ENTITY_TYPE: ClassVar[str] = "teleport__teleport_cluster"
    ENTITY_NAME: ClassVar[str] = "Teleport Cluster"
    ENTITY_DESCRIPTION: ClassVar[str] = (
        "A Teleport cluster: the access service (Auth Service + Proxy Service and the backend they share) that brokers SSH, Kubernetes, database, application and desktop access, and the cluster-wide settings that govern it."
    )
    ENTITY_ICON: ClassVar[str] = "teleport-cluster"
    # The Teleport plane this type belongs to (domain/dimensions/teleport.plane.md). No dcom or
    # environment default: those belong to the observation, stamped by whoever writes the node.
    DEFAULT_DIMENSIONS: ClassVar[dict[str, str]] = {"teleport.plane": "deployment"}
    # The cluster name is Teleport's own stable identity: it is set once at first start
    # (`cluster_name`), baked into every certificate the cluster issues, and cannot be changed
    # without rebuilding the cluster. A design knows it before anything is built.
    NATURAL_KEY: ClassVar[tuple[str, ...]] = ('name',)
    # Node constraints derived from this plugin's edge files (req-teleport-edges-5): the teleport
    # edges this type may start / receive. Foreign edge types whose own endpoint lists are open
    # (or name this type) stay permitted by the grid's permission union.
    OUTBOUND_EDGES: ClassVar[list[dict[str, Any]]] = [
        {"nodes": [{"type": "teleport__teleport_cluster"}], "edges": [{"type": "TRUSTS_ROOT_CLUSTER__teleport"}]},
    ]
    INBOUND_EDGES: ClassVar[list[dict[str, Any]]] = [
        {"nodes": [{"type": "teleport__teleport_auth_server"}, {"type": "teleport__teleport_proxy_server"}, {"type": "teleport__teleport_agent"}, {"type": "teleport__teleport_certificate_authority"}, {"type": "teleport__teleport_role"}, {"type": "teleport__teleport_user"}, {"type": "teleport__teleport_sso_connector"}, {"type": "teleport__teleport_bot"}, {"type": "teleport__teleport_join_token"}, {"type": "teleport__teleport_access_list"}, {"type": "teleport__teleport_access_request"}, {"type": "teleport__teleport_trusted_device"}, {"type": "teleport__teleport_ssh_node"}, {"type": "teleport__teleport_kube_cluster"}, {"type": "teleport__teleport_database"}, {"type": "teleport__teleport_app"}, {"type": "teleport__teleport_windows_desktop"}], "edges": [{"type": "BELONGS_TO_CLUSTER__teleport"}]},
        {"nodes": [{"type": "teleport__teleport_cluster"}], "edges": [{"type": "TRUSTS_ROOT_CLUSTER__teleport"}]},
    ]
    DEFAULT_DISPLAY: ClassVar[dict[str, Any]] = {
        "tap_viz": {
            "shape": "round-rectangle",
            "colors": {"fill": "#FFFFFF", "border": "#512FC9", "label": "#2B1A6E"},
            "label": {"valign": "bottom", "halign": "center", "position": "outside"},
        }
    }

    FIELD_CRUD_SCHEMA: ClassVar[dict[str, Any]] = {
        # The type slug is reserved: it is the /teleport page's every-cluster sentinel (req-teleport-page).
        "name": {"type": "string", "minLength": 1, "not": {"const": "teleport__teleport_cluster"}},
        "proxy_address": {"type": "string"},
        "teleport_version": {"type": "string"},
        "edition": {"type": "string", "enum": ["community", "enterprise", ""]},
        "fips": {"type": "string", "enum": ["enabled", "disabled", ""]},
        "signature_algorithm_suite": {"type": "string", "enum": ["legacy", "balanced-v1", "fips-v1", "hsm-v1", ""]},
        "local_auth": {"type": "string", "enum": ["enabled", "disabled", ""]},
        "second_factor": {"type": "string"},
        "device_trust_mode": {"type": "string", "enum": ["off", "optional", "required", ""]},
        "session_recording_mode": {"type": "string", "enum": ["node", "node-sync", "proxy", "proxy-sync", "off", ""]},
        "tags": {"type": "object"},
    }
    FIELD_VALIDATION_SCHEMA: ClassVar[dict[str, Any]] = {
        "name": {"validation": "jsonschema", "schema": {"type": "string", "minLength": 1, "not": {"const": "teleport__teleport_cluster"}}},
        "proxy_address": {"validation": "jsonschema", "schema": {"type": "string"}},
        "teleport_version": {"validation": "jsonschema", "schema": {"type": "string"}},
        "edition": {"validation": "jsonschema", "schema": {"type": "string", "enum": ["community", "enterprise", ""]}},
        "fips": {"validation": "jsonschema", "schema": {"type": "string", "enum": ["enabled", "disabled", ""]}},
        "signature_algorithm_suite": {"validation": "jsonschema", "schema": {"type": "string", "enum": ["legacy", "balanced-v1", "fips-v1", "hsm-v1", ""]}},
        "local_auth": {"validation": "jsonschema", "schema": {"type": "string", "enum": ["enabled", "disabled", ""]}},
        "second_factor": {"validation": "jsonschema", "schema": {"type": "string"}},
        "device_trust_mode": {"validation": "jsonschema", "schema": {"type": "string", "enum": ["off", "optional", "required", ""]}},
        "session_recording_mode": {"validation": "jsonschema", "schema": {"type": "string", "enum": ["node", "node-sync", "proxy", "proxy-sync", "off", ""]}},
        "tags": {"validation": "jsonschema", "schema": {"type": "object"}},
    }
    CREATE_REQUIRED: ClassVar[list[str]] = ['name']

    name = models.CharField(max_length=512, blank=True, default="", db_index=True)
    proxy_address = models.CharField(max_length=512, blank=True, default="")
    teleport_version = models.CharField(max_length=512, blank=True, default="")
    edition = models.CharField(max_length=64, blank=True, default="")
    fips = models.CharField(max_length=64, blank=True, default="")
    signature_algorithm_suite = models.CharField(max_length=64, blank=True, default="")
    local_auth = models.CharField(max_length=64, blank=True, default="")
    second_factor = models.CharField(max_length=512, blank=True, default="")
    device_trust_mode = models.CharField(max_length=64, blank=True, default="")
    session_recording_mode = models.CharField(max_length=64, blank=True, default="")
    tags = models.JSONField(default=dict, blank=True)

    class Meta(BaseModel.Meta):
        db_table = "teleport__teleport_cluster"

    def get_name(self) -> str:
        return self.name or ""

    def __str__(self) -> str:
        return self.get_name()
