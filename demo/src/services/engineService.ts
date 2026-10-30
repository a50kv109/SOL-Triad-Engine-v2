import {
  SourcePrimitive,
  ConstraintPrimitive,
  DissipatePrimitive,
  SystemState,
  EvidenceRecord,
  EvaluationReport,
  CoherenceVerdict,
  CoherenceDiagnostic,
} from "../types/triad";

// Unit dimensionality mappings identical to sol_triad/units.py
const DIMENSIONS: Record<string, string> = {
  pa: "pressure",
  kpa: "pressure",
  mpa: "pressure",
  bar: "pressure",
  mbar: "pressure",
  psi: "pressure",
  atm: "pressure",
  torr: "pressure",

  s: "time",
  sec: "time",
  ms: "time",
  min: "time",
  hr: "time",
  hour: "time",
  day: "time",

  c: "temperature",
  celsius: "temperature",
  k: "temperature",
  kelvin: "temperature",
  f: "temperature",
  fahrenheit: "temperature",

  ratio: "ratio",
  fraction: "ratio",
  percent: "ratio",
  "%": "ratio",
  ppm: "ratio",

  j: "energy",
  joule: "energy",
  kj: "energy",
  kwh: "energy",
  cal: "energy",
  kcal: "energy",

  kg: "mass",
  g: "mass",
  mg: "mass",
  lb: "mass",

  m: "length",
  cm: "length",
  mm: "length",
  km: "length",
  inch: "length",
  ft: "length",

  hz: "frequency",
  khz: "frequency",
  mhz: "frequency",
  rpm: "rotational_speed",
};

const CONVERSIONS_TO_BASE: Record<string, [number, number]> = {
  pa: [1.0, 0.0],
  kpa: [1000.0, 0.0],
  mpa: [1000000.0, 0.0],
  bar: [100000.0, 0.0],
  mbar: [100.0, 0.0],
  psi: [6894.757293, 0.0],
  atm: [101325.0, 0.0],
  torr: [133.322368, 0.0],

  s: [1.0, 0.0],
  sec: [1.0, 0.0],
  ms: [0.001, 0.0],
  min: [60.0, 0.0],
  hr: [3600.0, 0.0],
  hour: [3600.0, 0.0],
  day: [86400.0, 0.0],

  k: [1.0, 0.0],
  kelvin: [1.0, 0.0],
  c: [1.0, 273.15],
  celsius: [1.0, 273.15],
  f: [5.0 / 9.0, 273.15 - (32.0 * 5.0) / 9.0],
  fahrenheit: [5.0 / 9.0, 273.15 - (32.0 * 5.0) / 9.0],

  ratio: [1.0, 0.0],
  fraction: [1.0, 0.0],
  percent: [0.01, 0.0],
  "%": [0.01, 0.0],
  ppm: [1e-6, 0.0],

  j: [1.0, 0.0],
  joule: [1.0, 0.0],
  kj: [1000.0, 0.0],
  kwh: [3600000.0, 0.0],
  cal: [4.184, 0.0],
  kcal: [4184.0, 0.0],

  kg: [1.0, 0.0],
  g: [0.001, 0.0],
  mg: [1e-6, 0.0],
  lb: [0.45359237, 0.0],

  m: [1.0, 0.0],
  cm: [0.01, 0.0],
  mm: [0.001, 0.0],
  km: [1000.0, 0.0],
  inch: [0.0254, 0.0],
  ft: [0.3048, 0.0],

  hz: [1.0, 0.0],
  khz: [1000.0, 0.0],
  mhz: [1000000.0, 0.0],
  rpm: [1.0 / 60.0, 0.0],
};

function normalizeUnit(u?: string | null): string | null {
  if (!u) return null;
  const trimmed = u.trim().toLowerCase();
  return trimmed.length > 0 ? trimmed : null;
}

