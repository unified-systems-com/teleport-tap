/**
 * teleport deployment — one Teleport cluster as a placed picture (req-teleport-layout-deployment,
 * mounted on /teleport by req-teleport-page).
 *
 *                                                           trusted clusters
 *            ┌────────────── Teleport cluster ─────────────┐
 *  compute ← │  proxy   proxy                    host CA   │
 *  compute ← │  auth    auth                     user CA   │ → KMS / HSM keys
 *            │                                   db CA     │
 *            └─────────────────────────────────────────────┘
 *              state table   audit table   recordings bucket
 *   compute ←  agent               agent
 *              resource resource   resource
 *              target   target     target
 *
 * Everything is derived from the scene; the module names no instance. The cluster is the one the
 * page asked for by name (`?cluster=<cluster name>`, read from the panel inputs and matched exactly
 * against each cluster's label, which is its name) or, when there is exactly one, that one. The scene
 * searches already filter by the same input server-side, so with `?cluster=` the scene holds that
 * cluster, its members and the peers it trusts or is trusted by. A Teleport record stays only when its BELONGS_TO_CLUSTER edge points at that cluster
 * (fail closed, the same membership the board uses), and any outside node left with no edge to what
 * remains leaves too. With several clusters and no
 * input (or an input naming no cluster) nothing is guessed: the clusters are drawn alone, as a
 * picker whose tiles open their own page, and a warning says why.
 *
 * Containment: the cluster box holds its proxies, auth servers and certificate authorities, read
 * from the BELONGS_TO_CLUSTER edges by `projectNested` (spec-viz-nested-projection.md). Agents and
 * resources belong to the cluster too, but Teleport's own architecture draws them outside the
 * control plane, next to what they serve, and so does this picture; their membership lines are
 * hidden. Everything outside the box is placed in bands relative to the node it is attached to,
 * so the picture grows with the deployment rather than with a hand-kept map.
 *
 * A node the bands do not account for is still drawn — in a row under the picture — and reported
 * as a warning, never dropped.
 *
 * Standard tap layout module: `export async function execute(context)`
 * (spec-viz-layouts.md, req-viz-layout-module-contract).
 */

import {projectNested} from "/static/tap_viz/js/runtime/nested-projection.js";
import {applyStandardChrome, placeParentLabels, parentLabelInset} from "/static/tap_viz/js/runtime/chrome.js";

const T = {
    cluster: "teleport__teleport_cluster",
    auth: "teleport__teleport_auth_server",
    proxy: "teleport__teleport_proxy_server",
    agent: "teleport__teleport_agent",
    ca: "teleport__teleport_certificate_authority",
};
const RESOURCE_TYPES = [
    "teleport__teleport_ssh_node",
    "teleport__teleport_kube_cluster",
    "teleport__teleport_database",
    "teleport__teleport_app",
    "teleport__teleport_windows_desktop",
];
const E = {
    belongs: "BELONGS_TO_CLUSTER__teleport",
    runsOn: "RUNS_ON_COMPUTE__teleport",
    state: "STORES_CLUSTER_STATE__teleport",
    audit: "WRITES_AUDIT_EVENTS__teleport",
    recordings: "UPLOADS_SESSION_RECORDINGS__teleport",
    callsAuth: "CALLS_AUTH_API__teleport",
    tunnel: "DIALS_REVERSE_TUNNEL__teleport",
    signs: "SIGNS_WITH_KEY__teleport",
    serves: "SERVES_RESOURCE__teleport",
    fronts: "FRONTS_TARGET__teleport",
    trusts: "TRUSTS_ROOT_CLUSTER__teleport",
};
//: Storage bands, left to right under the cluster.
const STORAGE_EDGES = [E.state, E.audit, E.recordings];

const GEOM = {
    leaf: {width: 150, height: 54},
    leafLabelMaxWidth: 130,
    clusterFloor: {width: 360, height: 200},
    gapX: 44,
    gapY: 48,
    band: 90,
    side: 110,
    labelInset: 16,
};
const _clusterPadding = (labelInset) => ({top: 22 + labelInset, right: 36, bottom: 30, left: 36});

const _type = (n) => n.data("entity_type") || "";
const _etype = (e) => e.data("edge_type") || e.data("label") || "";
const _edges = (cy, type) => cy.edges().filter((e) => _etype(e) === type);
const _byLabel = (a, b) => String(a.data("label")).localeCompare(String(b.data("label")));

