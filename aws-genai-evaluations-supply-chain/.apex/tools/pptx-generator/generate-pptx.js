#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');

// Load pptxgenjs from the same directory (copied from node_modules during build)
const pptxLibPath = path.join(__dirname, 'pptxgenjs.bundle.js');
let PptxGenJS;
try {
  PptxGenJS = require(pptxLibPath);
} catch {
  console.error(`Error: pptxgenjs.bundle.js not found at ${pptxLibPath}. Run the build to copy it from node_modules.`);
  process.exit(1);
}

// AWS color palette
const COLORS = {
  primary: '232F3E',
  secondary: 'FF9900',
  text: '232F3E',
  lightText: '545B64',
  white: 'FFFFFF',
  lightGray: 'F7F8F8',
  accent: '0073BB'
};

const FONTS = { title: 'Amazon Ember', body: 'Amazon Ember' };

// --- Markdown parsing helpers ---

function extractTitle(md) {
  const match = md.match(/^#\s+(.+)$/m);
  return match ? match[1].trim() : 'Untitled';
}

function extractField(md, fieldName) {
  const re = new RegExp(`\\*\\*${fieldName}\\*\\*:\\s*(.+?)(?=\\n|$)`, 'i');
  const match = md.match(re);
  return match ? match[1].trim() : null;
}

function extractSection(md, sectionName) {
  const lines = md.split('\n');
  let capturing = false;
  const result = [];
  for (const line of lines) {
    if (line.match(new RegExp(`^##\\s+${sectionName}`, 'i'))) {
      capturing = true;
      continue;
    }
    if (capturing) {
      if (line.match(/^##\s+/) || line.match(/^---\s*$/)) break;
      result.push(line);
    }
  }
  return result.join('\n');
}

function extractListItems(md, maxItems = 8) {
  const items = [];
  const lines = md.split('\n');
  for (const line of lines) {
    const match = line.match(/^[-*]\s+(.+)$/) || line.match(/^\d+\.\s+(.+)$/);
    if (match) {
      const text = match[1].trim()
        .replace(/\*\*(.+?)\*\*/g, '$1')
        .replace(/\[(.+?)\]\(.+?\)/g, '$1');
      items.push(text);
      if (items.length >= maxItems) break;
    }
  }
  return items;
}

function extractNumberedItems(md, maxItems = 6) {
  const items = [];
  const lines = md.split('\n');
  for (const line of lines) {
    const match = line.match(/^\d+\.\s+\*\*(.+?)\*\*:\s*(.+)$/);
    if (match) {
      items.push({ title: match[1].trim(), desc: match[2].trim() });
      if (items.length >= maxItems) break;
    }
  }
  return items;
}

function extractKeyValueItems(md) {
  const items = [];
  const lines = md.split('\n');
  for (const line of lines) {
    const match = line.match(/^-\s+\*\*(.+?)\*\*:\s*(.+)$/);
    if (match) {
      items.push({ category: match[1].trim(), value: match[2].trim() });
    }
  }
  return items;
}

function readFileIfExists(filePath) {
  try {
    if (fs.existsSync(filePath)) return fs.readFileSync(filePath, 'utf-8');
  } catch {
    console.warn(`Warning: Could not read ${filePath}`);
  }
  return null;
}

// --- Slide builders ---

function addSlideHeader(slide, title) {
  slide.addShape('rect', { x: 0, y: 0, w: '100%', h: 0.7, fill: { color: COLORS.primary } });
  slide.addText(title, { x: 0.4, y: 0.15, w: '90%', h: 0.4, fontSize: 24, fontFace: FONTS.title, color: COLORS.white, bold: true });
}

function addProblemSlide(pptx, data) {
  const slide = pptx.addSlide();
  addSlideHeader(slide, 'Problem Statement');
  slide.addText(data.problem, { x: 0.5, y: 1.2, w: 12.3, h: 1.5, fontSize: 20, fontFace: FONTS.body, color: COLORS.text, valign: 'top', wrap: true });
  slide.addShape('rect', { x: 0.5, y: 3, w: 12.3, h: 2.5, fill: { color: COLORS.lightGray }, line: { color: 'E0E0E0', width: 1 } });
  slide.addText('Context', { x: 0.7, y: 3.1, w: 12, h: 0.4, fontSize: 14, fontFace: FONTS.title, color: COLORS.primary, bold: true });
  const contextItems = [
    { text: `Target: ${data.target}`, options: { bullet: true } },
    { text: `Scope: ${data.scope}`, options: { bullet: true } },
    { text: `Timeline: ${data.timeline}`, options: { bullet: true } }
  ];
  slide.addText(contextItems, { x: 0.7, y: 3.6, w: 11.8, h: 1.8, fontSize: 14, fontFace: FONTS.body, color: COLORS.text, lineSpacing: 24 });
}

function addSolutionSlide(pptx, data) {
  const slide = pptx.addSlide();
  addSlideHeader(slide, 'Solution');
  slide.addText(data.solution, { x: 0.5, y: 1.2, w: 12.3, h: 1.8, fontSize: 18, fontFace: FONTS.body, color: COLORS.text, valign: 'top', wrap: true });
  slide.addShape('rect', { x: 0.5, y: 3.2, w: 12.3, h: 3.5, fill: { color: COLORS.lightGray }, line: { color: 'E0E0E0', width: 1 } });
  slide.addText('Business Value', { x: 0.7, y: 3.3, w: 12, h: 0.4, fontSize: 14, fontFace: FONTS.title, color: COLORS.primary, bold: true });
  const items = data.businessValue.map(v => ({ text: v, options: { bullet: true } }));
  slide.addText(items, { x: 0.7, y: 3.8, w: 11.8, h: 2.8, fontSize: 12, fontFace: FONTS.body, color: COLORS.text, lineSpacing: 20, valign: 'top' });
}

function addRequirementsSlide(pptx, data) {
  const slide = pptx.addSlide();
  addSlideHeader(slide, 'Requirements');
  const colW = 6;

  slide.addShape('rect', { x: 0.5, y: 1, w: colW, h: 5.8, fill: { color: COLORS.lightGray }, line: { color: 'E0E0E0', width: 1 } });
  slide.addText(`Functional (${data.funcCount})`, { x: 0.7, y: 1.1, w: colW - 0.4, h: 0.4, fontSize: 14, fontFace: FONTS.title, color: COLORS.primary, bold: true });
  const funcItems = data.funcReqs.map(r => ({ text: r, options: { bullet: true } }));
  slide.addText(funcItems, { x: 0.7, y: 1.6, w: colW - 0.4, h: 5, fontSize: 10, fontFace: FONTS.body, color: COLORS.text, lineSpacing: 16, valign: 'top' });

  slide.addShape('rect', { x: 6.8, y: 1, w: colW, h: 5.8, fill: { color: COLORS.lightGray }, line: { color: 'E0E0E0', width: 1 } });
  slide.addText(`Non-Functional (${data.nonfuncCount})`, { x: 7, y: 1.1, w: colW - 0.4, h: 0.4, fontSize: 14, fontFace: FONTS.title, color: COLORS.primary, bold: true });
  const nfItems = data.nonfuncReqs.map(r => ({ text: r, options: { bullet: true } }));
  slide.addText(nfItems, { x: 7, y: 1.6, w: colW - 0.4, h: 5, fontSize: 10, fontFace: FONTS.body, color: COLORS.text, lineSpacing: 16, valign: 'top' });
}

function addArchitectureSlide(pptx, data) {
  const slide = pptx.addSlide();
  addSlideHeader(slide, 'Architecture');
  const colW = 6;

  slide.addText('Key Decisions', { x: 0.5, y: 1, w: colW, h: 0.4, fontSize: 14, fontFace: FONTS.title, color: COLORS.primary, bold: true });
  const decisionText = data.decisions.map(d => [
    { text: `${d.title}: `, options: { bold: true, fontSize: 10 } },
    { text: d.desc + '\n', options: { fontSize: 9 } }
  ]).flat();
  slide.addText(decisionText, { x: 0.5, y: 1.5, w: colW, h: 5.5, fontFace: FONTS.body, color: COLORS.text, valign: 'top', wrap: true, lineSpacing: 14 });

  slide.addShape('rect', { x: 6.8, y: 1, w: colW, h: 5.8, fill: { color: COLORS.lightGray }, line: { color: 'E0E0E0', width: 1 } });
  slide.addText('Technology Stack', { x: 7, y: 1.1, w: colW - 0.4, h: 0.4, fontSize: 14, fontFace: FONTS.title, color: COLORS.primary, bold: true });
  const techText = data.techStack.map(t => [
    { text: `${t.category}: `, options: { bold: true, fontSize: 10 } },
    { text: t.value + '\n', options: { fontSize: 9 } }
  ]).flat();
  slide.addText(techText, { x: 7, y: 1.6, w: colW - 0.4, h: 5, fontFace: FONTS.body, color: COLORS.text, valign: 'top', wrap: true, lineSpacing: 14 });
}

// --- Main ---

function main() {
  const designDir = path.join(process.cwd(), 'generated', 'design');
  const outputDir = path.join(process.cwd(), 'generated', 'design_pptx');

  if (!fs.existsSync(designDir)) {
    console.error(`Error: Source directory ${designDir} does not exist`);
    process.exit(1);
  }
  fs.mkdirSync(outputDir, { recursive: true });

  console.log('Reading design specification files...');
  const readme = readFileIfExists(path.join(designDir, 'README.md'));
  const execSummary = readFileIfExists(path.join(designDir, 'project-management', 'executive-summary.md'));
  const funcReqsMd = readFileIfExists(path.join(designDir, 'requirements', 'functional-requirements.md'));
  const nfReqsMd = readFileIfExists(path.join(designDir, 'requirements', 'non-functional-requirements.md'));

  if (!readme) { console.error('Error: README.md not found'); process.exit(1); }

  const title = extractTitle(readme);
  console.log(`Project: ${title}`);

  const problem = extractField(readme, 'Problem Solved') || 'Problem statement not found';
  const target = extractField(readme, 'Target Delivery') || 'TBD';
  const scope = extractField(readme, 'Scope') || 'TBD';
  const timeline = extractField(execSummary || readme, 'Target Delivery') || target;
  const solution = extractField(readme, 'Solution') || 'Solution description not found';

  const bizValueSection = extractSection(execSummary || '', 'Business Value');
  const businessValue = extractListItems(bizValueSection, 6);
  if (businessValue.length === 0) businessValue.push('See executive summary for business value details');

  const funcReqs = extractListItems(funcReqsMd || '', 10);
  const nonfuncReqs = extractListItems(nfReqsMd || '', 10);
  const funcCount = (funcReqsMd?.match(/^###\s+FR-|^-\s+\*\*FR-/gm) || []).length || funcReqs.length;
  const nonfuncCount = (nfReqsMd?.match(/^###\s+NFR-|^-\s+\*\*NFR-/gm) || []).length || nonfuncReqs.length;

  const adrSection = extractSection(readme, 'Key Architectural Decisions');
  const decisions = extractNumberedItems(adrSection, 6);
  const techSection = extractSection(readme, 'Technology Stack');
  const techStack = extractKeyValueItems(techSection);

  console.log('Extracted content:');
  console.log(`  - Problem: ${problem.length} chars`);
  console.log(`  - Solution: ${solution.length} chars`);
  console.log(`  - Business Value: ${businessValue.length} items`);
  console.log(`  - Functional Reqs: ${funcReqs.length} items (${funcCount} total)`);
  console.log(`  - Non-Functional Reqs: ${nonfuncReqs.length} items (${nonfuncCount} total)`);
  console.log(`  - Architecture Decisions: ${decisions.length} items`);
  console.log(`  - Tech Stack: ${techStack.length} items`);

  const pptx = new PptxGenJS();
  pptx.author = 'APEX Design Agent';
  pptx.title = `${title} - Design Summary`;
  pptx.layout = 'LAYOUT_WIDE';

  console.log('Building slides...');
  addProblemSlide(pptx, { problem, target, scope, timeline });
  addSolutionSlide(pptx, { solution, businessValue });
  addRequirementsSlide(pptx, { funcReqs, nonfuncReqs, funcCount, nonfuncCount });
  addArchitectureSlide(pptx, { decisions, techStack });

  const outputPath = path.join(outputDir, 'design-summary.pptx');
  pptx.writeFile({ fileName: outputPath })
    .then(() => console.log(`Done! Created presentation at: ${outputPath}`))
    .catch(err => { console.error('Error writing PPTX:', err); process.exit(1); });
}

if (require.main === module) main();

module.exports = { extractTitle, extractSection, extractListItems };