function areUnitsCompatible(u1?: string | null, u2?: string | null): [boolean, string] {
  const norm1 = normalizeUnit(u1);
  const norm2 = normalizeUnit(u2);

  if (!norm1 && !norm2) return [true, "Both parameters are unitless."];
  if ((!norm1 && norm2) || (norm1 && !norm2)) {
    return [false, `Asymmetric unit specification: '${u1}' vs '${u2}'. Missing unit bypass rejected.`];
  }

  const dim1 = DIMENSIONS[norm1!];
  const dim2 = DIMENSIONS[norm2!];

  if (!dim1 && !dim2) {
    return [false, `Both units '${u1}' and '${u2}' are unknown to UnitRegistry.`];
  }
  if (!dim1) return [false, `Unit '${u1}' is not recognized in UnitRegistry.`];
  if (!dim2) return [false, `Unit '${u2}' is not recognized in UnitRegistry.`];

  if (dim1 !== dim2) {
    return [false, `Dimensional incompatibility: '${u1}' (${dim1}) cannot be reconciled with '${u2}' (${dim2}).`];
  }

  return [true, `Units '${u1}' and '${u2}' are dimensionally compatible (${dim1}).`];
}

function convertUnit(val: number, fromUnit: string, toUnit: string): number {
  const u1 = normalizeUnit(fromUnit);
  const u2 = normalizeUnit(toUnit);
  if (!u1 || !CONVERSIONS_TO_BASE[u1]) throw new Error(`Unknown unit: ${fromUnit}`);
  if (!u2 || !CONVERSIONS_TO_BASE[u2]) throw new Error(`Unknown unit: ${toUnit}`);
  if (DIMENSIONS[u1] !== DIMENSIONS[u2]) throw new Error(`Incompatible dimensions: ${fromUnit} -> ${toUnit}`);
  if (u1 === u2) return val;

  const [m1, off1] = CONVERSIONS_TO_BASE[u1];
  const base = val * m1 + off1;
  const [m2, off2] = CONVERSIONS_TO_BASE[u2];
  return (base - off2) / m2;
}

