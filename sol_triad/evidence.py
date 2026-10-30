"""
SOL-Triad Engine v0.4.1
Evidence Registry Interfaces and In-Memory Implementation.
"""

from typing import Optional, Protocol, Dict, runtime_checkable
from .models import EvidenceRecord, EpistemicStatus


@runtime_checkable
class EvidenceRegistryOracle(Protocol):
    """Host-owned evidence lookup; INFERENCE records must include their own premise IDs."""
    def get_record(self, evidence_id: str) -> Optional[EvidenceRecord]:
        ...

    def is_available(self) -> bool:
        ...


class InMemoryEvidenceRegistry:
    """
    In-memory reference implementation of EvidenceRegistryOracle.
    Allows simulating online/offline registries, expired records, and tampering.
    """
    def __init__(self, available: bool = True):
        self._records: Dict[str, EvidenceRecord] = {}
        self._available = available

    def is_available(self) -> bool:
        return self._available

    def set_available(self, available: bool) -> None:
        self._available = available

    def register(self, record: EvidenceRecord) -> None:
        self._records[record.evidence_id] = record

    def get_record(self, evidence_id: str) -> Optional[EvidenceRecord]:
        if not self._available:
            return None
        return self._records.get(evidence_id)

    def remove(self, evidence_id: str) -> Optional[EvidenceRecord]:
        return self._records.pop(evidence_id, None)

    def clear(self) -> None:
        self._records.clear()

    def count(self) -> int:
        return len(self._records)
