#!/usr/bin/env python3
"""
Example: Basic PASS Scenario.
Demonstrates a fully grounded, authorized, and invariant-preserving state transition.
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

    # 1. Authoritative Evidence Registry
    registry = InMemoryEvidenceRegistry()
    registry.register(EvidenceRecord(
        evidence_id="ev-pwr-42",
        domain="power_distribution",
        epistemic_status=EpistemicStatus.FACT,
        timestamp_sec=current_time - 15.0,
        payload_hash="sha256-verified-power-grant"
    ))

    # 2. SOURCE Primitive: Grounded authorization
    source = SourcePrimitive(
        evidence_id="ev-pwr-42",
        authority_domain={"power_distribution", "auxiliary_subsystems"},
        granted_scope={"transformer_alpha", "relay_beta"},
        granted_loss_domains={"joule_heat"},
        epistemic_type=EpistemicStatus.FACT,
        timestamp_sec=current_time - 15.0,
        max_age_sec=300.0,
        payload_hash="sha256-verified-power-grant"
    )

    # 3. CONSTRAINT Primitive: Boundary conditions & invariants
    constraint = ConstraintPrimitive(
        domain_scope={"power_distribution"},
        target_objects={"transformer_alpha"},
        protected_set={"hardware_safety_interlock"},
        protected_values={"frequency_hz": 60.0},
        min_bounds={"voltage_volts": 210.0, "reserve_capacity_percent": 20.0},
        max_bounds={"voltage_volts": 250.0, "reserve_capacity_percent": 100.0},
        units={"voltage_volts": "ratio", "reserve_capacity_percent": "percent"},
        protected_flags={"grid_sync": True},
    )

    # 4. DISSIPATE Primitive: Proposed actuation / state mutation
    dissipate = DissipatePrimitive(
        loss_domain={"joule_heat"},
        target_states={"feeder_line_balanced"},
        side_effects=set(),
        resource_cost={"reserve_capacity_percent": 10.0},
        state_delta={"voltage_volts": 5.0},
        flag_delta={},
        units={"voltage_volts": "ratio", "reserve_capacity_percent": "percent"},
    )

    # 5. System State: Current observations
    initial_state = SystemState(
        current_values={
            "voltage_volts": 220.0,
            "reserve_capacity_percent": 85.0,
            "frequency_hz": 60.0,
            "hardware_safety_interlock": 1.0,
        },
        active_flags={"grid_sync": True},
        units={"voltage_volts": "ratio", "reserve_capacity_percent": "percent"},
    )

    # 6. Evaluate Coherence
    engine = SolTriadEngine(registry=registry, clock=lambda: current_time)
    report = engine.evaluate(source, constraint, dissipate, initial_state)

    print("=" * 60)
    print(f"VERDICT: {report.verdict.value}")
    print(f"Engine Version: {report.engine_version}")
    print("=" * 60)
    for rel, p in report.pairwise_checks.items():
        print(f"[{rel}] {p.relationship} -> {p.verdict.value}")
    print("\nSimulated Terminal Values:")
    for k, v in report.simulated_values.items():
        print(f"  {k}: {v}")
    print("\nDiagnostics:")
    for d in report.diagnostics:
        print(f"  [{d.code.value}] ({d.severity.value}) {d.message}")


if __name__ == "__main__":
    main()
