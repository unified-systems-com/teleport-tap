"""Teleport Access List — An access list: a set of owners and members that grants roles and traits to its members, with a periodic access review (audit) that owners must complete.

Spec: specs/spec-teleport-v0.md (req-teleport-policy).
Domain article: domain/teleport_access_list.md.
"""

from typing import Any, ClassVar

from django.db import models

from tap_grid.models import BaseModel


class TeleportAccessList(BaseModel):
    """An access list: a set of owners and members that grants roles and traits to its members, with a periodic access review (audit) that owners must complete."""

    ENTITY_TYPE: ClassVar[str] = "teleport__teleport_access_list"
    ENTITY_NAME: ClassVar[str] = "Teleport Access List"
    ENTITY_DESCRIPTION: ClassVar[str] = (
        "An access list: a set of owners and members that grants roles and traits to its members, with a periodic access review (audit) that owners must complete."
    )
    ENTITY_ICON: ClassVar[str] = "teleport-access-list"
    # The Teleport plane this type belongs to (domain/dimensions/teleport.plane.md). No dcom or
    # environment default: those belong to the observation, stamped by whoever writes the node.
    DEFAULT_DIMENSIONS: ClassVar[dict[str, str]] = {"teleport.plane": "policy"}
    # Teleport names access lists with a UUID it assigns (or a name set by IaC); unique within the
    # cluster. A design keys on the name it chooses; revisit if the collector must key on the
    # assigned UUID.
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
        "title": {"type": "string"},
        "description": {"type": "string"},
        "audit_frequency": {"type": "string"},
        "next_audit_date": {"type": "string"},
        "grants": {"type": "object"},
        "membership_requires": {"type": "object"},
    }
    FIELD_VALIDATION_SCHEMA: ClassVar[dict[str, Any]] = {
        "name": {"validation": "jsonschema", "schema": {"type": "string", "minLength": 1}},
        "cluster_name": {"validation": "jsonschema", "schema": {"type": "string", "minLength": 1}},
        "title": {"validation": "jsonschema", "schema": {"type": "string"}},
        "description": {"validation": "jsonschema", "schema": {"type": "string"}},
        "audit_frequency": {"validation": "jsonschema", "schema": {"type": "string"}},
        "next_audit_date": {"validation": "jsonschema", "schema": {"type": "string"}},
        "grants": {"validation": "jsonschema", "schema": {"type": "object"}},
        "membership_requires": {"validation": "jsonschema", "schema": {"type": "object"}},
    }
    CREATE_REQUIRED: ClassVar[list[str]] = ['name', 'cluster_name']

    name = models.CharField(max_length=512, blank=True, default="", db_index=True)
    cluster_name = models.CharField(max_length=512, blank=True, default="", db_index=True)
    title = models.CharField(max_length=512, blank=True, default="")
    description = models.TextField(blank=True, default="")
    audit_frequency = models.CharField(max_length=512, blank=True, default="")
    next_audit_date = models.CharField(max_length=512, blank=True, default="")
    grants = models.JSONField(default=dict, blank=True)
    membership_requires = models.JSONField(default=dict, blank=True)

    class Meta(BaseModel.Meta):
        db_table = "teleport__teleport_access_list"

    def get_name(self) -> str:
        return self.title or self.name or ""

    def __str__(self) -> str:
        return self.get_name()
