import time
from typing import Dict, Any, Optional
from .models import SourcePrimitive, ConstraintPrimitive, DissipatePrimitive, SystemState, CoherenceVerdict
from .validators import EvidenceValidator, ScopeValidator, StateValidator, EvidenceRegistryOracle

class SolTriadEngine:
    """
    SOL-Triad Engine v0.3
    Coordinates Evidence, Scope, and State Validators to adjudicate coherence.
    """
    def __init__(self, registry: Optional[EvidenceRegistryOracle] = None):
        self.registry = registry
        self.audit_log = []

    def evaluate(
        self, 
        s: SourcePrimitive, 
        c: ConstraintPrimitive, 
        d: DissipatePrimitive, 
        initial_state: SystemState
    ) -> Dict[str, Any]:
        
        current_time = time.time()
        
        # Initialize Validators
        evidence_val = EvidenceValidator(self.registry, current_time)
        scope_val = ScopeValidator()
        state_val = StateValidator()

        # 1. Evidence & Applicability Check (P_SC Grounding)
        ev_ok, ev_verdict, ev_msg = evidence_val.validate(s)
        if not ev_ok:
            return self._finalize(ev_verdict, [ev_msg])

        # 2. Scope & Authority Check (P_SC & P_SD Authority)
        sc_ok, sc_msg = scope_val.validate(s, c, d)
        if not sc_ok:
            return self._finalize(CoherenceVerdict.FAIL, [ev_msg, sc_msg])

        # 3. State & Invariant Simulation (P_CD Integrity)
        st_ok, st_msg = state_val.validate(c, d, initial_state)
        if not st_ok:
            return self._finalize(CoherenceVerdict.FAIL, [ev_msg, sc_msg, st_msg])

        # All structural and epistemic checks passed
        return self._finalize(CoherenceVerdict.PASS, [ev_msg, sc_msg, st_msg])

    def _finalize(self, verdict: CoherenceVerdict, messages: list) -> Dict[str, Any]:
        record = {
            "verdict": verdict.value,
            "engine_version": "0.3.0",
            "messages": messages,
            "timestamp": time.time()
        }
        self.audit_log.append(record)
        return record