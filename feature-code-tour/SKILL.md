---
name: feature-code-tour
description: Generate implementation-path documentation for a code feature from git diffs, commit comparisons, and local source inspection. Use when the user asks to compare commits, explain how a newly implemented feature works, draw clickable Mermaid diagrams for code execution flow, create a natural-language Mermaid walkthrough, generate CodeTour JSON, or says things like "把这个新功能实现的代码实现画个 mermaid", "梳理这个功能的执行路径", "生成 codetour", or "对比 commit 看这块怎么接上的".
---

# Feature Code Tour

## Goal

Create a reusable implementation walkthrough from real code, not a guessed architecture diagram. The expected output is usually:

- A main clickable Mermaid flowchart that shows the end-to-end stages first.
- One clickable Mermaid subflowchart per stage, with code-level details.
- Optional natural-language clickable Mermaid flowcharts when helpful for reviewers.
- Matching HTML files exported from every Mermaid Markdown file.
- A CodeTour `.tour` JSON file.
- Optional short report files when the user asks for deeper explanation.

Prefer repo-local output under `.tour/` unless the user asks for another location.

## Workflow

1. Establish the comparison scope.
   - Identify current branch, remotes, recent commits, and changed files.
   - If the user names commits, compare exactly those commits.
   - If not, infer the likely base from the branch, upstream, or recent commits, and state the assumption.

2. Read the implementation path from source.
   - Start from user-facing entry points, tests, or examples.
   - Follow the call chain through dispatch, matching/lowering, codegen/template, runtime wrapper, kernel/runtime, and output.
   - Use `rg` first for symbols and `sed -n`/`nl -ba` for local context.
   - Record concrete file paths and line numbers for every diagram node.

3. Build the main Mermaid flowchart first.
   - Name it `.tour/<feature>_main_flow_mermaid.md`.
   - Show only the major execution stages, such as entry, lowering, match, codegen, wrapper, runtime, and output.
   - Use one node per stage unless a branch changes the overall path.
   - Add `click NODE "vscode://file/<absolute-path>:<line>:1"` to stage nodes that have a representative source location.
   - Keep this diagram short enough to orient a reviewer before they open the detailed stage diagrams.

4. Build one Mermaid subflowchart per stage.
   - Name files `.tour/<feature>_<stage>_flow_mermaid.md`.
   - Each subflowchart should expand exactly one main-flow stage.
   - Use subgraphs for layers such as entry, lowering, match, codegen, wrapper, runtime, and output.
   - Node text should name the function or object and include the local code location.
   - Add `click NODE "vscode://file/<absolute-path>:<line>:1"` for every code node.
   - Label branch edges with `yes`/`no`; make fallback branches explicit terminal nodes when not expanded.
   - Preserve the same stage node id prefix used in the main flow when practical, so readers can map overview nodes to detail diagrams.

5. Build natural-language Mermaid only when it adds value.
   - Reuse the same node ids and click links where possible.
   - Replace function-heavy labels with what each step does, its input, and its output.
   - Keep it readable for a human reviewer who has not read the code.

6. Export matching HTML for every Mermaid Markdown file.
   - Use the bundled exporter:

```bash
python3 .agents/skills/feature-code-tour/scripts/export_mermaid_html.py .tour
```

   - The exporter creates a same-basename `.html` file next to each `*_mermaid.md` file.
   - If the skill is installed at another path, run the script from that installed skill directory instead.

7. Build the CodeTour JSON.
   - Use `.tour/<feature>_execution_hierarchy.tour`.
   - Keep steps in execution order.
   - Each step should contain a relative `file`, 1-based `line`, and a short description.

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
