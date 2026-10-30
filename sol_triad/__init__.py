"""
SOL-Triad Engine v0.4.1
Independent Structural Coherence Verification Kernel & Agent Integration Layer.

Canonical Primitives:
  - SOURCE (S)
  - CONSTRAINT (C)
  - DISSIPATE (D)
"""

from .models import (
    SourcePrimitive,
    ConstraintPrimitive,
    DissipatePrimitive,
    SystemState,
    EvidenceRecord,
    EpistemicStatus,
    CoherenceVerdict,
    CoherenceDiagnostic,
    DiagnosticCode,
    DiagnosticSeverity,
    PairwiseEvaluation,
    EvaluationReport,
)
from .units import (
    UnitRegistry,
    DimensionalityError,
    UnknownUnitError,
)
from .evidence import (
    EvidenceRegistryOracle,
    InMemoryEvidenceRegistry,
)
from .validators import (
    EvidenceValidator,
    ScopeValidator,
    StateValidator,
)
from .engine import SolTriadEngine
from .adapter import SolTriadJsonAdapter

__version__ = "0.4.1"

__all__ = [
    "SourcePrimitive",
    "ConstraintPrimitive",
    "DissipatePrimitive",
    "SystemState",
    "EvidenceRecord",
    "EpistemicStatus",
    "CoherenceVerdict",
    "CoherenceDiagnostic",
    "DiagnosticCode",
    "DiagnosticSeverity",
    "PairwiseEvaluation",
    "EvaluationReport",
    "UnitRegistry",
    "DimensionalityError",
    "UnknownUnitError",
    "EvidenceRegistryOracle",
    "InMemoryEvidenceRegistry",
    "EvidenceValidator",
    "ScopeValidator",
    "StateValidator",
    "SolTriadEngine",
    "SolTriadJsonAdapter",
    "__version__",
]