export function evaluateTriad(
  s: SourcePrimitive,
  c: ConstraintPrimitive,
  d: DissipatePrimitive,
  initialState: SystemState,
  registry: Record<string, EvidenceRecord> | null,
  evaluationTime: number
): EvaluationReport {
  const diagnostics: CoherenceDiagnostic[] = [];
  let evVerdict: CoherenceVerdict = "PASS";
  let scVerdict: CoherenceVerdict = "PASS";
  let stVerdict: CoherenceVerdict = "PASS";

  // --- 1. Evidence Grounding ---
  if (isNaN(s.timestamp_sec) || !isFinite(s.timestamp_sec)) {
    diagnostics.push({
      code: "STATE_INVALID_NUMERIC",
      severity: "ERROR",
      message: `Source timestamp is non-finite: ${s.timestamp_sec}`,
      primitive: "SOURCE",
      field_name: "timestamp_sec",
    });
    evVerdict = "FAIL";
  } else if (s.max_age_sec <= 0 || isNaN(s.max_age_sec) || !isFinite(s.max_age_sec)) {
    diagnostics.push({
      code: "TEMPORAL_INVALID_LIMIT",
      severity: "ERROR",
      message: `Source max_age_sec must be positive and finite: ${s.max_age_sec}`,
      primitive: "SOURCE",
      field_name: "max_age_sec",
    });
    evVerdict = "FAIL";
  } else if (s.timestamp_sec > evaluationTime) {
    diagnostics.push({
      code: "TEMPORAL_FUTURE",
      severity: "ERROR",
      message: `Source timestamp is in the future (${s.timestamp_sec.toFixed(2)} > current ${evaluationTime.toFixed(2)})`,
      primitive: "SOURCE",
      field_name: "timestamp_sec",
    });
    evVerdict = "FAIL";
  } else {
    const age = evaluationTime - s.timestamp_sec;
    if (age > s.max_age_sec) {
      diagnostics.push({
        code: "TEMPORAL_STALE",
        severity: "WARNING",
        message: `Evidence is stale: age ${age.toFixed(2)}s exceeds max_age_sec (${s.max_age_sec.toFixed(2)}s)`,
        primitive: "SOURCE",
        field_name: "timestamp_sec",
      });
      evVerdict = "REVIEW";
    }
  }

  if (evVerdict !== "FAIL") {
    if (!registry) {
      diagnostics.push({
        code: "REGISTRY_OFFLINE",
        severity: "WARNING",
        message: "Evidence registry is offline; cannot verify claim.",
        primitive: "SOURCE",
        field_name: "epistemic_type",
      });
      evVerdict = "REVIEW";
    } else {
      const record = registry[s.evidence_id];
      if (!record) {
        diagnostics.push({
          code: "EVIDENCE_NOT_FOUND",
          severity: "ERROR",
          message: `Primary evidence ID '${s.evidence_id}' not found in registry.`,
          primitive: "SOURCE",
          field_name: "evidence_id",
        });
        evVerdict = "FAIL";
      } else {
        if (record.timestamp_sec > evaluationTime) {
          diagnostics.push({
            code: "TEMPORAL_FUTURE",
            severity: "ERROR",
            message: `Registry record '${record.evidence_id}' has future timestamp.`,
            primitive: "SOURCE",
            field_name: "evidence_id",
          });
          evVerdict = "FAIL";
        }
        if (s.epistemic_type === "FACT" && record.epistemic_status !== "FACT") {
          diagnostics.push({
            code: "EVIDENCE_MISMATCH",
            severity: "ERROR",
            message: `Claimed FACT, but registry records status as ${record.epistemic_status}.`,
            primitive: "SOURCE",
            field_name: "epistemic_type",
          });
          evVerdict = "FAIL";
        }
        if (s.authority_domain && !s.authority_domain.includes(record.domain)) {
          diagnostics.push({
            code: "EVIDENCE_DOMAIN_MISMATCH",
            severity: "ERROR",
            message: `Evidence domain '${record.domain}' is not within claimed authority [${s.authority_domain.join(", ")}].`,
            primitive: "SOURCE",
            field_name: "authority_domain",
          });
          evVerdict = "FAIL";
        }
        // 6. Explicit Cryptographic Payload Hash Verification
        if (s.payload_hash !== undefined && s.payload_hash !== null && !record.payload_hash) {
          diagnostics.push({
            code: "EVIDENCE_HASH_MISSING_IN_REGISTRY",
            severity: "ERROR",
            message: `Source supplied payload_hash '${s.payload_hash}', but registry record '${s.evidence_id}' lacks a payload_hash for verification.`,
            primitive: "SOURCE",
            field_name: "payload_hash",
          });
          evVerdict = "FAIL";
        } else if (record.payload_hash && !s.payload_hash) {
          diagnostics.push({
            code: "EVIDENCE_HASH_REQUIRED_BY_REGISTRY",
            severity: "ERROR",
            message: `Registry record '${s.evidence_id}' requires payload_hash verification, but Source omitted payload_hash.`,
            primitive: "SOURCE",
            field_name: "payload_hash",
          });
          evVerdict = "FAIL";
        } else if (s.payload_hash && record.payload_hash && s.payload_hash !== record.payload_hash) {
          diagnostics.push({
            code: "EVIDENCE_PAYLOAD_MISMATCH",
            severity: "ERROR",
            message: `Payload hash mismatch for evidence '${s.evidence_id}': '${s.payload_hash}' != '${record.payload_hash}'.`,
            primitive: "SOURCE",
            field_name: "payload_hash",
          });
          evVerdict = "FAIL";
        }

        // 7. INFERENCE Corroboration & Premise Verification
        if (s.epistemic_type === "INFERENCE") {
          const corrob = s.corroborating_evidence_ids || [];
          if (corrob.length === 0) {
            diagnostics.push({
              code: "INFERENCE_UNSUPPORTED",
              severity: "WARNING",
              message: "Claimed INFERENCE lacks corroborating evidence IDs; requires epistemic review.",
              primitive: "SOURCE",
              field_name: "corroborating_evidence_ids",
            });
            if (evVerdict !== "FAIL") evVerdict = "REVIEW";
          } else if (corrob.includes(s.evidence_id)) {
            diagnostics.push({
              code: "INFERENCE_CIRCULAR_DEPENDENCY",
              severity: "ERROR",
              message: `Circular inference dependency: evidence '${s.evidence_id}' cites itself as a corroborating premise.`,
              primitive: "SOURCE",
              field_name: "corroborating_evidence_ids",
            });
            evVerdict = "FAIL";
          } else {
            for (const cid of corrob) {
              const crec = registry[cid];
              if (!crec) {
                diagnostics.push({
                  code: "EVIDENCE_NOT_FOUND",
                  severity: "ERROR",
                  message: `Corroborating evidence ID '${cid}' not found in registry.`,
                  primitive: "SOURCE",
                  field_name: "corroborating_evidence_ids",
                });
                evVerdict = "FAIL";
              } else {
                if (s.authority_domain && !s.authority_domain.includes(crec.domain)) {
                  diagnostics.push({
                    code: "EVIDENCE_DOMAIN_MISMATCH",
                    severity: "ERROR",
                    message: `Corroborating evidence '${cid}' domain '${crec.domain}' not in authority domain.`,
                    primitive: "SOURCE",
                    field_name: "corroborating_evidence_ids",
                  });
                  evVerdict = "FAIL";
                }
                if (crec.epistemic_status !== "FACT" && crec.epistemic_status !== "INFERENCE") {
                  diagnostics.push({
                    code: "INFERENCE_PREMISE_INVALID_STATUS",
                    severity: "ERROR",
                    message: `Corroborating premise '${cid}' has invalid epistemic status '${crec.epistemic_status}'; must be FACT or verified INFERENCE.`,
                    primitive: "SOURCE",
                    field_name: "corroborating_evidence_ids",
                  });
                  evVerdict = "FAIL";
                }
                if (crec.timestamp_sec > evaluationTime) {
                  diagnostics.push({
                    code: "TEMPORAL_FUTURE",
                    severity: "ERROR",
                    message: `Corroborating evidence '${cid}' has future timestamp (${crec.timestamp_sec} > ${evaluationTime}).`,
                    primitive: "SOURCE",
                    field_name: "corroborating_evidence_ids",
                  });
                  evVerdict = "FAIL";
                }
                const corrobAge = evaluationTime - crec.timestamp_sec;
                if (corrobAge > s.max_age_sec) {
                  diagnostics.push({
                    code: "TEMPORAL_STALE",
                    severity: "WARNING",
                    message: `Corroborating evidence '${cid}' is stale: age ${corrobAge.toFixed(2)}s exceeds max_age_sec (${s.max_age_sec.toFixed(2)}s).`,
                    primitive: "SOURCE",
                    field_name: "corroborating_evidence_ids",
                  });
                  if (evVerdict !== "FAIL") evVerdict = "REVIEW";
                }
              }
            }
          }
        }
      }
    }
  }

  if (evVerdict === "PASS") {
    diagnostics.push({
      code: "EVIDENCE_PASS",
      severity: "INFO",
      message: "Evidence verified against authoritative registry.",
      primitive: "SOURCE",
    });
  }

  // --- 2. Scope & Authority ---
  let hasDefect = false;
  if (s.authority_domain === null) {
    diagnostics.push({
      code: "SCOPE_DEFECT_NONE",
      severity: "ERROR",
      message: "Source authority_domain is None (structural defect).",
      primitive: "SOURCE",
      field_name: "authority_domain",
    });
    hasDefect = true;
  }
  if (s.granted_scope === null) {
    diagnostics.push({
      code: "SCOPE_DEFECT_NONE",
      severity: "ERROR",
      message: "Source granted_scope is None (structural defect).",
      primitive: "SOURCE",
      field_name: "granted_scope",
    });
    hasDefect = true;
  }
  if (s.granted_loss_domains === null) {
    diagnostics.push({
      code: "SCOPE_DEFECT_NONE",
      severity: "ERROR",
      message: "Source granted_loss_domains is None (structural defect).",
      primitive: "SOURCE",
      field_name: "granted_loss_domains",
    });
    hasDefect = true;
  }

  if (hasDefect) {
    scVerdict = "FAIL";
  } else {
    const authSet = new Set(s.authority_domain || []);
    const scopeSet = new Set(s.granted_scope || []);
    const lossSet = new Set(s.granted_loss_domains || []);

    const unauthDomains = c.domain_scope.filter((dom) => !authSet.has(dom));
    if (unauthDomains.length > 0) {
      diagnostics.push({
        code: "SCOPE_EXCEEDED_DOMAIN",
        severity: "ERROR",
        message: `Constraint domain scope exceeds authority: unauthorized [${unauthDomains.join(", ")}].`,
        primitive: "CONSTRAINT",
        field_name: "domain_scope",
      });
      scVerdict = "FAIL";
    }

    const unauthObjects = c.target_objects.filter((obj) => !scopeSet.has(obj));
    if (unauthObjects.length > 0) {
      diagnostics.push({
        code: "SCOPE_EXCEEDED_OBJECTS",
        severity: "ERROR",
        message: `Constraint target objects exceed granted scope: unauthorized [${unauthObjects.join(", ")}].`,
        primitive: "CONSTRAINT",
        field_name: "target_objects",
      });
      scVerdict = "FAIL";
    }

    const unauthLoss = d.loss_domain.filter((ld) => !lossSet.has(ld));
    if (unauthLoss.length > 0) {
      diagnostics.push({
        code: "SCOPE_EXCEEDED_LOSS",
        severity: "ERROR",
        message: `Dissipate loss domain exceeds granted loss domains: unauthorized [${unauthLoss.join(", ")}].`,
        primitive: "DISSIPATE",
        field_name: "loss_domain",
      });
      scVerdict = "FAIL";
    }

    if (scVerdict === "PASS") {
      diagnostics.push({
        code: "SCOPE_PASS",
        severity: "INFO",
        message: "Scope and authority checks satisfied.",
        primitive: "SOURCE",
      });
    }
  }

  // --- 3. State & Invariants Simulation ---
  const simulatedValues: Record<string, number> = { ...initialState.current_values };
  const simulatedFlags: Record<string, boolean> = { ...initialState.active_flags };

  // Numeric checks
  const checkNumeric = (dictName: string, dict?: Record<string, number>) => {
    if (!dict) return;
    for (const [k, v] of Object.entries(dict)) {
      if (isNaN(v) || !isFinite(v)) {
        diagnostics.push({
          code: "STATE_INVALID_NUMERIC",
          severity: "ERROR",
          message: `Non-finite numeric value (${v}) in '${dictName}' for key '${k}'.`,
          primitive: dictName.includes("dissipate") ? "DISSIPATE" : "CONSTRAINT",
          field_name: k,
        });
        stVerdict = "FAIL";
      }
    }
  };

  checkNumeric("initial_state.current_values", initialState.current_values);
  checkNumeric("dissipate.state_delta", d.state_delta);
  checkNumeric("dissipate.resource_cost", d.resource_cost);
  checkNumeric("constraint.min_bounds", c.min_bounds);
  checkNumeric("constraint.max_bounds", c.max_bounds);
  checkNumeric("constraint.protected_values", c.protected_values);

  // Non-negative resource costs
  if (d.resource_cost) {
    for (const [r, cost] of Object.entries(d.resource_cost)) {
      if (cost < 0.0) {
        diagnostics.push({
          code: "STATE_NEGATIVE_RESOURCE_COST",
          severity: "ERROR",
          message: `Negative resource cost (${cost}) for '${r}' is forbidden.`,
          primitive: "DISSIPATE",
          field_name: r,
        });
        stVerdict = "FAIL";
      }
    }
  }

  // Mutation vectors vs protected set
  const allModifiedParams = new Set<string>([
    ...d.target_states,
    ...d.side_effects,
    ...Object.keys(d.state_delta || {}),
    ...Object.keys(d.resource_cost || {}),
    ...Object.keys(d.flag_delta || {}),
  ]);

  const protSet = new Set(c.protected_set || []);
  const protViolations = [...allModifiedParams].filter((p) => protSet.has(p));
  if (protViolations.length > 0) {
    diagnostics.push({
      code: "STATE_PROTECTED_PARAM_MUTATED",
      severity: "ERROR",
      message: `Dissipation mutates protected parameters: [${protViolations.join(", ")}].`,
      primitive: "DISSIPATE",
      field_name: "protected_set",
    });
    stVerdict = "FAIL";
  }

  // Unit compatibility
  for (const p of allModifiedParams) {
    const dUnit = d.units?.[p];
    const cUnit = c.units?.[p];
    const sUnit = initialState.units?.[p];

    if (dUnit || cUnit) {
      const [compDC, msgDC] = areUnitsCompatible(dUnit, cUnit);
      if (!compDC) {
        diagnostics.push({
          code: "UNIT_INCOMPATIBLE",
          severity: "ERROR",
          message: `Unit mismatch for param '${p}' between Dissipate ('${dUnit}') and Constraint ('${cUnit}'): ${msgDC}`,
          primitive: "DISSIPATE",
          field_name: p,
        });
        stVerdict = "FAIL";
      }
    }

    if (dUnit || sUnit) {
      const [compDS, msgDS] = areUnitsCompatible(dUnit, sUnit);
      if (!compDS) {
        diagnostics.push({
          code: "UNIT_INCOMPATIBLE",
          severity: "ERROR",
          message: `Unit mismatch for param '${p}' between Dissipate ('${dUnit}') and SystemState ('${sUnit}'): ${msgDS}`,
          primitive: "DISSIPATE",
          field_name: p,
        });
        stVerdict = "FAIL";
      }
    }
  }

  // Apply State Deltas & Resource Costs
  if (stVerdict !== "FAIL") {
    if (d.state_delta) {
      for (const [varName, rawDelta] of Object.entries(d.state_delta)) {
        const baseUnit = initialState.units?.[varName];
        const deltaUnit = d.units?.[varName];
        let effDelta = rawDelta;
        if (deltaUnit && baseUnit && deltaUnit.toLowerCase() !== baseUnit.toLowerCase()) {
          try {
            effDelta = convertUnit(rawDelta, deltaUnit, baseUnit);
          } catch (e) {
            diagnostics.push({
              code: "UNIT_CONVERSION_FAILED",
              severity: "ERROR",
              message: `Failed converting delta for '${varName}': ${(e as Error).message}`,
              primitive: "DISSIPATE",
              field_name: varName,
            });
            stVerdict = "FAIL";
          }
        }
        simulatedValues[varName] = (simulatedValues[varName] ?? 0.0) + effDelta;
      }
    }

    if (d.resource_cost) {
      for (const [varName, rawCost] of Object.entries(d.resource_cost)) {
        const baseUnit = initialState.units?.[varName];
        const costUnit = d.units?.[varName];
        let effCost = rawCost;
        if (costUnit && baseUnit && costUnit.toLowerCase() !== baseUnit.toLowerCase()) {
          try {
            effCost = convertUnit(rawCost, costUnit, baseUnit);
          } catch (e) {
            diagnostics.push({
              code: "UNIT_CONVERSION_FAILED",
              severity: "ERROR",
              message: `Failed converting resource cost for '${varName}': ${(e as Error).message}`,
              primitive: "DISSIPATE",
              field_name: varName,
            });
            stVerdict = "FAIL";
          }
        }
        simulatedValues[varName] = (simulatedValues[varName] ?? 0.0) - effCost;
      }
    }

    // Apply Flag Deltas & Protected Flags
    if (d.flag_delta) {
      const protectedFlags = new Set(c.protected_flags || []);
      for (const [flagName, newVal] of Object.entries(d.flag_delta)) {
        if (protectedFlags.has(flagName)) {
          const initVal = initialState.active_flags?.[flagName] ?? false;
          if (initVal !== newVal) {
            diagnostics.push({
              code: "STATE_PROTECTED_FLAG_MUTATED",
              severity: "ERROR",
              message: `Flag '${flagName}' is protected and cannot be mutated from ${initVal} to ${newVal}.`,
              primitive: "CONSTRAINT",
              field_name: flagName,
            });
            stVerdict = "FAIL";
          }
        }
        simulatedFlags[flagName] = newVal;
      }
    }

    // Missing required variables
    const requiredVars = new Set<string>([
      ...Object.keys(c.min_bounds || {}),
      ...Object.keys(c.max_bounds || {}),
      ...Object.keys(c.protected_values || {}),
    ]);
    const missingVars = [...requiredVars].filter((v) => !(v in simulatedValues));
    if (missingVars.length > 0) {
      diagnostics.push({
        code: "STATE_MISSING_VAR",
        severity: "ERROR",
        message: `Missing required state variables in terminal simulation: [${missingVars.join(", ")}].`,
        primitive: "CONSTRAINT",
        field_name: "required_variables",
      });
      stVerdict = "FAIL";
    }

    // Forbidden / Required Flags
    if (c.forbidden_flags) {
      for (const [fName, fVal] of Object.entries(c.forbidden_flags)) {
        if ((simulatedFlags[fName] ?? false) === fVal) {
          diagnostics.push({
            code: "STATE_FORBIDDEN_FLAG_ACTIVE",
            severity: "ERROR",
            message: `Terminal state flag '${fName}' holds forbidden value (${fVal}).`,
            primitive: "CONSTRAINT",
            field_name: fName,
          });
          stVerdict = "FAIL";
        }
      }
    }
    if (c.required_flags) {
      for (const [fName, rVal] of Object.entries(c.required_flags)) {
        if ((simulatedFlags[fName] ?? false) !== rVal) {
          diagnostics.push({
            code: "STATE_REQUIRED_FLAG_MISSING",
            severity: "ERROR",
            message: `Terminal state flag '${fName}' is ${simulatedFlags[fName]}, but required to be ${rVal}.`,
            primitive: "CONSTRAINT",
            field_name: fName,
          });
          stVerdict = "FAIL";
        }
      }
    }

    // Protected Values
    if (c.protected_values) {
      for (const [vName, expectedVal] of Object.entries(c.protected_values)) {
        const simVal = simulatedValues[vName];
        let effExpected = expectedVal;
        const cU = c.units?.[vName];
        const sU = initialState.units?.[vName];
        if (cU && sU && cU.toLowerCase() !== sU.toLowerCase()) {
          try {
            effExpected = convertUnit(expectedVal, cU, sU);
          } catch (e) {
            diagnostics.push({
              code: "UNIT_CONVERSION_FAILED",
              severity: "ERROR",
              message: `Failed converting protected value: ${(e as Error).message}`,
              primitive: "CONSTRAINT",
              field_name: vName,
            });
            stVerdict = "FAIL";
          }
        }
        if (Math.abs(simVal - effExpected) > 1e-9) {
          diagnostics.push({
            code: "STATE_PROTECTED_VALUE_VIOLATED",
            severity: "ERROR",
            message: `Protected value for '${vName}' violated: simulated ${simVal.toFixed(4)} != expected ${effExpected.toFixed(4)}.`,
            primitive: "CONSTRAINT",
            field_name: vName,
          });
          stVerdict = "FAIL";
        }
      }
    }

    // Bounds Checks
    if (c.min_bounds) {
      for (const [vName, minB] of Object.entries(c.min_bounds)) {
        const simVal = simulatedValues[vName];
        let effMin = minB;
        const cU = c.units?.[vName];
        const sU = initialState.units?.[vName];
        if (cU && sU && cU.toLowerCase() !== sU.toLowerCase()) {
          try {
            effMin = convertUnit(minB, cU, sU);
          } catch {}
        }
        if (simVal < effMin) {
          diagnostics.push({
            code: "STATE_MIN_BOUND_BREACH",
            severity: "ERROR",
            message: `Variable '${vName}' (${simVal.toFixed(4)}) falls below min_bound (${effMin.toFixed(4)}).`,
            primitive: "CONSTRAINT",
            field_name: vName,
          });
          stVerdict = "FAIL";
        }
      }
    }
    if (c.max_bounds) {
      for (const [vName, maxB] of Object.entries(c.max_bounds)) {
        const simVal = simulatedValues[vName];
        let effMax = maxB;
        const cU = c.units?.[vName];
        const sU = initialState.units?.[vName];
        if (cU && sU && cU.toLowerCase() !== sU.toLowerCase()) {
          try {
            effMax = convertUnit(maxB, cU, sU);
          } catch {}
        }
        if (simVal > effMax) {
          diagnostics.push({
            code: "STATE_MAX_BOUND_BREACH",
            severity: "ERROR",
            message: `Variable '${vName}' (${simVal.toFixed(4)}) exceeds max_bound (${effMax.toFixed(4)}).`,
            primitive: "CONSTRAINT",
            field_name: vName,
          });
          stVerdict = "FAIL";
        }
      }
    }
  }

  if (stVerdict === "PASS") {
    diagnostics.push({
      code: "STATE_PASS",
      severity: "INFO",
      message: "State simulation and invariant checks satisfied.",
      primitive: "STATE",
    });
  }

  // --- Pairwise Synthesis ---
  const pScFail = evVerdict === "FAIL" || diagnostics.some((d) => d.code.includes("SCOPE_EXCEEDED_DOMAIN") || d.code.includes("SCOPE_EXCEEDED_OBJECTS") || d.code.includes("SCOPE_DEFECT"));
  const pScReview = evVerdict === "REVIEW";
  const pScVerdict: CoherenceVerdict = pScFail ? "FAIL" : pScReview ? "REVIEW" : "PASS";

  const pSdFail = diagnostics.some((d) => d.code.includes("SCOPE_EXCEEDED_LOSS") || d.code.includes("SCOPE_DEFECT"));
  const pSdVerdict: CoherenceVerdict = pSdFail ? "FAIL" : "PASS";

  const pCdVerdict = stVerdict;

  // Final Verdict
  const verdicts = [evVerdict, scVerdict, stVerdict];
  let finalVerdict: CoherenceVerdict = "PASS";
  if (verdicts.includes("FAIL")) {
    finalVerdict = "FAIL";
  } else if (verdicts.includes("REVIEW")) {
    finalVerdict = "REVIEW";
  }

  return {
    verdict: finalVerdict,
    engine_version: "0.4.0",
    timestamp_sec: evaluationTime,
    pairwise_checks: {
      P_SC: {
        relationship: "P_SC: SOURCE <-> CONSTRAINT (Grounding & Authority)",
        is_valid: pScVerdict === "PASS",
        verdict: pScVerdict,
        diagnostics: diagnostics.filter((d) => d.primitive === "SOURCE" || d.primitive === "CONSTRAINT"),
      },
      P_CD: {
        relationship: "P_CD: CONSTRAINT <-> DISSIPATE (State Invariant Integrity)",
        is_valid: pCdVerdict === "PASS",
        verdict: pCdVerdict,
        diagnostics: diagnostics.filter((d) => d.primitive === "STATE" || d.primitive === "DISSIPATE"),
      },
      P_SD: {
        relationship: "P_SD: SOURCE <-> DISSIPATE (Loss Domain Authority)",
        is_valid: pSdVerdict === "PASS",
        verdict: pSdVerdict,
        diagnostics: diagnostics.filter((d) => d.code === "SCOPE_EXCEEDED_LOSS"),
      },
    },
    diagnostics,
    simulated_values: simulatedValues,
    simulated_flags: simulatedFlags,
    messages: diagnostics.map((d) => `[${d.code}] ${d.message}`),
  };
}
