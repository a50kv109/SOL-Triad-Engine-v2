# Historical Experimental Benchmarks & Empirical Observations — SOL-Triad Engine

## 1. Experimental Methodology
The measurements below are historical v0.3.1 observations; they are not current performance guarantees or a benchmark of the v0.4.1 tree.

1. **Deterministic Execution Latency:** Microbenchmarking time-to-decision for simple and compound triad structures.
2. **Adversarial Catch Rate:** Measuring detection rate against 16 distinct bypass vectors.
3. **Epistemic Arbiter Stability:** Ensuring no silent promotion from `REVIEW` to `PASS`.

---

## 2. Benchmark Results

### 2.1 Latency Overhead (Synthetic Benchmarks)
- **Mean Single-Triad Verification Latency:** $< 0.15\text{ ms}$ on standard Linux x86_64 CPU.
- **Historical 56-Test Suite Total Execution Time:** $0.20\text{ seconds}$ via `pytest 7.2.1`.
- **Memory Footprint:** Zero persistent background memory allocations (pure stateless evaluation with optional audit log).

### 2.2 Adversarial Catch Rate
| Test Category | Attacks Tested | Caught / Blocked | Catch Rate |
|---|---|---|---|
| Domain & Scope Substitution | 3 | 3 | 100% |
| Epistemic & Evidence Forgery | 4 | 4 | 100% |
| Unit & Dimensional Bypasses | 3 | 3 | 100% |
| State & Invariant Violations | 4 | 4 | 100% |
| Multi-Vector Compound Attacks | 2 | 2 | 100% |
| **Total Adversarial Suite** | **16** | **16** | **100%** |

---

## 3. Findings from v0.3 Prototype Audit

During the transition from v0.3 to v0.3.1, the following critical empirical defects were demonstrated and corrected:

1. **The `None == None` Dimensional Bypass:**  
   In v0.3, `UnitRegistry.are_compatible(u1, u2)` checked `DIMENSIONS.get(u1) == DIMENSIONS.get(u2)`. When both `u1` and `u2` were unrecognized strings, both returned `None`, evaluating `None == None -> True`! This allowed arbitrary unphysical mutations. In v0.3.1, this bypass is 100% blocked.
2. **The Inert `protected_values` Defect:**  
   In v0.3, `protected_values` was populated into `required_vars` for missing key checks, but simulated values were never actually compared against the protected value! In v0.3.1, exact invariant equality is strictly enforced.
3. **The Silent String Verdict TypeError:**  
   `EvidenceValidator` returned string literals `"FAIL"` and `"REVIEW"`, while `_finalize()` attempted to read `verdict.value`. This produced runtime `AttributeError` on rejection. In v0.3.1, `CoherenceVerdict` enum is strictly typed throughout.
