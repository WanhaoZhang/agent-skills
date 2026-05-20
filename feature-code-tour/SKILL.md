---
name: feature-code-tour
description: Generate natural-language implementation-path documentation for a code feature from git diffs, commit comparisons, and local source inspection. Use when the user asks to compare commits, explain how a newly implemented feature works, draw detailed clickable Mermaid execution diagrams, create a natural-language Mermaid walkthrough, generate CodeTour JSON, or says things like "把这个新功能实现的代码实现画个 mermaid", "梳理这个功能的执行路径", "生成 codetour", or "对比 commit 看这块怎么接上的".
---

# Feature Code Tour

## Goal

Create a reusable implementation walkthrough from real code, not a guessed architecture diagram. The expected output is usually:

- One natural-language Mermaid Markdown file containing:
  - A main clickable flowchart that shows the end-to-end stages first, with `subgraph` blocks grouping each stage.
  - One detailed clickable subflowchart per stage in the same Markdown file.
  - A Chinese execution-flow analysis section after each stage subflowchart.
- One CodeTour `.tour` JSON file.
- Optional short report files when the user asks for deeper explanation.

Always write required artifacts to the target project's root `.tour/` directory unless the user explicitly asks for another location. Resolve the project root with `git rev-parse --show-toplevel` when available; otherwise use the current working directory.

Use generated-by naming for required artifacts:

```text
.tour/<tool>-<model>-<feature>-YYYYMMDD_mermaid.md
.tour/<tool>-<model>-<feature>-YYYYMMDD_codetour.tour
```

Choose `<tool>` and `<model>` from the actual user context. Prefer explicit user-provided values; Keep all filename parts lowercase and filesystem-safe. Replace `YYYYMMDD` with the actual generation date.

The Mermaid Markdown header must include the actual tool, model, analyzed feature, generation date, and scope.

When available, search the workspace or look for local architectural documents (e.g., custom blog posts or design specs) as a style reference for report rhythm: overview prose, a staged main flowchart, then stage-by-stage detail sections. If a local file path like `/Users/zhangwh/Documents/ObsidianBlogs/ZWHNotes/技术博客/FlexAttention相关/【WIP】FlexAttention接入Cutlass链路分析.md` exists and is accessible, use it as a reference for layout rhythm. Do not copy code-path-heavy node styles; keep generated Mermaid node labels code-free and Chinese.

## Workflow

1. Establish the comparison scope.
   - Identify current branch, remotes, recent commits, and changed files.
   - If the user names commits, compare exactly those commits.
   - If not, infer the likely base from the branch, upstream, or recent commits, and state the assumption.

2. Read the implementation path from source.
   - Start from user-facing entry points, tests, or examples.
   - Follow the execution/call chain through all major layers of the system. Adapt vocabulary depending on the architecture:
     * **Compilers / Code-Gen (e.g. TVM, CATLASS)**: trace AST parsing -> graph passes/optimization -> lowering -> templates/codegen -> runtime wrapper -> hardware kernel -> output.
     * **Web Apps / Backend Services**: trace HTTP Request/UI action -> Router -> Middleware -> Controller -> Database ORM/Query -> Serializer -> Response -> DOM render.
     * **General Systems / Concurrent Daemons**: trace API invocation -> queueing/scheduling -> worker threads/concurrency locks -> hardware/OS driver IOCTL -> interrupt/sync -> output.
   - Use `rg` first for symbols and view code files for local context.
   - Record what each stage does, what it consumes, what it produces, and the concrete file paths and line numbers that prove it.

3. Build the single natural-language Mermaid Markdown file.
   - Name it `.tour/<tool>-<model>-<feature>-YYYYMMDD_mermaid.md`.
   - Start with a short title and metadata lines: `工具：...`, `模型：...`, `分析功能：...`, `生成日期：...`, and `分析范围：...`.
   - Before the main graph, add a short Chinese overview explaining what the feature path does and which side of the system each major component owns.
   - First include `## 整体调用链路` and the main flowchart.
   - The main flowchart must be more detailed than a flat stage list: use `subgraph` blocks to group major logic boundaries or subsystems.
   - Put 2-4 Chinese natural-language nodes inside each main-flow `subgraph` so readers can see what each stage does at a glance.
   - Node text must use Chinese natural language only; do not put function names, file paths, or line numbers inside node labels.
   - Keep code locations only in `click NODE "vscode://file/<absolute-path>:<line>:1"` statements and in the CodeTour JSON.
   - Keep this first diagram short enough to orient a reviewer before the detailed stage diagrams.

