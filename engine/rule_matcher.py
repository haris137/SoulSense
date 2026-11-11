"""
rule_matcher.py - evaluates rule CONDITIONS against working memory.

A condition is a small tree:

    Cond(fact, operator, value)   a single test, e.g. shell_durability_pct <= 30
    AllOf(c1, c2, ...)            logical AND
    AnyOf(c1, c2, ...)            logical OR
    Not(c)                        logical NOT

Evaluation uses THREE-VALUED logic so that missing answers are handled
gracefully:

    True   the condition holds
    False  the condition does not hold
    None   UNKNOWN - a needed fact has not been provided

    AND: any False -> False, else any unknown -> unknown, else True
    OR : any True  -> True,  else any unknown -> unknown, else False
    NOT: swaps True/False, unknown stays unknown

A rule only FIRES when its condition evaluates to True.  Rules that evaluate
to unknown are reported to the user as "could not be evaluated - answer X to
unlock them".

Every evaluation also returns human-readable lines (the "why did this match"
part of the explanation facility).
"""

from dataclasses import dataclass, field
from typing import Any, List, Optional, Set

# --------------------------------------------------------------------------
# Operators.  "a" is the fact's current value, "b" is the value in the rule.
# --------------------------------------------------------------------------
OPERATORS = {
    "==":           lambda a, b: a == b,
    "!=":           lambda a, b: a != b,
    "<":            lambda a, b: a < b,
    "<=":           lambda a, b: a <= b,
    ">":            lambda a, b: a > b,
    ">=":           lambda a, b: a >= b,
    "in":           lambda a, b: a in b,                    # scalar fact in a list
    "not in":       lambda a, b: a not in b,
    "contains":     lambda a, b: b in a,                    # list fact contains item
    "not contains": lambda a, b: b not in a,
    "contains any": lambda a, b: any(x in a for x in b),
    "is true":      lambda a, b: a is True,
    "is false":     lambda a, b: a is False,
    "count ==":     lambda a, b: len(a) == b,               # length of a list fact
    "count >=":     lambda a, b: len(a) >= b,
    "count <":      lambda a, b: len(a) < b,
}

# Used by the rule-analysis tool to negate a leaf condition.
NEGATED_OPERATOR = {
    "==": "!=", "!=": "==", "<": ">=", "<=": ">", ">": "<=", ">=": "<",
    "in": "not in", "not in": "in", "contains": "not contains",
    "not contains": "contains", "is true": "is false", "is false": "is true",
    "count >=": "count <", "count <": "count >=",
}


def _fmt(value: Any) -> str:
    """Compact text for a value in explanations."""
    if isinstance(value, str):
        return repr(value)
    return str(value)


@dataclass
class MatchResult:
    """Outcome of evaluating a condition tree."""
    status: Optional[bool]                            # True / False / None (unknown)
    lines: List[str] = field(default_factory=list)    # explanation lines
    unknown_facts: Set[str] = field(default_factory=set)


# --------------------------------------------------------------------------
# Condition classes
# --------------------------------------------------------------------------
class Condition:
    """Base class - every node can evaluate itself and describe itself."""

    def evaluate(self, memory) -> MatchResult:           # pragma: no cover
        raise NotImplementedError

    def describe(self) -> str:                           # pragma: no cover
        raise NotImplementedError

    def fact_names(self) -> Set[str]:                    # pragma: no cover
        raise NotImplementedError

    def size(self) -> int:                               # pragma: no cover
        """Number of leaf tests = the rule's 'specificity'."""
        raise NotImplementedError


class Cond(Condition):
    """A single test: <fact> <operator> <value>."""

    def __init__(self, fact: str, op: str, value: Any = None):
        if op not in OPERATORS:
            raise ValueError(f"Unknown operator {op!r}")
        self.fact, self.op, self.value = fact, op, value

    def describe(self) -> str:
        if self.op in ("is true", "is false"):
            return f"{self.fact} {self.op}"
        if self.op.startswith("count"):
            return f"count({self.fact}) {self.op[len('count '):]} {self.value}"
        return f"{self.fact} {self.op} {_fmt(self.value)}"

    def fact_names(self) -> Set[str]:
        return {self.fact}

    def size(self) -> int:
        return 1

    def evaluate(self, memory) -> MatchResult:
        actual = memory.get(self.fact)
        if actual is None:
            return MatchResult(None, [f"?  {self.describe()}   [fact unknown]"], {self.fact})
        try:
            ok = bool(OPERATORS[self.op](actual, self.value))
        except TypeError:        # e.g. comparing text with a number -> no match
            ok = False
        mark = "OK" if ok else "NO"
        return MatchResult(ok, [f"{mark}  {self.describe()}   [actual: {_fmt(actual)}]"])


