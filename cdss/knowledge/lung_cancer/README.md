# Lung Cancer Clinical Knowledge Pack (RU KR 2025)

This pack externalizes deterministic clinical logic for **злокачественное новообразование бронхов и легкого (C34)** as YAML/DSL knowledge for the Oncology CDSS. The only clinical source is the 2025 Russian guideline PDF declared in `metadata.yaml`.

## Files

- `metadata.yaml` — pack identity, scope, source-of-truth policy, engine contract.
- `entities.yaml` — symptoms, risk factors, diagnostics, histologies, biomarkers, stages, treatments, constraints.
- `inference.yaml` — derived state rules for histology group, driver status, PD-L1 category, stage/intention buckets.
- `diagnosis.yaml` — completeness checks, missing data, workup and biomarker requirements.
- `scenarios.yaml` — branch generation when histology, biomarkers, resectability, or SCLC extent are missing.
- `treatment.yaml` — explainable treatment pathway rules for NSCLC and SCLC.
- `constraints.yaml` — comorbidity, medication, organ function and procedure constraints.
- `backward.yaml` — required data planner for selected treatments.
- `followup.yaml` — surveillance, smoking cessation and complications monitoring.
- `workflow.yaml` — UI/workflow tabs with no embedded clinical logic.
- `source_map.yaml` — rule-to-guideline section traceability.

## Safety rules

- Keep all clinical logic in YAML.
- Do not duplicate clinical rules in UI code.
- Every emitted recommendation must include `rule_id` and `explain`.
- Treat this pack as executable decision support, not autonomous prescribing.
