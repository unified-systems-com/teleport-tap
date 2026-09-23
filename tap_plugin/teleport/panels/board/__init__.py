"""teleport-board — one section of the /teleport operator page, for one cluster.

Spec: specs/spec-teleport-v0.md (req-teleport-panel-board).

A panel instance names its ``section`` in ``config``; every section reads the same way:

1. Resolve the cluster: ``?cluster=<cluster name>`` (``teleport__teleport_cluster.name``, its natural
   key, matched exactly) when the page was given one, otherwise the single cluster on the grid. With
   several clusters and no parameter (or the every-cluster sentinel the page's searches default to)
   the board says so and picks none — picking one silently would present one cluster's posture as
   "the" cluster's.
2. Run the section's Gryphon reads, each filtered to that cluster by ``cluster_name`` (every
   in-cluster type carries it as part of its natural key). A read that joins two Teleport records
   filters BOTH ends, so a cross-cluster edge never brings a foreign record into the section.
3. Fold the envelopes into rows with pure functions, so the tests need no grid.

Three states, never two: a blank field is *not observed*, and the board says "not observed" in
grey rather than rendering an absence as a pass or a fail. Reads go through Gryphon
(``execute_gryphon_raw``, gated on ``grid.read``).
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, ClassVar

if TYPE_CHECKING:
    from django.http import HttpRequest

    from tap_web.models import Panel

logger = logging.getLogger(__name__)

T_CLUSTER = "teleport__teleport_cluster"
RESOURCE_KINDS: dict[str, str] = {
    "teleport__teleport_ssh_node": "SSH node",
    "teleport__teleport_kube_cluster": "Kubernetes cluster",
    "teleport__teleport_database": "Database",
    "teleport__teleport_app": "Application",
    "teleport__teleport_windows_desktop": "Windows desktop",
}
SECTIONS = ("posture", "roles", "identity", "resources", "requests", "machines", "trust")
NOT_OBSERVED = "not observed"

#: One Gryphon read per key, per section. ``$cluster`` is the resolved cluster's name.
_IN = 'WHERE {v}.data.cluster_name = $cluster'
#: A join between two Teleport records: both ends in the cluster.
_BOTH = 'WHERE {a}.data.cluster_name = $cluster AND {b}.data.cluster_name = $cluster'
#: A join whose other end is untyped (it may be one of several Teleport types): Gryphon can read
#: ``cluster_name`` only on a labelled variable, so that end is scoped by its BELONGS_TO_CLUSTER edge
#: to the cluster named ``$cluster`` instead, bound to ``c``.
_B = "BELONGS_TO_CLUSTER__teleport"
_VIA = 'WHERE {v}.data.cluster_name = $cluster AND c.data.name = $cluster'
QUERIES: dict[str, dict[str, str]] = {
    "posture": {
        "auth": f"MATCH (n:teleport__teleport_auth_server) {_IN.format(v='n')} RETURN n",
        "proxy": f"MATCH (n:teleport__teleport_proxy_server) {_IN.format(v='n')} RETURN n",
        "agent": f"MATCH (n:teleport__teleport_agent) {_IN.format(v='n')} RETURN n",
        "user": f"MATCH (n:teleport__teleport_user) {_IN.format(v='n')} RETURN n",
        "role": f"MATCH (n:teleport__teleport_role) {_IN.format(v='n')} RETURN n",
        "bot": f"MATCH (n:teleport__teleport_bot) {_IN.format(v='n')} RETURN n",
        "request": f"MATCH (n:teleport__teleport_access_request) {_IN.format(v='n')} RETURN n",
        **{k.split("__")[1]: f"MATCH (n:{k}) {_IN.format(v='n')} RETURN n" for k in RESOURCE_KINDS},
    },
    "roles": {
        "role": f"MATCH (n:teleport__teleport_role) {_IN.format(v='n')} RETURN n",
        "grants": f"MATCH (r:teleport__teleport_role)-[e:GRANTS_RESOURCE_ACCESS__teleport]->(x)-[:{_B}]->(c:{T_CLUSTER}) {_VIA.format(v='r')} RETURN r, x",
        "requestable": f"MATCH (r:teleport__teleport_role)-[e:PERMITS_ROLE_REQUEST__teleport]->(x:teleport__teleport_role) {_BOTH.format(a='r', b='x')} RETURN r, x",
        "holders": f"MATCH (c:{T_CLUSTER})<-[:{_B}]-(h)-[e:HOLDS_ROLE__teleport]->(r:teleport__teleport_role) {_VIA.format(v='r')} RETURN h, r",
        "mappings": f"MATCH (c:teleport__teleport_sso_connector)-[e:MAPS_TO_ROLE__teleport]->(r:teleport__teleport_role) {_BOTH.format(a='c', b='r')} RETURN c, r",
        "lists": f"MATCH (l:teleport__teleport_access_list)-[e:GRANTS_ROLE__teleport]->(r:teleport__teleport_role) {_BOTH.format(a='l', b='r')} RETURN l, r",
    },
    "identity": {
        "connector": f"MATCH (n:teleport__teleport_sso_connector) {_IN.format(v='n')} RETURN n",
        "idp": f"MATCH (c:teleport__teleport_sso_connector)-[e:DELEGATES_LOGIN__teleport]->(i) {_IN.format(v='c')} RETURN c, i",
        "user": f"MATCH (n:teleport__teleport_user) {_IN.format(v='n')} RETURN n",
        "list": f"MATCH (n:teleport__teleport_access_list) {_IN.format(v='n')} RETURN n",
        "members": f"MATCH (c:{T_CLUSTER})<-[:{_B}]-(m)-[e:MEMBER_OF_ACCESS_LIST__teleport]->(l:teleport__teleport_access_list) {_VIA.format(v='l')} RETURN m, l",
        "list_roles": f"MATCH (l:teleport__teleport_access_list)-[e:GRANTS_ROLE__teleport]->(r:teleport__teleport_role) {_BOTH.format(a='l', b='r')} RETURN l, r",
        "device": f"MATCH (n:teleport__teleport_trusted_device) {_IN.format(v='n')} RETURN n",
    },
    "resources": {
        **{k.split("__")[1]: f"MATCH (n:{k}) {_IN.format(v='n')} RETURN n" for k in RESOURCE_KINDS},
        "served": f"MATCH (a:teleport__teleport_agent)-[e:SERVES_RESOURCE__teleport]->(x)-[:{_B}]->(c:{T_CLUSTER}) {_VIA.format(v='a')} RETURN a, x",
        "grants": f"MATCH (r:teleport__teleport_role)-[e:GRANTS_RESOURCE_ACCESS__teleport]->(x)-[:{_B}]->(c:{T_CLUSTER}) {_VIA.format(v='r')} RETURN r, x",
    },
    "requests": {
        "request": f"MATCH (n:teleport__teleport_access_request) {_IN.format(v='n')} RETURN n",
        "raised": f"MATCH (u:teleport__teleport_user)-[e:RAISES_ACCESS_REQUEST__teleport]->(q:teleport__teleport_access_request) {_BOTH.format(a='u', b='q')} RETURN u, q",
        "roles": f"MATCH (q:teleport__teleport_access_request)-[e:REQUESTS_ROLE__teleport]->(r:teleport__teleport_role) {_BOTH.format(a='q', b='r')} RETURN q, r",
        "resources": f"MATCH (q:teleport__teleport_access_request)-[e:REQUESTS_RESOURCE__teleport]->(x)-[:{_B}]->(c:{T_CLUSTER}) {_VIA.format(v='q')} RETURN q, x",
        "reviews": f"MATCH (u:teleport__teleport_user)-[e:REVIEWED_ACCESS_REQUEST__teleport]->(q:teleport__teleport_access_request) {_BOTH.format(a='u', b='q')} RETURN u, q",
    },
    "machines": {
        "bot": f"MATCH (n:teleport__teleport_bot) {_IN.format(v='n')} RETURN n",
        "token": f"MATCH (n:teleport__teleport_join_token) {_IN.format(v='n')} RETURN n",
        "agent": f"MATCH (n:teleport__teleport_agent) {_IN.format(v='n')} RETURN n",
        "joins": f"MATCH (c:{T_CLUSTER})<-[:{_B}]-(j)-[e:JOINS_WITH_TOKEN__teleport]->(t:teleport__teleport_join_token) {_VIA.format(v='t')} RETURN j, t",
        "bot_roles": f"MATCH (b:teleport__teleport_bot)-[e:HOLDS_ROLE__teleport]->(r:teleport__teleport_role) {_BOTH.format(a='b', b='r')} RETURN b, r",
        "admits": f"MATCH (t:teleport__teleport_join_token)-[e:ADMITS_IDENTITY__teleport]->(i) {_IN.format(v='t')} RETURN t, i",
    },
    "trust": {
        "ca": f"MATCH (n:teleport__teleport_certificate_authority) {_IN.format(v='n')} RETURN n",
        "keys": f"MATCH (c:teleport__teleport_certificate_authority)-[e:SIGNS_WITH_KEY__teleport]->(k) {_IN.format(v='c')} RETURN c, k",
        "roots": "MATCH (l:teleport__teleport_cluster)-[e:TRUSTS_ROOT_CLUSTER__teleport]->(r:teleport__teleport_cluster) WHERE l.data.name = $cluster RETURN l, r",
        "leaves": "MATCH (l:teleport__teleport_cluster)-[e:TRUSTS_ROOT_CLUSTER__teleport]->(r:teleport__teleport_cluster) WHERE r.data.name = $cluster RETURN l, r",
    },
}
CLUSTERS_QUERY = f"MATCH (c:{T_CLUSTER}) RETURN c"
#: The cluster's members by their BELONGS_TO_CLUSTER edge — the same membership the graph uses.
MEMBERS_QUERY = (
    f"MATCH (n)-[e:BELONGS_TO_CLUSTER__teleport]->(c:{T_CLUSTER}) WHERE c.entity_id = $cluster_id RETURN n, c"
)


# ---------------------------------------------------------------------------
# Envelope helpers
# ---------------------------------------------------------------------------


def _data(node: dict[str, Any]) -> dict[str, Any]:
    data = dict(node.get("data") or {})
    data["entity_id"] = str(node.get("entity_id") or data.get("entity_id") or "")
    data["entity_type"] = str(node.get("entity_type") or "")
    data["_label"] = str(node.get("name") or data.get("name") or "")
    data["_dimensions"] = dict(node.get("dimensions") or {})
    return data


def _obj(value: Any) -> dict[str, Any]:
    """A JSON object field, or an empty dict when it is absent or not an object."""
    return dict(value) if isinstance(value, dict) else {}


def nodes_of(env: dict[str, Any], entity_type: str | None = None) -> list[dict[str, Any]]:
    """Every node in an envelope (optionally of one type), flattened to its data dict."""
    out = []
    for node in env.get("nodes", []) or []:
        if entity_type is None or node.get("entity_type") == entity_type:
            out.append(_data(node))
    return out


def edges_of(env: dict[str, Any], edge_type: str) -> list[tuple[str, str, dict[str, Any]]]:
    """(from_entity_id, to_entity_id, properties) for every edge of one type in an envelope."""
    out = []
    for edge in env.get("edges", []) or []:
        ed = edge.get("data") or edge
        if ed.get("edge_type") == edge_type:
            out.append((str(ed.get("from_entity_id")), str(ed.get("to_entity_id")), dict(ed.get("properties") or {})))
    return out


def index(env: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {n["entity_id"]: n for n in nodes_of(env)}


def _parse_ts(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _age(moment: datetime | None, now: datetime) -> str:
    if moment is None:
        return ""
    seconds = int((now - moment).total_seconds())
    if seconds < 0:
        return "in the future"
    for unit, size in (("d", 86400), ("h", 3600), ("m", 60)):
        if seconds >= size:
            return f"{seconds // size}{unit} ago"
    return "just now"


# ---------------------------------------------------------------------------
# Cluster resolution
# ---------------------------------------------------------------------------


@dataclass
class ClusterChoice:
    cluster: dict[str, Any] | None
    message: str = ""
    others: list[dict[str, Any]] = field(default_factory=list)


def choose_cluster(clusters: list[dict[str, Any]], requested: str) -> ClusterChoice:
    """``?cluster=<cluster name>`` wins, matched exactly; otherwise the only cluster; otherwise none,
    and say why. The every-cluster sentinel (the type slug the page's searches default to) is no
    choice at all, so it reads as absent."""
    clusters = sorted(clusters, key=lambda c: str(c.get("name") or ""))
    if requested == T_CLUSTER:
        requested = ""
    if requested:
        for c in clusters:
            if c.get("name") == requested:
                return ClusterChoice(c, others=[o for o in clusters if o is not c])
        return ClusterChoice(None, f"No Teleport cluster on the grid is named {requested!r}.", clusters)
    if len(clusters) == 1:
        return ClusterChoice(clusters[0])
    if not clusters:
        return ClusterChoice(None, "No Teleport cluster is on the grid yet.")
    return ClusterChoice(None, f"{len(clusters)} Teleport clusters are on the grid; pick one.", clusters)


# ---------------------------------------------------------------------------
# Posture: the cluster's FedRAMP-relevant settings as tiles
# ---------------------------------------------------------------------------


@dataclass
class Tile:
    label: str
    value: str
    tone: str  # good | warn | bad | unknown | info
    note: str = ""


#: For each posture field: the values that meet a FedRAMP 20x expectation (good), the ones that
#: fall short (bad), and a note naming the expectation. Anything else observed is ``warn``.
POSTURE: tuple[tuple[str, str, set[str], set[str], str], ...] = (
    ("fips", "FIPS build", {"enabled"}, {"disabled"}, "FedRAMP requires FIPS 140 validated cryptography: the Enterprise FIPS build started with --fips."),
    ("signature_algorithm_suite", "Signature suite", {"fips-v1", "hsm-v1"}, {"legacy"}, "A FIPS cluster signs with the fips-v1 (or hsm-v1) suite."),
    ("local_auth", "Local auth", {"disabled"}, {"enabled"}, "Every human signs in through the SSO connector; local passwords are a bypass of the IdP."),
    # `on` requires a second factor but admits OTP, so it is not proof of phishing resistance: warn.
    ("second_factor", "Second factor", {"webauthn"}, {"off", "otp"}, "Phishing-resistant MFA (WebAuthn / hardware keys); `on` also admits OTP."),
    ("device_trust_mode", "Device trust", {"required"}, {"off"}, "Access only from enrolled, trusted devices."),
    ("session_recording_mode", "Session recording", {"node-sync", "proxy-sync", "node", "proxy"}, {"off"}, "Every interactive session recorded."),
    ("edition", "Edition", {"enterprise"}, set(), "FIPS builds, HSM/KMS keys, device trust and access lists are Enterprise features."),
)


def posture_tiles(cluster: dict[str, Any]) -> list[Tile]:
    tiles = []
    for key, label, good, bad, note in POSTURE:
        value = str(cluster.get(key) or "")
        if not value:
            tiles.append(Tile(label, NOT_OBSERVED, "unknown", note))
        elif value in good:
            tiles.append(Tile(label, value, "good", note))
        elif value in bad:
            tiles.append(Tile(label, value, "bad", note))
        else:
            tiles.append(Tile(label, value, "warn", note))
    for key, label in (("teleport_version", "Version"), ("proxy_address", "Proxy address")):
        value = str(cluster.get(key) or "")
        tiles.append(Tile(label, value or NOT_OBSERVED, "info" if value else "unknown"))
    return tiles


def inventory(envs: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Counts for the posture strip: the deployment, the principals, the resources."""
    users = nodes_of(envs.get("user", {}))
    local = sum(1 for u in users if u.get("user_type") == "local")
    sso = sum(1 for u in users if u.get("user_type") == "sso")
    pending = sum(1 for r in nodes_of(envs.get("request", {})) if r.get("state") == "PENDING")
    items = [
        {"label": "Auth servers", "count": len(nodes_of(envs.get("auth", {})))},
        {"label": "Proxies", "count": len(nodes_of(envs.get("proxy", {})))},
        {"label": "Agents", "count": len(nodes_of(envs.get("agent", {})))},
        {"label": "Roles", "count": len(nodes_of(envs.get("role", {})))},
        {"label": "Users", "count": len(users), "detail": f"{sso} SSO · {local} local" if users else ""},
        {"label": "Bots", "count": len(nodes_of(envs.get("bot", {})))},
        {"label": "Pending requests", "count": pending, "tone": "warn" if pending else ""},
    ]
    resources = sum(len(nodes_of(envs.get(k.split("__")[1], {}))) for k in RESOURCE_KINDS)
    items.append({"label": "Protected resources", "count": resources})
    if local:
        items[4]["tone"] = "bad"
    return items


# ---------------------------------------------------------------------------
# Roles
# ---------------------------------------------------------------------------

_LABEL_KEYS = (
    ("node_labels", "SSH"), ("kubernetes_labels", "Kube"), ("db_labels", "DB"),
    ("app_labels", "App"), ("windows_desktop_labels", "Desktop"),
)


def _selectors(allow: dict[str, Any]) -> list[str]:
    out = []
    for key, kind in _LABEL_KEYS:
        sel = allow.get(key)
        if isinstance(sel, dict) and sel:
            parts = [f"{k}={'|'.join(v) if isinstance(v, list) else v}" for k, v in sorted(sel.items())]
            out.append(f"{kind}: {', '.join(parts)}")
    return out


@dataclass
class RoleRow:
    entity_id: str
    name: str
    origin: str
    logins: list[str]
    selectors: list[str]
    reach: dict[str, int]
    requestable: list[str]
    session_mfa: str
    max_ttl: str
    has_deny: bool | None
    held_by: list[str]
    mapped_from: list[str]
    via_lists: list[str]
    observed: bool

    @property
    def reach_text(self) -> str:
        return ", ".join(f"{n} {k}" for k, n in sorted(self.reach.items())) if self.reach else ""


def role_rows(envs: dict[str, dict[str, Any]]) -> list[RoleRow]:
    roles = nodes_of(envs.get("role", {}), "teleport__teleport_role")
    names = {r["entity_id"]: r.get("name") or r["_label"] for r in roles}
    reach: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    grants_env = envs.get("grants", {})
    targets = index(grants_env)
    for src, dst, _props in edges_of(grants_env, "GRANTS_RESOURCE_ACCESS__teleport"):
        kind = RESOURCE_KINDS.get(targets.get(dst, {}).get("entity_type", ""), "resource")
        reach[src][kind] += 1
    requestable: dict[str, list[str]] = defaultdict(list)
    req_env = envs.get("requestable", {})
    req_names = {n["entity_id"]: n.get("name") or n["_label"] for n in nodes_of(req_env)}
    for src, dst, props in edges_of(req_env, "PERMITS_ROLE_REQUEST__teleport"):
        n = props.get("approvals_required")
        requestable[src].append(req_names.get(dst, dst) + (f" ({n} approval{'s' if n != 1 else ''})" if isinstance(n, int) else ""))
    held: dict[str, list[str]] = defaultdict(list)
    hold_env = envs.get("holders", {})
    holders = index(hold_env)
    for src, dst, props in edges_of(hold_env, "HOLDS_ROLE__teleport"):
        h = holders.get(src, {})
        kind = "bot" if h.get("entity_type") == "teleport__teleport_bot" else "user"
        how = props.get("granted_by") or ""
        held[dst].append(f"{h.get('_label') or src} ({kind}{', ' + how.replace('_', ' ') if how else ''})")
    mapped: dict[str, list[str]] = defaultdict(list)
    map_env = envs.get("mappings", {})
    conns = index(map_env)
    for src, dst, props in edges_of(map_env, "MAPS_TO_ROLE__teleport"):
        attr = props.get("attribute") or "?"
        val = props.get("value") or "?"
        mapped[dst].append(f"{conns.get(src, {}).get('_label') or src}: {attr}={val}")
    lists: dict[str, list[str]] = defaultdict(list)
    list_env = envs.get("lists", {})
    lnodes = index(list_env)
    for src, dst, _props in edges_of(list_env, "GRANTS_ROLE__teleport"):
        lists[dst].append(lnodes.get(src, {}).get("title") or lnodes.get(src, {}).get("_label") or src)
    rows = []
    for r in roles:
        allow = _obj(r.get("allow"))
        deny = _obj(r.get("deny"))
        options = _obj(r.get("options"))
        observed = bool(allow or deny or options)
        rows.append(RoleRow(
            entity_id=r["entity_id"],
            name=names[r["entity_id"]],
            origin=str(r.get("origin") or ""),
            logins=[str(x) for x in (allow.get("logins") or [])],
            selectors=_selectors(allow),
            reach=dict(reach.get(r["entity_id"], {})),
            requestable=sorted(requestable.get(r["entity_id"], [])),
            session_mfa=str(options.get("require_session_mfa") or ""),
            max_ttl=str(options.get("max_session_ttl") or ""),
            has_deny=bool(deny) if observed else None,
            held_by=sorted(held.get(r["entity_id"], [])),
            mapped_from=sorted(mapped.get(r["entity_id"], [])),
            via_lists=sorted(lists.get(r["entity_id"], [])),
            observed=observed,
        ))
    rows.sort(key=lambda x: (-sum(x.reach.values()), x.name.lower()))
    return rows


# ---------------------------------------------------------------------------
# Identity: connectors, users, access lists, devices
# ---------------------------------------------------------------------------


def identity_view(envs: dict[str, dict[str, Any]], now: datetime) -> dict[str, Any]:
    idp_env = envs.get("idp", {})
    idps = index(idp_env)
    idp_of: dict[str, list[str]] = defaultdict(list)
    for src, dst, _p in edges_of(idp_env, "DELEGATES_LOGIN__teleport"):
        idp_of[src].append(idps.get(dst, {}).get("_label") or dst)
    connectors = [
        {
            "name": c.get("name") or c["_label"],
            "kind": c.get("kind") or "",
            "display": c.get("display") or "",
            "idp_url": c.get("idp_url") or "",
            "idp": ", ".join(sorted(idp_of.get(c["entity_id"], []))),
        }
        for c in nodes_of(envs.get("connector", {}), "teleport__teleport_sso_connector")
    ]
    connectors.sort(key=lambda c: (c["kind"], c["name"].lower()))
    users = nodes_of(envs.get("user", {}), "teleport__teleport_user")
    by_type: dict[str, int] = defaultdict(int)
    for u in users:
        by_type[u.get("user_type") or "unknown"] += 1
    local_users = sorted(u.get("name") or u["_label"] for u in users if u.get("user_type") == "local")
    members_env = envs.get("members", {})
    owners: dict[str, int] = defaultdict(int)
    members: dict[str, int] = defaultdict(int)
    for _src, dst, props in edges_of(members_env, "MEMBER_OF_ACCESS_LIST__teleport"):
        if props.get("membership") == "owner":
            owners[dst] += 1
        else:
            members[dst] += 1
    lr_env = envs.get("list_roles", {})
    lr_nodes = index(lr_env)
    list_roles: dict[str, list[str]] = defaultdict(list)
    for src, dst, _props in edges_of(lr_env, "GRANTS_ROLE__teleport"):
        list_roles[src].append(lr_nodes.get(dst, {}).get("_label") or dst)
    lists = []
    for lst in nodes_of(envs.get("list", {}), "teleport__teleport_access_list"):
        due = _parse_ts(lst.get("next_audit_date"))
        state = "unknown" if due is None else ("bad" if due < now else "good")
        lists.append({
            "title": lst.get("title") or lst.get("name") or lst["_label"],
            "roles": ", ".join(sorted(list_roles.get(lst["entity_id"], []))),
            "owners": owners.get(lst["entity_id"], 0),
            "members": members.get(lst["entity_id"], 0),
            "frequency": lst.get("audit_frequency") or "",
            "due": due,
            "due_text": ("overdue — " if state == "bad" else "") + (lst.get("next_audit_date") or NOT_OBSERVED),
            "due_tone": state,
        })
    lists.sort(key=lambda x: (x["due_tone"] != "bad", x["title"].lower()))
    devices = nodes_of(envs.get("device", {}), "teleport__teleport_trusted_device")
    enrolled = sum(1 for d in devices if d.get("enroll_status") == "enrolled")
    return {
        "connectors": connectors,
        "user_total": len(users),
        "user_by_type": dict(by_type),
        "local_users": local_users,
        "access_lists": lists,
        "devices": {"total": len(devices), "enrolled": enrolled, "unknown": sum(1 for d in devices if not d.get("enroll_status"))},
    }


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------


def resource_view(envs: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    served_env = envs.get("served", {})
    agents = index(served_env)
    served_by: dict[str, list[str]] = defaultdict(list)
    for src, dst, _p in edges_of(served_env, "SERVES_RESOURCE__teleport"):
        served_by[dst].append(agents.get(src, {}).get("_label") or src)
    grants_env = envs.get("grants", {})
    gnodes = index(grants_env)
    reached_by: dict[str, list[str]] = defaultdict(list)
    for src, dst, props in edges_of(grants_env, "GRANTS_RESOURCE_ACCESS__teleport"):
        who = gnodes.get(src, {}).get("_label") or src
        principals = props.get("principals") or []
        reached_by[dst].append(who + (f" as {', '.join(principals)}" if principals else ""))
    groups = []
    for etype, kind in RESOURCE_KINDS.items():
        rows = []
        for n in nodes_of(envs.get(etype.split("__")[1], {}), etype):
            labels = _obj(n.get("labels"))
            rows.append({
                "name": n.get("name") or n.get("hostname") or n["_label"],
                "detail": n.get("protocol") or n.get("sub_kind") or n.get("public_addr") or n.get("addr") or n.get("uri") or "",
                "labels": [f"{k}={v}" for k, v in sorted(labels.items())],
                "served_by": ", ".join(sorted(served_by.get(n["entity_id"], []))),
                "reached_by": sorted(reached_by.get(n["entity_id"], [])),
            })
        rows.sort(key=lambda r: r["name"].lower())
        label_counts: dict[str, int] = defaultdict(int)
        for r in rows:
            for lab in r["labels"]:
                label_counts[lab] += 1
        groups.append({"kind": kind, "rows": rows, "labels": sorted(label_counts.items())})
    return groups


# ---------------------------------------------------------------------------
# Access requests
# ---------------------------------------------------------------------------


def request_rows(envs: dict[str, dict[str, Any]], now: datetime) -> list[dict[str, Any]]:
    raised_env = envs.get("raised", {})
    who = index(raised_env)
    requester: dict[str, str] = {}
    for src, dst, _p in edges_of(raised_env, "RAISES_ACCESS_REQUEST__teleport"):
        requester[dst] = who.get(src, {}).get("_label") or src
    wanted: dict[str, list[str]] = defaultdict(list)
    for key, et in (("roles", "REQUESTS_ROLE__teleport"), ("resources", "REQUESTS_RESOURCE__teleport")):
        env = envs.get(key, {})
        idx = index(env)
        for src, dst, _p in edges_of(env, et):
            wanted[src].append(idx.get(dst, {}).get("_label") or dst)
    rev_env = envs.get("reviews", {})
    rev = index(rev_env)
    reviews: dict[str, list[str]] = defaultdict(list)
    for src, dst, props in edges_of(rev_env, "REVIEWED_ACCESS_REQUEST__teleport"):
        reviews[dst].append(f"{rev.get(src, {}).get('_label') or src}: {props.get('proposal') or '?'}")
    rows = []
    for q in nodes_of(envs.get("request", {}), "teleport__teleport_access_request"):
        state = q.get("state") or ""
        expires = _parse_ts(q.get("expires_at"))
        live = state == "PENDING" or (state == "APPROVED" and (expires is None or expires > now))
        if not live:
            continue
        created = _parse_ts(q.get("created_at"))
        rows.append({
            "id": q.get("name") or q["_label"],
            "state": state,
            "requester": requester.get(q["entity_id"], ""),
            "wants": ", ".join(sorted(wanted.get(q["entity_id"], []))),
            "reason": q.get("reason") or "",
            "age": _age(created, now),
            "created": created,
            "expires": q.get("expires_at") or "",
            "reviews": sorted(reviews.get(q["entity_id"], [])),
        })
    rows.sort(key=lambda r: (r["state"] != "PENDING", r["created"] or now))
    return rows


# ---------------------------------------------------------------------------
# Machines: bots, join tokens, agents
# ---------------------------------------------------------------------------

#: A token that is a shared secret is a standing credential; every other method binds the join to a
#: workload identity the platform attests.
STATIC_METHODS = frozenset({"token"})


def machine_view(envs: dict[str, dict[str, Any]], now: datetime) -> dict[str, Any]:
    joins_env = envs.get("joins", {})
    jidx = index(joins_env)
    token_of: dict[str, list[dict[str, Any]]] = defaultdict(list)
    joiners: dict[str, list[str]] = defaultdict(list)
    for src, dst, _p in edges_of(joins_env, "JOINS_WITH_TOKEN__teleport"):
        token_of[src].append(jidx.get(dst, {}))
        joiners[dst].append(jidx.get(src, {}).get("_label") or src)
    br_env = envs.get("bot_roles", {})
    bidx = index(br_env)
    bot_roles: dict[str, list[str]] = defaultdict(list)
    for src, dst, _p in edges_of(br_env, "HOLDS_ROLE__teleport"):
        bot_roles[src].append(bidx.get(dst, {}).get("_label") or dst)
    ad_env = envs.get("admits", {})
    aidx = index(ad_env)
    admits: dict[str, list[str]] = defaultdict(list)
    for src, dst, _p in edges_of(ad_env, "ADMITS_IDENTITY__teleport"):
        admits[src].append(aidx.get(dst, {}).get("_label") or dst)

    def _methods(eid: str) -> str:
        return ", ".join(sorted({t.get("join_method") or "?" for t in token_of.get(eid, [])}))

    bots = [
        {
            "name": b.get("name") or b["_label"],
            "roles": ", ".join(sorted(bot_roles.get(b["entity_id"], []))),
            "join": _methods(b["entity_id"]),
            "static": any((t.get("join_method") in STATIC_METHODS) for t in token_of.get(b["entity_id"], [])),
            "ttl": b.get("max_session_ttl") or "",
        }
        for b in nodes_of(envs.get("bot", {}), "teleport__teleport_bot")
    ]
    tokens = []
    for t in nodes_of(envs.get("token", {}), "teleport__teleport_join_token"):
        expires = _parse_ts(t.get("expires_at"))
        tokens.append({
            "name": t.get("name") or t["_label"],
            "method": t.get("join_method") or "",
            "static": (t.get("join_method") or "") in STATIC_METHODS,
            "roles": ", ".join(t.get("system_roles") or []),
            "admits": ", ".join(sorted(admits.get(t["entity_id"], []))),
            "joiners": ", ".join(sorted(joiners.get(t["entity_id"], []))),
            "expires": t.get("expires_at") or "",
            "expired": bool(expires and expires < now),
        })
    agents = [
        {
            "name": a.get("name") or a["_label"],
            "version": a.get("teleport_version") or "",
            "services": ", ".join(a.get("services") or []),
            "join": _methods(a["entity_id"]),
        }
        for a in nodes_of(envs.get("agent", {}), "teleport__teleport_agent")
    ]
    for rows in (bots, tokens, agents):
        rows.sort(key=lambda r: str(r["name"]).lower())
    return {"bots": bots, "tokens": tokens, "agents": agents}


# ---------------------------------------------------------------------------
# Trust: CAs and trusted clusters
# ---------------------------------------------------------------------------

_KEY_TONE = {"aws_kms": "good", "gcp_kms": "good", "pkcs11": "good", "software": "warn"}


def trust_view(envs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    keys_env = envs.get("keys", {})
    kidx = index(keys_env)
    key_of: dict[str, list[str]] = defaultdict(list)
    for src, dst, props in edges_of(keys_env, "SIGNS_WITH_KEY__teleport"):
        state = props.get("key_state")
        key_of[src].append((kidx.get(dst, {}).get("_label") or dst) + (f" ({state.replace('_', ' ')})" if state else ""))
    cas = []
    for ca in nodes_of(envs.get("ca", {}), "teleport__teleport_certificate_authority"):
        phase = ca.get("rotation_phase") or ""
        storage = ca.get("key_storage") or ""
        cas.append({
            "type": ca.get("ca_type") or "",
            "phase": phase or NOT_OBSERVED,
            "phase_tone": "unknown" if not phase else ("good" if phase == "standby" else "warn"),
            "rotated": ca.get("last_rotated_at") or "",
            "storage": storage or NOT_OBSERVED,
            "storage_tone": _KEY_TONE.get(storage, "unknown" if not storage else "warn"),
            "keys": ", ".join(sorted(key_of.get(ca["entity_id"], []))),
        })
    cas.sort(key=lambda c: c["type"])
    trusts = []
    for key, direction in (("roots", "root"), ("leaves", "leaf")):
        env = envs.get(key, {})
        idx = index(env)
        for src, dst, props in edges_of(env, "TRUSTS_ROOT_CLUSTER__teleport"):
            peer = idx.get(dst if direction == "root" else src, {})
            role_map = props.get("role_map") or []
            trusts.append({
                "direction": direction,
                "peer": peer.get("_label") or "",
                "peer_name": peer.get("name") or "",
                "enabled": props.get("enabled"),
                "status": props.get("connection_status") or "",
                "role_map": ", ".join(
                    f"{m.get('remote', '?')}→{', '.join(m.get('local') or []) if isinstance(m.get('local'), list) else m.get('local', '?')}"
                    for m in role_map if isinstance(m, dict)
                ),
            })
    return {"cas": cas, "trusts": trusts}


# ---------------------------------------------------------------------------
# The panel type
# ---------------------------------------------------------------------------


def _fetch(queries: dict[str, str], cluster_name: str) -> dict[str, dict[str, Any]]:
    from tap_grid.gryphon.executor import execute_gryphon_raw

    return {key: execute_gryphon_raw(q, {"cluster": cluster_name}, layer="full") for key, q in queries.items()}


@dataclass
class Scope:
    """What the board may show for one cluster, and what it refused to."""

    member_ids: set[str]
    #: Records whose `cluster_name` names this cluster but which have no BELONGS_TO_CLUSTER edge to it.
    unlinked: list[str] = field(default_factory=list)
    #: dcom values across the cluster and its members: {"design": n, "observed": m}.
    provenance: dict[str, int] = field(default_factory=dict)

    @property
    def provenance_label(self) -> str:
        design = self.provenance.get("design", 0)
        other = sum(v for k, v in self.provenance.items() if k != "design")
        if design and not other:
            return "design"
        if design:
            return f"mixed: {design} design · {other} not design"
        return ""


def membership(members_env: dict[str, Any], cluster: dict[str, Any]) -> Scope:
    """The member ids (from the edge) and the provenance mix of the cluster plus its members."""
    ids = {n["entity_id"] for n in nodes_of(members_env) if n["entity_type"] != T_CLUSTER}
    prov: dict[str, int] = defaultdict(int)
    for n in [cluster, *[m for m in nodes_of(members_env) if m["entity_id"] in ids]]:
        prov["design" if n["_dimensions"].get("dcom") == "design" else "other"] += 1
    return Scope(member_ids=ids, provenance=dict(prov))


def scope_envs(envs: dict[str, dict[str, Any]], scope: Scope) -> dict[str, dict[str, Any]]:
    """Keep only in-cluster records that BELONG to the cluster by edge (cluster and foreign nodes pass
    through); drop edges that touch a dropped record. A record the name column claims but the edge
    does not is recorded in ``scope.unlinked`` rather than shown — the board and the graph must agree."""
    out: dict[str, dict[str, Any]] = {}
    unlinked: set[str] = set(scope.unlinked)
    for key, env in envs.items():
        keep_nodes, dropped = [], set()
        for node in env.get("nodes", []) or []:
            etype = str(node.get("entity_type") or "")
            eid = str(node.get("entity_id") or "")
            if etype.startswith("teleport__") and etype != T_CLUSTER and eid not in scope.member_ids:
                dropped.add(eid)
                unlinked.add(f"{node.get('name') or eid} ({etype.split('__', 1)[1]})")
                continue
            keep_nodes.append(node)
        keep_edges = []
        for edge in env.get("edges", []) or []:
            ed = edge.get("data") or edge
            if str(ed.get("from_entity_id")) in dropped or str(ed.get("to_entity_id")) in dropped:
                continue
            keep_edges.append(edge)
        out[key] = {**env, "nodes": keep_nodes, "edges": keep_edges}
    scope.unlinked = sorted(unlinked)
    return out


def build_section(section: str, envs: dict[str, dict[str, Any]], cluster: dict[str, Any], now: datetime) -> dict[str, Any]:
    """The template context for one section, from its envelopes. Pure: the tests call it directly."""
    if section == "posture":
        return {"tiles": posture_tiles(cluster), "inventory": inventory(envs)}
    if section == "roles":
        return {"roles": role_rows(envs)}
    if section == "identity":
        return identity_view(envs, now)
    if section == "resources":
        return {"groups": resource_view(envs)}
    if section == "requests":
        return {"requests": request_rows(envs, now)}
    if section == "machines":
        return machine_view(envs, now)
    if section == "trust":
        return trust_view(envs)
    raise ValueError(f"unknown section {section!r}")


class TeleportBoardPanelType:
    """One section of the /teleport operator board, for the resolved cluster."""

    slug: ClassVar[str] = "teleport-board"
    label: ClassVar[str] = "Teleport board"
    view: ClassVar[str] = "teleport/panels/board.html"
    css: ClassVar[list[str]] = ["teleport/css/board.css"]
    js: ClassVar[list[str]] = []
    editor_view: ClassVar[str] = ""
    config_defaults: ClassVar[dict[str, Any]] = {"section": "posture"}

    @classmethod
    def get_view_context(cls, panel: Panel, request: HttpRequest) -> dict[str, Any]:
        config = dict(cls.config_defaults)
        config.update(panel.config or {})
        section = str(config.get("section") or "posture")
        base: dict[str, Any] = {
            "section": section,
            "title": config.get("title") or section.title(),
            "intro": config.get("intro") or "",
            "board_error": None,
            "cluster": None,
            "choice_message": "",
            "clusters": [],
            "provenance": "",
            "unlinked": [],
        }
        if section not in SECTIONS:
            base["board_error"] = f"Unknown board section {section!r}."
            return base
        from tap_grid.gryphon.executor import execute_gryphon_raw

        try:
            clusters = nodes_of(execute_gryphon_raw(CLUSTERS_QUERY, {}, layer="full"), T_CLUSTER)
        except Exception:  # noqa: BLE001 — the panel renders its failure, never a blank frame
            logger.exception("[7d31] teleport board: cluster read failed for panel %s", panel.entity_id)
            base["board_error"] = "The cluster read failed — see the server log ([7d31])."
            return base
        choice = choose_cluster(clusters, str(request.GET.get("cluster") or ""))
        base["clusters"] = [{"name": c.get("name") or c["_label"], "entity_id": c["entity_id"]} for c in choice.others]
        base["choice_message"] = choice.message
        if choice.cluster is None:
            return base
        cluster = choice.cluster
        base["cluster"] = {"name": cluster.get("name") or cluster["_label"], "entity_id": cluster["entity_id"]}
        try:
            scope = membership(
                execute_gryphon_raw(MEMBERS_QUERY, {"cluster_id": cluster["entity_id"]}, layer="full"), cluster
            )
            envs = scope_envs(_fetch(QUERIES[section], base["cluster"]["name"]), scope)
            base["provenance"] = scope.provenance_label
            base["unlinked"] = scope.unlinked
            base.update(build_section(section, envs, cluster, datetime.now(UTC)))
        except Exception:  # noqa: BLE001
            logger.exception("[7d32] teleport board: section %s reads failed for panel %s", section, panel.entity_id)
            base["board_error"] = f"The {section} reads failed — see the server log ([7d32])."
        return base
