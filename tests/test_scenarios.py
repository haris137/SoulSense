"""Scenario tests: realistic player situations and the rules they must trigger."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.inference_engine import InferenceEngine
from knowledge_base.rules import RULES
from knowledge_base.scenarios import SCENARIOS

ENGINE = InferenceEngine(RULES)


def run(name):
    return ENGINE.run(SCENARIOS[name]["facts"])


class ScenarioTests(unittest.TestCase):
    def test_new_crab_facing_nephro(self):
        r = run("New crab facing Nephro")
        for rid in ("SHL-09", "BOS-05", "CMB-04", "BOS-04", "PRG-01"):
            self.assertIn(rid, r.fired_ids)
        self.assertNotIn("SHL-07", r.fired_ids)   # shells are locked -> not "pick one up"
        self.assertNotIn("DEF-02", r.fired_ids)   # that rule needs shells unlocked
        self.assertNotIn("DEF-01", r.fired_ids)   # newcomers are not told about stamina habits

    def test_failing_shell_chains_through_derived_fact(self):
        r = run("Blocker with a cracking shell")
        self.assertEqual(r.derived_facts["shell_condition"], "critical")
        self.assertIn("SHL-04", r.recommendation_ids)
        self.assertEqual(r.firing("SHL-04").depends_on_rules, ["SHL-01"])
        self.assertEqual(r.recommendations[0].rule.severity, "critical")
        self.assertIn("SHL-05", r.fired_ids)              # Kintsugi known

    def test_defense_mode_conflict_is_resolved_by_priority(self):
        r = run("Blocker with a cracking shell")
        # CMB-03 (block) is not even eligible: shell is critical.  Parry rule needs a worn shell.
        self.assertNotIn("CMB-03", r.fired_ids)
        facts = dict(SCENARIOS["Blocker with a cracking shell"]["facts"], shell_durability_pct=50)
        r2 = ENGINE.run(facts)
        self.assertIn("DEF-06", r2.recommendation_ids)    # conserve worn shell wins
        self.assertIn("DEF-07", r2.fired_ids)
        suppressed = {s.rule.id: w.rule.id for s, w in r2.suppressed}
        self.assertEqual(suppressed.get("CMB-03"), "DEF-06")

    def test_specificity_beats_generality(self):
        facts = {"experience": "veteran", "playstyle": "aggressor", "game_stage": "early", "vit": 2}
        r = ENGINE.run(facts)
        self.assertIn("PRG-02", r.recommendation_ids)
        self.assertNotIn("PRG-01", r.recommendation_ids)
        self.assertEqual({s.rule.id: w.rule.id for s, w in r.suppressed}["PRG-01"], "PRG-02")

    def test_low_on_everything_at_firth(self):
        r = run("Low on everything at Firth")
        self.assertEqual(r.derived_facts["hp_state"], "low")
        for rid in ("SRV-08", "SRV-07", "BOS-16"):
            self.assertIn(rid, r.fired_ids)

    def test_rich_and_far_from_checkpoint(self):
        r = run("Rich and far from a checkpoint")
        self.assertTrue(r.derived_facts["carrying_much"])
        for rid in ("PRG-10", "ADP-08"):
            self.assertIn(rid, r.fired_ids)
        self.assertNotIn("PRG-09", r.fired_ids)

    def test_voltai_phase_two_replaces_generic_phase_advice(self):
        r = run("Voltai with a heavy shell")
        self.assertIn("BOS-03", r.recommendation_ids)
        self.assertNotIn("BOS-02", r.recommendation_ids)
        for rid in ("CMB-08", "BOS-12"):
            self.assertIn(rid, r.fired_ids)

    def test_heal_or_rest_specific_rule_wins(self):
        facts = {"player_hp_pct": 20, "near_moon_snail": True, "heartkelp_pods": 2,
                 "tough_enemies_cleared": True}
        r = ENGINE.run(facts)
        self.assertIn("SRV-06", r.recommendation_ids)
        self.assertNotIn("SRV-05", r.recommendation_ids)
        self.assertEqual(r.firing("SRV-06").reason[:8], "highest ")

    def test_build_problem_scenario(self):
        r = run("Unhappy with the build")
        for rid in ("PRG-08", "PRG-11", "PRG-13", "ADP-09", "DEF-04"):
            self.assertIn(rid, r.fired_ids)

    def test_empty_input_is_handled_gracefully(self):
        r = ENGINE.run({})
        self.assertEqual(r.recommendations, [])
        self.assertGreater(len(r.unevaluated), 0)
        self.assertTrue(r.missing_inputs())

    def test_partial_input_reports_what_to_answer_next(self):
        r = ENGINE.run({"enemy_count": 4, "playstyle": "blocker"})
        self.assertIn("CMB-02", r.fired_ids)
        self.assertIn("shell_durability_pct", r.missing_inputs())

    def test_unsure_answers_are_ignored(self):
        r = ENGINE.run({"player_hp_pct": None, "playstyle": "blocker"})
        self.assertNotIn("player_hp_pct", r.memory.snapshot())

    def test_all_scenarios_produce_advice(self):
        for name in SCENARIOS:
            self.assertGreater(len(run(name).recommendations), 0, name)


if __name__ == "__main__":
    unittest.main()
