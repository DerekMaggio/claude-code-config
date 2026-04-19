---
name: pr-tour
description: Guided, sectioned walkthrough of a PR (or current branch diff) to re-orient yourself days/weeks after the work was done. Produces a saved self-contained HTML artifact for later phone reading (works fully offline). Use when reviewing AI-written PRs you've forgotten the details of.
argument-hint: "[<PR# [PR# ...] | URL> | (no arg = current branch vs main)]"
allowed-tools: Bash(git:*), Bash(gh:*), Bash(mkdir:*), AskUserQuestion, Read, Write
updated: 2026-04-18
---

# PR Tour

Generates a self-contained HTML artifact (`docs/pr-tours/<...>.html`) with five sections — Goals, Why, Diagrams, Implementation, Tests — that Derek can re-read on his phone days or weeks later, fully offline. After the file is written, optionally walks through any section inline for immediate re-orientation.

## Use when

- Derek has come back to a PR days/weeks after it was written (by him or by an agent) and has lost the thread.
- He wants a narrative re-orientation, not a diff review.
- He wants the walkthrough preserved for later mobile re-reading.

## Do not use when

- The PR is being created right now and needs a description → use `/pr-generator`.
- The user wants a one-off diagram of architecture → use `/visualize`.
- The user wants code review / feedback → this skill is explanatory, not evaluative.

## Runtime Workflow

### Step 1 — Parse argument(s), determine mode

Inspect the argument(s) passed to the skill.

- Single arg matches `^\d+$` or contains `github.com/*/pull/\d+` → **PR mode**. Extract the PR number.
- Multiple space-separated PR numbers / URLs (e.g. `/pr-tour 517 519 520 521`) → **Batch mode**. Extract all PR numbers. Treat as N independent tours generated in parallel, with a single consolidated walkthrough menu at the end (see Step 5).
- No argument → **Branch mode**. Range is `origin/main..HEAD` (fall back to `origin/master` if `origin/main` missing).

**Early exit errors:**
```bash
# Not inside a git repo
git rev-parse --show-toplevel >/dev/null 2>&1 \
  || { echo "Run /pr-tour from inside a git repo"; exit 1; }

# Branch mode + on main itself
BRANCH=$(git rev-parse --abbrev-ref HEAD)
[ "$BRANCH" = "main" ] || [ "$BRANCH" = "master" ] \
  && echo "Can't tour main itself; pass a PR number or check out a feature branch."

# Branch mode + no commits ahead
[ "$(git rev-list --count origin/main..HEAD)" = "0" ] \
  && echo "No commits ahead of main; nothing to tour."
```

### Step 2 — Gather sources (silent)

**Do not echo raw output to the user** in this step. Load into working memory only.

**Cwd-independence — always pass `-R <owner/repo>`** to every `gh` call. The skill may be invoked from a staging directory (e.g. `/tmp/pr-tour`) that isn't inside a git repo, which otherwise breaks `gh pr view` with `fatal: not a git repository`. Extract the owner/repo from the PR URL, or from `git -C <path> remote get-url origin` if a repo path is known.

**"Pull the code changes" disambiguation** — if the user tells you to "pull" the PR, it has two meanings, and both matter:
1. **Sync the branch locally** — `gt sync` or `git fetch origin <headRefName>` — makes your local view match GitHub.
2. **Pull the diff into context** — run `gh pr diff ...` below and actually read the output, not just the file paths.

Do both. Skipping #2 is the single most common failure mode for this skill (see Step 3).

**PR mode (per PR — in batch mode, run all PRs in parallel):**
```bash
# Metadata
gh pr view <PR> -R <owner/repo> --json number,title,headRefName,baseRefName,body,labels,closingIssuesReferences,commits,files

# Diff — READ THE FULL OUTPUT INTO WORKING MEMORY. Not just the file list.
gh pr diff <PR> -R <owner/repo>

# For each entry in closingIssuesReferences:
gh issue view <num> -R <owner/repo> --json title,body,labels
```

**Branch mode:**
```bash
git log origin/main..HEAD --pretty=format:'%H%x09%s%x09%an%x09%aI%n%b%n---'
git diff origin/main..HEAD
git diff --stat origin/main..HEAD
```

