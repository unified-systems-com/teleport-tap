# teleport_trusted_device

## Blurb

A device registered in Teleport's device inventory (by serial / asset tag) and, once enrolled, holding a device credential that device-trust mode requires before access is granted.

## Purpose

With device trust `required`, access depends on the device as well as the user — a FedRAMP control (AC-19, IA-3). The inventory and its enrollment state are what an operator checks.

## Goals

- Count enrolled vs registered devices.
- Show which user enrolled which device (`ENROLLED_DEVICE`).

## Identity

`NATURAL_KEY = (`cluster_name`, `asset_tag`)`. Teleport identifies a device by its asset tag (the serial number on macOS/Windows/Linux) within the cluster's inventory; the internal UUID is assigned at registration.

## Boundaries

- No free-form `configuration` field: the resources Teleport keeps for this object can carry secret material or personal data (key material, a connector's client secret, a user's traits), so only promoted columns are stored.
- Not an MDM record — Jamf/Intune sync is a separate integration (Backlog).

## Neutrality

Vendor-specific record; a neutral device substrate (computing_core) may later link to it.

## Observability

**Not observed.** No collector exists (`req-teleport-collector`, Backlog), so nothing here has been read from a live cluster and nothing below is written from an executed call. What the documentation says: the record is readable with `tctl get` (or the gRPC API) by a Teleport identity whose role allows `read`/`list` on this resource kind; a Machine ID bot with a read-only role is the expected collector credential. Until a collector exists, every node of `teleport__teleport_trusted_device` on a grid is a design node (`dcom: design`) carrying only the fields its designer knew.

## Authoritative Source

- **Source:** Teleport documentation — Resources reference (goteleport.com/docs/reference/resources/), Teleport configuration reference, and the Teleport Terraform provider resource list
- **Version:** Teleport 18.x documentation and Terraform provider `~> 18.0`
- **Retrieved:** 2026-09-22

## Prior Art

- Teleport Terraform provider resource list (provider `~> 18.0`, retrieved 2026-09-22) — the curated set of Teleport resources worth managing; this type's counterpart is named in `specs/spec-teleport-v0.md` § Model catalog.
- BloodHound OpenGraph community library (retrieved 2026-09-22) — no Teleport extension exists; TailscaleHound is the nearest access-broker graph.
- Cartography intel module list (retrieved 2026-09-22) — no Teleport module.

## Fields

- `cluster_name` — The name of the Teleport cluster this record lives in — the same string as that cluster node's `name`. Part of the natural key because Teleport's names are unique only within one cluster (every cluster ships preset roles called `access`, `editor` and `auditor`). The traversable form of the same membership is the `BELONGS_TO_CLUSTER` edge; this column is what the key rests on (a key must be a column the generated search can filter).
- `asset_tag` — The device's asset tag — its serial number. Required; the natural key.
- `os_type` — The device's operating system. Blank until observed.
- `enroll_status` — Whether the device holds an enrolled credential. Blank until observed — and blank is not `not_enrolled`.
