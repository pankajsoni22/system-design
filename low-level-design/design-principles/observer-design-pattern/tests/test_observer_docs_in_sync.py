"""Guards the tutorial: code shown in README.md must match the real source files."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TITLED_BLOCK = re.compile(
    r'^```python title="([^"]+)"\n(.*?)^```', re.DOTALL | re.MULTILINE
)


def test_embedded_code_matches_source_files() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    blocks = TITLED_BLOCK.findall(readme)

    assert blocks, "README.md has no titled code blocks to check"
    for title, body in blocks:
        source = (ROOT / title).read_text(encoding="utf-8")
        assert body == source, f"{title} in README.md is out of sync with the file"
