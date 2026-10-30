"""
Unit tests for ScopeValidator.
"""

from sol_triad.models import (
    SourcePrimitive,
    ConstraintPrimitive,
    DissipatePrimitive,
    EpistemicStatus,
    CoherenceVerdict,
    DiagnosticCode,
)
from sol_triad.validators import ScopeValidator


def test_valid_scope_passes():
    s = SourcePrimitive(
        evidence_id="ev-1",
        authority_domain={"physics", "thermal"},
        granted_scope={"valve_1", "heater_2"},
        granted_loss_domains={"heat_sink"},
        epistemic_type=EpistemicStatus.FACT,
        timestamp_sec=100.0,
    )
    c = ConstraintPrimitive(
        domain_scope={"physics"},
        target_objects={"valve_1"},
        protected_set=set(),
    )
    d = DissipatePrimitive(
        loss_domain={"heat_sink"},
        target_states=set(),
        side_effects=set(),
    )

    validator = ScopeValidator()
    is_valid, verdict, diags = validator.validate(s, c, d)

    assert is_valid is True
    assert verdict == CoherenceVerdict.PASS
    assert any(d.code == DiagnosticCode.SCOPE_PASS for d in diags)


def test_structural_defect_none_fails():
    # None represents missing mandatory field (defect)
    s = SourcePrimitive(
        evidence_id="ev-1",
        authority_domain=None,
        granted_scope={"valve_1"},
        granted_loss_domains={"heat_sink"},
        epistemic_type=EpistemicStatus.FACT,
        timestamp_sec=100.0,
    )
    c = ConstraintPrimitive(
        domain_scope={"physics"},
        target_objects={"valve_1"},
        protected_set=set(),
    )
    d = DissipatePrimitive(
        loss_domain={"heat_sink"},
        target_states=set(),
        side_effects=set(),
    )

    validator = ScopeValidator()
    is_valid, verdict, diags = validator.validate(s, c, d)

    assert is_valid is False
    assert verdict == CoherenceVerdict.FAIL
    assert any(d.code == DiagnosticCode.SCOPE_DEFECT_NONE for d in diags)


def test_empty_set_zero_privileges_rejects_non_empty_request():
    # set() represents zero privileges explicitly granted
    s = SourcePrimitive(
        evidence_id="ev-1",
        authority_domain=set(),  # Zero privileges!
        granted_scope=set(),
        granted_loss_domains=set(),
        epistemic_type=EpistemicStatus.FACT,
        timestamp_sec=100.0,
    )
    c = ConstraintPrimitive(
        domain_scope={"physics"},
        target_objects={"valve_1"},
        protected_set=set(),
    )
    d = DissipatePrimitive(
        loss_domain={"heat_sink"},
        target_states=set(),
        side_effects=set(),
    )

    validator = ScopeValidator()
    is_valid, verdict, diags = validator.validate(s, c, d)

    assert is_valid is False
    assert verdict == CoherenceVerdict.FAIL
    codes = {d.code for d in diags}
    assert DiagnosticCode.SCOPE_EXCEEDED_DOMAIN in codes
    assert DiagnosticCode.SCOPE_EXCEEDED_OBJECTS in codes
    assert DiagnosticCode.SCOPE_EXCEEDED_LOSS in codes


def test_unauthorized_loss_domain_fails():
    s = SourcePrimitive(
        evidence_id="ev-1",
        authority_domain={"physics"},
        granted_scope={"valve_1"},
        granted_loss_domains={"safe_cooling"},
        epistemic_type=EpistemicStatus.FACT,
        timestamp_sec=100.0,
    )
    c = ConstraintPrimitive(
        domain_scope={"physics"},
        target_objects={"valve_1"},
        protected_set=set(),
    )
    d = DissipatePrimitive(
        loss_domain={"destructive_venting"},  # unauthorized!
        target_states=set(),
        side_effects=set(),
    )

    validator = ScopeValidator()
    is_valid, verdict, diags = validator.validate(s, c, d)

    assert is_valid is False
    assert verdict == CoherenceVerdict.FAIL
    assert any(d.code == DiagnosticCode.SCOPE_EXCEEDED_LOSS for d in diags)