export async function execute(context) {
    const {cy} = context;
    const inputs = context.inputs || {};
    const warnings = [];
    const warn = (category, message) => {
        warnings.push({category, message});
        console.warn(`[teleport deployment] ${category}: ${message}`);
    };

    const cluster = _chooseCluster(cy, inputs.cluster, warn);
    if (!cluster) {
        _picker(cy);
        return {warnings};
    }
    _scope(cy, cluster);

    const chrome = applyStandardChrome(cy);
    const labelInset = parentLabelInset({...chrome, inset: GEOM.labelInset});
    const baseSizes = {};
    cy.nodes().forEach((n) => { baseSizes[_type(n)] = GEOM.leaf; });
    // The chosen cluster is a container and is re-sized around its control plane below; a peer
    // cluster (root or leaf) is a tile like any other node.
    baseSizes[T.cluster] = GEOM.leaf;
    const nested = [T.proxy, T.auth, T.ca];
    const result = await projectNested(cy, {
        relationships: nested.map((t) => ({
            name: `cluster-holds-${t}`,
            gryphon: `(parent:${T.cluster})<-[:${E.belongs}]-(child:${t})`,
        })),
        baseSizes,
        padding: 24,
        paddings: {[T.cluster]: _clusterPadding(labelInset)},
        innerLayout: {name: "flow", gap: 40, sort: "input"},
    });
    warnings.push(...(result.warnings || []));

    const placed = new Set();
    const rows = _placeControlPlane(cy, cluster, _clusterPadding(labelInset), placed);
    _placeOutside(cy, cluster, rows, placed, warn);
    placeParentLabels(cy, {
        anchor: "upper-left", inset: GEOM.labelInset,
        parentFontSize: chrome.parentFontSize, parentFontWeight: chrome.parentFontWeight,
    });
    _style(cy);
    return {warnings};
}

// ---------------------------------------------------------------------------
// Scope: one cluster
// ---------------------------------------------------------------------------

function _chooseCluster(cy, requested, warn) {
    const clusters = cy.nodes(`[entity_type = "${T.cluster}"]`).sort(_byLabel);
    // The every-cluster sentinel the scene searches default to is no choice at all.
    const name = requested === T.cluster ? "" : String(requested || "");
    if (name) {
        const hit = clusters.filter((n) => String(n.data("label")) === name);
        if (hit.length === 1) return hit[0];
        warn("teleport_cluster_not_found", `no Teleport cluster named ${JSON.stringify(name)} is in the scene`);
        return null;
    }
    if (clusters.empty()) {
        warn("teleport_no_cluster", "no Teleport cluster is in the scene");
        return null;
    }
    if (clusters.length > 1) {
        warn("teleport_many_clusters", `${clusters.length} clusters in the scene and no ?cluster= input; drawing them as a picker`);
        return null;
    }
    return clusters[0];
}

//: No cluster chosen: draw only the clusters, in a row, each one a way into its own page (the
//: panel's nav rule opens /teleport?cluster=<cluster name>). The board below says the same in words.
function _picker(cy) {
    cy.remove(cy.nodes().filter((n) => _type(n) !== T.cluster));
    const clusters = cy.nodes().sort(_byLabel);
    clusters.forEach((n) => n.style({width: GEOM.leaf.width, height: GEOM.leaf.height}));
    _rowInOrder(cy, clusters, 0, 0, new Set());
    _style(cy);
}

//: Keep the chosen cluster, its members, the clusters it trusts or is trusted by, and every outside
//: node still attached to what is kept. Everything else leaves the scene.
function _scope(cy, cluster) {
    const memberOf = {};
    _edges(cy, E.belongs).forEach((e) => { memberOf[e.source().id()] = e.target().id(); });
    const peers = new Set();
    _edges(cy, E.trusts).forEach((e) => {
        if (e.source().id() === cluster.id()) peers.add(e.target().id());
        if (e.target().id() === cluster.id()) peers.add(e.source().id());
    });
    // Fail closed, as the board does: a Teleport record is drawn only when its BELONGS_TO_CLUSTER
    // edge points at the chosen cluster. One reached only through another edge search, with no
    // membership edge, is not this cluster's (the board lists such records by name).
    const drop = cy.nodes().filter((n) => {
        if (n.id() === cluster.id() || peers.has(n.id())) return false;
        if (_type(n) === T.cluster) return true;
        if (!_type(n).startsWith("teleport__")) return false;
        return memberOf[n.id()] !== cluster.id();
    });
    cy.remove(drop);
    // Outside nodes (not Teleport types) survive only while attached to something that stayed.
    let changed = true;
    while (changed) {
        changed = false;
        cy.nodes().forEach((n) => {
            if (_type(n).startsWith("teleport__")) return;
            if (n.connectedEdges().filter((e) => !e.hasClass("tap-hidden-containment")).empty()) {
                cy.remove(n);
                changed = true;
            }
        });
    }
}

