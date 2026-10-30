# Universal Structural Applicability — SOL-Triad Framework

## 1. Overview & Conceptual Scope

The **SOL Framework** provides a universal structural-causal vocabulary for representing, analyzing, and verifying systems across diverse domains of knowledge. 

Rather than treating verification solely as a low-level programming assert or arbitrary guardrail, SOL models systems through their foundational structural triad:
- **SOURCE ($\mathbf{S}$):** The grounding origin, authorized domains, epistemic credentials, and temporal coordinates.
- **CONSTRAINT ($\mathbf{C}$):** The boundary conditions, invariant requirements, protected parameters, and operational limits.
- **DISSIPATE ($\mathbf{D}$):** The proposed change, entropy dispersal, side effects, applied deltas, and resource expenditures.

The **SOL-Triad Engine** is the deterministic verification kernel that computes the mathematical and epistemic coherence of this triad across pairwise relationships ($P_{SC}$, $P_{CD}$, $P_{SD}$).

---

## 2. Two Levels of Application

SOL explicitly distinguishes between two fundamental tiers of systemic modeling:

### Level I: Physical, Technical, and Computational Systems
In Level I, primitives correspond directly to measurable physical or numerical variables:
- **Physical & Engineering Systems:** Mechanical stresses, thermal balances, fluid dynamics, pressure bounds.
- **Energy & Grid Systems:** Megawatts generated, battery state-of-charge, grid frequency, distribution thermal limits.
- **Software & Agentic Systems:** Memory allocations, file locks, network egress quotas, rate limits, deterministic state machines.
- **Geometric & Mathematical Systems:** Coordinate manifolds, topological boundaries, dimensional correctness.

*Example (Thermal Regulation):*
- **SOURCE:** Authoritative sensor reading (`temp_sensor_01 = 82.4 °C`, verified in registry, timestamp within 5 sec).
- **CONSTRAINT:** Core temperature $\le 85.0\ ^\circ\text{C}$, protected coolant valve state `active == True`.
- **DISSIPATE:** Increase coolant flow rate by $15.0\ \text{L/min}$, consuming $2.5\ \text{kW}$ auxiliary power.

### Level II: Semantic, Philosophical, Ethical, and Social Systems
In Level II, SOL applies its structural apparatus to concepts that are not physical measurements, but nevertheless exhibit definite relationships, preconditions, constraints, and consequences:
- **Responsibility & Accountability:** Who authorizes an intervention and under what delegated authority?
- **Justice & Fairness:** What rights and protections must remain inviolate regardless of efficiency?
- **Trust & Integrity:** What epistemic status grounds a social consensus claim (`FACT`, `INFERENCE`, or uncorroborated assertion)?
- **Harm & Value Preservation:** What irreversible costs, social friction, or value trade-offs are incurred by an action?

*Example (Resource Allocation & Distributive Justice):*
- **SOURCE:** What are the epistemic and legal grounds for the allocation claim? Who authorized the mandate? Are the criteria grounded in verified registries or uncorroborated assumptions?
- **CONSTRAINT:** What human rights, legal minimums, or protected equity invariants must remain strictly unviolated ($C_{\text{protected}}$)?
- **DISSIPATE:** What resources, administrative budgets, or collateral losses are dissipated in implementing the policy?

---

## 3. Preservation of Domain Semantics: Non-Equivalence Axiom

A core architectural principle of SOL is:

> **Structural isomorphism is NOT semantic equivalence.**

1. **Physical Energy is Not Information:**  
   The thermodynamic dissipation of heat in a processor is structurally modeled via $D$, but it is not semantically identical to the erasure of information or the degradation of cryptographic entropy.
2. **Resource Cost is Not Moral Harm:**  
   Expending 100 liters of water is numerically represented in $D_{\text{cost}}$, but moral or ecological harm involves ethical frameworks that cannot be reduced to a scalar float without loss of meaning.
3. **Justice is Not a Trivial Math Invariant:**  
   Modeling an inviolable right via $C_{\text{protected}}$ enforces that a proposed action does not alter that condition, but the computational engine **does not define** what constitutes ultimate justice.

SOL does not attempt to convert philosophy into physics or physics into philosophy. Instead, it provides a **common structural syntax** where domain-specific semantics are preserved within typed domains, explicit units, and authoritative registries.

---

## 4. The Role of Domain Interpretation Modules & External Oracles

The computational kernel (`SolTriadEngine`) is deliberately domain-agnostic. It operates strictly on:
- Set operations (containment, intersection, disjointness).
- Propositional logic and fail-closed security arbiter.
- Dimensional arithmetic and base conversion.
- Authoritative evidence registry lookups.

To apply SOL to specialized fields (such as bioethics, autonomous driving, financial compliance, or aerospace), system architects deploy **Domain Interpretation Modules**:

```
[ Domain Reality: e.g. Bioethics / Medical Policy ]
                       │
                       ▼
         [ Domain Interpretation Adapter ]
  Translates ethical guidelines & clinical protocols
  into formal Source, Constraint, and Dissipate objects
                       │
                       ▼
            [ SOL-Triad Engine Core ]
  Evaluates mathematical, epistemic, and invariant coherence
  Returns deterministic verdict: PASS / REVIEW / FAIL
                       │
                       ▼
       [ Domain Decision & Execution Layer ]
  Interprets report within legal, clinical, and human oversight context
```

---

## 5. Epistemic Limitations of the Engine

To prevent misuse and maintain scientific integrity, the limits of the engine are formally bounded:

1. **Formal Consistency vs. Empirical/Moral Truth:**  
   The engine verifies whether a proposed action is *consistent with its stated evidence, granted authority, and defined constraints*. It does not independently discover natural laws or validate philosophical doctrines.
2. **Garbage In, Fail Closed:**  
   If an external authority registers false evidence, or if an ethical constraint is defined maliciously, the engine will enforce that flawed premise faithfully. For this reason, **authoritative registries must have strict external trust boundaries**.
3. **The Role of REVIEW:**  
   When evidence is stale, uncorroborated, or claims are of `UNKNOWN` epistemic status, the engine emits `REVIEW`. This signals that automated execution must pause and human judgment or fresh grounding is required.
