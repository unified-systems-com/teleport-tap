"""Teleport Access Request — A just-in-time access request: a user asks for roles or specific resources for a bounded time, reviewers approve or deny it, and an approved request is assumed as elevated certificates.

Spec: specs/spec-teleport-v0.md (req-teleport-policy).
Domain article: domain/teleport_access_request.md.
"""

from typing import Any, ClassVar

from django.db import models

from tap_grid.models import BaseModel


class TeleportAccessRequest(BaseModel):
    """A just-in-time access request: a user asks for roles or specific resources for a bounded time, reviewers approve or deny it, and an approved request is assumed as elevated certificates."""

    ENTITY_TYPE: ClassVar[str] = "teleport__teleport_access_request"
    ENTITY_NAME: ClassVar[str] = "Teleport Access Request"
    ENTITY_DESCRIPTION: ClassVar[str] = (
        "A just-in-time access request: a user asks for roles or specific resources for a bounded time, reviewers approve or deny it, and an approved request is assumed as elevated certificates."
    )
    ENTITY_ICON: ClassVar[str] = "teleport-access-request"
    # The Teleport plane this type belongs to (domain/dimensions/teleport.plane.md). No dcom or
    # environment default: those belong to the observation, stamped by whoever writes the node.
    DEFAULT_DIMENSIONS: ClassVar[dict[str, str]] = {"teleport.plane": "policy"}
    # Teleport assigns each request a UUID (`metadata.name`); unique within the cluster. A request
    # is observed, not designed.
    NATURAL_KEY: ClassVar[tuple[str, ...]] = ('cluster_name', 'name')
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
        "state": {"type": "string", "enum": ["PENDING", "APPROVED", "DENIED", "PROMOTED", ""]},
        "reason": {"type": "string"},
        "resolve_reason": {"type": "string"},
        "created_at": {"type": "string"},
        "expires_at": {"type": "string"},
        "configuration": {"type": "object"},
    }
    FIELD_VALIDATION_SCHEMA: ClassVar[dict[str, Any]] = {
        "name": {"validation": "jsonschema", "schema": {"type": "string", "minLength": 1}},
        "cluster_name": {"validation": "jsonschema", "schema": {"type": "string", "minLength": 1}},
        "state": {"validation": "jsonschema", "schema": {"type": "string", "enum": ["PENDING", "APPROVED", "DENIED", "PROMOTED", ""]}},
        "reason": {"validation": "jsonschema", "schema": {"type": "string"}},
        "resolve_reason": {"validation": "jsonschema", "schema": {"type": "string"}},
        "created_at": {"validation": "jsonschema", "schema": {"type": "string"}},
        "expires_at": {"validation": "jsonschema", "schema": {"type": "string"}},
        "configuration": {"validation": "jsonschema", "schema": {"type": "object"}},
    }
    CREATE_REQUIRED: ClassVar[list[str]] = ['name', 'cluster_name']

    name = models.CharField(max_length=512, blank=True, default="", db_index=True)
    cluster_name = models.CharField(max_length=512, blank=True, default="", db_index=True)
    state = models.CharField(max_length=64, blank=True, default="")
    reason = models.TextField(blank=True, default="")
    resolve_reason = models.TextField(blank=True, default="")
    created_at = models.CharField(max_length=512, blank=True, default="")
    expires_at = models.CharField(max_length=512, blank=True, default="")
    configuration = models.JSONField(default=dict, blank=True)

    class Meta(BaseModel.Meta):
        db_table = "teleport__teleport_access_request"

    def get_name(self) -> str:
        return self.name or ""

    def __str__(self) -> str:
        return self.get_name()
