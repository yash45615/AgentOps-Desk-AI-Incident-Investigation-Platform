import json
from pathlib import Path

import pytest

from app.evaluation.evaluator import (
    calculate_metrics,
    evaluate_cases,
    load_cases,
    write_report,
)

ROOT = Path(__file__).resolve().parents[2]
DATASET = ROOT / "data" / "evaluations" / "investigation_cases.json"


def test_metric_calculation_with_false_positive_and_false_negative() -> None:
    metrics = calculate_metrics(
        {"timeout", "server_error"},
        {"timeout", "high_latency"},
    )

    assert metrics["true_positives"] == 1
    assert metrics["false_positives"] == 1
    assert metrics["false_negatives"] == 1
    assert metrics["precision"] == 0.5
    assert metrics["recall"] == 0.5
    assert metrics["f1"] == 0.5


def test_empty_expected_and_predicted_sets_are_handled() -> None:
    metrics = calculate_metrics(set(), set())

    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 1.0
    assert metrics["f1"] == 1.0


def test_dataset_loads_and_evaluation_is_correct() -> None:
    cases = load_cases(DATASET)
    report = evaluate_cases(cases)

    assert report["dataset_cases"] == 8
    assert report["correct_cases"] == 8
    assert report["case_accuracy"] == 1.0
    assert report["aggregate"]["precision"] == 1.0
    assert report["aggregate"]["recall"] == 1.0
    assert report["aggregate"]["f1"] == 1.0


def test_report_is_written_as_valid_json(tmp_path: Path) -> None:
    report = evaluate_cases(load_cases(DATASET))
    output = tmp_path / "nested" / "evaluation.json"

    write_report(report, output)

    saved = json.loads(output.read_text(encoding="utf-8"))
    assert saved["dataset_cases"] == 8
    assert saved["results"]


def test_duplicate_case_ids_are_rejected(tmp_path: Path) -> None:
    cases = [
        {
            "case_id": "duplicate",
            "evidence": [],
            "expected_rule_ids": [],
        },
        {
            "case_id": "duplicate",
            "evidence": [],
            "expected_rule_ids": [],
        },
    ]
    dataset = tmp_path / "duplicate.json"
    dataset.write_text(json.dumps(cases), encoding="utf-8")

    with pytest.raises(ValueError, match="Duplicate case_id"):
        load_cases(dataset)


def test_invalid_dataset_root_is_rejected(tmp_path: Path) -> None:
    dataset = tmp_path / "invalid.json"
    dataset.write_text('{"case_id": "not-a-list"}', encoding="utf-8")

    with pytest.raises(ValueError, match="JSON array"):
        load_cases(dataset)
