---
description: ""
covers: []
updated: 2026-03-27
---

  ---
  name: visualize
  description: "Generate interactive HTML visualizations to explain work, architecture, and systems. Use this skill
  whenever the user says 'visualize', 'diagram', 'draw', 'show me', 'explain visually', 'overview' (when they want a
  visual, not text), or when the user seems confused and a picture would genuinely help them understand what happened, how
   things connect, or what the current state looks like. Also use when the user asks to see something 'as a tree', 'as a
  flow', 'as slides', or 'as a diagram'. This skill renders in the browser via Chrome MCP tools — it is NOT for generating
   text-based explanations."
  ---

  # Visualize

  Generate self-contained HTML visualizations and render them in the user's browser. The goal is to help the user *see*
  what they're working on — architecture, data flows, session progress, hierarchies, sequences — in a way that builds
  intuition faster than text.

  ## When to Use This

  - **End of a task or batch** — summarize what was built, changed, or fixed
  - **User is confused** — "wait, how does this connect?" or "I'm lost" signals
  - **Architecture questions** — how components relate, data flows, dependency chains
  - **Explaining a complex change** — before/after comparisons, multi-step processes
  - **User explicitly asks** — "visualize", "diagram this", "show me as a tree"

  ## Core Principles

  1. **Pick the right visualization type for the content.** Don't default to one format — match the shape of the
  information.
  2. **Less is more.** A focused diagram beats a cluttered dashboard. Only include what helps understanding.
  3. **Domain-agnostic.** This works for Ansible, Terraform, Python, GHA, shell scripts, APIs, databases — anything. Don't
   hardcode domain assumptions.
  4. **Always persist.** Every visualization gets saved to `~/visualizations/` so the user can come back to it later.

  ## Visualization Types

  ### 1. Session Summary (Slide Deck)

  **When:** End of a task, batch completion, or "what did we do?"

  A scrollable page that tells the story of what was done and *why*. The user wants to understand the reasoning behind
  changes, not just a changelog.

  **Section order (this matters):**

  1. **Files touched** — at the top. Group by file category (production code, workflows, inventory, config). For each
  file, show a brief description of *what* changed and *why* — not just "+3/-2 lines" but "added no_log to prevent
  credential leakage." Use concept tags (security, schema, config, etc.) to visually categorize.

  2. **Per-concept breakdown** — organize by the *problem being solved*, not by ticket number. Each concept card has two
  distinct halves with clear roles:

     **Diagram = the what and how.** Every concept card MUST have a diagram that shows what changed and how it works.
  Before/after flowcharts, data flow diagrams, annotated architecture — the diagram should be self-explanatory enough that
   someone can understand the change just by looking at it. The diagram is the centerpiece of the card.

     **Text = the problem, why, and key notes.** A few short lines (2-4 sentences max) explaining: what problem existed,
  why this approach was chosen, and any gotchas or non-obvious decisions. The text gives context that the diagram can't
  convey — motivation, constraints, trade-offs.

     If the diagram is doing its job, the text should feel like a caption, not an essay.

  3. **Stats bar** — small, at the bottom. Files changed, lines added/removed. No commit hashes or commit log.

  4. **Validation status** — what passed, what's pending (if applicable).

  **Do NOT include:**
  - Commit logs, SHAs, or git history
  - Raw line counts without context
  - Ticket numbers as primary organizers (concepts are better)
  - Dense paragraphs explaining changes — if you need more than 2-3 sentences, the diagram isn't doing its job

  ### 2. Architecture Diagram

  **When:** "How does X connect to Y?", data flow questions, system overview

  Use Mermaid.js diagrams. Pick the right Mermaid diagram type:

  - **flowchart LR/TD** — data flows, pipelines, request paths (e.g., "how do credentials get from GHA to the managed
  node?")
  - **sequenceDiagram** — multi-actor interactions over time (e.g., "what happens during a deploy?")
  - **graph** — dependency relationships (e.g., "which roles depend on which?")
  - **stateDiagram-v2** — state machines, lifecycle flows

  Use subgraphs to group related components. Color-code to highlight important nodes (green for new/good, red for
  removed/bad, yellow for modified).

  ### 3. Tree / Hierarchy

  **When:** File structures, inheritance chains, nested configurations

  There are two very different things a user might mean by "show me as a tree":

  **A. Filesystem tree** — just the directory/file layout. Use only when the user explicitly wants to see what files exist
   and where. A styled HTML `<ul>` with expand/collapse works well here. This is rarely what the user actually wants.

  **B. Relationship/dependency graph** — how things *connect*. This is usually what the user wants, even when they say
  "tree." When someone says "show me the role structure" or "show me the class hierarchy," they want to see which roles
  are used by which playbooks, which classes inherit from which, which modules import which. This requires reading the
  code (grep for `include_role`, `import`, `extends`, etc.) to discover actual relationships, not just listing
  directories.

  Default to B unless the user specifically asks for a file listing. For relationship graphs:
  - Use `flowchart` with directional arrows showing dependency direction
  - Group related items with subgraphs
  - Color-code by category (e.g., playbooks vs roles vs tasks)
  - Add edge labels to show the relationship type ("includes", "depends on", "imports")
  - Show which roles are shared (used by multiple playbooks) by giving them a distinct style

  The whole point of a tree visualization is to show *why things are organized the way they are* — a flat directory
  listing doesn't do that. Relationships do.

  ### 4. Single Focused Diagram

  **When:** User asks for one specific thing — "diagram the SSH key flow", "show me the playbook include chain"

  Generate just that one diagram, no surrounding dashboard. Still persist it.

  ### 5. Before/After Comparison

  **When:** Explaining what a change accomplished

  Side-by-side or stacked diagrams showing the old state and new state. Highlight what was removed (red), added (green),
  or modified (yellow). This is especially powerful for refactors and pipeline changes.

  ## How to Build It

  ### Step 1: Analyze What to Visualize

  Look at the conversation context. What does the user need to understand? Sources:
  - Recent git log / diff for what changed
  - Task list for progress tracking
  - The conversation itself for what was discussed
  - The codebase for architecture questions

  Don't try to visualize everything. Identify the 2-3 most important things and focus on those.

  ### Step 2: Choose Visualization Type(s)

  Based on the content, pick one or more types from the list above. A session summary might contain multiple architecture
  diagrams inside it. A single-diagram request is just one.

  If the user asked for a specific format ("show me as a tree"), use that format. Otherwise, pick what fits best.

  ### Step 3: Generate the HTML

  Build a self-contained HTML file. Requirements:
  - **Dark theme** — background `#0d1117`, text `#c9d1d9`, accents `#58a6ff` (GitHub dark palette)
  - **Mermaid.js** via CDN: `https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js`
  - **Mermaid config**: `mermaid.initialize({ startOnLoad: true, theme: 'dark' })`
  - **Responsive** — looks good at different window sizes
  - **No external dependencies** beyond the Mermaid CDN
  - **Font**: `-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif` (system font stack)

  #### HTML Structure

  ```html
  <!DOCTYPE html>
  <html lang="en">
  <head>
    <meta charset="UTF-8">
    <title>[Descriptive Title]</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
    <style>
      /* Dark theme base */
      * { margin: 0; padding: 0; box-sizing: border-box; }
      body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        background: #0d1117; color: #c9d1d9; padding: 2rem;
        max-width: 1200px; margin: 0 auto;
      }
      h1 { color: #58a6ff; margin-bottom: 0.5rem; }
      h2 { color: #58a6ff; margin: 2rem 0 1rem; border-bottom: 1px solid #30363d; padding-bottom: 0.5rem; }
      .card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 1.5rem; margin: 1rem 0; }
      .mermaid { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 1.5rem; margin: 1rem 0; }

      /* Clickable diagrams — lightbox expand */
      .diagram-container { cursor: pointer; position: relative; }
      .diagram-container::after {
        content: 'Click to expand'; position: absolute; bottom: 8px; right: 12px;
        font-size: 0.7rem; color: #484f58; opacity: 0; transition: opacity 0.2s;
      }
      .diagram-container:hover::after { opacity: 1; }
      .lightbox {
        display: none; position: fixed; inset: 0; background: rgba(1,4,9,0.92);
        z-index: 1000; justify-content: center; align-items: center; padding: 2rem; cursor: pointer;
      }
      .lightbox.active { display: flex; }
      .lightbox-content {
        background: #161b22; border: 1px solid #30363d; border-radius: 12px;
        padding: 2rem; max-width: 95vw; max-height: 95vh; overflow: auto; cursor: default;
      }
      .lightbox-close {
        position: fixed; top: 1rem; right: 1.5rem; color: #8b949e;
        font-size: 2rem; cursor: pointer; z-index: 1001;
      }
      .lightbox-close:hover { color: #e6edf3; }

      /* Add more styles as needed for the specific visualization */
    </style>
  </head>
  <body>
    <!-- Content here -->

    <!-- Lightbox overlay — place before closing </body> -->
    <div class="lightbox" id="lightbox">
      <span class="lightbox-close" id="lightbox-close">&times;</span>
      <div class="lightbox-content" id="lightbox-content"></div>
    </div>

    <script>
    mermaid.initialize({ startOnLoad: true, theme: 'dark' });

    // Click-to-expand: any element with class "diagram-container" opens its SVG in a fullscreen lightbox
    document.addEventListener('DOMContentLoaded', () => {
      const lightbox = document.getElementById('lightbox');
      const lbContent = document.getElementById('lightbox-content');
      const lbClose = document.getElementById('lightbox-close');

      document.querySelectorAll('.diagram-container').forEach(el => {
        el.addEventListener('click', () => {
          const svg = el.querySelector('svg');
          if (!svg) return;
          const clone = svg.cloneNode(true);
          clone.style.width = '100%';
          clone.style.height = 'auto';
          clone.style.maxHeight = '85vh';
          lbContent.innerHTML = '';
          lbContent.appendChild(clone);
          lightbox.classList.add('active');
        });
      });

      lightbox.addEventListener('click', (e) => {
        if (e.target === lightbox || e.target === lbClose) lightbox.classList.remove('active');
      });
      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') lightbox.classList.remove('active');
      });
    });
    </script>
  </body>
  </html>

  This is a starting point — extend it based on what the visualization needs. Add grids, stat cards, progress bars,
  concept tags, or whatever serves the content. The styling should feel polished, not like a raw HTML dump.

  #### Clickable Diagrams

  Every diagram container MUST be clickable and expand to fullscreen. To enable this:

  1. Wrap each Mermaid diagram in a `<div class="diagram-container">` (not just `.mermaid`)
  2. The lightbox CSS + JS in the template above handles the rest automatically
  3. On hover, a "Click to expand" hint appears
  4. On click, the SVG is cloned into a fullscreen lightbox overlay
  5. Escape key or clicking outside closes the lightbox

  This is especially important for complex diagrams that are hard to read at the default card size.

  Mermaid Tips

  - Use %%{init: {'theme': 'dark'}}%% at the top of each Mermaid block
  - Use style directives to highlight nodes: style NodeA fill:#23863644,stroke:#238636 (green), style NodeB
  fill:#f8514944,stroke:#f85149 (red)
  - Use subgraphs to group related components
  - Keep labels short — use line breaks (<br/>) if needed
  - For complex diagrams, break into multiple smaller diagrams rather than one giant one

  Step 4: Save the File

  Save to ~/visualizations/ with a descriptive filename:

  ~/visualizations/YYYY-MM-DD-<short-description>.html

  Examples:
  - 2026-03-27-devops-1779-data-flow.html
  - 2026-03-27-ansible-role-hierarchy.html
  - 2026-03-27-deploy-sequence.html

  If generating multiple visualizations in one session, each gets its own file.

  Step 5: Render in Chrome

  Use the Chrome MCP tools to display the visualization:

  1. Start a local HTTP server:
  cd ~/visualizations && python3 -m http.server 8765 &>/dev/null &
  1. Run this in the background.
  2. Get browser context:
  mcp__claude-in-chrome__tabs_context_mcp (createIfEmpty: true)
  3. Create a new tab:
  mcp__claude-in-chrome__tabs_create_mcp
  4. Navigate to the file:
  mcp__claude-in-chrome__navigate (url: http://localhost:8765/<filename>.html, tabId: <new-tab-id>)
  5. Take a screenshot to confirm it rendered:
  mcp__claude-in-chrome__computer (action: screenshot, tabId: <tab-id>)
  6. Tell the user: "Dashboard is live in your browser at http://localhost:8765/<filename>. Also saved to
  ~/visualizations/<filename> for later."

  If Chrome MCP tools are unavailable, still generate and save the HTML file, and tell the user where to find it.

  Mermaid Diagram Quick Reference

  Flowchart (data flows, pipelines)

  flowchart LR
      A[Source] --> B{Decision}
      B -->|Yes| C[Action]
      B -->|No| D[Other Action]
      subgraph Group["Label"]
          C --> E[Result]
      end

  Sequence Diagram (multi-actor over time)

  sequenceDiagram
      participant GHA as GHA Runner
      participant Ctrl as Controller
      participant Node as Managed Node
      GHA->>Ctrl: SCP deploy-vars.json
      Ctrl->>Ctrl: Run prep_controller.yml
      Ctrl->>Node: Run deploy.yml
      Node-->>Ctrl: Success

  Tree (hierarchy, dependencies)

  graph TD
      A[Root] --> B[Child 1]
      A --> C[Child 2]
      B --> D[Grandchild]
      B --> E[Grandchild]

  State Diagram (lifecycle, state machine)

  stateDiagram-v2
      [*] --> Provisioning
      Provisioning --> Configured: prep_controller
      Configured --> Deploying: deploy.yml
      Deploying --> Verified: verify_deploy
      Deploying --> Failed: error
      Failed --> Deploying: retry

  Mindmap (conceptual hierarchy)

  mindmap
    root((Project))
      Security
        no_log
        cleanup
      Schema
        unified JSON
      Config
        pipeline
        validation
