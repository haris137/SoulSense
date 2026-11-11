"""
inference_engine.py - the FORWARD-CHAINING inference engine.

Forward chaining is DATA-DRIVEN: start from the known facts and keep applying
rules until nothing new can be concluded.  The classic
"recognise - resolve - act" cycle is used:

    repeat
        1. MATCH    evaluate every not-yet-fired rule against working memory
                    -> conflict set = rules whose conditions are TRUE
        2. RESOLVE  the ConflictResolver selects ONE rule from the conflict set
        3. ACT      fire it: assert its inferred facts, record its advice
    until the conflict set is empty

Because a fired rule may add new facts, rules that did not match before may
match in a later cycle - that is the "chaining".  For example:

    cycle 1  SHL-01  shell_durability_pct <= 30   -> shell_condition = 'critical'
    cycle 2  SHL-04  shell_condition == 'critical' -> "swap your shell now"

Termination: each rule fires at most once (refraction) and memory is
monotonic, so the loop ends after at most len(rules) cycles.

Missing information: conditions that depend on unknown facts evaluate to
"unknown" (three-valued logic, see rule_matcher.py).  Those rules simply do
not fire, and the result lists which user answers would let them be evaluated.
"""

from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

from engine.conflict_resolver import ConflictResolver
from engine.rule_matcher import MatchResult, RuleMatcher
from engine.working_memory import ADDED, BLOCKED, WorkingMemory


@dataclass
class Firing:
    """Everything we recorded about one rule firing (the explanation record)."""
    cycle: int
    rule: object
    match: MatchResult
    asserted: Dict[str, Any]                 # facts newly added by this firing
    blocked: Dict[str, Any]                  # facts it tried to add but could not
    candidates: List[str]                    # ids that were in the conflict set
    reason: str                              # why this rule won the conflict
    used_facts: Dict[str, Tuple[Any, str]]   # fact -> (value, origin) it relied on

    @property
    def depends_on_rules(self) -> List[str]:
        """Rules whose conclusions this rule used (the 'chain')."""
        return sorted({origin for _, origin in self.used_facts.values() if origin != "user"})


@dataclass
class InferenceResult:
    firings: List[Firing]
    recommendations: List[Firing]                       # primary advice, sorted
    suppressed: List[Tuple[Firing, Firing]]             # (overruled, winner)
    unevaluated: List[Tuple[object, List[str]]]         # (rule, missing user facts)
    memory: WorkingMemory
    cycles: int
    rules_total: int

    # ---- convenience views used by the UI and the tests
    @property
    def fired_ids(self) -> List[str]:
        return [f.rule.id for f in self.firings]

    @property
    def recommendation_ids(self) -> List[str]:
        return [f.rule.id for f in self.recommendations]

    @property
    def derived_facts(self) -> Dict[str, Any]:
        return self.memory.inferred_facts()

    def firing(self, rule_id: str) -> Optional[Firing]:
        return next((f for f in self.firings if f.rule.id == rule_id), None)

    def recommendations_for(self, categories: Optional[Sequence[str]]) -> List[Firing]:
        if not categories:
            return list(self.recommendations)
        return [f for f in self.recommendations if f.rule.category in categories]

    def missing_inputs(self) -> Counter:
        """fact name -> number of rules that are waiting for that answer."""
        counter: Counter = Counter()
        for _, facts in self.unevaluated:
            counter.update(facts)
        return counter

    def explain(self, rule_id: str) -> str:
        """Plain-text 'why' and 'how' for one fired rule (CLI / PDF friendly)."""
        f = self.firing(rule_id)
        if f is None:
            return f"Rule {rule_id} did not fire."
        r = f.rule
        out = [f"{r.id}  {r.name}   [cycle {f.cycle}, priority {r.priority}, "
               f"specificity {r.specificity}]",
               f"  IF   {r.conditions.describe()}"]
        out += ["       " + line for line in f.match.lines]
        if r.asserts:
            out.append("  INFER " + ", ".join(f"{k} = {v!r}" for k, v in f.asserted.items()))
        if r.advice:
            out.append(f"  THEN  {r.advice}")
        out.append(f"  WHY   {r.rationale}")
        out.append(f"  WON   {f.reason}  (conflict set: {', '.join(f.candidates)})")
        if f.depends_on_rules:
            out.append("  CHAIN uses conclusions of " + ", ".join(f.depends_on_rules))
        return "\n".join(out)


