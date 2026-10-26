import argparse
import json
from pathlib import Path

from app.evaluation.evaluator import evaluate_cases, load_cases, write_report

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = ROOT / "data" / "evaluations" / "investigation_cases.json"
DEFAULT_REPORT = ROOT / "reports" / "evaluations" / "latest.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate the AgentOps Desk investigation engine.")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    cases = load_cases(args.dataset)
    report = evaluate_cases(cases)
    write_report(report, args.output)

    print(
        json.dumps(
            {
                "dataset_cases": report["dataset_cases"],
                "correct_cases": report["correct_cases"],
                "case_accuracy": report["case_accuracy"],
                "aggregate": report["aggregate"],
                "report_path": str(args.output),
            },
            indent=2,
        )
    )

    return 0 if report["correct_cases"] == report["dataset_cases"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
