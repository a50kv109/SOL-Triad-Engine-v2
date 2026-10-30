import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from sol_triad import (
    EpistemicStatus,
    EvidenceRecord,
    InMemoryEvidenceRegistry,
    SolTriadJsonAdapter,
)


ROOT = Path(__file__).parents[2]


def _read_schema(name: str) -> dict:
    return json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))


def _valid_request(timestamp: float) -> dict:
    return {
        "request_id": "schema-test",
        "protocol_version": "0.4.0",
        "source": {
            "evidence_id": "registered-reading",
            "authority_domain": ["thermal"],
            "granted_scope": ["pump-1"],
            "granted_loss_domains": ["heat"],
            "epistemic_type": "FACT",
            "timestamp_sec": timestamp,
        },
        "constraint": {
            "domain_scope": ["thermal"],
            "target_objects": ["pump-1"],
            "protected_set": [],
        },
        "dissipate": {
            "loss_domain": ["heat"],
            "target_states": [],
            "side_effects": [],
        },
        "initial_state": {"current_values": {}},
    }


def test_json_schemas_are_valid_draft_2020_12():
    for name in ("sol_triad_request.schema.json", "sol_triad_response.schema.json"):
        Draft202012Validator.check_schema(_read_schema(name))


def test_adapter_request_and_all_verdict_responses_match_schemas():
    request_schema = _read_schema("sol_triad_request.schema.json")
    response_validator = Draft202012Validator(_read_schema("sol_triad_response.schema.json"))
    current_time = 1740000000.0
    registry = InMemoryEvidenceRegistry()
    registry.register(EvidenceRecord(
        evidence_id="registered-reading",
        domain="thermal",
        epistemic_status=EpistemicStatus.FACT,
        timestamp_sec=current_time - 10.0,
    ))
    adapter = SolTriadJsonAdapter(default_registry=registry)
    request = _valid_request(current_time - 10.0)
    Draft202012Validator(request_schema).validate(request)
    response_validator.validate(adapter.evaluate_json(request, evaluation_time=current_time))

    stale_request = _valid_request(current_time - 500.0)
    registry.register(EvidenceRecord(
        evidence_id="registered-reading",
        domain="thermal",
        epistemic_status=EpistemicStatus.FACT,
        timestamp_sec=current_time - 500.0,
    ))
    response_validator.validate(adapter.evaluate_json(stale_request, evaluation_time=current_time))

    invalid_request = dict(request)
    invalid_request["evidence_records"] = []
    with pytest.raises(ValidationError):
        Draft202012Validator(request_schema).validate(invalid_request)
    response_validator.validate(adapter.evaluate_json(invalid_request))

    client_controlled_time = _valid_request(current_time - 10.0)
    client_controlled_time["evaluation_time"] = current_time - 3600.0
    with pytest.raises(ValidationError):
        Draft202012Validator(request_schema).validate(client_controlled_time)
    response_validator.validate(
        adapter.evaluate_json(client_controlled_time, evaluation_time=current_time)
    )


def test_request_schema_rejects_non_boolean_state_flags():
    request = _valid_request(1740000000.0)
    request["initial_state"]["active_flags"] = {"enabled": "false"}
    validator = Draft202012Validator(_read_schema("sol_triad_request.schema.json"))

    assert list(validator.iter_errors(request))