4. Add detailed stage subflowcharts in the same Markdown file.
   - Add a `## 阶段 N：<stage name>` heading before each stage subflowchart.
   - Each subflowchart should expand exactly one main-flow stage.
   - Each node must use Chinese to say what happens, why it matters, and what data/control object moves forward.
   - Do not include code symbols, file paths, or line numbers in Mermaid node labels. Use `click` targets instead.
   - **Enforce Deep Microscopic Details**: For each stage, you must deeply analyze and explicitly diagram the following elements:
     * **Variables and Constraints**: Note critical loop coordinates (e.g., block indices, tile rows/cols), layout constraints (e.g., 32-byte alignment, tensor strides), shape transformations, and size boundaries.
     * **Concurrency and Synchronization**: If the feature runs asynchronously or concurrently, map out thread/core coordination, queue mechanisms, synchronization flags (e.g., AscendC SetFlag/WaitFlag, cross-core signals, locks, event loops), and state machine flags.
     * **Resource Mapping**: Identify physical or local resource pools (e.g., local buffers/Unified Buffer offsets, shared memory, cache levels, CPU/GPU thread blocks, socket descriptors).
     * **Conditionals & Fallbacks**: Branching rules (e.g. `if cols <= COMPUTE_LENGTH`), fallback configurations, assertion failures, and error-handling endpoints must be represented as decision nodes or distinct terminal edges.
   - Add `click NODE "vscode://file/<absolute-path>:<line>:1"` for every source-backed node.
   - Label branch edges with Chinese labels such as `是`/`否`; make fallback branches explicit terminal nodes when not expanded.
   - After each stage subflowchart, add `### 执行流程分析` and explain the stage in Chinese prose: input, key decisions, variables, hardware synchronization, transformation, produced artifact/data, and handoff to the next stage.

5. Make the Mermaid visually tidy.
   - Prefer `flowchart TD` for execution chains and `flowchart LR` for compact handoffs.
   - Use stable stage prefixes (e.g., `API_`, `AST_`, `LOWER_`, `RUNTIME_`, `SYNC_`, `DB_`).
   - Use `classDef` and `class` lines for stage roles such as entry, transform, decision, backend, output, and fallback.
   - Keep labels concise but explanatory; split long text with `<br/>`.
   - Follow the `beautiful-mermaid` spirit: restrained colors, clear grouping, readable spacing, and no decorative clutter.

6. Export matching HTML for the Mermaid Markdown file.
   - Locate the export script in the current skill directory (e.g., `<skill-dir>/scripts/export_mermaid_html.py` or `.agents/skills/feature-code-tour/scripts/export_mermaid_html.py`) and run it:
   ```bash
   python3 <path-to-skill>/scripts/export_mermaid_html.py .tour
   ```
   - The exporter creates the same-basename `.html` file next to `<tool>-<model>-<feature>-YYYYMMDD_mermaid.md`.

7. Build the CodeTour JSON.
   - Use `.tour/<tool>-<model>-<feature>-YYYYMMDD_codetour.tour`.
   - Keep steps in execution order.
   - Each step should contain a relative `file`, 1-based `line`, and a short Chinese natural-language description of what that code does in the feature path.

8. Validate artifacts.
   - Run the bundled checker from the skill directory:
   ```bash
   python3 <path-to-skill>/scripts/check_feature_tour.py .tour
   ```
   - Fix reported Mermaid compatibility issues before handing off.

9. Commit only requested artifacts when the user asks to commit or push.
   - Stage `.tour/` artifacts explicitly.
   - Avoid unrelated local files such as `.DS_Store`.
   - Mention untracked or intentionally ignored files.

## Important Mermaid Rules

- Use solid edges for control/calls: `A -->|调用| B`.
- Use dashed edges for produced data: `A -. 产出结果 .-> B`.
- Avoid `A -.->|label| B`; some VS Code Mermaid renderers dislike it.
- Avoid node id `END`; use `ZEND`, `DONE`, or `OUT`.
- Avoid labels starting with `1. text`; use `1: text` or omit numbering.
- Do not use `&#46;` unless there is no better option.
- Keep every branch with a clear destination; terminal fallback nodes are fine.
- Prefer absolute `vscode://file/...` click targets for clickable Mermaid, but keep node labels free of code locations.

For detailed commands, naming, and validation patterns, read `references/workflow.md`.
