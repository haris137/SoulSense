"""Integrity tests for the knowledge base (rules, facts, mechanics document)."""
import os
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from engine.inference_engine import InferenceEngine
from engine.rule import BASES, SEVERITY_ORDER
from engine.rule_analysis import synthesize_example, to_alternatives
from engine.rule_matcher import Cond
from knowledge_base.facts import FACT_SCHEMA
from knowledge_base.rules import CATEGORIES, DERIVED_FACTS, RULES, rules_by_category


def leaves(cond):
    return [leaf for alt in to_alternatives(cond) for leaf in alt]


class KnowledgeBaseTests(unittest.TestCase):
    def test_at_least_50_rules(self):
        self.assertGreaterEqual(len(RULES), 50)

    def test_unique_ids_with_category_prefix(self):
        ids = [r.id for r in RULES]
        self.assertEqual(len(ids), len(set(ids)))
        for r in RULES:
            self.assertRegex(r.id, r"^[A-Z]{3}-\d{2}$")

    def test_all_eight_categories_have_enough_rules(self):
        for key, rules in rules_by_category().items():
            self.assertIn(key, CATEGORIES)
            self.assertGreaterEqual(len(rules), 6, key)

    def test_each_rule_concludes_something(self):
        for r in RULES:
            self.assertTrue(r.advice or r.asserts, r.id)
            self.assertIn(r.severity, SEVERITY_ORDER, r.id)
            self.assertIn(r.basis, BASES, r.id)
            self.assertTrue(0 <= r.priority <= 100, r.id)
            self.assertTrue(r.rationale, r.id)

    def test_conditions_only_use_known_facts(self):
        for r in RULES:
            for fact in r.conditions.fact_names():
                self.assertTrue(fact in FACT_SCHEMA or fact in DERIVED_FACTS,
                                f"{r.id} uses unknown fact {fact}")

    def test_condition_values_exist_in_schema(self):
        """Catches typos such as 'fast_relentles' that would silently never match."""
        for r in RULES:
            for fact, op, value in leaves(r.conditions):
                if fact in DERIVED_FACTS:
                    values = value if isinstance(value, list) else [value]
                    for v in values:
                        if op in ("==", "!=", "in", "not in"):
                            self.assertIn(v, DERIVED_FACTS[fact], f"{r.id}: {fact}={v}")
                    continue
                spec = FACT_SCHEMA[fact]
                if spec.kind in ("select", "multi") and op not in ("count >=", "count <", "count =="):
                    values = value if isinstance(value, list) else [value]
                    for v in values:
                        self.assertIn(v, spec.option_values, f"{r.id}: {fact} -> {v!r}")
                if spec.kind == "bool":
                    self.assertIn(op, ("is true", "is false"), f"{r.id}: {fact}")
                if spec.kind in ("int", "number"):
                    self.assertIsInstance(value, int, f"{r.id}: {fact}")

    def test_derived_facts_are_inferred_by_some_rule(self):
        asserted = {}
        for r in RULES:
            for fact, value in r.asserts.items():
                asserted.setdefault(fact, set()).add(value)
        for fact, values in DERIVED_FACTS.items():
            self.assertIn(fact, asserted, f"nobody infers {fact}")
            self.assertEqual(set(values), asserted[fact], fact)
        for fact in asserted:
            self.assertNotIn(fact, FACT_SCHEMA, f"{fact} would clash with a user input")

    def test_groups_have_at_least_two_rules(self):
        groups = {}
        for r in RULES:
            if r.group:
                groups.setdefault(r.group, []).append(r.id)
        for name, ids in groups.items():
            self.assertGreaterEqual(len(ids), 2, name)

    def test_no_duplicate_advice_text(self):
        texts = [r.advice for r in RULES if r.advice]
        self.assertEqual(len(texts), len(set(texts)))

    def test_every_rule_cites_existing_mechanics(self):
        with open(os.path.join(ROOT, "knowledge_base", "game_mechanics.md"), encoding="utf-8") as fh:
            known = set(re.findall(r"^## (M-\d+)", fh.read(), flags=re.M))
        for r in RULES:
            if r.basis != "design":
                self.assertTrue(r.sources, f"{r.id} cites no mechanic")
            for src in r.sources:
                self.assertIn(src, known, f"{r.id} cites unknown {src}")

    def test_every_rule_is_reachable(self):
        """No dead rules: a satisfying input exists and the engine really fires the rule."""
        engine = InferenceEngine(RULES)
        for r in RULES:
            example = synthesize_example(r, RULES, FACT_SCHEMA)
            self.assertIsNotNone(example, f"{r.id} cannot be satisfied")
            self.assertIn(r.id, engine.run(example).fired_ids, r.id)

    def test_forms_cover_every_fact_used(self):
        """Every user fact referenced by a rule can be entered in some page form."""
        import importlib
        sys.modules.setdefault("streamlit", __import__("unittest.mock").mock.MagicMock())
        from components import input_forms
        covered = set(input_forms.all_form_facts())
        for r in RULES:
            for fact in r.conditions.fact_names():
                if fact in FACT_SCHEMA:
                    self.assertIn(fact, covered, f"{r.id}: no form asks for {fact}")


if __name__ == "__main__":
    unittest.main()
