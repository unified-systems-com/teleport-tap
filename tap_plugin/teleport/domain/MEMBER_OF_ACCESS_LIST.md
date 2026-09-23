# MEMBER_OF_ACCESS_LIST

## Blurb

A user (or a nested access list) is a member or an owner of an access list.

## Purpose

Part of the teleport corpus (`specs/spec-teleport-v0.md` § Edge types, `req-teleport-edges`). Both ends are teleport types.

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

- **Source:** `teleport__teleport_user`, `teleport__teleport_access_list`
- **Target:** `teleport__teleport_access_list`
- **Dimensions:** `teleport.plane: policy`

Properties:

- `membership` — Owner (reviews and manages) or member (receives grants).
- `expires_at` — When the membership expires (ISO-8601); absent when it does not or when not observed.
