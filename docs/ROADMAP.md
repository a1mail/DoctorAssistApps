# Oncology CDSS Development Roadmap

This roadmap keeps the project aligned with the Patient State Architecture and the rule that clinical logic belongs in YAML/DSL knowledge packs, not UI or storage code.

## Completed foundation

1. **Knowledge pack skeleton**
   - Lung cancer Russian-guideline pack under `cdss/knowledge/lung_cancer/`.
   - YAML files for metadata, entities, inference, diagnosis, treatment, constraints, scenarios, backward planning, follow-up, workflow, and source traceability.

2. **Pack loader and structural validator**
   - `cdss.core.KnowledgePackLoader` loads required YAML files.
   - `cdss.core.KnowledgePackValidator` checks metadata, entity structure, rule IDs, explainability, source-map coverage, and workflow rule groups.

3. **Deterministic rule execution MVP**
   - `ConditionMatcher` evaluates the current DSL subset.
   - `RuleEngine` evaluates rule groups without mutating input patient state.
   - Minimal forward inference applies `then.derive` payloads to a derived state copy.

4. **Clinical pipeline orchestration**
   - `ClinicalPipeline.run_forward()` runs inference, scenarios, diagnosis, treatment, constraints, and follow-up in deterministic order.
   - `ClinicalPipeline.plan_backward()` returns treatment-specific prerequisite plans.

5. **Report-ready transformation**
   - `ClinicalReportBuilder` converts `PipelineResult` into sections for diagnosis, missing data, scenarios, recommendations, constraints, follow-up, and audit trail.

## Next priorities

### Priority 1 — Clinical schema hardening

- ✅ Added explicit runtime schema metadata for supported rule groups, patient-state fields, condition operators, and rule-output keys.
- ✅ Added validator checks for unknown condition operators, unknown patient-state fields, and unknown output keys.
- Next: normalize enum-like values such as stages, treatment IDs, and biomarker IDs into reusable constants.

### Priority 2 — Lung cancer pack deepening

- Add dedicated `tnm.yaml` with deterministic T/N/M derivation rules.
- Split treatment knowledge into NSCLC and SCLC submodules if file size grows.
- Add precise biomarker-testing requirements and richer treatment prerequisites.
- Add guideline-source traceability at a more granular section/table level.

### Priority 3 — Clinical fixtures and regression tests

- Add patient fixtures for core clinical scenarios:
  - NSCLC stage I operable;
  - NSCLC stage III unresectable after chemoradiation;
  - NSCLC stage IV EGFR-positive;
  - NSCLC stage IV driver-negative PD-L1 high;
  - SCLC limited;
  - SCLC extensive;
  - missing histology;
  - missing biomarkers.
- Assert expected matched rule IDs, missing data, recommendations, constraints, follow-up, and report sections.

### Priority 4 — Exporters and storage

- Build JSON, Markdown, DOCX, and PDF exporters on top of `ClinicalReport.to_dict()`.
- Add SQLite patient persistence after the runtime/report model stabilizes.

### Priority 5 — UI

- Build UI only after runtime, validation, fixtures, and reports are stable.
- UI must render workflow metadata and report outputs; it must not contain clinical rules.

## Current next best implementation step

Implement **clinical fixtures and regression tests**:

1. Add reusable patient fixtures for representative lung cancer scenarios.
2. Assert expected matched rule IDs, missing data, recommendations, constraints, follow-up, and report sections.
3. Use fixtures to protect future knowledge-pack deepening work, including `tnm.yaml`.
