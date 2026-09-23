# teleport_bot

## Blurb

A Machine ID bot: a non-human identity whose `tbot` agent joins the cluster (by token or a delegated join method) and renews short-lived certificates for the roles it holds.

## Purpose

CI pipelines, Ansible and service accounts reach infrastructure through bots. Their join method is the whole trust story: a GitHub or IAM join ties the identity to a workload, a static token does not.

## Goals

- List bots, their roles (`HOLDS_ROLE`) and how they join (`JOINS_WITH_TOKEN`).

## Identity

`NATURAL_KEY = (`cluster_name`, `name`)`. Bot names are unique within a cluster (Teleport creates a `bot-<name>` user and role from it).

## Boundaries

- Not each running `tbot` instance (`bot_instance`, Backlog).
- Not the generated `bot-<name>` user and role; they are Teleport plumbing for the bot, not separate identities.

## Neutrality

Vendor-specific (Teleport Machine ID).

## Observability

**Not observed.** No collector exists (`req-teleport-collector`, Backlog), so nothing here has been read from a live cluster and nothing below is written from an executed call. What the documentation says: the record is readable with `tctl get` (or the gRPC API) by a Teleport identity whose role allows `read`/`list` on this resource kind; a Machine ID bot with a read-only role is the expected collector credential. Until a collector exists, every node of `teleport__teleport_bot` on a grid is a design node (`dcom: design`) carrying only the fields its designer knew.

## Authoritative Source

- **Source:** Teleport documentation — Resources reference (goteleport.com/docs/reference/resources/), Teleport configuration reference, and the Teleport Terraform provider resource list
- **Version:** Teleport 18.x documentation and Terraform provider `~> 18.0`
- **Retrieved:** 2026-09-22

## Prior Art

- Teleport Terraform provider resource list (provider `~> 18.0`, retrieved 2026-09-22) — the curated set of Teleport resources worth managing; this type's counterpart is named in `specs/spec-teleport-v0.md` § Model catalog.
- BloodHound OpenGraph community library (retrieved 2026-09-22) — no Teleport extension exists; TailscaleHound is the nearest access-broker graph.
- Cartography intel module list (retrieved 2026-09-22) — no Teleport module.

## Fields

- `name` — The bot name. Required.
- `cluster_name` — The name of the Teleport cluster this record lives in — the same string as that cluster node's `name`. Part of the natural key because Teleport's names are unique only within one cluster (every cluster ships preset roles called `access`, `editor` and `auditor`). The traversable form of the same membership is the `BELONGS_TO_CLUSTER` edge; this column is what the key rests on (a key must be a column the generated search can filter).
- `max_session_ttl` — The longest certificate lifetime the bot may request, as Teleport reports it (e.g. `12h`). Blank until observed.
- `traits` — The bot's traits (`logins`, `db_users` …) filled into its roles' templates. Empty means not observed.
- `configuration` — The rest of the resource as Teleport reports it (the `spec` a collector did not lift into a column). Empty means not observed.
