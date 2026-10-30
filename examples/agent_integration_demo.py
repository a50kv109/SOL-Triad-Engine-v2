#!/usr/bin/env python3
"""
SOL-Triad Engine v0.4.1 — Agent Integration Demonstration.

Demonstrates an end-to-end integration lifecycle between:
  1. An AI Agent synthesizing candidate system actions.
  2. A trusted host binding registry-backed SOURCE and policy CONSTRAINT values to the proposal.
  3. The SolTriadJsonAdapter bridging the host-bound JSON into canonical S-C-D primitives.
  4. The SolTriadEngine computing deterministic verification verdicts.
  5. An External Execution Controller enforcing the verdict (PASS / REVIEW / FAIL).

The request fixtures below represent complete host-bound requests, not raw agent
payloads. The adapter does not authenticate its caller or make agent-supplied
SOURCE authority trustworthy; the host must construct those fields itself.
The demo's registry and host policy are illustrative.
"""

import json
import sys
import os

# Ensure package root is in sys.path for direct invocation
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sol_triad import SolTriadJsonAdapter, InMemoryEvidenceRegistry, EvidenceRecord, EpistemicStatus


class MockExecutionController:
    """Simulates the external policy gate enforcing the SOL verdict."""
    def dispatch(self, response: dict) -> str:
        verdict = response.get("verdict")
        req_id = response.get("request_id")
        
        if verdict == "PASS":
            return f"[CONTROLLER: EXECUTED] Request '{req_id}' approved. Dispatching commands to actuators."
        elif verdict == "REVIEW":
            return f"[CONTROLLER: HELD] Request '{req_id}' requires verification. Escalating to human supervisor or requesting telemetry refresh."
        elif verdict == "FAIL":
            diags = [d["message"] for d in response.get("diagnostics", [])]
            return f"[CONTROLLER: BLOCKED] Request '{req_id}' strictly rejected! Violations: {'; '.join(diags)}. Notifying agent to replan."
        else:
            return f"[CONTROLLER: BLOCKED] Unknown verdict '{verdict}'. Failing closed."


def run_scenario(name: str, adapter: SolTriadJsonAdapter, controller: MockExecutionController, request_payload: dict, evaluation_time: float):
    print("=" * 78)
    print(f"SCENARIO: {name}")
    print("=" * 78)
    print("1. Host-bound verification request (agent proposal combined with trusted context):")
    print(f"   Request ID: {request_payload['request_id']}")
    print(f"   Target: {request_payload['constraint']['target_objects']}")
    print(f"   Proposed Delta: {request_payload['dissipate']['state_delta']}")
    
    # Send through adapter
    response = adapter.evaluate_json(request_payload, evaluation_time=evaluation_time)
    
    print("\n2. SOL-Triad Engine Response:")
    print(f"   Verdict: {response['verdict']}")
    print(f"   Protocol Version: {response['protocol_version']}")
    print(f"   Diagnostics Count: {len(response['diagnostics'])}")
    for d in response['diagnostics']:
        print(f"     [{d['severity']}] {d['code']}: {d['message']}")
    
    # Execution controller enforces verdict
    controller_decision = controller.dispatch(response)
    print("\n3. External Execution Controller Action:")
    print(f"   {controller_decision}\n")


