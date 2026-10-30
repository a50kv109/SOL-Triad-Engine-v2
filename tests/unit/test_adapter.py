"""
Unit Tests for SolTriadJsonAdapter package v0.4.1 and JSON protocol v0.4.0.
"""

import json
import pytest

from sol_triad import (
    SolTriadJsonAdapter,
    InMemoryEvidenceRegistry,
    EvidenceRecord,
    EpistemicStatus,
    CoherenceVerdict,
    DiagnosticCode,
    DiagnosticSeverity,
)


@pytest.fixture
def current_time():
    return 1740000000.0


@pytest.fixture
def sample_registry(current_time):
    reg = InMemoryEvidenceRegistry()
    reg.register(EvidenceRecord(
        evidence_id="ev-sensor-100",
        domain="thermal_control",
        epistemic_status=EpistemicStatus.FACT,
        timestamp_sec=current_time - 10.0,
        payload_hash="sha256-hash-ok"
    ))
    return reg


@pytest.fixture
def base_valid_request(current_time):
    return {
        "request_id": "test-req-001",
        "protocol_version": "0.4.0",
        "engine_version": "0.4.1",
        "source": {
            "evidence_id": "ev-sensor-100",
            "authority_domain": ["thermal_control"],
            "granted_scope": ["pump_alpha"],
            "granted_loss_domains": ["thermal_entropy"],
            "epistemic_type": "FACT",
            "timestamp_sec": current_time - 10.0,
            "max_age_sec": 300.0,
            "payload_hash": "sha256-hash-ok"
        },
        "constraint": {
            "domain_scope": ["thermal_control"],
            "target_objects": ["pump_alpha"],
            "protected_set": ["emergency_valve"],
            "max_bounds": {"coolant_pressure": 10.0},
            "min_bounds": {"coolant_pressure": 0.5},
            "units": {"coolant_pressure": "bar"}
        },
        "dissipate": {
            "loss_domain": ["thermal_entropy"],
            "target_states": ["coolant_flowing"],
            "side_effects": ["pipe_vibration"],
            "resource_cost": {},
            "state_delta": {"coolant_pressure": 1.5},
            "units": {"coolant_pressure": "bar"}
        },
        "initial_state": {
            "current_values": {"coolant_pressure": 3.0},
            "active_flags": {},
            "units": {"coolant_pressure": "bar"}
        }
    }


def test_adapter_valid_request_pass(sample_registry, base_valid_request, current_time):
    """Test 1: Valid JSON request serializes and evaluates to PASS."""
    adapter = SolTriadJsonAdapter(default_registry=sample_registry)
    response = adapter.evaluate_json(base_valid_request, evaluation_time=current_time)

    assert response["request_id"] == "test-req-001"
    assert response["protocol_version"] == "0.4.0"
    assert response["engine_version"] == "0.4.1"
    assert response["verdict"] == CoherenceVerdict.PASS.value
    assert response["simulated_values"]["coolant_pressure"] == 4.5
    assert len(response["diagnostics"]) > 0
    assert any(d["code"] == DiagnosticCode.STATE_PASS.value for d in response["diagnostics"])


def test_adapter_recursively_validates_registry_owned_inference_chain(
    sample_registry, base_valid_request, current_time
):
    root_id = "ev-inference-root"
    middle_id = "ev-inference-middle"
    fact_id = "ev-inference-fact"
    sample_registry.register(EvidenceRecord(
        evidence_id=root_id,
        domain="thermal_control",
        epistemic_status=EpistemicStatus.INFERENCE,
        timestamp_sec=current_time - 10.0,
        payload_hash="sha256-hash-ok",
        corroborating_evidence_ids={middle_id},
    ))
    sample_registry.register(EvidenceRecord(
        evidence_id=middle_id,
        domain="thermal_control",
        epistemic_status=EpistemicStatus.INFERENCE,
        timestamp_sec=current_time - 20.0,
        corroborating_evidence_ids={fact_id},
    ))
    sample_registry.register(EvidenceRecord(
        evidence_id=fact_id,
        domain="thermal_control",
        epistemic_status=EpistemicStatus.FACT,
        timestamp_sec=current_time - 30.0,
    ))

    request = json.loads(json.dumps(base_valid_request))
    request["source"]["evidence_id"] = root_id
    request["source"]["epistemic_type"] = EpistemicStatus.INFERENCE.value
    request["source"]["corroborating_evidence_ids"] = [middle_id]

    response = SolTriadJsonAdapter(default_registry=sample_registry).evaluate_json(
        request, evaluation_time=current_time
    )

    assert response["verdict"] == CoherenceVerdict.PASS.value


def test_adapter_missing_required_fields(sample_registry, base_valid_request, current_time):
    """Test 2: Missing required top-level fields triggers fail-closed response."""
    adapter = SolTriadJsonAdapter(default_registry=sample_registry)

    # Missing request_id
    bad_req_1 = dict(base_valid_request)
    del bad_req_1["request_id"]
    res1 = adapter.evaluate_json(bad_req_1, evaluation_time=current_time)
    assert res1["verdict"] == CoherenceVerdict.FAIL.value
    assert res1["request_id"] == "missing_request_id"

    # Missing source primitive
    bad_req_2 = dict(base_valid_request)
    del bad_req_2["source"]
    res2 = adapter.evaluate_json(bad_req_2, evaluation_time=current_time)
    assert res2["verdict"] == CoherenceVerdict.FAIL.value
    assert any("source" in d["message"] for d in res2["diagnostics"])


