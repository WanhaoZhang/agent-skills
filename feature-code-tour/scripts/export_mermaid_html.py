#!/usr/bin/env python3
"""Export Mermaid Markdown tour files to standalone HTML."""

from __future__ import annotations

import argparse
import html
from pathlib import Path


HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
    :root {{
      color-scheme: light dark;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.5;
    }}
    body {{
      margin: 0;
      padding: 32px;
      background: Canvas;
      color: CanvasText;
    }}
    main {{
      max-width: 1200px;
      margin: 0 auto;
    }}
    h1, h2, h3 {{
      line-height: 1.2;
    }}
    pre {{
      overflow-x: auto;
      padding: 16px;
      border: 1px solid color-mix(in srgb, CanvasText 18%, transparent);
      border-radius: 8px;
    }}
    pre.mermaid {{
      background: color-mix(in srgb, Canvas 94%, CanvasText);
    }}
    code {{
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    }}
    a {{
      color: LinkText;
    }}
  </style>
  <script type="module">
    import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs";
    mermaid.initialize({{ startOnLoad: true, securityLevel: "loose" }});
  </script>
</head>
<body>
  <main>
{body}
  </main>
</body>
</html>
"""


def iter_mermaid_markdown(path: Path) -> list[Path]:
    if path.is_file():
        return [path] if path.suffix == ".md" and path.name.endswith("_mermaid.md") else []
    return sorted(path.glob("*_mermaid.md"))


def render_inline(text: str) -> str:
    escaped = html.escape(text)
    parts = escaped.split("`")
    if len(parts) == 1:
        return escaped
    rendered: list[str] = []
    for idx, part in enumerate(parts):
        if idx % 2:
            rendered.append(f"<code>{part}</code>")
        else:
            rendered.append(part)
    return "".join(rendered)


def render_markdown(text: str) -> str:
    lines = text.splitlines()
    out: list[str] = []
    paragraph: list[str] = []
    in_fence = False
    fence_lang = ""
    fence_lines: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            out.append(f"    <p>{render_inline(' '.join(paragraph))}</p>")
            paragraph.clear()

    def flush_fence() -> None:
        code = html.escape("\n".join(fence_lines))
        if fence_lang == "mermaid":
            out.append(f"    <pre class=\"mermaid\">{code}</pre>")
        else:
            out.append(f"    <pre><code>{code}</code></pre>")

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            if in_fence:
                flush_fence()
                in_fence = False
                fence_lang = ""
                fence_lines = []
            else:
                flush_paragraph()
                in_fence = True
                fence_lang = stripped[3:].strip()
                fence_lines = []
            continue

        if in_fence:
            fence_lines.append(line)
            continue

        if not stripped:
            flush_paragraph()
            continue

        if stripped.startswith("#"):
            flush_paragraph()
            level = len(stripped) - len(stripped.lstrip("#"))
            if 1 <= level <= 6 and stripped[level:level + 1] == " ":
                content = render_inline(stripped[level + 1 :])
                out.append(f"    <h{level}>{content}</h{level}>")
                continue

        if stripped.startswith("- "):
            flush_paragraph()
            out.append(f"    <p>- {render_inline(stripped[2:])}</p>")
            continue

        paragraph.append(stripped)

    if in_fence:
        flush_fence()
    flush_paragraph()
    return "\n".join(out)


def export_file(path: Path) -> Path:
    text = path.read_text(encoding="utf-8")
    title = path.stem.replace("_", " ").title()
    body = render_markdown(text)
    output = path.with_suffix(".html")
    output.write_text(HTML_TEMPLATE.format(title=html.escape(title), body=body), encoding="utf-8")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", default=".tour", help="Tour directory or *_mermaid.md file.")
    args = parser.parse_args()

    root = Path(args.path)
    if not root.exists():
        parser.error(f"missing path: {root}")

    files = iter_mermaid_markdown(root)
    if not files:
        print(f"no *_mermaid.md files found under {root}")
        return 0

    for source in files:
        output = export_file(source)
        print(f"exported {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
