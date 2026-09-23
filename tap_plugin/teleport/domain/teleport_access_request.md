# teleport_access_request

## Blurb

A just-in-time access request: a user asks for roles or specific resources for a bounded time, reviewers approve or deny it, and an approved request is assumed as elevated certificates.

## Purpose

Pending requests are the operator's inbox, and approved-but-unexpired requests are live standing access. Both belong on a FedRAMP front page (AC-2, AC-6 least privilege).

## Goals

- List pending requests with requester, what is requested and age.
- Record who reviewed and how (`REVIEWED_ACCESS_REQUEST`).

## Identity

`NATURAL_KEY = (`cluster_name`, `name`)`. Teleport assigns each request a UUID (`metadata.name`); unique within the cluster. A request is observed, not designed.

## Boundaries

- No free-form `configuration` field: the resources Teleport keeps for this object can carry secret material or personal data (key material, a connector's client secret, a user's traits), so only promoted columns are stored.
- Not access-request audit events (the grid's history covers state changes).
- Not access monitoring rules (automatic review) — Backlog.

## Neutrality

Vendor-specific; JIT elevation is common (PIM, Boundary) but the request/review/assume flow is Teleport's.

## Observability

**Not observed.** No collector exists (`req-teleport-collector`, Backlog), so nothing here has been read from a live cluster and nothing below is written from an executed call. What the documentation says: the record is readable with `tctl get` (or the gRPC API) by a Teleport identity whose role allows `read`/`list` on this resource kind; a Machine ID bot with a read-only role is the expected collector credential. Until a collector exists, every node of `teleport__teleport_access_request` on a grid is a design node (`dcom: design`) carrying only the fields its designer knew.

## Authoritative Source

- **Source:** Teleport documentation — Resources reference (goteleport.com/docs/reference/resources/), Teleport configuration reference, and the Teleport Terraform provider resource list
- **Version:** Teleport 18.x documentation and Terraform provider `~> 18.0`
- **Retrieved:** 2026-09-22

## Prior Art

- Teleport Terraform provider resource list (provider `~> 18.0`, retrieved 2026-09-22) — the curated set of Teleport resources worth managing; this type's counterpart is named in `specs/spec-teleport-v0.md` § Model catalog.
- BloodHound OpenGraph community library (retrieved 2026-09-22) — no Teleport extension exists; TailscaleHound is the nearest access-broker graph.
- Cartography intel module list (retrieved 2026-09-22) — no Teleport module.

## Fields

- `name` — The request id Teleport assigns. Required.
- `cluster_name` — The name of the Teleport cluster this record lives in — the same string as that cluster node's `name`. Part of the natural key because Teleport's names are unique only within one cluster (every cluster ships preset roles called `access`, `editor` and `auditor`). The traversable form of the same membership is the `BELONGS_TO_CLUSTER` edge; this column is what the key rests on (a key must be a column the generated search can filter).
- `state` — The request state as Teleport reports it (`PROMOTED` means turned into an access list). Blank until observed.
- `reason` — The requester's stated reason. Blank until observed.
- `resolve_reason` — The reviewer's reason for the final decision. Blank until observed.
- `created_at` — When the request was made (ISO-8601). Blank until observed.
- `expires_at` — When the request (pending) or the granted access (approved) expires (ISO-8601). Blank until observed.
