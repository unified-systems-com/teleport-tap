# teleport_certificate_authority

## Blurb

One of the cluster's certificate authorities (host, user, database, OpenSSH, JWT, SAML IdP, OIDC IdP, SPIFFE …): the key pair that signs a class of short-lived certificates, with its rotation phase and where its private key is stored.

## Purpose

Certificates are Teleport's whole security model: whoever holds a CA key can mint any identity. FedRAMP operators are asked where those keys live (KMS/HSM) and when they were last rotated, so the CA is a node the page can list and a key edge (`SIGNS_WITH_KEY`) can point from.

## Goals

- Show CA rotation state per type.
- Show whether keys are in KMS/HSM and which key (`SIGNS_WITH_KEY`).

## Identity

`NATURAL_KEY = (`cluster_name`, `ca_type`)`. A cluster has exactly one CA of each type, and Teleport names the CA resource after the cluster, so `(cluster_name, ca_type)` is Teleport's own identity and a design can know it.

## Boundaries

- No free-form `configuration` field: the resources Teleport keeps for this object can carry secret material or personal data (key material, a connector's client secret, a user's traits), so only promoted columns are stored.
- Not the issued certificates — short-lived and never stored.
- Not a trusted cluster's copy of another cluster's CA; cross-cluster trust is the `TRUSTS_ROOT_CLUSTER` edge.

## Neutrality

Vendor-specific. The CA-type set and rotation phases are Teleport's.

## Observability

**Not observed.** No collector exists (`req-teleport-collector`, Backlog), so nothing here has been read from a live cluster and nothing below is written from an executed call. What the documentation says: the record is readable with `tctl get` (or the gRPC API) by a Teleport identity whose role allows `read`/`list` on this resource kind; a Machine ID bot with a read-only role is the expected collector credential. Until a collector exists, every node of `teleport__teleport_certificate_authority` on a grid is a design node (`dcom: design`) carrying only the fields its designer knew.

## Authoritative Source

- **Source:** Teleport documentation — Resources reference (goteleport.com/docs/reference/resources/), Teleport configuration reference, and the Teleport Terraform provider resource list
- **Version:** Teleport 18.x documentation and Terraform provider `~> 18.0`
- **Retrieved:** 2026-09-22

## Prior Art

- Teleport Terraform provider resource list (provider `~> 18.0`, retrieved 2026-09-22) — the curated set of Teleport resources worth managing; this type's counterpart is named in `specs/spec-teleport-v0.md` § Model catalog.
- BloodHound OpenGraph community library (retrieved 2026-09-22) — no Teleport extension exists; TailscaleHound is the nearest access-broker graph.
- Cartography intel module list (retrieved 2026-09-22) — no Teleport module.

## Fields

- `cluster_name` — The name of the Teleport cluster this record lives in — the same string as that cluster node's `name`. Part of the natural key because Teleport's names are unique only within one cluster (every cluster ships preset roles called `access`, `editor` and `auditor`). The traversable form of the same membership is the `BELONGS_TO_CLUSTER` edge; this column is what the key rests on (a key must be a column the generated search can filter).
- `ca_type` — Which authority: `host` signs host certificates, `user` signs user certificates, `db`/`db_client` the database mTLS pair, and so on. Required; the second half of the key.
- `rotation_phase` — Where the CA is in Teleport's rotation state machine (`tctl status`). `standby` is at rest; any other value is a rotation in flight. Blank until observed.
- `last_rotated_at` — When the last rotation completed (ISO-8601). Blank until observed — and blank is not "never rotated".
- `key_storage` — Where the CA's active private keys live: in the backend (`software`), in AWS KMS or GCP KMS (`ca_key_params`), or in an HSM over PKCS#11. Blank until observed.
