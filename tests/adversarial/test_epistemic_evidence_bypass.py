"""
Adversarial tests: Epistemic & Evidence Bypass Attacks.

Simulates adversarial attempts:
  - Forged evidence identifiers (hallucinated references)
  - Premise-less INFERENCE assertions (trying to smuggle unverified deductions)
  - Time-travel attacks (future timestamps claiming prophetic validity)
  - Replay of expired/stale ground-truth evidence
  - Tampered payload hashes
"""

from sol_triad.models import (
    SourcePrimitive,
    ConstraintPrimitive,
    DissipatePrimitive,
    SystemState,
    EvidenceRecord,
    EpistemicStatus,
    CoherenceVerdict,
    DiagnosticCode,
)
from sol_triad.evidence import InMemoryEvidenceRegistry
from sol_triad.engine import SolTriadEngine


def test_adversarial_hallucinated_evidence_id():
    """Agent hallucinates a non-existent evidence ID."""
    fixed_time = 1000.0
    registry = InMemoryEvidenceRegistry()

    source = SourcePrimitive(
        evidence_id="ev-hallucinated-fake-source-777",
        authority_domain={"finance"},
        granted_scope={"wire_transfer"},
        granted_loss_domains={"fee"},
        epistemic_type=EpistemicStatus.FACT,
        timestamp_sec=fixed_time - 5.0,
    )

    constraint = ConstraintPrimitive(
        domain_scope={"finance"},
        target_objects={"wire_transfer"},
        protected_set=set(),
    )

    dissipate = DissipatePrimitive(
        loss_domain={"fee"},
        target_states=set(),
        side_effects=set(),
    )

    engine = SolTriadEngine(registry=registry, clock=lambda: fixed_time)
    report = engine.evaluate(source, constraint, dissipate, SystemState())

    assert report.verdict == CoherenceVerdict.FAIL
    assert any(d.code == DiagnosticCode.EVIDENCE_NOT_FOUND for d in report.diagnostics)


def test_adversarial_time_travel_future_timestamp():
    """Agent declares an action justified by future observation."""
    fixed_time = 1000.0
    registry = InMemoryEvidenceRegistry()

    source = SourcePrimitive(
        evidence_id="ev-future",
        authority_domain={"sensors"},
        granted_scope={"radar"},
        granted_loss_domains={"energy"},
        epistemic_type=EpistemicStatus.FACT,
        timestamp_sec=fixed_time + 3600.0,  # 1 hour in the future!
    )

    constraint = ConstraintPrimitive(
        domain_scope={"sensors"},
        target_objects={"radar"},
        protected_set=set(),
    )

    dissipate = DissipatePrimitive(
        loss_domain={"energy"},
        target_states=set(),
        side_effects=set(),
    )

    engine = SolTriadEngine(registry=registry, clock=lambda: fixed_time)
    report = engine.evaluate(source, constraint, dissipate, SystemState())

    assert report.verdict == CoherenceVerdict.FAIL
    assert any(d.code == DiagnosticCode.TEMPORAL_FUTURE for d in report.diagnostics)


def test_adversarial_source_timestamp_cannot_refresh_old_registry_evidence():
    """A fresh source timestamp cannot make an older registry record fresh."""
    fixed_time = 1000.0
    registry = InMemoryEvidenceRegistry()
    registry.register(EvidenceRecord(
        evidence_id="ev-old-record",
        domain="sensors",
        epistemic_status=EpistemicStatus.FACT,
        timestamp_sec=fixed_time - 500.0,
    ))
    source = SourcePrimitive(
        evidence_id="ev-old-record",
        authority_domain={"sensors"},
        granted_scope={"radar"},
        granted_loss_domains={"energy"},
        epistemic_type=EpistemicStatus.FACT,
        timestamp_sec=fixed_time - 1.0,
        max_age_sec=60.0,
    )
    engine = SolTriadEngine(registry=registry, clock=lambda: fixed_time)

    report = engine.evaluate(
        source,
        ConstraintPrimitive(domain_scope={"sensors"}, target_objects={"radar"}, protected_set=set()),
        DissipatePrimitive(loss_domain={"energy"}, target_states=set(), side_effects=set()),
        SystemState(),
    )

    assert report.verdict == CoherenceVerdict.FAIL
    assert any(d.code == DiagnosticCode.EVIDENCE_TIMESTAMP_MISMATCH for d in report.diagnostics)


