"""Schema metadata for the CDSS YAML/DSL runtime.

The schema is intentionally lightweight: it defines the current executable DSL
surface so validators can catch structural mistakes without embedding clinical
rules in Python code.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class KnowledgePackSchema:
    """Declarative schema for knowledge-pack validation."""

    rule_groups: frozenset[str] = field(
        default_factory=lambda: frozenset(
            {
                "inference_rules",
                "diagnosis_rules",
                "treatment_rules",
                "constraint_rules",
                "backward_planning_rules",
                "scenario_rules",
                "followup_rules",
            }
        )
    )
    logical_condition_keys: frozenset[str] = field(default_factory=lambda: frozenset({"all", "any"}))
    condition_operators: frozenset[str] = field(
        default_factory=lambda: frozenset(
            {"contains", "any", "not_any", "in", "exists", "missing", "gte", "gt", "lte", "lt", "matches"}
        )
    )
    rule_top_level_keys: frozenset[str] = field(
        default_factory=lambda: frozenset(
            {
                "id",
                "description",
                "if",
                "then",
                "when_missing",
                "target_treatment",
                "applies_to",
                "explain",
                "generate_branches",
                "requires",
                "missing_data_plan",
            }
        )
    )
    output_keys: frozenset[str] = field(
        default_factory=lambda: frozenset(
            {
                "action",
                "alternatives",
                "avoid_until_driver_known",
                "conditional",
                "derive",
                "explain",
                "generate_branches",
                "histology_specific",
                "intent",
                "missing_data",
                "monitor",
                "not_recommended",
                "options",
                "recommend",
                "recommend_diagnostics",
                "required_actions",
                "required_biomarkers",
                "required_data",
                "required_decisions",
                "required_next_data",
                "requires",
                "missing_data_plan",
                "schedule",
                "sequencing",
                "start_window",
                "status",
            }
        )
    )
    derived_state_keys: frozenset[str] = field(
        default_factory=lambda: frozenset(
            {
                "driver_gene",
                "driver_positive",
                "driver_status",
                "histology_group",
                "pd_l1_category",
                "stage_group",
                "targeted_option",
                "treatment_intent",
            }
        )
    )
    schedule_keys: frozenset[str] = field(
        default_factory=lambda: frozenset(
            {
                "abdomen_us_or_ct",
                "annual_systemic_imaging",
                "bone_scan",
                "brain_mri",
                "brain_mri_or_ct_contrast",
                "chest_xray_or_ct",
                "oncology_visit",
                "physical_exam",
                "surveillance",
            }
        )
    )
    patient_state_fields: frozenset[str] = field(
        default_factory=lambda: frozenset(
            {
                "active_pneumonitis",
                "active_systemic_therapy",
                "adjuvant_platinum_completed",
                "baseline_qtc_prolonged",
                "biomarkers",
                "chemoradiation_completed",
                "coagulation_uncontrolled",
                "comorbidities",
                "complaints",
                "creatinine_clearance",
                "current_smoking",
                "diagnostics",
                "driver_positive",
                "ecog",
                "general_condition",
                "histology",
                "histology_group",
                "imaging_findings",
                "immunosuppression_high_dose",
                "medications",
                "multidisciplinary_board",
                "no_immunotherapy_contraindication",
                "operability",
                "organ_function_allows_platinum",
                "pd_l1_tps",
                "performance_status.ecog",
                "post_treatment_status",
                "postoperative_status",
                "predicted_postoperative_fev1_dlco_low",
                "progression_after_chemoradiation",
                "prophylactic_cranial_irradiation_done",
                "pulmonary_function_severely_limited",
                "resectability",
                "risk_factors",
                "sclc_extent",
                "severe_hepatic_impairment",
                "severe_uncontrolled_comorbidity",
                "stage_group",
                "thoracic_radiotherapy",
                "tnm.M",
                "tnm.N",
                "tnm.T",
                "toxicity.baseline_neuropathy_grade",
                "uncontrolled_heart_failure",
                "years_since_radical_treatment",
                "years_since_treatment_start",
            }
        )
    )

    def is_allowed_output_key(self, key: str) -> bool:
        """Return whether an output key is part of the current DSL surface."""
        return key in self.output_keys or key in self.derived_state_keys or key in self.schedule_keys


DEFAULT_SCHEMA = KnowledgePackSchema()
