# TAP Teleport Plugin Specification

**Teleport infrastructure access as grid vocabulary: a Teleport cluster's HA deployment (auth and proxy tiers, agents, and the compute, storage and keys they use), its certificate authorities, roles, identities, join paths, access governance and protected resources — enough to design a professional FedRAMP-oriented Teleport deployment before it exists, and to read one once a collector observes it — with a reusable `/teleport` operator page drawn from that vocabulary.**

## Plugin Identity

| Field | Value |
| --- | --- |
| Slug | `teleport` |
| Display name | TAP Teleport |
| Description | Teleport infrastructure access as grid vocabulary: a cluster's HA deployment, certificate authorities, roles, identities, join paths, access governance and protected resources, with a reusable /teleport operator page. |
| Kind | Leaf plugin: Teleport vocabulary plus its page. Consumes nothing (every edge that reaches another platform leaves that end open, so no `depends_on`); consumed by instance plugins that place a Teleport deployment in a design (highbar first). |

**Default dimensions**

| Dimension | Value | Why |
| --- | --- | --- |
| `teleport.plane` | `deployment` · `trust` · `identity` · `policy` · `resource` | Every node and edge type declares the one plane it belongs to (`req-teleport-dimension`), so a view selects a plane in one predicate (`n.dimensions["teleport.plane"] = "deployment"`) instead of listing types. |
| `dcom`, `deployment.environment.*` | (none) | Not defaulted on any type or edge: whether a node is designed or observed, and which environment it serves, belong to the observation. The bundle or collector that writes a node stamps them. |

## Philosophy

A Teleport cluster is the front door to everything a FedRAMP operator administers, and an assessor's questions about it are specific: is the build FIPS, are the CA keys in a KMS or HSM and when were they rotated, can anyone sign in without the IdP, which IdP groups become which roles, what can each role reach, who can request more, which machines can join and how, is every session recorded, and are access reviews on time. This plugin models exactly the objects those questions are about — and draws them — before any of it is built. A design places the deployment; a later collector (`req-teleport-collector`, Backlog) fills in the same types from a live cluster.

**What the corpus is and is not.** It is Teleport's own resource model (the `tctl` resource kinds and the Terraform provider's resource list), accepted narrowly: eighteen node types and twenty-six edge types, each justified in `req-teleport-vocabulary`. It is not Teleport's whole API — login rules, locks, session and audit-event records, access monitoring rules, bot instances, discovery and integration configs are Backlog rows, each with its reason. It is not the cloud: the EC2 instances, ECS service, load balancer, DynamoDB tables, S3 bucket and KMS keys a Teleport deployment runs on belong to the cloud plugin, and teleport reaches them by edges whose far end is left open (the add-edge cross-plugin rule, step 2), because Teleport genuinely runs on any compute and writes to any of several backends.

**Singletons are fields, grants are edges.** Cluster-wide configuration (`cluster_auth_preference`, `session_recording_config`) has no identity of its own and nothing points at it, so it is columns on the cluster (build-domain-vocabulary Step 4). A fact about a relationship — how a user came to hold a role, which IdP attribute maps to which role, which principals a role grants on a resource, how many approvals a role request needs — is an edge property, so a view can tell *this shape exists* from *this shape is dangerous*.

**Identity is per cluster.** Teleport names are unique only within a cluster (every cluster ships preset roles called `access` and `editor`), so every in-cluster type carries `cluster_name` as part of its natural key, and the traversable form of the same membership is the `BELONGS_TO_CLUSTER` edge — the same column-plus-edge pairing as github_core's `full_name` beside its `OWNS_REPO`. Design-phase keys rest on what a design can know (a name, a hostname); types whose Teleport identity is an assigned UUID say in their requirement that the key is revisited when the collector observes it.

**Three states, never two.** A blank field is *not observed*; every posture enum admits `""` beside its vocabulary, and the page renders a blank as a grey "not observed", never as a pass or a fail. A missing edge on the page reads "—" (the grid holds none), and the board says what that can and cannot mean.

**Prior art, and what it changed** (surveyed 2026-09-22):

- *Teleport's resource model* — the `tctl` resource reference and the Terraform provider's 45 resources (provider `~> 18.0`). Adopted as the naming source: model names follow Teleport's kinds (`auth_server`, `proxy`, `node`, `kube_cluster`, `db`, `app`, `windows_desktop`, `cert_authority`, `role`, `user`, `saml`/`oidc`/`github` connectors, `bot`, `token`, `access_list`, `access_request`, `device`, `trusted_cluster`). The Terraform list is the "worth managing" filter; what it holds that is not modelled is in the Backlog rows.
- *Teleport's HA-on-AWS guide and Storage Backends reference* — changed the deployment shape: two DynamoDB tables (state, audit), one S3 bucket for recordings, at most two auth servers reading one DynamoDB stream, a layer-4 load balancer; FIPS endpoints via `use_fips_endpoint`; CA keys in AWS KMS through `ca_key_params`. This is why storage and keys are edges from the auth server, not nodes of our own.
- *Teleport's FedRAMP guide* — changed the cluster's columns: FIPS build, local auth disabled, WebAuthn/per-session MFA, `fips-v1` signature suite, HSM support. These are the posture tiles.
- *BloodHound OpenGraph community library* — **no Teleport extension exists** (the nearest access-broker graph is TailscaleHound). An empty space in the field: the role → resource and connector → role grant edges here are ahead of any published graph model of Teleport.
- *Cartography* — no Teleport intel module (Tailscale is its only access broker). Confirms the gap.

