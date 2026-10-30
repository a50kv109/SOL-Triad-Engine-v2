"""
SOL-Triad Engine v0.4.1
Canonical Models and Epistemic Data Contracts.

Primitives:
  - SOURCE: Epistemic origin, authority domains, granted scope, and temporal grounding.
  - CONSTRAINT: Boundary invariants, protected sets, numerical/flag bounds, and target objects.
  - DISSIPATE: Entropy dissipation, side effects, state deltas, resource costs, and loss domains.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Set, Dict, Optional, Any, List


class EpistemicStatus(str, Enum):
    """Declared epistemic status of a source claim."""
    FACT = "FACT"
    INFERENCE = "INFERENCE"
    UNKNOWN = "UNKNOWN"


class CoherenceVerdict(str, Enum):
    """
    Unified public verdict semantics for the SOL-Triad Engine.
      - PASS: Grounded evidence and all state/scope/invariant checks passed.
      - REVIEW: Epistemic uncertainty, stale evidence, or registry offline for UNKNOWN claims.
      - FAIL: Structural defect, unauthorized scope/domain, or invariant violation.
    """
    PASS = "PASS"
    REVIEW = "REVIEW"
    FAIL = "FAIL"


class DiagnosticSeverity(str, Enum):
    """Severity tier for individual coherence diagnostic findings."""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class DiagnosticCode(str, Enum):
    """Machine-readable diagnostic identifiers for audit and programmatic handling."""
    # Temporal & Evidence
    TEMPORAL_FUTURE = "TEMPORAL_FUTURE"
    TEMPORAL_STALE = "TEMPORAL_STALE"
    TEMPORAL_INVALID_LIMIT = "TEMPORAL_INVALID_LIMIT"
    REGISTRY_OFFLINE = "REGISTRY_OFFLINE"
    EVIDENCE_NOT_FOUND = "EVIDENCE_NOT_FOUND"
    EVIDENCE_MISMATCH = "EVIDENCE_MISMATCH"
    EVIDENCE_TIMESTAMP_MISMATCH = "EVIDENCE_TIMESTAMP_MISMATCH"
    UNTRUSTED_EVIDENCE_SOURCE = "UNTRUSTED_EVIDENCE_SOURCE"
    EVIDENCE_DOMAIN_MISMATCH = "EVIDENCE_DOMAIN_MISMATCH"
    EVIDENCE_PAYLOAD_MISMATCH = "EVIDENCE_PAYLOAD_MISMATCH"
    EVIDENCE_HASH_MISSING_IN_REGISTRY = "EVIDENCE_HASH_MISSING_IN_REGISTRY"
    EVIDENCE_HASH_REQUIRED_BY_REGISTRY = "EVIDENCE_HASH_REQUIRED_BY_REGISTRY"
    INFERENCE_UNSUPPORTED = "INFERENCE_UNSUPPORTED"
    INFERENCE_CHAIN_INCOMPLETE = "INFERENCE_CHAIN_INCOMPLETE"
    INFERENCE_TRAVERSAL_LIMIT_EXCEEDED = "INFERENCE_TRAVERSAL_LIMIT_EXCEEDED"
    INFERENCE_PREMISE_INVALID_STATUS = "INFERENCE_PREMISE_INVALID_STATUS"
    INFERENCE_CIRCULAR_DEPENDENCY = "INFERENCE_CIRCULAR_DEPENDENCY"
    EVIDENCE_PASS = "EVIDENCE_PASS"

    # Scope & Authority
    SCOPE_DEFECT_NONE = "SCOPE_DEFECT_NONE"
    SCOPE_EXCEEDED_DOMAIN = "SCOPE_EXCEEDED_DOMAIN"
    SCOPE_EXCEEDED_OBJECTS = "SCOPE_EXCEEDED_OBJECTS"
    SCOPE_EXCEEDED_LOSS = "SCOPE_EXCEEDED_LOSS"
    SCOPE_PASS = "SCOPE_PASS"

    # State & Invariants
    STATE_PROTECTED_PARAM_MUTATED = "STATE_PROTECTED_PARAM_MUTATED"
    STATE_PROTECTED_VALUE_VIOLATED = "STATE_PROTECTED_VALUE_VIOLATED"
    STATE_PROTECTED_FLAG_MUTATED = "STATE_PROTECTED_FLAG_MUTATED"
    STATE_FORBIDDEN_FLAG_ACTIVE = "STATE_FORBIDDEN_FLAG_ACTIVE"
    STATE_REQUIRED_FLAG_MISSING = "STATE_REQUIRED_FLAG_MISSING"
    STATE_MIN_BOUND_BREACH = "STATE_MIN_BOUND_BREACH"
    STATE_MAX_BOUND_BREACH = "STATE_MAX_BOUND_BREACH"
    STATE_MISSING_VAR = "STATE_MISSING_VAR"
    STATE_NEGATIVE_RESOURCE_COST = "STATE_NEGATIVE_RESOURCE_COST"
    STATE_INVALID_NUMERIC = "STATE_INVALID_NUMERIC"
    STATE_PASS = "STATE_PASS"

    # Dimensionality & Units
    UNIT_UNKNOWN = "UNIT_UNKNOWN"
    UNIT_MISSING = "UNIT_MISSING"
    UNIT_INCOMPATIBLE = "UNIT_INCOMPATIBLE"
    UNIT_CONVERSION_FAILED = "UNIT_CONVERSION_FAILED"
    UNIT_PASS = "UNIT_PASS"

    # General Structural
    STRUCTURAL_DEFECT = "STRUCTURAL_DEFECT"


@dataclass(frozen=True)
class CoherenceDiagnostic:
    """Detailed diagnostic item produced by validators."""
    code: DiagnosticCode
    severity: DiagnosticSeverity
    message: str
    primitive: Optional[str] = None
    field_name: Optional[str] = None

    def as_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code.value,
            "severity": self.severity.value,
            "message": self.message,
            "primitive": self.primitive,
            "field_name": self.field_name,
        }


@dataclass
class EvidenceRecord:
    """Verified ground-truth record held in an external authoritative registry."""
    evidence_id: str
    domain: str
    epistemic_status: EpistemicStatus
    timestamp_sec: float
    payload_hash: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    corroborating_evidence_ids: Optional[Set[str]] = None


@dataclass
class SourcePrimitive:
    """
    SOURCE (S) Primitive.
    Represents epistemic origin, authority domain, granted scope, and temporal grounding.
    """
    evidence_id: str
    authority_domain: Optional[Set[str]]       # None = Structural Defect; set() = Zero privileges
    granted_scope: Optional[Set[str]]          # None = Structural Defect; set() = Zero privileges
    granted_loss_domains: Optional[Set[str]]   # None = Structural Defect; set() = Zero privileges
    epistemic_type: EpistemicStatus
    timestamp_sec: float
    max_age_sec: float = 300.0
    corroborating_evidence_ids: Set[str] = field(default_factory=set)
    payload_hash: Optional[str] = None


@dataclass
class ConstraintPrimitive:
    """
    CONSTRAINT (C) Primitive.
    Represents boundary conditions, protected sets, bounds, and dimensional requirements.
    """
    domain_scope: Set[str]
    target_objects: Set[str]
    protected_set: Set[str]
    protected_values: Dict[str, float] = field(default_factory=dict)
    max_bounds: Dict[str, float] = field(default_factory=dict)
    min_bounds: Dict[str, float] = field(default_factory=dict)
    units: Dict[str, str] = field(default_factory=dict)  # e.g., {"pressure": "bar", "duration": "sec"}
    protected_flags: Set[str] = field(default_factory=set)
    forbidden_flags: Dict[str, bool] = field(default_factory=dict)  # Flag name -> forbidden boolean value
    required_flags: Dict[str, bool] = field(default_factory=dict)   # Flag name -> required boolean value


@dataclass
class DissipatePrimitive:
    """
    DISSIPATE (D) Primitive.
    Represents intended action, entropy dissipation, state mutations, and resource costs.
    """
    loss_domain: Set[str]
    target_states: Set[str]
    side_effects: Set[str]
    resource_cost: Dict[str, float] = field(default_factory=dict)
    state_delta: Dict[str, float] = field(default_factory=dict)
    flag_delta: Dict[str, bool] = field(default_factory=dict)
    units: Dict[str, str] = field(default_factory=dict)


@dataclass
class SystemState:
    """
    SystemState.
    Represents current observed state before applying dissipation.
    """
    current_values: Dict[str, float] = field(default_factory=dict)
    active_flags: Dict[str, bool] = field(default_factory=dict)
    units: Dict[str, str] = field(default_factory=dict)


@dataclass
class PairwiseEvaluation:
    """Result for one pairwise relationship (P_SC, P_CD, P_SD)."""
    relationship: str
    is_valid: bool
    verdict: CoherenceVerdict
    diagnostics: List[CoherenceDiagnostic] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "relationship": self.relationship,
            "is_valid": self.is_valid,
            "verdict": self.verdict.value,
            "diagnostics": [d.as_dict() for d in self.diagnostics],
        }


@dataclass
class EvaluationReport:
    """Complete, immutable evaluation report produced by the SOL-Triad Engine."""
    verdict: CoherenceVerdict
    engine_version: str
    pairwise_checks: Dict[str, PairwiseEvaluation]
    diagnostics: List[CoherenceDiagnostic]
    simulated_values: Dict[str, float]
    simulated_flags: Dict[str, bool]
    timestamp_sec: float

    def as_dict(self) -> Dict[str, Any]:
        return {
            "verdict": self.verdict.value,
            "engine_version": self.engine_version,
            "timestamp_sec": self.timestamp_sec,
            "pairwise_checks": {
                k: v.as_dict() for k, v in self.pairwise_checks.items()
            },
            "diagnostics": [d.as_dict() for d in self.diagnostics],
            "simulated_values": self.simulated_values,
            "simulated_flags": self.simulated_flags,
            "messages": [f"[{d.code.value}] {d.message}" for d in self.diagnostics],
        }
