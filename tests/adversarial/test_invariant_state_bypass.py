"""
Adversarial tests: Invariant & State Mutation Bypass Attacks.

Simulates attacks trying to circumvent state safety:
  - Injecting NaN to defeat inequality bounds (since NaN < X is False in Python!)
  - Forging free resources via negative resource cost
  - Mutating protected_values while keeping them within min_bounds and max_bounds
  - Smuggling mutation of protected_set inside side_effects or target_states
  - Silently disabling safety flags
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


def test_adversarial_nan_inequality_bypass_attack():
    """
    Classic numerical exploit: inject NaN into delta.
    In raw Python: `float('nan') < 5.0` is False, and `float('nan') > 10.0` is False!
    A naive bounds check would pass! SolTriadEngine must explicitly detect and reject NaN.
    """
    fixed_time = 1000.0
    registry = InMemoryEvidenceRegistry()
    registry.register(EvidenceRecord(
        evidence_id="ev-nan",
        domain="core",
        epistemic_status=EpistemicStatus.FACT,
        timestamp_sec=fixed_time - 1.0,
    ))

    source = SourcePrimitive(
        evidence_id="ev-nan",
        authority_domain={"core"},
        granted_scope={"reactor"},
        granted_loss_domains={"heat"},
        epistemic_type=EpistemicStatus.FACT,
        timestamp_sec=fixed_time - 1.0,
    )

    constraint = ConstraintPrimitive(
        domain_scope={"core"},
        target_objects={"reactor"},
        protected_set=set(),
        min_bounds={"radiation_level": 0.0},
        max_bounds={"radiation_level": 100.0},
    )

    dissipate = DissipatePrimitive(
        loss_domain={"heat"},
        target_states=set(),
        side_effects=set(),
        state_delta={"radiation_level": float("nan")},  # Adversarial NaN payload!
    )

    state = SystemState(current_values={"radiation_level": 50.0})

    engine = SolTriadEngine(registry=registry, clock=lambda: fixed_time)
    report = engine.evaluate(source, constraint, dissipate, state)

    assert report.verdict == CoherenceVerdict.FAIL
    assert any(d.code == DiagnosticCode.STATE_INVALID_NUMERIC for d in report.diagnostics)


def test_adversarial_negative_resource_cost_forgery():
    """Agent tries to mint 500 extra tokens by specifying negative resource cost."""
    fixed_time = 1000.0
    registry = InMemoryEvidenceRegistry()
    registry.register(EvidenceRecord(
        evidence_id="ev-cost",
        domain="finance",
        epistemic_status=EpistemicStatus.FACT,
        timestamp_sec=fixed_time - 1.0,
    ))

    source = SourcePrimitive(
        evidence_id="ev-cost",
        authority_domain={"finance"},
        granted_scope={"wallet"},
        granted_loss_domains={"tx_fee"},
        epistemic_type=EpistemicStatus.FACT,
        timestamp_sec=fixed_time - 1.0,
    )

    constraint = ConstraintPrimitive(
        domain_scope={"finance"},
        target_objects={"wallet"},
        protected_set=set(),
    )

    dissipate = DissipatePrimitive(
        loss_domain={"tx_fee"},
        target_states=set(),
        side_effects=set(),
        resource_cost={"credit_balance": -500.0},  # Negative cost exploit!
    )

    state = SystemState(current_values={"credit_balance": 100.0})

    engine = SolTriadEngine(registry=registry, clock=lambda: fixed_time)
    report = engine.evaluate(source, constraint, dissipate, state)

    assert report.verdict == CoherenceVerdict.FAIL
    assert any(d.code == DiagnosticCode.STATE_NEGATIVE_RESOURCE_COST for d in report.diagnostics)


def test_adversarial_protected_value_mutation_within_bounds():
    """
    Agent mutates a protected constant value (e.g., encryption key parameter)
    with a delta that still falls within the broad min/max bounds.
    In v0.3, protected_values was never evaluated against simulated values!
    """
    fixed_time = 1000.0
    registry = InMemoryEvidenceRegistry()
    registry.register(EvidenceRecord(
        evidence_id="ev-prot-val",
        domain="crypto",
        epistemic_status=EpistemicStatus.FACT,
        timestamp_sec=fixed_time - 1.0,
    ))

    source = SourcePrimitive(
        evidence_id="ev-prot-val",
        authority_domain={"crypto"},
        granted_scope={"signer"},
        granted_loss_domains={"entropy"},
        epistemic_type=EpistemicStatus.FACT,
        timestamp_sec=fixed_time - 1.0,
    )

    constraint = ConstraintPrimitive(
        domain_scope={"crypto"},
        target_objects={"signer"},
        protected_set=set(),
        min_bounds={"key_seed": 0.0},
        max_bounds={"key_seed": 10000.0},
        protected_values={"key_seed": 4096.0},  # Invariant constant!
    )

    dissipate = DissipatePrimitive(
        loss_domain={"entropy"},
        target_states=set(),
        side_effects=set(),
        state_delta={"key_seed": 100.0},  # 4096 + 100 = 4196 (within 0..10000 bounds, but changes protected value!)
    )

    state = SystemState(current_values={"key_seed": 4096.0})

    engine = SolTriadEngine(registry=registry, clock=lambda: fixed_time)
    report = engine.evaluate(source, constraint, dissipate, state)

    assert report.verdict == CoherenceVerdict.FAIL
    assert any(d.code == DiagnosticCode.STATE_PROTECTED_VALUE_VIOLATED for d in report.diagnostics)


def test_adversarial_side_effect_smuggling_into_protected_set():
    """Agent claims harmless delta, but slips protected parameter into side_effects."""
    fixed_time = 1000.0
    registry = InMemoryEvidenceRegistry()
    registry.register(EvidenceRecord(
        evidence_id="ev-smuggle",
        domain="ops",
        epistemic_status=EpistemicStatus.FACT,
        timestamp_sec=fixed_time - 1.0,
    ))

    source = SourcePrimitive(
        evidence_id="ev-smuggle",
        authority_domain={"ops"},
        granted_scope={"terminal"},
        granted_loss_domains={"log"},
        epistemic_type=EpistemicStatus.FACT,
        timestamp_sec=fixed_time - 1.0,
    )

    constraint = ConstraintPrimitive(
        domain_scope={"ops"},
        target_objects={"terminal"},
        protected_set={"admin_credentials", "root_key"},
    )

    dissipate = DissipatePrimitive(
        loss_domain={"log"},
        target_states=set(),
        side_effects={"root_key"},  # Smuggled mutation!
    )

    state = SystemState()

    engine = SolTriadEngine(registry=registry, clock=lambda: fixed_time)
    report = engine.evaluate(source, constraint, dissipate, state)

    assert report.verdict == CoherenceVerdict.FAIL
    assert any(d.code == DiagnosticCode.STATE_PROTECTED_PARAM_MUTATED for d in report.diagnostics)
