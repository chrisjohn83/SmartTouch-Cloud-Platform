from pathlib import Path
import re
import json

docs_dir = Path("docs")

procedures = []

for md_file in docs_dir.rglob("*.md"):

    content = md_file.read_text(
        encoding="utf-8"
    )

    steps = re.findall(
        r'^\d+\.\s+(.+)$',
        content,
        re.MULTILINE
    )

    if not steps:
        continue

    procedure = {
        "file": str(md_file),
        "step_count": len(steps),
        "steps": steps
    }

    procedures.append(procedure)

Path("build").mkdir(
    exist_ok=True
)

with open(
    "build/procedures.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        procedures,
        f,
        indent=2
    )

print(
    f"Exported {len(procedures)} procedures"
)