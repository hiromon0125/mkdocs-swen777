"""Generate a fixed, offline MkDocs corpus in container-local storage."""
import hashlib
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
docs = root / "docs"
docs.mkdir(parents=True, exist_ok=True)
(root / "mkdocs.yml").write_text(
    "site_name: Performance Fixture\nsite_url: http://app:8000/\n"
    "theme: mkdocs\nplugins: [search]\n"
    "markdown_extensions: [tables, fenced_code]\n",
    encoding="utf-8",
)
(docs / "index.md").write_text(
    "# Performance Fixture\n\nA deterministic offline documentation site.\n\n"
    + "\n".join(f"- [Page {i}](page-{i:02d}.md)" for i in range(20)),
    encoding="utf-8",
)
for i in range(20):
    text = f"# Page {i}\n\n"
    for j in range(16):
        text += f"## Section {j}\n\n"
        text += (f"Document {i}, section {j}: reproducible Markdown content for HTTP performance testing. " * 8)
        text += "\n\n```python\nprint('MkDocs performance')\n```\n\n"
    (docs / f"page-{i:02d}.md").write_text(text, encoding="utf-8")
files = sorted(p for p in root.rglob("*") if p.is_file())
manifest = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
(root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
