"""Clinical pipeline orchestration for executable knowledge packs."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping

from .decision import DecisionResult, RuleMatch
from .loader import KnowledgePack
from .rules import RuleEngine
from .validation import KnowledgePackValidator, ValidationReport

FORWARD_STAGE_RULE_GROUPS: tuple[tuple[str, set[str]], ...] = (
    ("scenarios", {"scenario_rules"}),
    ("diagnosis", {"diagnosis_rules"}),
    ("treatment", {"treatment_rules"}),
    ("constraints", {"constraint_rules"}),
    ("followup", {"followup_rules"}),
)


@dataclass(frozen=True)
class PipelineResult:
    """Report-ready result of a deterministic clinical pipeline run."""

    input_state: Mapping[str, Any]
    inferred_state: Mapping[str, Any]
    validation: ValidationReport | None
    stages: Mapping[str, DecisionResult]
    all_matches: tuple[RuleMatch, ...] = field(default_factory=tuple)

    @property
    def matched_rule_ids(self) -> tuple[str, ...]:
        """Return all matched rule IDs in pipeline execution order."""
        return tuple(match.rule_id for match in self.all_matches)

    def stage(self, name: str) -> DecisionResult:
        """Return the decision result for a named pipeline stage."""
        return self.stages[name]

    def by_rule_id(self, rule_id: str) -> RuleMatch | None:
        """Find the first matched rule by ID across all pipeline stages."""
        for match in self.all_matches:
            if match.rule_id == rule_id:
                return match
        return None


class ClinicalPipeline:
    """Run deterministic forward and backward workflows for a knowledge pack."""

    def __init__(
        self,
        *,
        rule_engine: RuleEngine | None = None,
        validator: KnowledgePackValidator | None = None,
        validate_pack: bool = True,
    ) -> None:
        self.rule_engine = rule_engine or RuleEngine()
        self.validator = validator or KnowledgePackValidator()
        self.validate_pack = validate_pack

    def run_forward(self, pack: KnowledgePack, patient_state: Mapping[str, Any]) -> PipelineResult:
        """Run the forward clinical pipeline.

        Execution order:
            input state -> inference -> scenarios -> diagnosis -> treatment ->
            constraints -> follow-up.

        The input mapping is never mutated. Inference returns a derived copy used
        by all downstream stages during this pipeline cycle.
        """
        validation_report = self._validate(pack)
        frozen_input = MappingProxyType(deepcopy(dict(patient_state)))
        inferred_state = self.rule_engine.infer(pack, frozen_input)

        stages: dict[str, DecisionResult] = {}
        all_matches: list[RuleMatch] = []
        for stage_name, rule_groups in FORWARD_STAGE_RULE_GROUPS:
            stage_result = self.rule_engine.evaluate(pack, inferred_state, rule_groups=rule_groups)
            stages[stage_name] = stage_result
            all_matches.extend(stage_result.matches)

        return PipelineResult(
            input_state=frozen_input,
            inferred_state=inferred_state,
            validation=validation_report,
            stages=MappingProxyType(stages),
            all_matches=tuple(all_matches),
        )

    def plan_backward(self, pack: KnowledgePack, target_treatment: str) -> DecisionResult:
        """Return backward-planning rules for a requested treatment target."""
        self._validate(pack)
        matches: list[RuleMatch] = []
        for filename, group_name, rules in pack.iter_rule_groups():
            if group_name != "backward_planning_rules":
                continue
            for rule in rules:
                if rule.get("target_treatment") != target_treatment:
                    continue
                matches.append(self.rule_engine.create_match(rule, rule_group=group_name, source_file=filename))
        return DecisionResult(tuple(matches))

    def _validate(self, pack: KnowledgePack) -> ValidationReport | None:
        if not self.validate_pack:
            return None
        report = self.validator.validate(pack)
        report.raise_for_errors()
        return report
