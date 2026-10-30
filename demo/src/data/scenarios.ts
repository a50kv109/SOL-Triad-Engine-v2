import {
  SourcePrimitive,
  ConstraintPrimitive,
  DissipatePrimitive,
  SystemState,
  EvidenceRecord,
  CoherenceVerdict,
} from "../types/triad";

export interface Scenario {
  id: string;
  title: string;
  expectedVerdict: CoherenceVerdict;
  category: "Valid" | "Epistemic Review" | "Scope Bypass" | "Invariant Attack" | "Dimensional Exploit" | "Multi-Vector";
  description: string;
  source: SourcePrimitive;
  constraint: ConstraintPrimitive;
  dissipate: DissipatePrimitive;
  initialState: SystemState;
  registry: Record<string, EvidenceRecord>;
  evaluationTime: number;
}

export const PRESET_SCENARIOS: Scenario[] = [
  {
    id: "pass-nominal",
    title: "1. Nominal Hydraulic Actuation (PASS)",
    expectedVerdict: "PASS",
    category: "Valid",
    description: "Fully verified FACT, bounded scope, terminal state within min/max bounds and protected parameters held invariant.",
    evaluationTime: 1700000100,
    registry: {
      "ev-hyd-01": {
        evidence_id: "ev-hyd-01",
        domain: "hydraulics",
        epistemic_status: "FACT",
        timestamp_sec: 1700000080,
        payload_hash: "sha256-verified-telemetry",
      },
    },
    source: {
      evidence_id: "ev-hyd-01",
      authority_domain: ["hydraulics", "coolant"],
      granted_scope: ["valve_alpha", "pump_beta"],
      granted_loss_domains: ["thermal_exhaust"],
      epistemic_type: "FACT",
      timestamp_sec: 1700000080,
      max_age_sec: 120,
      payload_hash: "sha256-verified-telemetry",
    },
    constraint: {
      domain_scope: ["hydraulics"],
      target_objects: ["valve_alpha"],
      protected_set: ["safety_interlock"],
      protected_values: { chamber_id: 101.0 },
      min_bounds: { system_pressure: 1.5 },
      max_bounds: { system_pressure: 8.0 },
      units: { system_pressure: "bar" },
      protected_flags: ["emergency_stop"],
    },
    dissipate: {
      loss_domain: ["thermal_exhaust"],
      target_states: ["pressure_normalized"],
      side_effects: [],
      state_delta: { system_pressure: 1.2 },
      resource_cost: { coolant_reserve: 0.5 },
      units: { system_pressure: "bar" },
    },
    initialState: {
      current_values: {
        system_pressure: 3.0,
        chamber_id: 101.0,
        safety_interlock: 1.0,
        coolant_reserve: 10.0,
      },
      active_flags: { emergency_stop: false },
      units: { system_pressure: "bar" },
    },
  },
  {
    id: "review-stale",
    title: "2. Stale Telemetry Reading (REVIEW)",
    expectedVerdict: "REVIEW",
    category: "Epistemic Review",
    description: "Observation age (600s) exceeds maximum permitted age limit (120s). The engine halts with REVIEW instead of falsely approving.",
    evaluationTime: 1700000600,
    registry: {
      "ev-old-temp": {
        evidence_id: "ev-old-temp",
        domain: "thermal",
        epistemic_status: "FACT",
        timestamp_sec: 1700000000,
      },
    },
    source: {
      evidence_id: "ev-old-temp",
      authority_domain: ["thermal"],
      granted_scope: ["radiator"],
      granted_loss_domains: ["heat_sink"],
      epistemic_type: "FACT",
      timestamp_sec: 1700000000,
      max_age_sec: 120,
    },
    constraint: {
      domain_scope: ["thermal"],
      target_objects: ["radiator"],
      protected_set: [],
      min_bounds: { temp: 20.0 },
      max_bounds: { temp: 95.0 },
    },
    dissipate: {
      loss_domain: ["heat_sink"],
      target_states: ["cooling"],
      side_effects: [],
      state_delta: { temp: -5.0 },
    },
    initialState: {
      current_values: { temp: 80.0 },
      active_flags: {},
      units: {},
    },
  },
  {
    id: "review-inference",
    title: "3. Uncorroborated Inference (REVIEW)",
    expectedVerdict: "REVIEW",
    category: "Epistemic Review",
    description: "Agent claims action is justified by an INFERENCE, but supplies zero corroborating evidence IDs in the premise tree.",
    evaluationTime: 1700000050,
    registry: {
      "inf-prediction": {
        evidence_id: "inf-prediction",
        domain: "predictive_ops",
        epistemic_status: "INFERENCE",
        timestamp_sec: 1700000040,
      },
    },
    source: {
      evidence_id: "inf-prediction",
      authority_domain: ["predictive_ops"],
      granted_scope: ["optimizer"],
      granted_loss_domains: ["compute_cycles"],
      epistemic_type: "INFERENCE",
      timestamp_sec: 1700000040,
      max_age_sec: 300,
      corroborating_evidence_ids: [], // EMPTY!
    },
    constraint: {
      domain_scope: ["predictive_ops"],
      target_objects: ["optimizer"],
      protected_set: [],
    },
    dissipate: {
      loss_domain: ["compute_cycles"],
      target_states: ["model_updated"],
      side_effects: [],
    },
    initialState: {
      current_values: {},
      active_flags: {},
      units: {},
    },
  },
  {
    id: "fail-domain-escalation",
    title: "4. Domain Scope Escalation Attack (FAIL)",
    expectedVerdict: "FAIL",
    category: "Scope Bypass",
    description: "Agent granted 'civilian_avionics' authority attempts to command 'military_payload' actuation.",
    evaluationTime: 1700000050,
    registry: {
      "ev-avionics": {
        evidence_id: "ev-avionics",
        domain: "civilian_avionics",
        epistemic_status: "FACT",
        timestamp_sec: 1700000040,
      },
    },
    source: {
      evidence_id: "ev-avionics",
      authority_domain: ["civilian_avionics"],
      granted_scope: ["altimeter", "radio"],
      granted_loss_domains: ["battery_draw"],
      epistemic_type: "FACT",
      timestamp_sec: 1700000040,
      max_age_sec: 120,
    },
    constraint: {
      domain_scope: ["military_payload"], // UNAUTHORIZED!
      target_objects: ["altimeter"],
      protected_set: [],
    },
    dissipate: {
      loss_domain: ["battery_draw"],
      target_states: [],
      side_effects: [],
    },
    initialState: {
      current_values: {},
      active_flags: {},
      units: {},
    },
  },
  {
    id: "fail-protected-value",
    title: "5. Invariant Constant Tampering (FAIL)",
    expectedVerdict: "FAIL",
    category: "Invariant Attack",
    description: "Agent modifies protected constant 'encryption_seed' while keeping delta within broad min/max bounds. Caught by strict invariant validation.",
    evaluationTime: 1700000050,
    registry: {
      "ev-crypto": {
        evidence_id: "ev-crypto",
        domain: "crypto_subsystem",
        epistemic_status: "FACT",
        timestamp_sec: 1700000040,
      },
    },
    source: {
      evidence_id: "ev-crypto",
      authority_domain: ["crypto_subsystem"],
      granted_scope: ["key_manager"],
      granted_loss_domains: ["entropy_pool"],
      epistemic_type: "FACT",
      timestamp_sec: 1700000040,
      max_age_sec: 120,
    },
    constraint: {
      domain_scope: ["crypto_subsystem"],
      target_objects: ["key_manager"],
      protected_set: [],
      protected_values: { encryption_seed: 4096.0 }, // INVARIANT CONSTANT!
      min_bounds: { encryption_seed: 0.0 },
      max_bounds: { encryption_seed: 10000.0 },
    },
    dissipate: {
      loss_domain: ["entropy_pool"],
      target_states: [],
      side_effects: [],
      state_delta: { encryption_seed: 100.0 }, // 4096 -> 4196
    },
    initialState: {
      current_values: { encryption_seed: 4096.0 },
      active_flags: {},
      units: {},
    },
  },
  {
    id: "fail-nan-exploit",
    title: "6. NaN Inequality Bypass Exploit (FAIL)",
    expectedVerdict: "FAIL",
    category: "Invariant Attack",
    description: "Agent injects NaN into state_delta. In standard Python/JS, 'NaN < 10' is False, bypassing bounds checks. Explicitly neutralized by the engine.",
    evaluationTime: 1700000050,
    registry: {
      "ev-reactor": {
        evidence_id: "ev-reactor",
        domain: "core_reactor",
        epistemic_status: "FACT",
        timestamp_sec: 1700000040,
      },
    },
    source: {
      evidence_id: "ev-reactor",
      authority_domain: ["core_reactor"],
      granted_scope: ["control_rod"],
      granted_loss_domains: ["heat"],
      epistemic_type: "FACT",
      timestamp_sec: 1700000040,
      max_age_sec: 120,
    },
    constraint: {
      domain_scope: ["core_reactor"],
      target_objects: ["control_rod"],
      protected_set: [],
      min_bounds: { radiation: 0.0 },
      max_bounds: { radiation: 50.0 },
    },
    dissipate: {
      loss_domain: ["heat"],
      target_states: [],
      side_effects: [],
      state_delta: { radiation: NaN }, // ADVERSARIAL NaN!
    },
    initialState: {
      current_values: { radiation: 25.0 },
      active_flags: {},
      units: {},
    },
  },
  {
    id: "fail-negative-cost",
    title: "7. Free Resource Forgery (FAIL)",
    expectedVerdict: "FAIL",
    category: "Invariant Attack",
    description: "Agent specifies negative resource cost (-500 credit) attempting to synthesize unauthorized assets during dissipation.",
    evaluationTime: 1700000050,
    registry: {
      "ev-wallet": {
        evidence_id: "ev-wallet",
        domain: "ledger",
        epistemic_status: "FACT",
        timestamp_sec: 1700000040,
      },
    },
    source: {
      evidence_id: "ev-wallet",
      authority_domain: ["ledger"],
      granted_scope: ["account_01"],
      granted_loss_domains: ["gas_fee"],
      epistemic_type: "FACT",
      timestamp_sec: 1700000040,
      max_age_sec: 120,
    },
    constraint: {
      domain_scope: ["ledger"],
      target_objects: ["account_01"],
      protected_set: [],
    },
    dissipate: {
      loss_domain: ["gas_fee"],
      target_states: [],
      side_effects: [],
      resource_cost: { credits: -500.0 }, // NEGATIVE FORGERY!
    },
    initialState: {
      current_values: { credits: 100.0 },
      active_flags: {},
      units: {},
    },
  },
  {
    id: "fail-unknown-unit",
    title: "8. Unknown Dimensionality Bypass (FAIL)",
    expectedVerdict: "FAIL",
    category: "Dimensional Exploit",
    description: "Agent attempts to exploit unknown units: both declare 'quantum_flux'. The prototype accepted None == None; v0.3.1 strictly blocks unknown units.",
    evaluationTime: 1700000050,
    registry: {
      "ev-flux": {
        evidence_id: "ev-flux",
        domain: "experimental",
        epistemic_status: "FACT",
        timestamp_sec: 1700000040,
      },
    },
    source: {
      evidence_id: "ev-flux",
      authority_domain: ["experimental"],
      granted_scope: ["flux_core"],
      granted_loss_domains: ["leakage"],
      epistemic_type: "FACT",
      timestamp_sec: 1700000040,
      max_age_sec: 120,
    },
    constraint: {
      domain_scope: ["experimental"],
      target_objects: ["flux_core"],
      protected_set: [],
      units: { flux: "quantum_flux" }, // UNKNOWN!
    },
    dissipate: {
      loss_domain: ["leakage"],
      target_states: [],
      side_effects: [],
      state_delta: { flux: 5.0 },
      units: { flux: "quantum_flux" }, // SAME UNKNOWN!
    },
    initialState: {
      current_values: { flux: 10.0 },
      active_flags: {},
      units: { flux: "quantum_flux" },
    },
  },
  {
    id: "fail-multi-vector",
    title: "9. Multi-Vector Compound Attack (FAIL)",
    expectedVerdict: "FAIL",
    category: "Multi-Vector",
    description: "Simultaneous attack combining forged evidence ID, unauthorized domain scope, unauthorized loss domain, and mutation of protected set.",
    evaluationTime: 1700000050,
    registry: {}, // EMPTY REGISTRY -> Forged ID!
    source: {
      evidence_id: "ev-ghost-phantom",
      authority_domain: ["safe_domain"],
      granted_scope: ["safe_object"],
      granted_loss_domains: ["safe_sink"],
      epistemic_type: "FACT",
      timestamp_sec: 1700000040,
      max_age_sec: 120,
    },
    constraint: {
      domain_scope: ["unauthorized_domain_1"],
      target_objects: ["safe_object", "unauthorized_target"],
      protected_set: ["critical_core_lock"],
    },
    dissipate: {
      loss_domain: ["unauthorized_sink"],
      target_states: [],
      side_effects: ["critical_core_lock"], // MUTATES PROTECTED!
    },
    initialState: {
      current_values: { critical_core_lock: 1.0 },
      active_flags: {},
      units: {},
    },
  },
];
