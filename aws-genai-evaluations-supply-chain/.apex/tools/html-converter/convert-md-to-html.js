#!/usr/bin/env node
/**
 * Markdown to HTML converter for design documentation.
 * Produces a professional documentation site with persona-based navigation tabs,
 * ordered document tree, dark mode, and mermaid diagram support.
 *
 * Run with: node convert-md-to-html.js
 */

const fs = require('fs');
const path = require('path');

// ---------------------------------------------------------------------------
// Template & asset paths (resolved relative to this script)
// ---------------------------------------------------------------------------
const SCRIPT_DIR = __dirname;
const REPORT_DIR = path.join(SCRIPT_DIR, 'html-report');

function loadTemplate(name) {
    return fs.readFileSync(path.join(REPORT_DIR, name), 'utf-8');
}

// ---------------------------------------------------------------------------
// Section ordering for the All Docs tree
// ---------------------------------------------------------------------------
const SECTION_ORDER = [
    { key: 'overview', label: 'Overview', files: ['README'] },
    {
        key: 'project-management', label: 'Project Management',
        files: ['executive-summary', 'user-stories', 'project-risk-analysis']
    },
    {
        key: 'requirements', label: 'Requirements',
        files: ['functional-requirements', 'non-functional-requirements']
    },
    {
        key: 'architecture', label: 'Architecture',
        files: ['system-architecture', 'data-architecture', 'api-specifications'],
        subfolders: [
            { key: 'architecture-decision-records', label: 'Decision Records', collapsed: true }
        ]
    },
    {
        key: 'security', label: 'Security',
        files: ['threat-analysis', 'security-controls', 'testing-framework', 'implementation-guidance']
    },
    {
        key: 'fpm-artifacts', label: 'Fixed Price Package',
        files: [
            'milestone-deliverable-plan-details',
            'resource-analysis',
            'resource-plan',
            'loe-calibration',
            'level-of-effort',
            'risk-assessment',
            'engagement-blueprint',
            'consistency-verification'
        ]
    },
    { key: 'appendices', label: 'Appendices', collapsed: true, catchAll: true }
];

// Files to exclude from output entirely
const EXCLUDED_FILES = ['AGENTS.md'];

// ---------------------------------------------------------------------------
// Markdown helpers
// ---------------------------------------------------------------------------

