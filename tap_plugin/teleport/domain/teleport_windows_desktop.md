# teleport_windows_desktop

## Blurb

A Windows host reachable over Teleport's desktop access (RDP through the proxy with certificate-based smart-card login), registered statically or discovered from Active Directory.

## Purpose

See `teleport_ssh_node`.

## Goals

- List desktops by label and the roles that reach them.

## Identity

`NATURAL_KEY = (`cluster_name`, `name`)`. Desktop names are unique within the Teleport cluster.

## Boundaries

- No free-form `configuration` field: the resources Teleport keeps for this object can carry secret material or personal data (key material, a connector's client secret, a user's traits), so only promoted columns are stored.
- Not the Windows Desktop Service process (an agent).

## Neutrality

Vendor-specific record of a neutral thing.

## Observability

**Not observed.** No collector exists (`req-teleport-collector`, Backlog), so nothing here has been read from a live cluster and nothing below is written from an executed call. What the documentation says: the record is readable with `tctl get` (or the gRPC API) by a Teleport identity whose role allows `read`/`list` on this resource kind; a Machine ID bot with a read-only role is the expected collector credential. Until a collector exists, every node of `teleport__teleport_windows_desktop` on a grid is a design node (`dcom: design`) carrying only the fields its designer knew.

## Authoritative Source

- **Source:** Teleport documentation — Resources reference (goteleport.com/docs/reference/resources/), Teleport configuration reference, and the Teleport Terraform provider resource list
- **Version:** Teleport 18.x documentation and Terraform provider `~> 18.0`
- **Retrieved:** 2026-09-22

## Prior Art

- Teleport Terraform provider resource list (provider `~> 18.0`, retrieved 2026-09-22) — the curated set of Teleport resources worth managing; this type's counterpart is named in `specs/spec-teleport-v0.md` § Model catalog.
- BloodHound OpenGraph community library (retrieved 2026-09-22) — no Teleport extension exists; TailscaleHound is the nearest access-broker graph.
- Cartography intel module list (retrieved 2026-09-22) — no Teleport module.

## Fields

- `name` — The desktop's name in Teleport. Required.
- `cluster_name` — The name of the Teleport cluster this record lives in — the same string as that cluster node's `name`. Part of the natural key because Teleport's names are unique only within one cluster (every cluster ships preset roles called `access`, `editor` and `auditor`). The traversable form of the same membership is the `BELONGS_TO_CLUSTER` edge; this column is what the key rests on (a key must be a column the generated search can filter).
- `addr` — The host's RDP address. Blank until observed.
- `domain` — The Active Directory domain, blank for non-AD desktops or when not observed.
- `labels` — The resource's labels (static `metadata.labels` plus the latest dynamic command-label values), as a flat string map. Role `*_labels` selectors match against these, which is how access is granted; empty means not observed, not unlabelled.
