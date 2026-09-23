# teleport_access_list

## Blurb

An access list: a set of owners and members that grants roles and traits to its members, with a periodic access review (audit) that owners must complete.

## Purpose

Access lists are Teleport's answer to recurring access review, which is exactly what a FedRAMP assessor samples. The front page needs what each list grants, who owns it, and whether its review is overdue.

## Goals

- List access lists with their grants, owners and review date.
- Model nested lists (a list as a member of a list).

## Identity

`NATURAL_KEY = (`cluster_name`, `name`)`. Teleport names access lists with a UUID it assigns (or a name set by IaC); unique within the cluster. A design keys on the name it chooses; revisit if the collector must key on the assigned UUID.

## Boundaries

- Not the membership records as nodes — membership is the `MEMBER_OF_ACCESS_LIST` edge with an owner/member property.
- Not access list review history (`access_list_review`) — Backlog.

## Neutrality

Vendor-specific (Teleport Identity Governance).

## Observability

**Not observed.** No collector exists (`req-teleport-collector`, Backlog), so nothing here has been read from a live cluster and nothing below is written from an executed call. What the documentation says: the record is readable with `tctl get` (or the gRPC API) by a Teleport identity whose role allows `read`/`list` on this resource kind; a Machine ID bot with a read-only role is the expected collector credential. Until a collector exists, every node of `teleport__teleport_access_list` on a grid is a design node (`dcom: design`) carrying only the fields its designer knew.

## Authoritative Source

- **Source:** Teleport documentation — Resources reference (goteleport.com/docs/reference/resources/), Teleport configuration reference, and the Teleport Terraform provider resource list
- **Version:** Teleport 18.x documentation and Terraform provider `~> 18.0`
- **Retrieved:** 2026-09-22

## Prior Art

- Teleport Terraform provider resource list (provider `~> 18.0`, retrieved 2026-09-22) — the curated set of Teleport resources worth managing; this type's counterpart is named in `specs/spec-teleport-v0.md` § Model catalog.
- BloodHound OpenGraph community library (retrieved 2026-09-22) — no Teleport extension exists; TailscaleHound is the nearest access-broker graph.
- Cartography intel module list (retrieved 2026-09-22) — no Teleport module.

## Fields

- `name` — The access list resource name. Required.
- `cluster_name` — The name of the Teleport cluster this record lives in — the same string as that cluster node's `name`. Part of the natural key because Teleport's names are unique only within one cluster (every cluster ships preset roles called `access`, `editor` and `auditor`). The traversable form of the same membership is the `BELONGS_TO_CLUSTER` edge; this column is what the key rests on (a key must be a column the generated search can filter).
- `title` — The human title shown in the UI. Blank until observed.
- `description` — The list's description. Blank until observed.
- `audit_frequency` — How often owners must review membership (e.g. `90d`) — FedRAMP AC-2 periodic review. Blank until observed.
- `next_audit_date` — When the next review is due (ISO-8601). Blank until observed; the page flags a date in the past.
- `grants` — The list's `spec.grants` (roles and traits for members). The role grants are also `GRANTS_ROLE` edges; traits have no edge. Empty means not observed.
- `membership_requires` — Roles/traits a user must already hold to be a member. Empty means not observed.
