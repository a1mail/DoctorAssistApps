"""Explainable decision result models for deterministic rule execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping


@dataclass(frozen=True)
class RuleMatch:
    """One rule that matched a patient state."""

    rule_id: str
    rule_group: str
    source_file: str
    explain: str
    output: Mapping[str, Any]

    @classmethod
    def from_rule(
        cls,
        *,
        rule_id: str,
        rule_group: str,
        source_file: str,
        explain: str,
        output: Mapping[str, Any],
    ) -> "RuleMatch":
        return cls(
            rule_id=rule_id,
            rule_group=rule_group,
            source_file=source_file,
            explain=explain,
            output=MappingProxyType(dict(output)),
        )


@dataclass(frozen=True)
class DecisionResult:
    """Aggregated deterministic evaluation result."""

    matches: tuple[RuleMatch, ...] = field(default_factory=tuple)

    @property
    def matched_rule_ids(self) -> tuple[str, ...]:
        """Return matched rule IDs in deterministic pack/rule order."""
        return tuple(match.rule_id for match in self.matches)

    @property
    def recommendations(self) -> tuple[Mapping[str, Any], ...]:
        """Return outputs that contain recommendations."""
        return tuple(match.output for match in self.matches if "recommend" in match.output)

    @property
    def missing_data(self) -> tuple[Any, ...]:
        """Return missing-data payloads emitted by matched rules."""
        payloads: list[Any] = []
        for match in self.matches:
            for key in ("missing_data", "required_next_data", "required_data", "required_biomarkers"):
                if key in match.output:
                    payloads.append(match.output[key])
        return tuple(payloads)

    def by_rule_id(self, rule_id: str) -> RuleMatch | None:
        """Find the first matched rule by ID."""
        for match in self.matches:
            if match.rule_id == rule_id:
                return match
        return None