def test_adapter_null_vs_empty_collections(sample_registry, base_valid_request, current_time):
    """Test 3: Null field denotes structural defect (FAIL); empty set denotes zero privileges."""
    adapter = SolTriadJsonAdapter(default_registry=sample_registry)

    # Null authority_domain -> SCOPE_DEFECT_NONE (FAIL)
    req_null = json.loads(json.dumps(base_valid_request))
    req_null["source"]["authority_domain"] = None
    res_null = adapter.evaluate_json(req_null, evaluation_time=current_time)
    assert res_null["verdict"] == CoherenceVerdict.FAIL.value
    assert any(d["code"] == DiagnosticCode.SCOPE_DEFECT_NONE.value for d in res_null["diagnostics"])

    # Empty list authority_domain -> Zero privileges, request for 'thermal_control' fails SCOPE_EXCEEDED_DOMAIN
    req_empty = json.loads(json.dumps(base_valid_request))
    req_empty["source"]["authority_domain"] = []
    res_empty = adapter.evaluate_json(req_empty, evaluation_time=current_time)
    assert res_empty["verdict"] == CoherenceVerdict.FAIL.value
    assert any(d["code"] == DiagnosticCode.SCOPE_EXCEEDED_DOMAIN.value for d in res_empty["diagnostics"])


def test_adapter_invalid_primitive_structures(sample_registry, base_valid_request, current_time):
    """Test 4: Malformed epistemic status or invalid numeric values fail gracefully."""
    adapter = SolTriadJsonAdapter(default_registry=sample_registry)

    req_bad_epistemic = json.loads(json.dumps(base_valid_request))
    req_bad_epistemic["source"]["epistemic_type"] = "INVALID_STATUS"
    res = adapter.evaluate_json(req_bad_epistemic, evaluation_time=current_time)
    assert res["verdict"] == CoherenceVerdict.FAIL.value
    assert any("epistemic_type" in d["message"] for d in res["diagnostics"])


def test_adapter_unsupported_protocol_version(sample_registry, base_valid_request, current_time):
    """Test 5: Protocol version mismatch fails closed."""
    adapter = SolTriadJsonAdapter(default_registry=sample_registry)

    req_proto = dict(base_valid_request)
    req_proto["protocol_version"] = "99.0.0"
    res = adapter.evaluate_json(req_proto, evaluation_time=current_time)
    assert res["verdict"] == CoherenceVerdict.FAIL.value
    assert any("Unsupported protocol_version" in d["message"] for d in res["diagnostics"])


def test_adapter_serialization_of_review(sample_registry, base_valid_request, current_time):
    """Test 6 & 7: Serialization of REVIEW verdict (e.g. stale evidence)."""
    adapter = SolTriadJsonAdapter(default_registry=sample_registry)

    # Make evidence stale (timestamp 1000s ago with max_age 300s)
    req_stale = json.loads(json.dumps(base_valid_request))
    req_stale["source"]["timestamp_sec"] = current_time - 1000.0
    # Also update registry record timestamp
    sample_registry.register(EvidenceRecord(
        evidence_id="ev-sensor-100",
        domain="thermal_control",
        epistemic_status=EpistemicStatus.FACT,
        timestamp_sec=current_time - 1000.0,
        payload_hash="sha256-hash-ok"
    ))

    res = adapter.evaluate_json(req_stale, evaluation_time=current_time)
    assert res["verdict"] == CoherenceVerdict.REVIEW.value
    assert any(d["code"] == DiagnosticCode.TEMPORAL_STALE.value for d in res["diagnostics"])
    assert any(d["severity"] == DiagnosticSeverity.WARNING.value for d in res["diagnostics"])


def test_adapter_serialization_of_fail(sample_registry, base_valid_request, current_time):
    """Test 8: Serialization of FAIL verdict (protected parameter mutation)."""
    adapter = SolTriadJsonAdapter(default_registry=sample_registry)

    req_fail = json.loads(json.dumps(base_valid_request))
    req_fail["dissipate"]["side_effects"] = ["emergency_valve"]  # In protected_set
    res = adapter.evaluate_json(req_fail, evaluation_time=current_time)

    assert res["verdict"] == CoherenceVerdict.FAIL.value
    assert any(d["code"] == DiagnosticCode.STATE_PROTECTED_PARAM_MUTATED.value for d in res["diagnostics"])
    assert res["pairwise_checks"]["P_CD"]["is_valid"] is False