function escapeHtml(text) {
    return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function escapeMermaid(text) {
    // Mermaid reads textContent from the DOM, so we must HTML-escape angle brackets
    // to prevent the browser from interpreting <br/> as HTML elements.
    // Additionally, parentheses inside square-bracket node labels like ID[label (text)]
    // are misinterpreted as mermaid shape syntax. Wrapping such labels in quotes fixes this.
    // We must NOT touch shape syntax like [( )], [{ }], [[ ]], etc.
    return text.split('\n').map(line => {
        return line.replace(/\[([^\]]*)\]/g, (match, inner) => {
            // Skip shape syntax: [(...)], [[...]], [{...}]
            if (/^\(.*\)$/.test(inner) || /^\[.*\]$/.test(inner) || /^\{.*\}$/.test(inner)) {
                return match;
            }
            // Already quoted — leave alone
            if (inner.startsWith('"') && inner.endsWith('"')) return match;
            // Contains parens that would confuse mermaid — quote the label
            if (inner.includes('(')) return '["' + inner + '"]';
            return match;
        });
    }).join('\n').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function processInline(text) {
    // Escape HTML to prevent XSS, then apply markdown formatting
    text = escapeHtml(text);
    text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
    text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    text = text.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    // Markdown links: external URLs open in new tab; relative .md links rewritten to .html
    text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, function(match, label, url) {
        if (/^https?:\/\//.test(url)) {
            return '<a href="' + url + '" target="_blank" rel="noopener">' + label + '</a>';
        }
        // Rewrite relative .md links (with optional #anchor) to .html
        const rewrittenUrl = url.replace(/\.md(#[^)]*)?$/, function(m, hash) {
            return '.html' + (hash || '');
        });
        return '<a href="' + rewrittenUrl + '">' + label + '</a>';
    });
    // Auto-link bare URLs not already inside an href attribute
    text = text.replace(/(^|[^"=])(https?:\/\/[^\s<]+)/g, function(match, prefix, url) {
        return prefix + '<a href="' + url + '" target="_blank" rel="noopener">' + url + '</a>';
    });
    return text;
}

function slugify(text) {
    return text.toLowerCase()
        .replace(/<[^>]+>/g, '')       // strip HTML tags from processInline output
        .replace(/[^\w\s-]/g, '')      // remove non-word chars
        .replace(/\s+/g, '-')          // spaces to hyphens
        .replace(/-+/g, '-')           // collapse multiple hyphens
        .replace(/^-|-$/g, '');        // trim leading/trailing hyphens
}

function preprocessLines(lines) {
    const result = [];
    let i = 0;
    let foundH1 = false;
    let inMetadataBlock = false;

    while (i < lines.length) {
        const line = lines[i];

        // Detect h1 — start watching for metadata block
        if (!foundH1 && /^#\s+/.test(line)) {
            foundH1 = true;
            result.push(line);
            i++;
            continue;
        }

        // After h1, skip bold key-value metadata lines (e.g. **Project**: ...)
        // and blank lines between them, until the first --- separator
        if (foundH1 && !inMetadataBlock && result.length > 0) {
            if (/^\*\*[^*]+\*\*\s*:/.test(line.trim()) || line.trim() === '') {
                inMetadataBlock = true;
                i++;
                continue;
            }
        }
        if (inMetadataBlock) {
            if (/^\*\*[^*]+\*\*\s*:/.test(line.trim()) || line.trim() === '') {
                i++;
                continue;
            }
            if (/^[-*_]{3,}\s*$/.test(line)) {
                // Skip the --- separator that ends the metadata block
                inMetadataBlock = false;
                i++;
                continue;
            }
            // Non-metadata line — stop skipping
            inMetadataBlock = false;
        }

        // Strip "## Table of Contents" section (from heading to next ---)
        if (/^##\s+Table of Contents\s*$/i.test(line)) {
            i++;
            while (i < lines.length && !/^[-*_]{3,}\s*$/.test(lines[i])) {
                i++;
            }
            if (i < lines.length) i++; // skip the --- too
            continue;
        }

        result.push(line);
        i++;
    }
    return result;
}

function convertMarkdownToHtml(mdContent) {
    const rawLines = mdContent.split('\n');
    const lines = preprocessLines(rawLines);
    const htmlLines = [];
    const headings = [];
    const usedIds = {};  // track ID occurrences to guarantee uniqueness
    let inCodeBlock = false;
    let codeLang = '';
    let codeContent = [];
    let inTable = false;
    let tableRows = [];

    function flushTable() {
        if (inTable && tableRows.length > 0) {
            htmlLines.push('<table><thead><tr>');
            for (const cell of tableRows[0]) {
                htmlLines.push(`<th>${processInline(cell)}</th>`);
            }
            htmlLines.push('</tr></thead><tbody>');
            for (let i = 2; i < tableRows.length; i++) {
                htmlLines.push('<tr>');
                for (const cell of tableRows[i]) {
                    htmlLines.push(`<td>${processInline(cell)}</td>`);
                }
                htmlLines.push('</tr>');
            }
            htmlLines.push('</tbody></table>');
        }
        inTable = false;
        tableRows = [];
    }

    for (const line of lines) {
        if (line.startsWith('```')) {
            if (inCodeBlock) {
                const content = codeContent.join('\n');
                if (codeLang === 'mermaid') {
                    htmlLines.push(`<pre class="mermaid">${escapeMermaid(content)}</pre>`);
                } else {
                    htmlLines.push(`<pre><code>${escapeHtml(content)}</code></pre>`);
                }
                inCodeBlock = false;
                codeContent = [];
            } else {
                flushTable();
                inCodeBlock = true;
                codeLang = line.slice(3).trim();
            }
            continue;
        }
        if (inCodeBlock) {
            codeContent.push(line);
            continue;
        }
        if (line.includes('|') && line.trim().startsWith('|')) {
            inTable = true;
            const cells = line.trim().replace(/^\||\|$/g, '').split('|').map(c => c.trim());
            tableRows.push(cells);
            continue;
        } else if (inTable) {
            flushTable();
        }

        const headerMatch = line.match(/^(#{1,6})\s+(.+)$/);
        if (headerMatch) {
            flushTable();
            const level = headerMatch[1].length;
            const inlineHtml = processInline(headerMatch[2]);
            let id = slugify(headerMatch[2]);
            // Ensure unique IDs when duplicate heading text exists
            if (usedIds[id]) {
                usedIds[id]++;
                id = id + '-' + usedIds[id];
            } else {
                usedIds[id] = 1;
            }
            htmlLines.push(`<h${level} id="${id}">${inlineHtml}</h${level}>`);
            if (level >= 2 && level <= 3) {
                headings.push({ level, text: headerMatch[2], id });
            }
            continue;
        }
        if (/^[-*_]{3,}\s*$/.test(line)) {
            flushTable();
            htmlLines.push('<hr>');
            continue;
        }
        if (line.startsWith('>')) {
            htmlLines.push(`<blockquote><p>${processInline(line.slice(1).trim())}</p></blockquote>`);
            continue;
        }
        const listMatch = line.match(/^(\s*)[-*+]\s+(.+)$/);
        if (listMatch) {
            htmlLines.push(`<li>${processInline(listMatch[2])}</li>`);
            continue;
        }
        const orderedMatch = line.match(/^(\s*)\d+\.\s+(.+)$/);
        if (orderedMatch) {
            htmlLines.push(`<li>${processInline(orderedMatch[2])}</li>`);
            continue;
        }
        if (line.trim() === '') {
            continue;
        }
        htmlLines.push(`<p>${processInline(line)}</p>`);
    }
    flushTable();
    return { html: htmlLines.join('\n'), headings };
}

// ---------------------------------------------------------------------------
// File discovery
// ---------------------------------------------------------------------------

function getAllMarkdownFiles(dir, baseDir) {
    baseDir = baseDir || dir;
    const files = [];
    const entries = fs.readdirSync(dir, { withFileTypes: true });
    for (const entry of entries) {
        const fullPath = path.join(dir, entry.name);
        if (entry.isDirectory()) {
            files.push(...getAllMarkdownFiles(fullPath, baseDir));
        } else if (entry.name.endsWith('.md')) {
            if (!EXCLUDED_FILES.includes(entry.name)) {
                files.push(fullPath);
            }
        }
    }
    return files;
}

// ---------------------------------------------------------------------------
// README parsing — extract persona reading paths
// ---------------------------------------------------------------------------

const TAB_HEADING_MAP = {
    'business stakeholders': 'business',
    'for business stakeholders': 'business',
    'business': 'business',
    'technical implementers': 'technical',
    'for technical implementers': 'technical',
    'for technical teams': 'technical',
    'technical': 'technical',
    'development team': 'technical',
    'security reviewers': 'security',
    'for security reviewers': 'security',
    'for security teams': 'security',
    'security': 'security',
    'quality reviewers': 'quality',
    'for quality reviewers': 'quality',
    'quality': 'quality',
    'architecture reviewers': 'quality',
    'for architecture reviewers': 'quality',
    'project managers': 'business',
    'for project managers': 'business'
};

// Match section headings that contain the navigation guide
const NAV_SECTION_PATTERN = /^##\s+(Navigation Guide|Reading Guide|Reading Order by Stakeholder)/i;

function parseReadingOrder(readmeContent) {
    const tabs = {};
    const lines = readmeContent.split('\n');
    let inSection = false;
    let currentTab = null;

    for (const line of lines) {
        // Detect navigation section heading
        if (NAV_SECTION_PATTERN.test(line)) {
            inSection = true;
            continue;
        }
        // Exit section on next h2 (that isn't an h3)
        if (inSection && /^##\s+/.test(line) && !/^###/.test(line) && !NAV_SECTION_PATTERN.test(line)) {
            break;
        }
        if (!inSection) continue;

        // Format 1: h3 persona heading (e.g. "### Business Stakeholders" or "### For Technical Teams")
        const h3Match = line.match(/^###\s+(.+)$/);
        if (h3Match) {
            const heading = h3Match[1].trim().toLowerCase();
            currentTab = TAB_HEADING_MAP[heading] || null;
            if (currentTab && !tabs[currentTab]) tabs[currentTab] = [];
            continue;
        }

        // Format 2: bold inline persona (e.g. "**Business stakeholders**: Start with `file.md`...")
        const boldMatch = line.match(/^\*\*([^*]+)\*\*\s*:/);
        if (boldMatch) {
            const heading = boldMatch[1].trim().toLowerCase();
            const mapped = TAB_HEADING_MAP[heading];
            if (mapped) {
                currentTab = mapped;
                if (!tabs[currentTab]) tabs[currentTab] = [];
                // Extract backtick paths from the rest of this line
                const backtickPaths = line.matchAll(/`([^`]+\.md)`|`([^`]+\/)`/g);
                for (const m of backtickPaths) {
                    addPathToTab(tabs, currentTab, (m[1] || m[2]).trim(), '');
                }
                // Extract markdown link paths from the rest of this line
                const mdLinkPaths = line.matchAll(/\[([^\]]+)\]\(([^)]+\.md)\)|\[([^\]]+)\]\(([^)]+\/)\)/g);
                for (const m of mdLinkPaths) {
                    addPathToTab(tabs, currentTab, (m[2] || m[4]).trim(), '');
                }
                continue;
            }
        }

        if (!currentTab) continue;

        // Format 1 items: numbered list with description
        // Supports both backtick paths and markdown links:
        //   1. `path/to/file.md` — Description
        //   1. [Title](path/to/file.md) — Description
        const itemBacktick = line.match(/^\d+\.\s+`([^`]+)`(?:\s+[^—–\-]*)?\s+[—–\-]\s+(.+)$/);
        if (itemBacktick) {
            addPathToTab(tabs, currentTab, itemBacktick[1].trim(), itemBacktick[2].trim());
            continue;
        }
        const itemMdLink = line.match(/^\d+\.\s+\[([^\]]+)\]\(([^)]+)\)\s+[—–\-]\s+(.+)$/);
        if (itemMdLink) {
            addPathToTab(tabs, currentTab, itemMdLink[2].trim(), itemMdLink[3].trim());
            continue;
        }

        // Format 1 items without description
        const itemNoDescBacktick = line.match(/^\d+\.\s+`([^`]+)`\s*$/);
        if (itemNoDescBacktick) {
            addPathToTab(tabs, currentTab, itemNoDescBacktick[1].trim(), '');
            continue;
        }
        const itemNoDescMdLink = line.match(/^\d+\.\s+\[([^\]]+)\]\(([^)]+)\)\s*$/);
        if (itemNoDescMdLink) {
            addPathToTab(tabs, currentTab, itemNoDescMdLink[2].trim(), '');
            continue;
        }

        // Format 2 continuation: prose line with backtick paths or markdown links
        if (!/^\*\*/.test(line)) {
            // Extract backtick paths
            const backtickPaths = line.matchAll(/`([^`]+\.md)`|`([^`]+\/)`/g);
            for (const m of backtickPaths) {
                addPathToTab(tabs, currentTab, (m[1] || m[2]).trim(), '');
            }
            // Extract markdown link paths
            const mdLinkPaths = line.matchAll(/\[([^\]]+)\]\(([^)]+\.md)\)|\[([^\]]+)\]\(([^)]+\/)\)/g);
            for (const m of mdLinkPaths) {
                const filePath = (m[2] || m[4]).trim();
                addPathToTab(tabs, currentTab, filePath, '');
            }
        }
    }

    const tabIds = Object.keys(tabs).filter(k => tabs[k].length > 0);
    return tabIds.length > 0 ? tabs : null;
}

