---
description: ""
covers: []
updated: 2026-04-18
---

# PR Tour Structure — when and how to break up sections

The companion guide to `TEMPLATE.html`. Answers two questions: **how do I decide
which sections a tour gets, and how do I decide when a section needs to be
split into h3 subsections?**

For the visual rules (CSS, color palette, SVG conventions), see `TEMPLATE.html`
— the CSS comments and the SVG color table are authoritative.

---

## The section hierarchy

Every tour uses the same three-level structure:

| Level | Tag | Role | Required? |
|-------|-----|------|-----------|
| Page | `<h1>` | One per tour, in `<header>`. The PR/branch title. | Yes |
| Section | `<h2>` | Top-level navigable unit. Renders as a card. | Yes |
| Subsection | `<h3>` | Navigable anchor inside a section. Renders as a banner. | Situational |

**Non-navigable h3s exist** (diagram BEFORE/AFTER labels are h3 with inline
styles). Those **do not get IDs** and **do not appear in the TOC**. Only "real"
subsection h3s are navigable.

---

## The three mandatory sections

Every tour has these, in this order:

1. **Goals** — what the PR sets out to do. Sub-headed bullets, not prose.
   Default h3s: `What` / `In scope` / `Out of scope`. Swap "In scope" for a
   more specific framing if the PR body uses one (e.g. "Ticket-gate
   deliverables").
2. **Why** — broader initiative + slicing rationale. Default h3s: `Broader
   initiative` / `Why slice it this way`.
3. **Tests** — coverage additions, rewrites, deletions, gate state. Default
   h3s: `New tests` / `Rewrites` / `Gate`.

These always exist. They anchor the reader — same skeleton across every tour,
so eyes know where to land.

---

## The content sections — the part that varies

Between Why and Tests sits the content. The shape depends on the PR:

### Pattern A — single-theme PR (one section)

If the PR does one thing (one feature, one bug fix, one refactor):

```
<section id="implementation">
  <h2>Implementation</h2>
  ...h3s for each theme...
</section>
```

### Pattern B — multi-phase PR (one section per phase)

If the PR spans multiple deliberate slices (Phase 5a / 5b / 5c / Polish, or
"infrastructure / UI / migration"), each slice is its own top-level section:

```
<section id="phase-5a">...</section>
<section id="phase-5b">...</section>
<section id="phase-5c">...</section>
<section id="polish">...</section>
```

### Pattern C — small PR (one section, no h3s)

If the PR is small (one concept, <5 commits), the content section may have
prose, one diagram, one code block, and no h3s. In that case the TOC entry is
a flat link with no nested list.

The right pattern is usually obvious from the PR body's own structure. Mirror it.

---

## When to split a section into h3 subsections

Four heuristics, in priority order. Any one is sufficient to create an h3.

### 1. The diagram heuristic

**If you wrote a diagram for X, there is probably an h3 whose topic is X.**

Diagrams anchor subsections visually. Each non-orientation diagram lives
"under" an h3 that names what the diagram is about. If you have 4 diagrams in
a section with no h3s, the section is under-structured.

Exception: orientation diagrams (one per section, showing the whole
section's shape) live at the section root, above the first h3.

### 2. The commit-group heuristic

**If commits naturally cluster into 3-5 themes, each cluster is an h3
candidate.**

Look at commit subjects. They almost always group themselves: tag/summarize/
embed/archive is four groups; "invariants" / "performance" / "defensive
wrappers" is three. The commit clustering becomes the h3 structure.

This is not the same as marching through commits chronologically — the h3s
are themes, not timelines. Commits within a theme can interleave
chronologically with commits from other themes.

### 3. The "would I jump here?" heuristic

**If the TOC showed "Section X", would a reader want a direct link to a
specific part of it?**

Imagine Derek re-reading on his phone three weeks later. He remembers the
phase, but wants to jump straight to "the atomicity seam migration" without
scrolling. If that's plausible, it's an h3.

Subsection names should pass the scannability test: short, descriptive,
surviveable on a mobile TOC line. Three to six words usually. Technical
terms in the name are fine (they're what the reader is searching for).

### 4. The scroll-length heuristic

**If a section is longer than about two phone screens without a heading,
you're missing an h3.**

This is a fallback for when the other three don't trigger cleanly. Readers
need at least one navigable anchor per ~2 screens of content to re-orient.

---

## What an h3 subsection must contain

Every h3 is a promise that there's something concrete here. An h3 followed
by one paragraph is a waste. Each h3 must pair its heading with **at least
one** of:

- A diagram (inline SVG) that illustrates the topic
- A `<details>` block with real code from the diff
- A `<blockquote>` callout that captures a non-obvious gotcha

Prose is scaffolding around those anchors, not the anchor itself. If all you
can write for an h3 is prose, it's probably not a distinct subsection — fold
it into the previous h3 or the section intro.

---

## The TOC contract

**Every h2 and every navigable h3 in the document MUST appear in the TOC.**
This is not optional. Orphan headings — ones with IDs but no TOC entries, or
vice versa — are broken links in practice because the reader can't discover
them.

Checklist before shipping a tour:

- [ ] Every `<section>` has an `id` attribute.
- [ ] Every navigable `<h3>` has an `id` attribute (not the BEFORE/AFTER h3s
      inside diagrams — those have inline styles and no IDs).
- [ ] Every id is referenced by a `<nav class="toc">` entry.
- [ ] No duplicate ids in the document (breaks anchor jumps).
- [ ] Every TOC entry corresponds to a real id (no 404s within the page).

---

## Paradigm summary — the section lifecycle

1. **Identify the section type.** Is this Goals, Why, Tests (fixed), or a
   content section?
2. **For content sections, pick the pattern.** Single-theme, multi-phase, or
   small PR?
3. **Write the section intro.** One or two sentences after the h2. What did
   this section accomplish? Why does it exist as a separate unit?
4. **Decide the h3s.** Apply the four heuristics. Err on the side of more h3s
   — a cluttered TOC is less bad than a wall of unstructured content.
5. **Attach artifacts to each h3.** Every h3 gets at least one diagram,
   details block, or blockquote.
6. **Update the TOC.** Add entries for every section and every h3. Sanity-check
   that every id is reachable from the TOC.
7. **Read the final file on a phone-width viewport** (browser devtools
   responsive mode, ~400px wide). If any section feels like a wall, you need
   more h3s. If any h3 feels empty, fold it back in.

---

## Anti-patterns

- **Wall-of-prose sections** — content sections with no h3s for >2 screens.
  Add h3s.
- **Orphan h3s** — heading exists but has no TOC entry or no id. Either add
  both or remove the h3.
- **Decorative h3s** — headings that break up prose without introducing new
  content. Either attach an anchor (diagram/details/blockquote) or delete.
- **Chronological h3s** — headings named "Monday" / "Tuesday" / "Week 1".
  Rename by theme. The reader doesn't care when it happened.
- **Paraphrased diagrams** — diagrams that restate the h3 heading in picture
  form. A good diagram teaches something the heading alone can't.
- **Diagram-heavy with prose starvation** — four diagrams in a row with one
  sentence between them. Prose is the connective tissue; without it, the
  reader sees pictures but doesn't know why they're there.
- **Matching every section color to its theme** — using different accent
  colors per section (blue for 5a, green for 5b, etc.) looks jarring at
  page-length. Stick with one accent color across all sections. Phase color
  cues belong inside diagrams, not in section chrome.

---

## Multi-agent authoring note

For large PRs (>20 commits, >4 distinct slices), consider generating each
content section with a separate agent in parallel. Each agent reads only the
files relevant to its slice, produces its `<section>` fragment with diagrams
and prose, and you concatenate them into the shared skeleton.

If you do this, the shared SVG color palette (in the CSS header comment of
`TEMPLATE.html`) and the layout rules (from the parent SKILL.md) must be
passed to every agent verbatim — otherwise the diagrams will drift stylistically
between sections.

The `.v2-note` block in the template exists for this case: flag to the reader
that voice may vary slightly between sections.
