import re
from dataclasses import dataclass
from typing import Any

ENGINE_VERSION = "rules-v1"


@dataclass(frozen=True)
class EvidenceInput:
    id: str
    evidence_type: str
    title: str
    content: str
    source: str


@dataclass(frozen=True)
class InvestigationResult:
    summary: str
    findings: list[dict[str, Any]]
    confidence: float
    engine_version: str


RULES: tuple[tuple[str, str, str, str], ...] = (
    (
        "timeout",
        r"\b(timeout|timed out|deadline exceeded)\b",
        "Timeout detected",
        "The evidence mentions a timeout or exceeded deadline.",
    ),
    (
        "connection_failure",
        r"\b(connection refused|connection reset|connection error|"
        r"failed to connect|connection failure)\b",
        "Connection failure detected",
        "The evidence indicates a connection failure.",
    ),
    (
        "server_error",
        r"\b(HTTP\s*5\d\d|status(?:\s+code)?\s*[:=]?\s*5\d\d|"
        r"\b5\d\d\s+(?:error|response)\b|internal server error|"
        r"bad gateway|service unavailable|gateway timeout)\b",
        "Server-side error detected",
        "The evidence mentions an HTTP 5xx or equivalent server-side error.",
    ),
    (
        "high_latency",
        r"\b(high latency|latency spike|slow response|"
        r"response time exceeded|latency\s*[:=]\s*[1-9]\d{3,}\s*ms)\b",
        "Elevated latency detected",
        "The evidence suggests a slow response or elevated latency.",
    ),
    (
        "resource_pressure",
        r"\b(out of memory|memory exhausted|CPU\s+(?:usage\s+)?"
        r"(?:at\s+)?(?:9\d|100)%|disk full|resource exhausted)\b",
        "Resource pressure detected",
        "The evidence suggests resource exhaustion or high resource usage.",
    ),
)


def analyze_evidence(
    evidence_items: list[EvidenceInput],
) -> InvestigationResult:
    findings: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    for item in evidence_items:
        text_to_scan = f"{item.title}\n{item.content}"

        for rule_id, pattern, title, description in RULES:
            if not re.search(pattern, text_to_scan, flags=re.IGNORECASE):
                continue

            deduplication_key = (rule_id, item.id)
            if deduplication_key in seen:
                continue
            seen.add(deduplication_key)

            excerpt = re.sub(r"\s+", " ", item.content).strip()[:240]
            findings.append(
                {
                    "rule_id": rule_id,
                    "title": title,
                    "description": description,
                    "evidence_id": item.id,
                    "evidence_title": item.title,
                    "evidence_type": item.evidence_type,
                    "source": item.source,
                    "excerpt": excerpt,
                }
            )

    if not evidence_items:
        summary = (
            "No evidence is available for analysis. "
            "Attach logs, metrics, events, or stack traces and run again."
        )
        confidence = 0.0
    elif findings:
        rule_names = ", ".join(dict.fromkeys(str(finding["title"]) for finding in findings))
        summary = (
            f"Analyzed {len(evidence_items)} evidence item(s) and found "
            f"{len(findings)} signal(s): {rule_names}. "
            "These are rule-based indicators, not proof of root cause."
        )
        evidence_coverage = len({str(finding["evidence_id"]) for finding in findings}) / len(
            evidence_items
        )
        confidence = round(min(0.95, 0.5 + 0.45 * evidence_coverage), 2)
    else:
        summary = (
            f"Analyzed {len(evidence_items)} evidence item(s), but no "
            "known failure patterns matched. This does not rule out a problem."
        )
        confidence = 0.25

    return InvestigationResult(
        summary=summary,
        findings=findings,
        confidence=confidence,
        engine_version=ENGINE_VERSION,
    )
