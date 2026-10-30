# SOL-Triad-Engine v0.4.1
**Reusable Structural Coherence Verification Kernel & Agent Integration Layer**

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)
[![Verification Status](https://img.shields.io/badge/verification-deterministic-purple.svg)]()

---

## 1. Overview & Objective

The **SOL-Triad Engine** is an independent, deterministic structural verification kernel designed to check whether a formalized action or state transition has:
1. **A SOURCE claim grounded in a host-controlled evidence registry**.
2. **Explicit authority, target-scope, and invariant bounds in `CONSTRAINT`**.
3. **Declared resource costs and effects in `DISSIPATE` that stay within those bounds**.
4. **Valid state transitions that preserve protected invariants, bounds, and dimensional units**.

Rather than relying on non-deterministic LLM self-evaluations ("LLM-as-a-judge"), the engine applies set containment, dimensional checks, evidence-record comparisons, and deterministic terminal-state simulation. It verifies formalized inputs; it is **not a universal source of truth** and does not establish scientific, philosophical, ethical, or legal truth.

The host application owns the evidence registry and must construct trusted SOURCE authority values. Payload hashes are compared with registry values; the engine does not calculate hashes or verify digital signatures.

---

## 2. Universal Structural Applicability

SOL provides a universal structural-causal vocabulary for representing, analyzing, and verifying systems across diverse domains of knowledge:

- **Level I: Physical, Technical, and Computational Systems:**  
  Engineering structures, energy grids, computational state machines, and autonomous software agents where parameters represent concrete physical or numerical variables (pressure, temperature, power, memory locks).
- **Level II: Semantic, Philosophical, Ethical, and Social Systems:**  
  Concepts such as responsibility, justice, fairness, and trust that are not physical scalars, but possess clear preconditions, boundaries, and consequences.

### The Non-Equivalence Axiom
> **Structural isomorphism is NOT semantic equivalence.**

SOL does not reduce ethics to physics or physics to ethics. Physical energy dissipation is not identical to information loss; resource costs are not identical to moral harms; and mathematical invariant preservation does not replace moral inquiry. The engine verifies structural and logical consistency of formalized models, but relies on domain interpretation modules and authoritative registries for real-world grounding.

For full architectural details, see [`docs/UNIVERSAL_STRUCTURAL_APPLICABILITY.md`](docs/UNIVERSAL_STRUCTURAL_APPLICABILITY.md).

---

## 3. The Canonical Triad

The verification core is strictly anchored to the canonical triad:
$$\text{Triad} = \langle \text{SOURCE}, \text{CONSTRAINT}, \text{DISSIPATE} \rangle$$

| Primitive | Mathematical Model | Semantic Purpose |
|---|---|---|
| **`SOURCE` (S)** | $\langle \text{id}, \text{auth}, \text{scope}, \text{loss\_auth}, \text{status}, t_0, \Delta t_{\text{max}}, \text{corrob}, \text{hash} \rangle$ | Epistemic grounding, authoritative registry lookup, and granted operational privileges. |
| **`CONSTRAINT` (C)** | $\langle \text{domain}, \text{targets}, \text{protected}, \text{constants}, \text{bounds}, \text{units}, \text{flags} \rangle$ | Operational boundaries, forbidden mutations, physical numerical bounds, and unit types. |
| **`DISSIPATE` (D)** | $\langle \text{loss\_domain}, \text{states}, \text{side\_effects}, \text{cost}, \Delta S, \Delta F, \text{units} \rangle$ | The proposed actuation: state deltas, resource costs, flag transitions, and entropy loss. |

---

## 4. AI Agent Integration Architecture

The Python package is version 0.4.1. Its backward-compatible JSON integration protocol and schemas remain at protocol version 0.4.0. The engine provides a Python SDK and JSON adapter for a host application to submit candidate actions for verification before execution:

```
TASK / OBSERVATION
        │
        ▼
   AI AGENT PLANNER  (Proposes candidate tool call or intervention)
        │
        ▼
 TRUSTED HOST LAYER (Adds registry-backed SOURCE and policy constraints)
        │
        ▼
    SOL ADAPTER      (Validates JSON shape and calls the engine)
        │
        ▼
 SOL-TRIAD-ENGINE    (Evaluates P_SC, P_CD, P_SD deterministically)
        │
   [ PASS / REVIEW / FAIL Report ]
        │
        ▼
EXECUTION CONTROLLER (Enforces verdict: dispatch, hold for review, or block)
```

### Integration Modes & Status

| Mode | Description | Status |
|---|---|---|
| **Python SDK** | Direct in-process import (`SolTriadEngine`, `SourcePrimitive`) | **Implemented** |
| **JSON Interface** | Standardized request/response contract via `SolTriadJsonAdapter` | **Implemented** |
| **REST API** | Lightweight HTTP service daemon | **Designed / Planned** |
| **MCP Server** | Model Context Protocol tool provider | **Designed / Planned** |
| **Action Gate** | Middleware policy enforcement pattern | **Architectural Pattern** |

See [`docs/AGENT_INTEGRATION.md`](docs/AGENT_INTEGRATION.md) for schemas, security boundaries, and controller gate rules.

### Evidence provenance and numeric semantics

For an `INFERENCE`, the host registry stores the premise IDs that produced the inference. The SOURCE premise list must match the root registry record, and the engine recursively validates nested inferences. Missing provenance, stale evidence, unavailable registry lookups, or traversal limits produce `REVIEW`; missing records in an available registry, invalid premise statuses, mismatched SOURCE/registry declarations, and cycles produce `FAIL`. A shared premise in a DAG is not a cycle. The registry and its operator remain trusted inputs; this graph check does not establish semantic truth or authenticate registry writes.

`UnitRegistry.convert()` preserves offsets for absolute values (for example, `0 °C = 273.15 K`); `UnitRegistry.convert_delta()` converts additive differences without offsets. State deltas use difference conversion. A temperature-valued resource cost is subtracted as a difference, while linear resource costs retain their existing conversion. Observed state values, bounds, and protected values remain absolute.

---

## 5. Verification Architecture & Pairwise Checks

Evaluation is structured across three orthogonal verification projections:

```
                  SOURCE (S)
                  /        \
          P_SC   /          \   P_SD
                /            \
               v              v
      CONSTRAINT (C) <------> DISSIPATE (D)
                      P_CD
```

- **$P_{SC}$ (Grounding & Authority):** Checks that the evidence reference exists in the host-controlled registry, matches its epistemic status, timestamp, and optional registered hash, and that $C.\text{domain\_scope} \subseteq S.\text{authority\_domain}$ and $C.\text{target\_objects} \subseteq S.\text{granted\_scope}$. The host must supply trusted SOURCE authority values.
- **$P_{SD}$ (Loss Domain Authority):** Checks that $D.\text{loss\_domain} \subseteq S.\text{granted\_loss\_domains}$.
- **$P_{CD}$ (State Invariant Integrity):** Simulates terminal state $S' = S_0 + \Delta - \text{Cost}$ and checks protected variables, flags, bounds, and dimensional compatibility.

---

## 6. Verdict Semantics

The public API returns a single unified `CoherenceVerdict`:

- **`PASS`**: All required checks passed with grounded evidence and verified invariants.
- **`REVIEW`**: Insufficient evidence, stale observation, uncorroborated inference, or offline registry for ambient claims.  
  *Rule:* **The engine never silently converts `REVIEW` into `PASS`**.
- **`FAIL`**: Structural defect, unauthorized authority/scope, invariant violation, bounds breach, negative resource cost, or dimensional mismatch.

---

## 7. Installation & Quickstart

### Installation from the repository root
```bash
python -m pip install .
```

Editable install with test/schema tooling:
```bash
python -m pip install -e ".[dev]"
```

Run the complete working example:
```bash
python examples/basic_pass.py
```

To install directly from GitHub after the changes are merged:
```bash
python -m pip install "git+https://github.com/a50kv109/SOL-Triad-Engine.git"
```

### Direct Python SDK Usage
```python
report = engine.evaluate(source, constraint, dissipate, initial_state)
print(report.verdict.value)  # PASS / REVIEW / FAIL
```

Construct the primitives and registry in the host application; see the complete runnable [`basic_pass.py`](examples/basic_pass.py) example for current argument names and types. SOURCE authority and evidence registry entries must come from trusted host data.

### JSON Agent Adapter Usage
```python
from sol_triad import InMemoryEvidenceRegistry, SolTriadJsonAdapter

registry = InMemoryEvidenceRegistry()  # Register trusted evidence before evaluation.
adapter = SolTriadJsonAdapter(default_registry=registry)
response = adapter.evaluate_json(request_payload)
print(f"Verdict: {response['verdict']}")
```

The adapter rejects `evidence_records` embedded in a request. Populate a trusted registry before accepting agent proposals; do not let an agent mint SOURCE authority or registry entries.
The evaluation timestamp is host-controlled: deterministic runs may pass `evaluation_time=` to `evaluate_json()`, but a timestamp in the JSON request is rejected.

---

## 8. Running Tests

The test suite covers unit, integration, adversarial attacks, adapter behavior, and both JSON Schemas. The current count is reported by the CI/test command rather than treated as a permanent API guarantee:

```bash
# Run full test suite
pytest -v

# Run adversarial bypass attacks only
pytest tests/adversarial/ -v

# Run agent integration adapter tests only
pytest tests/unit/test_adapter.py -v
```

---

## 9. Directory Structure

```
SOL-Triad-Engine/
├── schemas/
│   ├── sol_triad_request.schema.json   # Machine-readable JSON protocol schema (v0.4.0)
│   └── sol_triad_response.schema.json  # Machine-readable JSON protocol schema (v0.4.0)
├── sol_triad/
│   ├── __init__.py                     # Public API exports
│   ├── adapter.py                      # SolTriadJsonAdapter (Agent Integration Layer)
│   ├── engine.py                       # SolTriadEngine coordinator & Decision Arbiter
│   ├── evidence.py                     # EvidenceRegistryOracle & InMemoryEvidenceRegistry
│   ├── models.py                       # Typed dataclasses & CoherenceVerdict enum
│   ├── units.py                        # UnitRegistry & dimensional conversion algebra
│   └── validators.py                   # EvidenceValidator, ScopeValidator, StateValidator
├── tests/
│   ├── unit/                           # Unit tests for models, units, validators, adapter
│   │   └── test_schemas.py             # JSON Schema request/response contract tests
│   ├── integration/                    # Full pipeline end-to-end tests
│   └── adversarial/                    # Comprehensive attack vectors & bypass tests
├── docs/
│   ├── ARCHITECTURE.md                 # Structural architecture and component flows
│   ├── AGENT_INTEGRATION.md            # Agent integration architecture & security gates
│   ├── UNIVERSAL_STRUCTURAL_APPLICABILITY.md # Level I vs Level II systemic modeling
│   ├── DATA_MODEL.md                   # Data models and attribute schemas
│   ├── VALIDATION_RULES.md             # Formal verification axioms
│   ├── THREAT_MODEL.md                 # Security threat model and mitigations
│   ├── EXPERIMENTS.md                  # Empirical benchmarks & prototype defect audit
│   ├── ROADMAP.md                      # Release roadmap and future milestones
│   ├── SOL_COMPATIBILITY.md            # Reference repository alignment & O7 taxonomy
│   ├── PURPOSE_AND_USE_CASES.md        # Purpose, scope, and use cases
│   └── RELEASE_STATUS.md               # Implemented capabilities and limitations
├── examples/
│   ├── basic_pass.py                   # Complete PASS execution example
│   ├── evidence_review.py              # REVIEW scenario example (stale evidence)
│   ├── invariant_fail.py               # FAIL scenario example (protected mutation)
│   └── agent_integration_demo.py       # Complete agent integration with execution controller
├── README.md
├── pyproject.toml
├── LICENSE
└── demo/                               # Separate React/TypeScript visual prototype; not Python runtime
```
