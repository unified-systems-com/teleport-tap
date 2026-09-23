# teleport-tap

Teleport infrastructure access as grid vocabulary: a cluster's HA deployment, certificate authorities, roles, identities, join paths, access governance and protected resources, with a reusable `/teleport` operator page.

## What this plugin owns

- **18 node types** (`teleport__*`) across five planes (`teleport.plane`): the cluster and its FedRAMP posture columns; auth servers, proxy servers and agents; certificate authorities; roles, join tokens, access lists and access requests; users, SSO connectors, Machine ID bots and trusted devices; SSH nodes, Kubernetes clusters, databases, applications and Windows desktops.
- **26 edge types**, including the grant paths (connector → role → resource, role → requestable role, token → joining identity). Every edge that reaches another platform (compute, storage, KMS keys, the IdP, fronted targets) leaves that end open, so the plugin depends on nothing.
- **`/teleport`** — a deployment graph (layout module `static/teleport/js/projections/teleport-deployment.js`) over seven board sections: posture, roles, identity, resources, requests, machines, trust. `?cluster=<entity_id>` picks the cluster; one cluster on the grid is chosen automatically.
- A domain article for every type, edge and dimension under `tap_plugin/teleport/domain/`.

Nothing here names a deployment: a specific cluster's design nodes belong in the instance plugin that seeds it.

## Read first

`specs/spec-teleport-v0.md` — the requirements, the corpus (scope, rejected candidates, source register) and the prior-art survey.

## Stand it up

From a TAP core checkout:

```bash
scripts/spawn-session.sh <label> cli --from 'git+https://github.com/unified-systems-com/teleport-tap@<rev>#ci' --dev-plugins teleport
```
