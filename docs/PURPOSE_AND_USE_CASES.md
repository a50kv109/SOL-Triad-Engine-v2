# Purpose and Universal Use Cases — SOL-Triad Engine v0.4.1

## 1. Core Purpose and Architectural Role

The **SOL-Triad Engine** is an independent, reusable structural verification mechanism intended to serve as an external checking layer for software projects, autonomous systems, and AI-agent hosts.

It is a structural checker, not a universal source of truth. It evaluates formal inputs against the host-provided registry and constraints; it does not independently establish scientific, philosophical, ethical, legal, or empirical truth.

### Primary Function
The engine accepts a formalized description of a proposed action and state and checks its structural coherence using the canonical triad:
- **`SOURCE`** — Foundations, authoritative origins, actors, credentials, and epistemic evidence.
- **`CONSTRAINT`** — Invariants, operational boundaries, permission scopes, and dimensional requirements.
- **`DISSIPATE`** — Resource expenditures, state deltas, side effects, and entropy consequences.

### Verification Verdicts
The engine evaluates the triad across three orthogonal pairwise projections ($P_{SC}$, $P_{CD}$, $P_{SD}$) and produces one of three deterministic outcomes:
- **`PASS`** — All formalized conditions, epistemic groundings, scope boundaries, and state invariants are satisfied.
- **`REVIEW`** — Required evidence is absent, expired, unverified, or ambiguous; execution must halt until an external arbiter (human supervisor or fresh sensor reading) confirms validity. The engine *never* silently promotes `REVIEW` to `PASS`.
- **`FAIL`** — A direct violation of conditions, invariants, authority, or bounds has been detected. The proposed action must be blocked.

---

## 2. Fundamental Properties and Non-Goals

To prevent architectural confusion, the following boundaries define what the engine is and what it is not:

1. **Not an AI Agent:** The engine is a deterministic verification kernel, not an autonomous agent or reasoning planner.
2. **Does Not Replace Agent Reasoning:** It does not synthesize goals, formulate strategies, or construct plans. It evaluates candidate inputs provided to it.
3. **Does Not Execute Actions:** It has no network actuators, shell access, or execution controllers. It returns a verdict; enforcement is strictly the responsibility of the calling host system.
4. **Independent Verification Layer:** It operates as an external gate or middleware that can be attached to any host architecture without tightly coupling to agent internals.
5. **Reusable Structural Procedure:** Its data model can represent inputs from multiple domains, but domain meaning, evidence quality, and policy correctness remain the responsibility of the host and domain-specific systems.
6. **No Claim to Absolute Truth:** The engine does not prove metaphysical, moral, or philosophical truth. It verifies structural and formal consistency *within the formalized model and evidence registry supplied to it*.
7. **Strict Model Boundedness:** It verifies whether the proposed action satisfies the explicit constraints, authorities, and state transformations declared in the request.

---

## 3. Seven Universal Application Domains

The triad can be used as a structural vocabulary in multiple domains. The following examples distinguish potential applicability from capabilities actually checked by package v0.4.1 (JSON protocol v0.4.0):

### 3.1 Engineering and Cyber-Physical Systems
- **What is verified:** Modeled numeric bounds, state invariants, declared resource costs, and dimensional unit consistency.
- **Not established:** Sensor calibration, hardware behavior, or physical safety; the engine does not connect to actuators.
- **Required inputs:** Telemetry readings with timestamps, physical unit annotations (e.g., `volts`, `pascal`), protected hardware registers, and sensor evidence records.
- **Where domain modules are required:** Sensor calibration oracles, physical unit conversion registries (included in `sol_triad.units`), and hardware abstraction layers.
- **Status in v0.4.1:** **Demonstrated and Verified** (`examples/basic_pass.py`, `examples/invariant_fail.py`).

### 3.2 Software and Operating Systems
- **What is verified:** Modeled state deltas, protected values and flags, numeric bounds, and dimensional consistency.
- **Not established:** Memory safety, thread safety, schema security, resource-leak prevention, or operating-system isolation.
- **Required inputs:** Initial state, proposed mutations, protected configuration values, and host-derived authority/scope.
- **Where domain modules are required:** Process environment oracles and database transaction gates.
- **Status in v0.4.1:** **Demonstrated and Verified** (`tests/unit/test_state_validator.py`, `tests/adversarial/test_invariant_state_bypass.py`).

