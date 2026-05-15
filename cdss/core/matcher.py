"""Deterministic condition matcher for the CDSS YAML/DSL subset."""

from __future__ import annotations

import re
from typing import Any, Mapping, Sequence

MISSING = object()


class ConditionMatcher:
    """Evaluate YAML `if` conditions against a patient-state mapping.

    Supported operators cover the current knowledge-pack DSL subset:
    `all`, `any`, `contains`, `not_any`, `in`, `exists`, `missing`,
    `gte`, `gt`, `lte`, `lt`, and `matches`.
    """

    def matches(self, condition: Any, state: Mapping[str, Any]) -> bool:
        """Return whether `condition` matches `state`. Empty conditions match."""
        if condition is None:
            return True
        if isinstance(condition, list):
            return all(self.matches(item, state) for item in condition)
        if not isinstance(condition, Mapping):
            return bool(condition)

        if "all" in condition:
            return self._matches_all(condition["all"], state)
        if "any" in condition:
            return self._matches_any(condition["any"], state)

        return all(self._matches_field(field, expected, state) for field, expected in condition.items())

    def _matches_all(self, value: Any, state: Mapping[str, Any]) -> bool:
        if isinstance(value, list):
            return all(self.matches(item, state) for item in value)
        if isinstance(value, Mapping):
            return self.matches(value, state)
        return bool(value)

    def _matches_any(self, value: Any, state: Mapping[str, Any]) -> bool:
        if isinstance(value, list):
            return any(self.matches(item, state) for item in value)
        if isinstance(value, Mapping):
            return any(self._matches_field(field, expected, state) for field, expected in value.items())
        return bool(value)

    def _matches_field(self, field: str, expected: Any, state: Mapping[str, Any]) -> bool:
        actual = self._resolve_path(state, field)

        if isinstance(expected, Mapping):
            return self._matches_operator_mapping(actual, expected)
        if isinstance(expected, list):
            return self._actual_contains_any(actual, expected)
        return self._equals(actual, expected)

    def _matches_operator_mapping(self, actual: Any, expected: Mapping[str, Any]) -> bool:
        operator_keys = {"contains", "any", "not_any", "in", "exists", "missing", "gte", "gt", "lte", "lt", "matches"}
        if not any(key in operator_keys for key in expected):
            return self._equals(actual, expected)

        for operator, operand in expected.items():
            if operator == "contains" and not self._actual_contains(actual, operand):
                return False
            if operator == "any" and not self._actual_contains_any(actual, operand):
                return False
            if operator == "not_any" and self._actual_contains_any(actual, operand):
                return False
            if operator == "in" and not self._actual_in(actual, operand):
                return False
            if operator == "exists" and bool(operand) != (actual is not MISSING):
                return False
            if operator == "missing" and bool(operand) != (actual is MISSING):
                return False
            if operator == "gte" and not self._compare(actual, operand, ">="):
                return False
            if operator == "gt" and not self._compare(actual, operand, ">"):
                return False
            if operator == "lte" and not self._compare(actual, operand, "<="):
                return False
            if operator == "lt" and not self._compare(actual, operand, "<"):
                return False
            if operator == "matches" and not self._regex_matches(actual, operand):
                return False
        return True

    def any_missing(self, fields: Sequence[str], state: Mapping[str, Any]) -> bool:
        """Return true when at least one named field/path is absent from state."""
        return any(self._resolve_path(state, field) is MISSING for field in fields)

    def _resolve_path(self, state: Mapping[str, Any], path: str) -> Any:
        current: Any = state
        for part in path.split("."):
            if not isinstance(current, Mapping) or part not in current:
                return MISSING
            current = current[part]
        return current

    def _equals(self, actual: Any, expected: Any) -> bool:
        if actual is MISSING:
            return False
        if isinstance(actual, list):
            return expected in actual
        return actual == expected

    def _actual_contains(self, actual: Any, expected_item: Any) -> bool:
        if actual is MISSING:
            return False
        if isinstance(actual, Mapping):
            return expected_item in actual.values() or expected_item in actual.keys()
        if isinstance(actual, str):
            return str(expected_item) in actual
        if isinstance(actual, Sequence):
            return expected_item in actual
        return actual == expected_item

    def _actual_contains_any(self, actual: Any, expected_items: Any) -> bool:
        if not isinstance(expected_items, list):
            expected_items = [expected_items]
        return any(self._actual_contains(actual, item) for item in expected_items)

    def _actual_in(self, actual: Any, expected_items: Any) -> bool:
        if actual is MISSING:
            return False
        if not isinstance(expected_items, list):
            expected_items = [expected_items]
        return actual in expected_items

    def _compare(self, actual: Any, expected: Any, operator: str) -> bool:
        if actual is MISSING:
            return False
        try:
            left = float(actual)
            right = float(expected)
        except (TypeError, ValueError):
            return False
        if operator == ">=":
            return left >= right
        if operator == ">":
            return left > right
        if operator == "<=":
            return left <= right
        if operator == "<":
            return left < right
        return False

    def _regex_matches(self, actual: Any, pattern: Any) -> bool:
        if actual is MISSING or pattern is None:
            return False
        return re.search(str(pattern), str(actual)) is not None
