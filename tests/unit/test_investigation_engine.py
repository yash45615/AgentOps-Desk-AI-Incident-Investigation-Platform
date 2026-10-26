from app.engine.investigation_engine import EvidenceInput, analyze_evidence


def make_evidence(
    evidence_id: str,
    content: str,
    *,
    title: str = "Test evidence",
    evidence_type: str = "log",
) -> EvidenceInput:
    return EvidenceInput(
        id=evidence_id,
        evidence_type=evidence_type,
        title=title,
        content=content,
        source="unit-test",
    )


def test_detects_timeout_and_links_evidence() -> None:
    result = analyze_evidence([make_evidence("ev-1", "Request timed out after 30 seconds.")])

    assert result.engine_version == "rules-v1"
    assert result.confidence > 0
    assert any(
        finding["rule_id"] == "timeout" and finding["evidence_id"] == "ev-1"
        for finding in result.findings
    )


def test_detects_multiple_failure_signals() -> None:
    result = analyze_evidence(
        [
            make_evidence("ev-1", "HTTP 503 service unavailable"),
            make_evidence("ev-2", "Connection refused by upstream"),
        ]
    )

    rule_ids = {finding["rule_id"] for finding in result.findings}
    assert "server_error" in rule_ids
    assert "connection_failure" in rule_ids


def test_deduplicates_same_rule_for_same_evidence() -> None:
    result = analyze_evidence(
        [
            make_evidence(
                "ev-1",
                "Timeout occurred. The request timed out.",
            )
        ]
    )

    timeout_findings = [finding for finding in result.findings if finding["rule_id"] == "timeout"]
    assert len(timeout_findings) == 1


def test_no_evidence_returns_zero_confidence() -> None:
    result = analyze_evidence([])

    assert result.findings == []
    assert result.confidence == 0.0
    assert "No evidence" in result.summary


def test_unmatched_evidence_does_not_claim_root_cause() -> None:
    result = analyze_evidence([make_evidence("ev-1", "Routine deployment completed successfully.")])

    assert result.findings == []
    assert result.confidence == 0.25
    assert "does not rule out a problem" in result.summary


def test_finding_excerpt_is_limited() -> None:
    result = analyze_evidence([make_evidence("ev-1", "Timeout " + "x" * 400)])

    assert result.findings
    assert len(result.findings[0]["excerpt"]) <= 240
