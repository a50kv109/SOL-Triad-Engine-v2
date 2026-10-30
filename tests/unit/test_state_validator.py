"""
Unit tests for StateValidator (State & Invariant simulation).
"""

from sol_triad.models import (
    ConstraintPrimitive,
    DissipatePrimitive,
    SystemState,
    CoherenceVerdict,
    DiagnosticCode,
)
from sol_triad.validators import StateValidator


def test_valid_state_simulation_passes():
    c = ConstraintPrimitive(
        domain_scope={"hydraulics"},
        target_objects={"valve_1"},
        protected_set={"security_pin"},
        min_bounds={"pressure": 2.0},
        max_bounds={"pressure": 8.0},
        protected_values={"chamber_id": 42.0},
        units={"pressure": "bar"},
    )
    d = DissipatePrimitive(
        loss_domain={"vent"},
        target_states={"coolant_ready"},
        side_effects=set(),
        state_delta={"pressure": 1.5},
        resource_cost={"fuel": 0.5},
        units={"pressure": "bar"},
    )
    state = SystemState(
        current_values={"pressure": 3.0, "chamber_id": 42.0, "fuel": 10.0},
        active_flags={"engine_on": True},
        units={"pressure": "bar"},
    )

    validator = StateValidator()
    is_valid, verdict, diags, sim_val, sim_flags = validator.validate(c, d, state)

    assert is_valid is True
    assert verdict == CoherenceVerdict.PASS
    assert sim_val["pressure"] == 4.5  # 3.0 + 1.5
    assert sim_val["fuel"] == 9.5      # 10.0 - 0.5


def test_temperature_state_delta_uses_difference_conversion():
    c = ConstraintPrimitive(
        domain_scope={"thermal"},
        target_objects={"heater"},
        protected_set=set(),
        units={"temperature": "celsius"},
        min_bounds={"temperature": 0.0},
        max_bounds={"temperature": 100.0},
    )
    d = DissipatePrimitive(
        loss_domain={"thermal"},
        target_states={"warmed"},
        side_effects=set(),
        state_delta={"temperature": 1.0},
        units={"temperature": "kelvin"},
    )
    state = SystemState(
        current_values={"temperature": 20.0},
        units={"temperature": "celsius"},
    )

    is_valid, verdict, _, simulated_values, _ = StateValidator().validate(c, d, state)

    assert is_valid is True
    assert verdict == CoherenceVerdict.PASS
    assert simulated_values["temperature"] == 21.0


def test_fahrenheit_temperature_state_delta_uses_difference_conversion():
    c = ConstraintPrimitive(
        domain_scope={"thermal"},
        target_objects={"heater"},
        protected_set=set(),
        units={"temperature": "celsius"},
    )
    d = DissipatePrimitive(
        loss_domain={"thermal"},
        target_states={"warmed"},
        side_effects=set(),
        state_delta={"temperature": 1.0},
        units={"temperature": "fahrenheit"},
    )
    state = SystemState(
        current_values={"temperature": 20.0},
        units={"temperature": "celsius"},
    )

    is_valid, verdict, _, simulated_values, _ = StateValidator().validate(c, d, state)

    assert is_valid is True
    assert verdict == CoherenceVerdict.PASS
    assert abs(simulated_values["temperature"] - (20.0 + 5.0 / 9.0)) < 1e-12


def test_temperature_resource_cost_is_subtracted_as_a_difference():
    c = ConstraintPrimitive(
        domain_scope={"thermal"},
        target_objects={"cooler"},
        protected_set=set(),
        units={"temperature": "celsius"},
        min_bounds={"temperature": 0.0},
        max_bounds={"temperature": 100.0},
    )
    d = DissipatePrimitive(
        loss_domain={"thermal"},
        target_states={"cooled"},
        side_effects=set(),
        resource_cost={"temperature": 1.0},
        units={"temperature": "kelvin"},
    )
    state = SystemState(
        current_values={"temperature": 22.0},
        units={"temperature": "celsius"},
    )

    is_valid, verdict, _, simulated_values, _ = StateValidator().validate(c, d, state)

    assert is_valid is True
    assert verdict == CoherenceVerdict.PASS
    assert simulated_values["temperature"] == 21.0


