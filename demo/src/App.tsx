import React, { useState, useMemo } from "react";
import {
  ShieldCheck,
  AlertTriangle,
  XCircle,
  RotateCcw,
  FileText,
  Boxes,
  Code2,
  Layers,
  ArrowRight,
  Database,
  Clock,
  Sparkles,
  GitBranch,
  Terminal,
  ExternalLink,
  ChevronRight,
  ChevronDown,
  Info,
  Scale,
  Cpu,
  Lock,
  Download,
} from "lucide-react";
import { PRESET_SCENARIOS, Scenario } from "./data/scenarios";
import { evaluateTriad } from "./services/engineService";
import {
  CoherenceVerdict,
  EvaluationReport,
  SourcePrimitive,
  ConstraintPrimitive,
  DissipatePrimitive,
  SystemState,
  EvidenceRecord,
} from "./types/triad";

// Static reference catalog; these entries are not executed by the demo.
interface TestItem {
  id: string;
  name: string;
  category: "Adversarial" | "Unit: Models & Units" | "Unit: Evidence" | "Unit: Scope" | "Unit: State" | "Integration" | "Unit: Adapter & Agent Integration";
  file: string;
  attackVector?: string;
}

const ALL_TESTS: TestItem[] = [
  // Adversarial (16)
  { id: "adv-1", name: "test_adversarial_domain_substitution", category: "Adversarial", file: "tests/adversarial/test_domain_scope_bypass.py", attackVector: "Agent requests unauthorized military domain with civilian token" },
  { id: "adv-2", name: "test_adversarial_prefix_spoofing", category: "Adversarial", file: "tests/adversarial/test_domain_scope_bypass.py", attackVector: "Agent spoofs prefix 'telemetry' to claim 'telemetry_superadmin'" },
  { id: "adv-3", name: "test_adversarial_unauthorized_loss_domain_leakage", category: "Adversarial", file: "tests/adversarial/test_domain_scope_bypass.py", attackVector: "Agent vents toxic exhaust into ungranted environmental sink" },
  { id: "adv-4", name: "test_adversarial_hallucinated_evidence_id", category: "Adversarial", file: "tests/adversarial/test_epistemic_evidence_bypass.py", attackVector: "Agent invents non-existent evidence ID 'ev-ghost-999'" },
  { id: "adv-5", name: "test_adversarial_time_travel_future_timestamp", category: "Adversarial", file: "tests/adversarial/test_epistemic_evidence_bypass.py", attackVector: "Agent supplies future timestamp (+3600s) claiming prophetic observation" },
  { id: "adv-6", name: "test_adversarial_tampered_payload_hash", category: "Adversarial", file: "tests/adversarial/test_epistemic_evidence_bypass.py", attackVector: "Agent references authentic evidence ID but tampers with SHA-256 digest" },
  { id: "adv-7", name: "test_adversarial_inference_with_unregistered_premise", category: "Adversarial", file: "tests/adversarial/test_epistemic_evidence_bypass.py", attackVector: "Agent claims INFERENCE supported by hallucinated premise ID" },
  { id: "adv-7b", name: "test_adversarial_source_hash_supplied_registry_hash_missing", category: "Adversarial", file: "tests/adversarial/test_epistemic_evidence_bypass.py", attackVector: "Source specifies cryptographic payload_hash, but registry record has no hash anchor" },
  { id: "adv-7c", name: "test_adversarial_registry_hash_supplied_source_hash_missing", category: "Adversarial", file: "tests/adversarial/test_epistemic_evidence_bypass.py", attackVector: "Registry record mandates hash verification, but Source omitted payload_hash" },
  { id: "adv-7d", name: "test_adversarial_inference_stale_corroborating_evidence", category: "Adversarial", file: "tests/adversarial/test_epistemic_evidence_bypass.py", attackVector: "Agent claims INFERENCE supported by stale premise (age > max_age_sec)" },
  { id: "adv-7e", name: "test_adversarial_inference_future_corroborating_evidence", category: "Adversarial", file: "tests/adversarial/test_epistemic_evidence_bypass.py", attackVector: "Agent claims INFERENCE supported by future-dated premise timestamp" },
  { id: "adv-7f", name: "test_adversarial_inference_incompatible_premise_epistemic_status", category: "Adversarial", file: "tests/adversarial/test_epistemic_evidence_bypass.py", attackVector: "Agent attempts to ground INFERENCE on UNKNOWN unverified premise" },
  { id: "adv-7g", name: "test_adversarial_inference_circular_dependency", category: "Adversarial", file: "tests/adversarial/test_epistemic_evidence_bypass.py", attackVector: "Circular inference dependency: evidence cites itself as corroborating premise" },
  { id: "adv-8", name: "test_adversarial_nan_inequality_bypass_attack", category: "Adversarial", file: "tests/adversarial/test_invariant_state_bypass.py", attackVector: "Agent injects NaN to defeat inequality bounds ('NaN < min' is False in Python)" },
  { id: "adv-9", name: "test_adversarial_negative_resource_cost_forgery", category: "Adversarial", file: "tests/adversarial/test_invariant_state_bypass.py", attackVector: "Agent specifies negative resource cost (-500) to synthesize free credits" },
  { id: "adv-10", name: "test_adversarial_protected_value_mutation_within_bounds", category: "Adversarial", file: "tests/adversarial/test_invariant_state_bypass.py", attackVector: "Agent alters protected constant while keeping value inside outer min/max envelope" },
  { id: "adv-11", name: "test_adversarial_side_effect_smuggling_into_protected_set", category: "Adversarial", file: "tests/adversarial/test_invariant_state_bypass.py", attackVector: "Agent smuggles protected security parameter inside side_effects set" },
  { id: "adv-12", name: "test_adversarial_simultaneous_multi_vector_violation", category: "Adversarial", file: "tests/adversarial/test_multi_vector_bypass.py", attackVector: "Simultaneous forged evidence ID + unauthorized scope + protected parameter breach" },
  { id: "adv-13", name: "test_adversarial_coherence_between_review_and_fail", category: "Adversarial", file: "tests/adversarial/test_multi_vector_bypass.py", attackVector: "Compound stale evidence (REVIEW) + unauthorized target (FAIL) must resolve to FAIL" },
  { id: "adv-14", name: "test_adversarial_unknown_unit_bypass_attempt", category: "Adversarial", file: "tests/adversarial/test_unit_dimensional_bypass.py", attackVector: "Agent exploits unknown units 'quantum_flux' (v0.3 None==None vulnerability)" },
  { id: "adv-15", name: "test_adversarial_asymmetric_unit_omission_bypass", category: "Adversarial", file: "tests/adversarial/test_unit_dimensional_bypass.py", attackVector: "Agent specifies unit in Constraint but omits unit in Dissipate" },
  { id: "adv-16", name: "test_adversarial_incompatible_dimension_bypass", category: "Adversarial", file: "tests/adversarial/test_unit_dimensional_bypass.py", attackVector: "Agent applies time delta (sec) to pressure parameter (bar)" },

  // Unit: Models & Units (15)
  { id: "unit-m-1", name: "test_epistemic_status_values", category: "Unit: Models & Units", file: "tests/unit/test_models.py" },
  { id: "unit-m-2", name: "test_coherence_verdict_values", category: "Unit: Models & Units", file: "tests/unit/test_models.py" },
  { id: "unit-m-3", name: "test_source_primitive_construction", category: "Unit: Models & Units", file: "tests/unit/test_models.py" },
  { id: "unit-m-4", name: "test_constraint_primitive_construction", category: "Unit: Models & Units", file: "tests/unit/test_models.py" },
  { id: "unit-m-5", name: "test_diagnostic_serialization", category: "Unit: Models & Units", file: "tests/unit/test_models.py" },
  { id: "unit-u-1", name: "test_recognized_dimensions", category: "Unit: Models & Units", file: "tests/unit/test_units.py" },
  { id: "unit-u-2", name: "test_unknown_units_not_compatible", category: "Unit: Models & Units", file: "tests/unit/test_units.py" },
  { id: "unit-u-3", name: "test_asymmetric_unit_specification_fails", category: "Unit: Models & Units", file: "tests/unit/test_units.py" },
  { id: "unit-u-4", name: "test_incompatible_dimensions_fail", category: "Unit: Models & Units", file: "tests/unit/test_units.py" },
  { id: "unit-u-5", name: "test_unit_conversion_pressure", category: "Unit: Models & Units", file: "tests/unit/test_units.py" },
  { id: "unit-u-6", name: "test_unit_conversion_time", category: "Unit: Models & Units", file: "tests/unit/test_units.py" },
  { id: "unit-u-7", name: "test_unit_conversion_temperature", category: "Unit: Models & Units", file: "tests/unit/test_units.py" },
  { id: "unit-u-8", name: "test_unit_conversion_ratio", category: "Unit: Models & Units", file: "tests/unit/test_units.py" },
  { id: "unit-u-9", name: "test_conversion_incompatible_dimension_raises", category: "Unit: Models & Units", file: "tests/unit/test_units.py" },
  { id: "unit-u-10", name: "test_conversion_unknown_unit_raises", category: "Unit: Models & Units", file: "tests/unit/test_units.py" },

  // Unit: Evidence (9)
  { id: "unit-e-1", name: "test_valid_fact_passes", category: "Unit: Evidence", file: "tests/unit/test_evidence_validator.py" },
  { id: "unit-e-2", name: "test_future_timestamp_fails", category: "Unit: Evidence", file: "tests/unit/test_evidence_validator.py" },
  { id: "unit-e-3", name: "test_invalid_max_age_fails", category: "Unit: Evidence", file: "tests/unit/test_evidence_validator.py" },
  { id: "unit-e-4", name: "test_stale_evidence_returns_review", category: "Unit: Evidence", file: "tests/unit/test_evidence_validator.py" },
  { id: "unit-e-5", name: "test_registry_offline_returns_review", category: "Unit: Evidence", file: "tests/unit/test_evidence_validator.py" },
  { id: "unit-e-6", name: "test_forged_evidence_id_fails", category: "Unit: Evidence", file: "tests/unit/test_evidence_validator.py" },
  { id: "unit-e-7", name: "test_epistemic_status_mismatch_fails", category: "Unit: Evidence", file: "tests/unit/test_evidence_validator.py" },
  { id: "unit-e-8", name: "test_inference_with_valid_corroboration_passes", category: "Unit: Evidence", file: "tests/unit/test_evidence_validator.py" },
  { id: "unit-e-9", name: "test_inference_without_corroboration_returns_review", category: "Unit: Evidence", file: "tests/unit/test_evidence_validator.py" },

  // Unit: Scope (4)
  { id: "unit-s-1", name: "test_valid_scope_passes", category: "Unit: Scope", file: "tests/unit/test_scope_validator.py" },
  { id: "unit-s-2", name: "test_structural_defect_none_fails", category: "Unit: Scope", file: "tests/unit/test_scope_validator.py" },
  { id: "unit-s-3", name: "test_empty_set_zero_privileges_rejects_non_empty_request", category: "Unit: Scope", file: "tests/unit/test_scope_validator.py" },
  { id: "unit-s-4", name: "test_unauthorized_loss_domain_fails", category: "Unit: Scope", file: "tests/unit/test_scope_validator.py" },

  // Unit: State & Invariants (9)
  { id: "unit-st-1", name: "test_valid_state_simulation_passes", category: "Unit: State", file: "tests/unit/test_state_validator.py" },
  { id: "unit-st-2", name: "test_mutation_of_protected_set_fails", category: "Unit: State", file: "tests/unit/test_state_validator.py" },
  { id: "unit-st-3", name: "test_protected_value_violation_fails", category: "Unit: State", file: "tests/unit/test_state_validator.py" },
  { id: "unit-st-4", name: "test_min_bound_breach_fails", category: "Unit: State", file: "tests/unit/test_state_validator.py" },
  { id: "unit-st-5", name: "test_max_bound_breach_fails", category: "Unit: State", file: "tests/unit/test_state_validator.py" },
  { id: "unit-st-6", name: "test_missing_state_variable_fails", category: "Unit: State", file: "tests/unit/test_state_validator.py" },
  { id: "unit-st-7", name: "test_negative_resource_cost_fails", category: "Unit: State", file: "tests/unit/test_state_validator.py" },
  { id: "unit-st-8", name: "test_nan_numeric_value_fails", category: "Unit: State", file: "tests/unit/test_state_validator.py" },
  { id: "unit-st-9", name: "test_flag_invariants_and_protected_flags", category: "Unit: State", file: "tests/unit/test_state_validator.py" },

  // Unit: Adapter & Agent Integration (11)
  { id: "unit-ad-1", name: "test_adapter_valid_request_pass", category: "Unit: Adapter & Agent Integration", file: "tests/unit/test_adapter.py" },
  { id: "unit-ad-2", name: "test_adapter_missing_required_fields", category: "Unit: Adapter & Agent Integration", file: "tests/unit/test_adapter.py" },
  { id: "unit-ad-3", name: "test_adapter_null_vs_empty_collections", category: "Unit: Adapter & Agent Integration", file: "tests/unit/test_adapter.py" },
  { id: "unit-ad-4", name: "test_adapter_invalid_primitive_structures", category: "Unit: Adapter & Agent Integration", file: "tests/unit/test_adapter.py" },
  { id: "unit-ad-5", name: "test_adapter_unsupported_protocol_version", category: "Unit: Adapter & Agent Integration", file: "tests/unit/test_adapter.py" },
  { id: "unit-ad-6", name: "test_adapter_serialization_of_review", category: "Unit: Adapter & Agent Integration", file: "tests/unit/test_adapter.py" },
  { id: "unit-ad-7", name: "test_adapter_serialization_of_fail", category: "Unit: Adapter & Agent Integration", file: "tests/unit/test_adapter.py" },
  { id: "unit-ad-8", name: "test_adapter_diagnostic_preservation", category: "Unit: Adapter & Agent Integration", file: "tests/unit/test_adapter.py" },
  { id: "unit-ad-9", name: "test_adapter_inline_evidence_records", category: "Unit: Adapter & Agent Integration", file: "tests/unit/test_adapter.py" },
  { id: "unit-ad-10", name: "test_adapter_malformed_json_string", category: "Unit: Adapter & Agent Integration", file: "tests/unit/test_adapter.py" },
  { id: "unit-ad-11", name: "test_adapter_controller_gate_bypass_prevention", category: "Unit: Adapter & Agent Integration", file: "tests/unit/test_adapter.py" },

  // Integration (3)
  { id: "int-1", name: "test_full_pipeline_pass", category: "Integration", file: "tests/integration/test_engine.py" },
  { id: "int-2", name: "test_full_pipeline_review_on_stale_evidence", category: "Integration", file: "tests/integration/test_engine.py" },
  { id: "int-3", name: "test_full_pipeline_fail_on_unauthorized_scope", category: "Integration", file: "tests/integration/test_engine.py" },
];

