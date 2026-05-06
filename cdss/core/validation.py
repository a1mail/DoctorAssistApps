"""Validation for YAML Clinical Knowledge Packs.

The validator checks structural guarantees needed before a deterministic runtime
can safely execute a pack. It does not judge clinical correctness; clinical
content still requires guideline review and medical validation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Literal, Mapping

from .loader import KnowledgePack

Severity = Literal["error", "warning"]


@dataclass(frozen=True)
class ValidationIssue:
    """One structural validation finding."""

    severity: Severity
    code: str
    message: str
    location: str


@dataclass(frozen=True)
class ValidationReport:
    """Aggregated validation result for a knowledge pack."""

    issues: tuple[ValidationIssue, ...] = field(default_factory=tuple)

    @property
    def errors(self) -> tuple[ValidationIssue, ...]:
        return tuple(issue for issue in self.issues if issue.severity == "error")

    @property
    def warnings(self) -> tuple[ValidationIssue, ...]:
        return tuple(issue for issue in self.issues if issue.severity == "warning")

    @property
    def is_valid(self) -> bool:
        return not self.errors

    def raise_for_errors(self) -> None:
        """Raise `ValueError` with all error messages when validation fails."""
        if self.is_valid:
            return
        details = "\n".join(f"- [{issue.code}] {issue.location}: {issue.message}" for issue in self.errors)
        raise ValueError(f"Knowledge pack validation failed:\n{details}")


class KnowledgePackValidator:
    """Run deterministic structural checks over a loaded knowledge pack."""

    def validate(self, pack: KnowledgePack) -> ValidationReport:
        issues: list[ValidationIssue] = []
        issues.extend(self._validate_metadata(pack))
        issues.extend(self._validate_entities(pack))
        issues.extend(self._validate_rule_ids(pack))
        issues.extend(self._validate_rule_explainability(pack))
        issues.extend(self._validate_source_map_coverage(pack))
        issues.extend(self._validate_workflow_rule_groups(pack))
        return ValidationReport(tuple(issues))

    def _validate_metadata(self, pack: KnowledgePack) -> Iterable[ValidationIssue]:
        metadata = pack.get_file("metadata.yaml")
        pack_info = metadata.get("pack")
        source = metadata.get("source_of_truth")
        engine_contract = metadata.get("engine_contract")

        if not isinstance(pack_info, Mapping):
            yield self._error("MISSING_PACK_METADATA", "metadata.yaml", "Missing `pack` mapping.")
        else:
            for field_name in ("id", "disease", "version", "language"):
                if not pack_info.get(field_name):
                    yield self._error(
                        "MISSING_PACK_FIELD",
                        f"metadata.yaml:pack.{field_name}",
                        f"Missing required pack field `{field_name}`.",
                    )

        if not isinstance(source, Mapping) or not source.get("url"):
            yield self._error("MISSING_SOURCE", "metadata.yaml:source_of_truth", "Missing source-of-truth URL.")

        if not isinstance(engine_contract, Mapping):
            yield self._error("MISSING_ENGINE_CONTRACT", "metadata.yaml", "Missing `engine_contract` mapping.")

    def _validate_entities(self, pack: KnowledgePack) -> Iterable[ValidationIssue]:
        entities = pack.get_file("entities.yaml").get("entities")
        if not isinstance(entities, Mapping):
            yield self._error("MISSING_ENTITIES", "entities.yaml", "Missing `entities` mapping.")
            return

        seen: dict[str, str] = {}
        for group_name, group_entities in entities.items():
            location = f"entities.yaml:entities.{group_name}"
            if not isinstance(group_entities, list):
                yield self._error("INVALID_ENTITY_GROUP", location, "Entity group must be a list.")
                continue
            for index, entity in enumerate(group_entities):
                entity_location = f"{location}[{index}]"
                if not isinstance(entity, Mapping):
                    yield self._error("INVALID_ENTITY", entity_location, "Entity must be a mapping.")
                    continue
                entity_id = entity.get("id")
                if not isinstance(entity_id, str) or not entity_id:
                    yield self._error("MISSING_ENTITY_ID", entity_location, "Entity is missing string `id`.")
                    continue
                if entity_id in seen:
                    yield self._error(
                        "DUPLICATE_ENTITY_ID",
                        entity_location,
                        f"Entity ID `{entity_id}` already declared at {seen[entity_id]}.",
                    )
                seen[entity_id] = entity_location
                for required in ("label", "type"):
                    if not entity.get(required):
                        yield self._error(
                            "MISSING_ENTITY_FIELD",
                            entity_location,
                            f"Entity `{entity_id}` is missing `{required}`.",
                        )

    def _validate_rule_ids(self, pack: KnowledgePack) -> Iterable[ValidationIssue]:
        seen: dict[str, str] = {}
        for filename, group_name, rules in pack.iter_rule_groups():
            for index, rule in enumerate(rules):
                location = f"{filename}:{group_name}[{index}]"
                if not isinstance(rule, Mapping):
                    yield self._error("INVALID_RULE", location, "Rule must be a mapping.")
                    continue
                rule_id = rule.get("id")
                if not isinstance(rule_id, str) or not rule_id:
                    yield self._error("MISSING_RULE_ID", location, "Rule is missing string `id`.")
                    continue
                if rule_id in seen:
                    yield self._error("DUPLICATE_RULE_ID", location, f"Rule ID `{rule_id}` already declared at {seen[rule_id]}.")
                seen[rule_id] = location

    def _validate_rule_explainability(self, pack: KnowledgePack) -> Iterable[ValidationIssue]:
        for filename, group_name, rules in pack.iter_rule_groups():
            for index, rule in enumerate(rules):
                if not isinstance(rule, Mapping):
                    continue
                location = f"{filename}:{group_name}[{index}]"
                if not self._has_explain(rule):
                    yield self._error("MISSING_RULE_EXPLAIN", location, "Rule must provide an `explain` string.")

    def _validate_source_map_coverage(self, pack: KnowledgePack) -> Iterable[ValidationIssue]:
        source_map = pack.get_file("source_map.yaml").get("source_map")
        if not isinstance(source_map, Mapping):
            yield self._error("MISSING_SOURCE_MAP", "source_map.yaml", "Missing `source_map` mapping.")
            return
        rule_sources = source_map.get("rule_sources")
        if not isinstance(rule_sources, Mapping):
            yield self._error("MISSING_RULE_SOURCES", "source_map.yaml:source_map", "Missing `rule_sources` mapping.")
            return

        rule_ids = set(pack.rule_ids())
        mapped_ids = set(str(rule_id) for rule_id in rule_sources.keys())
        for rule_id in sorted(rule_ids - mapped_ids):
            yield self._error("RULE_NOT_SOURCE_MAPPED", "source_map.yaml:rule_sources", f"Rule `{rule_id}` is not source mapped.")
        for rule_id in sorted(mapped_ids - rule_ids):
            yield self._warning("STALE_SOURCE_MAP_ENTRY", "source_map.yaml:rule_sources", f"Mapped rule `{rule_id}` is not present in rule files.")

        for rule_id, mapping in rule_sources.items():
            location = f"source_map.yaml:rule_sources.{rule_id}"
            if not isinstance(mapping, Mapping) or not mapping.get("sections"):
                yield self._error("EMPTY_RULE_SOURCE", location, "Mapped rule must declare non-empty `sections`.")

    def _validate_workflow_rule_groups(self, pack: KnowledgePack) -> Iterable[ValidationIssue]:
        workflow = pack.get_file("workflow.yaml").get("workflow")
        if not isinstance(workflow, Mapping):
            yield self._error("MISSING_WORKFLOW", "workflow.yaml", "Missing `workflow` mapping.")
            return
        tabs = workflow.get("tabs")
        if not isinstance(tabs, list):
            yield self._error("INVALID_WORKFLOW_TABS", "workflow.yaml:workflow.tabs", "Workflow tabs must be a list.")
            return

        known_rule_groups = pack.rule_group_names()
        for index, tab in enumerate(tabs):
            location = f"workflow.yaml:workflow.tabs[{index}]"
            if not isinstance(tab, Mapping):
                yield self._error("INVALID_WORKFLOW_TAB", location, "Workflow tab must be a mapping.")
                continue
            rule_groups = tab.get("rule_groups", [])
            if not isinstance(rule_groups, list):
                yield self._error("INVALID_WORKFLOW_RULE_GROUPS", location, "`rule_groups` must be a list.")
                continue
            for group_name in rule_groups:
                if group_name not in known_rule_groups:
                    yield self._error(
                        "UNKNOWN_WORKFLOW_RULE_GROUP",
                        location,
                        f"Workflow references unknown rule group `{group_name}`.",
                    )

    def _has_explain(self, rule: Mapping[str, Any]) -> bool:
        direct_explain = rule.get("explain")
        if isinstance(direct_explain, str) and direct_explain.strip():
            return True
        then = rule.get("then")
        if isinstance(then, Mapping):
            then_explain = then.get("explain")
            return isinstance(then_explain, str) and bool(then_explain.strip())
        return False

    def _error(self, code: str, location: str, message: str) -> ValidationIssue:
        return ValidationIssue("error", code, message, location)

    def _warning(self, code: str, location: str, message: str) -> ValidationIssue:
        return ValidationIssue("warning", code, message, location)