def test_linear_resource_cost_keeps_existing_unit_conversion():
    c = ConstraintPrimitive(
        domain_scope={"energy"},
        target_objects={"battery"},
        protected_set=set(),
        units={"capacity": "kWh"},
    )
    d = DissipatePrimitive(
        loss_domain={"energy"},
        target_states={"discharged"},
        side_effects=set(),
        resource_cost={"capacity": 1000.0},
        units={"capacity": "kJ"},
    )
    state = SystemState(
        current_values={"capacity": 2.0},
        units={"capacity": "kWh"},
    )

    is_valid, verdict, _, simulated_values, _ = StateValidator().validate(c, d, state)

    assert is_valid is True
    assert verdict == CoherenceVerdict.PASS
    assert abs(simulated_values["capacity"] - (2.0 - 1000.0 / 3600.0)) < 1e-12


def test_temperature_bounds_remain_absolute_values():
    c = ConstraintPrimitive(
        domain_scope={"thermal"},
        target_objects={"sensor"},
        protected_set=set(),
        min_bounds={"temperature": 293.15},
        max_bounds={"temperature": 294.15},
        units={"temperature": "kelvin"},
    )
    d = DissipatePrimitive(
        loss_domain={"thermal"},
        target_states=set(),
        side_effects=set(),
        state_delta={"temperature": 0.0},
        units={"temperature": "celsius"},
    )
    state = SystemState(
        current_values={"temperature": 20.0},
        units={"temperature": "celsius"},
    )

    is_valid, verdict, _, simulated_values, _ = StateValidator().validate(c, d, state)

    assert is_valid is True
    assert verdict == CoherenceVerdict.PASS
    assert simulated_values["temperature"] == 20.0


def test_mutation_of_protected_set_fails():
    c = ConstraintPrimitive(
        domain_scope={"core"},
        target_objects={"core_node"},
        protected_set={"safety_lock"},
    )
    d = DissipatePrimitive(
        loss_domain={"vent"},
        target_states=set(),
        side_effects={"safety_lock"},  # mutates protected set!
    )
    state = SystemState()

    validator = StateValidator()
    is_valid, verdict, diags, _, _ = validator.validate(c, d, state)

    assert is_valid is False
    assert verdict == CoherenceVerdict.FAIL
    assert any(d.code == DiagnosticCode.STATE_PROTECTED_PARAM_MUTATED for d in diags)


def test_protected_value_violation_fails():
    c = ConstraintPrimitive(
        domain_scope={"core"},
        target_objects={"core_node"},
        protected_set=set(),
        protected_values={"encryption_seed": 12345.0},
    )
    d = DissipatePrimitive(
        loss_domain={"vent"},
        target_states=set(),
        side_effects=set(),
        state_delta={"encryption_seed": 1.0},  # mutates protected value!
    )
    state = SystemState(
        current_values={"encryption_seed": 12345.0}
    )

    validator = StateValidator()
    is_valid, verdict, diags, _, _ = validator.validate(c, d, state)

    assert is_valid is False
    assert verdict == CoherenceVerdict.FAIL
    assert any(d.code == DiagnosticCode.STATE_PROTECTED_VALUE_VIOLATED for d in diags)


def test_min_bound_breach_fails():
    c = ConstraintPrimitive(
        domain_scope={"coolant"},
        target_objects={"pump"},
        protected_set=set(),
        min_bounds={"coolant_level": 10.0},
    )
    d = DissipatePrimitive(
        loss_domain={"vent"},
        target_states=set(),
        side_effects=set(),
        resource_cost={"coolant_level": 5.0},
    )
    state = SystemState(current_values={"coolant_level": 12.0})

    # 12.0 - 5.0 = 7.0 < min_bound 10.0!
    validator = StateValidator()
    is_valid, verdict, diags, _, _ = validator.validate(c, d, state)

    assert is_valid is False
    assert verdict == CoherenceVerdict.FAIL
    assert any(d.code == DiagnosticCode.STATE_MIN_BOUND_BREACH for d in diags)


