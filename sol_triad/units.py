"""
SOL-Triad Engine v0.4.1
Unit Registry and Dimensional Verification.

Enforces strict physical dimensionality, avoids unknown/untyped bypasses,
and supports deterministic numerical conversions.
"""

from typing import Dict, Optional, Tuple, Callable
import math


class DimensionalityError(ValueError):
    """Raised when two units belong to incompatible physical dimensions."""
    pass


class UnknownUnitError(ValueError):
    """Raised when a unit string is not recognized by the registry."""
    pass


class UnitRegistry:
    """
    Authoritative Unit Registry.
    Guarantees strict dimensional compatibility and provides standard conversion factors.
    """

    # Normalized dimension mapping: unit_alias.lower() -> dimension
    DIMENSIONS: Dict[str, str] = {
        # Pressure
        "pa": "pressure",
        "kpa": "pressure",
        "mpa": "pressure",
        "bar": "pressure",
        "mbar": "pressure",
        "psi": "pressure",
        "atm": "pressure",
        "torr": "pressure",

        # Time
        "s": "time",
        "sec": "time",
        "ms": "time",
        "min": "time",
        "hr": "time",
        "hour": "time",
        "day": "time",

        # Temperature
        "c": "temperature",
        "celsius": "temperature",
        "k": "temperature",
        "kelvin": "temperature",
        "f": "temperature",
        "fahrenheit": "temperature",

        # Ratio / Dimensionless
        "ratio": "ratio",
        "fraction": "ratio",
        "percent": "ratio",
        "%": "ratio",
        "ppm": "ratio",

        # Energy
        "j": "energy",
        "joule": "energy",
        "kj": "energy",
        "kwh": "energy",
        "cal": "energy",
        "kcal": "energy",

        # Mass
        "kg": "mass",
        "g": "mass",
        "mg": "mass",
        "lb": "mass",

        # Length
        "m": "length",
        "cm": "length",
        "mm": "length",
        "km": "length",
        "inch": "length",
        "ft": "length",

        # Frequency / Velocity
        "hz": "frequency",
        "khz": "frequency",
        "mhz": "frequency",
        "rpm": "rotational_speed",
    }

    # Linear conversion factors to base SI units: (multiplier_to_base, offset_to_base)
    # Base units: Pa, s, K, ratio (1.0), J, kg, m, Hz
    _CONVERSION_TO_BASE: Dict[str, Tuple[float, float]] = {
        # Pressure -> Pa
        "pa": (1.0, 0.0),
        "kpa": (1_000.0, 0.0),
        "mpa": (1_000_000.0, 0.0),
        "bar": (100_000.0, 0.0),
        "mbar": (100.0, 0.0),
        "psi": (6894.757293, 0.0),
        "atm": (101325.0, 0.0),
        "torr": (133.322368, 0.0),

        # Time -> s
        "s": (1.0, 0.0),
        "sec": (1.0, 0.0),
        "ms": (0.001, 0.0),
        "min": (60.0, 0.0),
        "hr": (3600.0, 0.0),
        "hour": (3600.0, 0.0),
        "day": (86400.0, 0.0),

        # Temperature -> K
        "k": (1.0, 0.0),
        "kelvin": (1.0, 0.0),
        "c": (1.0, 273.15),
        "celsius": (1.0, 273.15),
        "f": (5.0 / 9.0, 273.15 - (32.0 * 5.0 / 9.0)),
        "fahrenheit": (5.0 / 9.0, 273.15 - (32.0 * 5.0 / 9.0)),

        # Ratio -> 1.0
        "ratio": (1.0, 0.0),
        "fraction": (1.0, 0.0),
        "percent": (0.01, 0.0),
        "%": (0.01, 0.0),
        "ppm": (1e-6, 0.0),

        # Energy -> J
        "j": (1.0, 0.0),
        "joule": (1.0, 0.0),
        "kj": (1000.0, 0.0),
        "kwh": (3_600_000.0, 0.0),
        "cal": (4.184, 0.0),
        "kcal": (4184.0, 0.0),

        # Mass -> kg
        "kg": (1.0, 0.0),
        "g": (0.001, 0.0),
        "mg": (1e-6, 0.0),
        "lb": (0.45359237, 0.0),

        # Length -> m
        "m": (1.0, 0.0),
        "cm": (0.01, 0.0),
        "mm": (0.001, 0.0),
        "km": (1000.0, 0.0),
        "inch": (0.0254, 0.0),
        "ft": (0.3048, 0.0),

        # Frequency -> Hz
        "hz": (1.0, 0.0),
        "khz": (1000.0, 0.0),
        "mhz": (1_000_000.0, 0.0),
        "rpm": (1.0 / 60.0, 0.0),
    }

    @classmethod
    def normalize_unit(cls, unit: Optional[str]) -> Optional[str]:
        if unit is None:
            return None
        trimmed = unit.strip().lower()
        return trimmed if trimmed else None

    @classmethod
    def get_dimension(cls, unit: Optional[str]) -> Optional[str]:
        """Returns the physical dimension of the unit, or None if unrecognized/empty."""
        u = cls.normalize_unit(unit)
        if not u:
            return None
        return cls.DIMENSIONS.get(u)

    @classmethod
    def is_known(cls, unit: Optional[str]) -> bool:
        """Returns True if the unit is registered, False otherwise."""
        u = cls.normalize_unit(unit)
        if not u:
            return False
        return u in cls.DIMENSIONS

    @classmethod
    def are_compatible(
        cls, 
        unit1: Optional[str], 
        unit2: Optional[str], 
        allow_both_empty: bool = True
    ) -> Tuple[bool, str]:
        """
        Strict compatibility check.
        Returns (is_compatible, explanation).

        Anti-bypass guarantees:
          - If one unit is missing and the other is specified, FAILS (no asymmetric bypass).
          - If both units are unrecognized, FAILS (unknown dimensions are not compatible with each other).
          - If both are empty, only passes if allow_both_empty is explicitly True (for dimensionless scalars).
        """
        u1 = cls.normalize_unit(unit1)
        u2 = cls.normalize_unit(unit2)

        if u1 is None and u2 is None:
            if allow_both_empty:
                return True, "Both parameters are unitless."
            return False, "Missing units for both parameters in strict dimensional context."

        if (u1 is None and u2 is not None) or (u1 is not None and u2 is None):
            return False, f"Asymmetric unit specification: '{unit1}' vs '{unit2}'. Missing unit bypass rejected."

        dim1 = cls.get_dimension(u1)
        dim2 = cls.get_dimension(u2)

        if dim1 is None and dim2 is None:
            return False, f"Both units '{unit1}' and '{unit2}' are unknown to UnitRegistry."
        if dim1 is None:
            return False, f"Unit '{unit1}' is not recognized in UnitRegistry."
        if dim2 is None:
            return False, f"Unit '{unit2}' is not recognized in UnitRegistry."

        if dim1 != dim2:
            return False, f"Dimensional incompatibility: '{unit1}' ({dim1}) cannot be reconciled with '{unit2}' ({dim2})."

        return True, f"Units '{unit1}' and '{unit2}' are dimensionally compatible ({dim1})."

    @classmethod
    def convert(cls, value: float, from_unit: str, to_unit: str) -> float:
        """
        Converts numerical value between dimensionally compatible units.
        Raises DimensionalityError if incompatible or UnknownUnitError if unit is unknown.
        """
        if math.isnan(value) or math.isinf(value):
            raise ValueError(f"Cannot convert non-finite float value: {value}")

        u_from = cls.normalize_unit(from_unit)
        u_to = cls.normalize_unit(to_unit)

        if not u_from or u_from not in cls._CONVERSION_TO_BASE:
            raise UnknownUnitError(f"Unknown source unit: '{from_unit}'")
        if not u_to or u_to not in cls._CONVERSION_TO_BASE:
            raise UnknownUnitError(f"Unknown destination unit: '{to_unit}'")

        dim_from = cls.get_dimension(u_from)
        dim_to = cls.get_dimension(u_to)
        if dim_from != dim_to:
            raise DimensionalityError(
                f"Cannot convert between different dimensions: '{from_unit}' ({dim_from}) -> '{to_unit}' ({dim_to})"
            )

        if u_from == u_to:
            return value

        # Convert from source to base
        mult_from, offset_from = cls._CONVERSION_TO_BASE[u_from]
        base_val = (value * mult_from) + offset_from

        # Convert from base to destination
        mult_to, offset_to = cls._CONVERSION_TO_BASE[u_to]
        converted = (base_val - offset_to) / mult_to
        return converted

    @classmethod
    def convert_delta(cls, value: float, from_unit: str, to_unit: str) -> float:
        """Converts an additive difference without applying affine offsets."""
        if math.isnan(value) or math.isinf(value):
            raise ValueError(f"Cannot convert non-finite float value: {value}")

        u_from = cls.normalize_unit(from_unit)
        u_to = cls.normalize_unit(to_unit)

        if not u_from or u_from not in cls._CONVERSION_TO_BASE:
            raise UnknownUnitError(f"Unknown source unit: '{from_unit}'")
        if not u_to or u_to not in cls._CONVERSION_TO_BASE:
            raise UnknownUnitError(f"Unknown destination unit: '{to_unit}'")

        dim_from = cls.get_dimension(u_from)
        dim_to = cls.get_dimension(u_to)
        if dim_from != dim_to:
            raise DimensionalityError(
                f"Cannot convert between different dimensions: '{from_unit}' ({dim_from}) -> '{to_unit}' ({dim_to})"
            )

        multiplier_from, _ = cls._CONVERSION_TO_BASE[u_from]
        multiplier_to, _ = cls._CONVERSION_TO_BASE[u_to]
        return value * multiplier_from / multiplier_to
