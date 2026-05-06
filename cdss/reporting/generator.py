"""Build report-ready structures from explainable pipeline results.

This module contains no clinical decision logic. It only reshapes matched rule
outputs and inferred patient state into a stable structure suitable for future
DOCX/PDF/UI exporters.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping

from cdss.core import PipelineResult, RuleMatch


@dataclass(frozen=True)
class ReportSection:
    """One named section of a clinical report."""

    title: str
    items: tuple[Any, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ClinicalReport:
    """Structured, audit-friendly report generated from a pipeline result."""

    summary: Mapping[str, Any]
    sections: Mapping[str, ReportSection]
    audit_trail: tuple[Mapping[str, Any], ...]

    def section(self, name: str) -> ReportSection:
        """Return a named report section."""
        return self.sections[name]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation of the report."""
        return {
            "summary": _to_plain(self.summary),
            "sections": {
                name: {"title": section.title, "items": _to_plain(section.items)}
                for name, section in self.sections.items()
            },
            "audit_trail": _to_plain(self.audit_trail),
        }


class ClinicalReportBuilder:
    """Build structured reports from `PipelineResult` objects."""

    def build(self, result: PipelineResult) -> ClinicalReport:
        """Create a report with summary, clinical sections, and audit trail."""
        summary = MappingProxyType(self._summary(result))
        sections = MappingProxyType(
            {
                "diagnosis": ReportSection("Диагноз и стадирование", self._diagnosis_items(result)),
                "missing_data": ReportSection("Недостающие данные", self._missing_data_items(result)),
                "scenarios": ReportSection("Сценарные ветви", self._scenario_items(result)),
                "recommendations": ReportSection("Рекомендации", self._recommendation_items(result)),
                "constraints": ReportSection("Ограничения и противопоказания", self._stage_outputs(result, "constraints")),
                "followup": ReportSection("Наблюдение", self._stage_outputs(result, "followup")),
            }
        )
        return ClinicalReport(summary=summary, sections=sections, audit_trail=self._audit_trail(result))

    def _summary(self, result: PipelineResult) -> dict[str, Any]:
        state = result.inferred_state
        return {
            "histology": state.get("histology"),
            "histology_group": state.get("histology_group"),
            "tnm": state.get("tnm"),
            "stage_group": state.get("stage_group"),
            "treatment_intent": state.get("treatment_intent"),
            "driver_positive": state.get("driver_positive"),
            "driver_gene": state.get("driver_gene"),
            "pd_l1_category": state.get("pd_l1_category"),
            "matched_rule_count": len(result.all_matches),
        }

    def _diagnosis_items(self, result: PipelineResult) -> tuple[Any, ...]:
        items: list[Any] = []
        state = result.inferred_state
        for key in ("histology", "histology_group", "tnm", "stage_group", "treatment_intent"):
            if key in state:
                items.append({key: state[key]})
        items.extend(self._stage_outputs(result, "diagnosis"))
        return tuple(items)

    def _missing_data_items(self, result: PipelineResult) -> tuple[Any, ...]:
        items: list[Any] = []
        for stage_name in ("diagnosis", "scenarios", "treatment", "constraints", "followup"):
            stage = result.stages.get(stage_name)
            if stage is None:
                continue
            items.extend(stage.missing_data)
        return tuple(items)

    def _scenario_items(self, result: PipelineResult) -> tuple[Any, ...]:
        items: list[Any] = []
        scenarios = result.stages.get("scenarios")
        if scenarios is None:
            return tuple(items)
        for match in scenarios.matches:
            branches = match.output.get("generate_branches")
            if branches:
                items.append({"rule_id": match.rule_id, "explain": match.explain, "branches": branches})
        return tuple(items)

    def _recommendation_items(self, result: PipelineResult) -> tuple[Any, ...]:
        items: list[Any] = []
        for stage_name in ("treatment", "followup"):
            stage = result.stages.get(stage_name)
            if stage is None:
                continue
            for match in stage.matches:
                if "recommend" in match.output or "schedule" in match.output or "not_recommended" in match.output:
                    items.append(self._match_payload(match))
        return tuple(items)

    def _stage_outputs(self, result: PipelineResult, stage_name: str) -> tuple[Any, ...]:
        stage = result.stages.get(stage_name)
        if stage is None:
            return ()
        return tuple(self._match_payload(match) for match in stage.matches)

    def _audit_trail(self, result: PipelineResult) -> tuple[Mapping[str, Any], ...]:
        return tuple(
            MappingProxyType(
                {
                    "rule_id": match.rule_id,
                    "rule_group": match.rule_group,
                    "source_file": match.source_file,
                    "explain": match.explain,
                }
            )
            for match in result.all_matches
        )

    def _match_payload(self, match: RuleMatch) -> Mapping[str, Any]:
        return MappingProxyType(
            {
                "rule_id": match.rule_id,
                "rule_group": match.rule_group,
                "source_file": match.source_file,
                "explain": match.explain,
                "output": match.output,
            }
        )


def _to_plain(value: Any) -> Any:
    """Recursively convert mappings/tuples into JSON-friendly containers."""
    if isinstance(value, Mapping):
        return {key: _to_plain(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_to_plain(item) for item in value]
    if isinstance(value, list):
        return [_to_plain(item) for item in value]
    return value
