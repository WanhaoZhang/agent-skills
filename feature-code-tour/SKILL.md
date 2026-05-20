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

Choose `<tool>` and `<model>` from the actual user context. Prefer explicit user-provided values; otherwise use the current tool/app identity and model identity when known. Keep all filename parts lowercase and filesystem-safe. Replace `YYYYMMDD` with the actual generation date.

The Mermaid Markdown header must include the actual tool, model, analyzed feature, generation date, and scope.

When available, use `/Users/zhangwh/Documents/ObsidianBlogs/ZWHNotes/技术博客/FlexAttention相关/【WIP】FlexAttention接入Cutlass链路分析.md` as a local style reference for report rhythm: overview prose, a staged main flowchart, then stage-by-stage detail sections. Do not copy its code-path-heavy node style; keep generated Mermaid node labels code-free and Chinese.

## Workflow

1. Establish the comparison scope.
   - Identify current branch, remotes, recent commits, and changed files.
   - If the user names commits, compare exactly those commits.
   - If not, infer the likely base from the branch, upstream, or recent commits, and state the assumption.

2. Read the implementation path from source.
   - Start from user-facing entry points, tests, or examples.
   - Follow the call chain through dispatch, matching/lowering, codegen/template, runtime wrapper, kernel/runtime, and output.
   - For generated, multi-language, framework-driven, or staged systems, analyze every handoff boundary: the producer side that interprets user intent, builds an intermediate model, transforms it, or emits artifacts, and the consumer side that turns those artifacts into actual execution and output.
   - Do not stop at an example, wrapper, generated file, or runtime entry until you have checked whether an upstream generator/lowering layer or downstream executor/scheduler layer also participates.
   - When a stage contains loops, partitioning, caches, queues, buffers, callbacks/handlers, async work, event synchronization, staged pipelines, or multi-worker execution, expand that logic as its own detailed stage with source-backed nodes.
   - Use `rg` first for symbols and `sed -n`/`nl -ba` for local context.
   - Record what each stage does, what it consumes, what it produces, and the concrete file paths and line numbers that prove it.

3. Build the single natural-language Mermaid Markdown file.
   - Name it `.tour/<tool>-<model>-<feature>-YYYYMMDD_mermaid.md`.
   - Start with a short title and metadata lines: `工具：...`, `模型：...`, `分析功能：...`, `生成日期：...`, and `分析范围：...`.
   - Before the main graph, add a short Chinese overview explaining what the feature path does and which side of the system each major component owns.
   - First include `## 整体调用链路` and the main flowchart.
   - The main flowchart must be more detailed than a flat stage list: use `subgraph` blocks for major stages such as API 入口、追踪建模、编译 lowering、后端选择、模板生成、运行时执行、反向链路、输出。
   - If the feature crosses a producer/consumer or generator/executor boundary, the main flowchart must show both halves explicitly, for example input capture, intermediate representation, transformation passes, artifact rendering, parameter conversion, scheduling, execution, and output.
   - Put 2-4 Chinese natural-language nodes inside each main-flow `subgraph` so readers can see what each stage does at a glance.
   - Node text must use Chinese natural language only; do not put function names, file paths, or line numbers inside node labels.
   - Keep code locations only in `click NODE "vscode://file/<absolute-path>:<line>:1"` statements and in the CodeTour JSON.
   - Keep this first diagram short enough to orient a reviewer before the detailed stage diagrams.

4. Add detailed stage subflowcharts in the same Markdown file.
   - Add a `## 阶段 N：<stage name>` heading before each stage subflowchart.
   - Each subflowchart should expand exactly one main-flow stage.
   - Each node must use Chinese to say what happens, why it matters, and what data/control object moves forward.
   - Do not include code symbols, file paths, or line numbers in Mermaid node labels.
   - Include branch conditions, fallback paths, generated artifacts, cached data, resource/state layout, handler or callback state, synchronization events, and output tensors/objects when relevant.
   - For runtime or executor stages, do not compress complex implementation into a single “run” node. Split the real source structure into loop boundaries, partition decisions, state/buffer rotation, scheduling or synchronization points, and the concrete per-phase operations.
   - Add `click NODE "vscode://file/<absolute-path>:<line>:1"` for every source-backed node, keeping the diagram visual text code-free.
   - Label branch edges with Chinese labels such as `是`/`否`; make fallback branches explicit terminal nodes when not expanded.
   - Preserve the same stage node id prefix used in the main flow when practical, so readers can map overview nodes to detail diagrams.
   - After each stage subflowchart, add `### 执行流程分析` and explain the stage in Chinese prose: input, key decisions, transformation, produced artifact/data, and handoff to the next stage.

5. Make the Mermaid visually tidy.
   - Prefer `flowchart TD` for execution chains and `flowchart LR` for compact handoffs.
   - Use stable stage prefixes such as `API_`, `HOP_`, `LOWER_`, `TEMPLATE_`, `RUNTIME_`, `BWD_`.
   - Use `classDef` and `class` lines for stage roles such as entry, transform, decision, backend, output, and fallback.
   - Keep labels concise but explanatory; split long text with `<br/>`.
   - Follow the `beautiful-mermaid` spirit: restrained colors, clear grouping, readable spacing, and no decorative clutter.

6. Build the CodeTour JSON.
   - Use `.tour/<tool>-<model>-<feature>-YYYYMMDD_codetour.tour`.
   - Keep steps in execution order.
   - Each step should contain a relative `file`, 1-based `line`, and a short Chinese natural-language description of what that code does in the feature path.

7. Validate artifacts.
   - Run the bundled checker:

```bash
python3 .agents/skills/feature-code-tour/scripts/check_feature_tour.py .tour
```

   - Fix reported Mermaid compatibility issues before handing off.

8. Commit only requested artifacts when the user asks to commit or push.
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
