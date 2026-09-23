"""Teleport User — A Teleport user: a local account (password + MFA) or an SSO user Teleport creates at login from a connector, with the traits that fill role templates.

Spec: specs/spec-teleport-v0.md (req-teleport-identity).
Domain article: domain/teleport_user.md.
"""

from typing import Any, ClassVar

from django.db import models

from tap_grid.models import BaseModel


class TeleportUser(BaseModel):
    """A Teleport user: a local account (password + MFA) or an SSO user Teleport creates at login from a connector, with the traits that fill role templates."""

    ENTITY_TYPE: ClassVar[str] = "teleport__teleport_user"
    ENTITY_NAME: ClassVar[str] = "Teleport User"
    ENTITY_DESCRIPTION: ClassVar[str] = (
        "A Teleport user: a local account (password + MFA) or an SSO user Teleport creates at login from a connector, with the traits that fill role templates."
    )
    ENTITY_ICON: ClassVar[str] = "teleport-user"
    # The Teleport plane this type belongs to (domain/dimensions/teleport.plane.md). No dcom or
    # environment default: those belong to the observation, stamped by whoever writes the node.
    DEFAULT_DIMENSIONS: ClassVar[dict[str, str]] = {"teleport.plane": "identity"}
    # Teleport user names are unique within a cluster and are the identity stamped into the user
    # certificate.
    NATURAL_KEY: ClassVar[tuple[str, ...]] = ('cluster_name', 'name')
    DEFAULT_DISPLAY: ClassVar[dict[str, Any]] = {
        "tap_viz": {
            "shape": "round-rectangle",
            "colors": {"fill": "#FFFFFF", "border": "#7C5CE0", "label": "#2B1A6E"},
            "label": {"valign": "bottom", "halign": "center", "position": "outside"},
        }
    }

    FIELD_CRUD_SCHEMA: ClassVar[dict[str, Any]] = {
        "name": {"type": "string", "minLength": 1},
        "cluster_name": {"type": "string", "minLength": 1},
        "user_type": {"type": "string", "enum": ["local", "sso", ""]},
        "traits": {"type": "object"},
        "created_at": {"type": "string"},
        "configuration": {"type": "object"},
    }
    FIELD_VALIDATION_SCHEMA: ClassVar[dict[str, Any]] = {
        "name": {"validation": "jsonschema", "schema": {"type": "string", "minLength": 1}},
        "cluster_name": {"validation": "jsonschema", "schema": {"type": "string", "minLength": 1}},
        "user_type": {"validation": "jsonschema", "schema": {"type": "string", "enum": ["local", "sso", ""]}},
        "traits": {"validation": "jsonschema", "schema": {"type": "object"}},
        "created_at": {"validation": "jsonschema", "schema": {"type": "string"}},
        "configuration": {"validation": "jsonschema", "schema": {"type": "object"}},
    }
    CREATE_REQUIRED: ClassVar[list[str]] = ['name', 'cluster_name']

    name = models.CharField(max_length=512, blank=True, default="", db_index=True)
    cluster_name = models.CharField(max_length=512, blank=True, default="", db_index=True)
    user_type = models.CharField(max_length=64, blank=True, default="")
    traits = models.JSONField(default=dict, blank=True)
    created_at = models.CharField(max_length=512, blank=True, default="")
    configuration = models.JSONField(default=dict, blank=True)

    class Meta(BaseModel.Meta):
        db_table = "teleport__teleport_user"

    def get_name(self) -> str:
        return self.name or ""

    def __str__(self) -> str:
        return self.get_name()
