---
name: feature-code-tour
description: Generate natural-language implementation-path documentation for a code feature from git diffs, commit comparisons, and local source inspection. Use when the user asks to compare commits, explain how a newly implemented feature works, draw detailed clickable Mermaid execution diagrams, create a natural-language Mermaid walkthrough, generate CodeTour JSON, or says things like "把这个新功能实现的代码实现画个 mermaid", "梳理这个功能的执行路径", "生成 codetour", or "对比 commit 看这块怎么接上的".
---

# Feature Code Tour

## Goal

Create a reusable implementation walkthrough from real code, not a guessed architecture diagram. The expected output is usually:

- One natural-language Mermaid Markdown file containing:
  - A main clickable flowchart that shows the end-to-end stages first.
  - One detailed clickable subflowchart per stage in the same Markdown file.
- One same-basename HTML export for that Mermaid Markdown file.
- One CodeTour `.tour` JSON file.
- Optional short report files when the user asks for deeper explanation.

Prefer repo-local output under `.tour/` unless the user asks for another location.

Use generated-by naming for required artifacts:

```text
.tour/codex-gpt5.5-YYYYMMDD-<feature>_mermaid.md
.tour/codex-gpt5.5-YYYYMMDD-<feature>_mermaid.html
.tour/codex-gpt5.5-YYYYMMDD-<feature>_codetour.tour
```

Replace `YYYYMMDD` with the actual generation date. Keep `<feature>` short, lowercase, and readable.

## Workflow

1. Establish the comparison scope.
   - Identify current branch, remotes, recent commits, and changed files.
   - If the user names commits, compare exactly those commits.
   - If not, infer the likely base from the branch, upstream, or recent commits, and state the assumption.

2. Read the implementation path from source.
   - Start from user-facing entry points, tests, or examples.
   - Follow the call chain through dispatch, matching/lowering, codegen/template, runtime wrapper, kernel/runtime, and output.
   - Use `rg` first for symbols and `sed -n`/`nl -ba` for local context.
   - Record what each stage does, what it consumes, what it produces, and the concrete file paths and line numbers that prove it.

3. Build the single natural-language Mermaid Markdown file.
   - Name it `.tour/codex-gpt5.5-YYYYMMDD-<feature>_mermaid.md`.
   - Start with a short title and generated-by line.
   - First include the main flowchart. Show only the major execution stages, such as entry, validation, user callback tracing, lowering, backend selection, template/code generation, runtime wrapper, kernel/runtime, backward, and output.
   - Use one node per stage unless a branch changes the overall path.
   - Node text must primarily explain the behavior in plain language; put function names and locations on a secondary line.
   - Add `click NODE "vscode://file/<absolute-path>:<line>:1"` to every node with a source location.
   - Keep this first diagram short enough to orient a reviewer before the detailed stage diagrams.

4. Add detailed stage subflowcharts in the same Markdown file.
   - Add a `## <stage name>` heading before each stage subflowchart.
   - Each subflowchart should expand exactly one main-flow stage.
   - Each node must say what happens, why it matters, and what data/control object moves forward.
   - Code symbols belong in the second line of the node label, not as the whole node label.
   - Include branch conditions, fallback paths, generated artifacts, cached data, and output tensors/objects when relevant.
   - Add `click NODE "vscode://file/<absolute-path>:<line>:1"` for every source-backed node.
   - Label branch edges with `yes`/`no`; make fallback branches explicit terminal nodes when not expanded.
   - Preserve the same stage node id prefix used in the main flow when practical, so readers can map overview nodes to detail diagrams.

5. Make the Mermaid visually tidy.
   - Prefer `flowchart TD` for execution chains and `flowchart LR` for compact handoffs.
   - Use stable stage prefixes such as `API_`, `HOP_`, `LOWER_`, `TEMPLATE_`, `RUNTIME_`, `BWD_`.
   - Use `classDef` and `class` lines for stage roles such as entry, transform, decision, backend, output, and fallback.
   - Keep labels concise but explanatory; split long text with `<br/>`.
   - Follow the `beautiful-mermaid` spirit: restrained colors, clear grouping, readable spacing, and no decorative clutter.

6. Export matching HTML for the Mermaid Markdown file.
   - Use the bundled exporter:

```bash
python3 .agents/skills/feature-code-tour/scripts/export_mermaid_html.py .tour
```

   - The exporter creates the same-basename `.html` file next to `codex-gpt5.5-YYYYMMDD-<feature>_mermaid.md`.
   - If the skill is installed at another path, run the script from that installed skill directory instead.

7. Build the CodeTour JSON.
   - Use `.tour/codex-gpt5.5-YYYYMMDD-<feature>_codetour.tour`.
   - Keep steps in execution order.
   - Each step should contain a relative `file`, 1-based `line`, and a short natural-language description of what that code does in the feature path.

8. Validate artifacts.
   - Run the bundled checker:

```bash
python3 .agents/skills/feature-code-tour/scripts/check_feature_tour.py .tour
```

   - Fix reported Mermaid compatibility issues before handing off.

9. Commit only requested artifacts when the user asks to commit or push.
   - Stage `.tour/` artifacts explicitly.
   - Avoid unrelated local files such as `.DS_Store`.
   - Mention untracked or intentionally ignored files.

## Important Mermaid Rules

- Use solid edges for control/calls: `A -->|calls| B`.
- Use dashed edges for produced data: `A -. returns result .-> B`.
- Avoid `A -.->|label| B`; some VS Code Mermaid renderers dislike it.
- Avoid node id `END`; use `ZEND`, `DONE`, or `OUT`.
- Avoid labels starting with `1. text`; use `1: text` or omit numbering.
- Do not use `&#46;` unless there is no better option.
- Keep every branch with a clear destination; terminal fallback nodes are fine.
- Prefer absolute `vscode://file/...` click targets for clickable Mermaid.

For detailed commands, naming, and validation patterns, read `references/workflow.md`.