export default function App() {
  const [activeTab, setActiveTab] = useState<"workbench" | "tests" | "architecture" | "docs" | "export">("workbench");
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>("pass-nominal");

  // Editable Scenario State in Workbench
  const currentScenario = useMemo(
    () => PRESET_SCENARIOS.find((s) => s.id === selectedScenarioId) || PRESET_SCENARIOS[0],
    [selectedScenarioId]
  );

  const [source, setSource] = useState<SourcePrimitive>(currentScenario.source);
  const [constraint, setConstraint] = useState<ConstraintPrimitive>(currentScenario.constraint);
  const [dissipate, setDissipate] = useState<DissipatePrimitive>(currentScenario.dissipate);
  const [state, setState] = useState<SystemState>(currentScenario.initialState);
  const [registry, setRegistry] = useState<Record<string, EvidenceRecord>>(currentScenario.registry);
  const [evalTime, setEvalTime] = useState<number>(currentScenario.evaluationTime);
  const [isEvaluating, setIsEvaluating] = useState<boolean>(false);

  // Test explorer state
  const [testFilter, setTestFilter] = useState<string>("All");
  const [selectedDoc, setSelectedDoc] = useState<string>("ARCHITECTURE.md");

  // Load a scenario
  const handleLoadScenario = (s: Scenario) => {
    setSelectedScenarioId(s.id);
    setSource(s.source);
    setConstraint(s.constraint);
    setDissipate(s.dissipate);
    setState(s.initialState);
    setRegistry(s.registry);
    setEvalTime(s.evaluationTime);
  };

  // Run evaluation
  const evaluationReport: EvaluationReport = useMemo(() => {
    return evaluateTriad(source, constraint, dissipate, state, registry, evalTime);
  }, [source, constraint, dissipate, state, registry, evalTime]);

  const verdictColor = (v: CoherenceVerdict) => {
    if (v === "PASS") return "border-emerald-500 bg-emerald-950/40 text-emerald-400";
    if (v === "REVIEW") return "border-amber-500 bg-amber-950/40 text-amber-400";
    return "border-rose-500 bg-rose-950/40 text-rose-400";
  };

  const filteredTests = useMemo(() => {
    if (testFilter === "All") return ALL_TESTS;
    if (testFilter === "Adversarial") return ALL_TESTS.filter((t) => t.category === "Adversarial");
    if (testFilter === "Unit") return ALL_TESTS.filter((t) => t.category.startsWith("Unit"));
    if (testFilter === "Integration") return ALL_TESTS.filter((t) => t.category === "Integration");
    return ALL_TESTS;
  }, [testFilter]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col selection:bg-indigo-500 selection:text-white">
      {/* Top Header */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-3 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-indigo-600/30 border border-indigo-500/50 flex items-center justify-center text-indigo-400 font-bold font-mono text-lg shadow-lg shadow-indigo-950">
              SOL
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-lg font-bold tracking-tight text-white font-mono">
                  SOL-Triad-Engine
                </h1>
                <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-950 text-indigo-300 border border-indigo-800 font-mono">
                  v0.4.0
                </span>
                <span className="text-xs px-2 py-0.5 rounded-full bg-amber-950 text-amber-300 border border-amber-800 font-mono">
                  Prototype · local simulation
                </span>
              </div>
              <p className="text-xs text-slate-400">
                TypeScript visual prototype · separate from the Python engine
              </p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="flex items-center space-x-1 bg-slate-950 p-1 rounded-xl border border-slate-800">
            <button
              onClick={() => setActiveTab("workbench")}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center space-x-1.5 ${
                activeTab === "workbench"
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
              }`}
            >
              <Cpu className="w-3.5 h-3.5" />
              <span>Workbench</span>
            </button>
            <button
              onClick={() => setActiveTab("tests")}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center space-x-1.5 ${
                activeTab === "tests"
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
              }`}
            >
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Test Catalog ({ALL_TESTS.length})</span>
            </button>
            <button
              onClick={() => setActiveTab("architecture")}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center space-x-1.5 ${
                activeTab === "architecture"
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              <span>Architecture & Matrix</span>
            </button>
            <button
              onClick={() => setActiveTab("docs")}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center space-x-1.5 ${
                activeTab === "docs"
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
              }`}
            >
              <FileText className="w-3.5 h-3.5" />
              <span>Docs Hub</span>
            </button>
            <button
              onClick={() => setActiveTab("export")}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center space-x-1.5 ${
                activeTab === "export"
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
              }`}
            >
              <GitBranch className="w-3.5 h-3.5" />
              <span>Audit & Export</span>
            </button>
          </nav>

          <button
            onClick={async () => {
              try {
                const res = await fetch("/SOL-Triad-Engine-v0.4.0.zip");
                if (!res.ok) throw new Error("HTTP " + res.status);
                const blob = await res.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = "SOL-Triad-Engine-v0.4.0.zip";
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
              } catch (e) {
                window.location.href = "/SOL-Triad-Engine-v0.4.0.zip";
              }
            }}
            className="px-3.5 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold font-mono flex items-center space-x-1.5 shadow-md shadow-emerald-950 transition-all cursor-pointer shrink-0"
            title="Download clean standalone Python package (.zip)"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download ZIP (v0.4.0)</span>
          </button>
        </div>
      </header>

      {/* Main Body */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 space-y-6">
        {/* ==================== WORKBENCH TAB ==================== */}
        {activeTab === "workbench" && (
          <div className="space-y-6">
            {/* Scenario Selector & Controls Bar */}
            <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
              <div className="flex-1 space-y-1">
                <label className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center space-x-1">
                  <span>Preset Validation Scenarios (PASS / REVIEW / FAIL)</span>
                </label>
                <div className="relative">
                  <select
                    value={selectedScenarioId}
                    onChange={(e) => {
                      const found = PRESET_SCENARIOS.find((s) => s.id === e.target.value);
                      if (found) handleLoadScenario(found);
                    }}
                    className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-sm text-slate-100 font-medium focus:outline-none focus:border-indigo-500 transition-colors"
                  >
                    {PRESET_SCENARIOS.map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.title} — [{s.expectedVerdict}] ({s.category})
                      </option>
                    ))}
                  </select>
                </div>
                <p className="text-xs text-slate-400 pt-1">
                  {currentScenario.description}
                </p>
              </div>

              <div className="flex items-center space-x-3 pt-2 md:pt-0">
                <div className="bg-slate-950 border border-slate-800 px-3 py-1.5 rounded-xl flex items-center space-x-2 text-xs font-mono">
                  <Clock className="w-3.5 h-3.5 text-slate-400" />
                  <span className="text-slate-400">Clock:</span>
                  <span className="text-slate-200 font-semibold">{evalTime}s</span>
                </div>
                <button
                  onClick={() => {
                    handleLoadScenario(currentScenario);
                  }}
                  className="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-xl border border-slate-700 flex items-center space-x-1.5 transition-colors"
                  title="Reset scenario inputs"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  <span>Reset</span>
                </button>
              </div>
            </div>

            {/* Verdict Hero Banner */}
            <div
              className={`p-6 rounded-2xl border-2 transition-all shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-6 ${verdictColor(
                evaluationReport.verdict
              )}`}
            >
              <div className="space-y-2">
                <div className="flex items-center space-x-3">
                  {evaluationReport.verdict === "PASS" && (
                    <div className="p-2.5 rounded-xl bg-emerald-500/20 text-emerald-400 border border-emerald-500/40">
                      <ShieldCheck className="w-8 h-8" />
                    </div>
                  )}
                  {evaluationReport.verdict === "REVIEW" && (
                    <div className="p-2.5 rounded-xl bg-amber-500/20 text-amber-400 border border-amber-500/40">
                      <AlertTriangle className="w-8 h-8" />
                    </div>
                  )}
                  {evaluationReport.verdict === "FAIL" && (
                    <div className="p-2.5 rounded-xl bg-rose-500/20 text-rose-400 border border-rose-500/40">
                      <XCircle className="w-8 h-8" />
                    </div>
                  )}
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="text-xs uppercase font-mono tracking-wider opacity-75">
                        Triad Arbiter Final Verdict
                      </span>
                      <span className="text-xs font-mono px-2 py-0.5 rounded bg-black/40">
                        Version {evaluationReport.engine_version}
                      </span>
                    </div>
                    <h2 className="text-3xl font-black font-mono tracking-tight">
                      COHERENCE: {evaluationReport.verdict}
                    </h2>
                  </div>
                </div>
                <p className="text-sm opacity-90 max-w-2xl">
                  {evaluationReport.verdict === "PASS" &&
                    "All required epistemic, authority scope, and physical state invariant checks passed strictly. State transition is authorized for external dispatch."}
                  {evaluationReport.verdict === "REVIEW" &&
                    "Epistemic uncertainty or stale observation detected. The engine operates fail-closed: it never silently converts REVIEW into PASS. Requires human operator or epistemic arbiter."}
                  {evaluationReport.verdict === "FAIL" &&
                    "Structural defect, scope escalation attempt, or physical invariant breach detected. Operation is strictly blocked."}
                </p>
              </div>

              {/* Pairwise Check Quick Badges */}
              <div className="flex flex-col sm:flex-row md:flex-col gap-2 w-full md:w-auto">
                {Object.entries(evaluationReport.pairwise_checks).map(([key, val]) => (
                  <div
                    key={key}
                    className="bg-black/40 px-3.5 py-2 rounded-xl border border-white/10 flex items-center justify-between space-x-4 text-xs font-mono"
                  >
                    <span className="font-semibold">{key}</span>
                    <span
                      className={`font-bold px-2 py-0.5 rounded ${
                        val.verdict === "PASS"
                          ? "bg-emerald-500/30 text-emerald-300"
                          : val.verdict === "REVIEW"
                          ? "bg-amber-500/30 text-amber-300"
                          : "bg-rose-500/30 text-rose-300"
                      }`}
                    >
                      {val.verdict}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Triad Primitives Inspector Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* SOURCE (S) */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex flex-col space-y-3">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <div className="flex items-center space-x-2">
                    <span className="w-6 h-6 rounded bg-blue-500/20 text-blue-400 font-mono text-xs flex items-center justify-center font-bold">
                      S
                    </span>
                    <h3 className="font-bold text-sm text-slate-200">SOURCE Primitive</h3>
                  </div>
                  <span
                    className={`text-xs font-mono px-2 py-0.5 rounded border ${
                      source.epistemic_type === "FACT"
                        ? "bg-emerald-950 text-emerald-300 border-emerald-800"
                        : source.epistemic_type === "INFERENCE"
                        ? "bg-blue-950 text-blue-300 border-blue-800"
                        : "bg-slate-800 text-slate-300 border-slate-700"
                    }`}
                  >
                    {source.epistemic_type}
                  </span>
                </div>

                <div className="space-y-2 text-xs font-mono flex-1">
                  <div>
                    <span className="text-slate-500">evidence_id:</span>{" "}
                    <span className="text-indigo-300 font-semibold">{source.evidence_id}</span>
                  </div>
                  <div>
                    <span className="text-slate-500">authority_domain:</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {source.authority_domain === null ? (
                        <span className="text-rose-400 bg-rose-950/60 px-1.5 py-0.5 rounded border border-rose-900">
                          None (Defect)
                        </span>
                      ) : source.authority_domain.length === 0 ? (
                        <span className="text-amber-400 bg-amber-950/60 px-1.5 py-0.5 rounded border border-amber-900">
                          ∅ (Zero Privileges)
                        </span>
                      ) : (
                        source.authority_domain.map((dom) => (
                          <span
                            key={dom}
                            className="bg-slate-800 px-1.5 py-0.5 rounded text-slate-300 border border-slate-700"
                          >
                            {dom}
                          </span>
                        ))
                      )}
                    </div>
                  </div>
                  <div>
                    <span className="text-slate-500">granted_scope:</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {source.granted_scope?.map((obj) => (
                        <span
                          key={obj}
                          className="bg-slate-800 px-1.5 py-0.5 rounded text-slate-300 border border-slate-700"
                        >
                          {obj}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div>
                    <span className="text-slate-500">granted_loss_domains:</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {source.granted_loss_domains?.map((ld) => (
                        <span
                          key={ld}
                          className="bg-slate-800 px-1.5 py-0.5 rounded text-slate-300 border border-slate-700"
                        >
                          {ld}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div className="pt-2 border-t border-slate-800/60 text-[11px] text-slate-400 flex justify-between">
                    <span>timestamp: {source.timestamp_sec}s</span>
                    <span>max_age: {source.max_age_sec}s</span>
                  </div>
                </div>
              </div>

              {/* CONSTRAINT (C) */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex flex-col space-y-3">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <div className="flex items-center space-x-2">
                    <span className="w-6 h-6 rounded bg-purple-500/20 text-purple-400 font-mono text-xs flex items-center justify-center font-bold">
                      C
                    </span>
                    <h3 className="font-bold text-sm text-slate-200">CONSTRAINT Primitive</h3>
                  </div>
                  <span className="text-xs font-mono text-slate-400">Invariants & Bounds</span>
                </div>

                <div className="space-y-2 text-xs font-mono flex-1">
                  <div>
                    <span className="text-slate-500">domain_scope:</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {constraint.domain_scope.map((dom) => (
                        <span
                          key={dom}
                          className="bg-purple-950/60 text-purple-300 border border-purple-900 px-1.5 py-0.5 rounded"
                        >
                          {dom}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div>
                    <span className="text-slate-500">target_objects:</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {constraint.target_objects.map((obj) => (
                        <span
                          key={obj}
                          className="bg-slate-800 px-1.5 py-0.5 rounded text-slate-300 border border-slate-700"
                        >
                          {obj}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div>
                    <span className="text-slate-500">protected_set:</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {constraint.protected_set.length === 0 ? (
                        <span className="text-slate-600">None</span>
                      ) : (
                        constraint.protected_set.map((p) => (
                          <span
                            key={p}
                            className="bg-rose-950/60 text-rose-300 border border-rose-900 px-1.5 py-0.5 rounded flex items-center space-x-1"
                          >
                            <Lock className="w-2.5 h-2.5" />
                            <span>{p}</span>
                          </span>
                        ))
                      )}
                    </div>
                  </div>
                  {constraint.protected_values && Object.keys(constraint.protected_values).length > 0 && (
                    <div>
                      <span className="text-slate-500">protected_values:</span>
                      <div className="text-[11px] text-amber-300 mt-0.5">
                        {Object.entries(constraint.protected_values).map(([k, v]) => (
                          <span key={k} className="bg-amber-950/50 border border-amber-900 px-1.5 py-0.5 rounded mr-1">
                            {k} == {v}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  {constraint.min_bounds && Object.keys(constraint.min_bounds).length > 0 && (
                    <div className="pt-1 text-[11px] text-slate-400">
                      <span>bounds: </span>
                      {Object.entries(constraint.min_bounds).map(([k, v]) => (
                        <span key={k}>
                          [{v} &le; {k} &le; {constraint.max_bounds?.[k] ?? "&infin;"}]
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* DISSIPATE (D) */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex flex-col space-y-3">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <div className="flex items-center space-x-2">
                    <span className="w-6 h-6 rounded bg-amber-500/20 text-amber-400 font-mono text-xs flex items-center justify-center font-bold">
                      D
                    </span>
                    <h3 className="font-bold text-sm text-slate-200">DISSIPATE Primitive</h3>
                  </div>
                  <span className="text-xs font-mono text-slate-400">Actuation & Deltas</span>
                </div>

                <div className="space-y-2 text-xs font-mono flex-1">
                  <div>
                    <span className="text-slate-500">loss_domain:</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {dissipate.loss_domain.map((ld) => (
                        <span
                          key={ld}
                          className="bg-amber-950/60 text-amber-300 border border-amber-900 px-1.5 py-0.5 rounded"
                        >
                          {ld}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div>
                    <span className="text-slate-500">state_delta:</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {dissipate.state_delta && Object.keys(dissipate.state_delta).length > 0 ? (
                        Object.entries(dissipate.state_delta).map(([k, v]) => (
                          <span
                            key={k}
                            className="bg-slate-800 px-1.5 py-0.5 rounded text-emerald-300 border border-slate-700"
                          >
                            &Delta;{k}: {isNaN(v) ? "NaN" : v > 0 ? `+${v}` : v} {dissipate.units?.[k] ?? ""}
                          </span>
                        ))
                      ) : (
                        <span className="text-slate-600">None</span>
                      )}
                    </div>
                  </div>
                  <div>
                    <span className="text-slate-500">resource_cost:</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {dissipate.resource_cost && Object.keys(dissipate.resource_cost).length > 0 ? (
                        Object.entries(dissipate.resource_cost).map(([k, v]) => (
                          <span
                            key={k}
                            className="bg-slate-800 px-1.5 py-0.5 rounded text-rose-300 border border-slate-700"
                          >
                            Cost({k}): {v}
                          </span>
                        ))
                      ) : (
                        <span className="text-slate-600">None</span>
                      )}
                    </div>
                  </div>
                  <div>
                    <span className="text-slate-500">side_effects:</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {dissipate.side_effects.length > 0 ? (
                        dissipate.side_effects.map((se) => (
                          <span
                            key={se}
                            className="bg-slate-800 px-1.5 py-0.5 rounded text-slate-300 border border-slate-700"
                          >
                            {se}
                          </span>
                        ))
                      ) : (
                        <span className="text-slate-600">None</span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Pairwise Evaluations & Terminal State Simulation */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {/* Pairwise Coherence Matrix Details */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <h3 className="text-sm font-bold text-slate-200 flex items-center space-x-2">
                    <Scale className="w-4 h-4 text-indigo-400" />
                    <span>Pairwise Verification Projections</span>
                  </h3>
                  <span className="text-xs font-mono text-slate-400">Formal Coherence</span>
                </div>

                <div className="space-y-3">
                  {Object.entries(evaluationReport.pairwise_checks).map(([key, p]) => (
                    <div
                      key={key}
                      className="bg-slate-950 border border-slate-800/80 rounded-xl p-3.5 space-y-2 font-mono text-xs"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-slate-300">{p.relationship}</span>
                        <span
                          className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                            p.verdict === "PASS"
                              ? "bg-emerald-950 text-emerald-300 border border-emerald-800"
                              : p.verdict === "REVIEW"
                              ? "bg-amber-950 text-amber-300 border border-amber-800"
                              : "bg-rose-950 text-rose-300 border border-rose-800"
                          }`}
                        >
                          {p.verdict}
                        </span>
                      </div>
                      <div className="text-[11px] text-slate-400">
                        {p.diagnostics.length > 0 ? (
                          p.diagnostics.map((d, i) => (
                            <p key={i} className="text-slate-300 pt-0.5">
                              &bull; [{d.code}] {d.message}
                            </p>
                          ))
                        ) : (
                          <p className="text-slate-500 italic">No violations recorded for this projection.</p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Terminal State Simulation Trace */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <h3 className="text-sm font-bold text-slate-200 flex items-center space-x-2">
                    <Database className="w-4 h-4 text-indigo-400" />
                    <span>Simulated Terminal State (S₀ &rarr; S&apos;)</span>
                  </h3>
                  <span className="text-xs font-mono text-slate-400">Invariant Check</span>
                </div>

                <div className="space-y-2">
                  <div className="overflow-x-auto">
                    <table className="w-full text-left font-mono text-xs">
                      <thead>
                        <tr className="border-b border-slate-800 text-slate-400">
                          <th className="py-1.5 px-2">Variable</th>
                          <th className="py-1.5 px-2">Initial (S₀)</th>
                          <th className="py-1.5 px-2">Delta / Cost</th>
                          <th className="py-1.5 px-2">Terminal (S&apos;)</th>
                          <th className="py-1.5 px-2">Constraint</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/40">
                        {Object.keys({
                          ...state.current_values,
                          ...evaluationReport.simulated_values,
                        }).map((varName) => {
                          const initialVal = state.current_values[varName];
                          const termVal = evaluationReport.simulated_values[varName];
                          const delta = dissipate.state_delta?.[varName];
                          const cost = dissipate.resource_cost?.[varName];
                          const isProtVal = constraint.protected_values?.[varName] !== undefined;
                          const isProtSet = constraint.protected_set.includes(varName);

                          return (
                            <tr key={varName} className="hover:bg-slate-800/30">
                              <td className="py-2 px-2 text-slate-200 font-semibold flex items-center space-x-1">
                                {isProtSet && <Lock className="w-3 h-3 text-rose-400" />}
                                <span>{varName}</span>
                              </td>
                              <td className="py-2 px-2 text-slate-400">
                                {initialVal !== undefined ? initialVal : "—"}
                              </td>
                              <td className="py-2 px-2 text-slate-400">
                                {delta !== undefined && (
                                  <span className="text-emerald-400">+{delta}</span>
                                )}
                                {cost !== undefined && (
                                  <span className="text-rose-400">-{cost}</span>
                                )}
                                {delta === undefined && cost === undefined && "0"}
                              </td>
                              <td className="py-2 px-2 text-slate-100 font-bold">
                                {termVal !== undefined ? (isNaN(termVal) ? "NaN" : termVal) : "—"}
                              </td>
                              <td className="py-2 px-2 text-[11px] text-slate-400">
                                {isProtVal && (
                                  <span className="text-amber-400">
                                    Invariant = {constraint.protected_values?.[varName]}
                                  </span>
                                )}
                                {constraint.min_bounds?.[varName] !== undefined && (
                                  <span>
                                    [{constraint.min_bounds[varName]}..{constraint.max_bounds?.[varName] ?? "&infin;"}]
                                  </span>
                                )}
                                {!isProtVal && constraint.min_bounds?.[varName] === undefined && "—"}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>

                  {/* Flag Invariants Display */}
                  {Object.keys(evaluationReport.simulated_flags).length > 0 && (
                    <div className="pt-3 border-t border-slate-800 text-xs font-mono">
                      <span className="text-slate-400">Simulated Flags:</span>
                      <div className="flex flex-wrap gap-2 mt-1">
                        {Object.entries(evaluationReport.simulated_flags).map(([flag, val]) => (
                          <span
                            key={flag}
                            className={`px-2 py-0.5 rounded border ${
                              val
                                ? "bg-emerald-950/60 text-emerald-300 border-emerald-800"
                                : "bg-slate-800 text-slate-400 border-slate-700"
                            }`}
                          >
                            {flag}: {val ? "true" : "false"}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Diagnostic Ledger */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-3">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h3 className="text-sm font-bold text-slate-200 flex items-center space-x-2">
                  <Terminal className="w-4 h-4 text-indigo-400" />
                  <span>Diagnostic Findings Ledger</span>
                </h3>
                <span className="text-xs font-mono text-slate-400">
                  {evaluationReport.diagnostics.length} findings
                </span>
              </div>

              <div className="space-y-2">
                {evaluationReport.diagnostics.map((diag, index) => (
                  <div
                    key={index}
                    className="bg-slate-950 border border-slate-800/80 rounded-xl p-3 flex items-start space-x-3 text-xs font-mono"
                  >
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase shrink-0 ${
                        diag.severity === "INFO"
                          ? "bg-blue-950 text-blue-300 border border-blue-800"
                          : diag.severity === "WARNING"
                          ? "bg-amber-950 text-amber-300 border border-amber-800"
                          : "bg-rose-950 text-rose-300 border border-rose-800"
                      }`}
                    >
                      {diag.severity}
                    </span>
                    <div className="flex-1 space-y-0.5">
                      <div className="flex items-center space-x-2">
                        <span className="font-bold text-slate-200">[{diag.code}]</span>
                        {diag.primitive && (
                          <span className="text-slate-500">primitive: {diag.primitive}</span>
                        )}
                        {diag.field_name && (
                          <span className="text-slate-500">field: {diag.field_name}</span>
                        )}
                      </div>
                      <p className="text-slate-300">{diag.message}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ==================== ADVERSARIAL TESTS TAB ==================== */}
        {activeTab === "tests" && (
          <div className="space-y-6">
            {/* Static test catalog; the demo does not execute pytest. */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <span className="px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800 text-xs font-mono">
                    Reference catalog only
                  </span>
                  <span className="text-xs text-slate-400">No Python tests are run by this TypeScript demo.</span>
                </div>
                <h2 className="text-2xl font-bold font-mono text-white">
                  {ALL_TESTS.length} listed cases
                </h2>
                <p className="text-sm text-slate-400 max-w-xl">
                  This historical catalog is illustrative and does not report current test results. Run pytest from the Python project root to verify the engine.
                </p>
              </div>
            </div>

            {/* Test Filters */}
            <div className="flex flex-wrap items-center gap-2">
              {["All", "Adversarial", "Unit", "Integration"].map((cat) => (
                <button
                  key={cat}
                  onClick={() => setTestFilter(cat)}
                  className={`px-3 py-1.5 rounded-xl text-xs font-medium transition-all ${
                    testFilter === cat
                      ? "bg-indigo-600 text-white"
                      : "bg-slate-900 text-slate-400 hover:bg-slate-800 hover:text-slate-200 border border-slate-800"
                  }`}
                >
                  {cat === "All"
                    ? `All Catalog Entries (${ALL_TESTS.length})`
                    : cat === "Adversarial"
                    ? `Adversarial (${ALL_TESTS.filter((test) => test.category === "Adversarial").length})`
                    : cat === "Unit"
                    ? `Unit (${ALL_TESTS.filter((test) => test.category.startsWith("Unit")).length})`
                    : `Integration (${ALL_TESTS.filter((test) => test.category === "Integration").length})`}
                </button>
              ))}
            </div>

            {/* Test Cards List */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {filteredTests.map((test) => (
                <div
                  key={test.id}
                  className="bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-xl p-4 space-y-2 transition-all font-mono text-xs"
                >
                  <div className="flex items-start justify-between gap-2">
                    <span className="font-semibold text-slate-200">{test.name}</span>
                    <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700 font-bold text-[10px]">
                      Reference
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-400 flex items-center space-x-1">
                    <span className="text-slate-500">File:</span>
                    <span className="text-indigo-300">{test.file}</span>
                  </div>
                  {test.attackVector && (
                    <div className="text-[11px] text-amber-300/90 bg-amber-950/30 border border-amber-900/50 p-2 rounded-lg">
                      <span className="font-semibold">Attack Defense:</span> {test.attackVector}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ==================== ARCHITECTURE & MATRIX TAB ==================== */}
        {activeTab === "architecture" && (
          <div className="space-y-6">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-6">
              <div>
                <h2 className="text-xl font-bold font-mono text-white">
                  SOL-Triad Verification Topology
                </h2>
                <p className="text-sm text-slate-400 mt-1">
                  Coherence is evaluated across three pairwise projections (P_SC, P_CD, P_SD) rooted in the canonical triad.
                </p>
              </div>

              {/* Visual Diagram */}
              <div className="p-8 bg-slate-950 rounded-2xl border border-slate-800 flex flex-col items-center justify-center">
                <div className="max-w-xl w-full grid grid-cols-3 gap-8 text-center font-mono">
                  <div className="col-span-3 flex justify-center">
                    <div className="p-4 rounded-2xl bg-blue-950/60 border border-blue-700 text-blue-200 w-52 shadow-xl shadow-blue-950/50">
                      <div className="font-bold text-base text-blue-400">SOURCE (S)</div>
                      <div className="text-[11px] text-slate-400 mt-1">
                        Epistemic Grounding, Authority Domains & Granted Scope
                      </div>
                    </div>
                  </div>

                  <div className="col-span-3 flex items-center justify-around text-xs text-indigo-400 font-semibold px-4">
                    <div className="flex flex-col items-center space-y-1">
                      <span>P_SC (Grounding)</span>
                      <div className="w-0.5 h-12 bg-indigo-500/50" />
                    </div>
                    <div className="flex flex-col items-center space-y-1">
                      <span>P_SD (Loss Authority)</span>
                      <div className="w-0.5 h-12 bg-amber-500/50" />
                    </div>
                  </div>

                  <div className="col-span-3 grid grid-cols-2 gap-8">
                    <div className="p-4 rounded-2xl bg-purple-950/60 border border-purple-700 text-purple-200 shadow-xl shadow-purple-950/50">
                      <div className="font-bold text-base text-purple-400">CONSTRAINT (C)</div>
                      <div className="text-[11px] text-slate-400 mt-1">
                        Invariants, Bounds, Protected Values & Physical Units
                      </div>
                    </div>
                    <div className="p-4 rounded-2xl bg-amber-950/60 border border-amber-700 text-amber-200 shadow-xl shadow-amber-950/50">
                      <div className="font-bold text-base text-amber-400">DISSIPATE (D)</div>
                      <div className="text-[11px] text-slate-400 mt-1">
                        State Deltas, Resource Costs, Entropy Loss & Flags
                      </div>
                    </div>
                  </div>

                  <div className="col-span-3 flex justify-center pt-2">
                    <div className="px-4 py-1.5 rounded-full bg-slate-900 border border-slate-700 text-xs text-slate-300">
                      &larr; P_CD (State Invariant Simulation & Bounds) &rarr;
                    </div>
                  </div>
                </div>
              </div>

              {/* Pairwise Definitions Breakdown */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 font-mono text-xs">
                <div className="bg-slate-950 border border-slate-800 p-4 rounded-xl space-y-2">
                  <h4 className="font-bold text-indigo-400 text-sm">P_SC: SOURCE &harr; CONSTRAINT</h4>
                  <p className="text-slate-400 text-[11px]">
                    Validates that the justification exists in the external authoritative registry, is not stale or futuristic, and that Constraint domain and target objects fall within granted authority.
                  </p>
                </div>
                <div className="bg-slate-950 border border-slate-800 p-4 rounded-xl space-y-2">
                  <h4 className="font-bold text-amber-400 text-sm">P_SD: SOURCE &harr; DISSIPATE</h4>
                  <p className="text-slate-400 text-[11px]">
                    Validates that dissipation loss domains (heat, compute, fee, emissions) are explicitly authorized by the Source. Prevents unauthorized resource leakage.
                  </p>
                </div>
                <div className="bg-slate-950 border border-slate-800 p-4 rounded-xl space-y-2">
                  <h4 className="font-bold text-purple-400 text-sm">P_CD: CONSTRAINT &harr; DISSIPATE</h4>
                  <p className="text-slate-400 text-[11px]">
                    Simulates terminal state S&apos; = S₀ + &Delta; - Cost. Checks protected_set, protected_values, min/max bounds, flag states, and performs unit conversions.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ==================== DOCS HUB TAB ==================== */}
        {activeTab === "docs" && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              {/* Document Nav */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 space-y-2">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 pb-2 border-b border-slate-800">
                  Documentation Specs
                </h3>
                {[
                  "UNIVERSAL_STRUCTURAL_APPLICABILITY.md",
                  "AGENT_INTEGRATION.md",
                  "ARCHITECTURE.md",
                  "DATA_MODEL.md",
                  "VALIDATION_RULES.md",
                  "THREAT_MODEL.md",
                  "SOL_COMPATIBILITY.md",
                  "EXPERIMENTS.md",
                  "ROADMAP.md",
                  "README.md",
                ].map((docName) => (
                  <button
                    key={docName}
                    onClick={() => setSelectedDoc(docName)}
                    className={`w-full text-left px-3 py-2 rounded-xl text-xs font-mono transition-all flex items-center justify-between ${
                      selectedDoc === docName
                        ? "bg-indigo-600 text-white font-semibold"
                        : "text-slate-400 hover:bg-slate-800 hover:text-slate-200"
                    }`}
                  >
                    <span>{docName}</span>
                    <ChevronRight className="w-3.5 h-3.5 opacity-60" />
                  </button>
                ))}
              </div>

              {/* Document Content Viewer */}
              <div className="md:col-span-3 bg-slate-900 border border-slate-800 rounded-2xl p-6 font-mono text-xs space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <div className="flex items-center space-x-2">
                    <FileText className="w-4 h-4 text-indigo-400" />
                    <span className="font-bold text-sm text-slate-200">{selectedDoc}</span>
                  </div>
                  <span className="text-[11px] text-slate-500">docs/{selectedDoc}</span>
                </div>

                <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 text-slate-300 leading-relaxed max-h-[600px] overflow-y-auto space-y-3 whitespace-pre-wrap">
                  {selectedDoc === "UNIVERSAL_STRUCTURAL_APPLICABILITY.md" && (
                    <div>
                      {`# Universal Structural Applicability — SOL-Triad Framework

SOL provides a universal structural-causal vocabulary for representing, analyzing, and verifying systems across diverse domains of knowledge:

1. Two Levels of Application:
   - Level I: Physical, Technical, and Computational Systems
     Parameters represent concrete physical or numerical variables (mechanical stresses, power balances, software state machines, memory locks).
   - Level II: Semantic, Philosophical, Ethical, and Social Systems
     Concepts that are not physical scalars, but exhibit definite relationships, boundaries, and consequences (responsibility, distributive justice, trust, value preservation).

2. The Non-Equivalence Axiom:
   "Structural isomorphism is NOT semantic equivalence."
   - Physical energy is NOT identical to information.
   - Resource cost is NOT identical to moral harm.
   - Justice is NOT automatically reducible to a mathematical invariant.

3. Role of Domain Interpretation Modules:
   The engine evaluates formal mathematical, epistemic, and invariant consistency; domain-specific truth and empirical facts are anchored via external authoritative registries.`}
                    </div>
                  )}

                  {selectedDoc === "AGENT_INTEGRATION.md" && (
                    <div>
                      {`# AI Agent Integration Architecture — SOL-Triad Engine v0.4.0

The SOL-Triad Engine acts as an External Structural Verification Layer (Action Gate) for AI agents:

1. Agent Lifecycle:
   TASK -> AI AGENT REASONING -> PROPOSED ACTION -> SOL ADAPTER -> S-C-D TRIAD -> SOL ENGINE -> PASS / REVIEW / FAIL -> EXTERNAL CONTROLLER

2. Five Integration Modes:
   - Python SDK: Direct package import (Implemented)
   - JSON Interface: SolTriadJsonAdapter & JSON Schemas (Implemented in v0.4.0)
   - REST API: Lightweight HTTP microservice (Designed / Planned)
   - MCP Server: Model Context Protocol tool provider (Designed / Planned)
   - Action Gate: Middleware enforcement pattern (Architectural Pattern)

3. Security Boundaries:
   - Agents must never self-certify evidence.
   - REVIEW verdicts are fail-closed and must never silently become PASS.
   - The SOL engine does not execute actions or mutate actuators directly.`}
                    </div>
                  )}

                  {selectedDoc === "ARCHITECTURE.md" && (
                    <div>
                      {`# Architecture Specification — SOL-Triad Engine v0.4.0

The SOL-Triad Engine is an independent, deterministic verification kernel designed to evaluate proposed actions against foundational structural, epistemic, and invariant constraints.

Unlike conventional heuristic guardrails or LLM-as-a-judge approaches, the SOL-Triad Engine operates strictly on:
- Set theory (containment, intersection, disjointness).
- Propositional logic and fail-closed security invariants.
- Deterministic numerical simulation and physical dimensionality algebra.
- Explicit epistemic verification against external authoritative ground truth.

Key Components:
1. EvidenceValidator (P_SC Grounding & Epistemic Verification)
2. ScopeValidator (P_SC Domain Scope & P_SD Loss Scope)
3. StateValidator (P_CD State Simulation & Bounds Invariants)
4. UnitRegistry (Dimensional Compatibility & SI Conversions)
5. Decision Arbiter (Strict PASS / REVIEW / FAIL semantics)
6. SolTriadJsonAdapter (Machine-readable JSON schema bridge for AI agents)`}
                    </div>
                  )}

                  {selectedDoc === "SOL_COMPATIBILITY.md" && (
                    <div>
                      {`# SOL Compatibility & Architectural Lineage

Canonical Reference Repositories:
1. SOL-Engineering-Core: https://github.com/a50kv109/SOL-Engineering-Core
2. SOL-2-sol-for-agents: https://github.com/a50kv109/SOL-2-sol-for-agents
3. Deep-Seek--engineering-os-core-: https://github.com/a50kv109/Deep-Seek--engineering-os-core-

Core Principles:
- The verification kernel strictly fixes its verification primitives to the canonical triad: SOURCE, CONSTRAINT, DISSIPATE.
- STATE is modeled as an observed input snapshot (SystemState).
- COMPARE is formalized into the pairwise verification engine (P_SC, P_CD, P_SD).
- FLOW and CAPABILITY are external agent orchestrator concerns.`}
                    </div>
                  )}

                  {selectedDoc === "VALIDATION_RULES.md" && (
                    <div>
                      {`# Validation Rules & Verification Axioms

Evidence Axioms:
- Axiom EV-1: Finite time anchor (reject NaN, Inf)
- Axiom EV-2: No prophetic observations (t <= t_current)
- Axiom EV-3: Freshness window (t_current - t <= max_age_sec)
- Axiom EV-4: Authoritative registry grounding
- Axiom EV-5: Epistemic status coherence (FACT claimed == FACT recorded)
- Axiom EV-6: Domain grounding (record.domain in authority_domain)
- Axiom EV-7: Inference corroboration dependencies

Scope Axioms:
- Axiom SC-1: No structural defects (reject None fields)
- Axiom SC-2: Domain authority containment (C.domain <= S.auth)
- Axiom SC-3: Object target containment (C.target <= S.scope)
- Axiom SC-4: Loss domain containment (D.loss <= S.loss_auth)`}
                    </div>
                  )}

                  {selectedDoc === "THREAT_MODEL.md" && (
                    <div>
                      {`# Threat Model & Attack Surface Analysis

The SOL-Triad Engine addresses an environment where an AI agent plans actions and requests state transitions.

Attack Vectors Neutralized:
1. Hallucinated Evidence IDs -> EVIDENCE_NOT_FOUND (FAIL)
2. Epistemic Escalation -> EVIDENCE_MISMATCH (FAIL)
3. Premise-less Inference -> INFERENCE_UNSUPPORTED (REVIEW)
4. Time Travel / Stale Evidence -> TEMPORAL_FUTURE (FAIL) / TEMPORAL_STALE (REVIEW)
5. Domain Scope Escalation -> SCOPE_EXCEEDED_DOMAIN (FAIL)
6. Zero-Privilege Confusion -> None vs set() distinction
7. NaN / Inf Bounds Bypass -> STATE_INVALID_NUMERIC (FAIL)
8. Free Resource Minting -> STATE_NEGATIVE_RESOURCE_COST (FAIL)
9. Protected Constant Tampering -> STATE_PROTECTED_VALUE_VIOLATED (FAIL)`}
                    </div>
                  )}

                  {selectedDoc === "ROADMAP.md" && (
                    <div>
                      {`# Roadmap excerpt

This pane is static demo content and is not synchronized with the current project.
For the authoritative release status and roadmap, read docs/RELEASE_STATUS.md
and docs/ROADMAP.md in the Python project checkout.`}
                    </div>
                  )}

                  {!["ARCHITECTURE.md", "SOL_COMPATIBILITY.md", "VALIDATION_RULES.md", "THREAT_MODEL.md", "ROADMAP.md"].includes(
                    selectedDoc
                  ) && (
                    <div>
                      {`Documentation for ${selectedDoc} is accessible in the repository at /docs/${selectedDoc}.`}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ==================== GIT EXPORT TAB ==================== */}
        {activeTab === "export" && (
          <div className="space-y-6">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-6 font-mono text-xs">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
                <div>
                  <h2 className="text-xl font-bold text-white flex items-center space-x-2">
                    <GitBranch className="w-5 h-5 text-indigo-400" />
                    <span>SOL-Triad-Engine v0.4.0 — Historical Release Snapshot</span>
                  </h2>
                  <p className="text-slate-400 mt-1">
                    Historical v0.4.0 release snapshot. This visual prototype is not a live package audit or test runner.
                  </p>
                </div>
                <button
                  onClick={async () => {
                    try {
                      const res = await fetch("/SOL-Triad-Engine-v0.4.0.zip");
                      if (!res.ok) throw new Error("HTTP " + res.status);
                      const blob = await res.blob();
                      const url = window.URL.createObjectURL(blob);
                      const a = document.createElement("a");
                      a.href = url;
                      a.download = "SOL-Triad-Engine-v0.4.0.zip";
                      document.body.appendChild(a);
                      a.click();
                      document.body.removeChild(a);
                      window.URL.revokeObjectURL(url);
                    } catch (e) {
                      window.location.href = "/SOL-Triad-Engine-v0.4.0.zip";
                    }
                  }}
                  className="px-5 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold flex items-center space-x-2 shadow-lg shadow-emerald-950 transition-all cursor-pointer shrink-0 text-xs"
                >
                  <Download className="w-4 h-4" />
                  <span>Download ZIP Archive (v0.4.0)</span>
                </button>
              </div>

                {/* Audit Feature Verification Matrix */}
                <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-300 font-bold uppercase tracking-wider text-[11px] flex items-center space-x-1.5">
                      <ShieldCheck className="w-4 h-4 text-emerald-400" />
                      <span>Independent Audit Feature Matrix (Python vs Frontend vs Docs)</span>
                    </span>
                    <span className="text-[10px] text-slate-500">All Core Logic Implemented in Pure Python</span>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-left font-mono text-[11px]">
                      <thead>
                        <tr className="border-b border-slate-800 text-slate-400">
                          <th className="py-1 px-2">Subsystem Feature</th>
                          <th className="py-1 px-2">Python Kernel (`sol_triad`)</th>
                          <th className="py-1 px-2">Pytest Coverage</th>
                          <th className="py-1 px-2">Status & Location</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/40 text-slate-300">
                        <tr>
                          <td className="py-1.5 px-2 font-semibold">EvidenceRegistry & Lookup</td>
                          <td className="py-1.5 px-2 text-emerald-400">Implemented (Protocol + InMemory)</td>
                          <td className="py-1.5 px-2">9 Unit + 4 Adversarial</td>
                          <td className="py-1.5 px-2 text-slate-400">`sol_triad/evidence.py`, `validators.py`</td>
                        </tr>
                        <tr>
                          <td className="py-1.5 px-2 font-semibold">Fail-Closed Hash Integrity</td>
                          <td className="py-1.5 px-2 text-emerald-400">Implemented (Symmetric check)</td>
                          <td className="py-1.5 px-2">3 Adversarial Hash Tests</td>
                          <td className="py-1.5 px-2 text-slate-400">`validators.py` (L86-115)</td>
                        </tr>
                        <tr>
                          <td className="py-1.5 px-2 font-semibold">Deep Premise Verification</td>
                          <td className="py-1.5 px-2 text-emerald-400">Implemented (No cycles, valid status)</td>
                          <td className="py-1.5 px-2">4 Adversarial Premise Tests</td>
                          <td className="py-1.5 px-2 text-slate-400">`validators.py` (L125-180)</td>
                        </tr>
                        <tr>
                          <td className="py-1.5 px-2 font-semibold">JSON Agent Adapter (v0.4.0)</td>
                          <td className="py-1.5 px-2 text-emerald-400">Implemented (`SolTriadJsonAdapter`)</td>
                          <td className="py-1.5 px-2">11 Unit Integration Tests</td>
                          <td className="py-1.5 px-2 text-slate-400">`sol_triad/adapter.py`, `schemas/`</td>
                        </tr>
                        <tr>
                          <td className="py-1.5 px-2 font-semibold">Projections P_SC, P_CD, P_SD</td>
                          <td className="py-1.5 px-2 text-emerald-400">Implemented (Formal synthesis)</td>
                          <td className="py-1.5 px-2">Integration + Adversarial</td>
                          <td className="py-1.5 px-2 text-slate-400">`sol_triad/engine.py` (L60-95)</td>
                        </tr>
                        <tr>
                          <td className="py-1.5 px-2 font-semibold">Unit Conversions (SI Base)</td>
                          <td className="py-1.5 px-2 text-emerald-400">Implemented (Affine transformations)</td>
                          <td className="py-1.5 px-2">10 Unit + 3 Adversarial</td>
                          <td className="py-1.5 px-2 text-slate-400">`sol_triad/units.py`</td>
                        </tr>
                        <tr>
                          <td className="py-1.5 px-2 font-semibold">Terminal State Simulation</td>
                          <td className="py-1.5 px-2 text-emerald-400">Implemented (S₀ + &Delta; - Cost)</td>
                          <td className="py-1.5 px-2">9 Unit + 4 Adversarial</td>
                          <td className="py-1.5 px-2 text-slate-400">`validators.py` (L235-310)</td>
                        </tr>
                        <tr>
                          <td className="py-1.5 px-2 font-semibold">Decision Arbiter (PASS/REVIEW/FAIL)</td>
                          <td className="py-1.5 px-2 text-emerald-400">Implemented (Strict fail-closed)</td>
                          <td className="py-1.5 px-2">Integration + Adversarial</td>
                          <td className="py-1.5 px-2 text-slate-400">`sol_triad/engine.py` (L98-112)</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Local audit execution commands */}
                <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-2">
                  <span className="text-slate-500 uppercase tracking-wider text-[10px] font-bold">
                    Local Python verification commands
                  </span>
                  <pre className="text-emerald-400 overflow-x-auto text-xs">
{`# From the Python project root
python -m pip install -e ".[dev]"
pytest
python examples/basic_pass.py
python examples/agent_integration_demo.py`}
                  </pre>
                </div>

                {/* Package Tree View */}
                <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-2">
                  <span className="text-slate-500 uppercase tracking-wider text-[10px] font-bold">
                    Illustrative Python core tree (not a live manifest)
                  </span>
                  <pre className="text-indigo-300 text-xs">
{`SOL-Triad-Engine/
├── .gitignore                                 # Standard Python gitignore
├── LICENSE                                    # Apache 2.0 Open Source License
├── README.md                                  # Comprehensive documentation & quickstart
├── pyproject.toml                             # Standard PEP 517/621 packaging metadata
│
├── schemas/                                   # Machine-Readable Contracts (v0.4.0)
│   ├── sol_triad_request.schema.json          # JSON Request Schema
│   └── sol_triad_response.schema.json         # JSON Response Schema
│
├── sol_triad/                                 # Canonical Verification Kernel & Adapter
│   ├── __init__.py                            # Public API exports
│   ├── adapter.py                             # SolTriadJsonAdapter for AI Agents
│   ├── engine.py                              # SolTriadEngine coordinator & Decision Arbiter
│   ├── evidence.py                            # EvidenceRegistryOracle & InMemoryEvidenceRegistry
│   ├── models.py                              # Typed dataclasses & CoherenceVerdict enum
│   ├── units.py                               # UnitRegistry & dimensional conversion algebra
│   └── validators.py                          # EvidenceValidator, ScopeValidator, StateValidator
│
├── tests/                                     # Python unit, integration, and adversarial tests
│   ├── unit/
│   │   ├── test_adapter.py                    # Agent adapter tests
│   │   ├── test_models.py
│   │   ├── test_units.py
│   │   ├── test_evidence_validator.py
│   │   ├── test_scope_validator.py
│   │   └── test_state_validator.py
│   ├── integration/
│   │   └── test_engine.py
│   └── adversarial/
│       ├── test_domain_scope_bypass.py
│       ├── test_epistemic_evidence_bypass.py
│       ├── test_unit_dimensional_bypass.py
│       ├── test_invariant_state_bypass.py
│       └── test_multi_vector_bypass.py
│
├── docs/                                      # Architecture, integration, and project documentation
│   ├── AGENT_INTEGRATION.md                   # AI Agent integration architecture & security gates
│   ├── ARCHITECTURE.md                        # Structural architecture and host topology
│   ├── DATA_MODEL.md                          # Data models and attribute schemas
│   ├── EXPERIMENTS.md                         # Empirical benchmarks & prototype defect audit
│   ├── PURPOSE_AND_USE_CASES.md               # Engine purpose, 7 properties & domain analysis
│   ├── RELEASE_STATUS.md                      # Audit readiness matrix & 7 critical questions
│   ├── ROADMAP.md                             # Release roadmap and future milestones (v0.5.0/v0.6.0)
│   ├── SOL_COMPATIBILITY.md                   # Reference repository alignment (O7 taxonomy)
│   ├── THREAT_MODEL.md                        # Security threat model and attack mitigations
│   ├── UNIVERSAL_STRUCTURAL_APPLICABILITY.md  # Level I vs Level II systemic modeling
│   └── VALIDATION_RULES.md                    # Formal verification axioms (EV, SC, ST)
│
└── examples/                                  # Runnable Python examples
    ├── agent_integration_demo.py              # Full agent + controller execution demo
    ├── basic_pass.py                          # Complete PASS execution example
    ├── evidence_review.py                     # REVIEW scenario example (stale evidence)
    └── invariant_fail.py                      # FAIL scenario example (protected mutation)`}
                  </pre>
                </div>

                {/* Upstream repository reference */}
                <div className="p-5 bg-gradient-to-br from-indigo-950/40 via-slate-900 to-slate-950 rounded-xl border border-indigo-500/30 space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <GitBranch className="w-5 h-5 text-indigo-400" />
                      <h4 className="font-semibold text-slate-100 text-sm">Upstream Repository</h4>
                    </div>
                    <span className="px-2.5 py-0.5 rounded text-xs font-mono font-medium bg-slate-800 text-slate-300 border border-slate-700">
                      Status not available in demo
                    </span>
                  </div>

                  <p className="text-xs text-slate-300 leading-relaxed">
                    This visual prototype cannot inspect Git state, create commits, or publish changes. Use the repository page for the current upstream branch and release status.
                  </p>

                  <a
                    className="inline-flex items-center gap-2 text-sm text-indigo-300 hover:text-indigo-200"
                    href="https://github.com/a50kv109/SOL-Triad-Engine"
                    target="_blank"
                    rel="noreferrer"
                  >
                    View SOL-Triad-Engine on GitHub <ExternalLink className="w-4 h-4" />
                  </a>
                </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
