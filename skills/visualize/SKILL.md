---
name: visualize
description: "Generate interactive HTML visualizations to explain work, architecture, and systems. Use this skill
whenever the user says 'visualize', 'diagram', 'draw', 'show me', 'explain visually', 'overview' (when they want a
visual, not text), or when the user seems confused and a picture would genuinely help them understand what happened, how
things connect, or what the current state looks like. Also use when the user asks to see something 'as a tree', 'as a
flow', 'as slides', or 'as a diagram'. This skill renders in the browser via Chrome MCP tools — it is NOT for generating
text-based explanations."
updated: 2026-04-02
---

# Visualize

Generate self-contained interactive HTML visualizations and render them in the user's browser. The goal is to help the
user *see* what they're working on — architecture, data flows, session progress, hierarchies, sequences — in a way
that builds intuition faster than text.

**All diagrams are pure HTML/CSS/JS. No Mermaid. No CDN dependencies. No external libraries.**

Every diagram is a single `.html` file that opens in any browser with zero setup.

## When to Use This

- **End of a task or batch** — summarize what was built, changed, or fixed
- **User is confused** — "wait, how does this connect?" or "I'm lost" signals
- **Architecture questions** — how components relate, data flows, dependency chains
- **Explaining a complex change** — before/after comparisons, multi-step processes
- **User explicitly asks** — "visualize", "diagram this", "show me as a tree"

## Core Principles

1. **Pick the right diagram type for the content.** Don't default to one format — match the shape of the information.
2. **Less is more.** A focused diagram beats a cluttered dashboard. Only include what helps understanding.
3. **Information layering.** Summary visible at a glance, details revealed on interaction (hover or click). The user
   controls how deep they go.
4. **Hover-to-isolate is the killer feature.** In any graph with connections, hovering a node fades everything
   unrelated. Dense graphs become instantly readable because you only see what matters right now.
5. **Semantic color coding.** Colors mean something consistent (category, relationship type) — never decorative.
6. **Domain-agnostic.** This works for Ansible, Terraform, Python, GHA, shell scripts, APIs, databases — anything.
7. **Always persist.** Every visualization gets saved to `~/visualizations/` so the user can come back to it later.

## Diagram Types

There are two core interactive diagram types. Everything else (session summaries, before/after comparisons, single
focused diagrams) is built by composing or embedding these.

---

### Type 1: Topology Graph (hover-to-isolate connections)

**When to use:** Architecture overviews, infrastructure maps, dependency graphs, "how does X connect to Y?",
relationship hierarchies, any system where things have connections to other things.

**What makes it special:** Hovering any node instantly fades out everything not directly connected to it. Only the
hovered node, its neighbors, and their connecting edges stay visible. Edge labels — hidden by default to reduce
clutter — appear only on the active connections. This turns a visually overwhelming graph into something you can
read one relationship at a time.

#### Architecture

Three layers inside a fixed-size container:

1. **Node divs** — absolutely positioned boxes with `data-node="unique_id"` and `data-tip="<html>"` for rich tooltips.
2. **Edge definitions** — a JS array of `[fromNodeId, toNodeId, label, color]` tuples. Rendered as SVG `<line>`
   elements by reading node DOM positions at runtime.
3. **Hover logic** — `highlightNode(id)` walks the edge array to find connected nodes, applies `.faded` to
   unconnected nodes, `.hidden`/`.highlight` to edges and labels. `clearHighlight()` resets on mouse leave.

#### Reference Implementation

