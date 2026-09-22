# teleport-tap

Teleport infrastructure access as grid vocabulary: v0 carries one outer node, the Teleport cluster (the access service), so a design can place it before anything is collected.

## What this plugin owns

One type in v0: `teleport__teleport_cluster` — a Teleport cluster: the access service (auth + proxy) that brokers SSH, Kubernetes, database, application and desktop access. A design can place it before any access exists; everything inside it is later vocabulary.

## Read first

`specs/spec-teleport-v0.md` — this is a thin v0 that puts the piece on the board; the full spec interview runs when the plugin grows.

## Stand it up

From a TAP core checkout:

```bash
scripts/spawn-session.sh <label> cli --from 'git+https://github.com/unified-systems-com/teleport-tap@<rev>#ci' --dev-plugins teleport
```
