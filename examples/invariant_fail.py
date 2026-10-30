#!/usr/bin/env python3
"""
Example: FAIL Scenario.
Demonstrates immediate failure when an operation violates protected parameter invariants.
"""

from sol_triad import (
    SourcePrimitive,
    ConstraintPrimitive,
    DissipatePrimitive,
    SystemState,
    EvidenceRecord,
    EpistemicStatus,
    InMemoryEvidenceRegistry,
    SolTriadEngine,
)


def main():
    current_time = 1700000000.0

    registry = InMemoryEvidenceRegistry()
    registry.register(EvidenceRecord(
        evidence_id="ev-override",
        domain="core_security",
        epistemic_status=EpistemicStatus.FACT,
        timestamp_sec=current_time - 2.0,
    ))

    source = SourcePrimitive(
        evidence_id="ev-override",
        authority_domain={"core_security"},
        granted_scope={"terminal"},
        granted_loss_domains={"log"},
        epistemic_type=EpistemicStatus.FACT,
        timestamp_sec=current_time - 2.0,
    )

    constraint = ConstraintPrimitive(
        domain_scope={"core_security"},
        target_objects={"terminal"},
        protected_set={"root_encryption_key", "audit_lock"},
        protected_values={"root_encryption_key": 9999.0},
    )

    # Attack: Dissipate attempts to modify protected set parameter 'root_encryption_key'
    dissipate = DissipatePrimitive(
        loss_domain={"log"},
        target_states=set(),
        side_effects={"root_encryption_key"},  # VIOLATION!
        state_delta={"root_encryption_key": 1.0},
    )

    initial_state = SystemState(
        current_values={"root_encryption_key": 9999.0, "audit_lock": 1.0}
    )

    engine = SolTriadEngine(registry=registry, clock=lambda: current_time)
    report = engine.evaluate(source, constraint, dissipate, initial_state)

    print("=" * 60)
    print(f"VERDICT: {report.verdict.value} (Blocked Invariant Violation)")
    print("=" * 60)
    for d in report.diagnostics:
        print(f"  [{d.code.value}] ({d.severity.value}) {d.message}")


if __name__ == "__main__":
    main()