This is the complete pattern. Adapt the nodes, edges, categories, and positioning for your specific content.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>[TITLE]</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: system-ui, -apple-system, sans-serif;
    background: #f8fafc; color: #1e293b;
    padding: 24px; max-width: 1100px; margin: 0 auto;
  }
  h1 { font-size: 1.4rem; font-weight: 700; margin-bottom: 2px; }
  .subtitle { font-size: 0.82rem; color: #64748b; margin-bottom: 20px; }

  /* ── Graph container ── */
  .graph {
    position: relative; width: 100%; height: 700px;
    background: white; border-radius: 12px;
    border: 1px solid #e2e8f0; overflow: hidden;
  }

  /* ── Nodes ── */
  .node {
    position: absolute; border-radius: 10px; padding: 10px 14px;
    text-align: center; cursor: default; z-index: 2;
    border: 2px solid; min-width: 120px;
    transition: box-shadow 0.15s, transform 0.15s;
  }
  .node:hover { transform: scale(1.05); z-index: 10; }
  .node.faded { opacity: 0.12; transform: scale(0.97); pointer-events: none; }
  .node.active { z-index: 10; }
  .node h3 { font-size: 0.82rem; font-weight: 700; margin-bottom: 2px; }
  .node p { font-size: 0.7rem; line-height: 1.3; }

  /*
   * Node categories — define one per logical group.
   * Each needs: background, border-color, text color, hover glow, h3 color.
   * Pick from: orange, blue, green, purple, amber, indigo, red, teal, pink.
   * Examples below — rename and recolor for your domain.
   */
  .node.cat-orange  { background: #fff7ed; border-color: #f97316; color: #9a3412; }
  .node.cat-orange:hover  { box-shadow: 0 4px 20px rgba(249,115,22,0.25); }
  .node.cat-orange  h3 { color: #c2410c; }

  .node.cat-blue    { background: #eff6ff; border-color: #3b82f6; color: #1e40af; }
  .node.cat-blue:hover    { box-shadow: 0 4px 20px rgba(59,130,246,0.25); }
  .node.cat-blue    h3 { color: #1d4ed8; }

  .node.cat-green   { background: #f0fdf4; border-color: #22c55e; color: #166534; }
  .node.cat-green:hover   { box-shadow: 0 4px 20px rgba(34,197,94,0.25); }
  .node.cat-green   h3 { color: #15803d; }

  .node.cat-purple  { background: #faf5ff; border-color: #8b5cf6; color: #5b21b6; }
  .node.cat-purple:hover  { box-shadow: 0 4px 20px rgba(139,92,246,0.25); }
  .node.cat-purple  h3 { color: #6d28d9; }

  .node.cat-amber   { background: #fffbeb; border-color: #f59e0b; color: #92400e; }
  .node.cat-amber:hover   { box-shadow: 0 4px 20px rgba(245,158,11,0.25); }
  .node.cat-amber   h3 { color: #b45309; }

  .node.cat-indigo  { background: #eef2ff; border-color: #6366f1; color: #3730a3; }
  .node.cat-indigo:hover  { box-shadow: 0 4px 20px rgba(99,102,241,0.25); }
  .node.cat-indigo  h3 { color: #4338ca; }

  .node.cat-red     { background: #fef2f2; border-color: #ef4444; color: #991b1b; }
  .node.cat-red:hover     { box-shadow: 0 4px 20px rgba(239,68,68,0.25); }
  .node.cat-red     h3 { color: #dc2626; }

  .node.cat-teal    { background: #f0fdfa; border-color: #14b8a6; color: #115e59; }
  .node.cat-teal:hover    { box-shadow: 0 4px 20px rgba(20,184,166,0.25); }
  .node.cat-teal    h3 { color: #0d9488; }

  /* ── Corner group labels ── */
  .group-label {
    position: absolute; font-size: 0.68rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.06em;
    z-index: 1; padding: 2px 8px; border-radius: 4px;
  }

  /* ── SVG Edges ── */
  svg.edges {
    position: absolute; top: 0; left: 0; width: 100%; height: 100%;
    z-index: 0; pointer-events: none;
  }
  svg.edges line { stroke-width: 1.5; transition: opacity 0.2s; }
  svg.edges line.hidden { opacity: 0 !important; }
  svg.edges line.highlight { opacity: 0.8 !important; stroke-width: 2; }
  svg.edges text {
    font-family: system-ui; font-size: 9px; fill: #94a3b8;
    transition: opacity 0.2s;
  }
  svg.edges text.hidden { opacity: 0 !important; }
  svg.edges text.highlight { opacity: 1 !important; fill: #475569; }

  /* ── Tooltip ── */
  .tooltip {
    display: none; position: absolute; background: white;
    border: 1px solid #e2e8f0; border-radius: 10px;
    padding: 12px 16px; max-width: 300px; z-index: 20;
    box-shadow: 0 8px 24px rgba(0,0,0,0.12); pointer-events: none;
  }
  .tooltip.visible { display: block; }
  .tooltip h4 { font-size: 0.85rem; margin-bottom: 4px; }
  .tooltip p { font-size: 0.78rem; color: #64748b; line-height: 1.5; margin-bottom: 3px; }
  .tooltip .badge {
    display: inline-block; font-size: 0.68rem; padding: 1px 7px;
    border-radius: 10px; margin: 1px; font-weight: 500;
  }
</style>
</head>
<body>

<h1>[TITLE]</h1>
<p class="subtitle">Hover any box for details. Connections show data flow between components.</p>

<div class="graph" id="graph">

  <!-- Group labels — position in corners to label spatial regions -->
  <span class="group-label" style="top:6px;left:12px;color:#c2410c;background:#fff7ed">[Group A]</span>
  <span class="group-label" style="top:6px;right:12px;color:#15803d;background:#f0fdf4">[Group B]</span>

  <!-- SVG edge layer (populated by JS) -->
  <svg class="edges" id="edgeSvg" viewBox="0 0 1100 700" preserveAspectRatio="none"></svg>

  <!--
    NODES — one div per entity.
    Required attributes:
      data-node="unique_id"     — must match edge definitions
      data-tip="<html>"         — rich tooltip shown on hover
      onmouseenter/onmouseleave — wire up hover behavior
    Position with style="left:Xpx;top:Ypx;width:Wpx"
    Category class: cat-orange, cat-blue, cat-green, cat-purple, cat-amber, cat-indigo, cat-red, cat-teal
  -->
  <div class="node cat-blue" style="left:30px;top:40px;width:180px" data-node="example_node"
    onmouseenter="onNodeEnter(this,event)" onmouseleave="onNodeLeave(this)"
    data-tip="<h4>Example Node</h4><p><strong>Detail:</strong> Some specifics</p><p>More context here</p>">
    <h3>Example Node</h3>
    <p>Short description</p>
  </div>

  <!-- ... more nodes ... -->

  <!-- Tooltip container -->
  <div class="tooltip" id="tooltip"></div>
</div>

<script>
const tip = document.getElementById('tooltip');
const graph = document.getElementById('graph');
const svg = document.getElementById('edgeSvg');

// ═══════════════════════════════════════════════════
// EDGE DEFINITIONS: [fromNodeId, toNodeId, label, color]
//
// Color conventions (adapt to your domain):
//   #3b82f6 — data/API connections (blue)
//   #22c55e — CI/CD or build flows (green)
//   #8b5cf6 — management/IaC (purple)
//   #f59e0b — secrets/config injection (amber)
//   #6366f1 — network/mesh (indigo)
//   #94a3b8 — secondary/dev connections (gray)
// ═══════════════════════════════════════════════════
const edges = [
  ['node_a', 'node_b', 'edge label', '#3b82f6'],
  // ... more edges ...
];

// ═══════════════════════════════════════════════════
// ENGINE — no changes needed below this line
// ═══════════════════════════════════════════════════

function getNodeCenter(nodeId) {
  const el = document.querySelector(`[data-node="${nodeId}"]`);
  if (!el) return { x: 0, y: 0 };
  const r = el.getBoundingClientRect();
  const gr = graph.getBoundingClientRect();
  const scaleX = 1100 / gr.width;
  const scaleY = 700 / gr.height;
  return {
    x: (r.left - gr.left + r.width / 2) * scaleX,
    y: (r.top - gr.top + r.height / 2) * scaleY,
  };
}

function renderEdges() {
  svg.innerHTML = '';
  edges.forEach(([from, to, label, color], i) => {
    const a = getNodeCenter(from);
    const b = getNodeCenter(to);
    const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    line.setAttribute('x1', a.x); line.setAttribute('y1', a.y);
    line.setAttribute('x2', b.x); line.setAttribute('y2', b.y);
    line.setAttribute('stroke', color);
    line.setAttribute('stroke-dasharray', '5,4');
    line.setAttribute('opacity', '0.35');
    line.dataset.from = from; line.dataset.to = to; line.dataset.idx = i;
    svg.appendChild(line);

    const txt = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    txt.setAttribute('x', (a.x + b.x) / 2);
    txt.setAttribute('y', (a.y + b.y) / 2 - 5);
    txt.setAttribute('text-anchor', 'middle');
    txt.setAttribute('opacity', '0');
    txt.textContent = label;
    txt.dataset.from = from; txt.dataset.to = to; txt.dataset.idx = i;
    svg.appendChild(txt);
  });
}

function highlightNode(nodeId) {
  const connected = new Set([nodeId]);
  edges.forEach(([from, to]) => {
    if (from === nodeId) connected.add(to);
    if (to === nodeId) connected.add(from);
  });
  document.querySelectorAll('.node[data-node]').forEach(el => {
    if (connected.has(el.dataset.node)) {
      el.classList.remove('faded'); el.classList.add('active');
    } else {
      el.classList.add('faded'); el.classList.remove('active');
    }
  });
  svg.querySelectorAll('line').forEach(l => {
    if (l.dataset.from === nodeId || l.dataset.to === nodeId) {
      l.classList.add('highlight'); l.classList.remove('hidden');
    } else {
      l.classList.add('hidden'); l.classList.remove('highlight');
    }
  });
  svg.querySelectorAll('text').forEach(t => {
    if (t.dataset.from === nodeId || t.dataset.to === nodeId) {
      t.classList.add('highlight'); t.classList.remove('hidden');
    } else {
      t.classList.add('hidden'); t.classList.remove('highlight');
    }
  });
}

function clearHighlight() {
  document.querySelectorAll('.node[data-node]').forEach(el => {
    el.classList.remove('faded', 'active');
  });
  svg.querySelectorAll('line').forEach(l => l.classList.remove('highlight', 'hidden'));
  svg.querySelectorAll('text').forEach(t => t.classList.remove('highlight', 'hidden'));
}

function onNodeEnter(el, event) { highlightNode(el.dataset.node); showTip(el, event); }
function onNodeLeave(el) { clearHighlight(); hideTip(); }

function showTip(el, event) {
  const html = el.getAttribute('data-tip');
  if (!html) return;
  tip.innerHTML = html;
  tip.classList.add('visible');
  positionTip(event);
}
function hideTip() { tip.classList.remove('visible'); }

document.addEventListener('mousemove', (e) => {
  if (tip.classList.contains('visible')) positionTip(e);
});
function positionTip(e) {
  const rect = graph.getBoundingClientRect();
  let x = e.clientX - rect.left + 16;
  let y = e.clientY - rect.top + 16;
  if (x + 310 > rect.width) x = e.clientX - rect.left - 316;
  if (y + 180 > rect.height) y = e.clientY - rect.top - 180;
  tip.style.left = x + 'px';
  tip.style.top = y + 'px';
}

renderEdges();
window.addEventListener('resize', renderEdges);
</script>
</body>
</html>
```

#### How to Adapt This Template

Only three things change per diagram:

1. **Nodes** — add `<div class="node cat-COLOR">` elements inside `#graph`. Position with `left`/`top` in
   `style`. Set `data-node` (unique ID) and `data-tip` (HTML tooltip). Wire up `onmouseenter`/`onmouseleave`.
2. **Edges** — populate the `edges` JS array with `[from, to, label, color]` tuples.
3. **Categories** — pick which `cat-*` classes to use (or add new ones following the same pattern).

The engine code below the edge definitions never changes.

#### Node Positioning Tips

- The graph container is conceptually 1100x700. Position nodes in spatial groups that reflect logical grouping.
- Put related nodes in columns or clusters. Use corner `group-label` spans to name the regions.
- Leave ~60px minimum between nodes to avoid overlap.
- Test by opening in a browser and hovering each node — verify connections highlight correctly.

#### Tooltip Content Tips

- Use `<h4>` for the title, `<p>` for details, `<strong>` for labels.
- Use `<span class='badge' style='background:COLOR;color:TEXT'>` for inline tags.
- Keep tooltips focused: specs, sub-components, key facts. Not paragraphs.

---

### Type 2: Pipeline Flow (collapsible step cards)

**When to use:** Sequential processes, data pipelines, build/deploy flows, "what happens in order?",
any system where things flow through stages.

**What makes it special:** Information is layered — you see the high-level flow at a glance (step names,
one-line descriptions, service badges), then click any step to expand its details (what goes in, what comes
out, which services it touches, key file references). Keeps the overview clean while letting you drill into
any step.

#### Architecture

A vertical stack of cards with down-arrow dividers:

1. **Step header** (always visible) — colored number circle, name, one-line description, service badges, chevron.
2. **Step body** (hidden, click to toggle) — detailed explanation, 2-column input/output grid, service tags,
   key file references.
3. **Toggle logic** — `onclick="toggle(this)"` flips `.open` class on header (rotates chevron) and body
   (shows/hides content).

#### Reference Implementation

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>[TITLE]</title>
<style>
  :root {
    --bg: #f8fafc; --card: #ffffff; --border: #e2e8f0;
    --text: #1e293b; --muted: #64748b; --subtle: #94a3b8;
    --blue: #3b82f6; --green: #22c55e; --orange: #f97316;
    --purple: #8b5cf6; --amber: #f59e0b; --red: #ef4444;
    --teal: #14b8a6; --indigo: #6366f1;
    --shadow: 0 1px 3px rgba(0,0,0,0.08);
    --radius: 10px;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: system-ui, -apple-system, sans-serif;
    background: var(--bg); color: var(--text);
    padding: 24px; max-width: 1000px; margin: 0 auto;
  }
  h1 { font-size: 1.5rem; margin-bottom: 4px; }
  .subtitle { color: var(--muted); font-size: 0.85rem; margin-bottom: 20px; }

  .pipeline { display: flex; flex-direction: column; gap: 0; }

  /* ── Step card ── */
  .step {
    background: var(--card); border-radius: var(--radius);
    box-shadow: var(--shadow); border: 1px solid var(--border);
    overflow: hidden; position: relative;
  }
  .step-header {
    padding: 14px 20px; cursor: pointer; display: flex;
    align-items: center; gap: 12px; user-select: none;
  }
  .step-header:hover { background: #f1f5f9; }
  .step-num {
    width: 32px; height: 32px; border-radius: 50%; display: flex;
    align-items: center; justify-content: center; font-weight: 700;
    font-size: 0.85rem; color: white; flex-shrink: 0;
  }
  .step-info { flex: 1; }
  .step-info h3 { font-size: 0.95rem; font-weight: 600; }
  .step-info .desc { font-size: 0.8rem; color: var(--muted); }
  .step-meta { display: flex; gap: 6px; align-items: center; }
  .badge {
    font-size: 0.7rem; padding: 2px 8px; border-radius: 20px; font-weight: 500;
  }
  .chevron { transition: transform 0.2s; font-size: 0.8rem; color: var(--subtle); }
  .step-header.open .chevron { transform: rotate(90deg); }

  /* ── Step body (expandable) ── */
  .step-body { padding: 0 20px 16px 64px; display: none; }
  .step-body.open { display: block; }
  .step-body p {
    font-size: 0.82rem; color: var(--muted); line-height: 1.5; margin-bottom: 8px;
  }

  /* ── Input / Output grid ── */
  .io-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin: 8px 0; }
  .io-box { border-radius: 8px; padding: 10px 12px; }
  .io-box h4 {
    font-size: 0.72rem; text-transform: uppercase;
    letter-spacing: 0.04em; margin-bottom: 4px;
  }
  .io-box ul { list-style: none; font-size: 0.8rem; }
  .io-box li { padding: 2px 0; }
  .io-box li::before {
    content: ""; display: inline-block; width: 6px; height: 6px;
    border-radius: 50%; margin-right: 6px;
  }
  .input-box { background: #f0fdf4; }
  .input-box h4 { color: #166534; }
  .input-box li::before { background: var(--green); }
  .output-box { background: #eff6ff; }
  .output-box h4 { color: #1e40af; }
  .output-box li::before { background: var(--blue); }

  /* ── Service tags ── */
  .service-tags { display: flex; gap: 4px; flex-wrap: wrap; margin-top: 8px; }
  .svc-tag {
    font-size: 0.72rem; padding: 2px 8px; border-radius: 20px; font-weight: 500;
  }

  /* ── Arrow divider ── */
  .arrow-down {
    text-align: center; padding: 4px 0; font-size: 1.4rem;
    color: var(--subtle); line-height: 1;
  }

  code {
    font-size: 0.78rem; background: #f1f5f9;
    padding: 1px 5px; border-radius: 3px;
  }
</style>
</head>
<body>

<h1>[TITLE]</h1>
<p class="subtitle">[Subtitle — what this flow shows]. Click each step to expand.</p>

<div class="pipeline">

  <!-- Step 1 -->
  <div class="step">
    <div class="step-header" onclick="toggle(this)">
      <div class="step-num" style="background:var(--green)">1</div>
      <div class="step-info">
        <h3>[Step Name]</h3>
        <div class="desc">[One-line description]</div>
      </div>
      <div class="step-meta">
        <span class="badge" style="background:#dcfce7;color:#166534">[badge]</span>
      </div>
      <span class="chevron">&#9654;</span>
    </div>
    <div class="step-body">
      <p>[Detailed explanation of what this step does and why.]</p>
      <div class="io-grid">
        <div class="io-box input-box">
          <h4>Input</h4>
          <ul>
            <li>[What this step reads]</li>
          </ul>
        </div>
        <div class="io-box output-box">
          <h4>Output</h4>
          <ul>
            <li>[What this step produces]</li>
          </ul>
        </div>
      </div>
      <div class="service-tags">
        <span class="svc-tag" style="background:#dbeafe;color:#1e40af">[Service]</span>
      </div>
      <p style="margin-top:8px"><strong>Key files:</strong> <code>[path/to/file]</code></p>
    </div>
  </div>

  <div class="arrow-down">&darr;</div>

  <!-- Step 2, 3, ... follow the same pattern -->

</div>

<script>
function toggle(header) {
  header.classList.toggle('open');
  header.nextElementSibling.classList.toggle('open');
}
</script>
</body>
</html>
```

#### How to Adapt This Template

1. **Steps** — add one `<div class="step">` block per stage. Precede each (except the first) with
   `<div class="arrow-down">&darr;</div>`.
2. **Step colors** — set `background:var(--COLOR)` on `.step-num`. Use different colors to visually
   distinguish phases.
3. **Badges** — add `<span class="badge">` elements in `.step-meta` for key attributes (service name,
   mode, count).
4. **Input/Output** — list what the step reads and writes. Be specific (table names, file paths, API
   endpoints — not vague labels).
5. **Service tags** — small pills showing which external services the step touches.
6. **Key files** — `<code>` references to the source files that implement this step.

#### Badge Color Reference

Common badge color pairings (background / text):
- Green: `#dcfce7` / `#166534`
- Blue: `#dbeafe` / `#1e40af`
- Amber: `#fef3c7` / `#92400e`
- Purple: `#ede9fe` / `#6d28d9`
- Orange: `#ffedd5` / `#c2410c`
- Red: `#fee2e2` / `#991b1b`
- Teal: `#ccfbf1` / `#115e59`

---

## Composing Diagrams into Pages

The two diagram types above are building blocks. For richer visualizations, embed them into a page.

### Session Summary

**When:** End of a task, batch completion, or "what did we do?"

A scrollable page that tells the story of what was done and *why*.

**Section order:**

1. **Files touched** — at the top. Group by category (production code, workflows, config). For each file,
   show *what* changed and *why* — not just "+3/-2 lines" but "added retry logic to handle transient API
   failures." Use concept tag badges to visually categorize.

2. **Per-concept breakdown** — organize by the *problem being solved*, not by ticket. Each concept card:
   - **Text first** (above the diagram): 2-4 sentences on what problem existed, why this approach, gotchas.
   - **Diagram below** (full width): embed a Topology Graph or Pipeline Flow showing what changed and how
     it connects. The diagram MUST span the full width of the card — NEVER side-by-side with text.

   **Layout rule: NEVER use side-by-side layout for diagram + text.** Always stack vertically.

3. **Stats bar** — small, at the bottom. Files changed, lines added/removed.

4. **Validation status** — what passed, what's pending.

**Do NOT include:** commit logs, SHAs, raw line counts without context, ticket numbers as primary organizers.

### Before/After Comparison

**When:** Explaining what a change accomplished.

Two diagrams (same type) side by side or stacked, showing old state and new state. Use color to highlight
what was removed (red nodes/edges), added (green), or modified (amber). This is powerful for refactors
and architecture changes.

### Single Focused Diagram

**When:** User asks for one specific thing — "diagram the deploy flow", "show me the service dependencies."

Generate just one Topology Graph or Pipeline Flow. No surrounding dashboard. Still persist it.

---

## How to Build It

### Step 1: Analyze What to Visualize

Look at the conversation context. What does the user need to understand? Sources:
- Recent git log / diff for what changed
- The conversation itself for what was discussed
- The codebase for architecture questions

Don't visualize everything. Identify the 2-3 most important things and focus on those.

### Step 2: Choose Diagram Type

- Things with **connections between entities** → Topology Graph (hover-to-isolate)
- Things with **sequential stages** → Pipeline Flow (collapsible cards)
- Things with **both** → use both, embedded in a session summary page

### Step 3: Research the Content

Before generating HTML, understand what you're diagramming. Read the relevant code, config, or docs.
For a topology graph, identify:
- Every entity (node) and its category
- Every connection (edge) with a descriptive label
- What details belong in each tooltip

For a pipeline flow, identify:
- Every stage in order
- What each stage reads and produces
- Which services it touches
- Which source files implement it

### Step 4: Generate the HTML

Build the self-contained HTML file using the reference implementations above. Adapt the nodes/edges/steps
for your specific content. Test mentally: does every node have a `data-node` and `data-tip`? Does every
edge reference valid node IDs? Are steps numbered sequentially?

### Step 5: Save the File

Save to `~/visualizations/` with a descriptive filename:

```
~/visualizations/YYYY-MM-DD-<short-description>.html
```

Examples:
- `2026-04-02-infra-topology.html`
- `2026-04-02-deploy-pipeline.html`
- `2026-04-02-api-dependency-graph.html`

### Step 6: Render in Chrome

Use the Chrome MCP tools to display the visualization:

1. Start a local HTTP server:
   `cd ~/visualizations && python3 -m http.server 8765 &>/dev/null &`
   Run this in the background.
2. Get browser context:
   `mcp__claude-in-chrome__tabs_context_mcp` (createIfEmpty: true)
3. Create a new tab:
   `mcp__claude-in-chrome__tabs_create_mcp`
4. Navigate to the file:
   `mcp__claude-in-chrome__navigate` (url: `http://localhost:8765/<filename>.html`, tabId: new-tab-id)
5. Take a screenshot to confirm it rendered:
   `mcp__claude-in-chrome__computer` (action: screenshot, tabId: tab-id)
6. Tell the user: "Dashboard is live in your browser. Also saved to `~/visualizations/<filename>` for later."

If Chrome MCP tools are unavailable, still generate and save the HTML file, and tell the user where to find it.

---

## Verification Checklist

### Topology Graph
- [ ] Every node has a unique `data-node` value
- [ ] Every node has `onmouseenter="onNodeEnter(this,event)"` and `onmouseleave="onNodeLeave(this)"`
- [ ] Every node has a `data-tip` attribute with descriptive HTML
- [ ] Every edge references valid `data-node` IDs on both ends
- [ ] No orphan nodes (every node has at least one edge)
- [ ] Open in browser: hovering each node fades unrelated nodes and shows only its connections
- [ ] Group labels accurately describe the spatial regions

### Pipeline Flow
- [ ] Steps are numbered sequentially (1, 2, 3, ...)
- [ ] Each step header has `onclick="toggle(this)"`
- [ ] Arrow-down dividers appear between all steps
- [ ] Each step's input/output accurately reflects the actual system
- [ ] Service tags match actual integrations
- [ ] Open in browser: clicking each step expands its details
