"""
SOL-Triad Engine v0.4.1
Triad Coherence Engine and Decision Arbiter.

Coordinates the canonical triad:
  - SOURCE (S)
  - CONSTRAINT (C)
  - DISSIPATE (D)
Across three pairwise verification relationships:
  - P_SC (SOURCE <-> CONSTRAINT)
  - P_CD (CONSTRAINT <-> DISSIPATE)
  - P_SD (SOURCE <-> DISSIPATE)
"""

import time
import math
from typing import Optional, Callable, Dict, Any, List

from .models import (
    SourcePrimitive,
    ConstraintPrimitive,
    DissipatePrimitive,
    SystemState,
    CoherenceVerdict,
    CoherenceDiagnostic,
    PairwiseEvaluation,
    EvaluationReport,
)
from .validators import EvidenceValidator, ScopeValidator, StateValidator
from .evidence import EvidenceRegistryOracle


class SolTriadEngine:
    """
    SOL-Triad Engine v0.4.1
    Independent structural coherence verification kernel.
    """
    VERSION = "0.4.1"

    def __init__(
        self,
        registry: Optional[EvidenceRegistryOracle] = None,
        clock: Optional[Callable[[], float]] = None,
    ):
        self.registry = registry
        self.clock: Callable[[], float] = clock if clock is not None else time.time
        self.audit_log: List[Dict[str, Any]] = []

    def evaluate(
        self,
        s: SourcePrimitive,
        c: ConstraintPrimitive,
        d: DissipatePrimitive,
        initial_state: SystemState,
        evaluation_time: Optional[float] = None,
    ) -> EvaluationReport:
        """
        Evaluates structural and epistemic coherence of the S-C-D triad.
        Deterministic: uses supplied evaluation_time or injected clock.
        """
        current_time = evaluation_time if evaluation_time is not None else self.clock()
        if isinstance(current_time, bool) or not isinstance(current_time, (int, float)):
            raise ValueError("evaluation_time must be a finite number.")
        try:
            current_time = float(current_time)
        except OverflowError:
            raise ValueError("evaluation_time must be a finite number.") from None
        if not math.isfinite(current_time):
            raise ValueError("evaluation_time must be a finite number.")

        evidence_val = EvidenceValidator(self.registry, current_time)
        scope_val = ScopeValidator()
        state_val = StateValidator()

        all_diagnostics: List[CoherenceDiagnostic] = []

        # 1. Evidence Grounding (Part of P_SC)
        ev_ok, ev_verdict, ev_diags = evidence_val.validate(s)
        all_diagnostics.extend(ev_diags)

        # 2. Scope & Authority (Covers P_SC and P_SD)
        sc_ok, sc_verdict, sc_diags = scope_val.validate(s, c, d)
        all_diagnostics.extend(sc_diags)

        # 3. State Invariants & Terminal Simulation (Covers P_CD)
        st_ok, st_verdict, st_diags, sim_values, sim_flags = state_val.validate(c, d, initial_state)
        all_diagnostics.extend(st_diags)

        # Construct Pairwise Evaluations:
        # P_SC: Grounding + Domain Scope + Target Objects
        p_sc_diags = [
            diag for diag in (ev_diags + sc_diags)
            if diag.primitive in ("SOURCE", "CONSTRAINT") and diag.field_name in (
                "evidence_id", "epistemic_type", "authority_domain", "granted_scope",
                "domain_scope", "target_objects", "timestamp_sec", "max_age_sec", "corroborating_evidence_ids"
            )
        ]
        # P_SC is valid if evidence is not FAIL and domain/target scope are not exceeded
        p_sc_fail = (
            ev_verdict == CoherenceVerdict.FAIL or
            any("SCOPE_EXCEEDED_DOMAIN" in diag.code.value or "SCOPE_EXCEEDED_OBJECTS" in diag.code.value or "SCOPE_DEFECT" in diag.code.value for diag in sc_diags)
        )
        p_sc_review = (ev_verdict == CoherenceVerdict.REVIEW)
        p_sc_verdict = CoherenceVerdict.FAIL if p_sc_fail else (CoherenceVerdict.REVIEW if p_sc_review else CoherenceVerdict.PASS)

        p_sc = PairwiseEvaluation(
            relationship="P_SC: SOURCE <-> CONSTRAINT (Grounding & Authority)",
            is_valid=(p_sc_verdict == CoherenceVerdict.PASS),
            verdict=p_sc_verdict,
            diagnostics=p_sc_diags,
        )

        # P_SD: Loss Domain Authority
        p_sd_diags = [
            diag for diag in sc_diags
            if "LOSS" in diag.code.value or diag.field_name == "granted_loss_domains"
        ]
        p_sd_fail = any("SCOPE_EXCEEDED_LOSS" in diag.code.value or "SCOPE_DEFECT" in diag.code.value for diag in sc_diags)
        p_sd_verdict = CoherenceVerdict.FAIL if p_sd_fail else CoherenceVerdict.PASS

        p_sd = PairwiseEvaluation(
            relationship="P_SD: SOURCE <-> DISSIPATE (Loss Domain Authority)",
            is_valid=(p_sd_verdict == CoherenceVerdict.PASS),
            verdict=p_sd_verdict,
            diagnostics=p_sd_diags,
        )

        # P_CD: State Mutation & Invariant Integrity
        p_cd_verdict = st_verdict
        p_cd = PairwiseEvaluation(
            relationship="P_CD: CONSTRAINT <-> DISSIPATE (State Invariant Integrity)",
            is_valid=(p_cd_verdict == CoherenceVerdict.PASS),
            verdict=p_cd_verdict,
            diagnostics=st_diags,
        )

        pairwise = {
            "P_SC": p_sc,
            "P_CD": p_cd,
            "P_SD": p_sd,
        }

        # 4. Final Verdict Arbitration
        # Rule 1: Any FAIL -> FAIL
        # Rule 2: If no FAIL and any REVIEW -> REVIEW (Never silently convert to PASS!)
        # Rule 3: All PASS -> PASS
        verdicts = [ev_verdict, sc_verdict, st_verdict]
        if CoherenceVerdict.FAIL in verdicts:
            final_verdict = CoherenceVerdict.FAIL
        elif CoherenceVerdict.REVIEW in verdicts:
            final_verdict = CoherenceVerdict.REVIEW
        else:
            final_verdict = CoherenceVerdict.PASS

        report = EvaluationReport(
            verdict=final_verdict,
            engine_version=self.VERSION,
            pairwise_checks=pairwise,
            diagnostics=all_diagnostics,
            simulated_values=sim_values,
            simulated_flags=sim_flags,
            timestamp_sec=current_time,
        )

        self.audit_log.append(report.as_dict())
        return report

    def evaluate_dict(
        self,
        s: SourcePrimitive,
        c: ConstraintPrimitive,
        d: DissipatePrimitive,
        initial_state: SystemState,
        evaluation_time: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Convenience method returning serialized dictionary report."""
        report = self.evaluate(s, c, d, initial_state, evaluation_time)
        return report.as_dict()
