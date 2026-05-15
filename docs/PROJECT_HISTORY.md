# DoctorAssistApps / Oncology CDSS Project History

This file is the cumulative handoff log for the Oncology CDSS work. Keep it updated after every development session so a future agent or developer can recover context quickly if the chat/session is interrupted.

## 2026-05-06 — Initial project handoff and architecture target

The user provided a full Russian handoff package describing the target system as a deterministic, knowledge-based Oncology CDSS / Clinical Knowledge Engine.

Core architectural commitments:

- Patient State Architecture is the single source of truth.
- Clinical logic must live in external YAML/DSL knowledge packs, not UI or storage code.
- Runtime must support deterministic rule execution, explainability, forward reasoning, backward planning, scenario expansion for missing data, constraints, and auditability.
- Initial MVP clinical domain: lung cancer based on the Russian 2025 guideline PDF declared in the pack metadata.

## 2026-05-06 to 2026-05-14 — Foundation implementation

Implemented the initial CDSS foundation in multiple iterations:

1. **Lung cancer knowledge pack**
   - Added `cdss/knowledge/lung_cancer/` with metadata, entities, inference, diagnosis, treatment, constraints, backward planning, scenarios, follow-up, workflow, source map, and README.
   - The pack declares the Russian lung-cancer guideline URL as source of truth.

2. **Core runtime**
   - Added `cdss.core.KnowledgePackLoader` to load pack YAML files.
   - Added `KnowledgePackValidator` for metadata, entity, rule ID, explainability, source-map, workflow, and schema checks.
   - Added `ConditionMatcher`, `RuleEngine`, `DecisionResult`, `RuleMatch`, `ClinicalPipeline`, and `PipelineResult`.
   - Added PyYAML as preferred dependency with Ruby YAML fallback for constrained environments.

3. **Reporting layer**
   - Added `cdss.reporting.ClinicalReportBuilder`, `ClinicalReport`, and `ReportSection`.
   - Reports contain summary, diagnosis, missing data, scenarios, recommendations, constraints, follow-up, and audit trail.

4. **Schema hardening**
   - Added `cdss/core/schema.py` with supported rule groups, condition operators, rule-output keys, derived-state keys, schedule keys, and patient-state fields.
   - Extended validation to catch unknown operators and warn about unknown fields/outputs.

5. **Tests**
   - Added tests for pack loading, validation, matcher semantics, rule engine behavior, pipeline forward/backward execution, report generation, and schema validation.

## 2026-05-15 — Clinical fixture regression layer

Before adding new work, the full existing test suite was run and passed (`23 tests OK`). Then a fixture-based regression layer was added.

Added fixture files under `tests/fixtures/lung_cancer/`:

- `nsclc_stage_iv_egfr_positive.yaml`
- `nsclc_stage_iv_driver_negative_pdl1_high.yaml`
- `nsclc_stage_iii_unresectable_after_chemoradiation.yaml`
- `sclc_limited.yaml`
- `missing_histology.yaml`
- `constraints_and_followup.yaml`

Added `tests/test_lung_cancer_fixtures.py`, which loads each fixture, runs `ClinicalPipeline`, builds a `ClinicalReport`, and asserts:

- expected inferred state values;
- expected matched rule IDs;
- expected non-empty report sections;
- JSON-serializability of report dictionaries.

The full suite now contains 24 tests and passes.

## Current status

The project currently has a functional MVP Clinical Knowledge Engine foundation:

```text
YAML knowledge pack
→ loader
→ validator + schema checks
→ matcher
→ rule engine
→ clinical pipeline
→ structured report builder
→ regression tests
```

Current repository state after this session:

- Latest planned commit: clinical fixture regression coverage.
- Working tree should be clean after commit.
- No git remote is configured in this environment, so an actual `git push` cannot be performed here unless a remote is added.

## Next recommended step

Proceed with **lung cancer pack deepening**, protected by the new fixture regression tests:

1. Add dedicated `tnm.yaml` for deterministic T/N/M derivation.
2. Update loader required files and validation schema to include the new TNM rule group.
3. Add fixture cases that verify T/N/M derivation from tumor size, nodes, and metastasis descriptors.
4. Gradually split NSCLC/SCLC treatment logic if files become too large.
5. Improve source-map granularity to guideline section/table level.

## Operational rules for future sessions

- Always run the existing test suite before making the next layer of changes.
- Keep clinical logic in YAML/DSL only.
- Keep UI/storage/report formatting free of clinical decision rules.
- Update this file after every development session.
- Commit at the end of each session.
- Push only if a git remote is configured; otherwise record that push was not possible.