// ---------------------------------------------------------------------------
// Placement
// ---------------------------------------------------------------------------

function _childrenOf(cy, parentId) {
    return cy.nodes().filter((n) => n.data("_viewport_parent") === parentId);
}

function _moveTreeTo(cy, node, x, y) {
    const p = node.position();
    const dx = x - p.x;
    const dy = y - p.y;
    const move = (n) => {
        const q = n.position();
        n.position({x: q.x + dx, y: q.y + dy});
        _childrenOf(cy, n.id()).forEach(move);
    };
    if (dx || dy) move(node);
}

//: Lay `nodes` out in one row centred on (cx, y); returns the row's width.
function _row(cy, nodes, cx, y, placed) {
    const list = nodes.sort ? nodes.sort(_byLabel) : nodes;
    const width = list.reduce((w, n) => w + n.width(), 0) + GEOM.gapX * Math.max(0, list.length - 1);
    let x = cx - width / 2;
    list.forEach((n) => {
        _moveTreeTo(cy, n, x + n.width() / 2, y);
        x += n.width() + GEOM.gapX;
        placed.add(n.id());
    });
    return width;
}

//: Proxies on top, auth servers below them, certificate authorities in a column on the right (so
//: each CA's line to its key leaves the box without crossing another CA); the cluster box is re-sized
//: around them. Returns the y of each control-plane row.
function _placeControlPlane(cy, cluster, pad, placed) {
    placed.add(cluster.id());
    const kids = _childrenOf(cy, cluster.id());
    const proxies = kids.filter((n) => _type(n) === T.proxy);
    const auths = kids.filter((n) => _type(n) === T.auth);
    const cas = kids.filter((n) => _type(n) === T.ca).sort(_byLabel);
    const h = GEOM.leaf.height;
    const rowW = (ns) => ns.reduce((w, n) => w + n.width(), 0) + GEOM.gapX * Math.max(0, ns.length - 1);
    const colW = cas.length ? Math.max(...cas.map((n) => n.width())) : 0;
    const colH = cas.length ? cas.length * h + (cas.length - 1) * (GEOM.gapY / 2) : 0;
    const planeW = Math.max(rowW(proxies), rowW(auths));
    const nRows = (proxies.length ? 1 : 0) + (auths.length ? 1 : 0);
    const rowsH = nRows * h + Math.max(0, nRows - 1) * GEOM.gapY;
    const innerW = Math.max(planeW + (cas.length ? GEOM.gapX * 2 + colW : 0), GEOM.clusterFloor.width - pad.left - pad.right);
    const innerH = Math.max(h, rowsH, colH);
    const width = innerW + pad.left + pad.right;
    const height = innerH + pad.top + pad.bottom;
    cluster.style({width, height});
    const cp = cluster.position();
    const left = cp.x - width / 2 + pad.left;
    const top = cp.y - height / 2 + pad.top;
    const planeSpan = innerW - (cas.length ? colW + GEOM.gapX * 2 : 0);
    let y = top + (innerH - rowsH) / 2 + h / 2;
    const rows = {};
    if (proxies.length) {
        _row(cy, proxies, left + planeSpan / 2, y, placed);
        rows.proxy = y;
        y += h + GEOM.gapY;
    }
    if (auths.length) {
        _row(cy, auths, left + planeSpan / 2, y, placed);
        rows.auth = y;
    }
    let cy0 = top + (innerH - colH) / 2 + h / 2;
    cas.forEach((n) => {
        _moveTreeTo(cy, n, left + innerW - colW / 2, cy0);
        placed.add(n.id());
        cy0 += h + GEOM.gapY / 2;
    });
    rows.ca = cas.length ? top + innerH / 2 : undefined;
    return rows;
}

