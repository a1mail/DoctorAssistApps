from copy import deepcopy
from pathlib import Path
from types import MappingProxyType
import unittest

from cdss.core import KnowledgePack, KnowledgePackLoader, KnowledgePackValidator


PACK_ROOT = Path(__file__).resolve().parents[1] / "cdss" / "knowledge" / "lung_cancer"


class SchemaValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.pack = KnowledgePackLoader().load(PACK_ROOT)

    def test_lung_cancer_pack_matches_runtime_schema_without_warnings(self) -> None:
        report = KnowledgePackValidator().validate(self.pack)

        self.assertEqual(report.errors, ())
        self.assertEqual(report.warnings, ())

    def test_unknown_condition_operator_is_error(self) -> None:
        pack = self._mutated_pack()
        pack.files["diagnosis.yaml"]["diagnosis_rules"][0]["if"] = {"pd_l1_tps": {"near_op": 50}}

        report = KnowledgePackValidator().validate(pack)

        self.assertIn("UNKNOWN_CONDITION_OPERATOR", {issue.code for issue in report.errors})

    def test_unknown_patient_state_field_is_warning(self) -> None:
        pack = self._mutated_pack()
        pack.files["diagnosis.yaml"]["diagnosis_rules"][0]["if"] = {"unregistered_namespace": True}

        report = KnowledgePackValidator().validate(pack)

        self.assertIn("UNKNOWN_PATIENT_STATE_FIELD", {issue.code for issue in report.warnings})
        self.assertEqual(report.errors, ())

    def test_unknown_rule_output_key_is_warning(self) -> None:
        pack = self._mutated_pack()
        pack.files["diagnosis.yaml"]["diagnosis_rules"][0]["then"]["unknown_payload"] = True

        report = KnowledgePackValidator().validate(pack)

        self.assertIn("UNKNOWN_RULE_OUTPUT_KEY", {issue.code for issue in report.warnings})
        self.assertEqual(report.errors, ())

    def _mutated_pack(self) -> KnowledgePack:
        copied_files = {filename: deepcopy(dict(document)) for filename, document in self.pack.files.items()}
        return KnowledgePack(root=self.pack.root, files=MappingProxyType(copied_files))


if __name__ == "__main__":
    unittest.main()
