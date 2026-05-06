# CDSS Core Runtime (MVP)

This package contains the first runtime layer for YAML/DSL Clinical Knowledge Packs.

## Current scope

- `loader.py` loads required pack YAML files into a `KnowledgePack` object.
- `validation.py` validates structural safety before execution:
  - required metadata/source fields;
  - entity shape and duplicate entity IDs;
  - rule ID presence and uniqueness;
  - explainability for every rule;
  - `source_map.rule_sources` coverage for every rule ID;
  - workflow `rule_groups` references.

The validator does **not** validate clinical correctness. Clinical content still requires guideline-level review and test cases before use in decision support.

## YAML backend

The preferred backend is PyYAML (`requirements.txt`). In constrained environments where PyYAML cannot be installed, the loader falls back to Ruby's standard YAML parser so repository tests can still validate the knowledge pack structure.
