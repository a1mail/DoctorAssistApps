from pathlib import Path
import unittest

from cdss.core import ConditionMatcher, KnowledgePackLoader, RuleEngine


PACK_ROOT = Path(__file__).resolve().parents[1] / "cdss" / "knowledge" / "lung_cancer"


class ConditionMatcherTests(unittest.TestCase):
    def setUp(self) -> None:
        self.matcher = ConditionMatcher()

    def test_matches_nested_all_any_and_numeric_operators(self) -> None:
        state = {"histology_group": "nsclc", "stage_group": "stage_iv", "pd_l1_tps": 75}
        condition = {
            "all": [
                {"histology_group": "nsclc"},
                {"stage_group": {"in": ["stage_iiib", "stage_iv"]}},
                {"pd_l1_tps": {"gte": 50}},
            ]
        }
        self.assertTrue(self.matcher.matches(condition, state))

    def test_matches_missing_exists_contains_and_regex(self) -> None:
        state = {"biomarkers": ["egfr_ex19del"], "tnm": {"M": "M1c"}}
        self.assertTrue(self.matcher.matches({"histology": {"missing": True}}, state))
        self.assertTrue(self.matcher.matches({"tnm.M": {"exists": True, "matches": "^M1"}}, state))
        self.assertTrue(self.matcher.matches({"biomarkers": {"contains": "egfr_ex19del"}}, state))
        self.assertFalse(self.matcher.matches({"biomarkers": {"not_any": ["egfr_ex19del"]}}, state))


class RuleEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.pack = KnowledgePackLoader().load(PACK_ROOT)
        cls.engine = RuleEngine()

    def test_inference_derives_nsclc_egfr_and_metastatic_state(self) -> None:
        state = {
            "histology": "adenocarcinoma",
            "biomarkers": ["egfr_ex19del"],
            "tnm": {"M": "M1b"},
        }
        inferred = self.engine.infer(self.pack, state)
        self.assertEqual(inferred["histology_group"], "nsclc")
        self.assertTrue(inferred["driver_positive"])
        self.assertEqual(inferred["driver_gene"], "EGFR")
        self.assertEqual(inferred["stage_group"], "stage_iv")
        self.assertEqual(inferred["treatment_intent"], "palliative")
        self.assertNotIn("histology_group", state)

    def test_stage_iv_egfr_positive_matches_targeted_treatment_rule(self) -> None:
        state = self.engine.infer(
            self.pack,
            {
                "histology": "adenocarcinoma",
                "biomarkers": ["egfr_ex19del"],
                "tnm": {"M": "M1b"},
            },
        )
        result = self.engine.evaluate(self.pack, state, rule_groups={"treatment_rules"})
        match = result.by_rule_id("LC_TX_NSCLC_STAGE_IV_DRIVER_POSITIVE")
        self.assertIsNotNone(match)
        self.assertIn("matched_targeted_therapy", match.output["recommend"])
        self.assertEqual(match.rule_group, "treatment_rules")
        self.assertTrue(match.explain)

    def test_missing_histology_emits_scenario_branches(self) -> None:
        result = self.engine.evaluate(self.pack, {}, rule_groups={"scenario_rules"})
        match = result.by_rule_id("LC_SC_HISTOLOGY_UNKNOWN")
        self.assertIsNotNone(match)
        branch_ids = [branch["branch_id"] for branch in match.output["generate_branches"]]
        self.assertEqual(branch_ids, ["possible_nsclc", "possible_sclc"])

    def test_present_histology_suppresses_missing_histology_scenario(self) -> None:
        result = self.engine.evaluate(self.pack, {"histology": "adenocarcinoma"}, rule_groups={"scenario_rules"})
        self.assertIsNone(result.by_rule_id("LC_SC_HISTOLOGY_UNKNOWN"))

    def test_unresectable_stage_iii_after_chemoradiation_matches_durvalumab(self) -> None:
        state = {
            "histology_group": "nsclc",
            "stage_group": "stage_iiib",
            "chemoradiation_completed": True,
            "progression_after_chemoradiation": False,
            "biomarkers": [],
            "pd_l1_tps": 10,
            "no_immunotherapy_contraindication": True,
        }
        result = self.engine.evaluate(self.pack, state, rule_groups={"treatment_rules"})
        self.assertIn("LC_TX_NSCLC_STAGE_III_DURVALUMAB_CONSOLIDATION", result.matched_rule_ids)


if __name__ == "__main__":
    unittest.main()