### 3.3 AI Agents and Autonomous Tool Calling
- **What is verified:** Formalized evidence references, authority/scope boundaries, modeled state changes, and resource costs. The host must bind the agent proposal to SOURCE and CONSTRAINT values derived from trusted policy and registry data.
- **Not established:** Prompt-injection detection, caller authentication, or safe execution by itself. A separate host controller must enforce the verdict.
- **Required inputs:** Agent-proposed action data plus a SOURCE assembled by the trusted host. Do not let an agent mint registry records or set its own authority.
- **Where domain modules are required:** Agent-to-Triad prompt adapters and external Execution Controllers.
- **Status in v0.4.1:** **Demonstrated with host integration** (`examples/agent_integration_demo.py`, `schemas/sol_triad_request.schema.json`); the JSON protocol remains v0.4.0, and the demo does not authenticate the host or execute real tools.

### 3.4 Mathematical and Geometric Systems
- **What is verified:** Invariant conservation laws, boundary conditions, topological constraints, and numerical stability (rejection of `NaN`, `±Inf`, and out-of-domain values).
- **Required inputs:** Initial mathematical state, parameter intervals, conservation equations formalized as constraints, proposed step deltas.
- **Where domain modules are required:** Formal algebraic solvers or SMT engines (planned for v0.5.0+).
- **Status in v0.4.1:** **Architectural Capability** (Numerical interval and sanity checks implemented; formal SMT proving planned).

### 3.5 Information and Data Management Systems
- **What is verified:** Registered evidence identifiers, equality of payload-hash strings when present, freshness windows, and state fields formalized as protected.
- **Not established:** Digest computation, cryptographic authenticity, privacy compliance, or data-schema security.
- **Required inputs:** Host-created registry records, timestamps, authorization domains, and modeled state boundaries.
- **Where domain modules are required:** Cryptographic keystores and distributed ledger oracles.
- **Status in v0.4.1:** **Partially implemented** (hash values are compared with the host registry; the engine does not calculate hashes or verify digital signatures).

### 3.6 Organizational, Governance, and Social Systems (Level II)
- **What is verified:** Formal authorization mandates, delegation scope, committee approval consensus thresholds, regulatory compliance boundaries, and budget consumption.
- **Required inputs:** Digital mandate signatures, institutional role registries, policy invariant rules, proposed expenditure limits.
- **Where domain modules are required:** Legal/organizational policy parsers and multi-signature authorization oracles.
- **Status in v0.4.1:** **Architectural Specification** (Formalized in `docs/UNIVERSAL_STRUCTURAL_APPLICABILITY.md`; domain-specific policy bridges planned).

### 3.7 Cognitive and Analytical Systems
- **What is verified:** Epistemic grounding of analytical inferences, premise chain validity, detection of circular reasoning dependencies, freshness of intelligence reports.
- **Required inputs:** Directed acyclic graphs of evidence IDs, epistemic status tags (`FACT`, `INFERENCE`, `UNKNOWN`), corroborating references.
- **Where domain modules are required:** Epistemic graph builders and fact-checking knowledge bases.
- **Status in v0.4.1:** **Demonstrated and Verified** (`tests/adversarial/test_epistemic_evidence_bypass.py`, `tests/unit/test_evidence_graph.py`).

---

## 4. Architectural Summary

| Domain | Core Verification Target | Status in v0.4.1 |
|---|---|---|
| **Engineering Systems** | Telemetry, units, hardware limits | **Verified in Code** |
| **Software Systems** | State transitions, protected constants | **Verified in Code** |
| **AI Agents** | Modeled authority/scope and action-state checks | **Partial (host integration required)** |
| **Math / Geometric** | Numerical invariants, sanity checks | **Partial (Sanity only)** |
| **Information Systems** | Registry references, optional hash equality, freshness | **Partial (host trust required)** |
| **Organizational / Social** | Mandate scope, policy boundaries | **Architectural Specification** |
| **Cognitive / Analytic** | Premise validity, anti-circularity | **Verified in Code** |
