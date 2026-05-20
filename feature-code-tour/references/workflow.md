# Feature Code Tour Workflow Reference

## Discovery Commands

Use these commands as a starting point, adjusting commit ranges and symbols to the repo:

```bash
git branch --show-current
git remote -v
git log --oneline --decorate -n 20
git diff --name-status <base>...HEAD
git diff --stat <base>...HEAD
git show --name-only --oneline <commit>
rg -n "symbol_or_backend_name" .
rg --files | rg "tour|mermaid|feature|test"
```

When comparing feature commits, collect:

- Entry files: examples, tests, public APIs.
- Dispatch/lowering files.
- Matcher or selector files.
- Codegen/template files.
- Runtime wrapper files.
- Kernel/runtime files.
- Validation scripts and reports.

## Output Naming

Prefer lowercase snake-case-ish filenames under `.tour/`:

```text
.tour/<feature>_main_flow_mermaid.md
.tour/<feature>_main_flow_mermaid.html
.tour/<feature>_<stage>_flow_mermaid.md
.tour/<feature>_<stage>_flow_mermaid.html
.tour/<feature>_execution_hierarchy.tour
.tour/<feature>_execution_narrative_mermaid.md
.tour/<feature>_execution_narrative_mermaid.html
.tour/<feature>_current_implementation_report_YYYYMMDD.md
.tour/<feature>_python_to_kernel_trace_report_YYYYMMDD.md
```

Create the main flow before stage subflows. The main file should answer "what are the phases?"
The stage files should answer "what code runs inside this phase?"

## CodeTour JSON Shape

Use the VS Code CodeTour extension style:

```json
{
  "title": "Feature Execution Hierarchy",
  "description": "End-to-end walkthrough of the feature implementation path.",
  "steps": [
    {
      "file": "relative/path/from/repo/root.py",
      "line": 123,
      "description": "Explain what happens at this step."
    }
  ]
}
```

Keep steps ordered by actual execution flow, not by file order.

## Main Mermaid Structure Template

```mermaid
flowchart TD
    START(["Start<br/>User/API call"])
    ENTRY["ENTRY: Entry<br/>path/file.py:10"]
    LOWER["LOWER: Lowering / dispatch<br/>path/lowering.py:20"]
    MATCH{"MATCH: Backend matched?<br/>path/lowering.py:30"}
    CODEGEN["CODEGEN: Build generated code<br/>path/codegen.py:40"]
    WRAP["WRAP: Runtime wrapper<br/>path/wrapper.py:50"]
    RUN["RUN: Kernel/runtime<br/>path/runtime.py:60"]
    FALLBACK["Fallback path<br/>not expanded"]
    OUT(["Done<br/>Output / runtime result"])

    START -->|calls| ENTRY
    ENTRY -->|normalizes request| LOWER
    LOWER -->|checks| MATCH
    MATCH -- yes --> CODEGEN
    MATCH -- no --> FALLBACK
    CODEGEN -->|emits wrapper| WRAP
    WRAP -->|launches| RUN
    RUN -. result .-> OUT

    click ENTRY "vscode://file/<absolute-path>/path/file.py:10:1"
    click LOWER "vscode://file/<absolute-path>/path/lowering.py:20:1"
    click MATCH "vscode://file/<absolute-path>/path/lowering.py:30:1"
    click CODEGEN "vscode://file/<absolute-path>/path/codegen.py:40:1"
    click WRAP "vscode://file/<absolute-path>/path/wrapper.py:50:1"
    click RUN "vscode://file/<absolute-path>/path/runtime.py:60:1"
```

## Stage Mermaid Structure Template

```mermaid
flowchart TD
    STAGE_START(["Stage start<br/>Input from previous stage"])

    subgraph ENTRY["Entry"]
        ENTRY_0["ENTRY.0: Entry point<br/>path/file.py:10"]
        ENTRY_1["ENTRY.1: Validate arguments<br/>path/file.py:15"]
    end

    subgraph LOWERING["Lowering / dispatch"]
        LOWER_0["LOWER.0: Select backend<br/>path/lowering.py:20"]
        LOWER_1{"LOWER.1: Backend matched?<br/>path/lowering.py:30"}
        LOWER_FALLBACK["LOWER.F: Fallback path<br/>not expanded"]
    end

    subgraph CODEGEN["Codegen"]
        CODEGEN_0["CODEGEN.0: Build plan<br/>path/codegen.py:40"]
        CODEGEN_1["CODEGEN.1: Render wrapper<br/>path/template.py:50"]
    end

    STAGE_OUT(["Stage output<br/>Data for next stage"])

    STAGE_START -->|calls| ENTRY_0
    ENTRY_0 -->|checks| ENTRY_1
    ENTRY_1 -->|calls| LOWER_0
    LOWER_0 -->|checks| LOWER_1
    LOWER_1 -- yes --> CODEGEN_0
    LOWER_1 -- no --> LOWER_FALLBACK
    CODEGEN_0 -. plan / cache key .-> CODEGEN_1
    CODEGEN_1 -->|returns| STAGE_OUT

    click ENTRY_0 "vscode://file/<absolute-path>/path/file.py:10:1"
```

## HTML Export

After writing or updating Mermaid Markdown files, export matching HTML files:

```bash
python3 .agents/skills/feature-code-tour/scripts/export_mermaid_html.py .tour
```

The exporter accepts either a directory or a single Markdown file. For each `*_mermaid.md`,
it writes a same-basename `.html` file that embeds Mermaid.js and keeps clickable links.

## Mermaid Compatibility Checklist

Run this mental checklist before finishing:

- Mermaid fences are balanced.
- Every `subgraph` has a matching `end`.
- Branch nodes use `{...}` and all outgoing branch edges have labels.
- Fallback branches terminate in explicit nodes if not expanded.
- No `-.->|label|` dashed edge syntax.
- No node id named exactly `END`.
- No label starts with `1. text` or another Markdown ordered-list pattern.
- No accidental HTML entity noise such as `&#46;`.
- `doc_id(q)` style labels are safer than `doc_id[q]` for stricter renderers.
- Click targets use absolute paths and line numbers.
- Every `*_mermaid.md` has a same-basename `.html` export.

## Git Hygiene

When committing:

```bash
git status --short
git add .tour/<specific-file-1> .tour/<specific-file-2>
git diff --cached --stat
git commit -m "docs: add <feature> code tour"
git push origin <branch>
git push gitcode <branch>
```

Do not stage unrelated generated files such as `.DS_Store`, old reports, or unrelated plan files.