class InferenceEngine:
    """Runs forward chaining over a list of Rule objects."""

    def __init__(self, rules: Sequence, resolver: Optional[ConflictResolver] = None,
                 matcher: Optional[RuleMatcher] = None):
        self.rules = list(rules)
        self.resolver = resolver or ConflictResolver(self.rules)
        self.matcher = matcher or RuleMatcher()
        # fact name -> rules that can infer it (used to trace missing inputs)
        self._derivations: Dict[str, List[object]] = {}
        for rule in self.rules:
            for fact in rule.asserts:
                self._derivations.setdefault(fact, []).append(rule)

    # --------------------------------------------------------------------- run
    def run(self, user_facts: Dict[str, Any]) -> InferenceResult:
        memory = WorkingMemory(user_facts)
        fired: Dict[str, Firing] = {}
        firings: List[Firing] = []
        cycle = 0

        while True:
            # 1. MATCH -------------------------------------------------------
            conflict_set = []
            for rule in self.rules:
                if rule.id in fired:
                    continue                     # refraction
                if self.matcher.match(rule, memory).status is True:
                    conflict_set.append(rule)
            if not conflict_set:
                break

            # 2. RESOLVE -----------------------------------------------------
            cycle += 1
            chosen, reason = self.resolver.select(conflict_set)

            # 3. ACT ---------------------------------------------------------
            match = self.matcher.match(chosen, memory)     # lines for the explanation
            used = {name: (memory.get(name), memory.origin(name))
                    for name in chosen.conditions.fact_names() if memory.has(name)}
            asserted, blocked = {}, {}
            for fact, value in chosen.asserts.items():
                outcome = memory.assert_inferred(fact, value, chosen.id)
                if outcome == ADDED:
                    asserted[fact] = value
                elif outcome == BLOCKED:
                    blocked[fact] = value
            firing = Firing(cycle, chosen, match, asserted, blocked,
                            [r.id for r in sorted(conflict_set, key=self.resolver.rank_key)],
                            reason, used)
            fired[chosen.id] = firing
            firings.append(firing)

            if cycle > len(self.rules) + 1:      # safety net, cannot normally happen
                break

        kept, suppressed = self.resolver.resolve_recommendations(firings)
        return InferenceResult(firings, kept, suppressed,
                               self._find_unevaluated(memory, fired), memory,
                               cycle, len(self.rules))

    # ------------------------------------------------------- missing information
    def _find_unevaluated(self, memory, fired) -> List[Tuple[object, List[str]]]:
        """Rules that never fired because a needed answer is missing."""
        waiting = []
        for rule in self.rules:
            if rule.id in fired:
                continue
            result = self.matcher.match(rule, memory)
            if result.status is not None:
                continue                         # definitely false -> not applicable
            missing = set()
            for fact in result.unknown_facts:
                missing |= self._root_unknown(memory, fact, frozenset())
            if missing:
                waiting.append((rule, sorted(missing)))
        return waiting

    def _root_unknown(self, memory, fact: str, seen: frozenset) -> set:
        """
        Which USER-answerable facts are missing behind `fact`?
        A derived fact (e.g. shell_condition) is traced back through the rules
        that would infer it to the user inputs those rules are waiting for.
        """
        derivers = self._derivations.get(fact)
        if not derivers:
            return {fact}                        # a plain user input
        if fact in seen:
            return set()
        seen = seen | {fact}
        roots: set = set()
        for rule in derivers:
            res = rule.conditions.evaluate(memory)
            if res.status is None:               # only unknown branches matter
                for unknown in res.unknown_facts:
                    roots |= self._root_unknown(memory, unknown, seen)
        return roots
