# teleport_sso_connector

## Blurb

A SAML, OIDC or GitHub authentication connector: the trust Teleport places in an external identity provider, and the mappings from the IdP's attributes, claims or teams to Teleport roles.

## Purpose

The connector is where Teleport hands authentication to the organization's IdP, and its mappings decide who becomes what. The most consequential edge in a Teleport cluster is often `MAPS_TO_ROLE`: an IdP group that grants `editor`.

## Goals

- List connectors and the IdP each trusts.
- Show which IdP attribute values map to which roles.

## Identity

`NATURAL_KEY = (`cluster_name`, `kind`, `name`)`. Teleport namespaces connectors by kind (`saml`, `oidc`, `github` are separate resource kinds), so a name is unique only within its kind and cluster.

## Boundaries

- Not the IdP: the target of `DELEGATES_LOGIN` is the IdP's own node (an OIDC issuer, an Okta org).
- Not `login_rule` resources (trait transforms) — Backlog.

## Neutrality

Vendor-specific resource over neutral protocols. The OIDC half points at the neutral `identity_core__oidc_issuer` by edge rather than copying the issuer.

## Observability

**Not observed.** No collector exists (`req-teleport-collector`, Backlog), so nothing here has been read from a live cluster and nothing below is written from an executed call. What the documentation says: the record is readable with `tctl get` (or the gRPC API) by a Teleport identity whose role allows `read`/`list` on this resource kind; a Machine ID bot with a read-only role is the expected collector credential. Until a collector exists, every node of `teleport__teleport_sso_connector` on a grid is a design node (`dcom: design`) carrying only the fields its designer knew.

## Authoritative Source

- **Source:** Teleport documentation — Resources reference (goteleport.com/docs/reference/resources/), Teleport configuration reference, and the Teleport Terraform provider resource list
- **Version:** Teleport 18.x documentation and Terraform provider `~> 18.0`
- **Retrieved:** 2026-09-22

## Prior Art

- Teleport Terraform provider resource list (provider `~> 18.0`, retrieved 2026-09-22) — the curated set of Teleport resources worth managing; this type's counterpart is named in `specs/spec-teleport-v0.md` § Model catalog.
- BloodHound OpenGraph community library (retrieved 2026-09-22) — no Teleport extension exists; TailscaleHound is the nearest access-broker graph.
- Cartography intel module list (retrieved 2026-09-22) — no Teleport module.

## Fields

- `name` — The connector name users pick at login (`tsh login --auth=<name>`). Required.
- `cluster_name` — The name of the Teleport cluster this record lives in — the same string as that cluster node's `name`. Part of the natural key because Teleport's names are unique only within one cluster (every cluster ships preset roles called `access`, `editor` and `auditor`). The traversable form of the same membership is the `BELONGS_TO_CLUSTER` edge; this column is what the key rests on (a key must be a column the generated search can filter).
- `kind` — Which protocol: `saml`, `oidc` or `github`. Required; part of the key.
- `display` — The label on the login button. Blank until observed.
- `idp_url` — The identity provider's address as the connector holds it: the OIDC `issuer_url`, the SAML `entity_descriptor_url` (or SSO URL), or the GitHub `endpoint_url`. The IdP itself is reached by `DELEGATES_LOGIN`; this is the string the trust was configured with. Blank until observed.
- `configuration` — The rest of the resource as Teleport reports it (the `spec` a collector did not lift into a column). Empty means not observed.
