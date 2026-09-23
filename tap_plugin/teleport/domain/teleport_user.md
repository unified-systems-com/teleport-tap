# teleport_user

## Blurb

A Teleport user: a local account (password + MFA) or an SSO user Teleport creates at login from a connector, with the traits that fill role templates.

## Purpose

Users are who holds roles. The local-vs-SSO split is itself a control: a local account is a bypass of the organization's IdP and its MFA, lifecycle and offboarding.

## Goals

- Count local vs SSO users.
- Show which roles each user holds and how (`HOLDS_ROLE.granted_by`).

## Identity

`NATURAL_KEY = (`cluster_name`, `name`)`. Teleport user names are unique within a cluster and are the identity stamped into the user certificate.

## Boundaries

- Not the person in the IdP — the SSO connector's IdP owns that; a user reaches it through `LOGS_IN_VIA_CONNECTOR`.
- Not bots (`teleport_bot`).

## Neutrality

Vendor-specific record; a neutral principal substrate may later link to it the way `github_core__github_repository` links to `git_core__git_repository`.

## Observability

**Not observed.** No collector exists (`req-teleport-collector`, Backlog), so nothing here has been read from a live cluster and nothing below is written from an executed call. What the documentation says: the record is readable with `tctl get` (or the gRPC API) by a Teleport identity whose role allows `read`/`list` on this resource kind; a Machine ID bot with a read-only role is the expected collector credential. Until a collector exists, every node of `teleport__teleport_user` on a grid is a design node (`dcom: design`) carrying only the fields its designer knew.

## Authoritative Source

- **Source:** Teleport documentation — Resources reference (goteleport.com/docs/reference/resources/), Teleport configuration reference, and the Teleport Terraform provider resource list
- **Version:** Teleport 18.x documentation and Terraform provider `~> 18.0`
- **Retrieved:** 2026-09-22

## Prior Art

- Teleport Terraform provider resource list (provider `~> 18.0`, retrieved 2026-09-22) — the curated set of Teleport resources worth managing; this type's counterpart is named in `specs/spec-teleport-v0.md` § Model catalog.
- BloodHound OpenGraph community library (retrieved 2026-09-22) — no Teleport extension exists; TailscaleHound is the nearest access-broker graph.
- Cartography intel module list (retrieved 2026-09-22) — no Teleport module.

## Fields

- `name` — The Teleport username (for an SSO user, the IdP's subject or email as the connector maps it). Required.
- `cluster_name` — The name of the Teleport cluster this record lives in — the same string as that cluster node's `name`. Part of the natural key because Teleport's names are unique only within one cluster (every cluster ships preset roles called `access`, `editor` and `auditor`). The traversable form of the same membership is the `BELONGS_TO_CLUSTER` edge; this column is what the key rests on (a key must be a column the generated search can filter).
- `user_type` — `local` for a user with a Teleport password, `sso` for a user Teleport created from a connector login. FedRAMP guidance expects none of the first once local auth is off. Blank until observed.
- `traits` — The user's traits (`logins`, `kubernetes_groups`, `db_users`, IdP attributes) that role templates interpolate. Empty means not observed.
- `created_at` — When the user record was created (ISO-8601). Blank until observed.
- `configuration` — The rest of the resource as Teleport reports it (the `spec` a collector did not lift into a column). Empty means not observed.
