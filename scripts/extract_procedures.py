from pathlib import Path
import yaml
import re

docs_dir = Path("docs")

for md_file in docs_dir.rglob("*.md"):

    content = md_file.read_text(
        encoding="utf-8"
    )

    if not content.startswith("---"):
        continue

    _, frontmatter, body = content.split(
        "---",
        2
    )

    metadata = yaml.safe_load(frontmatter)

    if metadata.get(
        "content_type"
    ) != "procedure":
        continue

    steps = re.findall(
        r'^\d+\.\s+(.+)$',
        body,
        re.MULTILINE
    )

    if steps:
        print(md_file)

        for step in steps:
            print(step)