# teleport_agent

## Blurb

A Teleport process that joined the cluster to serve protected resources: it runs one or more of the SSH, Kubernetes, Database, Application, Windows Desktop and Discovery services and dials the proxy over a reverse tunnel.

## Purpose

Agents are how resources enter the cluster, and the join is the trust decision a FedRAMP assessor asks about: which token admitted this process, and what does it now serve. One node per process, not per service, because the process is what joins, holds a host certificate and runs somewhere.

## Goals

- Show which agent serves which resource (`SERVES_RESOURCE`).
- Show how it joined (`JOINS_WITH_TOKEN`) and where it runs (`RUNS_ON_COMPUTE`).

## Identity

`NATURAL_KEY = (`cluster_name`, `name`)`. The design knows a name; the host UUID arrives when the agent joins. Revisit to `(cluster_name, host_id)` when observed.

## Boundaries

- No free-form `configuration` field: the resources Teleport keeps for this object can carry secret material or personal data (key material, a connector's client secret, a user's traits), so only promoted columns are stored.
- Not a protected resource: an SSH host an agent runs on is still a `teleport_ssh_node`, served by the agent.
- Not the Machine ID `tbot` process — that is a `teleport_bot` identity.

## Neutrality

Vendor-specific. Boundary has workers and StrongDM has gateways/relays, but the one-process-many-services join model is Teleport's.

## Observability

**Not observed.** No collector exists (`req-teleport-collector`, Backlog), so nothing here has been read from a live cluster and nothing below is written from an executed call. What the documentation says: the record is readable with `tctl get` (or the gRPC API) by a Teleport identity whose role allows `read`/`list` on this resource kind; a Machine ID bot with a read-only role is the expected collector credential. Until a collector exists, every node of `teleport__teleport_agent` on a grid is a design node (`dcom: design`) carrying only the fields its designer knew.

## Authoritative Source

- **Source:** Teleport documentation — Resources reference (goteleport.com/docs/reference/resources/), Teleport configuration reference, and the Teleport Terraform provider resource list
- **Version:** Teleport 18.x documentation and Terraform provider `~> 18.0`
- **Retrieved:** 2026-09-22

## Prior Art

- Teleport Terraform provider resource list (provider `~> 18.0`, retrieved 2026-09-22) — the curated set of Teleport resources worth managing; this type's counterpart is named in `specs/spec-teleport-v0.md` § Model catalog.
- BloodHound OpenGraph community library (retrieved 2026-09-22) — no Teleport extension exists; TailscaleHound is the nearest access-broker graph.
- Cartography intel module list (retrieved 2026-09-22) — no Teleport module.

## Fields

- `name` — The agent's name (hostname, or the planned name in a design). Required.
- `cluster_name` — The name of the Teleport cluster this record lives in — the same string as that cluster node's `name`. Part of the natural key because Teleport's names are unique only within one cluster (every cluster ships preset roles called `access`, `editor` and `auditor`). The traversable form of the same membership is the `BELONGS_TO_CLUSTER` edge; this column is what the key rests on (a key must be a column the generated search can filter).
- `host_id` — The host UUID the agent received when it joined. Blank until observed; the future key.
- `teleport_version` — The Teleport version the agent runs — the one fact auto-update and CVE triage need. Blank until observed.
- `services` — Which Teleport services this process runs, from the instance inventory. Empty means not observed.
