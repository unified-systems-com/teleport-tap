"""A small HA Teleport design written through the service layer, shared by the board and page tests.

Shape (the AWS HA reference): two auth servers, two proxies, one agent serving a database and an SSH
node, host/user/db CAs, a leaf cluster trusting this one, a
SAML connector mapping a group to a role, users, a bot joining with a token, an access list and a
pending request. The open-end targets (compute, tables, bucket, KMS key, IdP) are other
plugins' types, so they are left out: teleport's tests depend on no other plugin.
"""

from __future__ import annotations

from typing import Any

from tap_grid.caller_context import CallerContext
from tap_grid.services import WriteOperation, write_batch

CLUSTER = "stg"


def node(type_slug: str, payload: dict[str, Any], dimensions: dict[str, str] | None = None) -> str:
    op = WriteOperation(verb="create_node", type_slug=type_slug, payload=payload, dimensions=dimensions or {})
    result = write_batch([op], caller_context=CallerContext()).results[0]
    assert result.success, result
    return str(result.entity_id)


def edge(src: str, dst: str, edge_type: str, properties: dict[str, Any] | None = None) -> None:
    payload = {"properties": properties} if properties else {}
    op = WriteOperation(verb="create_edge", from_target=src, to_target=dst, edge_type=edge_type, payload=payload)
    result = write_batch([op], caller_context=CallerContext()).results[0]
    assert result.success, result


def member(type_slug: str, payload: dict[str, Any], cluster_id: str, cluster_name: str = CLUSTER) -> str:
    eid = node(type_slug, {"cluster_name": cluster_name, **payload}, {"dcom": "design"})
    edge(eid, cluster_id, "BELONGS_TO_CLUSTER__teleport")
    return eid


def seed() -> dict[str, str]:
    ids: dict[str, str] = {}
    c = ids["cluster"] = node("teleport__teleport_cluster", {
        "name": CLUSTER, "fips": "enabled", "local_auth": "disabled", "second_factor": "webauthn",
        "device_trust_mode": "optional", "edition": "enterprise",
    }, {"dcom": "design"})
    ids["leaf"] = node("teleport__teleport_cluster", {"name": "leaf"})
    edge(ids["leaf"], c, "TRUSTS_ROOT_CLUSTER__teleport", {"role_map": [{"remote": "admin", "local": ["access"]}], "enabled": True})
    for n in ("auth-a", "auth-b"):
        ids[n] = member("teleport__teleport_auth_server", {"name": n}, c)
    for n in ("proxy-a", "proxy-b"):
        ids[n] = member("teleport__teleport_proxy_server", {"name": n}, c)
        for a in ("auth-a", "auth-b"):
            edge(ids[n], ids[a], "CALLS_AUTH_API__teleport")
    ids["agent"] = member("teleport__teleport_agent", {"name": "agent-1", "services": ["db", "ssh"]}, c)
    edge(ids["agent"], ids["proxy-a"], "DIALS_REVERSE_TUNNEL__teleport")
    ids["db"] = member("teleport__teleport_database", {"name": "app-db", "protocol": "postgres", "labels": {"env": "stg"}}, c)
    ids["ssh"] = member("teleport__teleport_ssh_node", {"hostname": "bastion", "labels": {"env": "stg"}}, c)
    for r in ("db", "ssh"):
        edge(ids["agent"], ids[r], "SERVES_RESOURCE__teleport")
    for ca in ("host", "user"):
        ids[f"ca-{ca}"] = member("teleport__teleport_certificate_authority", {"ca_type": ca, "rotation_phase": "standby", "key_storage": "aws_kms"}, c)
    ids["db-ca"] = member("teleport__teleport_certificate_authority", {"ca_type": "db"}, c)
    ids["access"] = member("teleport__teleport_role", {"name": "access", "allow": {"logins": ["ec2-user"], "node_labels": {"env": ["stg"]}}, "options": {"require_session_mfa": "true"}}, c)
    ids["admin"] = member("teleport__teleport_role", {"name": "admin"}, c)
    edge(ids["access"], ids["ssh"], "GRANTS_RESOURCE_ACCESS__teleport", {"principals": ["ec2-user"], "match": "labels"})
    edge(ids["access"], ids["admin"], "PERMITS_ROLE_REQUEST__teleport", {"approvals_required": 2})
    ids["saml"] = member("teleport__teleport_sso_connector", {"name": "okta", "kind": "saml", "idp_url": "https://example.okta.com/app/x/sso/saml/metadata"}, c)
    edge(ids["saml"], ids["access"], "MAPS_TO_ROLE__teleport", {"attribute": "groups", "value": "engineers"})
    ids["alice"] = member("teleport__teleport_user", {"name": "alice", "user_type": "sso"}, c)
    ids["breakglass"] = member("teleport__teleport_user", {"name": "breakglass", "user_type": "local"}, c)
    edge(ids["alice"], ids["access"], "HOLDS_ROLE__teleport", {"granted_by": "sso_mapping"})
    edge(ids["alice"], ids["saml"], "LOGS_IN_VIA_CONNECTOR__teleport")
    ids["bot"] = member("teleport__teleport_bot", {"name": "gitlab-ci"}, c)
    ids["token"] = member("teleport__teleport_join_token", {"name": "sha256:" + "ab" * 32, "join_method": "token", "system_roles": ["Bot"]}, c)
    edge(ids["bot"], ids["token"], "JOINS_WITH_TOKEN__teleport")
    edge(ids["bot"], ids["access"], "HOLDS_ROLE__teleport", {"granted_by": "static"})
    ids["list"] = member("teleport__teleport_access_list", {"name": "admins", "title": "Admins", "next_audit_date": "2020-01-01T00:00:00Z"}, c)
    edge(ids["list"], ids["admin"], "GRANTS_ROLE__teleport", {"audience": "member"})
    edge(ids["alice"], ids["list"], "MEMBER_OF_ACCESS_LIST__teleport", {"membership": "owner"})
    ids["req"] = member("teleport__teleport_access_request", {"name": "req-1", "state": "PENDING", "reason": "incident", "created_at": "2026-09-22T10:00:00Z"}, c)
    ids["req-old"] = member("teleport__teleport_access_request", {"name": "req-0", "state": "DENIED"}, c)
    edge(ids["alice"], ids["req"], "RAISES_ACCESS_REQUEST__teleport")
    edge(ids["req"], ids["admin"], "REQUESTS_ROLE__teleport")
    return ids


