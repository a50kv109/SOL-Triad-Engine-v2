from dataclasses import dataclass, field
from enum import Enum
from typing import Set, Dict, Optional, Any

class EpistemicStatus(str, Enum):
    FACT = "FACT"
    INFERENCE = "INFERENCE"
    UNKNOWN = "UNKNOWN"

class CoherenceVerdict(str, Enum):
    PASS = "PASS"
    REVIEW = "REVIEW"
    FAIL = "FAIL"

@dataclass
class EvidenceRecord:
    """Represents a verified ground-truth record in the external registry."""
    evidence_id: str
    domain: str
    epistemic_status: EpistemicStatus
    timestamp_sec: float
    payload_hash: str

@dataclass
class SourcePrimitive:
    evidence_id: str
    authority_domain: Optional[Set[str]]
    granted_scope: Optional[Set[str]]  # None = Structural Defect, set() = Zero Privileges
    granted_loss_domains: Optional[Set[str]]
    epistemic_type: EpistemicStatus
    timestamp_sec: float
    max_age_sec: float = 300.0
    corroborating_evidence_ids: Set[str] = field(default_factory=set)

@dataclass
class ConstraintPrimitive:
    domain_scope: Set[str]
    target_objects: Set[str]
    protected_set: Set[str]
    protected_values: Dict[str, float] = field(default_factory=dict)
    max_bounds: Dict[str, float] = field(default_factory=dict)
    min_bounds: Dict[str, float] = field(default_factory=dict)
    units: Dict[str, str] = field(default_factory=dict) # E.g., {"pressure": "bar", "time": "sec"}

@dataclass
class DissipatePrimitive:
    loss_domain: Set[str]
    target_states: Set[str]
    side_effects: Set[str]
    resource_cost: Dict[str, float] = field(default_factory=dict)
    state_delta: Dict[str, float] = field(default_factory=dict)
    flag_delta: Dict[str, bool] = field(default_factory=dict)
    units: Dict[str, str] = field(default_factory=dict)

@dataclass
class SystemState:
    current_values: Dict[str, float] = field(default_factory=dict)
    active_flags: Dict[str, bool] = field(default_factory=dict)
    units: Dict[str, str] = field(default_factory=dict)