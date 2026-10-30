"""
Adversarial tests: Multi-Vector Compound Attack Scenarios.

Verifies that the engine detects compound, simultaneous violations across multiple
primitives and validators without dropping diagnostics or masking severe failures.
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


def test_adversarial_simultaneous_multi_vector_violation():
    """
    Compound attack:
      1. Forged evidence ID (fails evidence check)
      2. Scope escalation on domain (fails scope check)
      3. Unauthorized loss domain (fails scope check)
      4. Mutation of protected set (fails state check)
      5. Breaching min bounds (fails state check)
    """
    fixed_time = 1000.0
    registry = InMemoryEvidenceRegistry()  # Empty registry -> evidence not found!

    source = SourcePrimitive(
        evidence_id="ev-ghost-phantom",
        authority_domain={"safe_domain"},
        granted_scope={"safe_sensor"},
        granted_loss_domains={"safe_sink"},
        epistemic_type=EpistemicStatus.FACT,
        timestamp_sec=fixed_time - 1.0,
    )

    constraint = ConstraintPrimitive(
        domain_scope={"unauthorized_domain_1", "unauthorized_domain_2"},
        target_objects={"safe_sensor", "unauthorized_target"},
        protected_set={"critical_core_lock"},
        min_bounds={"coolant_temp": 50.0},
    )

    dissipate = DissipatePrimitive(
        loss_domain={"unauthorized_loss_sink"},
        target_states=set(),
        side_effects={"critical_core_lock"},  # Mutates protected set!
        state_delta={"coolant_temp": -60.0},  # Breaches min bounds!
    )

    state = SystemState(
        current_values={"coolant_temp": 60.0, "critical_core_lock": 1.0}
    )

    engine = SolTriadEngine(registry=registry, clock=lambda: fixed_time)
    report = engine.evaluate(source, constraint, dissipate, state)

    # Must FAIL decisively
    assert report.verdict == CoherenceVerdict.FAIL

    # Must retain multi-vector diagnostics across all violated domains
    diag_codes = {d.code for d in report.diagnostics}
    assert DiagnosticCode.EVIDENCE_NOT_FOUND in diag_codes
    assert DiagnosticCode.SCOPE_EXCEEDED_DOMAIN in diag_codes
    assert DiagnosticCode.SCOPE_EXCEEDED_OBJECTS in diag_codes
    assert DiagnosticCode.SCOPE_EXCEEDED_LOSS in diag_codes
    assert DiagnosticCode.STATE_PROTECTED_PARAM_MUTATED in diag_codes


def test_adversarial_coherence_between_review_and_fail():
    """
    If one check is REVIEW (e.g. stale evidence) and another is FAIL (e.g. scope breach),
    the final arbiter verdict MUST be FAIL (fail-closed semantics).
    """
    fixed_time = 1000.0
    registry = InMemoryEvidenceRegistry()
    registry.register(EvidenceRecord(
        evidence_id="ev-stale-but-real",
        domain="valid_domain",
        epistemic_status=EpistemicStatus.FACT,
        timestamp_sec=fixed_time - 500.0,  # 500s ago
    ))

    source = SourcePrimitive(
        evidence_id="ev-stale-but-real",
        authority_domain={"valid_domain"},
        granted_scope={"valid_object"},
        granted_loss_domains={"valid_loss"},
        epistemic_type=EpistemicStatus.FACT,
        timestamp_sec=fixed_time - 500.0,
        max_age_sec=60.0,  # Stale -> triggers REVIEW in EvidenceValidator
    )

    constraint = ConstraintPrimitive(
        domain_scope={"valid_domain"},
        target_objects={"unauthorized_rogue_object"},  # Scope breach -> triggers FAIL!
        protected_set=set(),
    )

    dissipate = DissipatePrimitive(
        loss_domain={"valid_loss"},
        target_states=set(),
        side_effects=set(),
    )

    engine = SolTriadEngine(registry=registry, clock=lambda: fixed_time)
    report = engine.evaluate(source, constraint, dissipate, SystemState())

    # FAIL must dominate REVIEW!
    assert report.verdict == CoherenceVerdict.FAIL
    assert report.pairwise_checks["P_SC"].verdict == CoherenceVerdict.FAIL
