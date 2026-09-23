"""Teleport Join Token — A provision token: what a new agent, proxy or bot must present to join the cluster, with its join method (static secret, EC2/IAM, GitHub, GitLab, Kubernetes, TPM …), the system roles it confers and the external identities it admits.

Spec: specs/spec-teleport-v0.md (req-teleport-policy).
Domain article: domain/teleport_join_token.md.
"""

import re
from typing import Any, ClassVar

from django.core.exceptions import ValidationError
from django.db import models

from tap_grid.models import BaseModel

#: Join methods whose token name is itself the shared secret.
STATIC_SECRET_METHODS = frozenset({"token"})
#: The only form such a name may take on the grid: the secret's SHA-256 digest.
SECRET_DIGEST = re.compile(r"sha256:[0-9a-f]{64}")


class TeleportJoinToken(BaseModel):
    """A provision token: what a new agent, proxy or bot must present to join the cluster, with its join method (static secret, EC2/IAM, GitHub, GitLab, Kubernetes, TPM …), the system roles it confers and the external identities it admits."""

    ENTITY_TYPE: ClassVar[str] = "teleport__teleport_join_token"
    ENTITY_NAME: ClassVar[str] = "Teleport Join Token"
    ENTITY_DESCRIPTION: ClassVar[str] = (
        "A provision token: what a new agent, proxy or bot must present to join the cluster, with its join method (static secret, EC2/IAM, GitHub, GitLab, Kubernetes, TPM \u2026), the system roles it confers and the external identities it admits."
    )
    ENTITY_ICON: ClassVar[str] = "teleport-join-token"
    # The Teleport plane this type belongs to (domain/dimensions/teleport.plane.md). No dcom or
    # environment default: those belong to the observation, stamped by whoever writes the node.
    DEFAULT_DIMENSIONS: ClassVar[dict[str, str]] = {"teleport.plane": "policy"}
    # Token names are unique within a cluster. For the `token` join method the name IS the secret,
    # so for that method only its digest (`sha256:<64 hex>`) is accepted in `name` — the model
    # refuses anything else; delegated methods have non-secret names.
    NATURAL_KEY: ClassVar[tuple[str, ...]] = ('cluster_name', 'name')
    # Node constraints derived from this plugin's edge files (req-teleport-edges-5): the teleport
    # edges this type may start / receive. Foreign edge types whose own endpoint lists are open
    # (or name this type) stay permitted by the grid's permission union.
    OUTBOUND_EDGES: ClassVar[list[dict[str, Any]]] = [
        {"nodes": [{"type": "teleport__teleport_cluster"}], "edges": [{"type": "BELONGS_TO_CLUSTER__teleport"}]},
        {"edges": [{"type": "ADMITS_IDENTITY__teleport"}]},
    ]
    INBOUND_EDGES: ClassVar[list[dict[str, Any]]] = [
        {"nodes": [{"type": "teleport__teleport_agent"}, {"type": "teleport__teleport_proxy_server"}, {"type": "teleport__teleport_bot"}], "edges": [{"type": "JOINS_WITH_TOKEN__teleport"}]},
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
        "join_method": {"type": "string", "minLength": 1, "pattern": "^[a-z][a-z0-9_]*$"},
        "system_roles": {"type": "array", "items": {"type": "string", "enum": ["Node", "Proxy", "Auth", "Kube", "Db", "App", "WindowsDesktop", "Discovery", "Bot", "Instance"]}},
        "bot_name": {"type": "string"},
        "allow_rules": {"type": "array", "items": {"type": "object"}},
        "expires_at": {"type": "string"},
    }
    FIELD_VALIDATION_SCHEMA: ClassVar[dict[str, Any]] = {
        "name": {"validation": "jsonschema", "schema": {"type": "string", "minLength": 1}},
        "cluster_name": {"validation": "jsonschema", "schema": {"type": "string", "minLength": 1}},
        "join_method": {"validation": "jsonschema", "schema": {"type": "string", "minLength": 1, "pattern": "^[a-z][a-z0-9_]*$"}},
        "system_roles": {"validation": "jsonschema", "schema": {"type": "array", "items": {"type": "string", "enum": ["Node", "Proxy", "Auth", "Kube", "Db", "App", "WindowsDesktop", "Discovery", "Bot", "Instance"]}}},
        "bot_name": {"validation": "jsonschema", "schema": {"type": "string"}},
        "allow_rules": {"validation": "jsonschema", "schema": {"type": "array", "items": {"type": "object"}}},
        "expires_at": {"validation": "jsonschema", "schema": {"type": "string"}},
    }
    CREATE_REQUIRED: ClassVar[list[str]] = ['name', 'cluster_name', 'join_method']

    name = models.CharField(max_length=512, blank=True, default="", db_index=True)
    cluster_name = models.CharField(max_length=512, blank=True, default="", db_index=True)
    join_method = models.CharField(max_length=512, blank=True, default="")
    system_roles = models.JSONField(default=list, blank=True)
    bot_name = models.CharField(max_length=512, blank=True, default="")
    allow_rules = models.JSONField(default=list, blank=True)
    expires_at = models.CharField(max_length=512, blank=True, default="")

    class Meta(BaseModel.Meta):
        db_table = "teleport__teleport_join_token"

    def get_name(self) -> str:
        return self.name or ""

    def __str__(self) -> str:
        return self.get_name()

    def validate(self) -> None:
        """A `token`-method token's name IS the join secret: only its digest may be stored."""
        if self.join_method in STATIC_SECRET_METHODS and not SECRET_DIGEST.fullmatch(self.name or ""):
            raise ValidationError(
                {"name": [f"join_method '{self.join_method}' names the secret: store sha256:<64 hex> of it, never the value."]}
            )
