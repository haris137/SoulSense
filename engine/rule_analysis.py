"""
rule_analysis.py - static analysis of the knowledge base.

Given a rule, `synthesize_example()` builds a small set of user facts that
makes the rule's conditions TRUE (it is a tiny constraint solver with
back-tracking).  It is used for

  * a unit test proving that no rule is "dead" (every rule can fire),
  * the "example input" shown in the Knowledge Explorer and in docs/RULES.md.

Conditions are first turned into alternatives (disjunctive normal form):
AND combines alternatives, OR offers a choice.  Facts that are INFERRED by
other rules are handled by also satisfying the conditions of the rule that
infers them.
"""

import itertools
from typing import Any, Dict, List, Optional, Sequence, Tuple

from engine.rule_matcher import (AllOf, AnyOf, Cond, NEGATED_OPERATOR, Not, OPERATORS)

Leaf = Tuple[str, str, Any]      # (fact, operator, value)


def to_alternatives(cond) -> List[List[Leaf]]:
    """Condition tree -> list of alternatives, each a list of leaf tests."""
    if isinstance(cond, Cond):
        return [[(cond.fact, cond.op, cond.value)]]
    if isinstance(cond, AllOf):
        parts = [to_alternatives(c) for c in cond.children]
        return [sum(combo, []) for combo in itertools.product(*parts)]
    if isinstance(cond, AnyOf):
        return [alt for c in cond.children for alt in to_alternatives(c)]
    if isinstance(cond, Not):
        child = cond.child
        if not isinstance(child, Cond) or child.op not in NEGATED_OPERATOR:
            raise ValueError("Analysis supports NOT only around a simple test")
        return [[(child.fact, NEGATED_OPERATOR[child.op], child.value)]]
    raise TypeError(cond)


def _candidates(spec) -> List[Any]:
    """Values worth trying for one user fact."""
    if spec.kind == "bool":
        return [True, False]
    if spec.kind == "select":
        return list(spec.option_values)
    values = {spec.min, spec.max, spec.default}
    values.update(range(spec.min, min(spec.max, spec.min + 40) + 1, max(1, spec.step)))
    for threshold in (1, 2, 3, 4, 5, 8, 25, 30, 31, 35, 36, 40, 50, 60, 61, 80, 2000, 2500, 3000, 5000):
        if spec.min <= threshold <= spec.max:
            values.add(threshold)
    return sorted(v for v in values if v is not None)


def _multi_value(spec, leaves: Sequence[Leaf]) -> Optional[List[str]]:
    required: List[str] = []
    forbidden = set()
    min_len, max_len = 0, 10**6
    for _, op, val in leaves:
        if op == "contains":
            required.append(val)
        elif op == "not contains":
            forbidden.add(val)
        elif op == "contains any":
            required.append(val[0])
        elif op == "count >=":
            min_len = max(min_len, val)
        elif op == "count <":
            max_len = min(max_len, val - 1)
        elif op == "count ==":
            min_len, max_len = max(min_len, val), min(max_len, val)
    chosen = list(dict.fromkeys(required))
    for option in spec.option_values:
        if len(chosen) >= min_len:
            break
        if option not in forbidden and option not in chosen:
            chosen.append(option)
    ok = all(OPERATORS[op](chosen, val) for _, op, val in leaves)
    return chosen if ok and min_len <= len(chosen) <= max_len else None


def _solve_fact(spec, leaves: Sequence[Leaf]):
    if spec.kind == "multi":
        return _multi_value(spec, leaves)
    for value in _candidates(spec):
        if all(OPERATORS[op](value, val) for _, op, val in leaves):
            return value
    return None


def _solve(leaves: List[Leaf], schema, derivers, depth=0) -> Optional[Dict[str, Any]]:
    if depth > 6:
        return None
    # expand one derived-fact constraint at a time
    for fact in {f for f, _, _ in leaves}:
        if fact in schema:
            continue
        mine = [l for l in leaves if l[0] == fact]
        rest = [l for l in leaves if l[0] != fact]
        for value, rule in derivers.get(fact, []):
            if all(OPERATORS[op](value, v) for _, op, v in mine):
                for alt in to_alternatives(rule.conditions):
                    found = _solve(rest + alt, schema, derivers, depth + 1)
                    if found is not None:
                        return found
        return None
    result: Dict[str, Any] = {}
    for fact in {f for f, _, _ in leaves}:
        value = _solve_fact(schema[fact], [l for l in leaves if l[0] == fact])
        if value is None:
            return None
        result[fact] = value
    return result


def synthesize_example(rule, rules: Sequence, schema) -> Optional[Dict[str, Any]]:
    """User facts that satisfy `rule`, or None if the rule is unsatisfiable."""
    derivers: Dict[str, List[Tuple[Any, Any]]] = {}
    for r in rules:
        for fact, value in r.asserts.items():
            derivers.setdefault(fact, []).append((value, r))
    for alternative in to_alternatives(rule.conditions):
        found = _solve(list(alternative), schema, derivers)
        if found is not None:
            return found
    return None