Linked-ticket inference (branch mode): scan branch name and commit subjects for these patterns and fetch via `gh issue view` if the repo is under `DerekMaggio/`:
- `#NNN`, `(#NNN)`, `[#NNN]`
- `Fixes #NNN`, `Closes #NNN`, `Resolves #NNN`
- `JIRA-NNN` style (any uppercase prefix + number)

**Repo detection** (for filename + routing):
```bash
git remote get-url origin
```

### Step 3 — Generate all five sections (silent)

Claude internally generates content for all five sections in one pass. Do **not** echo any of this to the user yet. These bodies populate the HTML in Step 4.

**Non-negotiable for the Implementation section:** read the *actual diff content* gathered in Step 2 — function signatures, method bodies, struct definitions, imports — as they appear in the code. Do **not** paraphrase the PR body. The PR body tells you *what was done*; the diff tells you *what the code looks like*. The Implementation `<details>` blocks in the HTML must contain real code snippets quoted from the diff, not descriptions of what the code probably does.

If the Implementation section was written without reading the diff, the tour has failed silently. This has happened in practice — the user catches it with *"did you pull the code changes"* and the whole section gets redone.

Section definitions are in **Section content** below. In batch mode, generate all N tours' section content before moving to Step 4.

### Step 4 — Write the HTML artifact

**Paths:**
```bash
REPO_ROOT=$(git rev-parse --show-toplevel)
OUT_DIR="${REPO_ROOT}/docs/pr-tours"
mkdir -p "$OUT_DIR"
DATE=$(date +%Y-%m-%d)
```

- PR mode filename: `pr-<N>-<DATE>.html`
- Branch mode filename: `branch-<sanitized-branch>-<DATE>.html`
- **Batch mode:** write N files in parallel, one per PR. Filenames follow the PR mode pattern.

**Branch name sanitization:**
```bash
SAFE_BRANCH=$(git rev-parse --abbrev-ref HEAD | tr -cd '[:alnum:]-' | cut -c1-50)
```

Same-day re-runs overwrite. Different day → new file (both preserved).

### Step 5 — Report & offer walkthrough

Report to the user in one short block:
- Absolute path(s) of the file(s) written — list all N in batch mode
- File size(s) (`ls -la` is fine)
- One-line reminder: *"Self-contained — works fully offline. Transfer to phone via whatever method you prefer."*

**Single PR / Branch mode** — invoke `AskUserQuestion`:

> Walk through a section here, or done?

Options (six): **Goals**, **Why**, **Diagrams**, **Implementation**, **Tests**, **Done** — finish without walkthrough.

If the user picks **Done**, stop.

**Batch mode (2+ PRs)** — a per-section walkthrough × N PRs would be overwhelming. Collapse to a tour-picker instead:

> Walk through which tour, or done?