def test_adversarial_tampered_payload_hash():
    """Agent presents an evidence ID but tampers with the payload hash."""
    fixed_time = 1000.0
    registry = InMemoryEvidenceRegistry()
    registry.register(EvidenceRecord(
        evidence_id="ev-signed-doc",
        domain="legal",
        epistemic_status=EpistemicStatus.FACT,
        timestamp_sec=fixed_time - 10.0,
        payload_hash="sha256-authentic-content-hash"
    ))

    source = SourcePrimitive(
        evidence_id="ev-signed-doc",
        authority_domain={"legal"},
        granted_scope={"contract_exec"},
        granted_loss_domains={"gas_fee"},
        epistemic_type=EpistemicStatus.FACT,
        timestamp_sec=fixed_time - 10.0,
        payload_hash="sha256-tampered-content-hash"  # TAMPERED!
    )

    constraint = ConstraintPrimitive(
        domain_scope={"legal"},
        target_objects={"contract_exec"},
        protected_set=set(),
    )

    dissipate = DissipatePrimitive(
        loss_domain={"gas_fee"},
        target_states=set(),
        side_effects=set(),
    )

    engine = SolTriadEngine(registry=registry, clock=lambda: fixed_time)
    report = engine.evaluate(source, constraint, dissipate, SystemState())

    assert report.verdict == CoherenceVerdict.FAIL
    assert any(d.code == DiagnosticCode.EVIDENCE_PAYLOAD_MISMATCH for d in report.diagnostics)


def test_adversarial_inference_with_unregistered_premise():
    """Agent claims INFERENCE supported by an evidence ID that does not exist."""
    fixed_time = 1000.0
    registry = InMemoryEvidenceRegistry()
    registry.register(EvidenceRecord(
        evidence_id="inf-root",
        domain="analytics",
        epistemic_status=EpistemicStatus.INFERENCE,
        timestamp_sec=fixed_time - 10.0,
        corroborating_evidence_ids={"ghost_premise_999"},
    ))

    source = SourcePrimitive(
        evidence_id="inf-root",
        authority_domain={"analytics"},
        granted_scope={"prediction_model"},
        granted_loss_domains={"compute"},
        epistemic_type=EpistemicStatus.INFERENCE,
        timestamp_sec=fixed_time - 10.0,
        corroborating_evidence_ids={"ghost_premise_999"}  # Does not exist in registry!
    )

    constraint = ConstraintPrimitive(
        domain_scope={"analytics"},
        target_objects={"prediction_model"},
        protected_set=set(),
    )

    dissipate = DissipatePrimitive(
        loss_domain={"compute"},
        target_states=set(),
        side_effects=set(),
    )

    engine = SolTriadEngine(registry=registry, clock=lambda: fixed_time)
    report = engine.evaluate(source, constraint, dissipate, SystemState())

    assert report.verdict == CoherenceVerdict.FAIL
    assert any(d.code == DiagnosticCode.EVIDENCE_NOT_FOUND for d in report.diagnostics)


def test_adversarial_source_hash_supplied_registry_hash_missing():
    """Agent supplies payload_hash, but registry record has no hash to verify against."""
    fixed_time = 1000.0
    registry = InMemoryEvidenceRegistry()
    registry.register(EvidenceRecord(
        evidence_id="ev-unhashed-reg",
        domain="finance",
        epistemic_status=EpistemicStatus.FACT,
        timestamp_sec=fixed_time - 10.0,
        payload_hash=None  # Registry has no hash!
    ))

    source = SourcePrimitive(
        evidence_id="ev-unhashed-reg",
        authority_domain={"finance"},
        granted_scope={"wire"},
        granted_loss_domains={"fee"},
        epistemic_type=EpistemicStatus.FACT,
        timestamp_sec=fixed_time - 10.0,
        payload_hash="sha256:claimed_source_hash_123"  # Source provides hash
    )

    constraint = ConstraintPrimitive(domain_scope={"finance"}, target_objects={"wire"}, protected_set=set())
    dissipate = DissipatePrimitive(loss_domain={"fee"}, target_states=set(), side_effects=set())

    engine = SolTriadEngine(registry=registry, clock=lambda: fixed_time)
    report = engine.evaluate(source, constraint, dissipate, SystemState())

    assert report.verdict == CoherenceVerdict.FAIL
    assert any(d.code == DiagnosticCode.EVIDENCE_HASH_MISSING_IN_REGISTRY for d in report.diagnostics)


