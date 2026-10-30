"""
Unit tests for SOL-Triad Engine data models.
"""

from sol_triad.models import (
    SourcePrimitive,
    ConstraintPrimitive,
    DissipatePrimitive,
    SystemState,
    EvidenceRecord,
    EpistemicStatus,
    CoherenceVerdict,
    DiagnosticCode,
    DiagnosticSeverity,
    CoherenceDiagnostic,
)
from sol_triad import __version__
from sol_triad.engine import SolTriadEngine


def test_package_and_engine_release_versions_match():
    assert __version__ == "0.4.1"
    assert SolTriadEngine.VERSION == __version__


def test_epistemic_status_values():
    assert EpistemicStatus.FACT.value == "FACT"
    assert EpistemicStatus.INFERENCE.value == "INFERENCE"
    assert EpistemicStatus.UNKNOWN.value == "UNKNOWN"


def test_coherence_verdict_values():
    assert CoherenceVerdict.PASS.value == "PASS"
    assert CoherenceVerdict.REVIEW.value == "REVIEW"
    assert CoherenceVerdict.FAIL.value == "FAIL"


def test_source_primitive_construction():
    s = SourcePrimitive(
        evidence_id="ev-101",
        authority_domain={"hydraulics", "valves"},
        granted_scope={"valve_1", "pump_a"},
        granted_loss_domains={"thermal_loss"},
        epistemic_type=EpistemicStatus.FACT,
        timestamp_sec=1700000000.0,
        max_age_sec=120.0,
    )
    assert s.evidence_id == "ev-101"
    assert "hydraulics" in s.authority_domain
    assert s.max_age_sec == 120.0
    assert s.corroborating_evidence_ids == set()


def test_evidence_record_keeps_legacy_positional_constructor_order():
    metadata = {"origin": "sensor"}
    record = EvidenceRecord(
        "ev-positional",
        "telemetry",
        EpistemicStatus.FACT,
        100.0,
        "sha256-value",
        metadata,
    )

    assert record.payload_hash == "sha256-value"
    assert record.metadata is metadata
    assert record.corroborating_evidence_ids is None


def test_constraint_primitive_construction():
    c = ConstraintPrimitive(
        domain_scope={"hydraulics"},
        target_objects={"valve_1"},
        protected_set={"safety_lock"},
        protected_values={"core_temp": 300.0},
        min_bounds={"pressure": 1.0},
        max_bounds={"pressure": 10.0},
        units={"pressure": "bar", "core_temp": "kelvin"},
        protected_flags={"emergency_stop"},
        forbidden_flags={"override_active": True},
        required_flags={"coolant_flow": True},
    )
    assert "safety_lock" in c.protected_set
    assert c.protected_values["core_temp"] == 300.0
    assert c.forbidden_flags["override_active"] is True


def test_diagnostic_serialization():
    diag = CoherenceDiagnostic(
        code=DiagnosticCode.SCOPE_EXCEEDED_DOMAIN,
        severity=DiagnosticSeverity.ERROR,
        message="Domain unauthorized",
        primitive="CONSTRAINT",
        field_name="domain_scope",
    )
    d = diag.as_dict()
    assert d["code"] == "SCOPE_EXCEEDED_DOMAIN"
    assert d["severity"] == "ERROR"
    assert d["primitive"] == "CONSTRAINT"