class _Group(Condition):
    label = ""

    def __init__(self, *children: Condition):
        if not children:
            raise ValueError("A condition group needs at least one child")
        self.children = list(children)

    def fact_names(self) -> Set[str]:
        names: Set[str] = set()
        for child in self.children:
            names |= child.fact_names()
        return names

    def size(self) -> int:
        return sum(child.size() for child in self.children)

    def describe(self) -> str:
        joined = f" {self.label} ".join(c.describe() for c in self.children)
        return f"({joined})"

    def _collect(self, memory):
        results = [child.evaluate(memory) for child in self.children]
        lines = [f"{self.label} of:"]
        unknown: Set[str] = set()
        for res in results:
            lines.extend("   " + line for line in res.lines)
            unknown |= res.unknown_facts
        return results, lines, unknown


class AllOf(_Group):
    """Logical AND."""
    label = "AND"

    def evaluate(self, memory) -> MatchResult:
        results, lines, unknown = self._collect(memory)
        statuses = [r.status for r in results]
        if any(s is False for s in statuses):
            status = False
        elif any(s is None for s in statuses):
            status = None
        else:
            status = True
        return MatchResult(status, lines, unknown if status is None else set())


class AnyOf(_Group):
    """Logical OR."""
    label = "OR"

    def evaluate(self, memory) -> MatchResult:
        results, lines, unknown = self._collect(memory)
        statuses = [r.status for r in results]
        if any(s is True for s in statuses):
            status = True
        elif any(s is None for s in statuses):
            status = None
        else:
            status = False
        return MatchResult(status, lines, unknown if status is None else set())


class Not(Condition):
    """Logical NOT."""

    def __init__(self, child: Condition):
        self.child = child

    def describe(self) -> str:
        return f"NOT {self.child.describe()}"

    def fact_names(self) -> Set[str]:
        return self.child.fact_names()

    def size(self) -> int:
        return self.child.size()

    def evaluate(self, memory) -> MatchResult:
        res = self.child.evaluate(memory)
        status = None if res.status is None else (not res.status)
        return MatchResult(status, ["NOT of:"] + ["   " + l for l in res.lines],
                           res.unknown_facts)


# --------------------------------------------------------------------------
# Short helper constructors - they keep the rule definitions readable.
# --------------------------------------------------------------------------
def eq(f, v):          return Cond(f, "==", v)
def ne(f, v):          return Cond(f, "!=", v)
def lt(f, v):          return Cond(f, "<", v)
def le(f, v):          return Cond(f, "<=", v)
def gt(f, v):          return Cond(f, ">", v)
def ge(f, v):          return Cond(f, ">=", v)
def one_of(f, vals):   return Cond(f, "in", list(vals))
def not_one_of(f, vs): return Cond(f, "not in", list(vs))
def has(f, item):      return Cond(f, "contains", item)
def lacks(f, item):    return Cond(f, "not contains", item)
def has_any(f, items): return Cond(f, "contains any", list(items))
def is_true(f):        return Cond(f, "is true")
def is_false(f):       return Cond(f, "is false")
def count_eq(f, n):    return Cond(f, "count ==", n)
def count_ge(f, n):    return Cond(f, "count >=", n)
def count_lt(f, n):    return Cond(f, "count <", n)
def AND(*c):           return AllOf(*c)
def OR(*c):            return AnyOf(*c)
def NOT(c):            return Not(c)


class RuleMatcher:
    """Thin wrapper so the engine depends on an object, not on functions."""

    def match(self, rule, memory) -> MatchResult:
        return rule.conditions.evaluate(memory)
