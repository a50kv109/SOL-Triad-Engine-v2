"""
Integration tests for SolTriadEngine.
Verifies pairwise evaluations (P_SC, P_CD, P_SD), Arbiter verdicts, and audit logging.
"""

import pytest

from sol_triad.models import (
    SourcePrimitive,
    ConstraintPrimitive,
    DissipatePrimitive,
    SystemState,
    EvidenceRecord,
    EpistemicStatus,
    CoherenceVerdict,
)
from sol_triad.evidence import InMemoryEvidenceRegistry
from sol_triad.engine import SolTriadEngine


def test_full_pipeline_pass():
    fixed_clock = 1700000000.0
    registry = InMemoryEvidenceRegistry()
    registry.register(EvidenceRecord(
        evidence_id="ev-telemetry-01",
        domain="flight_control",
        epistemic_status=EpistemicStatus.FACT,
        timestamp_sec=fixed_clock - 10.0,
        payload_hash="hash-xyz"
    ))

    source = SourcePrimitive(
        evidence_id="ev-telemetry-01",
        authority_domain={"flight_control", "navigation"},
        granted_scope={"thruster_a", "rudder_1"},
        granted_loss_domains={"propellant_loss"},
        epistemic_type=EpistemicStatus.FACT,
        timestamp_sec=fixed_clock - 10.0,
        max_age_sec=60.0,
        payload_hash="hash-xyz"
    )

    constraint = ConstraintPrimitive(
        domain_scope={"flight_control"},
        target_objects={"thruster_a"},
        protected_set={"hull_integrity"},
        protected_values={"chamber_id": 1.0},
        min_bounds={"propellant_kg": 50.0},
        max_bounds={"propellant_kg": 500.0},
        units={"propellant_kg": "kg"},
    )

    dissipate = DissipatePrimitive(
        loss_domain={"propellant_loss"},
        target_states={"vector_adjusted"},
        side_effects=set(),
        resource_cost={"propellant_kg": 15.0},
        state_delta={},
        units={"propellant_kg": "kg"},
    )

    initial_state = SystemState(
        current_values={"propellant_kg": 200.0, "chamber_id": 1.0, "hull_integrity": 100.0},
        active_flags={"in_orbit": True},
        units={"propellant_kg": "kg"},
    )

    engine = SolTriadEngine(registry=registry, clock=lambda: fixed_clock)
    report = engine.evaluate(source, constraint, dissipate, initial_state)

    assert report.verdict == CoherenceVerdict.PASS
    assert report.pairwise_checks["P_SC"].is_valid is True
    assert report.pairwise_checks["P_CD"].is_valid is True
    assert report.pairwise_checks["P_SD"].is_valid is True
    assert report.simulated_values["propellant_kg"] == 185.0
    assert len(engine.audit_log) == 1


def test_full_pipeline_review_on_stale_evidence():
    fixed_clock = 1700000000.0
    registry = InMemoryEvidenceRegistry()
    registry.register(EvidenceRecord(
        evidence_id="ev-stale-01",
        domain="flight_control",
        epistemic_status=EpistemicStatus.FACT,
        timestamp_sec=fixed_clock - 500.0,
    ))

    source = SourcePrimitive(
        evidence_id="ev-stale-01",
        authority_domain={"flight_control"},
        granted_scope={"thruster_a"},
        granted_loss_domains={"propellant_loss"},
        epistemic_type=EpistemicStatus.FACT,
        timestamp_sec=fixed_clock - 500.0,
        max_age_sec=60.0,  # 500s > 60s -> stale!
    )

    constraint = ConstraintPrimitive(
        domain_scope={"flight_control"},
        target_objects={"thruster_a"},
        protected_set=set(),
    )

    dissipate = DissipatePrimitive(
        loss_domain={"propellant_loss"},
        target_states=set(),
        side_effects=set(),
    )

    initial_state = SystemState()

    engine = SolTriadEngine(registry=registry, clock=lambda: fixed_clock)
    report = engine.evaluate(source, constraint, dissipate, initial_state)

    assert report.verdict == CoherenceVerdict.REVIEW
    assert report.pairwise_checks["P_SC"].verdict == CoherenceVerdict.REVIEW


def test_full_pipeline_fail_on_unauthorized_scope():
    fixed_clock = 1700000000.0
    registry = InMemoryEvidenceRegistry()
    registry.register(EvidenceRecord(
        evidence_id="ev-01",
        domain="flight_control",
        epistemic_status=EpistemicStatus.FACT,
        timestamp_sec=fixed_clock - 5.0,
    ))

    source = SourcePrimitive(
        evidence_id="ev-01",
        authority_domain={"flight_control"},
        granted_scope={"thruster_a"},  # only thruster_a is granted
        granted_loss_domains={"propellant_loss"},
        epistemic_type=EpistemicStatus.FACT,
        timestamp_sec=fixed_clock - 5.0,
    )

    constraint = ConstraintPrimitive(
        domain_scope={"flight_control"},
        target_objects={"reactor_core"},  # UNAUTHORIZED TARGET!
        protected_set=set(),
    )

    dissipate = DissipatePrimitive(
        loss_domain={"propellant_loss"},
        target_states=set(),
        side_effects=set(),
    )

    initial_state = SystemState()

    engine = SolTriadEngine(registry=registry, clock=lambda: fixed_clock)
    report = engine.evaluate(source, constraint, dissipate, initial_state)

    assert report.verdict == CoherenceVerdict.FAIL
    assert report.pairwise_checks["P_SC"].is_valid is False


@pytest.mark.parametrize("invalid_time", [float("nan"), float("inf"), True])
def test_engine_rejects_invalid_evaluation_time(invalid_time):
    engine = SolTriadEngine(clock=lambda: invalid_time)
    source = SourcePrimitive(
        evidence_id="ev-1",
        authority_domain=set(),
        granted_scope=set(),
        granted_loss_domains=set(),
        epistemic_type=EpistemicStatus.UNKNOWN,
        timestamp_sec=0.0,
    )

    with pytest.raises(ValueError, match="evaluation_time must be a finite number"):
        engine.evaluate(
            source,
            ConstraintPrimitive(domain_scope=set(), target_objects=set(), protected_set=set()),
            DissipatePrimitive(loss_domain=set(), target_states=set(), side_effects=set()),
            SystemState(),
        )
