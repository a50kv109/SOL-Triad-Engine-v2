# Validation Rules & Verification Axioms — SOL-Triad Engine v0.4.1

This document formalizes the validation axioms implemented across the SOL-Triad Engine.

---

## 1. Evidence Grounding Axioms ($P_{SC}$)

1. **Axiom EV-1 (Finite Time Anchors):**
   Both the SOURCE timestamp and the evaluation time must be finite numbers.
   If violated $\rightarrow$ `FAIL (STATE_INVALID_NUMERIC)`.

2. **Axiom EV-2 (No Prophetic Observation):**
   $\text{timestamp\_sec}(S) \le t_{\text{current}}$.
   If violated $\rightarrow$ `FAIL (TEMPORAL_FUTURE)`.

3. **Axiom EV-3 (Freshness Window):**
   $(t_{\text{current}} - \text{timestamp\_sec}(S)) \le \text{max\_age\_sec}(S)$.
   If violated $\rightarrow$ `REVIEW (TEMPORAL_STALE)`.

4. **Axiom EV-4 (Authoritative Grounding):**
   $\exists R \in \text{Registry} : R.\text{evidence\_id} = S.\text{evidence\_id}$.
   If Registry is unavailable and status is `FACT`/`INFERENCE` $\rightarrow$ `REVIEW (REGISTRY_OFFLINE)`.
   If Registry is online and $R$ does not exist $\rightarrow$ `FAIL (EVIDENCE_NOT_FOUND)`.

5. **Axiom EV-5 (Registry-Anchored Timestamp):**
    $R.\text{timestamp\_sec} = S.\text{timestamp\_sec}$ and the registry timestamp must be finite and not in the future.
    If the timestamps differ $\rightarrow$ `FAIL (EVIDENCE_TIMESTAMP_MISMATCH)`.

6. **Axiom EV-6 (Epistemic Status Coherence):**
   $S.\text{epistemic\_type} = R.\text{epistemic\_status}$ for every root SOURCE claim.
   If violated $\rightarrow$ `FAIL (EVIDENCE_MISMATCH)`.

7. **Axiom EV-7 (Domain Grounding):**
   $R.\text{domain} \in S.\text{authority\_domain}$.
   If violated $\rightarrow$ `FAIL (EVIDENCE_DOMAIN_MISMATCH)`.

8. **Axiom EV-8 (Registry-Owned Inference Provenance):**
   An `INFERENCE` record in the registry must contain a non-empty `corroborating_evidence_ids` list. The SOURCE list must exactly match the root registry list; a mismatch $\rightarrow$ `FAIL (EVIDENCE_MISMATCH)`. Missing or empty registered premises $\rightarrow$ `REVIEW (INFERENCE_CHAIN_INCOMPLETE / INFERENCE_UNSUPPORTED)`.

9. **Axiom EV-9 (Fail-Closed Payload Hash Comparison):**
   - If $S.\text{payload\_hash} \ne \text{None} \land R.\text{payload\_hash} = \text{None} \rightarrow \text{FAIL (EVIDENCE_HASH_MISSING_IN_REGISTRY)}$.
   - If $S.\text{payload\_hash} = \text{None} \land R.\text{payload\_hash} \ne \text{None} \rightarrow \text{FAIL (EVIDENCE_HASH_REQUIRED_BY_REGISTRY)}$.
   - If $S.\text{payload\_hash} \ne R.\text{payload\_hash} \rightarrow \text{FAIL (EVIDENCE_PAYLOAD_MISMATCH)}$.
   - Hash evaluation never silently ignores asymmetric presence.

10. **Axiom EV-10 (Recursive Inference Graph Validation):**
   Every registered `INFERENCE` premise is traversed recursively. Each visited record must exist, have a valid ID and status (`FACT` or `INFERENCE`), be in the SOURCE authority domain, have a finite non-future timestamp, and be within the SOURCE freshness window. Missing records in an available registry, invalid statuses, malformed/future timestamps, or cycles $\rightarrow$ `FAIL`; stale evidence or unavailable registry $\rightarrow$ `REVIEW`. An inference without its own registered premises $\rightarrow$ `REVIEW`. Separate `visiting` and `visited` sets detect cycles without rejecting shared DAG nodes. Traversal is bounded to 64 dependency levels and 1,024 unique records; exceeding a limit $\rightarrow$ `REVIEW`.

---

## 2. Scope & Authority Axioms ($P_{SC}$ and $P_{SD}$)

