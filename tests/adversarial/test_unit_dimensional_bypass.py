"""
Adversarial tests: Unit & Dimensionality Bypass Attacks.

Specifically tests against the known defects in prototype v0.3:
  - Both units unknown (previously evaluated as None == None -> True!)
  - One unit missing / omitted (previously bypassed compatibility)
  - Applying delta in wrong physical dimension (e.g. pressure + seconds)
  - Unrecognized pseudo-scientific unit names designed to spoof validators
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


def test_adversarial_unknown_unit_bypass_attempt():
    """Agent attempts to exploit unknown units: both declare 'quantum_flux'."""
    fixed_time = 1000.0
    registry = InMemoryEvidenceRegistry()
    registry.register(EvidenceRecord(
        evidence_id="ev-unit-test",
        domain="experimental",
        epistemic_status=EpistemicStatus.FACT,
        timestamp_sec=fixed_time - 1.0,
    ))

    source = SourcePrimitive(
        evidence_id="ev-unit-test",
        authority_domain={"experimental"},
        granted_scope={"reactor"},
        granted_loss_domains={"flux_loss"},
        epistemic_type=EpistemicStatus.FACT,
        timestamp_sec=fixed_time - 1.0,
    )

    constraint = ConstraintPrimitive(
        domain_scope={"experimental"},
        target_objects={"reactor"},
        protected_set=set(),
        min_bounds={"flux": 10.0},
        units={"flux": "quantum_flux"},  # UNKNOWN UNIT!
    )

    dissipate = DissipatePrimitive(
        loss_domain={"flux_loss"},
        target_states=set(),
        side_effects=set(),
        state_delta={"flux": 5.0},
        units={"flux": "quantum_flux"},  # Same unknown unit! In v0.3 this returned True!
    )

    state = SystemState(
        current_values={"flux": 20.0},
        units={"flux": "quantum_flux"}
    )

    engine = SolTriadEngine(registry=registry, clock=lambda: fixed_time)
    report = engine.evaluate(source, constraint, dissipate, state)

    # In v0.3.1, unknown units in strict validation MUST fail!
    assert report.verdict == CoherenceVerdict.FAIL
    assert any(d.code == DiagnosticCode.UNIT_INCOMPATIBLE for d in report.diagnostics)


def test_adversarial_asymmetric_unit_omission_bypass():
    """Agent specifies 'bar' in Constraint, but omits unit in Dissipate."""
    fixed_time = 1000.0
    registry = InMemoryEvidenceRegistry()
    registry.register(EvidenceRecord(
        evidence_id="ev-unit-omission",
        domain="hydraulics",
        epistemic_status=EpistemicStatus.FACT,
        timestamp_sec=fixed_time - 1.0,
    ))

    source = SourcePrimitive(
        evidence_id="ev-unit-omission",
        authority_domain={"hydraulics"},
        granted_scope={"valve_1"},
        granted_loss_domains={"pressure_relief"},
        epistemic_type=EpistemicStatus.FACT,
        timestamp_sec=fixed_time - 1.0,
    )

    constraint = ConstraintPrimitive(
        domain_scope={"hydraulics"},
        target_objects={"valve_1"},
        protected_set=set(),
        max_bounds={"pipe_pressure": 50.0},
        units={"pipe_pressure": "bar"},
    )

    dissipate = DissipatePrimitive(
        loss_domain={"pressure_relief"},
        target_states=set(),
        side_effects=set(),
        state_delta={"pipe_pressure": 10.0},
        units={},  # Asymmetric omission!
    )

    state = SystemState(
        current_values={"pipe_pressure": 30.0},
        units={"pipe_pressure": "bar"}
    )

    engine = SolTriadEngine(registry=registry, clock=lambda: fixed_time)
    report = engine.evaluate(source, constraint, dissipate, state)

    assert report.verdict == CoherenceVerdict.FAIL
    assert any(d.code == DiagnosticCode.UNIT_INCOMPATIBLE for d in report.diagnostics)


def test_adversarial_incompatible_dimension_bypass():
    """Agent adds time (sec) to pressure (bar)."""
    fixed_time = 1000.0
    registry = InMemoryEvidenceRegistry()
    registry.register(EvidenceRecord(
        evidence_id="ev-dim-test",
        domain="hydraulics",
        epistemic_status=EpistemicStatus.FACT,
        timestamp_sec=fixed_time - 1.0,
    ))

    source = SourcePrimitive(
        evidence_id="ev-dim-test",
        authority_domain={"hydraulics"},
        granted_scope={"valve_1"},
        granted_loss_domains={"pressure_relief"},
        epistemic_type=EpistemicStatus.FACT,
        timestamp_sec=fixed_time - 1.0,
    )

    constraint = ConstraintPrimitive(
        domain_scope={"hydraulics"},
        target_objects={"valve_1"},
        protected_set=set(),
        units={"pipe_pressure": "bar"},
    )

    dissipate = DissipatePrimitive(
        loss_domain={"pressure_relief"},
        target_states=set(),
        side_effects=set(),
        state_delta={"pipe_pressure": 10.0},
        units={"pipe_pressure": "sec"},  # Incompatible dimension (time vs pressure)!
    )

    state = SystemState(
        current_values={"pipe_pressure": 30.0},
        units={"pipe_pressure": "bar"}
    )

    engine = SolTriadEngine(registry=registry, clock=lambda: fixed_time)
    report = engine.evaluate(source, constraint, dissipate, state)

    assert report.verdict == CoherenceVerdict.FAIL
    assert any(d.code == DiagnosticCode.UNIT_INCOMPATIBLE for d in report.diagnostics)
