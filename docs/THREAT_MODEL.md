# Threat Model & Attack Surface Analysis — SOL-Triad Engine v0.4.1

## 1. Threat Profile
The SOL-Triad Engine addresses an environment where an AI agent (LLM, autonomous workflow, or autonomous subagent) plans actions and requests state transitions.

The engine does not authenticate request callers. A host must construct trusted SOURCE authority values and provide a host-controlled evidence registry. The JSON adapter rejects agent-supplied evidence records; the engine checks the formal inputs it receives but cannot establish their real-world truth.

---

## 2. Attack Vectors & Mitigations

| Threat Vector | Attack Mechanism | Engine Defense & Axiom | Test Coverage |
|---|---|---|---|
| **Hallucinated Evidence** | Agent manufactures an authoritative justification (`ev-12345`) that does not exist. | Host-controlled registry lookup: `EVIDENCE_NOT_FOUND` $\rightarrow$ `FAIL`; request-supplied records are rejected. | `test_adversarial_hallucinated_evidence_id`, `test_adapter_rejects_inline_evidence_records` |
| **Epistemic Escalation** | Agent labels unverified speculation as `FACT`. | Cross-check against registered status: mismatch $\rightarrow$ `EVIDENCE_MISMATCH` (`FAIL`). | `test_epistemic_status_mismatch_fails` |
| **Unverified Inference Chain** | Agent claims `INFERENCE` based on a registered inference whose own provenance is missing, invalid, stale, or cyclic. | SOURCE premise IDs must match the registry-owned root list; every nested inference is recursively checked. Missing premises / offline registry / stale chain $\rightarrow$ `REVIEW`; missing records in an available registry, invalid premise status, and cycles $\rightarrow$ `FAIL`. Shared DAG evidence is visited once. | `test_nested_inference_chain_passes_when_every_inference_has_registered_premises`, `test_nested_cycle_fails`, `test_shared_fact_dependency_in_dag_is_not_a_cycle` |
| **Time Travel / Replay** | Agent supplies future timestamps, changes a registered timestamp, replays expired observations, or attempts to control evaluation time in JSON. | Registry timestamps must be finite and match SOURCE; future anchors fail, stale evidence yields `REVIEW`, and request-controlled evaluation time is rejected. Deterministic time must be passed by the trusted host. | `test_adversarial_time_travel_future_timestamp`, `test_adversarial_source_timestamp_cannot_refresh_old_registry_evidence`, `test_adapter_rejects_request_controlled_evaluation_time`, `test_stale_evidence_returns_review` |
| **Domain Scope Escalation** | Agent requests actuation in unauthorized domain (e.g. `reactor_control` when granted `telemetry`). | Strict set containment: $C.\text{domain\_scope} \subseteq S.\text{authority\_domain}$. | `test_adversarial_domain_substitution` |
| **Zero-Privilege Confusion** | Agent exploits `None` vs `set()` ambiguity to bypass authority. | `None` is rejected as structural defect; `set()` enforces zero privileges. | `test_empty_set_zero_privileges_rejects_non_empty_request` |
| **Unauthorized Loss Sink** | Agent dumps toxic residue or unauthorized energy into forbidden sink. | Strict loss containment: $D.\text{loss\_domain} \subseteq S.\text{granted\_loss\_domains}$. | `test_adversarial_unauthorized_loss_domain_leakage` |
| **NaN / Inf Bounds Bypass** | Agent injects `float('nan')` to bypass `< min_bound` comparisons (`NaN < X` is False in Python). | Strict `math.isnan` and `math.isinf` sanitization across all inputs. | `test_adversarial_nan_inequality_bypass_attack` |
| **Free Resource Minting** | Agent specifies negative resource cost ($D_{\text{cost}} = -500$) to mint resources. | Non-negative cost enforcement ($D_{\text{cost}} \ge 0.0$). | `test_adversarial_negative_resource_cost_forgery` |
| **Protected Set Smuggling** | Agent smuggles protected variables into `side_effects` or `target_states`. | Unified mutation vector intersection check against $C.\text{protected\_set}$. | `test_adversarial_side_effect_smuggling_into_protected_set` |
| **Protected Value Drift** | Agent mutates a protected constant within the outer min/max envelope. | Terminal simulation compares final value with $C.\text{protected\_values}$. | `test_adversarial_protected_value_mutation_within_bounds` |
| **Dimensional Spoofing** | Agent invents unknown units or exploits missing units to bypass conversion. | Strict `UnitRegistry`: unknown units reject; asymmetric omissions reject. | `test_adversarial_unknown_unit_bypass_attempt` |

---

## 3. Explicit Security Boundaries & Honest Disclosures

1. **Host-Owned Trust Inputs:**
   The JSON adapter rejects request-supplied `evidence_records` and request-controlled evaluation time. The host must provide a trusted registry, construct SOURCE authority/scope values, and provide deterministic time through the method argument if needed. The adapter does not authenticate callers or establish that a host registry is trustworthy; forwarding an agent-authored SOURCE unchanged is unsafe.
2. **Hash Comparison Is Not Signature Verification:**
   The engine compares a supplied payload hash with the registered hash. It does not calculate the digest or verify a digital signature. Authenticity depends on the host-controlled registry.
3. **Registry-Owned Inference Provenance:**
   Every `INFERENCE` in the registry must carry its own premise IDs. The engine requires the root SOURCE list to match the registry record and recursively checks the recorded graph. The registry operator remains trusted to attest that the registered IDs and record contents are accurate; graph validation does not prove semantic truth or authenticate registry writes.
4. **Deterministic Pre-Execution Verification:**
   The engine validates the *declared proposal*. If the underlying execution substrate suffers physical drift or out-of-band hardware failure, runtime monitoring must detect this post-actuation.
5. **No Claim of Immunity to All LLM Attacks:**
   The engine does not guarantee semantic alignment of natural language. It checks declared structural, numeric, and invariant conditions, not the truth or completeness of the propositions.
