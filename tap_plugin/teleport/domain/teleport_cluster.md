# teleport_cluster

## Blurb

A Teleport cluster: the access service (Auth Service + Proxy Service and the backend they share) that brokers SSH, Kubernetes, database, application and desktop access, and the cluster-wide settings that govern it.

## Purpose

The outer node a reader recognises as Teleport, and the home of the cluster-wide singletons (`cluster_auth_preference`, `session_recording_config`, `cluster_networking_config`). Those singletons are fields here, not nodes: nothing points at them and none exists without the cluster (build-domain-vocabulary Step 4).

## Goals

- Let a design place the cluster before anything is built.
- Answer the FedRAMP front-page questions about the cluster itself in one row: FIPS build, local auth off, MFA, device trust, recording mode.
- Anchor every in-cluster record through `cluster_name`.

## Identity

`NATURAL_KEY = (`name`)`. The cluster name is Teleport's own stable identity: it is set once at first start (`cluster_name`), baked into every certificate the cluster issues, and cannot be changed without rebuilding the cluster. A design knows it before anything is built.

## Boundaries

- No free-form `configuration` field: the resources Teleport keeps for this object can carry secret material or personal data (key material, a connector's client secret, a user's traits), so only promoted columns are stored.
- Not the Auth or Proxy processes — those are `teleport_auth_server` / `teleport_proxy_server`.
- Not the storage: the DynamoDB tables and S3 bucket are cloud nodes the auth servers reach by edges.
- Root/leaf trust is the `TRUSTS_ROOT_CLUSTER` edge, not a field.

## Neutrality

Vendor-specific. Other access brokers (HashiCorp Boundary, StrongDM, Tailscale) have a control plane, but the certificate-authority-per-cluster design and every singleton here are Teleport's.

## Observability

**Not observed.** No collector exists (`req-teleport-collector`, Backlog), so nothing here has been read from a live cluster and nothing below is written from an executed call. What the documentation says: the record is readable with `tctl get` (or the gRPC API) by a Teleport identity whose role allows `read`/`list` on this resource kind; a Machine ID bot with a read-only role is the expected collector credential. Until a collector exists, every node of `teleport__teleport_cluster` on a grid is a design node (`dcom: design`) carrying only the fields its designer knew.

## Authoritative Source

- **Source:** Teleport documentation — Resources reference (goteleport.com/docs/reference/resources/), Teleport configuration reference, and the Teleport Terraform provider resource list
- **Version:** Teleport 18.x documentation and Terraform provider `~> 18.0`
- **Retrieved:** 2026-09-22

## Prior Art

- Teleport Terraform provider resource list (provider `~> 18.0`, retrieved 2026-09-22) — the curated set of Teleport resources worth managing; this type's counterpart is named in `specs/spec-teleport-v0.md` § Model catalog.
- BloodHound OpenGraph community library (retrieved 2026-09-22) — no Teleport extension exists; TailscaleHound is the nearest access-broker graph.
- Cartography intel module list (retrieved 2026-09-22) — no Teleport module.

## Fields

- `name` — The cluster name (`auth_service.cluster_name`), which Teleport stamps into every host and user certificate. Required and the natural key, and the value every member's `cluster_name` carries. The value `teleport__teleport_cluster` is refused: the /teleport page uses the type's own slug as its every-cluster sentinel.
- `proxy_address` — The public address of the Proxy Service (host:port) users and agents dial. Blank until observed.
- `teleport_version` — The Teleport version the Auth Service reports (`tctl status`). Blank until observed.
- `edition` — Which build runs the cluster: `community` or `enterprise`. FedRAMP-relevant features (FIPS builds, HSM/KMS key storage, device trust, access lists) are Enterprise-only. Blank until observed.
- `fips` — Whether the cluster runs the FIPS build started with `--fips` (BoringCrypto; `teleport version` reports `X:boringcrypto`). Three states: blank is not observed, never `disabled`.
- `signature_algorithm_suite` — The `cluster_auth_preference.signature_algorithm_suite`: which key algorithms new CA and certificate keys use. A FIPS cluster needs `fips-v1` (or `hsm-v1` with HSM/KMS). Blank until observed.
- `local_auth` — Whether `cluster_auth_preference.allow_local_auth` permits password login. Teleport's FedRAMP guidance disables it so every human signs in through an SSO connector. Blank until observed.
- `second_factor` — The `cluster_auth_preference.second_factor(s)` setting as Teleport reports it (e.g. `webauthn`, `on`, `otp`). A string rather than an enum because the vocabulary has changed across major versions. Blank until observed.
- `device_trust_mode` — The `cluster_auth_preference.device_trust.mode`: whether access demands an enrolled trusted device. Blank until observed.
- `session_recording_mode` — The `session_recording_config.mode`: where sessions are recorded and whether recording is synchronous. Blank until observed.
- `tags` — Free-form tags a design or operator attaches to the cluster node. Not a Teleport concept.