def test_adversarial_registry_hash_supplied_source_hash_missing():
    """Registry record demands cryptographic hash verification, but Source omitted it."""
    fixed_time = 1000.0
    registry = InMemoryEvidenceRegistry()
    registry.register(EvidenceRecord(
        evidence_id="ev-secure-audit",
        domain="finance",
        epistemic_status=EpistemicStatus.FACT,
        timestamp_sec=fixed_time - 10.0,
        payload_hash="sha256:required_anchor_hash_456"  # Registry mandates hash
    ))

    source = SourcePrimitive(
        evidence_id="ev-secure-audit",
        authority_domain={"finance"},
        granted_scope={"wire"},
        granted_loss_domains={"fee"},
        epistemic_type=EpistemicStatus.FACT,
        timestamp_sec=fixed_time - 10.0,
        payload_hash=None  # Omitted by source!
    )

    constraint = ConstraintPrimitive(domain_scope={"finance"}, target_objects={"wire"}, protected_set=set())
    dissipate = DissipatePrimitive(loss_domain={"fee"}, target_states=set(), side_effects=set())

    engine = SolTriadEngine(registry=registry, clock=lambda: fixed_time)
    report = engine.evaluate(source, constraint, dissipate, SystemState())

    assert report.verdict == CoherenceVerdict.FAIL
    assert any(d.code == DiagnosticCode.EVIDENCE_HASH_REQUIRED_BY_REGISTRY for d in report.diagnostics)


def test_adversarial_inference_stale_corroborating_evidence():
    """Agent claims INFERENCE supported by stale premise (age > max_age_sec)."""
    fixed_time = 1000.0
    registry = InMemoryEvidenceRegistry()
    registry.register(EvidenceRecord(
        evidence_id="inf-claim",
        domain="telemetry",
        epistemic_status=EpistemicStatus.INFERENCE,
        timestamp_sec=fixed_time - 10.0,
        corroborating_evidence_ids={"premise-stale"},
    ))
    registry.register(EvidenceRecord(
        evidence_id="premise-stale",
        domain="telemetry",
        epistemic_status=EpistemicStatus.FACT,
        timestamp_sec=fixed_time - 800.0,  # 800s old > max_age 120s!
    ))

    source = SourcePrimitive(
        evidence_id="inf-claim",
        authority_domain={"telemetry"},
        granted_scope={"antenna"},
        granted_loss_domains={"power"},
        epistemic_type=EpistemicStatus.INFERENCE,
        timestamp_sec=fixed_time - 10.0,
        max_age_sec=120.0,
        corroborating_evidence_ids={"premise-stale"}
    )

    constraint = ConstraintPrimitive(domain_scope={"telemetry"}, target_objects={"antenna"}, protected_set=set())
    dissipate = DissipatePrimitive(loss_domain={"power"}, target_states=set(), side_effects=set())

    engine = SolTriadEngine(registry=registry, clock=lambda: fixed_time)
    report = engine.evaluate(source, constraint, dissipate, SystemState())

    assert report.verdict == CoherenceVerdict.REVIEW
    assert any(d.code == DiagnosticCode.TEMPORAL_STALE for d in report.diagnostics)


