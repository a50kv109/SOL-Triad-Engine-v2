"""
SOL-Triad Engine v0.4.1
Agent Integration Adapter & Machine-Readable Contract.

Provides a decoupled, fail-closed bridge between AI Agent architectures
(planners, tool-calling systems, reasoning loops) and the core SolTriadEngine.
"""

import json
import math
import time
from typing import Dict, Any, Optional, Union, List, Set

from .models import (
    SourcePrimitive,
    ConstraintPrimitive,
    DissipatePrimitive,
    SystemState,
    EpistemicStatus,
    CoherenceVerdict,
    CoherenceDiagnostic,
    DiagnosticCode,
    DiagnosticSeverity,
    PairwiseEvaluation,
    EvaluationReport,
)
from .evidence import EvidenceRegistryOracle
from .engine import SolTriadEngine


class SolTriadJsonAdapter:
    """
    Standard JSON Adapter for SOL-Triad Engine v0.4.1.

    The JSON protocol version remains 0.4.0 for backward compatibility.

    Adheres to schemas/sol_triad_request.schema.json and
    schemas/sol_triad_response.schema.json.
    """
    PROTOCOL_VERSION = "0.4.0"
    SUPPORTED_VERSIONS = {"0.4.0"}

    def __init__(
        self,
        default_registry: Optional[EvidenceRegistryOracle] = None,
        engine: Optional[SolTriadEngine] = None,
    ):
        self.default_registry = default_registry
        self.engine = engine if engine is not None else SolTriadEngine(registry=default_registry)

    def evaluate_json(
        self,
        request_input: Union[str, Dict[str, Any]],
        registry: Optional[EvidenceRegistryOracle] = None,
        evaluation_time: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Parses a JSON string or dict request, validates its structure,
        evaluates via SolTriadEngine, and serializes the report to a
        JSON-compatible dictionary matching sol_triad_response.schema.json.
        """
        current_ts = time.time()
        if evaluation_time is not None:
            try:
                current_ts = self._number(evaluation_time, "evaluation_time")
            except ValueError as ex:
                return self._create_fail_response(
                    request_id="invalid_evaluation_time",
                    message=str(ex),
                    code=DiagnosticCode.STRUCTURAL_DEFECT,
                    field_name="evaluation_time",
                    timestamp_sec=current_ts,
                )
        request_id = "unknown_request"

        # 1. Parse JSON if string
        if isinstance(request_input, str):
            try:
                data = json.loads(request_input, parse_constant=self._reject_json_constant)
            except (json.JSONDecodeError, ValueError) as e:
                return self._create_fail_response(
                    request_id="malformed_json",
                    message=f"JSON decoding failure: {str(e)}",
                    code=DiagnosticCode.STRUCTURAL_DEFECT,
                    timestamp_sec=current_ts,
                )
        elif isinstance(request_input, dict):
            data = request_input
        else:
            return self._create_fail_response(
                request_id="invalid_input_type",
                message=f"Expected JSON string or dict, got {type(request_input).__name__}",
                code=DiagnosticCode.STRUCTURAL_DEFECT,
                timestamp_sec=current_ts,
            )

        if not isinstance(data, dict):
            return self._create_fail_response(
                request_id="invalid_request_shape",
                message="The JSON request must be an object",
                code=DiagnosticCode.STRUCTURAL_DEFECT,
                timestamp_sec=current_ts,
            )

        if "evidence_records" in data:
            untrusted_request_id = data.get("request_id")
            if not isinstance(untrusted_request_id, str) or not untrusted_request_id.strip():
                untrusted_request_id = "untrusted_evidence_request"
            return self._create_fail_response(
                request_id=untrusted_request_id,
                message=(
                    "Inline evidence_records are not trusted. Register evidence in a "
                    "host-controlled EvidenceRegistryOracle instead."
                ),
                code=DiagnosticCode.UNTRUSTED_EVIDENCE_SOURCE,
                field_name="evidence_records",
                timestamp_sec=current_ts,
            )

        # 2. Extract request_id
        raw_request_id = data.get("request_id")
        if not isinstance(raw_request_id, str) or not raw_request_id.strip():
            return self._create_fail_response(
                request_id="missing_request_id",
                message="Field 'request_id' is required and must be a non-empty string",
                code=DiagnosticCode.STRUCTURAL_DEFECT,
                timestamp_sec=current_ts,
            )
        request_id = raw_request_id

        try:
            self._validate_keys(
                data,
                {"request_id", "protocol_version", "engine_version", "evaluation_context",
                 "source", "constraint", "dissipate", "initial_state"},
                set(),
                "request",
            )
        except ValueError as ex:
            return self._create_fail_response(
                request_id=request_id,
                message=str(ex),
                code=DiagnosticCode.STRUCTURAL_DEFECT,
                timestamp_sec=current_ts,
            )

        # 3. Validate Protocol Version
        proto_ver = data.get("protocol_version")
        if not isinstance(proto_ver, str) or proto_ver not in self.SUPPORTED_VERSIONS:
            return self._create_fail_response(
                request_id=request_id,
                message=f"Unsupported protocol_version '{proto_ver}'. Supported: {sorted(list(self.SUPPORTED_VERSIONS))}",
                code=DiagnosticCode.STRUCTURAL_DEFECT,
                timestamp_sec=current_ts,
            )

        if "engine_version" in data and not isinstance(data["engine_version"], str):
            return self._create_fail_response(
                request_id=request_id,
                message="Field 'engine_version' must be a string",
                code=DiagnosticCode.STRUCTURAL_DEFECT,
                field_name="engine_version",
                timestamp_sec=current_ts,
            )
        if "evaluation_context" in data and not isinstance(data["evaluation_context"], dict):
            return self._create_fail_response(
                request_id=request_id,
                message="Field 'evaluation_context' must be an object",
                code=DiagnosticCode.STRUCTURAL_DEFECT,
                field_name="evaluation_context",
                timestamp_sec=current_ts,
            )

        # 4. Check Required Primitives
        for req_field in ("source", "constraint", "dissipate", "initial_state"):
            if req_field not in data or not isinstance(data[req_field], dict):
                return self._create_fail_response(
                    request_id=request_id,
                    message=f"Missing or invalid required section '{req_field}' in request payload",
                    code=DiagnosticCode.STRUCTURAL_DEFECT,
                    field_name=req_field,
                    timestamp_sec=current_ts,
                )

        # 5. Parse and Build Primitives
        try:
            source = self._parse_source(data["source"])
            constraint = self._parse_constraint(data["constraint"])
            dissipate = self._parse_dissipate(data["dissipate"])
            initial_state = self._parse_initial_state(data["initial_state"])
        except ValueError as ve:
            return self._create_fail_response(
                request_id=request_id,
                message=f"Validation error in request primitives: {str(ve)}",
                code=DiagnosticCode.STRUCTURAL_DEFECT,
                timestamp_sec=current_ts,
            )
        except TypeError as ex:
            return self._create_fail_response(
                request_id=request_id,
                message=f"Invalid request primitive type: {str(ex)}",
                code=DiagnosticCode.STRUCTURAL_DEFECT,
                timestamp_sec=current_ts,
            )

        # 6. Setup Evidence Registry
        active_registry = registry if registry is not None else self.default_registry

        # 7. Evaluate via Engine
        evaluator = self.engine
        if active_registry is not None and active_registry != self.engine.registry:
            evaluator = SolTriadEngine(registry=active_registry, clock=lambda: current_ts)

        report = evaluator.evaluate(
            s=source,
            c=constraint,
            d=dissipate,
            initial_state=initial_state,
            evaluation_time=current_ts,
        )

        # 8. Format response according to schema
        return self._format_response(request_id, report)

    @staticmethod
    def _reject_json_constant(value: str) -> None:
        raise ValueError(f"Non-standard JSON numeric constant '{value}' is not allowed")

    @staticmethod
    def _number(value: Any, path: str) -> float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{path} must be a finite number")
        try:
            result = float(value)
        except OverflowError:
            raise ValueError(f"{path} must be a finite number") from None
        if not math.isfinite(result):
            raise ValueError(f"{path} must be a finite number")
        return result

    @staticmethod
    def _validate_keys(
        value: Dict[str, Any],
        allowed: Set[str],
        required: Set[str],
        path: str,
    ) -> None:
        missing = required - value.keys()
        non_string_keys = [key for key in value if not isinstance(key, str)]
        if non_string_keys:
            raise ValueError(f"{path} keys must be strings")
        unknown = value.keys() - allowed
        if missing:
            raise ValueError(f"{path} is missing required field(s): {', '.join(sorted(missing))}")
        if unknown:
            raise ValueError(f"{path} contains unsupported field(s): {', '.join(sorted(unknown))}")

    @staticmethod
    def _object(value: Any, path: str) -> Dict[str, Any]:
        if not isinstance(value, dict):
            raise ValueError(f"{path} must be an object")
        return value

    @staticmethod
    def _string_list(value: Any, path: str, allow_none: bool = False) -> Optional[Set[str]]:
        if allow_none and value is None:
            return None
        if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
            raise ValueError(f"{path} must be an array of strings" + (" or null" if allow_none else ""))
        return set(value)

    @classmethod
    def _string_list_field(
        cls,
        obj: Dict[str, Any],
        key: str,
        path: str,
        required: bool = False,
        allow_none: bool = False,
    ) -> Optional[Set[str]]:
        if key not in obj:
            if required:
                raise ValueError(f"{path}.{key} is required")
            return None if allow_none else set()
        return cls._string_list(obj[key], f"{path}.{key}", allow_none)

    @classmethod
    def _number_mapping(cls, obj: Dict[str, Any], key: str, path: str) -> Dict[str, float]:
        if key not in obj:
            return {}
        value = cls._object(obj[key], f"{path}.{key}")
        result: Dict[str, float] = {}
        for field_name, field_value in value.items():
            if not isinstance(field_name, str):
                raise ValueError(f"{path}.{key} keys must be strings")
            result[field_name] = cls._number(field_value, f"{path}.{key}.{field_name}")
        return result

    @classmethod
    def _boolean_mapping(cls, obj: Dict[str, Any], key: str, path: str) -> Dict[str, bool]:
        if key not in obj:
            return {}
        value = cls._object(obj[key], f"{path}.{key}")
        result: Dict[str, bool] = {}
        for field_name, field_value in value.items():
            if not isinstance(field_name, str):
                raise ValueError(f"{path}.{key} keys must be strings")
            if not isinstance(field_value, bool):
                raise ValueError(f"{path}.{key}.{field_name} must be a boolean")
            result[field_name] = field_value
        return result

    @classmethod
    def _string_mapping(cls, obj: Dict[str, Any], key: str, path: str) -> Dict[str, str]:
        if key not in obj:
            return {}
        value = cls._object(obj[key], f"{path}.{key}")
        result: Dict[str, str] = {}
        for field_name, field_value in value.items():
            if not isinstance(field_name, str):
                raise ValueError(f"{path}.{key} keys must be strings")
            if not isinstance(field_value, str):
                raise ValueError(f"{path}.{key}.{field_name} must be a string")
            result[field_name] = field_value
        return result

    def _parse_source(self, s_dict: Dict[str, Any]) -> SourcePrimitive:
        self._validate_keys(
            s_dict,
            {"evidence_id", "authority_domain", "granted_scope", "granted_loss_domains",
             "epistemic_type", "timestamp_sec", "max_age_sec", "corroborating_evidence_ids",
             "payload_hash"},
            {"evidence_id", "authority_domain", "granted_scope", "granted_loss_domains",
             "epistemic_type", "timestamp_sec"},
            "source",
        )
        if not isinstance(s_dict["evidence_id"], str) or not s_dict["evidence_id"].strip():
            raise ValueError("source.evidence_id must be a non-empty string")

        try:
            epistemic_type = EpistemicStatus(s_dict["epistemic_type"])
        except (ValueError, TypeError):
            raise ValueError(f"Invalid source.epistemic_type '{s_dict.get('epistemic_type')}'") from None

        # Crucial: Distinguish None (structural defect) from empty list [] (zero privileges)
        authority_domain = self._string_list_field(s_dict, "authority_domain", "source", allow_none=True)
        granted_scope = self._string_list_field(s_dict, "granted_scope", "source", allow_none=True)
        granted_loss_domains = self._string_list_field(s_dict, "granted_loss_domains", "source", allow_none=True)
        corroborating = self._string_list_field(
            s_dict, "corroborating_evidence_ids", "source"
        ) or set()
        payload_hash = s_dict.get("payload_hash")
        if payload_hash is not None and not isinstance(payload_hash, str):
            raise ValueError("source.payload_hash must be a string or null")

        return SourcePrimitive(
            evidence_id=s_dict["evidence_id"],
            authority_domain=authority_domain,
            granted_scope=granted_scope,
            granted_loss_domains=granted_loss_domains,
            epistemic_type=epistemic_type,
            timestamp_sec=self._number(s_dict["timestamp_sec"], "source.timestamp_sec"),
            max_age_sec=self._number(s_dict.get("max_age_sec", 300.0), "source.max_age_sec"),
            corroborating_evidence_ids=corroborating,
            payload_hash=payload_hash,
        )

    def _parse_constraint(self, c_dict: Dict[str, Any]) -> ConstraintPrimitive:
        self._validate_keys(
            c_dict,
            {"domain_scope", "target_objects", "protected_set", "protected_values", "max_bounds",
             "min_bounds", "units", "protected_flags", "forbidden_flags", "required_flags"},
            {"domain_scope", "target_objects", "protected_set"},
            "constraint",
        )
        domain_scope = self._string_list_field(c_dict, "domain_scope", "constraint", required=True) or set()
        target_objects = self._string_list_field(c_dict, "target_objects", "constraint", required=True) or set()
        protected_set = self._string_list_field(c_dict, "protected_set", "constraint", required=True) or set()
        protected_flags = self._string_list_field(c_dict, "protected_flags", "constraint") or set()
        protected_values = self._number_mapping(c_dict, "protected_values", "constraint")
        max_bounds = self._number_mapping(c_dict, "max_bounds", "constraint")
        min_bounds = self._number_mapping(c_dict, "min_bounds", "constraint")
        units = self._string_mapping(c_dict, "units", "constraint")
        forbidden_flags = self._boolean_mapping(c_dict, "forbidden_flags", "constraint")
        required_flags = self._boolean_mapping(c_dict, "required_flags", "constraint")

        return ConstraintPrimitive(
            domain_scope=domain_scope,
            target_objects=target_objects,
            protected_set=protected_set,
            protected_values=protected_values,
            max_bounds=max_bounds,
            min_bounds=min_bounds,
            units=units,
            protected_flags=protected_flags,
            forbidden_flags=forbidden_flags,
            required_flags=required_flags,
        )

    def _parse_dissipate(self, d_dict: Dict[str, Any]) -> DissipatePrimitive:
        self._validate_keys(
            d_dict,
            {"loss_domain", "target_states", "side_effects", "resource_cost", "state_delta",
             "flag_delta", "units"},
            {"loss_domain", "target_states", "side_effects"},
            "dissipate",
        )
        loss_domain = self._string_list_field(d_dict, "loss_domain", "dissipate", required=True) or set()
        target_states = self._string_list_field(d_dict, "target_states", "dissipate", required=True) or set()
        side_effects = self._string_list_field(d_dict, "side_effects", "dissipate", required=True) or set()
        resource_cost = self._number_mapping(d_dict, "resource_cost", "dissipate")
        state_delta = self._number_mapping(d_dict, "state_delta", "dissipate")
        flag_delta = self._boolean_mapping(d_dict, "flag_delta", "dissipate")
        units = self._string_mapping(d_dict, "units", "dissipate")

        return DissipatePrimitive(
            loss_domain=loss_domain,
            target_states=target_states,
            side_effects=side_effects,
            resource_cost=resource_cost,
            state_delta=state_delta,
            flag_delta=flag_delta,
            units=units,
        )

    def _parse_initial_state(self, s_dict: Dict[str, Any]) -> SystemState:
        self._validate_keys(
            s_dict,
            {"current_values", "active_flags", "units"},
            {"current_values"},
            "initial_state",
        )
        current_values = self._number_mapping(s_dict, "current_values", "initial_state")
        active_flags = self._boolean_mapping(s_dict, "active_flags", "initial_state")
        units = self._string_mapping(s_dict, "units", "initial_state")

        return SystemState(
            current_values=current_values,
            active_flags=active_flags,
            units=units,
        )

    def _format_response(
        self,
        request_id: str,
        report: EvaluationReport,
    ) -> Dict[str, Any]:
        return {
            "request_id": request_id,
            "protocol_version": self.PROTOCOL_VERSION,
            "engine_version": report.engine_version,
            "verdict": report.verdict.value,
            "pairwise_checks": {
                k: v.as_dict() for k, v in report.pairwise_checks.items()
            },
            "diagnostics": [d.as_dict() for d in report.diagnostics],
            "simulated_values": report.simulated_values,
            "simulated_flags": report.simulated_flags,
            "evaluation_timestamp": report.timestamp_sec,
            "messages": [f"[{d.code.value}] {d.message}" for d in report.diagnostics],
        }

    def _create_fail_response(
        self,
        request_id: str,
        message: str,
        code: DiagnosticCode = DiagnosticCode.STRUCTURAL_DEFECT,
        primitive: Optional[str] = None,
        field_name: Optional[str] = None,
        timestamp_sec: Optional[float] = None,
    ) -> Dict[str, Any]:
        ts = timestamp_sec if timestamp_sec is not None else time.time()
        if not math.isfinite(ts):
            ts = time.time()
        if not isinstance(request_id, str):
            request_id = "invalid_request_id"
        diag = CoherenceDiagnostic(
            code=code,
            severity=DiagnosticSeverity.ERROR,
            message=message,
            primitive=primitive,
            field_name=field_name,
        )
        fail_pairwise = {
            rel: {
                "relationship": rel,
                "is_valid": False,
                "verdict": CoherenceVerdict.FAIL.value,
                "diagnostics": [diag.as_dict()],
            }
            for rel in ("P_SC", "P_CD", "P_SD")
        }
        return {
            "request_id": request_id,
            "protocol_version": self.PROTOCOL_VERSION,
            "engine_version": SolTriadEngine.VERSION,
            "verdict": CoherenceVerdict.FAIL.value,
            "pairwise_checks": fail_pairwise,
            "diagnostics": [diag.as_dict()],
            "simulated_values": {},
            "simulated_flags": {},
            "evaluation_timestamp": ts,
            "messages": [f"[{code.value}] {message}"],
        }
