from pathlib import Path
import unittest

from cdss.core import KnowledgePackLoader, KnowledgePackValidator


PACK_ROOT = Path(__file__).resolve().parents[1] / "cdss" / "knowledge" / "lung_cancer"


class LungCancerKnowledgePackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.pack = KnowledgePackLoader().load(PACK_ROOT)
        cls.report = KnowledgePackValidator().validate(cls.pack)

    def test_pack_loads_required_yaml_files(self) -> None:
        self.assertEqual(len(self.pack.files), 11)
        self.assertIn("metadata.yaml", self.pack.files)
        self.assertIn("source_map.yaml", self.pack.files)

    def test_rule_ids_are_discoverable(self) -> None:
        rule_ids = self.pack.rule_ids()
        self.assertEqual(len(rule_ids), 61)
        self.assertIn("LC_TX_NSCLC_STAGE_IV_DRIVER_POSITIVE", rule_ids)
        self.assertIn("LC_SC_HISTOLOGY_UNKNOWN", rule_ids)

    def test_pack_is_structurally_valid(self) -> None:
        self.assertTrue(self.report.is_valid, self.report.errors)
        self.assertEqual(self.report.errors, ())

    def test_workflow_references_existing_rule_groups(self) -> None:
        unknown_group_errors = [issue for issue in self.report.errors if issue.code == "UNKNOWN_WORKFLOW_RULE_GROUP"]
        self.assertEqual(unknown_group_errors, [])

    def test_all_rule_ids_have_source_map_entries(self) -> None:
        source_map_errors = [issue for issue in self.report.errors if issue.code == "RULE_NOT_SOURCE_MAPPED"]
        self.assertEqual(source_map_errors, [])


if __name__ == "__main__":
    unittest.main()
