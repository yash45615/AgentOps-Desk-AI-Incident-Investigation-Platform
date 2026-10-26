import json
from collections import Counter
from pathlib import Path
from typing import Any

from app.engine.investigation_engine import EvidenceInput, analyze_evidence


def load_cases(dataset_path: Path) -> list[dict[str, Any]]:
    """Load and validate the basic structure of an evaluation dataset."""
    with dataset_path.open("r", encoding="utf-8") as file:
        cases = json.load(file)

    if not isinstance(cases, list):
        raise ValueError("Evaluation dataset must be a JSON array.")

    seen_case_ids: set[str] = set()

    for case in cases:
        if not isinstance(case, dict):
            raise ValueError("Each evaluation case must be a JSON object.")

        case_id = case.get("case_id")
        evidence = case.get("evidence")
        expected = case.get("expected_rule_ids")

        if not isinstance(case_id, str) or not case_id.strip():
            raise ValueError("Each case must have a non-empty case_id.")
        if case_id in seen_case_ids:
            raise ValueError(f"Duplicate case_id: {case_id}")
        seen_case_ids.add(case_id)

        if not isinstance(evidence, list):
            raise ValueError(f"{case_id}: evidence must be a list.")
        if not isinstance(expected, list) or not all(isinstance(item, str) for item in expected):
            raise ValueError(f"{case_id}: expected_rule_ids must be strings.")

        for item in evidence:
            required = ("id", "evidence_type", "title", "content", "source")
            if not isinstance(item, dict) or any(
                not isinstance(item.get(field), str) for field in required
            ):
                raise ValueError(
                    f"{case_id}: each evidence item must contain string "
                    "fields id, evidence_type, title, content, and source."
                )

    return cases


def calculate_metrics(
    expected: set[str],
    predicted: set[str],
) -> dict[str, int | float]:
    true_positives = len(expected & predicted)
    false_positives = len(predicted - expected)
    false_negatives = len(expected - predicted)

    precision = (
        true_positives / (true_positives + false_positives)
        if true_positives + false_positives
        else (1.0 if not expected and not predicted else 0.0)
    )
    recall = (
        true_positives / (true_positives + false_negatives)
        if true_positives + false_negatives
        else 1.0
    )
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0

    return {
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
    }


def evaluate_cases(cases: list[dict[str, Any]]) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    totals: Counter[str] = Counter()
    expected_by_rule: dict[str, set[str]] = {}
    predicted_by_rule: dict[str, set[str]] = {}

    for case in cases:
        evidence = [
            EvidenceInput(
                id=item["id"],
                evidence_type=item["evidence_type"],
                title=item["title"],
                content=item["content"],
                source=item["source"],
            )
            for item in case["evidence"]
        ]

        expected = set(case["expected_rule_ids"])
        result = analyze_evidence(evidence)
        predicted = {str(finding["rule_id"]) for finding in result.findings}

        case_metrics = calculate_metrics(expected, predicted)
        totals.update(
            {
                "true_positives": int(case_metrics["true_positives"]),
                "false_positives": int(case_metrics["false_positives"]),
                "false_negatives": int(case_metrics["false_negatives"]),
            }
        )

        for rule_id in expected | predicted:
            expected_by_rule.setdefault(rule_id, set())
            predicted_by_rule.setdefault(rule_id, set())
            if rule_id in expected:
                expected_by_rule[rule_id].add(case["case_id"])
            if rule_id in predicted:
                predicted_by_rule[rule_id].add(case["case_id"])

        results.append(
            {
                "case_id": case["case_id"],
                "description": case.get("description", ""),
                "expected_rule_ids": sorted(expected),
                "predicted_rule_ids": sorted(predicted),
                "correct": expected == predicted,
                "metrics": case_metrics,
            }
        )

    aggregate = calculate_metrics(
        {
            f"{case_id}:{rule_id}"
            for rule_id, case_ids in expected_by_rule.items()
            for case_id in case_ids
        },
        {
            f"{case_id}:{rule_id}"
            for rule_id, case_ids in predicted_by_rule.items()
            for case_id in case_ids
        },
    )

    per_rule = {}
    for rule_id in sorted(expected_by_rule.keys() | predicted_by_rule.keys()):
        expected_cases = expected_by_rule.get(rule_id, set())
        predicted_cases = predicted_by_rule.get(rule_id, set())
        per_rule[rule_id] = calculate_metrics(
            {f"{case_id}:{rule_id}" for case_id in expected_cases},
            {f"{case_id}:{rule_id}" for case_id in predicted_cases},
        )

    correct_cases = sum(item["correct"] for item in results)
    case_accuracy = correct_cases / len(results) if results else 1.0

    return {
        "dataset_cases": len(cases),
        "correct_cases": correct_cases,
        "case_accuracy": round(case_accuracy, 4),
        "aggregate": aggregate,
        "per_rule": per_rule,
        "results": results,
    }


def write_report(report: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2, ensure_ascii=False)
        file.write("\n")
