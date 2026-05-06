"""Deterministic rule execution helpers for Clinical Knowledge Packs."""

from __future__ import annotations

from copy import deepcopy
from types import MappingProxyType
from typing import Any, Mapping

from .decision import DecisionResult, RuleMatch
from .loader import KnowledgePack
from .matcher import ConditionMatcher


class RuleEngine:
    """Execute YAML rule groups against patient state without mutating input."""

    def __init__(self, matcher: ConditionMatcher | None = None) -> None:
        self.matcher = matcher or ConditionMatcher()

    def evaluate(
        self,
        pack: KnowledgePack,
        patient_state: Mapping[str, Any],
        *,
        rule_groups: set[str] | None = None,
    ) -> DecisionResult:
        """Evaluate matching rules and return explainable outputs.

        Args:
            pack: Loaded knowledge pack.
            patient_state: Immutable input state for the evaluation cycle.
            rule_groups: Optional subset of rule-group names to execute.
        """
        matches: list[RuleMatch] = []
        frozen_state = MappingProxyType(deepcopy(dict(patient_state)))
        for filename, group_name, rules in pack.iter_rule_groups():
            if rule_groups is not None and group_name not in rule_groups:
                continue
            for rule in rules:
                condition = rule.get("if")
                if not self.matcher.matches(condition, frozen_state):
                    continue
                when_missing = rule.get("when_missing")
                if isinstance(when_missing, list) and not self.matcher.any_missing(when_missing, frozen_state):
                    continue
                matches.append(self.create_match(rule, rule_group=group_name, source_file=filename))
        return DecisionResult(tuple(matches))

    def create_match(self, rule: Mapping[str, Any], *, rule_group: str, source_file: str) -> RuleMatch:
        """Create an explainable match object for a rule that already matched."""
        output = self.rule_output(rule)
        return RuleMatch.from_rule(
            rule_id=str(rule["id"]),
            rule_group=rule_group,
            source_file=source_file,
            explain=self.explain(rule, output),
            output=output,
        )

    def infer(self, pack: KnowledgePack, patient_state: Mapping[str, Any]) -> Mapping[str, Any]:
        """Return a new state with matching `then.derive` payloads applied.

        This is a minimal forward-inference helper. It does not mutate
        `patient_state`; derived values are applied to a deep copy in rule order.
        """
        next_state: dict[str, Any] = deepcopy(dict(patient_state))
        for _, group_name, rules in pack.iter_rule_groups():
            if group_name != "inference_rules":
                continue
            for rule in rules:
                if not self.matcher.matches(rule.get("if"), next_state):
                    continue
                then = rule.get("then")
                if isinstance(then, Mapping) and isinstance(then.get("derive"), Mapping):
                    next_state.update(deepcopy(dict(then["derive"])))
        return MappingProxyType(next_state)

    def rule_output(self, rule: Mapping[str, Any]) -> Mapping[str, Any]:
        then = rule.get("then")
        if isinstance(then, Mapping):
            return MappingProxyType(deepcopy(dict(then)))

        output: dict[str, Any] = {}
        for key, value in rule.items():
            if key not in {"id", "if", "description", "target_treatment", "applies_to"}:
                output[key] = deepcopy(value)
        return MappingProxyType(output)

    def explain(self, rule: Mapping[str, Any], output: Mapping[str, Any]) -> str:
        direct_explain = rule.get("explain")
        if isinstance(direct_explain, str):
            return direct_explain
        output_explain = output.get("explain")
        if isinstance(output_explain, str):
            return output_explain
        return ""
