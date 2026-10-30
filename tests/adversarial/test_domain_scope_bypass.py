"""
Adversarial tests: Domain & Scope Substitution / Escalation Attacks.

Simulates adversarial attempts by an LLM agent to bypass authority boundaries:
  - Unauthorized domain substitution (e.g. asking for "nuclear" when granted "thermal")
  - Case spoofing and partial prefix matching ("thermal_root" vs "thermal")
  - Empty privilege bypass (exploiting empty set representations)
  - Unauthorized loss domain leakage (dissipating into ungranted environmental sink)
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
)
from sol_triad.evidence import InMemoryEvidenceRegistry
from sol_triad.engine import SolTriadEngine


def test_adversarial_domain_substitution():
    """Agent is authorized for 'civilian_avionics' but requests 'military_payload'."""
    fixed_time = 1000.0
    registry = InMemoryEvidenceRegistry()
    registry.register(EvidenceRecord(
        evidence_id="ev-auth",
        domain="civilian_avionics",
        epistemic_status=EpistemicStatus.FACT,
        timestamp_sec=fixed_time - 1.0,
    ))

    source = SourcePrimitive(
        evidence_id="ev-auth",
        authority_domain={"civilian_avionics"},
        granted_scope={"altimeter", "radio"},
        granted_loss_domains={"battery_draw"},
        epistemic_type=EpistemicStatus.FACT,
        timestamp_sec=fixed_time - 1.0,
    )

    constraint = ConstraintPrimitive(
        domain_scope={"military_payload"},  # Domain substitution attack!
        target_objects={"altimeter"},
        protected_set=set(),
    )

    dissipate = DissipatePrimitive(
        loss_domain={"battery_draw"},
        target_states=set(),
        side_effects=set(),
    )

    engine = SolTriadEngine(registry=registry, clock=lambda: fixed_time)
    report = engine.evaluate(source, constraint, dissipate, SystemState())

    assert report.verdict == CoherenceVerdict.FAIL
    assert any(d.code == DiagnosticCode.SCOPE_EXCEEDED_DOMAIN for d in report.diagnostics)


def test_adversarial_prefix_spoofing():
    """Agent attempts to claim 'telemetry_extended_admin' by matching prefix 'telemetry'."""
    fixed_time = 1000.0
    registry = InMemoryEvidenceRegistry()
    registry.register(EvidenceRecord(
        evidence_id="ev-telemetry",
        domain="telemetry",
        epistemic_status=EpistemicStatus.FACT,
        timestamp_sec=fixed_time - 1.0,
    ))

    source = SourcePrimitive(
        evidence_id="ev-telemetry",
        authority_domain={"telemetry"},
        granted_scope={"sensor_reading"},
        granted_loss_domains={"log_buffer"},
        epistemic_type=EpistemicStatus.FACT,
        timestamp_sec=fixed_time - 1.0,
    )

    constraint = ConstraintPrimitive(
        domain_scope={"telemetry_superadmin"},  # Prefix spoof
        target_objects={"sensor_reading"},
        protected_set=set(),
    )

    dissipate = DissipatePrimitive(
        loss_domain={"log_buffer"},
        target_states=set(),
        side_effects=set(),
    )

    engine = SolTriadEngine(registry=registry, clock=lambda: fixed_time)
    report = engine.evaluate(source, constraint, dissipate, SystemState())

    assert report.verdict == CoherenceVerdict.FAIL
    assert any(d.code == DiagnosticCode.SCOPE_EXCEEDED_DOMAIN for d in report.diagnostics)


def test_adversarial_unauthorized_loss_domain_leakage():
    """Agent attempts to vent toxic exhaust to 'atmospheric_release' instead of 'scrubber'."""
    fixed_time = 1000.0
    registry = InMemoryEvidenceRegistry()
    registry.register(EvidenceRecord(
        evidence_id="ev-vent",
        domain="life_support",
        epistemic_status=EpistemicStatus.FACT,
        timestamp_sec=fixed_time - 1.0,
    ))

    source = SourcePrimitive(
        evidence_id="ev-vent",
        authority_domain={"life_support"},
        granted_scope={"exhaust_valve"},
        granted_loss_domains={"carbon_scrubber"},  # only scrubbers allowed!
        epistemic_type=EpistemicStatus.FACT,
        timestamp_sec=fixed_time - 1.0,
    )

    constraint = ConstraintPrimitive(
        domain_scope={"life_support"},
        target_objects={"exhaust_valve"},
        protected_set=set(),
    )

    dissipate = DissipatePrimitive(
        loss_domain={"atmospheric_release"},  # Unauthorized loss domain!
        target_states=set(),
        side_effects=set(),
    )

    engine = SolTriadEngine(registry=registry, clock=lambda: fixed_time)
    report = engine.evaluate(source, constraint, dissipate, SystemState())

    assert report.verdict == CoherenceVerdict.FAIL
    assert any(d.code == DiagnosticCode.SCOPE_EXCEEDED_LOSS for d in report.diagnostics)