**Provenance markers.** *Documented*: every type, field and edge here is drawn from Teleport's documentation (versions above); none has been read from a live cluster. *Designed*: the planes, the natural keys for design nodes, the page. *Observed*: nothing yet — `req-teleport-collector` is Backlog, and every domain article's Observability section says so rather than inferring what a credential can see.

## Goals

| # | Name | Description |
| --- | --- | --- |
| 1 | Designable Deployment | A design can place a professional HA Teleport deployment — auth pair, proxy tier, agents, and the compute, storage and keys they use — before any of it is built. |
| 2 | Answer The Assessor | The FedRAMP 20x questions about a Teleport cluster (FIPS, key custody, CA rotation, SSO-only sign-in, MFA, device trust, recording, grants, JIT requests, join paths, access reviews) each have a type or an edge to answer from. |
| 3 | Grants As Paths | Who can reach what is traversable: IdP group → connector → role → resource, role → requestable role, token → joining workload. |
| 4 | One Page Per Cluster | A reusable `/teleport` page draws any cluster's deployment and its operator front page, parameterized by the cluster, naming no instance. |
| 5 | No Dependency Drag | The vocabulary names no other plugin's type, so it installs alone. |

## Requirements

| RID | Name | Status | Notes |
| --- | --- | --- | --- |
| req-teleport-vocabulary | [Vocabulary Corpus](#vocabulary-corpus) | Implemented | Which types and edges, why, what was rejected, and the source register |
| req-teleport-dimension | [Plane Dimension](#plane-dimension) | Implemented | `teleport.plane` on every type and edge |
| req-teleport-model | [Teleport Cluster Model](#teleport-cluster-model) | Implemented | The cluster and its FedRAMP posture columns |
| req-teleport-deployment | [Deployment Models](#deployment-models) | Implemented | Auth servers, proxy servers, agents |
| req-teleport-trust | [Certificate Authority Model](#certificate-authority-model) | Implemented | CAs with rotation phase and key custody |
| req-teleport-policy | [Policy Models](#policy-models) | Implemented | Roles, join tokens, access lists, access requests |
| req-teleport-identity | [Identity Models](#identity-models) | Implemented | Users, SSO connectors, bots, trusted devices |
| req-teleport-resources | [Protected Resource Models](#protected-resource-models) | Implemented | SSH nodes, Kubernetes clusters, databases, applications, Windows desktops |
| req-teleport-edges | [Edge Types](#edge-types-requirement) | Implemented | The twenty-six edge types |
| req-teleport-page | [Teleport Page](#teleport-page) | Implemented | `/teleport`: the deployment graph and seven board sections |
| req-teleport-layout-deployment | [Deployment Layout](#deployment-layout) | Implemented | The reusable layout module that draws one cluster |
| req-teleport-panel-board | [Board Panel](#board-panel) | Implemented | The `teleport-board` panel type and its seven sections |
| req-teleport-record | [CI Record and Tests](#ci-record-and-tests) | Implemented | The in-package `ci` boot record and the test suite |
| req-teleport-collector | [Collector](#collector) | Backlog | Observe a live cluster onto the same types |
| req-teleport-activity | [Sessions and Audit Events](#sessions-and-audit-events) | Backlog | Session recordings and audit events as nodes |
| req-teleport-governance-extras | [Further Governance Resources](#further-governance-resources) | Backlog | Locks, login rules, access monitoring rules, bot instances, access list reviews |
| req-teleport-nongoals | [Non-Goals](#non-goals) | Implemented | What this plugin will not model, and who owns it |

---

### Vocabulary Corpus
----
RID: `req-teleport-vocabulary`

Status: `Implemented`

The corpus (build-domain-vocabulary): the node and edge inventories are the tail catalogs of this spec; the per-concept justification lives in each type's domain article (`tap_plugin/teleport/domain/`). This section holds the scope, the rejected candidates and the source register.

**Scope.** In: a single Teleport cluster's control plane, its trust, the identities and policy that govern access, and the resources it protects — as a FedRAMP operator reviews them. Out (the neighbour everyone confuses it with): the cloud the cluster runs on, and the identity provider behind the SSO connector; both are reached by open-ended edges. First use case: the highbar staging design (auth on EC2, proxies on ECS Fargate behind an NLB, DynamoDB state and audit, S3 recordings, KMS CA keys).

**Rejected or deferred candidates.**

| Candidate | Verdict | Why |
| --- | --- | --- |
| `cluster_auth_preference`, `session_recording_config`, `cluster_networking_config` | Fields on the cluster | Singletons; nothing points at them; never exist without the cluster. |
| `remote_cluster` / `trusted_cluster` as a node | Edge `TRUSTS_ROOT_CLUSTER` | It is the relationship between two clusters; its facts (role map, enabled, tunnel status) are edge properties. |
| A backend / storage node of our own | Edges to open ends | The DynamoDB table, S3 bucket or etcd cluster already is a node in its own plugin; a Teleport-side "backend" node would restate it. |
| One `teleport_resource` type with a `kind` field | Five types | Teleport keeps them separate kinds with different fields (protocol/URI, public address, AD domain, sub-kind) and different agents. |
| One `teleport_instance` type with a `services` field | Auth server, proxy server, agent | The deployment picture and the HA questions need the control-plane tiers individually; agents keep `services` for their resource services. |
| `lock` | Backlog (`req-teleport-governance-extras`) | Incident-response state, valuable but not needed to design or review the standing deployment. |
| `login_rule`, `access_monitoring_rule`, `bot_instance`, `access_list_review`, `okta_import_rule`, `integration`, `discovery_config`, `workload_identity`, `autoupdate_*`, `ui_config`, `vnet_config`, scoped roles | Backlog / out | Named by the Terraform list; none answers a question the first use case asks. |
| Session and audit-event records | Backlog (`req-teleport-activity`) | Execution records at high volume; the grid's own history covers configuration change. |
| `user_token` (signup/reset invites) | Rejected | Short-lived plumbing, and a secret. |

**Source register.**

| Source | Version | Retrieved | Artifact | Verdict |
| --- | --- | --- | --- | --- |
| Teleport Resources reference (goteleport.com/docs/reference/resources/) | Teleport 18.x | 2026-09-22 | `tctl get` YAML shapes | Adopt (names, fields) |
| Teleport Terraform provider resource list | provider `~> 18.0` | 2026-09-22 | registry resource list (45 resources) | Align (the worth-managing filter) |
| Teleport HA on AWS guide; Storage Backends reference | Teleport 18.x | 2026-09-22 | DynamoDB/S3 URI parameters | Adopt (deployment edges) |
| Teleport FedRAMP compliance guide | Teleport 17.7.3+/18 FIPS builds | 2026-09-22 | configuration requirements | Adopt (posture columns) |
| Teleport AWS KMS / HSM guides | Teleport 18.x | 2026-09-22 | `ca_key_params` | Adopt (`key_storage`, `SIGNS_WITH_KEY`) |
| BloodHound OpenGraph community library | as listed | 2026-09-22 | extension list | Reference (no Teleport extension) |
| Cartography intel module list | as listed | 2026-09-22 | module list | Reference (no Teleport module) |

**Update seam.** Teleport ships a major version roughly every four months and adds resource kinds and join methods most releases (hence `join_method` is a string, not an enum). The Terraform provider's resource list, versioned with Teleport, is the machine-readable change signal: a new `teleport_*` resource is a candidate for this corpus.

#### Implementation

The corpus documents: this section, the tail catalogs, and one domain article per node type, edge type and dimension under `tap_plugin/teleport/domain/` (`spec-domain-articles.md`), each with the Authoritative Source pin above.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-teleport-vocabulary-1 | Every Type Articled | Implemented | Every registered node type, edge type and the `teleport.plane` dimension has a conforming, field-complete domain article (core's `domain-article-coverage` guard finds nothing). | Checked with `tap.domain_articles.findings_for_root`: 45 subjects (18 nodes, 26 edges, 1 dimension), 0 findings. |
| req-teleport-vocabulary-2 | Rejections Recorded | Implemented | Every candidate the survey considered and did not model is in the table above with its reason. | |
| req-teleport-vocabulary-3 | No Free-Form Record | Implemented | No type declares `configuration` (migration `0003_drop_unused_configuration` removed it), and a `create_node` write carrying it is refused. | `tests/test_teleport_models.py` |

---

### Plane Dimension
----
RID: `req-teleport-dimension`

Status: `Implemented`

`teleport.plane` partitions the corpus into five concerns so a view can select one without listing types. Address it in brackets in Gryphon: `n.dimensions["teleport.plane"]` (a dotted path is read as nested keys and matches nothing).

#### Implementation

Each model's `DEFAULT_DIMENSIONS` is `{"teleport.plane": "<plane>"}`; each edge file's `default_dimensions` likewise. Values and meanings: `tap_plugin/teleport/domain/dimensions/teleport.plane.md`.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-teleport-dimension-1 | Stamped On Nodes | Implemented | A node created through the service layer carries its type's plane. | `tests/test_teleport_models.py::test_created_from_design_payload` |
| req-teleport-dimension-2 | Stamped On Edges | Implemented | Every edge file declares a plane from the five values, and a created edge carries it. | `tests/test_teleport_edges.py` |

---

### Teleport Cluster Model
----
RID: `req-teleport-model`

Status: `Implemented`

The cluster: the outer node, and the home of the cluster-wide settings an assessor reads first.

#### Implementation

`models/teleport_cluster.py` — `TeleportCluster`, `teleport__teleport_cluster`, icon `teleport-cluster`, plane `deployment`, `NATURAL_KEY = ("name",)` (the cluster name is set once and baked into every certificate, so it is Teleport's own stable identity). Fields: `name` (required; the value `teleport__teleport_cluster` is refused because it is the /teleport page's every-cluster sentinel), `proxy_address`, `teleport_version`, `edition`, `fips`, `signature_algorithm_suite`, `local_auth`, `second_factor`, `device_trust_mode`, `session_recording_mode`, `tags`. Every enum admits `""` (not observed). Field meanings: `domain/teleport_cluster.md`.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-teleport-model-1 | Created Through The Service Layer | Implemented | A `create_node` write with only `name` succeeds and the row carries it. | |
| req-teleport-model-2 | Name Required | Implemented | A `create_node` write without `name` is refused. | |
| req-teleport-model-3 | Keyed By Name | Implemented | `NATURAL_KEY` is `("name",)` and every key field is a model field. | |
| req-teleport-model-4 | Posture Is Three-State | Implemented | Each posture enum accepts `""` and its vocabulary and refuses any other value. | `test_enum_refuses_an_unknown_value` |
| req-teleport-model-5 | Sentinel Refused | Implemented | A `create_node` write whose `name` is `teleport__teleport_cluster` is refused. | `tests/test_teleport_cluster.py` |

---

### Deployment Models
----
RID: `req-teleport-deployment`

Status: `Implemented`

The processes that make up a running cluster. In Teleport's HA reference the Auth Service runs as a small pool behind a layer-4 load balancer (at most two readers of one DynamoDB stream), the Proxy Service as a stateless tier behind a public load balancer, and agents join to serve resources.

#### Implementation

| Model | Entity type | Key | Fields beyond `name`, `cluster_name` |
| --- | --- | --- | --- |
| `TeleportAuthServer` | `teleport__teleport_auth_server` | `(cluster_name, name)` | `host_id`, `teleport_version` |
| `TeleportProxyServer` | `teleport__teleport_proxy_server` | `(cluster_name, name)` | `host_id`, `teleport_version`, `public_addr` |
| `TeleportAgent` | `teleport__teleport_agent` | `(cluster_name, name)` | `host_id`, `teleport_version`, `services` (ssh, kube, db, app, windows_desktop, discovery) |

Plane `deployment`. The design key is the name; Teleport's own identity is the host UUID (`host_id`) assigned on first start, and **the key is revisited to `(cluster_name, host_id)` when `req-teleport-collector` observes it**.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-teleport-deployment-1 | Designable | Implemented | Each type is created from `name` + `cluster_name` alone; each is refused without either. | `tests/test_teleport_models.py` (parametrized over every type) |
| req-teleport-deployment-2 | Key On Carried Fields | Implemented | Each key field is a model field and part of `CREATE_REQUIRED`. | same |

---

### Certificate Authority Model
----
RID: `req-teleport-trust`

Status: `Implemented`

One of the cluster's CAs, with where its private key lives and where it is in rotation — the key-custody questions.

#### Implementation

`models/teleport_certificate_authority.py` — `teleport__teleport_certificate_authority`, plane `trust`, `NATURAL_KEY = ("cluster_name", "ca_type")` (one CA per type per cluster, named after the cluster by Teleport itself). Fields: `cluster_name`, `ca_type` (host, user, db, db_client, openssh, jwt, saml_idp, oidc_idp, spiffe, okta, awsra), `rotation_phase` (standby, init, update_clients, update_servers, rollback), `last_rotated_at`, `key_storage` (software, aws_kms, gcp_kms, pkcs11). The key a CA signs with, when it is outside the backend, is the `SIGNS_WITH_KEY` edge.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-teleport-trust-1 | Designable And Keyed | Implemented | Created from `cluster_name` + `ca_type`; refused without either; key rests on both. | `tests/test_teleport_models.py` |

---

### Policy Models
----
RID: `req-teleport-policy`

Status: `Implemented`

What is permitted and how it is granted.

#### Implementation

| Model | Entity type | Key | Notable fields |
| --- | --- | --- | --- |
| `TeleportRole` | `teleport__teleport_role` | `(cluster_name, name)` | `role_version`, `origin`, `description`, `allow`, `deny`, `options` (the full rule blocks; the rules that point at modelled things are also edges) |
| `TeleportJoinToken` | `teleport__teleport_join_token` | `(cluster_name, name)` | `join_method` (required; a string, Teleport adds methods often), `system_roles`, `bot_name`, `allow_rules`, `expires_at`. For the `token` method the name IS the secret: the model refuses anything but `sha256:<64 hex>`. |
| `TeleportAccessList` | `teleport__teleport_access_list` | `(cluster_name, name)` | `title`, `description`, `audit_frequency`, `next_audit_date`, `grants`, `membership_requires` |
| `TeleportAccessRequest` | `teleport__teleport_access_request` | `(cluster_name, name)` | `state` (PENDING, APPROVED, DENIED, PROMOTED), `reason`, `resolve_reason`, `created_at`, `expires_at` |

Plane `policy`. The access list and access request are named by Teleport-assigned UUIDs when created in the UI; a design keys on the name it chooses, **revisited if the collector must key on the assigned id**.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-teleport-policy-1 | Designable And Keyed | Implemented | Each type is created from its `CREATE_REQUIRED` fields alone and refused without any one of them; keys rest on carried fields. | `tests/test_teleport_models.py` |
| req-teleport-policy-2 | No Secret Stored | Implemented | For a secret-bearing join method (`token`) the model's `validate()` refuses any `name` that is not `sha256:<64 hex>`, so the secret cannot reach the grid or the page; delegated methods keep plain names. | `test_static_token_name_must_be_a_digest` |

---

### Identity Models
----
RID: `req-teleport-identity`

Status: `Implemented`

Who and what authenticates.

#### Implementation

| Model | Entity type | Key | Notable fields |
| --- | --- | --- | --- |
| `TeleportUser` | `teleport__teleport_user` | `(cluster_name, name)` | `user_type` (local, sso), `traits`, `created_at` |
| `TeleportSsoConnector` | `teleport__teleport_sso_connector` | `(cluster_name, kind, name)` | `kind` (saml, oidc, github; required — Teleport namespaces connectors by kind), `display`, `idp_url` |
| `TeleportBot` | `teleport__teleport_bot` | `(cluster_name, name)` | `max_session_ttl`, `traits` |
| `TeleportTrustedDevice` | `teleport__teleport_trusted_device` | `(cluster_name, asset_tag)` | `asset_tag` (serial number; required), `os_type`, `enroll_status` |

Plane `identity`. The IdP behind a connector is reached by `DELEGATES_LOGIN` (open end: `identity_core__oidc_issuer` for OIDC, the IdP's own node for SAML, the GitHub platform for GitHub) — teleport does not depend on any IdP plugin.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-teleport-identity-1 | Designable And Keyed | Implemented | As `req-teleport-policy-1`, for these four types. | `tests/test_teleport_models.py` |

---

### Protected Resource Models
----
RID: `req-teleport-resources`

Status: `Implemented`

What the cluster protects. Grouped on the page by kind and label, because labels are how roles grant access.

#### Implementation

| Model | Entity type | Key | Fields beyond `cluster_name`, `labels` |
| --- | --- | --- | --- |
| `TeleportSshNode` | `teleport__teleport_ssh_node` | `(cluster_name, hostname)` | `hostname`, `host_id`, `addr`, `sub_kind` (teleport, openssh, openssh-ec2-ice) |
| `TeleportKubeCluster` | `teleport__teleport_kube_cluster` | `(cluster_name, name)` | `name` |
| `TeleportDatabase` | `teleport__teleport_database` | `(cluster_name, name)` | `name`, `protocol`, `uri` |
| `TeleportApp` | `teleport__teleport_app` | `(cluster_name, name)` | `name`, `uri`, `public_addr` |
| `TeleportWindowsDesktop` | `teleport__teleport_windows_desktop` | `(cluster_name, name)` | `name`, `addr`, `domain` |

Plane `resource`. An SSH node's Teleport name is its host UUID; the design key is the hostname, **revisited to `(cluster_name, host_id)` when observed**. The real target behind a resource (an EC2 instance, an EKS cluster, an RDS instance) is `FRONTS_TARGET`.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-teleport-resources-1 | Designable And Keyed | Implemented | As `req-teleport-policy-1`, for these five types. | `tests/test_teleport_models.py` |

---

### Edge Types Requirement
----
RID: `req-teleport-edges`

Status: `Implemented`

The twenty-six relationships in the tail catalog, each a `.edge.json` under `edges/` registered in `[edges]`, with a domain article.

#### Implementation

Every closed end names teleport types only. The eight edges that reach another platform — `RUNS_ON_COMPUTE`, `STORES_CLUSTER_STATE`, `WRITES_AUDIT_EVENTS`, `UPLOADS_SESSION_RECORDINGS`, `SIGNS_WITH_KEY`, `FRONTS_TARGET`, `ADMITS_IDENTITY`, `DELEGATES_LOGIN` — omit `targets`, and each description says what may appear there. Every `property_schema` is `additionalProperties: false`. Every edge stamps `teleport.plane`.

Endpoint lists are **enforced**. The grid's permission union (`req-grid-edge-constraints-3`) lets an unconstrained node create any edge, so every teleport model declares `OUTBOUND_EDGES` — and `INBOUND_EDGES` where a teleport edge ends on it — derived from the edge files. A teleport edge from or to a type its definition does not name is refused (a role cannot "hold" a role; a forged grant path cannot be written). Foreign edge types stay permitted wherever their own endpoint lists are open or name the teleport type (e.g. compliance_core's `SCOPED_TO_COMPLIANCE_BOUNDARY`, whose sources are open). The three types no teleport edge ends on (agent, user, bot) leave `INBOUND_EDGES` undeclared, because an empty list would block every inbound edge, foreign ones included. A test asserts the declared constraints equal the edge files' endpoints, so they cannot drift.

No containment is declared: records do not retire with their cluster by cascade (a cluster rebuild re-observes them), so `CONTAINMENT_EDGES` is empty on every type.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-teleport-edges-1 | Declared And Articled | Implemented | Every edge file is in the manifest under its slug and has a domain article. | `tests/test_teleport_edges.py` |
| req-teleport-edges-2 | Open Only Across Platforms | Implemented | An end is open exactly for the eight cross-platform edges; every closed end names teleport types only. | same |
| req-teleport-edges-3 | Closed Property Schemas | Implemented | Every property schema forbids extras and declares no `hotlink`; an unknown property or enum value is refused through the service layer. | same |
| req-teleport-edges-4 | Plane Stamped | Implemented | Every edge carries its plane. | same |
| req-teleport-edges-5 | Endpoints Enforced | Implemented | An edge from or to a type its definition does not name is refused through the service layer; declared node constraints equal the edge files' endpoints. | same |

---

### Teleport Page
----
RID: `req-teleport-page`

Status: `Implemented`

`/teleport` — the operator's front page for one cluster in a FedRAMP 20x environment.

#### Implementation

`grift/page.grift.json` (bundle `page`, batch "teleport page v0.1.0"): one page, full-bleed, one column —

| Row | Slot | Panel | Height |
| --- | --- | --- | --- |
| 1 | `deployment` | Teleport deployment (tap_viz graph panel, `req-teleport-layout-deployment`) | `75vh` |
| 2 | `posture` | Cluster posture (`teleport-board`, section `posture`) | auto |
| 3 | `roles` | Roles and what they grant | auto |
| 4 | `identity` | Who signs in (connectors, users, devices, access lists) | auto |
| 5 | `resources` | Protected resources | auto |
| 6 | `requests` | Access requests | auto |
| 7 | `machines` | Machines: bots, agents and join tokens | auto |
| 8 | `trust` | Trust: certificate authorities and trusted clusters | auto |

**Parameter.** `?cluster=<cluster name>` selects the cluster for every panel: the cluster's name (`teleport__teleport_cluster.name`, its natural key), matched exactly, never its entity id (ruled 2026-09-23: there will be many clusters, and a name is what an operator types and a link carries). With exactly one cluster on the grid it is chosen without the parameter; with several and none named, the graph draws the clusters alone as a picker (each tile opens `/teleport?cluster=<name>` through the panel's nav rule, `{data.name}`) and each board section lists them as links. Nothing in the bundle names an instance.

**Scene searches take the name.** Every search declares one input, `cluster` (string), and filters each cluster it reaches with `(c.data.name = $cluster OR c.entity_type = $cluster)`. The default is the sentinel `teleport__teleport_cluster`, the cluster type's own slug, which every cluster's `entity_type` equals, so `?cluster` absent returns every cluster (the one cluster on a single-cluster grid, the picker on a multi-cluster one). The sentinel stands in for the parameter-absent predicate Gryphon does not have (tap#360); `teleport__teleport_cluster.name` refuses it, so it is never a real cluster's name. This is the Okta page's pattern (okta-tap `specs/spec-okta-v0.md` § Page: Org).

- **Both ends in the cluster.** A search that joins two Teleport records runs the path cluster to cluster, `(c)<-[:BELONGS_TO_CLUSTER]-(a)-[:EDGE]->(b)-[:BELONGS_TO_CLUSTER]->(c2)`, both filtered (`CALLS_AUTH_API`, `DIALS_REVERSE_TUNNEL`, `SERVES_RESOURCE`), so a cross-cluster edge never pulls a foreign proxy, auth server or resource onto this cluster's picture. A pattern that reuses one variable to close the loop is not used: Gryphon does not unify a variable bound twice in one pattern. A search whose far end is another platform's record (`RUNS_ON_COMPUTE`, `STORES_CLUSTER_STATE`, `WRITES_AUDIT_EVENTS`, `UPLOADS_SESSION_RECORDINGS`, `SIGNS_WITH_KEY`, `FRONTS_TARGET`) scopes its Teleport end through membership; the open end carries no cluster. `TRUSTS_ROOT_CLUSTER` joins two clusters, so it keeps an edge with the chosen cluster at *either* end and draws the peer.
- **Every path is linear.** No scene search has a node in the middle of its path that is not a cluster, so none needs the `cluster_name` column filter the Okta page uses for its mid-path nodes.

The graph panel pre-bakes twelve scene searches: the chosen cluster (every cluster when absent); every deployment/trust/resource-plane member of it with its `BELONGS_TO_CLUSTER` edge; and one search per edge type drawn (`RUNS_ON_COMPUTE`, `STORES_CLUSTER_STATE`, `WRITES_AUDIT_EVENTS`, `UPLOADS_SESSION_RECORDINGS`, `CALLS_AUTH_API`, `DIALS_REVERSE_TUNNEL`, `SIGNS_WITH_KEY`, `SERVES_RESOURCE`, `FRONTS_TARGET`, `TRUSTS_ROOT_CLUSTER`). No search is an unfiltered edge search. Gryphon has no edge-type alternation, so one search per type is the narrowest form. A search routed through the cluster also returns the `BELONGS_TO_CLUSTER` edges it walked; the members search draws those edges anyway. The layout still scopes the scene by membership in the browser (`req-teleport-layout-deployment`), so the two agree.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-teleport-page-1 | Bundle Valid | Implemented | The bundle validates against the GRIFT schema and imports into an empty grid under the bootloader actor. | `tests/test_teleport_page.py` |
| req-teleport-page-2 | Slots Exact | Implemented | The layout's slots equal the `USES_PANEL` hotlink values. | same |
| req-teleport-page-3 | Scene Searches Named | Implemented | Every edge type the layout draws is shipped by this plugin and fetched by a search that names it. | same |
| req-teleport-page-4 | Searches Run | Implemented | Every scene search executes against a seeded design and returns the expected shape. | same |
| req-teleport-page-6 | Scoped By Cluster Name | Implemented | Every scene search takes `cluster` (default `teleport__teleport_cluster`); with two clusters and an edge of every drawn type crossing between them, each search returns only the named cluster's records, in both directions; `?cluster=a` does not match a cluster named `aba`; absent, every cluster is returned. | `tests/test_teleport_page.py` |
| req-teleport-page-5 | Renders Live | Proposed | The page renders in a booted stack with the graph drawn and every section filled. | NOT OBSERVED: needs a boot with this plugin's migrations; the layout module itself was executed in headless Chromium against a synthetic scene (see the PR). |

---

### Deployment Layout
----
RID: `req-teleport-layout-deployment`

Status: `Implemented`

The reusable layout module that draws one Teleport cluster as a placed picture; any page can mount it through the projection in `grift/page.grift.json`.

#### Implementation

`static/teleport/js/projections/teleport-deployment.js` — standard layout module (`execute(context)`). It (1) picks the cluster whose name (its label) equals `context.inputs.cluster`, or the single cluster, else draws a picker (the every-cluster sentinel counts as no input); (2) keeps a Teleport record only when its `BELONGS_TO_CLUSTER` edge points at the chosen cluster (fail closed, the board's membership), keeps trusted peer clusters, and removes any non-teleport node left unattached; (3) nests proxies, auth servers and CAs in the cluster box with `projectNested` over `BELONGS_TO_CLUSTER`; (4) places proxies above auth servers, CAs in a column on the right; compute (`RUNS_ON_COMPUTE` targets) left of each tier; KMS/HSM keys (`SIGNS_WITH_KEY`) right of the CAs; peer clusters top-right; state/audit/recording stores in a band beneath; then each agent with the resources it serves and the targets those front; agent compute to the left; (5) draws any node no band accounts for in a row beneath and returns a warning — nothing is dropped. Icon-badge chrome comes from the projection (`node_style.mode = icon-badge`, `lock_nodes`, `min_zoom: fit`).

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-teleport-layout-deployment-1 | Names No Instance | Implemented | The module contains no entity id and no instance name. | review |
| req-teleport-layout-deployment-2 | Scoped To One Cluster | Implemented | With `?cluster=<name>` the other cluster's members and unattached outside nodes leave the scene; with several clusters and none named, only clusters are drawn and a warning says why. | headless Chromium run, 2026-09-22 (PR) |
| req-teleport-layout-deployment-3 | Nothing Dropped | Implemented | A node no band accounts for is drawn and reported. | code path; not exercised by a scene yet |

---

### Board Panel
----
RID: `req-teleport-panel-board`

Status: `Implemented`

`teleport-board`: one section of the operator board for the resolved cluster. A plugin panel type because the standard table panel cannot resolve a default cluster (Gryphon has no parameter-absent predicate) or join several reads into one row.

#### Implementation

`panels/board/__init__.py` (`TeleportBoardPanelType`, slug `teleport-board`, view `teleport/panels/board.html`, css `teleport/css/board.css`), registered in `TeleportConfig.ready()`. `config.section` ∈ `posture`, `roles`, `identity`, `resources`, `requests`, `machines`, `trust`; `config.title`, `config.intro` optional. The cluster is resolved from `?cluster=<cluster name>`, matched exactly (the every-cluster sentinel counts as no parameter). Reads are Gryphon (`execute_gryphon_raw`), each narrowed by `$cluster` (the resolved name) on `cluster_name`; a read that joins two Teleport records narrows BOTH ends, by `cluster_name` where the end is typed and through its `BELONGS_TO_CLUSTER` edge to the named cluster where it is not (Gryphon reads a model column only on a labelled variable), so a cross-cluster edge never brings a foreign record in or has it misreported as unlinked; then **scoped by membership**: only records with a `BELONGS_TO_CLUSTER` edge to the chosen cluster are shown (the same membership the graph uses), a record the name column claims but the edge does not is listed in a red note instead of shown, and the section badge reports provenance over the cluster and its members (`design`, or `mixed: n design · m not design`). Folds are pure functions. Sections:

- **posture** — tiles for FIPS, signature suite, local auth, second factor (only `webauthn` is green; `on` admits OTP and warns), device trust, session recording, edition (each good / bad / other / not observed against the FedRAMP expectation it names), version and proxy address; counts of auth servers, proxies, agents, roles, users (SSO vs local; any local is red), bots, pending requests, protected resources.
- **roles** — per role: logins, label selectors, resources reached (`GRANTS_RESOURCE_ACCESS`), requestable roles with approvals (`PERMITS_ROLE_REQUEST`), session MFA, max TTL, deny present, holders with how granted (`HOLDS_ROLE.granted_by`), SSO mappings and access lists that grant it.
- **identity** — SSO connectors with IdP; users by type with local accounts named; trusted devices enrolled; access lists with grants, owner/member counts and next review (overdue red).
- **resources** — counts by kind; per kind, label frequencies and a table with detail, labels, serving agent and reaching roles/principals.
- **requests** — pending, and approved-and-unexpired, requests with requester, what is wanted, reason, age, expiry and reviews.
- **machines** — bots (roles, join method; static secret red), agents (services, version, join), tokens (method, system roles, admitted identities, joiners, expiry).
- **trust** — CAs (rotation phase, last rotation, key storage, key) and trusted clusters (direction, enabled, tunnel, role map; peer links to its own page).

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-teleport-panel-board-1 | Cluster Resolution | Implemented | `?cluster=<name>` wins, matched by name, never by entity id; one cluster is chosen without it; several without it choose none and list them by name. | `tests/test_teleport_board.py` |
| req-teleport-panel-board-2 | Three States | Implemented | A blank posture field renders "not observed", never a verdict. | same |
| req-teleport-panel-board-3 | Every Section Renders | Implemented | Each section's context builds from real Gryphon reads over a seeded design and its template renders. | same |
| req-teleport-panel-board-5 | Membership Is The Edge | Implemented | A record naming the cluster without a membership edge is not shown, and the board names it. | `test_membership_is_the_edge_not_the_name` |
| req-teleport-panel-board-4 | Grants Folded | Implemented | Role reach, requestable roles, SSO mappings, list grants, local-user and static-token flags, overdue reviews, live requests and CA custody are computed as specified. | same |
| req-teleport-panel-board-6 | No Other Cluster's Records | Implemented | With a second cluster and every board join crossing between the two, no section shows the other cluster's records and none is reported as unlinked. | `test_no_section_shows_another_clusters_records` |

---

### CI Record and Tests
----
RID: `req-teleport-record`

Status: `Implemented`

#### Implementation

`boot/ci.boot.json` installs teleport alone (no dependencies), offline and credential-free, and seeds teleport's own bundle; the consumer flips self to editable. Tests: `test_teleport_manifest.py` (validate_plugin structure + strict), `test_teleport_cluster.py`, `test_teleport_models.py`, `test_teleport_edges.py`, `test_teleport_board.py`, `test_teleport_page.py`; `tests/_design.py` is the shared HA design fixture.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-teleport-record-1 | Record Declared | Implemented | The manifest declares the `ci` record with its sha256. | |
| req-teleport-record-2 | Validates Strict | Implemented | `validate_plugin --strict` passes on the package. | |

---

### Collector
----
RID: `req-teleport-collector`

Status: `Backlog`

Observe a live cluster onto these types with a read-only Machine ID bot identity (`tctl get` / gRPC list over each kind), derive `GRANTS_RESOURCE_ACCESS` by evaluating each role's allow/deny label selectors against resource labels, store join-token secrets only as digests, and revisit the design keys named above. Deferred until a cluster exists; the Observability section of every domain article is written from its first executed calls.

### Sessions and Audit Events
----
RID: `req-teleport-activity`

Status: `Backlog`

Session recordings and audit events as nodes (who reached what, when, with which certificate). High-volume execution records; the right shape (sampled, windowed, or summary nodes) is decided with the collector.

### Further Governance Resources
----
RID: `req-teleport-governance-extras`

Status: `Backlog`

`lock` (incident response), `login_rule`, `access_monitoring_rule` (automatic review), `bot_instance`, `access_list_review` history, `okta_import_rule`, `discovery_config`, `integration`, `workload_identity` / SPIFFE federation — each added when a view needs it.

### Non-Goals
----
RID: `req-teleport-nongoals`

Status: `Implemented`

- **The cloud underneath** — EC2, ECS, load balancers, DynamoDB, S3, KMS belong to the cloud plugin (aws_core); teleport reaches them by open-ended edges.
- **The identity provider** — Okta, Entra, GitHub identities belong to their plugins or to identity_core; teleport reaches them by `DELEGATES_LOGIN`.
- **A specific deployment** — the staging cluster's names, instances and tables are an instance plugin's design seed (highbar), never this plugin's GRIFT.
- **Secrets** — no join-token value, key material or credential is ever a field. No type has a free-form `configuration` field either: the resources Teleport keeps can carry secret material and personal data (a CA's key material, an SSO connector's client secret, a user's traits), and no collector exists to fill one, so only promoted columns are stored and a resource cannot be passed through whole.

## Model catalog

Superseded by the manifest (`[models]`) and the model classes as of v0.2.0. The rows that survive record decisions the code cannot state.

| Model | Entity type | Category | Rationale |
| --- | --- | --- | --- |
| `TeleportCluster` | `teleport__teleport_cluster` | Outer node | Singletons (auth preference, recording config) are its columns, not nodes. |
| `TeleportAuthServer` / `TeleportProxyServer` / `TeleportAgent` | `teleport__teleport_*` | Deployment | Three types, not one instance type with a services list: the HA picture needs the tiers individually. |
| `TeleportCertificateAuthority` | `teleport__teleport_certificate_authority` | Trust | A node because a key edge points from it and the page lists it. |
| `TeleportRole` | `teleport__teleport_role` | Policy | Full rule blocks kept as fields so nothing unmodelled is dropped; rules that point at modelled things are also edges. |
| `TeleportJoinToken` | `teleport__teleport_join_token` | Policy | A node because agents/bots point at it and it points at external identities; never holds the secret. |
| Resources (five) | `teleport__teleport_ssh_node` … | Resource | Five kinds, not one: different fields, different agents. |

## Edge types

Superseded by the manifest (`[edges]`) and the edge files as of v0.2.0. Decision rows only.

| Edge | From → To | Properties | Rationale |
| --- | --- | --- | --- |
| `BELONGS_TO_CLUSTER` | every in-cluster type → cluster | — | Traversable twin of the `cluster_name` key column (github_core's `full_name` + `OWNS_REPO` pattern); one relationship over every source. |
| `RUNS_ON_COMPUTE`, `STORES_CLUSTER_STATE`, `WRITES_AUDIT_EVENTS`, `UPLOADS_SESSION_RECORDINGS` | instances / auth server → open | — | Sourced from the process that does the work, not the cluster; open because Teleport runs on and writes to many platforms. |
| `SIGNS_WITH_KEY` | CA → open | `key_state` | Absent when `key_storage` is `software`; read the CA's column to tell that from not observed. |
| `TRUSTS_ROOT_CLUSTER` | leaf cluster → root cluster | `role_map`, `enabled`, `connection_status` | The trusted-cluster resource is a relationship, not a thing. |
| `GRANTS_RESOURCE_ACCESS` | role → resource | `principals`, `match` | Derived by label matching net of deny; `match` separates wildcard grants from specific ones. |
| `HOLDS_ROLE` | user, bot → role | `granted_by` | How a role was obtained is the access-review question. |
| `MAPS_TO_ROLE` | SSO connector → role | `attribute`, `value` | The IdP-group-becomes-admin path. |
| `PERMITS_ROLE_REQUEST` | role → role | `approvals_required` | The just-in-time elevation path. |
| `DELEGATES_LOGIN` | SSO connector → open | — | Points at the neutral `identity_core__oidc_issuer` for OIDC; no IdP plugin dependency. |
| `ADMITS_IDENTITY` | join token → open | `rule` | Which workload identity may join. |
| Others | see manifest | | `CALLS_AUTH_API`, `DIALS_REVERSE_TUNNEL`, `JOINS_WITH_TOKEN`, `SERVES_RESOURCE`, `FRONTS_TARGET`, `LOGS_IN_VIA_CONNECTOR`, `GRANTS_ROLE`, `MEMBER_OF_ACCESS_LIST`, `RAISES_ACCESS_REQUEST`, `REQUESTS_ROLE`, `REQUESTS_RESOURCE`, `REVIEWED_ACCESS_REQUEST`, `ENROLLED_DEVICE`. |

## Icons

`teleport-cluster` is Teleport's own mark, used nominatively to identify the vendor on diagrams. No reusable licence for it was found (Teleport's press kit is available on request, not under a stated licence), so it is used only as the cluster's tile, it remains its owner's trademark, and it is **not** covered by this repository's Apache-2.0 licence. The other seventeen glyphs (`teleport-auth-server`, `-proxy-server`, `-agent`, `-certificate-authority`, `-role`, `-user`, `-sso-connector`, `-bot`, `-join-token`, `-access-list`, `-access-request`, `-trusted-device`, `-ssh-node`, `-kube-cluster`, `-database`, `-app`, `-windows-desktop`) were drawn for this plugin (Apache-2.0): 64×64, square viewBox, stroked in the plane's colour (Teleport purple for deployment and trust, violet for identity, slate for policy, teal for resources), since icons render as image assets where `currentColor` cannot inherit.