def test_adapter_diagnostic_preservation(sample_registry, base_valid_request, current_time):
    """Test 9: Verifies diagnostics preserve code, severity, message, primitive, and field_name."""
    adapter = SolTriadJsonAdapter(default_registry=sample_registry)

    req_fail = json.loads(json.dumps(base_valid_request))
    req_fail["constraint"]["min_bounds"]["coolant_pressure"] = 5.0  # Final simulated will be 4.5 < 5.0 (breach)

    res = adapter.evaluate_json(req_fail, evaluation_time=current_time)
    assert res["verdict"] == CoherenceVerdict.FAIL.value
    breach_diags = [d for d in res["diagnostics"] if d["code"] == DiagnosticCode.STATE_MIN_BOUND_BREACH.value]
    assert len(breach_diags) == 1
    d = breach_diags[0]
    assert d["severity"] == "ERROR"
    assert "coolant_pressure" in d["message"]
    assert d["primitive"] == "CONSTRAINT"
    assert d["field_name"] == "coolant_pressure"


def test_adapter_rejects_inline_evidence_records(sample_registry, base_valid_request, current_time):
    """Evidence records supplied by an agent are never treated as authoritative."""
    adapter = SolTriadJsonAdapter(default_registry=sample_registry)

    req_inline = json.loads(json.dumps(base_valid_request))
    req_inline["evidence_records"] = [
        {
            "evidence_id": "ev-sensor-100",
            "domain": "thermal_control",
            "epistemic_status": "FACT",
            "timestamp_sec": current_time - 10.0,
            "payload_hash": "sha256-hash-ok",
            "metadata": {"sensor_vendor": "AcmeThermal"}
        }
    ]

    res = adapter.evaluate_json(req_inline, evaluation_time=current_time)
    assert res["verdict"] == CoherenceVerdict.FAIL.value
    assert any(
        d["code"] == DiagnosticCode.UNTRUSTED_EVIDENCE_SOURCE.value
        for d in res["diagnostics"]
    )

    req_inline["request_id"] = 42
    invalid_id_response = adapter.evaluate_json(req_inline, evaluation_time=current_time)
    assert invalid_id_response["request_id"] == "untrusted_evidence_request"


@pytest.mark.parametrize("bad_time", [float("nan"), float("inf"), True, "1740000000"])
def test_adapter_rejects_invalid_evaluation_time(base_valid_request, bad_time):
    adapter = SolTriadJsonAdapter()
    request = json.loads(json.dumps(base_valid_request))

    response = adapter.evaluate_json(request, evaluation_time=bad_time)

    assert response["verdict"] == CoherenceVerdict.FAIL.value
    assert any(d["field_name"] == "evaluation_time" for d in response["diagnostics"])


def test_adapter_rejects_request_controlled_evaluation_time(
    sample_registry, base_valid_request, current_time
):
    adapter = SolTriadJsonAdapter(default_registry=sample_registry)
    request = json.loads(json.dumps(base_valid_request))
    request["evaluation_time"] = current_time - 3600.0

    response = adapter.evaluate_json(request, evaluation_time=current_time)

    assert response["verdict"] == CoherenceVerdict.FAIL.value
    assert any("evaluation_time" in diagnostic["message"] for diagnostic in response["diagnostics"])


def test_adapter_rejects_coerced_boolean_values(sample_registry, base_valid_request, current_time):
    adapter = SolTriadJsonAdapter(default_registry=sample_registry)
    request = json.loads(json.dumps(base_valid_request))
    request["initial_state"]["active_flags"] = {"enabled": "false"}

    response = adapter.evaluate_json(request, evaluation_time=current_time)

    assert response["verdict"] == CoherenceVerdict.FAIL.value
    assert "must be a boolean" in response["diagnostics"][0]["message"]


def test_adapter_malformed_json_string(sample_registry):
    """Test 11: Malformed JSON string fails closed with STRUCTURAL_DEFECT."""
    adapter = SolTriadJsonAdapter(default_registry=sample_registry)
    bad_json_string = "{\"request_id\": \"test\", \"unclosed...}"

    res = adapter.evaluate_json(bad_json_string)
    assert res["verdict"] == CoherenceVerdict.FAIL.value
    assert res["request_id"] == "malformed_json"
    assert any(d["code"] == DiagnosticCode.STRUCTURAL_DEFECT.value for d in res["diagnostics"])


def test_adapter_rejects_non_object_json(sample_registry):
    adapter = SolTriadJsonAdapter(default_registry=sample_registry)

    response = adapter.evaluate_json('["not", "an", "object"]')

    assert response["verdict"] == CoherenceVerdict.FAIL.value
    assert response["request_id"] == "invalid_request_shape"


def test_adapter_controller_gate_bypass_prevention(sample_registry, base_valid_request, current_time):
    """Test 12: Simulates execution controller behavior rejecting any bypassed attempt."""
    adapter = SolTriadJsonAdapter(default_registry=sample_registry)

    # Tamper payload hash
    req_tamper = json.loads(json.dumps(base_valid_request))
    req_tamper["source"]["payload_hash"] = "forged-hash-123"

    res = adapter.evaluate_json(req_tamper, evaluation_time=current_time)
    assert res["verdict"] == CoherenceVerdict.FAIL.value

    # Controller gate check
    def execution_gate(response: dict) -> bool:
        if response.get("verdict") != "PASS":
            return False
        return True

    assert execution_gate(res) is False, "Execution controller MUST NOT allow non-PASS verdicts through"
