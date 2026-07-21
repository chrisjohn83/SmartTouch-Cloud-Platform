from pathlib import Path
import re

docs_dir = Path("docs")

for md_file in docs_dir.rglob("*.md"):

    content = md_file.read_text(encoding="utf-8")

    steps = re.findall(
        r'^\d+\.\s+(.+)$',
        content,
        re.MULTILINE
    )

    if steps:
        print(f"\n{md_file}")

        for idx, step in enumerate(steps, start=1):
            print(f"{idx}. {step}")