function _targets(cy, edgeType, sources) {
    const ids = new Set(sources.map((n) => n.id()));
    return _edges(cy, edgeType).filter((e) => ids.has(e.source().id())).targets();
}

function _placeOutside(cy, cluster, rows, placed, warn) {
    const cp = cluster.position();
    const cw = cluster.width();
    const ch = cluster.height();
    const leftEdge = cp.x - cw / 2;
    const rightEdge = cp.x + cw / 2;
    const kids = _childrenOf(cy, cluster.id());
    const proxies = kids.filter((n) => _type(n) === T.proxy);
    const auths = kids.filter((n) => _type(n) === T.auth);
    const cas = kids.filter((n) => _type(n) === T.ca);

    // Left of the box: what the proxies and auth servers run on, level with their row.
    const stackLeft = (nodes, y) => {
        const list = nodes.filter((n) => !placed.has(n.id())).sort(_byLabel);
        const total = list.reduce((s, n) => s + n.height(), 0) + GEOM.gapY / 2 * Math.max(0, list.length - 1);
        let top = y - total / 2;
        list.forEach((n) => {
            _moveTreeTo(cy, n, leftEdge - GEOM.side - n.width() / 2, top + n.height() / 2);
            top += n.height() + GEOM.gapY / 2;
            placed.add(n.id());
        });
    };
    if (rows.proxy !== undefined) stackLeft(_targets(cy, E.runsOn, proxies), rows.proxy);
    if (rows.auth !== undefined) stackLeft(_targets(cy, E.runsOn, auths), rows.auth);

    // Right of the box: the keys the CAs sign with, level with the auth row; peer clusters above them.
    let rightTop = cp.y - ch / 2 - GEOM.leaf.height - GEOM.gapY;
    const keys = _targets(cy, E.signs, cas).filter((n) => !placed.has(n.id())).sort(_byLabel);
    keys.forEach((n, i) => {
        const y = (rows.ca ?? rows.auth ?? cp.y) + (i - (keys.length - 1) / 2) * (n.height() + GEOM.gapY / 2);
        _moveTreeTo(cy, n, rightEdge + GEOM.side + n.width() / 2, y);
        placed.add(n.id());
    });
    cy.nodes(`[entity_type = "${T.cluster}"]`).filter((n) => !placed.has(n.id())).sort(_byLabel).forEach((n) => {
        _moveTreeTo(cy, n, rightEdge + GEOM.side + n.width() / 2, rightTop + n.height() / 2);
        rightTop += n.height() + GEOM.gapY / 2;
        placed.add(n.id());
    });

    // Under the box: the storage the auth servers write, in band order (state, audit, recordings).
    let y = cp.y + ch / 2 + GEOM.band;
    const storage = [];
    STORAGE_EDGES.forEach((t) => _targets(cy, t, auths).sort(_byLabel).forEach((n) => {
        if (!placed.has(n.id()) && !storage.some((s) => s.id() === n.id())) storage.push(n);
    }));
    if (storage.length) {
        _rowInOrder(cy, storage, cp.x, y, placed);
        y += GEOM.leaf.height + GEOM.band;
    }

    // Agents, each with the resources it serves under it and the targets those front under them.
    const agents = cy.nodes(`[entity_type = "${T.agent}"]`).sort(_byLabel);
    if (!agents.empty()) {
        const columns = agents.map((a) => {
            const resources = _targets(cy, E.serves, [a]).filter((n) => !placed.has(n.id())).sort(_byLabel);
            resources.forEach((r) => placed.add(r.id()));
            const fronted = _targets(cy, E.fronts, resources).filter((n) => !placed.has(n.id())).sort(_byLabel);
            fronted.forEach((f) => placed.add(f.id()));
            const w = (ns) => ns.reduce((s, n) => s + n.width(), 0) + GEOM.gapX * Math.max(0, ns.length - 1);
            return {agent: a, resources, fronted, width: Math.max(a.width(), w(resources), w(fronted))};
        });
        const total = columns.reduce((s, c) => s + c.width, 0) + GEOM.gapX * 2 * Math.max(0, columns.length - 1);
        let x = cp.x - total / 2;
        const yAgent = y;
        const yRes = yAgent + GEOM.leaf.height + GEOM.gapY * 1.5;
        const yTarget = yRes + GEOM.leaf.height + GEOM.gapY * 1.5;
        columns.forEach((c) => {
            const cx = x + c.width / 2;
            _moveTreeTo(cy, c.agent, cx, yAgent);
            placed.add(c.agent.id());
            if (c.resources.length) _rowInOrder(cy, c.resources, cx, yRes, placed);
            if (c.fronted.length) _rowInOrder(cy, c.fronted, cx, yTarget, placed);
            x += c.width + GEOM.gapX * 2;
        });
        // What the agents run on: left of the agent band.
        const agentCompute = _targets(cy, E.runsOn, agents).filter((n) => !placed.has(n.id())).sort(_byLabel);
        let ly = yAgent;
        agentCompute.forEach((n) => {
            _moveTreeTo(cy, n, cp.x - total / 2 - GEOM.side - n.width() / 2, ly);
            ly += n.height() + GEOM.gapY / 2;
            placed.add(n.id());
        });
        y = (columns.some((c) => c.fronted.length) ? yTarget : columns.some((c) => c.resources.length) ? yRes : yAgent)
            + GEOM.leaf.height + GEOM.band;
    }

    // Resources no agent serves (agentless OpenSSH, or not yet wired), with their targets.
    const loose = cy.nodes().filter((n) => RESOURCE_TYPES.includes(_type(n)) && !placed.has(n.id())).sort(_byLabel);
    if (!loose.empty()) {
        _rowInOrder(cy, loose.toArray(), cp.x, y, placed);
        const fronted = _targets(cy, E.fronts, loose).filter((n) => !placed.has(n.id())).sort(_byLabel);
        y += GEOM.leaf.height + GEOM.gapY * 1.5;
        if (!fronted.empty()) {
            _rowInOrder(cy, fronted.toArray(), cp.x, y, placed);
            y += GEOM.leaf.height;
        }
        y += GEOM.band;
    }

    // Anything else: one row under the picture, never dropped.
    const rest = cy.nodes().filter((n) => !placed.has(n.id()) && !n.data("_viewport_parent") && !n.data("_is_badge")).sort(_byLabel);
    rest.forEach((n) => warn("teleport_unplaced", `${n.data("label")} (${_type(n)}) has no band in the deployment picture; drawn under it`));
    if (!rest.empty()) _rowInOrder(cy, rest.toArray(), cp.x, y, placed);
}

