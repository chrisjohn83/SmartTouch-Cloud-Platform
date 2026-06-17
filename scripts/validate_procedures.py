from pathlib import Path
import re
import json

print("VALIDATOR VERSION 2")

results = []

## quality rules
WEAK_EXPECTED_RESULTS = [
    "success",
    "completed",
    "done",
    "working",
    "works"
]

AMBIGUOUS_TERMS = [
    "click here",
    "configure settings",
    "appropriate button",
    "simply",
    "easily",
    "obviously",
    "somehow"
]

def extract_content_type(content):

    match = re.search(
        r"content_type:\s*(\w+)",
        content,
        re.IGNORECASE
    )

    if match:
        return match.group(1).lower()

    return "unknown"


def find_weak_instructions(step):

    findings = []

    lower_step = step.lower()

    for term in AMBIGUOUS_TERMS:

        if term in lower_step:
            findings.append(term)

    return findings


def extract_expected_result(content):

    match = re.search(
        r"## Expected Result\s*\n(.*?)(?=\n## |\Z)",
        content,
        re.DOTALL
    )

    if match:
        return match.group(1).strip()

    return ""

def validate_expected_result(content):

    issues = []

    result = extract_expected_result(
        content
    )

    if not result:

        issues.append(
            "Expected Result section is empty"
        )

        return issues

    if len(result.split()) < 5:

        issues.append(
            "Expected Result is too short"
        )

    lower_result = result.lower()

    for term in WEAK_EXPECTED_RESULTS:

        if lower_result == term:

            issues.append(
                f"Expected Result is vague: {term}"
            )

    return issues

docs_dir = Path("docs")

print(f"Scanning: {docs_dir.resolve()}")

for md_file in docs_dir.rglob("*.md"):

    content = md_file.read_text(
        encoding="utf-8"
    )


    #
    expected_result_issues = (
    validate_expected_result(
        content
    )
 )
   
    steps = re.findall(
        r'^\s*\d+\.\s+(.+)$',
        content,
        re.MULTILINE
    )

    print(f"{md_file}: {len(steps)} steps found")

    if not steps:
        continue

    score = 0
    issues = []

    #
    # Prerequisites
    #
    if "## Prerequisites" in content:
        score += 20
    else:
        issues.append(
            "Missing Prerequisites section"
        )

    #
    # Steps
    #
    if len(steps) > 0:
        score += 20
    else:
        issues.append(
            "No procedure steps found"
        )


    #
    # Expected Result
    #
    if not expected_result_issues:

        score += 20

    else:

        issues.extend(
            expected_result_issues
        )

    #
    # Troubleshooting
    #
    if "## Troubleshooting" in content:
        score += 20
    else:
        issues.append(
            "Missing Troubleshooting section"
        )

    #
    # Weak Instruction Validation
    #
    weak_steps = []

    for step in steps:

        matches = find_weak_instructions(step)

        if matches:

            weak_steps.append({
                "step": step,
                "matches": matches
            })

    if not weak_steps:

        score += 20

    else:

        for weak in weak_steps:

            issues.append(
                f"Weak step: '{weak['step']}' "
                f"(matched: {', '.join(weak['matches'])})"
            )

    results.append({
        "file": str(md_file),
        "score": score,
        "issues": issues
    })
#
# Summary
#
print(f"\nResults count: {len(results)}")

#
# Build Directory
#
Path("build").mkdir(
    exist_ok=True
)

#
# JSON Report
#
with open(
    "build/validation_report.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        results,
        f,
        indent=2
    )

#
# Console Report
#
for result in results:

    print()
    print(result["file"])
    print(f"Score: {result['score']}/100")

    if not result["issues"]:

        print(" - No issues found")

    else:

        for issue in result["issues"]:

            print(
                f" - {issue}"
            )