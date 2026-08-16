"""Compatibility imports for the phase-two calendar domain package."""

from app.calendar.engine import (
    ENGINE_VERSION, MAX_YEAR, MIN_YEAR, RULE_VERSION, apply_true_solar_time,
    calendar_analysis, equation_of_time_minutes, parse_local_datetime,
)

__all__ = (
    "ENGINE_VERSION", "MAX_YEAR", "MIN_YEAR", "RULE_VERSION", "apply_true_solar_time",
    "calendar_analysis", "equation_of_time_minutes", "parse_local_datetime",
)
