# SOL-Triad Engine (Experimental)

**System Signature:** `AAM-V2_ARTSYBASHEV_UA_KHARKIV_AIANALYSIS`
**Version:** 0.3.0 (Experimental Prototype)

## Overview
The **SOL-Triad Engine** is an independent, experimental verification kernel designed to sit atop the SOL-1 Core. Its purpose is to perform deterministic structural and epistemic coherence checks across the three canonical SOL primitives: **SOURCE**, **CONSTRAINT**, and **DISSIPATE**.

Rather than trusting LLM self-declarations, this engine applies strict Boolean propositional logic, set theory, and dimensionality checks to ensure that intended actions have the invariant right to mutate system state.

## Architecture
The engine is decoupled into specific validation domains:
1. **Data Model (`models.py`):** Canonical dataclasses for $S$, $C$, $D$, and Evidence Records.
2. **Evidence Validator:** Enforces temporal freshness, epistemic status, and domain applicability against an external `EvidenceRegistry`.
3. **Scope & Authority Validator:** Differentiates between structural defects (missing fields) and zero-privilege states (empty sets).
4. **State & Invariant Validator:** Consolidates all mutation vectors (deltas, resource costs) and simulates terminal states utilizing a dimensional `UnitRegistry`.
5. **Triad Coherence Engine (`engine.py`):** Adjudicates the final verdict (`ALLOW`, `REVIEW`, `BLOCK`) across the validators.