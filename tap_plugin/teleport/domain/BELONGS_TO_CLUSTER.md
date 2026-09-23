# BELONGS_TO_CLUSTER

## Blurb

A Teleport record or process belongs to one cluster: it is stored in (or heartbeats into) that cluster's backend and is governed by its CAs. The traversable form of the `cluster_name` column every in-cluster type carries for its natural key — the same pairing as github_core's `full_name` column beside its `OWNS_REPO` edge. One relationship over every in-cluster type, like aws_core's account membership: the target is always the cluster and the meaning never varies by source.

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

- **Source:** `teleport__teleport_auth_server`, `teleport__teleport_proxy_server`, `teleport__teleport_agent`, `teleport__teleport_certificate_authority`, `teleport__teleport_role`, `teleport__teleport_user`, `teleport__teleport_sso_connector`, `teleport__teleport_bot`, `teleport__teleport_join_token`, `teleport__teleport_access_list`, `teleport__teleport_access_request`, `teleport__teleport_trusted_device`, `teleport__teleport_ssh_node`, `teleport__teleport_kube_cluster`, `teleport__teleport_database`, `teleport__teleport_app`, `teleport__teleport_windows_desktop`
- **Target:** `teleport__teleport_cluster`
- **Dimensions:** `teleport.plane: deployment`
