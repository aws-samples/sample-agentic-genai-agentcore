#!/usr/bin/env node
/**
 * Convert diagram-spec.json + aws-drawio-styles.json → aws-architecture.drawio
 *
 * Usage: node convert.js <spec.json> <styles.json> [output.drawio]
 *
 * Zero external dependencies — uses only built-in Node.js modules.
 */

const fs = require('fs');
const path = require('path');

function loadSpec(filePath) {
    const content = fs.readFileSync(filePath, 'utf-8');
    return JSON.parse(content);
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function escapeXml(str) {
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

function makeLabel(label, subtitle) {
    if (subtitle) {
        return `${escapeXml(label)}&lt;br/&gt;&lt;font style=&quot;font-size:10px;font-weight:normal&quot;&gt;${escapeXml(subtitle)}&lt;/font&gt;`;
    }
    return escapeXml(label);
}

// ── Icon style builder ──────────────────────────────────────────────────────

function matchIcon(serviceType, icons) {
    if (icons[serviceType]) return icons[serviceType];
    for (const [, icon] of Object.entries(icons)) {
        const kws = icon.keywords || icon.kw || [];
        for (const kw of kws) {
            if (kw.toLowerCase() === serviceType.toLowerCase()) return icon;
        }
    }
    return null;
}

function buildIconStyle(serviceType, styles) {
    const icon = matchIcon(serviceType, styles.icons || {});
    if (!icon) return styles.genericStyles?.default || 'rounded=1;fillColor=#f5f5f5;strokeColor=#666666;';
    const cat = icon.category || icon.cat;
    const colors = (styles.categoryColors || {})[cat] || styles.categoryColors?.general;
    const resIcon = icon.resIcon || icon.icon;
    const template = styles.iconStyleTemplate;
    return template
        .replace('${fill}', colors.fill)
        .replace('${gradient}', colors.gradient)
        .replace('${font}', colors.font)
        .replace('${resIcon}', resIcon);
}

// ── Layout calculator ───────────────────────────────────────────────────────

const MIN_CLUSTER_H = 50 + 78 + 60 + 30; // 218px

function calculateClusterDims(cluster, ICON_W, ICON_H, H_SPACE, V_SPACE, CLUST_PAD_TOP, CLUST_PAD_SIDE) {
    const n = (cluster.services || []).length;
    const isGrouped = cluster.grouped !== false;
    const flow = cluster.flow || 'horizontal';
    let cols, rows;
    if (flow === 'vertical') {
        cols = Math.min(n, 2);
        rows = Math.ceil(n / 2);
    } else {
        cols = Math.min(n, 4);
        rows = Math.ceil(n / cols);
    }

    // Ungrouped clusters: no padding for container box, just icon space
    const padTop = isGrouped ? CLUST_PAD_TOP : 10;
    const padSide = isGrouped ? CLUST_PAD_SIDE : 10;

    const w = cols * (ICON_W + H_SPACE) - H_SPACE + padSide * 2;
    const rawH = rows * (ICON_H + V_SPACE) - V_SPACE + padTop + padSide;
    const h = isGrouped ? Math.max(rawH, MIN_CLUSTER_H) : rawH;
    return { w, h, cols, rows, flow, padTop, padSide };
}

function calculateLayout(spec) {
    const clusters = spec.clusters || [];
    const shared = spec.shared || [];
    const sidebar = spec.sidebar || [];
    const layoutGrid = spec.layout?.clusters || null;

    const ICON_W = 78, ICON_H = 78;
    const H_SPACE = 80, V_SPACE = 60;
    const CLUST_PAD_TOP = 50, CLUST_PAD_SIDE = 30;
    const CLUSTER_GAP = 80;
    const CLOUD_PAD_TOP = 60, CLOUD_PAD_SIDE = 60;

    const clusterMap = {};
    for (const c of clusters) {
        clusterMap[c.id] = {
            ...c,
            dims: calculateClusterDims(c, ICON_W, ICON_H, H_SPACE, V_SPACE, CLUST_PAD_TOP, CLUST_PAD_SIDE)
        };
    }

    let gridRows;
    if (layoutGrid && layoutGrid.length > 0) {
        gridRows = layoutGrid;
    } else {
        gridRows = [];
        for (let i = 0; i < clusters.length; i += 3) {
            gridRows.push(clusters.slice(i, i + 3).map(c => c.id));
        }
    }

    const rowWidths = [];
    const rowHeights = [];
    for (const row of gridRows) {
        const dims = row.map(id => clusterMap[id]?.dims || { w: 200, h: 150 });
        rowWidths.push(dims.reduce((s, d) => s + d.w, 0) + CLUSTER_GAP * (dims.length - 1));
        rowHeights.push(Math.max(...dims.map(d => d.h)));
    }

    const sharedW = shared.length ? shared.length * (ICON_W + H_SPACE) - H_SPACE : 0;
    const sharedH = shared.length ? ICON_H + 30 : 0;
    const sidebarW = sidebar.length ? ICON_W + CLUST_PAD_SIDE * 2 : 0;

    const staggerPad = gridRows.length > 1 ? Math.round(CLUSTER_GAP / 2 + 60) : 0;
    const contentW = Math.max(...rowWidths, sharedW, 400) + staggerPad;
    const totalClusterH = rowHeights.reduce((s, h) => s + h, 0) + CLUSTER_GAP * (rowHeights.length - 1);
    const contentH = totalClusterH + (sharedH ? sharedH + CLUSTER_GAP : 0);

    const cloudW = contentW + CLOUD_PAD_SIDE * 2 + (sidebarW ? sidebarW + CLUSTER_GAP : 0);
    const cloudH = contentH + CLOUD_PAD_TOP + CLOUD_PAD_SIDE;
    const cloudX = 120, cloudY = 20;

    const pageW = Math.max(1600, cloudX + cloudW + 100);
    const pageH = Math.max(1200, cloudY + cloudH + 200);

    return {
        ICON_W, ICON_H, H_SPACE, V_SPACE,
        CLUST_PAD_TOP, CLUST_PAD_SIDE,
        CLUSTER_GAP, CLOUD_PAD_TOP, CLOUD_PAD_SIDE,
        clusterMap, gridRows, rowWidths, rowHeights,
        sharedW, sharedH, sidebarW,
        contentW, totalClusterH, contentH,
        cloudW, cloudH, cloudX, cloudY,
        pageW, pageH
    };
}

// ── Connection routing ──────────────────────────────────────────────────────

function buildConnectionRouting(connections, positions) {
    const outCount = {}, inCount = {}, outIndex = {}, inIndex = {};

    for (const conn of connections) {
        outCount[conn.from] = (outCount[conn.from] || 0) + 1;
        inCount[conn.to] = (inCount[conn.to] || 0) + 1;
    }

    function spreadPoint(index, total) {
        if (total <= 1) return 0.5;
        return 0.2 + (0.6 * index) / (total - 1);
    }

    // Determine best exit/entry edge based on relative position of source and target
    function bestEdge(fromPos, toPos) {
        if (!fromPos || !toPos) return { exitEdge: 'bottom', entryEdge: 'top' };
        const dx = toPos.x - fromPos.x;
        const dy = toPos.y - fromPos.y;
        const absDx = Math.abs(dx);
        const absDy = Math.abs(dy);

        // If target is primarily below source
        if (dy > 0 && absDy >= absDx) return { exitEdge: 'bottom', entryEdge: 'top' };
        // If target is primarily above source
        if (dy < 0 && absDy >= absDx) return { exitEdge: 'top', entryEdge: 'bottom' };
        // If target is primarily to the right
        if (dx > 0 && absDx > absDy) return { exitEdge: 'right', entryEdge: 'left' };
        // If target is primarily to the left
        if (dx < 0 && absDx > absDy) return { exitEdge: 'left', entryEdge: 'right' };
        return { exitEdge: 'bottom', entryEdge: 'top' };
    }

    function edgeSuffix(type, edge, spread) {
        const prefix = type === 'exit' ? 'exit' : 'entry';
        switch (edge) {
            case 'top':    return `${prefix}X=${spread.toFixed(2)};${prefix}Y=0;${prefix}Dx=0;${prefix}Dy=0;`;
            case 'bottom': return `${prefix}X=${spread.toFixed(2)};${prefix}Y=1;${prefix}Dx=0;${prefix}Dy=0;`;
            case 'left':   return `${prefix}X=0;${prefix}Y=${spread.toFixed(2)};${prefix}Dx=0;${prefix}Dy=0;`;
            case 'right':  return `${prefix}X=1;${prefix}Y=${spread.toFixed(2)};${prefix}Dx=0;${prefix}Dy=0;`;
            default:       return `${prefix}X=${spread.toFixed(2)};${prefix}Y=1;${prefix}Dx=0;${prefix}Dy=0;`;
        }
    }

    const routing = [];
    for (const conn of connections) {
        if (!outIndex[conn.from]) outIndex[conn.from] = 0;
        if (!inIndex[conn.to]) inIndex[conn.to] = 0;

        const oTotal = outCount[conn.from];
        const iTotal = inCount[conn.to];
        const oIdx = outIndex[conn.from]++;
        const iIdx = inIndex[conn.to]++;

        const fromPos = positions[conn.from];
        const toPos = positions[conn.to];
        const { exitEdge, entryEdge } = bestEdge(fromPos, toPos);

        let exitSuffix = '';
        let entrySuffix = '';

        if (oTotal > 1) {
            const spread = spreadPoint(oIdx, oTotal);
            exitSuffix = edgeSuffix('exit', exitEdge, spread);
        }
        if (iTotal > 1) {
            const spread = spreadPoint(iIdx, iTotal);
            entrySuffix = edgeSuffix('entry', entryEdge, spread);
        }

        routing.push({ ...conn, exitSuffix, entrySuffix });
    }

    return routing;
}

// ── XML builder ─────────────────────────────────────────────────────────────

function buildDiagram(spec, styles) {
    const L = calculateLayout(spec);
    const cells = [];
    const positions = {};

    function cell(id, value, style, parent, x, y, w, h, rawValue) {
        cells.push({ id, value: rawValue ? value : escapeXml(value), style, parent, x, y, w, h, edge: false });
    }
    function edge(id, value, style, parent, source, target) {
        cells.push({ id, value: escapeXml(value || ''), style, parent, source, target, edge: true });
    }

    // AWS Cloud
    const cloudStyle = styles.groupStyles?.awsCloud?.style
        || 'rounded=1;fillColor=none;strokeColor=#232F3E;container=1;collapsible=0;';
    cell('aws-cloud', 'AWS Cloud', cloudStyle, '1', L.cloudX, L.cloudY, L.cloudW, L.cloudH);

    // Cluster style (for grouped clusters only)
    const clusterStyle = styles.layoutGuidelines?.clusterVisualStyle?.style
        || 'rounded=1;fillColor=#F5F5F5;strokeColor=#CCCCCC;dashed=1;container=1;collapsible=0;recursiveResize=1;verticalAlign=top;fontSize=11;fontColor=#666666;';

    // Render clusters
    let cy = L.CLOUD_PAD_TOP;
    for (let ri = 0; ri < L.gridRows.length; ri++) {
        const rowIds = L.gridRows[ri];
        const rowH = L.rowHeights[ri];
        const rowW = rowIds.reduce((s, id) => s + (L.clusterMap[id]?.dims.w || 200), 0) + L.CLUSTER_GAP * (rowIds.length - 1);
        // Stagger odd rows: offset by half a cluster gap + average cluster width / 2
        const staggerOffset = (ri % 2 === 1) ? Math.round(L.CLUSTER_GAP / 2 + 60) : 0;
        let cx = L.CLOUD_PAD_SIDE + (L.contentW - rowW) / 2 + staggerOffset;

        for (const clusterId of rowIds) {
            const cluster = L.clusterMap[clusterId];
            if (!cluster) continue;
            const { w: cw, h: ch, cols, padTop, padSide } = cluster.dims;
            const isGrouped = cluster.grouped !== false;
            const clusterY = cy + (rowH - ch) / 2;

            if (isGrouped) {
                // Grouped: draw container box, services are children
                cell(cluster.id, cluster.label, clusterStyle, 'aws-cloud', cx, clusterY, cw, ch);

                const services = cluster.services || [];
                for (let si = 0; si < services.length; si++) {
                    const svc = services[si];
                    const col = si % cols;
                    const row = Math.floor(si / cols);
                    const sx = padSide + col * (L.ICON_W + L.H_SPACE);
                    const sy = padTop + row * (L.ICON_H + L.V_SPACE);
                    const style = buildIconStyle(svc.type, styles);
                    const label = makeLabel(svc.label, svc.subtitle);
                    cell(svc.id, label, style, cluster.id, sx, sy, L.ICON_W, L.ICON_H, true);
                    positions[svc.id] = {
                        x: L.cloudX + cx + sx + L.ICON_W / 2,
                        y: L.cloudY + clusterY + sy + L.ICON_H / 2
                    };
                }
            } else {
                // Ungrouped: no container box, services float directly in aws-cloud
                const services = cluster.services || [];
                for (let si = 0; si < services.length; si++) {
                    const svc = services[si];
                    const col = si % cols;
                    const row = Math.floor(si / cols);
                    const sx = cx + padSide + col * (L.ICON_W + L.H_SPACE);
                    const sy = clusterY + padTop + row * (L.ICON_H + L.V_SPACE);
                    const style = buildIconStyle(svc.type, styles);
                    const label = makeLabel(svc.label, svc.subtitle);
                    cell(svc.id, label, style, 'aws-cloud', sx, sy, L.ICON_W, L.ICON_H, true);
                    positions[svc.id] = {
                        x: L.cloudX + sx + L.ICON_W / 2,
                        y: L.cloudY + sy + L.ICON_H / 2
                    };
                }
            }
            cx += cw + L.CLUSTER_GAP;
        }
        cy += rowH + L.CLUSTER_GAP;
    }

    // Shared services
    const shared = spec.shared || [];
    if (shared.length) {
        const startX = L.CLOUD_PAD_SIDE + (L.contentW - L.sharedW) / 2;
        for (let si = 0; si < shared.length; si++) {
            const svc = shared[si];
            const sx = startX + si * (L.ICON_W + L.H_SPACE);
            const style = buildIconStyle(svc.type, styles);
            const label = makeLabel(svc.label, svc.subtitle);
            cell(svc.id, label, style, 'aws-cloud', sx, cy, L.ICON_W, L.ICON_H, true);
            positions[svc.id] = { x: L.cloudX + sx + L.ICON_W / 2, y: L.cloudY + cy + L.ICON_H / 2 };
        }
    }

    // Sidebar
    const sidebar = spec.sidebar || [];
    if (sidebar.length) {
        const sbX = L.cloudW - (L.ICON_W + L.CLUST_PAD_SIDE * 2) - L.CLOUD_PAD_SIDE;
        for (let si = 0; si < sidebar.length; si++) {
            const svc = sidebar[si];
            const sy = L.CLOUD_PAD_TOP + si * (L.ICON_H + L.V_SPACE);
            const style = buildIconStyle(svc.type, styles);
            const label = makeLabel(svc.label, svc.subtitle);
            cell(svc.id, label, style, 'aws-cloud', sbX, sy, L.ICON_W, L.ICON_H, true);
            positions[svc.id] = { x: L.cloudX + sbX + L.ICON_W / 2, y: L.cloudY + sy + L.ICON_H / 2 };
        }
    }

    // External actors — position near the services they connect to
    const external = spec.external || [];
    const connections = spec.connections || [];
    for (let ei = 0; ei < external.length; ei++) {
        const ext = external[ei];

        // Find the first service this external actor connects to, and position nearby
        let targetX = null;
        for (const conn of connections) {
            if (conn.from === ext.id && positions[conn.to]) {
                targetX = positions[conn.to].x;
                break;
            }
        }

        const ex = targetX !== null ? targetX - L.ICON_W / 2 - L.cloudX : 20 + ei * (L.ICON_W + L.H_SPACE);
        const ey = L.cloudY + L.cloudH + 40;
        const extDef = styles.externalActors?.[ext.type];
        const style = extDef?.style || 'rounded=1;fillColor=#f5f5f5;strokeColor=#666666;';
        cell(ext.id, ext.label, style, '1', ex, ey, L.ICON_W, L.ICON_H);
        positions[ext.id] = { x: ex + L.ICON_W / 2, y: ey + L.ICON_H / 2 };
    }

    // Build flow number lookup: (from,to) → flow number
    const flowMap = {};
    for (const flow of (spec.flows || [])) {
        if (flow.from && flow.to) {
            flowMap[`${flow.from}-${flow.to}`] = flow.number;
        }
    }

    // Connections — attach flow numbers as edge labels
    const connStyles = styles.connectionStyles || {};
    const defaultConn = 'edgeStyle=orthogonalEdgeStyle;rounded=0;curved=0;strokeColor=#232F3E;strokeWidth=2;endArrow=classic;endFill=1;jumpStyle=arc;jumpSize=10;';
    const routedConns = buildConnectionRouting(spec.connections || [], positions);
    for (const conn of routedConns) {
        let cStyle = connStyles[conn.style]?.style || defaultConn;
        if (conn.exitSuffix) cStyle += conn.exitSuffix;
        if (conn.entrySuffix) cStyle += conn.entrySuffix;
        // Check if this connection has a flow number
        const flowNum = flowMap[`${conn.from}-${conn.to}`];
        const label = flowNum != null ? String(flowNum) : (conn.label || '');
        // Add flow number styling to edge if it has a flow number
        if (flowNum != null) {
            cStyle += 'fontSize=18;fontStyle=1;fontColor=#FFFFFF;labelBackgroundColor=#232F3E;spacingTop=-2;spacingBottom=-2;spacingLeft=8;spacingRight=8;';
        }
        edge(`conn-${conn.from}-${conn.to}`, label, cStyle, '1', conn.from, conn.to);
    }

    // Flow indicators for flows that don't match any connection (fallback)
    const flowStyle = styles.flowIndicator?.style
        || 'ellipse;fillColor=#232F3E;strokeColor=#232F3E;fontColor=#FFFFFF;fontSize=18;fontStyle=1;';
    for (const flow of (spec.flows || [])) {
        const key = `${flow.from}-${flow.to}`;
        // Skip if already attached to a connection
        if (flowMap[key] != null) {
            const matchingConn = routedConns.find(c => c.from === flow.from && c.to === flow.to);
            if (matchingConn) continue;
        }
        // Fallback: render as standalone circle
        let fx, fy;
        if (flow.from && flow.to && positions[flow.from] && positions[flow.to]) {
            const fromPos = positions[flow.from];
            const toPos = positions[flow.to];
            fx = (fromPos.x + toPos.x) / 2 - 35;
            fy = (fromPos.y + toPos.y) / 2 - 15;
        } else if (flow.near && positions[flow.near]) {
            const pos = positions[flow.near];
            fx = pos.x - 45;
            fy = pos.y - 15;
        } else {
            fx = 100;
            fy = 100;
        }
        cell(`flow-${flow.number}`, String(flow.number), flowStyle, '1', fx, fy, 30, 30);
    }

    return { cells, pageW: L.pageW, pageH: L.pageH };
}

// ── XML serializer ──────────────────────────────────────────────────────────

function toXml(cells, pageW, pageH) {
    const lines = [
        '<mxfile host="app.diagrams.net" agent="APEX Design Agent" version="21.1.0">',
        '  <diagram name="AWS Architecture" id="aws-arch">',
        `    <mxGraphModel dx="1434" dy="780" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="${pageW}" pageHeight="${pageH}" math="0" shadow="0">`,
        '      <root>',
        '        <mxCell id="0"/>',
        '        <mxCell id="1" parent="0"/>',
    ];

    for (const c of cells) {
        if (c.edge) {
            const labelAttr = c.value ? ` value="${escapeXml(c.value)}"` : '';
            lines.push(`        <mxCell id="${c.id}"${labelAttr} style="${c.style}" edge="1" parent="${c.parent}" source="${c.source}" target="${c.target}">`);
            lines.push('          <mxGeometry relative="1" as="geometry"/>');
            lines.push('        </mxCell>');
        } else {
            lines.push(`        <mxCell id="${c.id}" value="${c.value}" style="${c.style}" vertex="1" parent="${c.parent}">`);
            lines.push(`          <mxGeometry x="${c.x}" y="${c.y}" width="${c.w}" height="${c.h}" as="geometry"/>`);
            lines.push('        </mxCell>');
        }
    }

    lines.push('      </root>');
    lines.push('    </mxGraphModel>');
    lines.push('  </diagram>');
    lines.push('</mxfile>');
    return lines.join('\n');
}

// ── Validation ──────────────────────────────────────────────────────────────

function validateSpec(spec) {
    const warnings = [];

    const serviceIds = new Set();
    for (const cluster of (spec.clusters || [])) {
        for (const svc of (cluster.services || [])) {
            serviceIds.add(svc.id);
        }
    }
    for (const svc of (spec.shared || [])) serviceIds.add(svc.id);
    for (const svc of (spec.sidebar || [])) serviceIds.add(svc.id);
    for (const ext of (spec.external || [])) serviceIds.add(ext.id);

    const connectedIds = new Set();
    for (const conn of (spec.connections || [])) {
        connectedIds.add(conn.from);
        connectedIds.add(conn.to);
        if (!serviceIds.has(conn.from)) {
            warnings.push(`Connection source "${conn.from}" not found in services`);
        }
        if (!serviceIds.has(conn.to)) {
            warnings.push(`Connection target "${conn.to}" not found in services`);
        }
    }

    // Orphan check — skip sidebar and services inside grouped clusters
    const sidebarIds = new Set((spec.sidebar || []).map(s => s.id));
    const groupedClusterServiceIds = new Set();
    for (const cluster of (spec.clusters || [])) {
        if (cluster.grouped !== false) {
            for (const svc of (cluster.services || [])) {
                groupedClusterServiceIds.add(svc.id);
            }
        }
    }
    for (const id of serviceIds) {
        if (!connectedIds.has(id) && !sidebarIds.has(id) && !groupedClusterServiceIds.has(id)) {
            warnings.push(`Service "${id}" has no connections (orphan)`);
        }
    }

    // Flow indicators
    for (const flow of (spec.flows || [])) {
        if (flow.from && !serviceIds.has(flow.from)) {
            warnings.push(`Flow ${flow.number} references unknown "from": "${flow.from}"`);
        }
        if (flow.to && !serviceIds.has(flow.to)) {
            warnings.push(`Flow ${flow.number} references unknown "to": "${flow.to}"`);
        }
        if (!flow.from && !flow.to && !flow.near) {
            warnings.push(`Flow ${flow.number} has no positioning`);
        }
    }

    return warnings;
}

// ── Main ────────────────────────────────────────────────────────────────────

function main() {
    const args = process.argv.slice(2);
    if (args.length < 2) {
        console.error('Usage: node convert.js <spec.json> <styles.json> [output.drawio]');
        process.exit(1);
    }

    const specPath = args[0];
    const stylesPath = args[1];
    const outputPath = args[2] || 'aws-architecture.drawio';

    const spec = loadSpec(specPath);
    const styles = JSON.parse(fs.readFileSync(stylesPath, 'utf-8'));

    const warnings = validateSpec(spec);
    if (warnings.length > 0) {
        console.warn(`\n⚠️  Spec validation warnings (${warnings.length}):`);
        for (const w of warnings) console.warn(`  - ${w}`);
        console.warn('');
    }

    const { cells, pageW, pageH } = buildDiagram(spec, styles);
    const xml = toXml(cells, pageW, pageH);

    try {
        if (!xml.includes('</mxfile>')) throw new Error('Missing closing mxfile tag');
    } catch (e) {
        console.error('XML validation failed:', e.message);
        process.exit(1);
    }

    const outDir = path.dirname(outputPath);
    if (outDir && !fs.existsSync(outDir)) {
        fs.mkdirSync(outDir, { recursive: true });
    }
    fs.writeFileSync(outputPath, xml);

    const nServices = (spec.clusters || []).reduce((s, c) => s + (c.services || []).length, 0)
        + (spec.shared || []).length + (spec.sidebar || []).length;
    const nGrouped = (spec.clusters || []).filter(c => c.grouped !== false).length;
    const nUngrouped = (spec.clusters || []).filter(c => c.grouped === false).length;
    const nConnections = (spec.connections || []).length;
    const nFlows = (spec.flows || []).length;
    console.log(`Generated: ${outputPath}`);
    console.log(`  ${nServices} services, ${nGrouped} grouped clusters, ${nUngrouped} ungrouped zones, ${nConnections} connections, ${nFlows} flow indicators`);
    if (warnings.length === 0) {
        console.log('  ✅ No validation warnings');
    }
}

main();
