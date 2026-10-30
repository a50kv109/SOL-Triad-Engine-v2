"""
Unit tests for EvidenceValidator.
"""

from sol_triad.models import (
    SourcePrimitive,
    EvidenceRecord,
    EpistemicStatus,
    CoherenceVerdict,
    DiagnosticCode,
)
from sol_triad.evidence import InMemoryEvidenceRegistry
from sol_triad.validators import EvidenceValidator


def test_valid_fact_passes():
    registry = InMemoryEvidenceRegistry()
    registry.register(EvidenceRecord(
        evidence_id="ev-1",
        domain="energy",
        epistemic_status=EpistemicStatus.FACT,
        timestamp_sec=100.0,
        payload_hash="sha256-abc"
    ))

    source = SourcePrimitive(
        evidence_id="ev-1",
        authority_domain={"energy", "thermal"},
        granted_scope={"sensor_1"},
        granted_loss_domains={"heat"},
        epistemic_type=EpistemicStatus.FACT,
        timestamp_sec=100.0,
        max_age_sec=300.0,
        payload_hash="sha256-abc"
    )

    validator = EvidenceValidator(registry, current_time_sec=150.0)
    is_valid, verdict, diags = validator.validate(source)

    assert is_valid is True
    assert verdict == CoherenceVerdict.PASS
    assert any(d.code == DiagnosticCode.EVIDENCE_PASS for d in diags)


def test_future_timestamp_fails():
    registry = InMemoryEvidenceRegistry()
    source = SourcePrimitive(
        evidence_id="ev-future",
        authority_domain={"energy"},
        granted_scope={"sensor_1"},
        granted_loss_domains={"heat"},
        epistemic_type=EpistemicStatus.FACT,
        timestamp_sec=500.0,
        max_age_sec=300.0,
    )

    validator = EvidenceValidator(registry, current_time_sec=200.0)
    is_valid, verdict, diags = validator.validate(source)

    assert is_valid is False
    assert verdict == CoherenceVerdict.FAIL
    assert any(d.code == DiagnosticCode.TEMPORAL_FUTURE for d in diags)


def test_invalid_max_age_fails():
    registry = InMemoryEvidenceRegistry()
    source = SourcePrimitive(
        evidence_id="ev-bad-age",
        authority_domain={"energy"},
        granted_scope={"sensor_1"},
        granted_loss_domains={"heat"},
        epistemic_type=EpistemicStatus.FACT,
        timestamp_sec=100.0,
        max_age_sec=-10.0,
    )

    validator = EvidenceValidator(registry, current_time_sec=120.0)
    is_valid, verdict, diags = validator.validate(source)

    assert is_valid is False
    assert verdict == CoherenceVerdict.FAIL
    assert any(d.code == DiagnosticCode.TEMPORAL_INVALID_LIMIT for d in diags)


def test_stale_evidence_returns_review():
    registry = InMemoryEvidenceRegistry()
    registry.register(EvidenceRecord(
        evidence_id="ev-stale",
        domain="energy",
        epistemic_status=EpistemicStatus.FACT,
        timestamp_sec=100.0
    ))
    source = SourcePrimitive(
        evidence_id="ev-stale",
        authority_domain={"energy"},
        granted_scope={"sensor_1"},
        granted_loss_domains={"heat"},
        epistemic_type=EpistemicStatus.FACT,
        timestamp_sec=100.0,
        max_age_sec=60.0,
    )

    # current_time is 200, age is 100 > max_age 60
    validator = EvidenceValidator(registry, current_time_sec=200.0)
    is_valid, verdict, diags = validator.validate(source)

    assert is_valid is False
    assert verdict == CoherenceVerdict.REVIEW
    assert any(d.code == DiagnosticCode.TEMPORAL_STALE for d in diags)


def test_registry_offline_returns_review():
    source = SourcePrimitive(
        evidence_id="ev-1",
        authority_domain={"energy"},
        granted_scope={"sensor_1"},
        granted_loss_domains={"heat"},
        epistemic_type=EpistemicStatus.FACT,
        timestamp_sec=100.0,
        max_age_sec=300.0,
    )

    validator = EvidenceValidator(None, current_time_sec=150.0)
    is_valid, verdict, diags = validator.validate(source)

    assert is_valid is False
    assert verdict == CoherenceVerdict.REVIEW
    assert any(d.code == DiagnosticCode.REGISTRY_OFFLINE for d in diags)