function _rowInOrder(cy, list, cx, y, placed) {
    const width = list.reduce((w, n) => w + n.width(), 0) + GEOM.gapX * Math.max(0, list.length - 1);
    let x = cx - width / 2;
    list.forEach((n) => {
        _moveTreeTo(cy, n, x + n.width() / 2, y);
        x += n.width() + GEOM.gapX;
        placed.add(n.id());
    });
}

// ---------------------------------------------------------------------------
// Style
// ---------------------------------------------------------------------------

function _style(cy) {
    cy.style()
        .selector(`node[entity_type != "${T.cluster}"]`)
        .style({
            "text-valign": "center",
            "text-halign": "center",
            "text-margin-y": 0,
            "text-wrap": "ellipsis",
            "text-max-width": `${GEOM.leafLabelMaxWidth}px`,
        })
        .selector(`node[entity_type = "${T.cluster}"].tap-viewport-parent`)
        .style({
            "shape": "round-rectangle",
            "background-color": "#f5f3ff",
            "background-opacity": 1,
            "border-width": 2,
            "border-color": "#512FC9",
            "color": "#2B1A6E",
        })
        // Membership is drawn as containment (control plane) or implied by the band (agents,
        // resources); its lines would only restate that.
        .selector(`edge[label = "${E.belongs}"]`)
        .style({"display": "none"})
        .selector(STORAGE_EDGES.map((t) => `edge[label = "${t}"]`).join(", "))
        .style({"line-style": "dashed", "line-color": "#7C5CE0", "target-arrow-color": "#7C5CE0"})
        .selector(`edge[label = "${E.signs}"]`)
        .style({"line-style": "dotted", "line-color": "#512FC9", "target-arrow-color": "#512FC9"})
        .selector(`edge[label = "${E.trusts}"]`)
        .style({"line-color": "#b45309", "target-arrow-color": "#b45309", "width": 2})
        .update();
}