def test_max_bound_breach_fails():
    c = ConstraintPrimitive(
        domain_scope={"thermal"},
        target_objects={"furnace"},
        protected_set=set(),
        max_bounds={"temp": 100.0},
    )
    d = DissipatePrimitive(
        loss_domain={"exhaust"},
        target_states=set(),
        side_effects=set(),
        state_delta={"temp": 30.0},
    )
    state = SystemState(current_values={"temp": 85.0})

    # 85.0 + 30.0 = 115.0 > max_bound 100.0!
    validator = StateValidator()
    is_valid, verdict, diags, _, _ = validator.validate(c, d, state)

    assert is_valid is False
    assert verdict == CoherenceVerdict.FAIL
    assert any(d.code == DiagnosticCode.STATE_MAX_BOUND_BREACH for d in diags)


def test_missing_state_variable_fails():
    c = ConstraintPrimitive(
        domain_scope={"physics"},
        target_objects={"engine"},
        protected_set=set(),
        min_bounds={"unknown_var": 5.0},
    )
    d = DissipatePrimitive(
        loss_domain={"exhaust"},
        target_states=set(),
        side_effects=set(),
    )
    state = SystemState(current_values={"other_var": 1.0})

    validator = StateValidator()
    is_valid, verdict, diags, _, _ = validator.validate(c, d, state)

    assert is_valid is False
    assert verdict == CoherenceVerdict.FAIL
    assert any(d.code == DiagnosticCode.STATE_MISSING_VAR for d in diags)


def test_negative_resource_cost_fails():
    c = ConstraintPrimitive(
        domain_scope={"finance"},
        target_objects={"account"},
        protected_set=set(),
    )
    d = DissipatePrimitive(
        loss_domain={"transaction"},
        target_states=set(),
        side_effects=set(),
        resource_cost={"credit": -100.0},  # Trying to forge free credit!
    )
    state = SystemState(current_values={"credit": 50.0})

    validator = StateValidator()
    is_valid, verdict, diags, _, _ = validator.validate(c, d, state)

    assert is_valid is False
    assert verdict == CoherenceVerdict.FAIL
    assert any(d.code == DiagnosticCode.STATE_NEGATIVE_RESOURCE_COST for d in diags)


def test_nan_numeric_value_fails():
    c = ConstraintPrimitive(
        domain_scope={"physics"},
        target_objects={"engine"},
        protected_set=set(),
        min_bounds={"speed": float("nan")},
    )
    d = DissipatePrimitive(
        loss_domain={"exhaust"},
        target_states=set(),
        side_effects=set(),
    )
    state = SystemState(current_values={"speed": 10.0})

    validator = StateValidator()
    is_valid, verdict, diags, _, _ = validator.validate(c, d, state)

    assert is_valid is False
    assert verdict == CoherenceVerdict.FAIL
    assert any(d.code == DiagnosticCode.STATE_INVALID_NUMERIC for d in diags)


def test_flag_invariants_and_protected_flags():
    c = ConstraintPrimitive(
        domain_scope={"ops"},
        target_objects={"reactor"},
        protected_set=set(),
        protected_flags={"lock_engaged"},
        forbidden_flags={"meltdown_mode": True},
        required_flags={"coolant_pump_active": True},
    )
    # Attempting to mutate protected flag
    d1 = DissipatePrimitive(
        loss_domain={"ops"},
        target_states=set(),
        side_effects=set(),
        flag_delta={"lock_engaged": False},  # protected!
    )
    state = SystemState(
        active_flags={"lock_engaged": True, "coolant_pump_active": True, "meltdown_mode": False}
    )

    validator = StateValidator()
    is_valid, verdict, diags, _, _ = validator.validate(c, d1, state)
    assert is_valid is False
    assert verdict == CoherenceVerdict.FAIL
    assert any(d.code == DiagnosticCode.STATE_PROTECTED_FLAG_MUTATED for d in diags)

    # Attempting to activate forbidden flag
    d2 = DissipatePrimitive(
        loss_domain={"ops"},
        target_states=set(),
        side_effects=set(),
        flag_delta={"meltdown_mode": True},
    )
    is_valid2, verdict2, diags2, _, _ = validator.validate(c, d2, state)
    assert is_valid2 is False
    assert verdict2 == CoherenceVerdict.FAIL
    assert any(d.code == DiagnosticCode.STATE_FORBIDDEN_FLAG_ACTIVE for d in diags2)