function addPathToTab(tabs, tabId, filePath, desc) {
    // Skip AGENTS.md — it's a machine-readable file, not a reading path
    if (filePath === 'AGENTS.md') return;

    const isFolder = filePath.endsWith('/');
    const htmlPath = isFolder ? filePath : filePath.replace(/\.md$/, '.html');
    const basename = isFolder
        ? path.basename(filePath.slice(0, -1))
        : path.basename(filePath, '.md');
    const title = basename.replace(/[-_]/g, ' ').replace(/\b\w/g, c => c.toUpperCase());

    // Deduplicate
    const isDuplicate = tabs[tabId].some(existing => existing.file === htmlPath);
    if (!isDuplicate) {
        tabs[tabId].push({ file: htmlPath, title: title, desc: desc, isFolder: isFolder });
    }
}

// ---------------------------------------------------------------------------
// Navigation builders
// ---------------------------------------------------------------------------

function buildNavTabs(tabs) {
    if (!tabs) return '';
    const tabDefs = [
        { id: 'business', label: 'Business' },
        { id: 'technical', label: 'Technical' },
        { id: 'security', label: 'Security' },
        { id: 'quality', label: 'Quality' }
    ];
    const activeTabs = tabDefs.filter(t => tabs[t.id] && tabs[t.id].length > 0);
    if (activeTabs.length === 0) return '';

    const html = ['<div class="nav-tabs">'];
    activeTabs.forEach((t, i) => {
        const active = i === 0 ? ' active' : '';
        html.push(`<div class="nav-tab${active}" onclick="switchTab('${t.id}', this)">${escapeHtml(t.label)}</div>`);
    });
    html.push('<div class="nav-tab" onclick="switchTab(\'all\', this)">All Docs</div>');
    html.push('</div>');
    return html.join('\n');
}