def test_forged_evidence_id_fails():
    registry = InMemoryEvidenceRegistry()
    source = SourcePrimitive(
        evidence_id="ev-ghost-999",
        authority_domain={"energy"},
        granted_scope={"sensor_1"},
        granted_loss_domains={"heat"},
        epistemic_type=EpistemicStatus.FACT,
        timestamp_sec=100.0,
        max_age_sec=300.0,
    )

    validator = EvidenceValidator(registry, current_time_sec=150.0)
    is_valid, verdict, diags = validator.validate(source)

    assert is_valid is False
    assert verdict == CoherenceVerdict.FAIL
    assert any(d.code == DiagnosticCode.EVIDENCE_NOT_FOUND for d in diags)


def test_epistemic_status_mismatch_fails():
    registry = InMemoryEvidenceRegistry()
    registry.register(EvidenceRecord(
        evidence_id="ev-claim",
        domain="energy",
        epistemic_status=EpistemicStatus.UNKNOWN,
        timestamp_sec=100.0
    ))
    source = SourcePrimitive(
        evidence_id="ev-claim",
        authority_domain={"energy"},
        granted_scope={"sensor_1"},
        granted_loss_domains={"heat"},
        epistemic_type=EpistemicStatus.FACT,
        timestamp_sec=100.0,
        max_age_sec=300.0,
    )

    validator = EvidenceValidator(registry, current_time_sec=150.0)
    is_valid, verdict, diags = validator.validate(source)

    assert is_valid is False
    assert verdict == CoherenceVerdict.FAIL
    assert any(d.code == DiagnosticCode.EVIDENCE_MISMATCH for d in diags)


def test_inference_with_valid_corroboration_passes():
    registry = InMemoryEvidenceRegistry()
    registry.register(EvidenceRecord(
        evidence_id="inf-root",
        domain="telemetry",
        epistemic_status=EpistemicStatus.INFERENCE,
        timestamp_sec=100.0,
        corroborating_evidence_ids={"corrob-1"}
    ))
    registry.register(EvidenceRecord(
        evidence_id="corrob-1",
        domain="telemetry",
        epistemic_status=EpistemicStatus.FACT,
        timestamp_sec=95.0
    ))

    source = SourcePrimitive(
        evidence_id="inf-root",
        authority_domain={"telemetry"},
        granted_scope={"sensor_1"},
        granted_loss_domains={"power"},
        epistemic_type=EpistemicStatus.INFERENCE,
        timestamp_sec=100.0,
        max_age_sec=300.0,
        corroborating_evidence_ids={"corrob-1"}
    )

    validator = EvidenceValidator(registry, current_time_sec=120.0)
    is_valid, verdict, diags = validator.validate(source)

    assert is_valid is True
    assert verdict == CoherenceVerdict.PASS


def test_inference_without_corroboration_returns_review():
    registry = InMemoryEvidenceRegistry()
    registry.register(EvidenceRecord(
        evidence_id="inf-bare",
        domain="telemetry",
        epistemic_status=EpistemicStatus.INFERENCE,
        timestamp_sec=100.0,
        corroborating_evidence_ids=set()
    ))

    source = SourcePrimitive(
        evidence_id="inf-bare",
        authority_domain={"telemetry"},
        granted_scope={"sensor_1"},
        granted_loss_domains={"power"},
        epistemic_type=EpistemicStatus.INFERENCE,
        timestamp_sec=100.0,
        max_age_sec=300.0,
        corroborating_evidence_ids=set()  # empty!
    )

    validator = EvidenceValidator(registry, current_time_sec=120.0)
    is_valid, verdict, diags = validator.validate(source)

    assert is_valid is False
    assert verdict == CoherenceVerdict.REVIEW
    assert any(d.code == DiagnosticCode.INFERENCE_UNSUPPORTED for d in diags)