Options: one per PR (e.g. **#517**, **#519**, **#520**, **#521**), plus **Done**.

If the user picks a PR, enter that tour's single-PR menu (Goals / Why / … / Done). When they hit Done on the section menu, return to the batch-level picker so they can pick another tour. Done at the batch level exits.

If the user picks **Done**, stop. The files are already on disk.

### Step 6 — Walkthrough loop (optional)

If the user picked a section in Step 5:

1. Render that section's prose inline in the conversation — the same narrative that's in the HTML, casual first-person-plural voice ("we did X because Y"), not clinical "the PR adds X".
2. Invoke `AskUserQuestion` with:
   - **Dive deeper** — expand the current section with more prose and relevant code, then re-prompt with these same two options
   - **Back to menu** — return to the Step 5 menu (**Done** remains the exit)
3. Loop until the user picks **Done**.

The HTML file written in Step 4 does **not** update based on walkthrough content. The chat walkthrough is ephemeral re-orientation; the file is the durable artifact.

## Section content

These are the five sections that fill the HTML. Generate all five in Step 3; render individually on request in Step 6.

### Goals

**Default shape: sub-headed bullets, not prose paragraphs.** The user scans this section — it needs to be scannable. Prose only when a bullet would be a single lie-flat thought that doesn't fit as a bullet.

Typical structure:

```html
<h3>What</h3>
<p>One-sentence summary of the change.</p>

<h3>In scope</h3>
<ul>
  <li>...</li>
</ul>

<h3>Out of scope</h3>
<ul>
  <li>... — link to the stacking PR if relevant</li>
</ul>
```

Swap "In scope" for more specific framing when the PR description uses one (e.g. "Fall-out", "Ticket-gate deliverables").

**Source priority:** linked ticket body → commit messages → diff signals.

If no linked ticket is found and one might have been expected (e.g. the branch name suggests one), explicitly note: *"No linked ticket found — goals inferred from commit messages and the diff."*

### Why

Same shape as Goals: **sub-headed bullets, not prose.**

Typical structure:

```html
<h3>Broader initiative</h3>
<ul>
  <li>Link to the parent ticket / milestone</li>
  <li>One-line description of the broader arc</li>
  <li>Phase breakdown, if this is part of a series (e.g. "Phase 5 of items migration")</li>
</ul>

<h3>Why this slice first / Why split this way</h3>
<ul>
  <li>...</li>
</ul>
```

**Source priority:** ticket body → recent repo activity (`git log --oneline -20 origin/main`) → cross-linked PRs in the ticket.

Keep it short. This is context, not a lecture.

### Diagrams

Decide whether a diagram helps:

- **Change touches >1 distinct component or stage** → generate one diagram (or two if before/after is clearer).
- **Change is single-component, docs-only, or one-function fix** → say explicitly *"No diagram needed — single-component change."* Do not fabricate a diagram.
- **>50 files changed** → generate an architectural-intent diagram, not a file inventory. Note: *"Diff is large; diagram shows architecture, not every file."*

All diagrams are inline SVG (see **Diagram patterns** below). Hard cap: 3 diagrams per tour.

**If the user wants desktop-interactive diagrams** (pan, zoom, clickable nodes), hand off to `/visualize` instead. `/pr-tour` diagrams are static because the tour is a mobile-read artifact — don't mix the two.

**Critical — layout discipline:** inline SVG is easy to misauthor. Read **Diagram layout rules** and the **Verification checklist** at the top of the Diagram Patterns section below *before* writing any `<svg>`. Skipping them produces diagrams where edges pass through unrelated boxes or labels sit in arrow paths — and that has happened in practice.

### Implementation

Commit-by-commit narrative. For each commit, answer:

- **Goal** — what this commit was for
- **How** — the actual approach taken
- **Decisions** — any tradeoffs or choices worth noting
- **Ordering** — why this commit came before/after its neighbors (if not obvious)

Code and data-structure specifics go inside `<details>` blocks so the prose reads clean. Short asides (one-liner observations, gotchas) go as `> ` blockquotes.

If >10 commits, group by theme and treat each group as one "commit" for narrative purposes. Don't march through 20+ commits linearly.

### Tests

Standalone section — does not inherit from implementation.

Identify test files via path heuristics:
- `tests/`, `test/`, `__tests__/`, `spec/`
- `*_test.py`, `*_test.go`
- `*.test.ts`, `*.test.tsx`, `*.test.js`
- `*.spec.ts`, `*.spec.js`

Structure:
- Group by feature or behavior
- Bullets for behaviors/states/transformations tested
- 1–2 sentences per test case summarizing what it asserts

**If no tests changed, say so explicitly:** *"No tests changed in this PR."* Do not fabricate coverage claims.

## HTML Skeleton (copy-paste, fill section bodies)

Use this skeleton verbatim. Fill in only:
- `<title>` and `<h1>` with the PR title
- The `.meta` line with date / commit count / file count
- The `<section>` bodies with generated prose + SVG
- `<details>` blocks per commit in `#implementation`

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PR Tour — {{REPO}}#{{N}}: {{TITLE}}</title>
<style>
  :root {
    --bg: #fafaf7;
    --surface: #ffffff;
    --text: #1a1a1a;
    --muted: #666;
    --subtle: #999;
    --border: #e4e4df;
    --accent: #2a5490;
    --code-bg: #f4f2ec;
    --callout-bg: #f7f4ea;
    --callout-border: #c9a227;
  }
  * { box-sizing: border-box; }
  html { -webkit-text-size-adjust: 100%; }
  body {
    margin: 0;
    padding: 0;
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                 "Helvetica Neue", Arial, sans-serif;
    font-size: 17px;
    line-height: 1.65;
  }
  main, header {
    max-width: 780px;
    margin: 0 auto;
    padding: 24px 20px;
  }
  header { border-bottom: 1px solid var(--border); }
  header h1 { font-size: 1.5rem; margin: 0 0 6px; line-height: 1.3; }
  .meta { color: var(--muted); font-size: 0.88rem; margin: 0 0 16px; }
  nav.toc { font-size: 0.92rem; }
  nav.toc a {
    display: inline-block;
    margin-right: 14px;
    color: var(--accent);
    text-decoration: none;
  }
  nav.toc a:hover { text-decoration: underline; }

  section {
    padding: 28px 0;
    border-bottom: 1px solid var(--border);
  }
  section:last-child { border-bottom: 0; }
  section h2 {
    font-size: 1.25rem;
    margin: 0 0 14px;
    color: var(--accent);
  }
  section p { margin: 0 0 14px; }

  code {
    font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
    font-size: 0.92em;
    background: var(--code-bg);
    padding: 1px 5px;
    border-radius: 3px;
  }
  pre {
    background: var(--code-bg);
    border-radius: 6px;
    padding: 12px 14px;
    overflow-x: auto;
    font-size: 0.88rem;
    line-height: 1.5;
  }
  pre code { background: transparent; padding: 0; }

  blockquote {
    margin: 12px 0;
    padding: 10px 14px;
    background: var(--callout-bg);
    border-left: 3px solid var(--callout-border);
    color: #5b4a10;
    font-size: 0.95rem;
  }
  blockquote p:last-child { margin-bottom: 0; }

  details {
    margin: 10px 0;
    padding: 8px 12px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 6px;
  }
  details[open] { padding-bottom: 12px; }
  details summary {
    cursor: pointer;
    font-weight: 600;
    color: var(--accent);
    list-style: none;
    padding: 4px 0;
  }
  details summary::-webkit-details-marker { display: none; }
  details summary::before {
    content: "▸ ";
    display: inline-block;
    width: 1.1em;
    color: var(--subtle);
  }
  details[open] summary::before { content: "▾ "; }

  .diagram-wrap {
    margin: 16px 0 20px;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }
  .diagram-wrap svg {
    display: block;
    max-width: 100%;
    height: auto;
  }
  .diagram-caption {
    font-size: 0.85rem;
    color: var(--muted);
    text-align: center;
    margin-top: 4px;
  }

  .commit-sha {
    font-family: ui-monospace, monospace;
    font-size: 0.85rem;
    color: var(--subtle);
    margin-right: 6px;
  }

  @media (min-width: 1100px) {
    nav.toc {
      position: fixed;
      top: 24px;
      right: calc((100vw - 780px) / 2 - 200px);
      width: 180px;
      display: flex;
      flex-direction: column;
    }
    nav.toc a { margin: 4px 0; font-size: 0.85rem; }
  }

  @media print {
    body { background: white; font-size: 12pt; }
    nav.toc { display: none; }
    details[open] { page-break-inside: avoid; }
  }
</style>
</head>
<body>
<header>
  <h1>PR Tour: {{REPO}}#{{N}} — {{TITLE}}</h1>
  <p class="meta">Generated {{DATE}} · {{COMMIT_COUNT}} commits · {{FILE_COUNT}} files</p>
  <nav class="toc">
    <a href="#goals">Goals</a>
    <a href="#why">Why</a>
    <a href="#diagrams">Diagrams</a>
    <a href="#implementation">Implementation</a>
    <a href="#tests">Tests</a>
  </nav>
</header>
<main>
  <section id="goals">
    <h2>Goals</h2>
    <!-- 1–3 short paragraphs -->
  </section>

  <section id="why">
    <h2>Why</h2>
    <!-- context for now / broader initiative -->
  </section>

  <section id="diagrams">
    <h2>Diagrams</h2>
    <!-- one or more .diagram-wrap blocks, OR a short "no diagram needed" note -->
  </section>

  <section id="implementation">
    <h2>Implementation</h2>
    <!-- one <details> block per commit (or commit-group if >10) -->
  </section>

  <section id="tests">
    <h2>Tests</h2>
    <!-- grouped by feature, or "No tests changed in this PR." -->
  </section>
</main>
</body>
</html>
```

## Diagram Patterns (inline SVG — no JS)

Pick the pattern that matches the content. Adapt coordinates as needed — these are starting points, not rigid templates. Always wrap in `<div class="diagram-wrap">` and add a `<p class="diagram-caption">` below.

### Diagram layout rules (read before writing any `<svg>`)

**1. Prefer single-column top-down.** Put every downstream component directly below the upstream one it depends on. Arrows are all `x1=X x2=X` (pure vertical). This eliminates the whole class of "edge passes through an unrelated box" bugs.

Fan-in / fan-out with diagonals is **last resort**. If you need them, keep fanouts to two branches max and make absolutely sure no edge cuts through a rect that isn't one of its endpoints.

**2. Cluster labels go in a margin, not inline.** Either above the first row (`y < row_top`) or in a left-margin column (`x < column_start`). Never inside the canvas where arrows live — labels at `y=184` between two rows at `y=150` and `y=220` will sit in the arrow paths.

**3. Text must fit inside its rect.** Rough width estimates at `font-size="14"`:
- Monospace: ~6.6 px per char
- Sans-serif: ~6.0 px per char

Confirm `text_x + (chars × 6.0) < rect_x + rect_width` before writing. If the label is too long, shorten it or widen the rect.

### Verification checklist — run mentally before emitting SVG

- [ ] No edge's `(x1,y1)→(x2,y2)` line segment passes through a `<rect>` that isn't one of its two endpoints
- [ ] No `<text>` element overlaps an edge line — if a text's `y` falls in the vertical range of an arrow, it probably overlaps
- [ ] Cluster labels are strictly above the first row OR in a left margin column — never inline with content
- [ ] Every `<text>` fits horizontally inside its parent `<rect>` (apply the char-width heuristic above)
- [ ] If the layout has >1 column, trace each `(x1,y1)→(x2,y2)` by eye — the arrows go where you think they go

If any check fails, redo the layout. Static SVG is hard to debug after the fact; a visibly broken diagram on Derek's phone is worse than no diagram.

### Pattern A — Horizontal flow (sequential process)

Use for: pipelines, request flows, step-by-step processes.

```html
<div class="diagram-wrap">
  <svg viewBox="0 0 760 140" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <marker id="arr" viewBox="0 0 10 10" refX="9" refY="5"
              markerWidth="6" markerHeight="6" orient="auto">
        <path d="M0,0 L10,5 L0,10 z" fill="#555"/>
      </marker>
    </defs>
    <!-- Steps: rect + text. Repeat for each step. -->
    <g>
      <rect x="20"  y="50" width="140" height="50" rx="6"
            fill="#e8eef9" stroke="#2a5490" stroke-width="1.5"/>
      <text x="90"  y="80" text-anchor="middle" font-size="14"
            font-family="system-ui, sans-serif">Step 1</text>
    </g>
    <g>
      <rect x="200" y="50" width="140" height="50" rx="6"
            fill="#e8f4e8" stroke="#2e7d32" stroke-width="1.5"/>
      <text x="270" y="80" text-anchor="middle" font-size="14"
            font-family="system-ui, sans-serif">Step 2</text>
    </g>
    <g>
      <rect x="380" y="50" width="140" height="50" rx="6"
            fill="#fdf2e0" stroke="#b47817" stroke-width="1.5"/>
      <text x="450" y="80" text-anchor="middle" font-size="14"
            font-family="system-ui, sans-serif">Step 3</text>
    </g>
    <g>
      <rect x="560" y="50" width="140" height="50" rx="6"
            fill="#f3e8f9" stroke="#6a1b9a" stroke-width="1.5"/>
      <text x="630" y="80" text-anchor="middle" font-size="14"
            font-family="system-ui, sans-serif">Step 4</text>
    </g>
    <!-- Arrows between steps -->
    <line x1="160" y1="75" x2="200" y2="75" stroke="#555" stroke-width="1.5"
          marker-end="url(#arr)"/>
    <line x1="340" y1="75" x2="380" y2="75" stroke="#555" stroke-width="1.5"
          marker-end="url(#arr)"/>
    <line x1="520" y1="75" x2="560" y2="75" stroke="#555" stroke-width="1.5"
          marker-end="url(#arr)"/>
  </svg>
  <p class="diagram-caption">Figure 1: request flow through the new middleware stack.</p>
</div>
```

### Pattern B — Component graph (architecture / dependencies)

Use for: showing how modules/services connect. Position rectangles in clusters, draw edges.

```html
<div class="diagram-wrap">
  <svg viewBox="0 0 760 420" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <marker id="arr2" viewBox="0 0 10 10" refX="9" refY="5"
              markerWidth="6" markerHeight="6" orient="auto">
        <path d="M0,0 L10,5 L0,10 z" fill="#777"/>
      </marker>
    </defs>
    <!-- Cluster label -->
    <text x="20" y="30" font-size="11" font-weight="600" fill="#666"
          font-family="system-ui" letter-spacing="0.06em">FRONTEND</text>
    <!-- Node -->
    <rect x="20" y="50" width="160" height="50" rx="6"
          fill="#e8eef9" stroke="#2a5490"/>
    <text x="100" y="80" text-anchor="middle" font-size="13"
          font-family="system-ui">UI Component</text>
    <!-- ... more nodes ... -->
    <!-- Edges with labels -->
    <line x1="180" y1="75" x2="300" y2="200" stroke="#777" stroke-width="1.2"
          stroke-dasharray="4,3" marker-end="url(#arr2)"/>
    <text x="240" y="130" font-size="10" fill="#888"
          font-family="system-ui">POST /api/x</text>
  </svg>
  <p class="diagram-caption">Figure 2: added a queue between ingestion and persistence.</p>
</div>
```

### Pattern C — Before / After (refactor)

Two stacked SVGs under `<h3>` markers. Use red strokes for removed, green for added, amber for modified.

```html
<h3 style="margin:14px 0 4px; color:#666;">BEFORE</h3>
<div class="diagram-wrap">
  <svg viewBox="0 0 760 160" xmlns="http://www.w3.org/2000/svg">
    <!-- original layout in neutral gray -->
    <rect x="20" y="50" width="140" height="50" rx="6"
          fill="#f4f2ec" stroke="#999" stroke-width="1.5"/>
    <text x="90" y="80" text-anchor="middle" font-size="14"
          font-family="system-ui">Old handler</text>
  </svg>
</div>

<h3 style="margin:14px 0 4px; color:#666;">AFTER</h3>
<div class="diagram-wrap">
  <svg viewBox="0 0 760 160" xmlns="http://www.w3.org/2000/svg">
    <!-- removed in red dashed -->
    <rect x="20" y="50" width="140" height="50" rx="6"
          fill="#fdecec" stroke="#c62828" stroke-width="1.5"
          stroke-dasharray="5,3"/>
    <text x="90" y="80" text-anchor="middle" font-size="14"
          font-family="system-ui" fill="#c62828">removed</text>
    <!-- added in solid green -->
    <rect x="200" y="50" width="140" height="50" rx="6"
          fill="#e8f4e8" stroke="#2e7d32" stroke-width="2"/>
    <text x="270" y="80" text-anchor="middle" font-size="14"
          font-family="system-ui" fill="#2e7d32">new handler</text>
  </svg>
  <p class="diagram-caption">Figure 3: handler extracted; legacy path removed.</p>
</div>
```

### Color palette (consistent across diagrams)

| Role | Fill | Stroke |
|------|------|--------|
| Primary / input | `#e8eef9` | `#2a5490` |
| Success / output | `#e8f4e8` | `#2e7d32` |
| Warning / external | `#fdf2e0` | `#b47817` |
| Special / derived | `#f3e8f9` | `#6a1b9a` |
| Neutral / pre-existing | `#f4f2ec` | `#999` |
| Removed | `#fdecec` | `#c62828` (dashed) |

## Edge cases

| Case | Handling |
|------|----------|
| No PR & on main/master | Error in Step 1 |
| Branch with no commits ahead of main | Error in Step 1 |
| Not inside a git repo | Error: "Run /pr-tour from inside a git repo" |
| Single-commit PR | Section 4 has one entry; works fine |
| No tests touched | Section 5: "No tests changed in this PR." Don't fabricate |
| No linked ticket | Sections 1–2 lean on commits + diff; note explicitly if one was expected |
| Huge diff (>50 files) | Section 3 notes intent-only; Section 4 groups commits if >10 |
| User aborts during walkthrough | HTML is already on disk from Step 4. Exit cleanly; nothing to undo. |
| Same-day re-run | Overwrite |
| `gh` not authenticated | Surface gh error, ask user to `gh auth login` |
| Special chars in PR title / branch name | Sanitize for filename via `tr -cd '[:alnum:]-' \| cut -c1-50` |

## Voice & tone

Write like a friend catching Derek up — not a technical writer, not a code reviewer.

- First-person-plural: "we added retries" > "the PR adds retries"
- Short paragraphs, conversational sentences
- Lead with intent, trail with mechanics
- It's OK to be casual ("the original approach was janky, so we…") as long as it's accurate
- Don't pad. If a section would be two sentences, it's two sentences.