function buildNavTabContents(tabs) {
    if (!tabs) return '';
    const tabDefs = [
        { id: 'business', label: 'Business' },
        { id: 'technical', label: 'Technical' },
        { id: 'security', label: 'Security' },
        { id: 'quality', label: 'Quality' }
    ];
    const html = [];
    let first = true;
    for (const t of tabDefs) {
        if (!tabs[t.id] || tabs[t.id].length === 0) continue;
        const active = first ? ' active' : '';
        html.push(`<div class="tab-content${active}" id="tab-${t.id}">`);
        html.push('<ul class="reading-path">');
        tabs[t.id].forEach((item, i) => {
            const stepActive = (first && i === 0) ? ' active' : '';
            const onclick = item.isFolder
                ? `openAdrFolder(this)`
                : `selectStep(this, '${escapeHtml(item.file)}')`;
            html.push('<li>');
            html.push(`<a class="reading-step${stepActive}" onclick="${onclick}">`);
            html.push(`<span class="step-num">${i + 1}</span>`);
            html.push('<div class="step-info">');
            html.push(`<div class="step-title">${escapeHtml(item.title)}</div>`);
            html.push(`<div class="step-desc">${escapeHtml(item.desc)}</div>`);
            html.push('</div></a></li>');
        });
        html.push('</ul></div>');
        first = false;
    }
    return html.join('\n');
}

