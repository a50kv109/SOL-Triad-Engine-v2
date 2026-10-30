#!/usr/bin/env python3
"""
Example: REVIEW Scenario.
Demonstrates when evidence is stale or unverified, yielding REVIEW (never converted to PASS).
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

    # Registry has an old record (600s ago)
    registry = InMemoryEvidenceRegistry()
    registry.register(EvidenceRecord(
        evidence_id="ev-temp-reading-old",
        domain="thermal",
        epistemic_status=EpistemicStatus.FACT,
        timestamp_sec=current_time - 600.0,
    ))

    # Source references stale record (max_age_sec is 120s)
    source = SourcePrimitive(
        evidence_id="ev-temp-reading-old",
        authority_domain={"thermal"},
        granted_scope={"cooler_unit_1"},
        granted_loss_domains={"exhaust_air"},
        epistemic_type=EpistemicStatus.FACT,
        timestamp_sec=current_time - 600.0,
        max_age_sec=120.0,
    )

    constraint = ConstraintPrimitive(
        domain_scope={"thermal"},
        target_objects={"cooler_unit_1"},
        protected_set=set(),
        min_bounds={"coolant_temp": 10.0},
        max_bounds={"coolant_temp": 90.0},
    )

    dissipate = DissipatePrimitive(
        loss_domain={"exhaust_air"},
        target_states={"cooling_cycle"},
        side_effects=set(),
        state_delta={"coolant_temp": -5.0},
    )

    initial_state = SystemState(
        current_values={"coolant_temp": 75.0}
    )

    engine = SolTriadEngine(registry=registry, clock=lambda: current_time)
    report = engine.evaluate(source, constraint, dissipate, initial_state)

    print("=" * 60)
    print(f"VERDICT: {report.verdict.value} (Requires Human / Epistemic Arbiter)")
    print("=" * 60)
    for d in report.diagnostics:
        print(f"  [{d.code.value}] ({d.severity.value}) {d.message}")


if __name__ == "__main__":
    main()