1. **Axiom SC-1 (No Structural Defects):**
   $S.\text{authority\_domain} \ne \text{None} \land S.\text{granted\_scope} \ne \text{None} \land S.\text{granted\_loss\_domains} \ne \text{None}$.
   If violated $\rightarrow$ `FAIL (SCOPE_DEFECT_NONE)`.

2. **Axiom SC-2 (Domain Authority Containment):**
   $C.\text{domain\_scope} \subseteq S.\text{authority\_domain}$.
   If violated $\rightarrow$ `FAIL (SCOPE_EXCEEDED_DOMAIN)`.

3. **Axiom SC-3 (Object Target Containment):**
   $C.\text{target\_objects} \subseteq S.\text{granted\_scope}$.
   If violated $\rightarrow$ `FAIL (SCOPE_EXCEEDED_OBJECTS)`.

4. **Axiom SC-4 (Loss Domain Containment):**
   $D.\text{loss\_domain} \subseteq S.\text{granted\_loss\_domains}$.
   If violated $\rightarrow$ `FAIL (SCOPE_EXCEEDED_LOSS)`.

---

## 3. State & Invariant Axioms ($P_{CD}$)

1. **Axiom ST-1 (Numeric Sanity):**
   All numerical values in $S_0, D_{\text{delta}}, D_{\text{cost}}, C_{\text{min}}, C_{\text{max}}, C_{\text{protected}}$ must be finite ($\neg \text{isnan} \land \neg \text{isinf}$).
   If violated $\rightarrow$ `FAIL (STATE_INVALID_NUMERIC)`.

2. **Axiom ST-2 (Non-Negative Resource Costs):**
   $\forall r \in \text{dom}(D_{\text{cost}}), D_{\text{cost}}[r] \ge 0.0$.
   If violated $\rightarrow$ `FAIL (STATE_NEGATIVE_RESOURCE_COST)`.

3. **Axiom ST-3 (Protected Parameter Inviolability):**
   Let $M = D_{\text{target\_states}} \cup D_{\text{side\_effects}} \cup \text{dom}(D_{\text{delta}}) \cup \text{dom}(D_{\text{cost}}) \cup \text{dom}(D_{\text{flags}})$.
   $M \cap C.\text{protected\_set} = \emptyset$.
   If violated $\rightarrow$ `FAIL (STATE_PROTECTED_PARAM_MUTATED)`.

4. **Axiom ST-4 (Dimensional Typing Compatibility):**
   For all $p \in M$, units must be dimensionally compatible ($\text{dim}(D_{\text{unit}}) = \text{dim}(C_{\text{unit}}) = \text{dim}(S_{0,\text{unit}})$).
   If an unknown unit or dimension mismatch occurs $\rightarrow$ `FAIL (UNIT_INCOMPATIBLE)`.

   Absolute values and additive differences use different conversions: `UnitRegistry.convert()` preserves affine offsets, while `UnitRegistry.convert_delta()` uses scale factors only. `state_delta` uses difference conversion. A temperature-valued `resource_cost` is subtracted as a difference; linear resource costs retain the existing conversion. Constraint bounds, protected values, and observed state values remain absolute.

5. **Axiom ST-5 (Fail-Closed Required Variables):**
   Let $R_{\text{vars}} = \text{dom}(C_{\text{min}}) \cup \text{dom}(C_{\text{max}}) \cup \text{dom}(C_{\text{protected\_values}})$.
   $R_{\text{vars}} \subseteq \text{dom}(S')$.
   If violated $\rightarrow$ `FAIL (STATE_MISSING_VAR)`.

6. **Axiom ST-6 (Invariant Constants):**
   $\forall v \in \text{dom}(C_{\text{protected\_values}}), |S'[v] - C_{\text{protected\_values}}[v]| \le \epsilon$.
   If violated $\rightarrow$ `FAIL (STATE_PROTECTED_VALUE_VIOLATED)`.

7. **Axiom ST-7 (Physical Boundary Bounds):**
   $\forall v \in \text{dom}(C_{\text{min}}), S'[v] \ge C_{\text{min}}[v]$.
   $\forall v \in \text{dom}(C_{\text{max}}), S'[v] \le C_{\text{max}}[v]$.
   If violated $\rightarrow$ `FAIL (STATE_MIN_BOUND_BREACH | STATE_MAX_BOUND_BREACH)`.

8. **Axiom ST-8 (Flag Invariants):**
   - $\forall f \in C_{\text{protected\_flags}}, S'_f = S_{0,f}$.
   - $\forall f, v \in C_{\text{forbidden\_flags}}, S'_f \ne v$.
   - $\forall f, v \in C_{\text{required\_flags}}, S'_f = v$.
   If violated $\rightarrow$ `FAIL`.
