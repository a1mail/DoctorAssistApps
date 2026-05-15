from pathlib import Path
import json
import unittest

from cdss.core import ClinicalPipeline, KnowledgePackLoader
from cdss.reporting import ClinicalReportBuilder


PACK_ROOT = Path(__file__).resolve().parents[1] / "cdss" / "knowledge" / "lung_cancer"


class ClinicalReportBuilderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.pack = KnowledgePackLoader().load(PACK_ROOT)
        cls.pipeline = ClinicalPipeline()
        cls.builder = ClinicalReportBuilder()

    def test_report_contains_summary_recommendations_and_audit_trail(self) -> None:
        result = self.pipeline.run_forward(
            self.pack,
            {
                "histology": "adenocarcinoma",
                "biomarkers": ["egfr_ex19del"],
                "tnm": {"M": "M1b"},
            },
        )
        report = self.builder.build(result)

        self.assertEqual(report.summary["histology_group"], "nsclc")
        self.assertEqual(report.summary["stage_group"], "stage_iv")
        self.assertGreater(report.summary["matched_rule_count"], 0)
        self.assertTrue(report.section("recommendations").items)
        audit_rule_ids = [item["rule_id"] for item in report.audit_trail]
        self.assertIn("LC_TX_NSCLC_STAGE_IV_DRIVER_POSITIVE", audit_rule_ids)

    def test_report_contains_missing_data_and_scenario_branches(self) -> None:
        result = self.pipeline.run_forward(self.pack, {})
        report = self.builder.build(result)

        self.assertTrue(report.section("missing_data").items)
        self.assertTrue(report.section("scenarios").items)
        scenario = report.section("scenarios").items[0]
        self.assertEqual(scenario["rule_id"], "LC_SC_HISTOLOGY_UNKNOWN")
        self.assertEqual([branch["branch_id"] for branch in scenario["branches"]], ["possible_nsclc", "possible_sclc"])

    def test_report_to_dict_is_exporter_friendly(self) -> None:
        result = self.pipeline.run_forward(
            self.pack,
            {
                "comorbidities": ["renal_failure"],
                "creatinine_clearance": 45,
            },
        )
        report_dict = self.builder.build(result).to_dict()

        self.assertIn("summary", report_dict)
        self.assertIn("sections", report_dict)
        self.assertIn("audit_trail", report_dict)
        self.assertIn("constraints", report_dict["sections"])
        json.dumps(report_dict, ensure_ascii=False)


if __name__ == "__main__":
    unittest.main()