def main():
    fixed_time = 1740000000.0
    
    # 0. Setup Authoritative Registry (Sensors and Certificates)
    registry = InMemoryEvidenceRegistry()
    registry.register(EvidenceRecord(
        evidence_id="sensor_telemetry_fresh",
        domain="thermal_control",
        epistemic_status=EpistemicStatus.FACT,
        timestamp_sec=fixed_time - 10.0,
        payload_hash="hash-fresh-telemetry-ok"
    ))
    registry.register(EvidenceRecord(
        evidence_id="sensor_telemetry_stale",
        domain="thermal_control",
        epistemic_status=EpistemicStatus.FACT,
        timestamp_sec=fixed_time - 800.0,  # 800s old, exceeds max_age_sec 300.0
        payload_hash="hash-stale-telemetry"
    ))
    
    adapter = SolTriadJsonAdapter(default_registry=registry)
    controller = MockExecutionController()
    
    # -------------------------------------------------------------
    # Scenario 1: PASS — Valid agent plan within limits and fresh telemetry
    # -------------------------------------------------------------
    pass_request = {
        "request_id": "agent-plan-001-pass",
        "protocol_version": "0.4.0",
        "source": {
            "evidence_id": "sensor_telemetry_fresh",
            "authority_domain": ["thermal_control"],
            "granted_scope": ["pump_alpha"],
            "granted_loss_domains": ["electrical_heat"],
            "epistemic_type": "FACT",
            "timestamp_sec": fixed_time - 10.0,
            "max_age_sec": 300.0,
            "payload_hash": "hash-fresh-telemetry-ok"
        },
        "constraint": {
            "domain_scope": ["thermal_control"],
            "target_objects": ["pump_alpha"],
            "protected_set": ["emergency_drain_valve"],
            "max_bounds": {"coolant_pressure": 10.0},
            "min_bounds": {"coolant_pressure": 0.5},
            "units": {"coolant_pressure": "bar"}
        },
        "dissipate": {
            "loss_domain": ["electrical_heat"],
            "target_states": ["coolant_flowing"],
            "side_effects": ["pipe_vibration"],
            "resource_cost": {},
            "state_delta": {"coolant_pressure": 1.5},
            "units": {"coolant_pressure": "bar"}
        },
        "initial_state": {
            "current_values": {"coolant_pressure": 3.0},
            "active_flags": {},
            "units": {"coolant_pressure": "bar"}
        }
    }
    run_scenario("Sound Agent Plan (PASS)", adapter, controller, pass_request, fixed_time)
    
    # -------------------------------------------------------------
    # Scenario 2: REVIEW — Stale telemetry requires human review or telemetry refresh
    # -------------------------------------------------------------
    review_request = {
        "request_id": "agent-plan-002-review",
        "protocol_version": "0.4.0",
        "source": {
            "evidence_id": "sensor_telemetry_stale",
            "authority_domain": ["thermal_control"],
            "granted_scope": ["pump_alpha"],
            "granted_loss_domains": ["electrical_heat"],
            "epistemic_type": "FACT",
            "timestamp_sec": fixed_time - 800.0,
            "max_age_sec": 300.0,
            "payload_hash": "hash-stale-telemetry"
        },
        "constraint": {
            "domain_scope": ["thermal_control"],
            "target_objects": ["pump_alpha"],
            "protected_set": ["emergency_drain_valve"],
            "max_bounds": {"coolant_pressure": 10.0},
            "min_bounds": {"coolant_pressure": 0.5},
            "units": {"coolant_pressure": "bar"}
        },
        "dissipate": {
            "loss_domain": ["electrical_heat"],
            "target_states": ["coolant_flowing"],
            "side_effects": ["pipe_vibration"],
            "resource_cost": {},
            "state_delta": {"coolant_pressure": 0.8},
            "units": {"coolant_pressure": "bar"}
        },
        "initial_state": {
            "current_values": {"coolant_pressure": 3.0},
            "active_flags": {},
            "units": {"coolant_pressure": "bar"}
        }
    }
    run_scenario("Stale Telemetry Plan (REVIEW)", adapter, controller, review_request, fixed_time)
    
    # -------------------------------------------------------------
    # Scenario 3: FAIL — Agent tries to mutate an invariant protected parameter
    # -------------------------------------------------------------
    fail_request = {
        "request_id": "agent-plan-003-fail",
        "protocol_version": "0.4.0",
        "source": {
            "evidence_id": "sensor_telemetry_fresh",
            "authority_domain": ["thermal_control"],
            "granted_scope": ["pump_alpha"],
            "granted_loss_domains": ["electrical_heat"],
            "epistemic_type": "FACT",
            "timestamp_sec": fixed_time - 10.0,
            "max_age_sec": 300.0,
            "payload_hash": "hash-fresh-telemetry-ok"
        },
        "constraint": {
            "domain_scope": ["thermal_control"],
            "target_objects": ["pump_alpha"],
            "protected_set": ["emergency_drain_valve"],  # Inviolable safety valve
            "max_bounds": {"coolant_pressure": 10.0},
            "min_bounds": {"coolant_pressure": 0.5},
            "units": {"coolant_pressure": "bar"}
        },
        "dissipate": {
            "loss_domain": ["electrical_heat"],
            "target_states": ["coolant_flowing"],
            "side_effects": ["emergency_drain_valve"],  # Mutates protected parameter!
            "resource_cost": {},
            "state_delta": {"coolant_pressure": 1.2},
            "units": {"coolant_pressure": "bar"}
        },
        "initial_state": {
            "current_values": {"coolant_pressure": 3.0},
            "active_flags": {},
            "units": {"coolant_pressure": "bar"}
        }
    }
    run_scenario("Protected Invariant Breach (FAIL)", adapter, controller, fail_request, fixed_time)


if __name__ == "__main__":
    main()
