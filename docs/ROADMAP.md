# Roadmap — SOL-Triad Engine

## Version 0.4.1 (Current Package Release; JSON Protocol 0.4.0)
- [x] Universal Structural Applicability framework documented (Level I Technical vs Level II Philosophical/Social systems).
- [x] Formal Non-Equivalence Axiom: structural isomorphism is not semantic equivalence.
- [x] Machine-readable JSON Request and Response Schemas (`schemas/sol_triad_request.schema.json`, `schemas/sol_triad_response.schema.json`).
- [x] Decoupled `SolTriadJsonAdapter` for polyglot AI Agent Integration.
- [x] Executable AI Agent integration demonstration with External Execution Controller (`examples/agent_integration_demo.py`).
- [x] Recursive registry-backed validation of `INFERENCE` provenance, with cycle detection, shared-DAG support, and bounded traversal.
- [x] Separate absolute and additive-difference unit conversions for state simulation.
- [x] Unit, integration, adversarial, adapter, and schema test coverage; run the suite on the current checkout for the current result.

---

## Version 0.3.2 (Previous Release)
- [x] Fail-closed comparison of SOURCE and registry payload-hash values when hash checking is required (`EVIDENCE_HASH_MISSING_IN_REGISTRY`, `EVIDENCE_HASH_REQUIRED_BY_REGISTRY`).
- [x] Strict corroborating premise validation for `INFERENCE` claims (existence, status validity, temporal bounds, freshness, and anti-circular dependency rejection).
- [x] Unit, integration, and adversarial regression coverage.
- [x] Clean standalone distribution package without development artifacts or cache bloat.

---

## Version 0.3.1 (Baseline Release)
- [x] Unified `CoherenceVerdict` (`PASS`, `REVIEW`, `FAIL`) with fail-closed arbiter.
- [x] Strict Unit Registry with dimensional checking and base SI conversions.
- [x] Full simulation of terminal state including `state_delta`, `resource_cost`, and `flag_delta`.
- [x] Invariant constant enforcement (`protected_values`) and flag invariants (`protected_flags`, `forbidden_flags`, `required_flags`).
- [x] Non-negative resource cost validation and numeric sanity (`NaN`, `Inf` rejection).
- [x] Deterministic evaluation with injectable clock.

---

## Version 0.5.0 (Planned)
- [ ] **Model Context Protocol (MCP) Server:** Native MCP tool integration allowing Anthropic/Claude and OpenAI compatible agents to call `sol_evaluate_triad`.
- [ ] **REST API Daemon:** Lightweight ASGI / FastAPI service daemon (`POST /api/v1/evaluate`).
- [ ] **Cryptographic Signatures:** Pluggable Ed25519 / ECDSA signature verifier for `EvidenceRecord`.
- [ ] **Multi-Triad Algebraic Composition:** Chaining multiple sequential or parallel triads ($T_1 \otimes T_2$) with transactional rollback.

---

## Longer-Term (Unscheduled)
- [ ] **Formal Verification Integration:** Integration with Z3 or SMT solvers for automated constraint satisfiability proving.
- [ ] **Real-Time Telemetry Bridge:** Live streaming audit logs to OpenTelemetry collectors.

Items in this roadmap are plans only; no REST API or MCP server is currently implemented.
