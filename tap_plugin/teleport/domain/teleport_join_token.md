# teleport_join_token

## Blurb

A provision token: what a new agent, proxy or bot must present to join the cluster, with its join method (static secret, EC2/IAM, GitHub, GitLab, Kubernetes, TPM …), the system roles it confers and the external identities it admits.

## Purpose

Joining is the cluster's front door for machines. A long-lived static token with the `Node` role is a standing credential; a delegated join bound to one AWS account or one GitHub repository is not. Tokens are nodes because agents and bots point at them and they point at external identities.

## Goals

- Show every join path into the cluster and its method.
- Flag static-secret tokens and what they confer.

## Identity

`NATURAL_KEY = (`cluster_name`, `name`)`. Token names are unique within a cluster. For the `token` join method the name IS the secret, so for that method only its digest (`sha256:<64 hex>`) is accepted in `name` — the model refuses anything else; delegated methods have non-secret names.

## Boundaries

- Never the secret value.
- Not the one-time invite tokens for user signup/reset (`user_token`) — out of scope.

## Neutrality

Vendor-specific.

## Observability

**Not observed.** No collector exists (`req-teleport-collector`, Backlog), so nothing here has been read from a live cluster and nothing below is written from an executed call. What the documentation says: the record is readable with `tctl get` (or the gRPC API) by a Teleport identity whose role allows `read`/`list` on this resource kind; a Machine ID bot with a read-only role is the expected collector credential. Until a collector exists, every node of `teleport__teleport_join_token` on a grid is a design node (`dcom: design`) carrying only the fields its designer knew.

## Authoritative Source

- **Source:** Teleport documentation — Resources reference (goteleport.com/docs/reference/resources/), Teleport configuration reference, and the Teleport Terraform provider resource list
- **Version:** Teleport 18.x documentation and Terraform provider `~> 18.0`
- **Retrieved:** 2026-09-22

## Prior Art

- Teleport Terraform provider resource list (provider `~> 18.0`, retrieved 2026-09-22) — the curated set of Teleport resources worth managing; this type's counterpart is named in `specs/spec-teleport-v0.md` § Model catalog.
- BloodHound OpenGraph community library (retrieved 2026-09-22) — no Teleport extension exists; TailscaleHound is the nearest access-broker graph.
- Cartography intel module list (retrieved 2026-09-22) — no Teleport module.

## Fields

- `name` — The token resource name. For delegated methods (`iam`, `github` …) a plain name; for the `token` method the model refuses any value but `sha256:<64 hex>` of the secret (`validate()`), so the secret itself cannot be stored. Required.
- `cluster_name` — The name of the Teleport cluster this record lives in — the same string as that cluster node's `name`. Part of the natural key because Teleport's names are unique only within one cluster (every cluster ships preset roles called `access`, `editor` and `auditor`). The traversable form of the same membership is the `BELONGS_TO_CLUSTER` edge; this column is what the key rests on (a key must be a column the generated search can filter).
- `join_method` — How a joiner proves itself: `token` (shared secret), `ec2`, `iam`, `github`, `gitlab`, `kubernetes`, `azure`, `gcp`, `tpm`, `circleci`, `spacelift`, `terraform_cloud`, `bitbucket`, `oracle`, `azure_devops`, `bound_keypair` …. A string because Teleport adds methods most releases. Required: a design decides it.
- `system_roles` — The system roles a joiner receives (`spec.roles`). Empty means not observed.
- `bot_name` — For a `Bot` token, the bot it admits (`spec.bot_name`). The bot is also reached by `JOINS_WITH_TOKEN`; this is the string the token names. Blank when not a bot token or not observed.
- `allow_rules` — The token's `spec.allow` rules (AWS account/ARN, GitHub repository/workflow, Kubernetes service account …). The rules whose identities are on the grid are also `ADMITS_IDENTITY` edges. Empty means not observed.
- `expires_at` — When the token expires (ISO-8601). Blank means not observed, not "never".
