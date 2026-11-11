"""Unit tests for the inference engine, matcher, memory and conflict resolver.
Run with:  python -m unittest discover -s tests -v
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.conflict_resolver import ConflictResolver
from engine.inference_engine import InferenceEngine
from engine.rule import Rule
from engine.rule_matcher import (AND, NOT, OR, count_ge, eq, ge, has, has_any, is_false,
                                 is_true, lacks, le, lt, ne, one_of)
from engine.working_memory import ADDED, BLOCKED, UNCHANGED, WorkingMemory


def rule(rid, cond, **kw):
    return Rule(rid, "test", rid, cond, **kw)


class WorkingMemoryTests(unittest.TestCase):
    def test_none_is_unknown(self):
        mem = WorkingMemory({"a": 1, "b": None})
        self.assertTrue(mem.has("a"))
        self.assertFalse(mem.has("b"))

    def test_user_facts_cannot_be_overwritten_by_rules(self):
        mem = WorkingMemory({"x": 1})
        self.assertEqual(mem.assert_inferred("x", 2, "R-1"), BLOCKED)
        self.assertEqual(mem.get("x"), 1)

    def test_inferred_fact_added_then_unchanged_then_blocked(self):
        mem = WorkingMemory()
        self.assertEqual(mem.assert_inferred("y", "a", "R-1"), ADDED)
        self.assertEqual(mem.assert_inferred("y", "a", "R-2"), UNCHANGED)
        self.assertEqual(mem.assert_inferred("y", "b", "R-3"), BLOCKED)
        self.assertEqual(mem.origin("y"), "R-1")

    def test_origin(self):
        mem = WorkingMemory({"u": 5})
        self.assertEqual(mem.origin("u"), "user")
        self.assertIsNone(mem.origin("missing"))


class MatcherTests(unittest.TestCase):
    def status(self, cond, facts):
        return cond.evaluate(WorkingMemory(facts)).status

    def test_comparison_operators(self):
        f = {"n": 5}
        self.assertTrue(self.status(eq("n", 5), f))
        self.assertTrue(self.status(ne("n", 4), f))
        self.assertTrue(self.status(lt("n", 6), f))
        self.assertTrue(self.status(le("n", 5), f))
        self.assertTrue(self.status(ge("n", 5), f))
        self.assertFalse(self.status(lt("n", 5), f))

    def test_membership_and_list_operators(self):
        f = {"s": "a", "L": ["x", "y"]}
        self.assertTrue(self.status(one_of("s", ["a", "b"]), f))
        self.assertTrue(self.status(has("L", "x"), f))
        self.assertTrue(self.status(lacks("L", "z"), f))
        self.assertTrue(self.status(has_any("L", ["q", "y"]), f))
        self.assertTrue(self.status(count_ge("L", 2), f))

    def test_booleans(self):
        self.assertTrue(self.status(is_true("b"), {"b": True}))
        self.assertFalse(self.status(is_true("b"), {"b": False}))
        self.assertTrue(self.status(is_false("b"), {"b": False}))

    def test_and_or_not(self):
        f = {"a": 1, "b": 2}
        self.assertTrue(self.status(AND(eq("a", 1), eq("b", 2)), f))
        self.assertFalse(self.status(AND(eq("a", 1), eq("b", 3)), f))
        self.assertTrue(self.status(OR(eq("a", 9), eq("b", 2)), f))
        self.assertFalse(self.status(OR(eq("a", 9), eq("b", 9)), f))
        self.assertTrue(self.status(NOT(eq("a", 9)), f))

    def test_unknown_three_valued_logic(self):
        f = {"a": 1}
        self.assertIsNone(self.status(eq("missing", 1), f))
        self.assertFalse(self.status(AND(eq("a", 2), eq("missing", 1)), f))   # False wins
        self.assertIsNone(self.status(AND(eq("a", 1), eq("missing", 1)), f))
        self.assertTrue(self.status(OR(eq("a", 1), eq("missing", 1)), f))     # True wins
        self.assertIsNone(self.status(OR(eq("a", 2), eq("missing", 1)), f))
        self.assertIsNone(self.status(NOT(eq("missing", 1)), f))

    def test_type_mismatch_is_false_not_crash(self):
        self.assertFalse(self.status(lt("a", 5), {"a": "text"}))

    def test_specificity_counts_leaf_tests(self):
        self.assertEqual(AND(eq("a", 1), OR(eq("b", 1), eq("c", 1))).size(), 3)

    def test_explanation_lines_show_actual_values(self):
        res = le("hp", 30).evaluate(WorkingMemory({"hp": 20}))
        self.assertIn("actual: 20", res.lines[0])


class ConflictResolverTests(unittest.TestCase):
    def test_priority_then_specificity_then_order(self):
        hi = rule("A", eq("x", 1), priority=80)
        lo = rule("B", eq("x", 1), priority=20)
        spec = rule("C", AND(eq("x", 1), eq("y", 1)), priority=20)
        same = rule("D", eq("x", 1), priority=20)
        res = ConflictResolver([lo, spec, same, hi])
        self.assertEqual(res.select([lo, hi])[0], hi)
        self.assertEqual(res.select([lo, spec])[0], spec)         # more specific
        self.assertEqual(res.select([same, lo])[0], lo)           # earlier in KB
        self.assertIn("priority", res.select([lo, hi])[1])
        self.assertIn("specific", res.select([lo, spec])[1])

    def test_group_keeps_only_best_advice(self):
        a = rule("A", eq("x", 1), priority=50, advice="a", group="g")
        b = rule("B", eq("x", 1), priority=70, advice="b", group="g")
        c = rule("C", eq("x", 1), priority=10, advice="c")
        engine = InferenceEngine([a, b, c])
        result = engine.run({"x": 1})
        self.assertEqual(set(result.recommendation_ids), {"B", "C"})
        self.assertEqual([(s.rule.id, w.rule.id) for s, w in result.suppressed], [("A", "B")])


class EngineTests(unittest.TestCase):
    def test_forward_chaining_two_steps(self):
        rules = [rule("ADV", eq("cond", "critical"), advice="swap"),
                 rule("DER", le("dur", 30), priority=100, asserts={"cond": "critical"})]
        result = InferenceEngine(rules).run({"dur": 10})
        self.assertEqual(result.fired_ids, ["DER", "ADV"])        # derivation first
        self.assertEqual(result.firing("ADV").depends_on_rules, ["DER"])
        self.assertEqual(result.derived_facts, {"cond": "critical"})

    def test_chain_of_three(self):
        rules = [rule("R3", eq("c", 3), advice="done"),
                 rule("R2", eq("b", 2), asserts={"c": 3}),
                 rule("R1", eq("a", 1), asserts={"b": 2})]
        result = InferenceEngine(rules).run({"a": 1})
        self.assertEqual(result.fired_ids, ["R1", "R2", "R3"])

    def test_each_rule_fires_once(self):
        rules = [rule("R", eq("a", 1), advice="x")]
        self.assertEqual(InferenceEngine(rules).run({"a": 1}).fired_ids, ["R"])

    def test_no_match_no_firing(self):
        result = InferenceEngine([rule("R", eq("a", 1), advice="x")]).run({"a": 2})
        self.assertEqual(result.fired_ids, [])
        self.assertEqual(result.unevaluated, [])        # false, not unknown

    def test_conflicting_derivations_first_ranked_wins(self):
        rules = [rule("LOW", ge("v", 0), priority=10, asserts={"k": "low"}),
                 rule("HIGH", ge("v", 0), priority=90, asserts={"k": "high"})]
        result = InferenceEngine(rules).run({"v": 1})
        self.assertEqual(result.derived_facts["k"], "high")
        self.assertEqual(result.firing("LOW").blocked, {"k": "low"})

    def test_missing_inputs_traced_through_derived_facts(self):
        rules = [rule("DER", le("dur", 30), priority=100, asserts={"cond": "critical"}),
                 rule("ADV", eq("cond", "critical"), advice="swap")]
        result = InferenceEngine(rules).run({})
        self.assertEqual(result.missing_inputs()["dur"], 2)    # both rules wait for 'dur'

    def test_user_fact_blocks_inference(self):
        rules = [rule("DER", le("dur", 30), asserts={"cond": "critical"})]
        result = InferenceEngine(rules).run({"dur": 10, "cond": "fine"})
        self.assertEqual(result.derived_facts, {})
        self.assertEqual(result.firing("DER").blocked, {"cond": "critical"})

    def test_explain_text(self):
        rules = [rule("R", eq("a", 1), advice="do it", priority=70)]
        text = InferenceEngine(rules).run({"a": 1}).explain("R")
        self.assertIn("IF", text)
        self.assertIn("do it", text)
        self.assertIn("priority 70", text)

    def test_recommendations_sorted_by_severity(self):
        rules = [rule("TIP", eq("a", 1), advice="t", severity="tip", priority=99),
                 rule("CRIT", eq("a", 1), advice="c", severity="critical", priority=1)]
        result = InferenceEngine(rules).run({"a": 1})
        self.assertEqual(result.recommendation_ids, ["CRIT", "TIP"])


if __name__ == "__main__":
    unittest.main()
