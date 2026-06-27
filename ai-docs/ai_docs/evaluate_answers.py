"""Evaluate generated SmartTouch documentation answers."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .answer_generator import INSUFFICIENT_CITED_INFORMATION
from .retrieval_service import answer_question


def load_cases(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as file:
        cases = json.load(file)

    if not isinstance(cases, list):
        raise ValueError("Answer evaluation fixture must contain a list")

    return cases


def evaluate_answer_response(
    case: dict[str, Any],
    response: dict[str, Any],
) -> list[str]:
    failures: list[str] = []

    answer = str(response.get("answer", ""))
    answer_lower = answer.casefold()
    citations = response.get("citations", [])

    required_citations = case.get("required_citations", [])
    for citation in required_citations:
        if citation not in citations:
            failures.append(f"missing required citation: {citation}")

    allowed_citations = set(required_citations)
    for citation in citations:
        if citation not in allowed_citations:
            failures.append(f"unexpected citation: {citation}")

    for text in case.get("required_answer_contains", []):
        if str(text).casefold() not in answer_lower:
            failures.append(f"answer missing required text: {text}")

    for text in case.get("forbidden_answer_contains", []):
        if str(text).casefold() in answer_lower:
            failures.append(f"answer contains forbidden text: {text}")

    if not case.get("allow_fallback", False):
        if answer == INSUFFICIENT_CITED_INFORMATION:
            failures.append("answer unexpectedly returned fallback")

    return failures


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Evaluate SmartTouch generated answers."
    )
    parser.add_argument(
        "--cases",
        type=Path,
        default=Path("tests/fixtures/answer-evaluation.json"),
    )
    parser.add_argument("--limit", type=int, default=3)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    cases = load_cases(args.cases)

    total = len(cases)
    failed = 0

    for case in cases:
        query = case["query"]
        response = answer_question(query, limit=args.limit)
        failures = evaluate_answer_response(case, response)

        print(f"Query: {query}")
        if failures:
            failed += 1
            print("Status: FAIL")
            for failure in failures:
                print(f"- {failure}")
        else:
            print("Status: PASS")
        print()

    print(f"Cases: {total}")
    print(f"Passed: {total - failed}")
    print(f"Failed: {failed}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
