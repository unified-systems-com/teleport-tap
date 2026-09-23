# teleport_role

## Blurb

A Teleport role: allow and deny rules (logins, resource label selectors, Kubernetes groups, database users, resource verbs, request and review permissions) plus session options such as MFA-per-session and maximum TTL.

## Purpose

Roles are the policy: what a certificate lets its holder reach. The front page's first question — "what does each role grant?" — needs roles as nodes and their grants as edges, which is also the shape BloodHound-style path analysis needs.

## Goals

- List roles with what they grant.
- Carry the rules that point at other things as edges (resource access, requestable roles).
- Keep the full rule blocks so nothing unmodelled is silently dropped.

## Identity

`NATURAL_KEY = (`cluster_name`, `name`)`. Role names are unique within a cluster and are what users, connectors and access lists reference, so `(cluster_name, name)` is Teleport's own identity.

## Boundaries

- Not the per-user assignment — `HOLDS_ROLE`.
- Not role templates' interpolated values (`{{internal.logins}}`): those resolve per user at login and are not observable from the role.

## Neutrality

Vendor-specific. RBAC roles are universal, but the allow/deny label-selector grammar is Teleport's.

## Observability

**Not observed.** No collector exists (`req-teleport-collector`, Backlog), so nothing here has been read from a live cluster and nothing below is written from an executed call. What the documentation says: the record is readable with `tctl get` (or the gRPC API) by a Teleport identity whose role allows `read`/`list` on this resource kind; a Machine ID bot with a read-only role is the expected collector credential. Until a collector exists, every node of `teleport__teleport_role` on a grid is a design node (`dcom: design`) carrying only the fields its designer knew.

## Authoritative Source

- **Source:** Teleport documentation — Resources reference (goteleport.com/docs/reference/resources/), Teleport configuration reference, and the Teleport Terraform provider resource list
- **Version:** Teleport 18.x documentation and Terraform provider `~> 18.0`
- **Retrieved:** 2026-09-22

## Prior Art

- Teleport Terraform provider resource list (provider `~> 18.0`, retrieved 2026-09-22) — the curated set of Teleport resources worth managing; this type's counterpart is named in `specs/spec-teleport-v0.md` § Model catalog.
- BloodHound OpenGraph community library (retrieved 2026-09-22) — no Teleport extension exists; TailscaleHound is the nearest access-broker graph.
- Cartography intel module list (retrieved 2026-09-22) — no Teleport module.

## Fields

- `name` — The role name, as users, connectors and access lists reference it. Required.
- `cluster_name` — The name of the Teleport cluster this record lives in — the same string as that cluster node's `name`. Part of the natural key because Teleport's names are unique only within one cluster (every cluster ships preset roles called `access`, `editor` and `auditor`). The traversable form of the same membership is the `BELONGS_TO_CLUSTER` edge; this column is what the key rests on (a key must be a column the generated search can filter).
- `role_version` — The role resource version (`v7`, `v8`): its semantics for label matching and Kubernetes resources differ. Blank until observed.
- `origin` — Where the role came from, from the `teleport.dev/origin` label (e.g. `defaults` for presets, `okta`, `config-file`). Blank until observed.
- `description` — The role's `metadata.description`. Blank until observed.
- `allow` — The role's `spec.allow` block as written. The rules that reference other things on the grid are ALSO edges (`GRANTS_RESOURCE_ACCESS`, `PERMITS_ROLE_REQUEST`); this keeps the complete block, including rules that reference nothing modelled. Empty means not observed.
- `deny` — The role's `spec.deny` block. Deny always wins in Teleport, so a derived access edge must be computed against it. Empty means not observed.
- `options` — The role's `spec.options` (`max_session_ttl`, `require_session_mfa`, `device_trust_mode`, `record_session`, `lock`, `create_host_user_mode` …). Empty means not observed.
