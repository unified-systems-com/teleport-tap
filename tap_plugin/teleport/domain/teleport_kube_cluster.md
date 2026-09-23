# teleport_kube_cluster

## Blurb

A Kubernetes cluster registered with Teleport and served by a Kubernetes Service agent, reached through the proxy with Teleport-issued credentials mapped to Kubernetes users and groups.

## Purpose

See `teleport_ssh_node`: a protected resource, grouped by label, reached by roles.

## Goals

- List Kubernetes clusters by label and the roles that reach them.

## Identity

`NATURAL_KEY = (`cluster_name`, `name`)`. Kubernetes cluster names are unique within the Teleport cluster and set by whoever registers them, so a design knows them.

## Boundaries

- Not the EKS cluster itself (reached by `FRONTS_TARGET`).
- Not Kubernetes RBAC inside the cluster.

## Neutrality

Vendor-specific record of a neutral thing.

## Observability

**Not observed.** No collector exists (`req-teleport-collector`, Backlog), so nothing here has been read from a live cluster and nothing below is written from an executed call. What the documentation says: the record is readable with `tctl get` (or the gRPC API) by a Teleport identity whose role allows `read`/`list` on this resource kind; a Machine ID bot with a read-only role is the expected collector credential. Until a collector exists, every node of `teleport__teleport_kube_cluster` on a grid is a design node (`dcom: design`) carrying only the fields its designer knew.

## Authoritative Source

- **Source:** Teleport documentation — Resources reference (goteleport.com/docs/reference/resources/), Teleport configuration reference, and the Teleport Terraform provider resource list
- **Version:** Teleport 18.x documentation and Terraform provider `~> 18.0`
- **Retrieved:** 2026-09-22

## Prior Art

- Teleport Terraform provider resource list (provider `~> 18.0`, retrieved 2026-09-22) — the curated set of Teleport resources worth managing; this type's counterpart is named in `specs/spec-teleport-v0.md` § Model catalog.
- BloodHound OpenGraph community library (retrieved 2026-09-22) — no Teleport extension exists; TailscaleHound is the nearest access-broker graph.
- Cartography intel module list (retrieved 2026-09-22) — no Teleport module.

## Fields

- `name` — The Kubernetes cluster's name in Teleport. Required.
- `cluster_name` — The name of the Teleport cluster this record lives in — the same string as that cluster node's `name`. Part of the natural key because Teleport's names are unique only within one cluster (every cluster ships preset roles called `access`, `editor` and `auditor`). The traversable form of the same membership is the `BELONGS_TO_CLUSTER` edge; this column is what the key rests on (a key must be a column the generated search can filter).
- `labels` — The resource's labels (static `metadata.labels` plus the latest dynamic command-label values), as a flat string map. Role `*_labels` selectors match against these, which is how access is granted; empty means not observed, not unlabelled.
- `configuration` — The rest of the resource as Teleport reports it (the `spec` a collector did not lift into a column). Empty means not observed.
