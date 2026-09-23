"""Teleport Certificate Authority — One of the cluster's certificate authorities (host, user, database, OpenSSH, JWT, SAML IdP, OIDC IdP, SPIFFE …): the key pair that signs a class of short-lived certificates, with its rotation phase and where its private key is stored.

Spec: specs/spec-teleport-v0.md (req-teleport-trust).
Domain article: domain/teleport_certificate_authority.md.
"""

from typing import Any, ClassVar

from django.db import models

from tap_grid.models import BaseModel


class TeleportCertificateAuthority(BaseModel):
    """One of the cluster's certificate authorities (host, user, database, OpenSSH, JWT, SAML IdP, OIDC IdP, SPIFFE …): the key pair that signs a class of short-lived certificates, with its rotation phase and where its private key is stored."""

    ENTITY_TYPE: ClassVar[str] = "teleport__teleport_certificate_authority"
    ENTITY_NAME: ClassVar[str] = "Teleport Certificate Authority"
    ENTITY_DESCRIPTION: ClassVar[str] = (
        "One of the cluster's certificate authorities (host, user, database, OpenSSH, JWT, SAML IdP, OIDC IdP, SPIFFE \u2026): the key pair that signs a class of short-lived certificates, with its rotation phase and where its private key is stored."
    )
    ENTITY_ICON: ClassVar[str] = "teleport-certificate-authority"
    # The Teleport plane this type belongs to (domain/dimensions/teleport.plane.md). No dcom or
    # environment default: those belong to the observation, stamped by whoever writes the node.
    DEFAULT_DIMENSIONS: ClassVar[dict[str, str]] = {"teleport.plane": "trust"}
    # A cluster has exactly one CA of each type, and Teleport names the CA resource after the
    # cluster, so `(cluster_name, ca_type)` is Teleport's own identity and a design can know it.
    NATURAL_KEY: ClassVar[tuple[str, ...]] = ('cluster_name', 'ca_type')
    DEFAULT_DISPLAY: ClassVar[dict[str, Any]] = {
        "tap_viz": {
            "shape": "round-rectangle",
            "colors": {"fill": "#F3F0FF", "border": "#512FC9", "label": "#2B1A6E"},
            "label": {"valign": "bottom", "halign": "center", "position": "outside"},
        }
    }

    FIELD_CRUD_SCHEMA: ClassVar[dict[str, Any]] = {
        "cluster_name": {"type": "string", "minLength": 1},
        "ca_type": {"type": "string", "enum": ["host", "user", "db", "db_client", "openssh", "jwt", "saml_idp", "oidc_idp", "spiffe", "okta", "awsra"]},
        "rotation_phase": {"type": "string", "enum": ["standby", "init", "update_clients", "update_servers", "rollback", ""]},
        "last_rotated_at": {"type": "string"},
        "key_storage": {"type": "string", "enum": ["software", "aws_kms", "gcp_kms", "pkcs11", ""]},
        "configuration": {"type": "object"},
    }
    FIELD_VALIDATION_SCHEMA: ClassVar[dict[str, Any]] = {
        "cluster_name": {"validation": "jsonschema", "schema": {"type": "string", "minLength": 1}},
        "ca_type": {"validation": "jsonschema", "schema": {"type": "string", "enum": ["host", "user", "db", "db_client", "openssh", "jwt", "saml_idp", "oidc_idp", "spiffe", "okta", "awsra"]}},
        "rotation_phase": {"validation": "jsonschema", "schema": {"type": "string", "enum": ["standby", "init", "update_clients", "update_servers", "rollback", ""]}},
        "last_rotated_at": {"validation": "jsonschema", "schema": {"type": "string"}},
        "key_storage": {"validation": "jsonschema", "schema": {"type": "string", "enum": ["software", "aws_kms", "gcp_kms", "pkcs11", ""]}},
        "configuration": {"validation": "jsonschema", "schema": {"type": "object"}},
    }
    CREATE_REQUIRED: ClassVar[list[str]] = ['cluster_name', 'ca_type']

    cluster_name = models.CharField(max_length=512, blank=True, default="", db_index=True)
    ca_type = models.CharField(max_length=64, blank=True, default="")
    rotation_phase = models.CharField(max_length=64, blank=True, default="")
    last_rotated_at = models.CharField(max_length=512, blank=True, default="")
    key_storage = models.CharField(max_length=64, blank=True, default="")
    configuration = models.JSONField(default=dict, blank=True)

    class Meta(BaseModel.Meta):
        db_table = "teleport__teleport_certificate_authority"

    def get_name(self) -> str:
        return f"{self.ca_type} CA · {self.cluster_name}" if self.cluster_name else f"{self.ca_type} CA" or ""

    def __str__(self) -> str:
        return self.get_name()
