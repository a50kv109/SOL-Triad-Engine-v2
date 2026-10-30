# AI Agent Integration Architecture — SOL-Triad Engine v0.4.1

The Python package release is v0.4.1. The JSON request/response protocol remains v0.4.0 for compatibility.

## 1. Overview & Architectural Role

The **SOL-Triad Engine** is an independent, non-executing verification kernel. It is not an LLM agent, not a prompt orchestration framework, and not an autonomous runtime.

Instead, SOL serves as an **External Structural Verification Layer (Action Gate)** for AI agents:
- The AI Agent generates thoughts, plans, and candidate tool calls.
- Before those actions touch actuators, APIs, or databases, the trusted host binds the proposal to a registry-backed SOURCE and its own authority/policy values, then forms the canonical triad ($\mathbf{S}, \mathbf{C}, \mathbf{D}$).
- The **SOL-Triad Engine** evaluates the plan against epistemic ground truth, scope bounds, and state invariants.
- The **External Execution Controller** enforces the resulting verdict: allowing execution (`PASS`), halting for human confirmation or telemetry refresh (`REVIEW`), or completely blocking execution (`FAIL`).

---

## 2. Agent Interaction Lifecycle

```
┌──────────────────────────────────────────────────────────┐
│                   ENVIRONMENT / SENSORS                  │
└────────────────────────────┬─────────────────────────────┘
                             │ Observes state / Receives task
                             ▼
┌──────────────────────────────────────────────────────────┐
│                 AI AGENT (LLM / PLANNER)                 │
│  - Reason over goals and constraints                     │
│  - Synthesize candidate intervention / tool call         │
└────────────────────────────┬─────────────────────────────┘
                             │ Proposed Action Plan
                             ▼
┌──────────────────────────────────────────────────────────┐
│                     SOL ADAPTER                          │
│  - Host binds trusted SOURCE and policy to the proposal: │
│    * SOURCE (evidence, domains, epistemic status)        │
│    * CONSTRAINT (invariants, protected vars, bounds)     │
│    * DISSIPATE (deltas, resource costs, side effects)    │
└────────────────────────────┬─────────────────────────────┘
                             │ Evaluates Triad Coherence
                             ▼
┌──────────────────────────────────────────────────────────┐
│                 SOL-TRIAD-ENGINE v0.4.1                  │
│  - P_SC: Epistemic grounding & scope authority           │
│  - P_CD: State simulation, bounds & protected sets       │
│  - P_SD: Loss domain containment & side-effect bounds    │
│  - Decision Arbiter (Fail-Closed)                        │
└────────────────────────────┬─────────────────────────────┘
                             │ EvaluationReport (PASS / REVIEW / FAIL)
                             ▼
┌──────────────────────────────────────────────────────────┐
│               EXTERNAL EXECUTION CONTROLLER              │
│  - PASS   ──► Executes action on actuators / systems     │
│  - REVIEW ──► Requests human operator or sensor refresh  │
│  - FAIL   ──► Blocks action; sends diagnostics to agent  │
└──────────────────────────────────────────────────────────┘
```

---

## 3. Integration Modes & Implementation Status

| Mode | Description | Status in package v0.4.1 |
| :--- | :--- | :--- |
| **A. Python SDK** | Direct in-process import of `sol_triad` classes (`SolTriadEngine`, `SourcePrimitive`, etc.) | **Implemented** |
| **B. JSON Interface** | Machine-readable JSON request/response contract via `SolTriadJsonAdapter` and JSON Schemas | **Implemented** |
| **C. REST API** | Remote HTTP microservice (`POST /api/v1/evaluate`) for polyglot agent runtimes | **Designed / Planned** |
| **D. MCP Server** | Model Context Protocol server exposing `sol_evaluate_triad` as an agent tool | **Designed / Planned** |
| **E. Agent Action Gate** | Middleware interceptor wrapping LangChain, LlamaIndex, AutoGen, or custom agent loops | **Architectural Pattern** |

> **Important Notice on Status:**
> Modes A (Python SDK) and B (JSON Interface, protocol 0.4.0) are implemented and verified by automated tests. Modes C, D, and E are architectural specifications. An actual MCP server or HTTP daemon has not been packaged into this repository.

---

## 4. The JSON Interface Contract (Mode B)

The JSON interface decouples an agent host's language (Python, TypeScript, Rust, Go) from the verification kernel. The request is not an authentication mechanism: the host must not forward agent-controlled SOURCE authority fields as trusted values.
The evaluation clock is also host-controlled. The request schema does not accept `evaluation_time`; deterministic test or replay time must be supplied through the trusted Python `evaluate_json(..., evaluation_time=...)` argument.

For `INFERENCE` claims, the host-owned registry must store `corroborating_evidence_ids` on each inference record. The root SOURCE list must match that registered list exactly; the engine recursively validates nested inferences and rejects cyclic or invalid chains. Missing registered provenance, stale evidence, and registry outages produce `REVIEW`; a missing record in an available registry, an invalid premise status, or a cycle produces `FAIL`. Keep provenance registration and SOURCE construction inside the trusted host boundary; JSON alone cannot authenticate either.

