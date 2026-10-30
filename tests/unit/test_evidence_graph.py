"""Regression tests for recursive validation of inference provenance."""

import pytest

from sol_triad.evidence import InMemoryEvidenceRegistry
from sol_triad.models import (
    CoherenceVerdict,
    DiagnosticCode,
    EpistemicStatus,
    EvidenceRecord,
    SourcePrimitive,
)
from sol_triad.validators import EvidenceValidator


NOW = 1_000.0
DOMAIN = "telemetry"


def _record(
    evidence_id: str,
    status: EpistemicStatus,
    premises: set[str] | None = None,
    timestamp: float = NOW,
) -> EvidenceRecord:
    return EvidenceRecord(
        evidence_id=evidence_id,
        domain=DOMAIN,
        epistemic_status=status,
        timestamp_sec=timestamp,
        corroborating_evidence_ids=premises,
    )


def _validate(
    registry: InMemoryEvidenceRegistry,
    premises: set[str],
) -> tuple[bool, CoherenceVerdict, list]:
    source = SourcePrimitive(
        evidence_id="root",
        authority_domain={DOMAIN},
        granted_scope={"sensor"},
        granted_loss_domains={"power"},
        epistemic_type=EpistemicStatus.INFERENCE,
        timestamp_sec=NOW,
        max_age_sec=300.0,
        corroborating_evidence_ids=premises,
    )
    return EvidenceValidator(registry, current_time_sec=NOW).validate(source)


def test_nested_inference_chain_passes_when_every_inference_has_registered_premises():
    registry = InMemoryEvidenceRegistry()
    registry.register(_record("root", EpistemicStatus.INFERENCE, {"middle"}))
    registry.register(_record("middle", EpistemicStatus.INFERENCE, {"fact"}))
    registry.register(_record("fact", EpistemicStatus.FACT))

    valid, verdict, diagnostics = _validate(registry, {"middle"})

    assert valid is True
    assert verdict == CoherenceVerdict.PASS
    assert not any(d.code == DiagnosticCode.INFERENCE_CHAIN_INCOMPLETE for d in diagnostics)


def test_source_and_registry_inference_premises_must_match():
    registry = InMemoryEvidenceRegistry()
    registry.register(_record("root", EpistemicStatus.INFERENCE, {"registered-premise"}))
    registry.register(_record("agent-premise", EpistemicStatus.FACT))
    registry.register(_record("registered-premise", EpistemicStatus.FACT))

    valid, verdict, diagnostics = _validate(registry, {"agent-premise"})

    assert valid is False
    assert verdict == CoherenceVerdict.FAIL
    assert any(d.code == DiagnosticCode.EVIDENCE_MISMATCH for d in diagnostics)


@pytest.mark.parametrize("registered_status", [EpistemicStatus.FACT, EpistemicStatus.UNKNOWN])
def test_source_inference_status_must_match_registry(registered_status: EpistemicStatus):
    registry = InMemoryEvidenceRegistry()
    registry.register(_record("root", registered_status))

    valid, verdict, diagnostics = _validate(registry, {"premise"})

    assert valid is False
    assert verdict == CoherenceVerdict.FAIL
    assert any(d.code == DiagnosticCode.EVIDENCE_MISMATCH for d in diagnostics)


def test_inference_without_registered_premises_returns_review():
    registry = InMemoryEvidenceRegistry()
    registry.register(_record("root", EpistemicStatus.INFERENCE))

    valid, verdict, diagnostics = _validate(registry, set())

    assert valid is False
    assert verdict == CoherenceVerdict.REVIEW
    assert any(d.code == DiagnosticCode.INFERENCE_CHAIN_INCOMPLETE for d in diagnostics)


def test_missing_premise_in_available_registry_fails():
    registry = InMemoryEvidenceRegistry()
    registry.register(_record("root", EpistemicStatus.INFERENCE, {"missing"}))

    valid, verdict, diagnostics = _validate(registry, {"missing"})

    assert valid is False
    assert verdict == CoherenceVerdict.FAIL
    assert any(d.code == DiagnosticCode.EVIDENCE_NOT_FOUND for d in diagnostics)


def test_unknown_nested_premise_fails():
    registry = InMemoryEvidenceRegistry()
    registry.register(_record("root", EpistemicStatus.INFERENCE, {"unknown"}))
    registry.register(_record("unknown", EpistemicStatus.UNKNOWN))

    valid, verdict, diagnostics = _validate(registry, {"unknown"})

    assert valid is False
    assert verdict == CoherenceVerdict.FAIL
    assert any(d.code == DiagnosticCode.INFERENCE_PREMISE_INVALID_STATUS for d in diagnostics)


