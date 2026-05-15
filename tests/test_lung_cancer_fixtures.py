from pathlib import Path
import json
import subprocess
import unittest

from cdss.core import ClinicalPipeline, KnowledgePackLoader
from cdss.reporting import ClinicalReportBuilder


ROOT = Path(__file__).resolve().parents[1]
PACK_ROOT = ROOT / "cdss" / "knowledge" / "lung_cancer"
FIXTURE_ROOT = ROOT / "tests" / "fixtures" / "lung_cancer"


def load_yaml(path: Path) -> dict:
    ruby_script = "require 'yaml'; require 'json'; puts JSON.generate(YAML.load_file(ARGV.fetch(0)))"
    completed = subprocess.run(["ruby", "-e", ruby_script, str(path)], check=True, capture_output=True, text=True)
    return json.loads(completed.stdout)


class LungCancerFixtureRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.pack = KnowledgePackLoader().load(PACK_ROOT)
        cls.pipeline = ClinicalPipeline()
        cls.report_builder = ClinicalReportBuilder()

    def test_fixture_regression_matrix(self) -> None:
        fixture_paths = sorted(FIXTURE_ROOT.glob("*.yaml"))
        self.assertGreaterEqual(len(fixture_paths), 6)

        for fixture_path in fixture_paths:
            with self.subTest(fixture=fixture_path.name):
                fixture = load_yaml(fixture_path)
                result = self.pipeline.run_forward(self.pack, fixture["patient_state"])
                report = self.report_builder.build(result)
                expected = fixture["expected"]

                for key, value in expected.get("inferred_state", {}).items():
                    self.assertEqual(result.inferred_state.get(key), value, f"{fixture_path.name}: inferred {key}")

                matched_rule_ids = set(result.matched_rule_ids)
                for rule_id in expected.get("matched_rule_ids", []):
                    self.assertIn(rule_id, matched_rule_ids, f"{fixture_path.name}: missing {rule_id}")
                    self.assertIsNotNone(result.by_rule_id(rule_id))

                report_dict = report.to_dict()
                json.dumps(report_dict, ensure_ascii=False)
                for section_name in expected.get("report_sections", []):
                    self.assertIn(section_name, report_dict["sections"], f"{fixture_path.name}: missing section {section_name}")
                    self.assertTrue(
                        report_dict["sections"][section_name]["items"],
                        f"{fixture_path.name}: section {section_name} should not be empty",
                    )