`EvidenceRecord.corroborating_evidence_ids` was appended after the existing fields, preserving prior positional constructor arguments. Existing inference records without this value remain constructible but are incomplete and yield `REVIEW` until their provenance is registered.

### Request Payload (`schemas/sol_triad_request.schema.json`)

`source.authority_domain`, `source.granted_scope`, `source.granted_loss_domains`, and the evidence reference must be populated by the trusted host. The adapter rejects inline `evidence_records`; evidence must come from the registry supplied to `SolTriadJsonAdapter`.

```json
{
  "request_id": "req-cooling-action-9481",
  "protocol_version": "0.4.0",
  "engine_version": "0.4.1",
  "source": {
    "evidence_id": "sensor_reading_core_temp",
    "authority_domain": ["facility_thermal_management"],
    "granted_scope": ["pump_01", "chiller_loop_a"],
    "granted_loss_domains": ["electrical_grid_power"],
    "epistemic_type": "FACT",
    "timestamp_sec": 1740000000.0,
    "max_age_sec": 30.0,
    "payload_hash": "a1b2c3d4..."
  },
  "constraint": {
    "domain_scope": ["facility_thermal_management"],
    "target_objects": ["pump_01"],
    "protected_set": ["emergency_valve_sealed"],
    "max_bounds": { "pump_rpm": 3600.0 },
    "min_bounds": { "pump_rpm": 0.0 },
    "units": { "pump_rpm": "rpm", "power_draw": "kW" },
    "required_flags": { "cooling_loop_active": true }
  },
  "dissipate": {
    "loss_domain": ["electrical_grid_power"],
    "target_states": ["coolant_circulating"],
    "side_effects": ["auxiliary_noise"],
    "resource_cost": { "power_draw": 4.5 },
    "state_delta": { "pump_rpm": 1200.0 },
    "units": { "pump_rpm": "rpm", "power_draw": "kW" }
  },
  "initial_state": {
    "current_values": { "pump_rpm": 1800.0, "power_draw": 10.0 },
    "active_flags": { "cooling_loop_active": true, "emergency_valve_sealed": true },
    "units": { "pump_rpm": "rpm", "power_draw": "kW" }
  }
}
```

### Response Payload (`schemas/sol_triad_response.schema.json`)
```json
{
  "request_id": "req-cooling-action-9481",
  "protocol_version": "0.4.0",
  "engine_version": "0.4.1",
  "verdict": "PASS",
  "pairwise_checks": {
    "P_SC": { "relationship": "P_SC", "is_valid": true, "verdict": "PASS", "diagnostics": [] },
    "P_CD": { "relationship": "P_CD", "is_valid": true, "verdict": "PASS", "diagnostics": [] },
    "P_SD": { "relationship": "P_SD", "is_valid": true, "verdict": "PASS", "diagnostics": [] }
  },
  "diagnostics": [
    { "code": "EVIDENCE_PASS", "severity": "INFO", "message": "Evidence verified." },
    { "code": "SCOPE_PASS", "severity": "INFO", "message": "Scope authorized." },
    { "code": "STATE_PASS", "severity": "INFO", "message": "State simulation invariant checks passed." }
  ],
  "simulated_values": {
    "pump_rpm": 3000.0,
    "power_draw": 5.5
  },
  "simulated_flags": {
    "cooling_loop_active": true,
    "emergency_valve_sealed": true
  },
  "evaluation_timestamp": 1740000005.0,
  "messages": ["[STATE_PASS] State simulation invariant checks passed."]
}
```

---

## 5. Security & Trust Boundaries

When deploying AI agents with the SOL verification layer, systems must enforce six strict security boundaries:

1. **No Self-Certification of Evidence:**
   The AI agent must **never** be permitted to populate or sign its own entries in the authoritative evidence registry. The JSON adapter rejects request-supplied `evidence_records`; the host must register trusted records separately.
2. **Registry and SOURCE Trust Boundary:**
   The engine trusts the registry oracle and SOURCE values supplied by its caller. The host—not the agent—must construct authority and scope values. The engine does not authenticate the caller or verify registry signatures.
3. **PASS is Necessary, Not Sufficient:**
   A `PASS` verdict means the submitted model passed the checks implemented by the engine. It does not establish that the action is optimal, that the inputs are truthful, or that omitted constraints are safe.
4. **REVIEW is Fail-Closed:**
   Under no circumstances may an adapter or execution controller automatically downgrade a `REVIEW` into a `PASS`. A `REVIEW` requires either fresh sensor telemetry or explicit operator authorization.
5. **Enforcement Separation:**
   The SOL engine **does not execute actions** and holds no direct network or hardware actuators. An external execution controller must inspect the verdict before dispatching tool calls.
6. **Immutable Triad:**
   No integration layer or adapter may add additional canonical primitives or bypass the pairwise evaluation pipeline ($P_{SC}$, $P_{CD}$, $P_{SD}$).
