# `teleport.plane`

## Blurb

Which part of a Teleport cluster a node or edge belongs to — deployment, trust, identity, policy or resource — so a view can select one plane without listing types.

## Purpose

The teleport corpus has eighteen node types and twenty-four edge types across five concerns. A page that draws the deployment wants only the deployment plane; a policy review wants only the policy plane. The dimension is the stable handle for that selection (`n.dimensions["teleport.plane"] = "deployment"`), declared on every type and edge.

## Goals

- Select a plane in one predicate.
- Keep the five concerns explicit so a new type must choose one.

## Identity

The key is `teleport.plane`, in the `teleport.` namespace this plugin owns. Address it in brackets in Gryphon — `n.dimensions["teleport.plane"]` — because a dotted path is read as nested keys and matches nothing.

## Boundaries

- Not the design/observed axis (`dcom`) and not environment membership; both belong to the observation.
- Not a severity or sensitivity ranking.

## Neutrality

Vendor-specific; the five planes are this corpus's grouping of Teleport's resource kinds.

## Observability

Declared, never fetched: applied from type and edge-type defaults at creation.

## Authoritative Source

- **Source:** `specs/spec-teleport-v0.md` (`req-teleport-dimension`)
- **Version:** teleport-tap corpus v1
- **Retrieved:** 2026-09-22

## Prior Art

- Teleport's own documentation groups its reference the same way (deploy a cluster, access controls, enroll resources), retrieved 2026-09-22.

## Values

- `deployment` — The processes that make up the cluster and what they run on and write to: the cluster, auth servers, proxy servers, agents, and the edges between them and their compute and storage.
- `trust` — Cryptographic trust: certificate authorities, the keys they sign with, and root/leaf cluster trust.
- `identity` — Who and what authenticates: users, SSO connectors, bots, trusted devices, and the IdPs connectors delegate to.
- `policy` — What is permitted and how it was granted: roles, join tokens, access lists, access requests and every grant edge.
- `resource` — What the cluster protects: SSH nodes, Kubernetes clusters, databases, applications and Windows desktops, the agents that serve them and the targets they front.
