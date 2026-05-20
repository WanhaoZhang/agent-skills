#!/usr/bin/env python3
"""Check Feature Code Tour artifacts for common Mermaid and CodeTour issues."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


BAD_MERMAID_PATTERNS = [
    (re.compile(r"-\.->\|"), "Use '-. label .->' instead of '-.->|label|'."),
    (re.compile(r"\bEND\s*(?:\[|\()"), "Avoid node id END; use ZEND/DONE/OUT."),
    (re.compile(r"(?:\[\"|\{\")\d+\.\s"), "Avoid labels starting with ordered-list text like '1. text'; use '1: text'."),
    (re.compile(r"&#46;"), "Avoid visible HTML entity noise '&#46;'."),
    (re.compile(r"doc_id\[[^\]]+\]"), "Prefer doc_id(q) over doc_id[q] in Mermaid labels."),
]
GENERAL_MERMAID_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]*-[a-z0-9][a-z0-9._-]*-.+-\d{8}_mermaid\.md$")
GENERAL_TOUR_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]*-[a-z0-9][a-z0-9._-]*-.+-\d{8}_codetour\.tour$")
CODE_IN_NODE_LABEL_PATTERN = re.compile(
    r"(?:\[[^\]]*(?:\.[a-zA-Z0-9_]{1,8}|:[0-9]+)[^\]]*\]|"
    r"\{[^\}]*(?:\.[a-zA-Z0-9_]{1,8}|:[0-9]+)[^\}]*\})"
)


def check_mermaid_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []

    if not GENERAL_MERMAID_NAME_PATTERN.match(path.name):
        errors.append(
            f"{path}: Mermaid filename should look like "
            "<tool>-<model>-<feature>-YYYYMMDD_mermaid.md."
        )

    fence_count = len(re.findall(r"```mermaid", text))
    closing_count = len(re.findall(r"^```$", text, flags=re.MULTILINE))
    if fence_count and closing_count < fence_count:
        errors.append(f"{path}: Mermaid fences look unbalanced.")

    for pattern, message in BAD_MERMAID_PATTERNS:
        for match in pattern.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            errors.append(f"{path}:{line}: {message}")
    for match in CODE_IN_NODE_LABEL_PATTERN.finditer(text):
        line = text.count("\n", 0, match.start()) + 1
        errors.append(f"{path}:{line}: Mermaid node labels should not contain code symbols, paths, or line numbers.")

    if "click " not in text:
        errors.append(f"{path}: no Mermaid click targets found; add clickable code links when requested.")
    if text.count("```mermaid") < 2:
        errors.append(f"{path}: expected a main flowchart and at least one stage subflowchart.")
    if "subgraph" not in text:
        errors.append(f"{path}: expected the main flowchart to group stages with subgraph blocks.")
    if "## 整体调用链路" not in text:
        errors.append(f"{path}: missing main report section: ## 整体调用链路")
    if "### 执行流程分析" not in text:
        errors.append(f"{path}: missing stage prose section: ### 执行流程分析")
    for header in ("工具：", "模型：", "分析功能：", "生成日期："):
        if header not in text:
            errors.append(f"{path}: missing metadata line: {header}")

    html_path = path.with_suffix(".html")
    if not html_path.exists():
        errors.append(f"{path}: missing matching HTML export: {html_path}")

    return errors


def check_html_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []
    if "mermaid" not in text:
        errors.append(f"{path}: HTML export does not appear to include Mermaid content.")
    if "cdn.jsdelivr.net/npm/mermaid" not in text:
        errors.append(f"{path}: HTML export does not include the Mermaid.js loader.")
    return errors


def check_tour_file(path: Path) -> list[str]:
    errors: list[str] = []
    if not GENERAL_TOUR_NAME_PATTERN.match(path.name):
        errors.append(
            f"{path}: CodeTour filename should look like "
            "<tool>-<model>-<feature>-YYYYMMDD_codetour.tour."
        )
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"{path}: invalid JSON: {exc}"]

    if not isinstance(data, dict):
        return [f"{path}: CodeTour root must be a JSON object."]
    if not data.get("title"):
        errors.append(f"{path}: missing title.")
    steps = data.get("steps")
    if not isinstance(steps, list) or not steps:
        errors.append(f"{path}: missing non-empty steps array.")
        return errors

    for idx, step in enumerate(steps, start=1):
        if not isinstance(step, dict):
            errors.append(f"{path}: step {idx} must be an object.")
            continue
        if not step.get("file"):
            errors.append(f"{path}: step {idx} missing file.")
        if not isinstance(step.get("line"), int) or step.get("line", 0) < 1:
            errors.append(f"{path}: step {idx} line must be a 1-based integer.")
        if not step.get("description"):
            errors.append(f"{path}: step {idx} missing description.")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", default=".tour", help="Tour directory or file to check.")
    args = parser.parse_args()

    root = Path(args.path)
    if not root.exists():
        print(f"missing path: {root}", file=sys.stderr)
        return 2

    files = [root] if root.is_file() else sorted(root.glob("*"))
    errors: list[str] = []
    if root.is_dir():
        mermaid_files = [path for path in files if path.suffix == ".md" and "mermaid" in path.name]
        if len(mermaid_files) > 1:
            names = ", ".join(path.name for path in mermaid_files)
            errors.append(f"{root}: expected exactly one Mermaid Markdown file, found {len(mermaid_files)}: {names}")
    checked = 0
    for path in files:
        if path.suffix == ".md" and "mermaid" in path.name:
            checked += 1
            errors.extend(check_mermaid_file(path))
        elif path.suffix == ".html" and "mermaid" in path.name:
            checked += 1
            errors.extend(check_html_file(path))
        elif path.suffix == ".tour":
            checked += 1
            errors.extend(check_tour_file(path))

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print(f"feature-code-tour check passed ({checked} artifact(s) checked).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