def test_nested_inference_without_registered_premises_returns_review():
    registry = InMemoryEvidenceRegistry()
    registry.register(_record("root", EpistemicStatus.INFERENCE, {"middle"}))
    registry.register(_record("middle", EpistemicStatus.INFERENCE))

    valid, verdict, diagnostics = _validate(registry, {"middle"})

    assert valid is False
    assert verdict == CoherenceVerdict.REVIEW
    assert any(d.code == DiagnosticCode.INFERENCE_CHAIN_INCOMPLETE for d in diagnostics)


def test_nested_cycle_fails():
    registry = InMemoryEvidenceRegistry()
    registry.register(_record("root", EpistemicStatus.INFERENCE, {"middle"}))
    registry.register(_record("middle", EpistemicStatus.INFERENCE, {"root"}))

    valid, verdict, diagnostics = _validate(registry, {"middle"})

    assert valid is False
    assert verdict == CoherenceVerdict.FAIL
    assert any(d.code == DiagnosticCode.INFERENCE_CIRCULAR_DEPENDENCY for d in diagnostics)


def test_shared_fact_dependency_in_dag_is_not_a_cycle():
    registry = InMemoryEvidenceRegistry()
    registry.register(_record("root", EpistemicStatus.INFERENCE, {"left", "right"}))
    registry.register(_record("left", EpistemicStatus.INFERENCE, {"shared"}))
    registry.register(_record("right", EpistemicStatus.INFERENCE, {"shared"}))
    registry.register(_record("shared", EpistemicStatus.FACT))

    valid, verdict, diagnostics = _validate(registry, {"left", "right"})

    assert valid is True
    assert verdict == CoherenceVerdict.PASS
    assert not any(d.code == DiagnosticCode.INFERENCE_CIRCULAR_DEPENDENCY for d in diagnostics)


@pytest.mark.parametrize(
    ("timestamp", "expected_verdict", "expected_code"),
    [
        (NOW - 301.0, CoherenceVerdict.REVIEW, DiagnosticCode.TEMPORAL_STALE),
        (NOW + 1.0, CoherenceVerdict.FAIL, DiagnosticCode.TEMPORAL_FUTURE),
        (float("nan"), CoherenceVerdict.FAIL, DiagnosticCode.STATE_INVALID_NUMERIC),
    ],
)
def test_nested_premise_timestamp_is_validated(timestamp, expected_verdict, expected_code):
    registry = InMemoryEvidenceRegistry()
    registry.register(_record("root", EpistemicStatus.INFERENCE, {"premise"}))
    registry.register(_record("premise", EpistemicStatus.FACT, timestamp=timestamp))

    valid, verdict, diagnostics = _validate(registry, {"premise"})

    assert valid is False
    assert verdict == expected_verdict
    assert any(d.code == expected_code for d in diagnostics)


def test_registry_becoming_unavailable_during_graph_walk_returns_review():
    class RegistryGoesOfflineAfterRootLookup(InMemoryEvidenceRegistry):
        def get_record(self, evidence_id: str):
            record = super().get_record(evidence_id)
            if evidence_id == "root":
                self.set_available(False)
            return record

    registry = RegistryGoesOfflineAfterRootLookup()
    registry.register(_record("root", EpistemicStatus.INFERENCE, {"premise"}))
    registry.register(_record("premise", EpistemicStatus.FACT))

    valid, verdict, diagnostics = _validate(registry, {"premise"})

    assert valid is False
    assert verdict == CoherenceVerdict.REVIEW
    assert any(d.code == DiagnosticCode.REGISTRY_OFFLINE for d in diagnostics)


def test_evidence_graph_node_limit_returns_review(monkeypatch):
    monkeypatch.setattr(EvidenceValidator, "MAX_INFERENCE_NODES", 2, raising=False)
    registry = InMemoryEvidenceRegistry()
    registry.register(_record("root", EpistemicStatus.INFERENCE, {"middle"}))
    registry.register(_record("middle", EpistemicStatus.INFERENCE, {"fact"}))
    registry.register(_record("fact", EpistemicStatus.FACT))

    valid, verdict, diagnostics = _validate(registry, {"middle"})

    assert valid is False
    assert verdict == CoherenceVerdict.REVIEW
    assert any(
        d.code == DiagnosticCode.INFERENCE_TRAVERSAL_LIMIT_EXCEEDED
        for d in diagnostics
    )


def test_evidence_graph_depth_limit_returns_review(monkeypatch):
    monkeypatch.setattr(EvidenceValidator, "MAX_INFERENCE_DEPTH", 1, raising=False)
    registry = InMemoryEvidenceRegistry()
    registry.register(_record("root", EpistemicStatus.INFERENCE, {"middle"}))
    registry.register(_record("middle", EpistemicStatus.INFERENCE, {"fact"}))
    registry.register(_record("fact", EpistemicStatus.FACT))

    valid, verdict, diagnostics = _validate(registry, {"middle"})

    assert valid is False
    assert verdict == CoherenceVerdict.REVIEW
    assert any(
        d.code == DiagnosticCode.INFERENCE_TRAVERSAL_LIMIT_EXCEEDED
        for d in diagnostics
    )