def test_adversarial_inference_future_corroborating_evidence():
    """Agent claims INFERENCE supported by a future-dated premise."""
    fixed_time = 1000.0
    registry = InMemoryEvidenceRegistry()
    registry.register(EvidenceRecord(
        evidence_id="inf-claim-future",
        domain="telemetry",
        epistemic_status=EpistemicStatus.INFERENCE,
        timestamp_sec=fixed_time - 10.0,
        corroborating_evidence_ids={"premise-future"},
    ))
    registry.register(EvidenceRecord(
        evidence_id="premise-future",
        domain="telemetry",
        epistemic_status=EpistemicStatus.FACT,
        timestamp_sec=fixed_time + 500.0,  # in future!
    ))

    source = SourcePrimitive(
        evidence_id="inf-claim-future",
        authority_domain={"telemetry"},
        granted_scope={"antenna"},
        granted_loss_domains={"power"},
        epistemic_type=EpistemicStatus.INFERENCE,
        timestamp_sec=fixed_time - 10.0,
        corroborating_evidence_ids={"premise-future"}
    )

    constraint = ConstraintPrimitive(domain_scope={"telemetry"}, target_objects={"antenna"}, protected_set=set())
    dissipate = DissipatePrimitive(loss_domain={"power"}, target_states=set(), side_effects=set())

    engine = SolTriadEngine(registry=registry, clock=lambda: fixed_time)
    report = engine.evaluate(source, constraint, dissipate, SystemState())

    assert report.verdict == CoherenceVerdict.FAIL
    assert any(d.code == DiagnosticCode.TEMPORAL_FUTURE for d in report.diagnostics)


def test_adversarial_inference_incompatible_premise_epistemic_status():
    """Agent attempts to ground INFERENCE on an UNKNOWN / unverified premise."""
    fixed_time = 1000.0
    registry = InMemoryEvidenceRegistry()
    registry.register(EvidenceRecord(
        evidence_id="inf-claim-unknown-premise",
        domain="telemetry",
        epistemic_status=EpistemicStatus.INFERENCE,
        timestamp_sec=fixed_time - 10.0,
        corroborating_evidence_ids={"premise-unknown"},
    ))
    registry.register(EvidenceRecord(
        evidence_id="premise-unknown",
        domain="telemetry",
        epistemic_status=EpistemicStatus.UNKNOWN,  # UNKNOWN status!
        timestamp_sec=fixed_time - 20.0,
    ))

    source = SourcePrimitive(
        evidence_id="inf-claim-unknown-premise",
        authority_domain={"telemetry"},
        granted_scope={"antenna"},
        granted_loss_domains={"power"},
        epistemic_type=EpistemicStatus.INFERENCE,
        timestamp_sec=fixed_time - 10.0,
        corroborating_evidence_ids={"premise-unknown"}
    )

    constraint = ConstraintPrimitive(domain_scope={"telemetry"}, target_objects={"antenna"}, protected_set=set())
    dissipate = DissipatePrimitive(loss_domain={"power"}, target_states=set(), side_effects=set())

    engine = SolTriadEngine(registry=registry, clock=lambda: fixed_time)
    report = engine.evaluate(source, constraint, dissipate, SystemState())

    assert report.verdict == CoherenceVerdict.FAIL
    assert any(d.code == DiagnosticCode.INFERENCE_PREMISE_INVALID_STATUS for d in report.diagnostics)


def test_adversarial_inference_circular_dependency():
    """Agent lists the inference ID itself inside corroborating_evidence_ids (tautological cycle)."""
    fixed_time = 1000.0
    registry = InMemoryEvidenceRegistry()
    registry.register(EvidenceRecord(
        evidence_id="inf-ouroboros",
        domain="telemetry",
        epistemic_status=EpistemicStatus.INFERENCE,
        timestamp_sec=fixed_time - 10.0,
        corroborating_evidence_ids={"inf-ouroboros"},
    ))

    source = SourcePrimitive(
        evidence_id="inf-ouroboros",
        authority_domain={"telemetry"},
        granted_scope={"antenna"},
        granted_loss_domains={"power"},
        epistemic_type=EpistemicStatus.INFERENCE,
        timestamp_sec=fixed_time - 10.0,
        corroborating_evidence_ids={"inf-ouroboros"}  # Circular!
    )

    constraint = ConstraintPrimitive(domain_scope={"telemetry"}, target_objects={"antenna"}, protected_set=set())
    dissipate = DissipatePrimitive(loss_domain={"power"}, target_states=set(), side_effects=set())

    engine = SolTriadEngine(registry=registry, clock=lambda: fixed_time)
    report = engine.evaluate(source, constraint, dissipate, SystemState())

    assert report.verdict == CoherenceVerdict.FAIL
    assert any(d.code == DiagnosticCode.INFERENCE_CIRCULAR_DEPENDENCY for d in report.diagnostics)
