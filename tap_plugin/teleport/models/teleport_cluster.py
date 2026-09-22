"""Teleport Cluster — a Teleport cluster: the access service (auth + proxy) that brokers SSH, Kubernetes, database, application and desktop access."""

from typing import Any, ClassVar

from django.db import models

from tap_grid.models import BaseModel


class TeleportCluster(BaseModel):
    """A Teleport cluster: the access service (auth + proxy) that brokers SSH, Kubernetes, database, application and desktop access.

    v0 is the outer node only: a design can place it before any access exists, so its one
    identifying field stays blank (not observed) until a collector reads it.

    Spec: specs/spec-teleport-v0.md (req-teleport-model).
    """

    ENTITY_TYPE: ClassVar[str] = "teleport__teleport_cluster"
    ENTITY_NAME: ClassVar[str] = "Teleport Cluster"
    ENTITY_DESCRIPTION: ClassVar[str] = "A Teleport cluster: the access service (auth + proxy) that brokers SSH, Kubernetes, database, application and desktop access."
    ENTITY_ICON: ClassVar[str] = "teleport-cluster"
    # No default dimension: the dcom value belongs to the observation (a seeded design node is
    # `design`, a collected one `configuration`), so the bundle that seeds a node stamps it.
    DEFAULT_DIMENSIONS: ClassVar[dict[str, str]] = {}
    # A design-phase node has no observed identifier; its name is the only fact it carries.
    # Revisit when the collector makes proxy_address observable (req-teleport-collector).
    NATURAL_KEY: ClassVar[tuple[str, ...]] = ("name",)
    DEFAULT_DISPLAY: ClassVar[dict[str, Any]] = {
        "tap_viz": {
            "shape": "round-rectangle",
            "colors": {"fill": "#FFFFFF", "border": "#512FC9", "label": "#2B1A6E"},
            "label": {"valign": "bottom", "halign": "center", "position": "outside"},
        }
    }

    FIELD_CRUD_SCHEMA: ClassVar[dict[str, Any]] = {
        "name": {"type": "string", "minLength": 1},
        "proxy_address": {"type": "string"},
        "configuration": {"type": "object"},
        "tags": {"type": "object"},
    }
    FIELD_VALIDATION_SCHEMA: ClassVar[dict[str, Any]] = {
        "name": {"validation": "jsonschema", "schema": {"type": "string", "minLength": 1}},
        "proxy_address": {"validation": "jsonschema", "schema": {"type": "string"}},
        "configuration": {"validation": "jsonschema", "schema": {"type": "object"}},
        "tags": {"validation": "jsonschema", "schema": {"type": "object"}},
    }
    CREATE_REQUIRED: ClassVar[list[str]] = ["name"]

    name = models.CharField(max_length=255, blank=True, default="", db_index=True)
    # The cluster's public proxy address (host:port). Blank until observed.
    proxy_address = models.CharField(max_length=255, blank=True, default="")
    configuration = models.JSONField(default=dict, blank=True)
    tags = models.JSONField(default=dict, blank=True)

    class Meta(BaseModel.Meta):
        db_table = "teleport__teleport_cluster"

    def get_name(self) -> str:
        return self.name

    def __str__(self) -> str:
        return self.get_name()
