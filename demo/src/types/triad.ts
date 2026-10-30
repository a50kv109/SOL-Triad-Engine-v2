export type EpistemicStatus = "FACT" | "INFERENCE" | "UNKNOWN";

export type CoherenceVerdict = "PASS" | "REVIEW" | "FAIL";

export type DiagnosticSeverity = "INFO" | "WARNING" | "ERROR";

export type DiagnosticCode =
  | "TEMPORAL_FUTURE"
  | "TEMPORAL_STALE"
  | "TEMPORAL_INVALID_LIMIT"
  | "REGISTRY_OFFLINE"
  | "EVIDENCE_NOT_FOUND"
  | "EVIDENCE_MISMATCH"
  | "EVIDENCE_TIMESTAMP_MISMATCH"
  | "UNTRUSTED_EVIDENCE_SOURCE"
  | "EVIDENCE_DOMAIN_MISMATCH"
  | "EVIDENCE_PAYLOAD_MISMATCH"
  | "EVIDENCE_HASH_MISSING_IN_REGISTRY"
  | "EVIDENCE_HASH_REQUIRED_BY_REGISTRY"
  | "INFERENCE_UNSUPPORTED"
  | "INFERENCE_PREMISE_INVALID_STATUS"
  | "INFERENCE_CIRCULAR_DEPENDENCY"
  | "EVIDENCE_PASS"
  | "SCOPE_DEFECT_NONE"
  | "SCOPE_EXCEEDED_DOMAIN"
  | "SCOPE_EXCEEDED_OBJECTS"
  | "SCOPE_EXCEEDED_LOSS"
  | "SCOPE_PASS"
  | "STATE_PROTECTED_PARAM_MUTATED"
  | "STATE_PROTECTED_VALUE_VIOLATED"
  | "STATE_PROTECTED_FLAG_MUTATED"
  | "STATE_FORBIDDEN_FLAG_ACTIVE"
  | "STATE_REQUIRED_FLAG_MISSING"
  | "STATE_MIN_BOUND_BREACH"
  | "STATE_MAX_BOUND_BREACH"
  | "STATE_MISSING_VAR"
  | "STATE_NEGATIVE_RESOURCE_COST"
  | "STATE_INVALID_NUMERIC"
  | "STATE_PASS"
  | "UNIT_UNKNOWN"
  | "UNIT_MISSING"
  | "UNIT_INCOMPATIBLE"
  | "UNIT_CONVERSION_FAILED"
  | "UNIT_PASS"
  | "STRUCTURAL_DEFECT";

export interface CoherenceDiagnostic {
  code: DiagnosticCode;
  severity: DiagnosticSeverity;
  message: string;
  primitive?: "SOURCE" | "CONSTRAINT" | "DISSIPATE" | "STATE";
  field_name?: string;
}

export interface EvidenceRecord {
  evidence_id: string;
  domain: string;
  epistemic_status: EpistemicStatus;
  timestamp_sec: number;
  payload_hash?: string;
  metadata?: Record<string, unknown>;
}

export interface SourcePrimitive {
  evidence_id: string;
  authority_domain: string[] | null;
  granted_scope: string[] | null;
  granted_loss_domains: string[] | null;
  epistemic_type: EpistemicStatus;
  timestamp_sec: number;
  max_age_sec: number;
  corroborating_evidence_ids?: string[];
  payload_hash?: string;
}

export interface ConstraintPrimitive {
  domain_scope: string[];
  target_objects: string[];
  protected_set: string[];
  protected_values?: Record<string, number>;
  max_bounds?: Record<string, number>;
  min_bounds?: Record<string, number>;
  units?: Record<string, string>;
  protected_flags?: string[];
  forbidden_flags?: Record<string, boolean>;
  required_flags?: Record<string, boolean>;
}

export interface DissipatePrimitive {
  loss_domain: string[];
  target_states: string[];
  side_effects: string[];
  resource_cost?: Record<string, number>;
  state_delta?: Record<string, number>;
  flag_delta?: Record<string, boolean>;
  units?: Record<string, string>;
}

export interface SystemState {
  current_values: Record<string, number>;
  active_flags: Record<string, boolean>;
  units: Record<string, string>;
}

export interface PairwiseEvaluation {
  relationship: string;
  is_valid: boolean;
  verdict: CoherenceVerdict;
  diagnostics: CoherenceDiagnostic[];
}

export interface EvaluationReport {
  verdict: CoherenceVerdict;
  engine_version: string;
  timestamp_sec: number;
  pairwise_checks: {
    P_SC: PairwiseEvaluation;
    P_CD: PairwiseEvaluation;
    P_SD: PairwiseEvaluation;
  };
  diagnostics: CoherenceDiagnostic[];
  simulated_values: Record<string, number>;
  simulated_flags: Record<string, boolean>;
  messages: string[];
}
