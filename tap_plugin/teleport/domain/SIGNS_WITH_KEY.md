# SIGNS_WITH_KEY

## Blurb

A certificate authority signs with a private key held outside the backend: an AWS KMS key, a GCP KMS key or an HSM object. Target open for those three stores. Absent when the key is `software` (held in the backend) — read `key_storage` on the CA to tell absent-because-software from not observed.

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

- **Source:** `teleport__teleport_certificate_authority`
- **Target:** open (any type — see Blurb)
- **Dimensions:** `teleport.plane: trust`

Properties:

- `key_state` — `active` for the key that signs now; `additional_trusted` for a key kept trusted during rotation.
