# CDSS Core Runtime (MVP)

This package contains the first runtime layer for YAML/DSL Clinical Knowledge Packs.

## Current scope

- `loader.py` loads required pack YAML files into a `KnowledgePack` object.
- `matcher.py` evaluates deterministic YAML `if` conditions against patient state.
- `rules.py` executes rule groups and returns explainable `DecisionResult` objects.
- `decision.py` defines immutable result models with `rule_id`, `explain`, and rule outputs.
- `validation.py` validates structural safety before execution:
  - required metadata/source fields;
  - entity shape and duplicate entity IDs;
  - rule ID presence and uniqueness;
  - explainability for every rule;
  - `source_map.rule_sources` coverage for every rule ID;
  - workflow `rule_groups` references.

The rule engine is an MVP executor for the current DSL subset; it does **not** perform clinical correctness validation. The validator does **not** validate clinical correctness. Clinical content still requires guideline-level review and test cases before use in decision support.

## YAML backend

The preferred backend is PyYAML (`requirements.txt`). In constrained environments where PyYAML cannot be installed, the loader falls back to Ruby's standard YAML parser so repository tests can still validate the knowledge pack structure.
