# DELEGATES_LOGIN

## Blurb

An SSO connector hands login to an external identity provider. Target open: for an OIDC connector the neutral `identity_core__oidc_issuer`; for SAML the IdP's own node (an Okta org, an Entra tenant); for GitHub the GitHub platform or organization. The connector's `idp_url` is the string the trust was configured with.

## Purpose

Part of the teleport corpus (`specs/spec-teleport-v0.md` § Edge types, `req-teleport-edges`). The target is deliberately open (the skill's cross-plugin rule, step 2): the far end lives in whichever plugin models that platform, so teleport declares no dependency on it.

## Goals

- Make this relationship traversable on the grid rather than implied by a field.

## Identity

Edges carry no natural key; ids are assigned (`req-grid-entity-natural-key`). One edge per (source, target) pair.

## Boundaries

- Mechanical relationship only; it asserts nothing about whether the relationship is safe — properties carry what a view needs to tell shape from risk.

## Neutrality

Vendor-specific (Teleport).

## Observability

**Not observed.** No collector exists (`req-teleport-collector`, Backlog), so nothing here has been read from a live cluster and nothing below is written from an executed call. What the documentation says: the relationship is readable from the source resource's spec (or, for deployment edges, from the Teleport process configuration and the cloud deployment). In a design it is drawn by the designer.

## Authoritative Source

- **Source:** Teleport documentation — Resources reference (goteleport.com/docs/reference/resources/), Teleport configuration reference, and the Teleport Terraform provider resource list
- **Version:** Teleport 18.x documentation and Terraform provider `~> 18.0`
- **Retrieved:** 2026-09-22

## Prior Art

- Teleport HA deployment on AWS guide and Storage Backends reference (Teleport 18.x docs, retrieved 2026-09-22).

## Endpoints

- **Source:** `teleport__teleport_sso_connector`
- **Target:** open (any type — see Blurb)
- **Dimensions:** `teleport.plane: identity`
