# teleport_auth_server

## Blurb

One Teleport process running the Auth Service: the cluster's certificate authority and API, which issues certificates, evaluates roles, and reads and writes the backend, audit log and session-recording storage.

## Purpose

Teleport's HA guide runs the Auth Service as a small pool (at most two readers of one DynamoDB stream) behind a layer-4 load balancer. Each process is a separate node because each one runs somewhere (an EC2 instance) and each one reaches the backend: the deployment picture needs them individually.

## Goals

- Place each auth instance on its compute (`RUNS_ON_COMPUTE`).
- Show which backend, audit store and recording store the cluster writes (`STORES_CLUSTER_STATE`, `WRITES_AUDIT_EVENTS`, `UPLOADS_SESSION_RECORDINGS`).

## Identity

`NATURAL_KEY = (`cluster_name`, `name`)`. A design knows an auth server only by the name it gives it; Teleport's own identity is the host UUID (`host_id`), which exists only once the process first starts. Revisit to `(cluster_name, host_id)` when the collector observes it.

## Boundaries

- Not the auto-scaling group or launch template that keeps the pool alive — those are cloud nodes.
- Not the CA keys themselves: `teleport_certificate_authority`.

## Neutrality

Vendor-specific (Teleport's Auth Service).

## Observability

**Not observed.** No collector exists (`req-teleport-collector`, Backlog), so nothing here has been read from a live cluster and nothing below is written from an executed call. What the documentation says: the record is readable with `tctl get` (or the gRPC API) by a Teleport identity whose role allows `read`/`list` on this resource kind; a Machine ID bot with a read-only role is the expected collector credential. Until a collector exists, every node of `teleport__teleport_auth_server` on a grid is a design node (`dcom: design`) carrying only the fields its designer knew.

## Authoritative Source

- **Source:** Teleport documentation — Resources reference (goteleport.com/docs/reference/resources/), Teleport configuration reference, and the Teleport Terraform provider resource list
- **Version:** Teleport 18.x documentation and Terraform provider `~> 18.0`
- **Retrieved:** 2026-09-22

## Prior Art

- Teleport Terraform provider resource list (provider `~> 18.0`, retrieved 2026-09-22) — the curated set of Teleport resources worth managing; this type's counterpart is named in `specs/spec-teleport-v0.md` § Model catalog.
- BloodHound OpenGraph community library (retrieved 2026-09-22) — no Teleport extension exists; TailscaleHound is the nearest access-broker graph.
- Cartography intel module list (retrieved 2026-09-22) — no Teleport module.

## Fields

- `name` — The instance's name — the hostname (design: the planned instance name). Required.
- `cluster_name` — The name of the Teleport cluster this record lives in — the same string as that cluster node's `name`. Part of the natural key because Teleport's names are unique only within one cluster (every cluster ships preset roles called `access`, `editor` and `auditor`). The traversable form of the same membership is the `BELONGS_TO_CLUSTER` edge; this column is what the key rests on (a key must be a column the generated search can filter).
- `host_id` — The host UUID Teleport assigns on first start and stamps into the instance's host certificate. Blank until observed; the future key.
- `teleport_version` — The Teleport version this process runs (instance inventory). Blank until observed.
- `configuration` — The rest of the resource as Teleport reports it (the `spec` a collector did not lift into a column). Empty means not observed.
