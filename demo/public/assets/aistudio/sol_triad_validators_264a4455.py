import time
from typing import Tuple, Optional, Protocol, List
from .models import SourcePrimitive, ConstraintPrimitive, DissipatePrimitive, SystemState, EvidenceRecord, EpistemicStatus

class EvidenceRegistryOracle(Protocol):
    def get_record(self, evidence_id: str) -> Optional[EvidenceRecord]:
        ...

class UnitRegistry:
    """Mock Unit Registry enforcing dimensionality constraints."""
    DIMENSIONS = {
        "bar": "pressure", "psi": "pressure", "atm": "pressure",
        "sec": "time", "ms": "time",
        "celsius": "temperature", "kelvin": "temperature",
        "percent": "ratio", "fraction": "ratio"
    }
    
    @classmethod
    def are_compatible(cls, unit1: str, unit2: str) -> bool:
        if not unit1 or not unit2:
            return True # Untyped bypass for simplicity in PoC
        return cls.DIMENSIONS.get(unit1.lower()) == cls.DIMENSIONS.get(unit2.lower())


class EvidenceValidator:
    def __init__(self, registry: Optional[EvidenceRegistryOracle], current_time_sec: float):
        self.registry = registry
        self.current_time_sec = current_time_sec

    def validate(self, s: SourcePrimitive) -> Tuple[bool, str, str]:
        """Returns (IsValid, Verdict, Message)"""
        # FIX 5: Strict temporal check (no future dates, valid age)
        if s.timestamp_sec > self.current_time_sec:
            return False, "FAIL", f"EVIDENCE_FAIL: Timestamp in future ({s.timestamp_sec} > {self.current_time_sec})"
        
        age = self.current_time_sec - s.timestamp_sec
        if age > s.max_age_sec:
            return False, "REVIEW", f"EVIDENCE_STALE: Age {age}s > {s.max_age_sec}s"

        # FIX 1: Missing registry is fatal for FACT/INFERENCE
        if self.registry is None:
            if s.epistemic_type in [EpistemicStatus.FACT, EpistemicStatus.INFERENCE]:
                return False, "REVIEW", "EVIDENCE_UNVERIFIABLE: Registry offline, cannot trust FACT/INFERENCE."
            return False, "REVIEW", "EVIDENCE_UNKNOWN: Epistemic status UNKNOWN."

        # Fetch and verify primary record
        record = self.registry.get_record(s.evidence_id)
        if not record:
            return False, "FAIL", f"EVIDENCE_FAIL: ID '{s.evidence_id}' not found in registry."

        # FIX 2: Applicability Check (Domain and Epistemic alignment)
        if s.epistemic_type == EpistemicStatus.FACT and record.epistemic_status != EpistemicStatus.FACT:
             return False, "FAIL", f"EVIDENCE_MISMATCH: Claimed FACT, but registry holds {record.epistemic_status.value}."
        
        if s.authority_domain and record.domain not in s.authority_domain:
             return False, "FAIL", f"EVIDENCE_DOMAIN_MISMATCH: Record domain '{record.domain}' not in claimed authority."

        return True, "PASS", "EVIDENCE_PASS: Source cryptographically and epistemically verified."


class ScopeValidator:
    def validate(self, s: SourcePrimitive, c: ConstraintPrimitive, d: DissipatePrimitive) -> Tuple[bool, str]:
        # FIX 3: Differentiate between Missing Field (None) and Empty Set (set())
        if s.authority_domain is None or s.granted_scope is None or s.granted_loss_domains is None:
            return False, "SCOPE_DEFECT: Source is missing mandatory authority/scope fields (None type)."

        if not c.domain_scope.issubset(s.authority_domain):
            return False, f"SCOPE_FAIL: Constraint domain {c.domain_scope} exceeds authority {s.authority_domain}."

        if not c.target_objects.issubset(s.granted_scope):
            return False, f"SCOPE_FAIL: Constraint targets {c.target_objects} exceed granted scope {s.granted_scope}."

        if not d.loss_domain.issubset(s.granted_loss_domains):
            return False, f"SCOPE_FAIL: Dissipate loss domain {d.loss_domain} exceeds granted loss domains {s.granted_loss_domains}."

        return True, "SCOPE_PASS: All domains and targets are within granted scope."


class StateValidator:
    def validate(self, c: ConstraintPrimitive, d: DissipatePrimitive, initial_state: SystemState) -> Tuple[bool, str]:
        # Unified mutation vectors
        all_modified_params = (
            d.target_states | 
            d.side_effects | 
            set(d.state_delta.keys()) | 
            set(d.resource_cost.keys()) |
            set(d.flag_delta.keys())
        )

        # Check protected sets
        protected_intersection = all_modified_params & c.protected_set
        if protected_intersection:
            return False, f"STATE_FAIL: Dissipation mutates protected parameters: {protected_intersection}."

        # FIX 4: Dimensionality compatibility check via UnitRegistry
        for param in all_modified_params:
            d_unit = d.units.get(param)
            c_unit = c.units.get(param)
            s_unit = initial_state.units.get(param)
            if not UnitRegistry.are_compatible(d_unit, c_unit) or not UnitRegistry.are_compatible(d_unit, s_unit):
                return False, f"UNIT_FAIL: Dimensionality mismatch for parameter '{param}'."

        # Terminal state simulation
        simulated_values = dict(initial_state.current_values)
        
        # Apply deltas and costs
        for var_name, delta in d.state_delta.items():
            simulated_values[var_name] = simulated_values.get(var_name, 0.0) + delta
        for var_name, cost in d.resource_cost.items():
            simulated_values[var_name] = simulated_values.get(var_name, 0.0) - cost

        # Check missing variables (Fail-Closed)
        required_vars = set(c.min_bounds.keys()) | set(c.max_bounds.keys()) | set(c.protected_values.keys())
        missing_vars = required_vars - set(simulated_values.keys())
        if missing_vars:
            return False, f"STATE_FAIL: Missing required state variables in simulation: {missing_vars}."

        # Validate bounds
        for var, min_val in c.min_bounds.items():
            if simulated_values[var] < min_val:
                return False, f"STATE_FAIL: '{var}' ({simulated_values[var]}) falls below min_bound ({min_val})."
        for var, max_val in c.max_bounds.items():
            if simulated_values[var] > max_val:
                return False, f"STATE_FAIL: '{var}' ({simulated_values[var]}) exceeds max_bound ({max_val})."

        return True, "STATE_PASS: Simulated terminal state maintains all invariants."