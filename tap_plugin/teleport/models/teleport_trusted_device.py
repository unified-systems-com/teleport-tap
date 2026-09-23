"""Teleport Trusted Device — A device registered in Teleport's device inventory (by serial / asset tag) and, once enrolled, holding a device credential that device-trust mode requires before access is granted.

Spec: specs/spec-teleport-v0.md (req-teleport-identity).
Domain article: domain/teleport_trusted_device.md.
"""

from typing import Any, ClassVar

from django.db import models

from tap_grid.models import BaseModel


class TeleportTrustedDevice(BaseModel):
    """A device registered in Teleport's device inventory (by serial / asset tag) and, once enrolled, holding a device credential that device-trust mode requires before access is granted."""

    ENTITY_TYPE: ClassVar[str] = "teleport__teleport_trusted_device"
    ENTITY_NAME: ClassVar[str] = "Teleport Trusted Device"
    ENTITY_DESCRIPTION: ClassVar[str] = (
        "A device registered in Teleport's device inventory (by serial / asset tag) and, once enrolled, holding a device credential that device-trust mode requires before access is granted."
    )
    ENTITY_ICON: ClassVar[str] = "teleport-trusted-device"
    # The Teleport plane this type belongs to (domain/dimensions/teleport.plane.md). No dcom or
    # environment default: those belong to the observation, stamped by whoever writes the node.
    DEFAULT_DIMENSIONS: ClassVar[dict[str, str]] = {"teleport.plane": "identity"}
    # Teleport identifies a device by its asset tag (the serial number on macOS/Windows/Linux)
    # within the cluster's inventory; the internal UUID is assigned at registration.
    NATURAL_KEY: ClassVar[tuple[str, ...]] = ('cluster_name', 'asset_tag')
    # Node constraints derived from this plugin's edge files (req-teleport-edges-5): the teleport
    # edges this type may start / receive. Foreign edge types whose own endpoint lists are open
    # (or name this type) stay permitted by the grid's permission union.
    OUTBOUND_EDGES: ClassVar[list[dict[str, Any]]] = [
        {"nodes": [{"type": "teleport__teleport_cluster"}], "edges": [{"type": "BELONGS_TO_CLUSTER__teleport"}]},
    ]
    INBOUND_EDGES: ClassVar[list[dict[str, Any]]] = [
        {"nodes": [{"type": "teleport__teleport_user"}], "edges": [{"type": "ENROLLED_DEVICE__teleport"}]},
    ]
    DEFAULT_DISPLAY: ClassVar[dict[str, Any]] = {
        "tap_viz": {
            "shape": "round-rectangle",
            "colors": {"fill": "#FFFFFF", "border": "#7C5CE0", "label": "#2B1A6E"},
            "label": {"valign": "bottom", "halign": "center", "position": "outside"},
        }
    }

    FIELD_CRUD_SCHEMA: ClassVar[dict[str, Any]] = {
        "cluster_name": {"type": "string", "minLength": 1},
        "asset_tag": {"type": "string", "minLength": 1},
        "os_type": {"type": "string", "enum": ["macos", "windows", "linux", ""]},
        "enroll_status": {"type": "string", "enum": ["enrolled", "not_enrolled", ""]},
    }
    FIELD_VALIDATION_SCHEMA: ClassVar[dict[str, Any]] = {
        "cluster_name": {"validation": "jsonschema", "schema": {"type": "string", "minLength": 1}},
        "asset_tag": {"validation": "jsonschema", "schema": {"type": "string", "minLength": 1}},
        "os_type": {"validation": "jsonschema", "schema": {"type": "string", "enum": ["macos", "windows", "linux", ""]}},
        "enroll_status": {"validation": "jsonschema", "schema": {"type": "string", "enum": ["enrolled", "not_enrolled", ""]}},
    }
    CREATE_REQUIRED: ClassVar[list[str]] = ['asset_tag', 'cluster_name']

    cluster_name = models.CharField(max_length=512, blank=True, default="", db_index=True)
    asset_tag = models.CharField(max_length=512, blank=True, default="", db_index=True)
    os_type = models.CharField(max_length=64, blank=True, default="")
    enroll_status = models.CharField(max_length=64, blank=True, default="")

    class Meta(BaseModel.Meta):
        db_table = "teleport__teleport_trusted_device"

    def get_name(self) -> str:
        return self.asset_tag or ""

    def __str__(self) -> str:
        return self.get_name()
