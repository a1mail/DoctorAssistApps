from pathlib import Path
import unittest

from cdss.core import ClinicalPipeline, KnowledgePackLoader


PACK_ROOT = Path(__file__).resolve().parents[1] / "cdss" / "knowledge" / "lung_cancer"


class ClinicalPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.pack = KnowledgePackLoader().load(PACK_ROOT)
        cls.pipeline = ClinicalPipeline()

    def test_forward_pipeline_runs_inference_to_treatment_without_mutating_input(self) -> None:
        state = {
            "histology": "adenocarcinoma",
            "biomarkers": ["egfr_ex19del"],
            "tnm": {"M": "M1b"},
        }
        result = self.pipeline.run_forward(self.pack, state)

        self.assertEqual(result.inferred_state["histology_group"], "nsclc")
        self.assertEqual(result.inferred_state["stage_group"], "stage_iv")
        self.assertIn("LC_TX_NSCLC_STAGE_IV_DRIVER_POSITIVE", result.matched_rule_ids)
        self.assertIsNotNone(result.by_rule_id("LC_TX_NSCLC_STAGE_IV_DRIVER_POSITIVE"))
        self.assertNotIn("histology_group", state)

    def test_forward_pipeline_reports_missing_tissue_and_stage(self) -> None:
        result = self.pipeline.run_forward(self.pack, {})

        self.assertIn("LC_SC_HISTOLOGY_UNKNOWN", result.matched_rule_ids)
        self.assertIn("LC_DX_MISSING_TISSUE", result.matched_rule_ids)
        self.assertIn("LC_DX_MISSING_STAGE", result.matched_rule_ids)
        self.assertTrue(result.stage("diagnosis").missing_data)

    def test_forward_pipeline_applies_constraints_and_followup(self) -> None:
        state = {
            "comorbidities": ["renal_failure"],
            "creatinine_clearance": 45,
            "post_treatment_status": "after_radical_treatment",
            "years_since_radical_treatment": 1,
            "general_condition": "satisfactory",
        }
        result = self.pipeline.run_forward(self.pack, state)

        self.assertIn("LC_CTR_PLATINUM_RENAL_FAILURE", result.stage("constraints").matched_rule_ids)
        self.assertIn("LC_FU_AFTER_RADICAL_YEARS_0_3", result.stage("followup").matched_rule_ids)

    def test_backward_planner_returns_only_requested_target(self) -> None:
        result = self.pipeline.plan_backward(self.pack, "matched_targeted_therapy")

        self.assertEqual(result.matched_rule_ids, ("LC_BW_TARGETED_THERAPY_REQUIREMENTS",))
        match = result.by_rule_id("LC_BW_TARGETED_THERAPY_REQUIREMENTS")
        self.assertIsNotNone(match)
        self.assertIn("requires", match.output)
        self.assertTrue(match.explain)


if __name__ == "__main__":
    unittest.main()