OTHER = "prod"


def outside(label: str) -> str:
    """A stand-in for another platform's record at an edge's open end (an EC2 instance, a DynamoDB
    table, a KMS key). teleport's tests depend on no other plugin, so it is a teleport user that
    belongs to no cluster; only the scene searches' open ends read it."""
    return node("teleport__teleport_user", {"name": label, "cluster_name": "outside"})


def seed_second(ids: dict[str, str], open_ends: bool = True) -> dict[str, str]:
    """A second cluster, ``prod``, beside the ``stg`` design from :func:`seed`, with an edge of every
    drawn type and every board join crossing between the two. Nothing of prod's may appear on stg's
    page, nor stg's on prod's. Adds its ids to ``ids`` with a ``prod-`` prefix and returns them.

    ``open_ends`` also gives each cluster a stand-in (:func:`outside`) at every open-end edge, for the
    scene searches; the board leaves it off, because it reports a Teleport-typed record that belongs to
    no cluster, which is what the stand-in is."""
    o = ids["prod-cluster"] = node("teleport__teleport_cluster", {"name": OTHER})

    def m(key: str, type_slug: str, payload: dict[str, Any]) -> str:
        ids[key] = member(type_slug, payload, o, OTHER)
        return ids[key]

    m("prod-auth", "teleport__teleport_auth_server", {"name": "prod-auth"})
    m("prod-proxy", "teleport__teleport_proxy_server", {"name": "prod-proxy"})
    m("prod-agent", "teleport__teleport_agent", {"name": "prod-agent"})
    m("prod-db", "teleport__teleport_database", {"name": "prod-db"})
    m("prod-ca", "teleport__teleport_certificate_authority", {"ca_type": "host"})
    m("prod-role", "teleport__teleport_role", {"name": "prod-role"})
    m("prod-user", "teleport__teleport_user", {"name": "prod-user", "user_type": "sso"})
    m("prod-bot", "teleport__teleport_bot", {"name": "prod-bot"})
    m("prod-token", "teleport__teleport_join_token", {"name": "prod-token", "join_method": "iam"})
    m("prod-list", "teleport__teleport_access_list", {"name": "prod-list", "title": "Prod list"})
    m("prod-req", "teleport__teleport_access_request", {"name": "prod-req", "state": "PENDING"})
    m("prod-saml", "teleport__teleport_sso_connector", {"name": "prod-saml", "kind": "saml"})
    # Each cluster's own open-end targets, so every open-end search has something to find.
    for pre, auth, agent, ca, res in (("stg", "auth-a", "agent", "ca-host", "db"), ("prod", "prod-auth", "prod-agent", "prod-ca", "prod-db"))[: 2 if open_ends else 0]:
        for et in ("RUNS_ON_COMPUTE", "STORES_CLUSTER_STATE", "WRITES_AUDIT_EVENTS", "UPLOADS_SESSION_RECORDINGS"):
            ids[f"{pre}-{et}"] = outside(f"{pre} {et.lower()} target")
            edge(ids[auth], ids[f"{pre}-{et}"], f"{et}__teleport")
        ids[f"{pre}-key"] = outside(f"{pre} kms key")
        edge(ids[ca], ids[f"{pre}-key"], "SIGNS_WITH_KEY__teleport")
        ids[f"{pre}-target"] = outside(f"{pre} rds instance")
        edge(ids[res], ids[f"{pre}-target"], "FRONTS_TARGET__teleport")
        ids[f"{pre}-agent-host"] = outside(f"{pre} agent host")
        edge(ids[agent], ids[f"{pre}-agent-host"], "RUNS_ON_COMPUTE__teleport")
    # prod's own deployment edges, so its page draws each type too.
    edge(ids["prod-proxy"], ids["prod-auth"], "CALLS_AUTH_API__teleport")
    edge(ids["prod-agent"], ids["prod-proxy"], "DIALS_REVERSE_TUNNEL__teleport")
    edge(ids["prod-agent"], ids["prod-db"], "SERVES_RESOURCE__teleport")
    # Cross-cluster edges, both directions, one per drawn edge type and board join.
    edge(ids["proxy-a"], ids["prod-auth"], "CALLS_AUTH_API__teleport")
    edge(ids["prod-proxy"], ids["auth-a"], "CALLS_AUTH_API__teleport")
    edge(ids["prod-agent"], ids["proxy-a"], "DIALS_REVERSE_TUNNEL__teleport")
    edge(ids["agent"], ids["prod-db"], "SERVES_RESOURCE__teleport")
    edge(ids["prod-agent"], ids["db"], "SERVES_RESOURCE__teleport")
    edge(ids["access"], ids["prod-db"], "GRANTS_RESOURCE_ACCESS__teleport")
    edge(ids["access"], ids["prod-role"], "PERMITS_ROLE_REQUEST__teleport")
    edge(ids["prod-user"], ids["access"], "HOLDS_ROLE__teleport", {"granted_by": "static"})
    edge(ids["prod-bot"], ids["access"], "HOLDS_ROLE__teleport", {"granted_by": "static"})
    edge(ids["bot"], ids["prod-role"], "HOLDS_ROLE__teleport", {"granted_by": "static"})
    edge(ids["prod-saml"], ids["access"], "MAPS_TO_ROLE__teleport", {"attribute": "groups", "value": "x"})
    edge(ids["prod-list"], ids["access"], "GRANTS_ROLE__teleport", {"audience": "member"})
    edge(ids["list"], ids["prod-role"], "GRANTS_ROLE__teleport", {"audience": "member"})
    edge(ids["prod-user"], ids["list"], "MEMBER_OF_ACCESS_LIST__teleport", {"membership": "member"})
    edge(ids["prod-user"], ids["req"], "REVIEWED_ACCESS_REQUEST__teleport", {"proposal": "approve"})
    edge(ids["alice"], ids["prod-req"], "RAISES_ACCESS_REQUEST__teleport")
    edge(ids["req"], ids["prod-role"], "REQUESTS_ROLE__teleport")
    edge(ids["req"], ids["prod-db"], "REQUESTS_RESOURCE__teleport")
    edge(ids["bot"], ids["prod-token"], "JOINS_WITH_TOKEN__teleport")
    edge(ids["prod-bot"], ids["token"], "JOINS_WITH_TOKEN__teleport")
    return {k: v for k, v in ids.items() if k.startswith("prod")}
