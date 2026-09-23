# TAP Teleport Plugin Specification

**Teleport infrastructure access as grid vocabulary: v0 carries one outer node, the Teleport cluster (the access service), so a design can place it before anything is collected.**

## Plugin Identity

| Field | Value |
| --- | --- |
| Slug | `teleport` |
| Display name | TAP Teleport |
| Description | Teleport infrastructure access as grid vocabulary: v0 carries one outer node, the Teleport cluster (the access service), so a design can place it before anything is collected. |
| Kind | Leaf plugin: Teleport vocabulary. Consumes nothing in v0; consumed by instance plugins that place it in a design (highbar first). |

**Default dimensions**

| Dimension | Value | Why |
| --- | --- | --- |
| (none) | | `teleport__teleport_cluster` declares no default dimension in v0. The only candidate is the `dcom` axis, and its value is a property of the observation, not the type: a seeded design node is `design`, the same type observed by a future collector is `configuration`. The seeding bundle stamps it per node. |

## Philosophy

This is a thin v0 (ruled 2026-09-22 for the highbar starter set): it exists to put the piece on the board so a design can reference it, not to model the domain. The full `create-plugin-spec` interview, prior-art search and requirement buy-in run when this plugin grows past v0; nothing here pre-empts them.

The one type, `teleport__teleport_cluster`, is the outermost thing a reader of a diagram recognises for Teleport. Everything inside it (users, groups, policies, projects, sessions) is later vocabulary, added when something observes or designs it.

Three states hold for every observed field: blank means *not observed*, never *empty*. A design-phase node carries only its name; its identifiers stay blank until a collector reads them.

**Provenance markers:** every node of this type seeded in v0 is *designed* (stamped `dcom: design` by the bundle that seeds it). No field is *observed* until the collector (`req-teleport-collector`, Backlog) exists.

## Goals

| # | Name | Description |
| --- | --- | --- |
| 1 | On The Board | Exist as an installable plugin so the highbar stack can boot with it. |
| 2 | Designable | Let a design place the Teleport outer node before any access exists. |

## Requirements

| RID | Name | Status | Notes |
| --- | --- | --- | --- |
| req-teleport-model | [Teleport Cluster Model](#teleport-cluster-model) | Implemented | The one outer node: its fields, natural key, icon and display |
| req-teleport-record | [CI Record and Tests](#ci-record-and-tests) | Implemented | The in-package `ci` boot record and the manifest/behaviour tests |
| req-teleport-collector | [Collector](#collector) | Backlog | Observe real Teleport state onto the grid; deferred until access exists |

---

### Teleport Cluster Model
----
RID: `req-teleport-model`

Status: `Implemented`

A Teleport cluster: the access service (auth + proxy) that brokers SSH, Kubernetes, database, application and desktop access.

#### Implementation

`tap_plugin/teleport/models/teleport_cluster.py` defines `TeleportCluster(BaseModel)` with `ENTITY_TYPE = "teleport__teleport_cluster"`, `ENTITY_ICON = "teleport-cluster"` (SVG at `static/teleport/icons/teleport-cluster.svg`), no default dimensions, and fields `name` (required), `proxy_address` (The cluster's public proxy address (host:port). Blank until observed.), `configuration` (object) and `tags` (object). `NATURAL_KEY = ("name",)`: a design-phase node has no observed identifier, so its name is the only fact it carries; the key is revisited when `req-teleport-collector` makes `proxy_address` observable.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-teleport-model-1 | Created Through The Service Layer | Implemented | A `create_node` write with only `name` succeeds and the row carries it. | |
| req-teleport-model-2 | Name Required | Implemented | A `create_node` write without `name` is refused. | |
| req-teleport-model-3 | Keyed By Name | Implemented | `NATURAL_KEY` is `("name",)` and every key field is a model field. | |

---

### CI Record and Tests
----
RID: `req-teleport-record`

Status: `Implemented`

The in-package `ci` boot record (`req-boot-bootstrap-ci-record`) and the tests that run in it.

#### Implementation

`tap_plugin/teleport/boot/ci.boot.json` installs this plugin alone (it declares no dependencies), offline and credential-free; the consumer flips self to editable. `tap_plugin/teleport/tests/test_teleport_manifest.py` runs `validate_plugin` at structure and strict levels; `tests/test_teleport_cluster.py` covers `req-teleport-model`.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-teleport-record-1 | Record Declared | Implemented | The manifest declares the `ci` record with its sha256. | |
| req-teleport-record-2 | Validates Strict | Implemented | `validate_plugin --strict` passes on the package. | |

---

### Collector
----
RID: `req-teleport-collector`

Status: `Backlog`

Observe real Teleport state onto the grid; deferred until access exists.

## Model catalog

| Model | Entity type | Category | Rationale |
| --- | --- | --- | --- |
| `TeleportCluster` | `teleport__teleport_cluster` | Outer node | The one node a reader recognises as Teleport; everything else nests inside it later. |

## Icons

`teleport-cluster` is Teleport's own mark, used nominatively to identify the vendor on diagrams. The mark remains its owner's trademark; it is not covered by this repository's licence.
