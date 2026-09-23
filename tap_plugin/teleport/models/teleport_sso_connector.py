"""Teleport SSO Connector — A SAML, OIDC or GitHub authentication connector: the trust Teleport places in an external identity provider, and the mappings from the IdP's attributes, claims or teams to Teleport roles.

Spec: specs/spec-teleport-v0.md (req-teleport-identity).
Domain article: domain/teleport_sso_connector.md.
"""

from typing import Any, ClassVar

from django.db import models

from tap_grid.models import BaseModel


class TeleportSsoConnector(BaseModel):
    """A SAML, OIDC or GitHub authentication connector: the trust Teleport places in an external identity provider, and the mappings from the IdP's attributes, claims or teams to Teleport roles."""

    ENTITY_TYPE: ClassVar[str] = "teleport__teleport_sso_connector"
    ENTITY_NAME: ClassVar[str] = "Teleport SSO Connector"
    ENTITY_DESCRIPTION: ClassVar[str] = (
        "A SAML, OIDC or GitHub authentication connector: the trust Teleport places in an external identity provider, and the mappings from the IdP's attributes, claims or teams to Teleport roles."
    )
    ENTITY_ICON: ClassVar[str] = "teleport-sso-connector"
    # The Teleport plane this type belongs to (domain/dimensions/teleport.plane.md). No dcom or
    # environment default: those belong to the observation, stamped by whoever writes the node.
    DEFAULT_DIMENSIONS: ClassVar[dict[str, str]] = {"teleport.plane": "identity"}
    # Teleport namespaces connectors by kind (`saml`, `oidc`, `github` are separate resource kinds),
    # so a name is unique only within its kind and cluster.
    NATURAL_KEY: ClassVar[tuple[str, ...]] = ('cluster_name', 'kind', 'name')
    # Node constraints derived from this plugin's edge files (req-teleport-edges-5): the teleport
    # edges this type may start / receive. Foreign edge types whose own endpoint lists are open
    # (or name this type) stay permitted by the grid's permission union.
    OUTBOUND_EDGES: ClassVar[list[dict[str, Any]]] = [
        {"nodes": [{"type": "teleport__teleport_cluster"}], "edges": [{"type": "BELONGS_TO_CLUSTER__teleport"}]},
        {"nodes": [{"type": "teleport__teleport_role"}], "edges": [{"type": "MAPS_TO_ROLE__teleport"}]},
        {"edges": [{"type": "DELEGATES_LOGIN__teleport"}]},
    ]
    INBOUND_EDGES: ClassVar[list[dict[str, Any]]] = [
        {"nodes": [{"type": "teleport__teleport_user"}], "edges": [{"type": "LOGS_IN_VIA_CONNECTOR__teleport"}]},
    ]
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
        "kind": {"type": "string", "enum": ["saml", "oidc", "github"]},
        "display": {"type": "string"},
        "idp_url": {"type": "string"},
        "configuration": {"type": "object"},
    }
    FIELD_VALIDATION_SCHEMA: ClassVar[dict[str, Any]] = {
        "name": {"validation": "jsonschema", "schema": {"type": "string", "minLength": 1}},
        "cluster_name": {"validation": "jsonschema", "schema": {"type": "string", "minLength": 1}},
        "kind": {"validation": "jsonschema", "schema": {"type": "string", "enum": ["saml", "oidc", "github"]}},
        "display": {"validation": "jsonschema", "schema": {"type": "string"}},
        "idp_url": {"validation": "jsonschema", "schema": {"type": "string"}},
        "configuration": {"validation": "jsonschema", "schema": {"type": "object"}},
    }
    CREATE_REQUIRED: ClassVar[list[str]] = ['name', 'cluster_name', 'kind']

    name = models.CharField(max_length=512, blank=True, default="", db_index=True)
    cluster_name = models.CharField(max_length=512, blank=True, default="", db_index=True)
    kind = models.CharField(max_length=64, blank=True, default="")
    display = models.CharField(max_length=512, blank=True, default="")
    idp_url = models.CharField(max_length=512, blank=True, default="")
    configuration = models.JSONField(default=dict, blank=True)

    class Meta(BaseModel.Meta):
        db_table = "teleport__teleport_sso_connector"

    def get_name(self) -> str:
        return self.name or ""

    def __str__(self) -> str:
        return self.get_name()
