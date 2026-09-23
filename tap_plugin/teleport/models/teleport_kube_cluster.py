"""Teleport Kubernetes Cluster — A Kubernetes cluster registered with Teleport and served by a Kubernetes Service agent, reached through the proxy with Teleport-issued credentials mapped to Kubernetes users and groups.

Spec: specs/spec-teleport-v0.md (req-teleport-resources).
Domain article: domain/teleport_kube_cluster.md.
"""

from typing import Any, ClassVar

from django.db import models

from tap_grid.models import BaseModel


class TeleportKubeCluster(BaseModel):
    """A Kubernetes cluster registered with Teleport and served by a Kubernetes Service agent, reached through the proxy with Teleport-issued credentials mapped to Kubernetes users and groups."""

    ENTITY_TYPE: ClassVar[str] = "teleport__teleport_kube_cluster"
    ENTITY_NAME: ClassVar[str] = "Teleport Kubernetes Cluster"
    ENTITY_DESCRIPTION: ClassVar[str] = (
        "A Kubernetes cluster registered with Teleport and served by a Kubernetes Service agent, reached through the proxy with Teleport-issued credentials mapped to Kubernetes users and groups."
    )
    ENTITY_ICON: ClassVar[str] = "teleport-kube-cluster"
    # The Teleport plane this type belongs to (domain/dimensions/teleport.plane.md). No dcom or
    # environment default: those belong to the observation, stamped by whoever writes the node.
    DEFAULT_DIMENSIONS: ClassVar[dict[str, str]] = {"teleport.plane": "resource"}
    # Kubernetes cluster names are unique within the Teleport cluster and set by whoever registers
    # them, so a design knows them.
    NATURAL_KEY: ClassVar[tuple[str, ...]] = ('cluster_name', 'name')
    DEFAULT_DISPLAY: ClassVar[dict[str, Any]] = {
        "tap_viz": {
            "shape": "round-rectangle",
            "colors": {"fill": "#FFFFFF", "border": "#0F766E", "label": "#134E4A"},
            "label": {"valign": "bottom", "halign": "center", "position": "outside"},
        }
    }

    FIELD_CRUD_SCHEMA: ClassVar[dict[str, Any]] = {
        "name": {"type": "string", "minLength": 1},
        "cluster_name": {"type": "string", "minLength": 1},
        "labels": {"type": "object"},
        "configuration": {"type": "object"},
    }
    FIELD_VALIDATION_SCHEMA: ClassVar[dict[str, Any]] = {
        "name": {"validation": "jsonschema", "schema": {"type": "string", "minLength": 1}},
        "cluster_name": {"validation": "jsonschema", "schema": {"type": "string", "minLength": 1}},
        "labels": {"validation": "jsonschema", "schema": {"type": "object"}},
        "configuration": {"validation": "jsonschema", "schema": {"type": "object"}},
    }
    CREATE_REQUIRED: ClassVar[list[str]] = ['name', 'cluster_name']

    name = models.CharField(max_length=512, blank=True, default="", db_index=True)
    cluster_name = models.CharField(max_length=512, blank=True, default="", db_index=True)
    labels = models.JSONField(default=dict, blank=True)
    configuration = models.JSONField(default=dict, blank=True)

    class Meta(BaseModel.Meta):
        db_table = "teleport__teleport_kube_cluster"

    def get_name(self) -> str:
        return self.name or ""

    def __str__(self) -> str:
        return self.get_name()