// ---------------------------------------------------------------------------
// All Docs tree builder (ordered by SECTION_ORDER)
// ---------------------------------------------------------------------------

function kebabToTitle(name) {
    return name.replace(/[-_]/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

function buildDocTree(convertedFiles, sourceDir) {
    // convertedFiles: Map of relPath (no ext) → htmlFilename
    // Build a lookup: { 'project-management/executive-summary': 'project-management/executive-summary.html' }
    const html = [];
    const placed = new Set();

    for (const section of SECTION_ORDER) {
        if (section.key === 'overview') {
            // Single file at root level
            const readmeKey = 'README';
            const readmeHtml = convertedFiles.get(readmeKey);
            if (readmeHtml) {
                html.push(`<li><a class="doc-file" onclick="selectDoc(this, '${escapeHtml(readmeHtml)}')" style="padding-left:8px;">Overview</a></li>`);
                placed.add(readmeKey);
            }
            continue;
        }

        if (section.catchAll) {
            // Appendices: everything not yet placed
            const remaining = [];
            for (const [key, htmlFile] of convertedFiles) {
                if (!placed.has(key)) {
                    remaining.push({ key, htmlFile });
                }
            }
            if (remaining.length === 0) continue;

            const collapsedClass = section.collapsed ? ' collapsed' : '';
            html.push('<li>');
            html.push(`<div class="doc-folder${collapsedClass}" onclick="toggleFolder(this)"><span class="doc-chevron">▾</span> ${escapeHtml(section.label)}</div>`);
            html.push(`<ul class="doc-nested${collapsedClass}">`);

            // Group remaining by folder
            const folders = {};
            const rootFiles = [];
            for (const item of remaining) {
                const parts = item.key.split('/');
                if (parts.length === 1) {
                    rootFiles.push(item);
                } else {
                    // Get the folder path relative to appendices
                    const folderParts = parts.slice(0, -1);
                    // For appendices, strip the 'appendices/' prefix if present
                    const folderKey = folderParts.join('/');
                    if (!folders[folderKey]) folders[folderKey] = [];
                    folders[folderKey].push(item);
                }
                placed.add(item.key);
            }

            // Render root-level appendix files first
            for (const item of rootFiles) {
                const displayName = kebabToTitle(item.key);
                html.push(`<li><a class="doc-file" onclick="selectDoc(this, '${escapeHtml(item.htmlFile)}')">${escapeHtml(displayName)}</a></li>`);
            }

            // Render appendix subfolders
            const appendixBase = 'appendices/';
            for (const item of remaining) {
                // Already handled root files above
            }
            // Group by immediate subfolder under appendices
            const subfolders = {};
            for (const item of remaining) {
                if (item.key.split('/').length <= 1) continue;
                const relToAppendix = item.key.startsWith(appendixBase)
                    ? item.key.slice(appendixBase.length)
                    : item.key;
                const subParts = relToAppendix.split('/');
                if (subParts.length > 1) {
                    const subName = subParts[0];
                    if (!subfolders[subName]) subfolders[subName] = [];
                    subfolders[subName].push(item);
                } else {
                    // Direct child of appendices
                    const displayName = kebabToTitle(path.basename(item.key));
                    html.push(`<li><a class="doc-file" onclick="selectDoc(this, '${escapeHtml(item.htmlFile)}')">${escapeHtml(displayName)}</a></li>`);
                }
            }

            for (const [subName, items] of Object.entries(subfolders)) {
                html.push('<li>');
                html.push(`<div class="doc-folder collapsed" onclick="toggleFolder(this)"><span class="doc-chevron">▾</span> ${escapeHtml(kebabToTitle(subName))}</div>`);
                html.push('<ul class="doc-nested collapsed">');
                for (const item of items) {
                    const displayName = kebabToTitle(path.basename(item.key));
                    html.push(`<li><a class="doc-file" onclick="selectDoc(this, '${escapeHtml(item.htmlFile)}')">${escapeHtml(displayName)}</a></li>`);
                }
                html.push('</ul></li>');
            }

            html.push('</ul></li>');
            continue;
        }

        // Regular section with known files
        const sectionFiles = [];
        for (const fileBase of section.files) {
            const key = section.key === 'overview' ? fileBase : `${section.key}/${fileBase}`;
            const htmlFile = convertedFiles.get(key);
            if (htmlFile) {
                sectionFiles.push({ key, htmlFile, displayName: kebabToTitle(fileBase) });
                placed.add(key);
            }
        }

        // Check for subfolders (e.g., architecture-decision-records)
        const subfolderItems = [];
        if (section.subfolders) {
            for (const sub of section.subfolders) {
                const prefix = `${section.key}/${sub.key}/`;
                const items = [];
                for (const [key, htmlFile] of convertedFiles) {
                    if (key.startsWith(prefix) && !placed.has(key)) {
                        items.push({ key, htmlFile, displayName: kebabToTitle(path.basename(key)) });
                        placed.add(key);
                    }
                }
                if (items.length > 0) {
                    // Sort ADRs by filename to preserve ADR-001, ADR-002 order
                    items.sort((a, b) => path.basename(a.key).localeCompare(path.basename(b.key)));
                    subfolderItems.push({ label: sub.label, collapsed: sub.collapsed, items, key: sub.key });
                }
            }
        }

        // Also pick up any files in this section folder not explicitly listed
        for (const [key, htmlFile] of convertedFiles) {
            if (key.startsWith(section.key + '/') && !placed.has(key)) {
                // Only direct children (not in subfolders)
                const rel = key.slice(section.key.length + 1);
                if (!rel.includes('/')) {
                    sectionFiles.push({ key, htmlFile, displayName: kebabToTitle(path.basename(key)) });
                    placed.add(key);
                }
            }
        }

        if (sectionFiles.length === 0 && subfolderItems.length === 0) continue;

        html.push('<li>');
        html.push(`<div class="doc-folder" onclick="toggleFolder(this)"><span class="doc-chevron">▾</span> ${escapeHtml(section.label)}</div>`);
        html.push('<ul class="doc-nested">');

        for (const f of sectionFiles) {
            html.push(`<li><a class="doc-file" onclick="selectDoc(this, '${escapeHtml(f.htmlFile)}')">${escapeHtml(f.displayName)}</a></li>`);
        }

        for (const sub of subfolderItems) {
            const collapsedClass = sub.collapsed ? ' collapsed' : '';
            const idAttr = sub.key === 'architecture-decision-records' ? ' id="adr-folder"' : '';
            html.push('<li>');
            html.push(`<div class="doc-folder${collapsedClass}"${idAttr} onclick="toggleFolder(this)"><span class="doc-chevron">▾</span> ${escapeHtml(sub.label)}</div>`);
            html.push(`<ul class="doc-nested${collapsedClass}">`);
            for (const item of sub.items) {
                html.push(`<li><a class="doc-file" onclick="selectDoc(this, '${escapeHtml(item.htmlFile)}')">${escapeHtml(item.displayName)}</a></li>`);
            }
            html.push('</ul></li>');
        }

        html.push('</ul></li>');
    }

    return html.join('\n');
}

// ---------------------------------------------------------------------------
// Date formatting
// ---------------------------------------------------------------------------

function formatDate(date) {
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    return `${months[date.getUTCMonth()]} ${date.getUTCDate()}, ${date.getUTCFullYear()}`;
}

// ---------------------------------------------------------------------------
// Logo embedding
// ---------------------------------------------------------------------------

function loadLogoDataUri() {
    const logoPath = path.join(REPORT_DIR, 'apex-logo.svg');
    if (fs.existsSync(logoPath)) {
        const svgContent = fs.readFileSync(logoPath);
        const base64 = svgContent.toString('base64');
        return `data:image/svg+xml;base64,${base64}`;
    }
    return '';
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

function main() {
    const sourceDir = path.join(process.cwd(), 'generated', 'design');
    const outputDir = path.join(process.cwd(), 'generated', 'design_html');
    // Additional source directories that live alongside generated/design/ but
    // should be rendered into the same HTML site under a relative path.
    // Each entry: { dir: absolute path, prefix: relative path under outputDir }
    const additionalSources = [
        {
            dir: path.join(process.cwd(), 'generated', 'fpm-artifacts'),
            prefix: 'fpm-artifacts'
        }
    ];

    if (!fs.existsSync(sourceDir)) {
        console.error(`Error: Source directory ${sourceDir} does not exist`);
        process.exit(1);
    }

    fs.mkdirSync(outputDir, { recursive: true });

    // mermaid.min.js is bundled alongside this script at build time
    const mermaidSource = path.join(SCRIPT_DIR, 'mermaid.min.js');
    const mermaidDest = path.join(outputDir, 'mermaid.min.js');
    if (fs.existsSync(mermaidSource)) {
        fs.copyFileSync(mermaidSource, mermaidDest);
        console.log('Copied mermaid.min.js to output directory');
    } else {
        console.warn('WARNING: mermaid.min.js not found in .apex/tools/ - diagrams will not render');
    }

    // Load templates and assets
    const indexTemplate = loadTemplate('template-index.html');
    const pageTemplate = loadTemplate('template-page.html');
    const indexCss = loadTemplate('styles-index.css');
    const pageCss = loadTemplate('styles-page.css');
    const logoDataUri = loadLogoDataUri();

    // Collect files to convert. Each entry tracks where the file came from so
    // we can emit it to the correct output path and include it in the nav tree.
    // filesToConvertWithMeta: [{ file, sourceRoot, outputRel }]
    //   file: absolute path to the .md file
    //   sourceRoot: the root directory this file was discovered under
    //   outputRel: relative path under outputDir where the HTML should land
    const filesToConvertWithMeta = getAllMarkdownFiles(sourceDir).map(f => ({
        file: f,
        sourceRoot: sourceDir,
        outputRel: path.relative(sourceDir, f)
    }));

    for (const extra of additionalSources) {
        if (!fs.existsSync(extra.dir)) continue;
        const extraFiles = getAllMarkdownFiles(extra.dir);
        for (const f of extraFiles) {
            const relWithinExtra = path.relative(extra.dir, f);
            filesToConvertWithMeta.push({
                file: f,
                sourceRoot: extra.dir,
                outputRel: path.join(extra.prefix, relWithinExtra)
            });
        }
    }

    console.log(`Found ${filesToConvertWithMeta.length} markdown files to convert`);

    // convertedFiles: Map of relKey (without extension) → html filename
    const convertedFiles = new Map();

    for (const entry of filesToConvertWithMeta) {
        const { file: mdFile, outputRel } = entry;
        const htmlFilename = outputRel.replace(/\.md$/, '.html');
        const relKey = outputRel.replace(/\.md$/, '').replace(/\\/g, '/');
        const outputPath = path.join(outputDir, htmlFilename);

        fs.mkdirSync(path.dirname(outputPath), { recursive: true });

        // Compute relative path from this HTML file back to mermaid.min.js at output root
        const depth = outputRel.split(path.sep).length - 1;
        const mermaidRelPath = (depth > 0 ? '../'.repeat(depth) : './') + 'mermaid.min.js';

        console.log(`Converting: ${outputRel}`);
        const mdContent = fs.readFileSync(mdFile, 'utf-8');
        const { html: htmlContent, headings } = convertMarkdownToHtml(mdContent);
        const title = path.basename(mdFile, '.md').replace(/[-_]/g, ' ').replace(/\b\w/g, c => c.toUpperCase());

        const fullHtml = pageTemplate
            .split('{{TITLE}}').join(escapeHtml(title))
            .split('{{CONTENT}}').join(htmlContent)
            .split('{{MERMAID_PATH}}').join(mermaidRelPath)
            .split('{{PAGE_CSS}}').join(pageCss);

        fs.writeFileSync(outputPath, fullHtml);
        convertedFiles.set(relKey, htmlFilename.replace(/\\/g, '/'));
    }

    // Get project name from README
    let projectName = 'Design Documentation';
    const readmePath = path.join(sourceDir, 'README.md');
    let readmeContent = '';
    if (fs.existsSync(readmePath)) {
        readmeContent = fs.readFileSync(readmePath, 'utf-8');
        const firstLine = readmeContent.split('\n')[0].trim();
        if (firstLine.startsWith('#')) {
            projectName = firstLine.replace(/^#+\s*/, '');
        }
    }

    // Parse persona tabs from README
    const tabs = readmeContent ? parseReadingOrder(readmeContent) : null;

    // Build navigation
    const navTabs = buildNavTabs(tabs);
    const navTabContents = buildNavTabContents(tabs);
    const navTree = buildDocTree(convertedFiles, sourceDir);

    // Determine default document to load
    let defaultDoc = 'README.html';
    if (convertedFiles.has('project-management/executive-summary')) {
        defaultDoc = 'project-management/executive-summary.html';
    }

    // If no persona tabs, All Docs is the only tab — make it active
    const allDocsActive = tabs ? '' : ' active';
    // If no persona tabs, don't render the tab bar at all (just show tree)
    const finalNavTabs = tabs
        ? navTabs
        : '';

    const indexHtml = indexTemplate
        .split('{{PROJECT_NAME}}').join(escapeHtml(projectName))
        .split('{{INDEX_CSS}}').join(indexCss)
        .split('{{LOGO_DATA_URI}}').join(logoDataUri)
        .split('{{NAV_TABS}}').join(finalNavTabs)
        .split('{{NAV_TAB_CONTENTS}}').join(navTabContents)
        .split('{{NAV_TREE}}').join(navTree)
        .split('{{ALL_DOCS_ACTIVE}}').join(allDocsActive)
        .split('{{DEFAULT_DOC}}').join(defaultDoc)
        .split('{{DATE}}').join(formatDate(new Date()));

    console.log('Creating index.html');
    fs.writeFileSync(path.join(outputDir, 'index.html'), indexHtml);

    console.log(`\nDone! Created ${filesToConvertWithMeta.length + 1} HTML files in ${outputDir}`);
}

if (require.main === module) {
    main();
}

// Export for testing
module.exports = { escapeHtml, processInline, convertMarkdownToHtml };
