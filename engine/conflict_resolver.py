"""
conflict_resolver.py - decides what happens when MANY rules match at once.

Two different conflicts exist in a rule-based system, so there are two
documented strategies.

1) AGENDA CONFLICT  (which matched rule fires next?)
   In every forward-chaining cycle the engine builds the CONFLICT SET: all
   rules that match the current facts and have not fired yet.  Exactly one
   rule is selected, using this ordering (classic OPS5-style strategies):

       a. PRIORITY     higher priority number first   (salience)
       b. SPECIFICITY  more elementary conditions first
                       (a rule that tests more facts is "more specific")
       c. RULE ORDER   earlier position in the knowledge base first
                       (deterministic final tie-break)

   "Refraction" (a rule fires at most once per run) is enforced by the
   engine, so the loop always ends.

2) RECOMMENDATION CONFLICT  (two pieces of advice that contradict)
   Rules that answer the SAME question ("block or dodge?", "heavy or light
   shell?", "heal with a pod or rest?") share a `group` name.  After
   inference, only the best-ranked advice per group (same ordering a-c above)
   is shown as primary; the others are listed as SUPPRESSED together with the
   rule that overruled them, so nothing is hidden from the user.
"""

from typing import Dict, List, Sequence, Tuple

from engine.rule import SEVERITY_ORDER


class ConflictResolver:
    def __init__(self, rules: Sequence):
        # position in the knowledge base = last tie-break
        self._position: Dict[str, int] = {r.id: i for i, r in enumerate(rules)}

    # ---------------------------------------------------------------- ranking
    def rank_key(self, rule) -> Tuple[int, int, int]:
        """Lower tuple = better.  (-priority, -specificity, kb position)."""
        return (-rule.priority, -rule.specificity, self._position.get(rule.id, 10**6))

    def select(self, conflict_set: Sequence) -> Tuple[object, str]:
        """Pick the rule to fire.  Returns (rule, human-readable reason)."""
        ranked = sorted(conflict_set, key=self.rank_key)
        best = ranked[0]
        if len(ranked) == 1:
            return best, "only matching rule"
        second = ranked[1]
        if best.priority != second.priority:
            return best, f"highest priority ({best.priority})"
        if best.specificity != second.specificity:
            return best, (f"same priority ({best.priority}); more specific "
                          f"({best.specificity} tests vs {second.specificity})")
        return best, "same priority and specificity; earlier in the knowledge base"

    # ------------------------------------------------- recommendation conflicts
    def resolve_recommendations(self, firings: Sequence) -> Tuple[List, List[Tuple[object, object]]]:
        """
        Split fired rules that carry advice into
          kept        - advice shown as primary recommendations (sorted)
          suppressed  - list of (suppressed_firing, winning_firing)
        """
        with_advice = [f for f in firings if f.rule.advice]
        winners: Dict[str, object] = {}
        for firing in with_advice:
            group = firing.rule.group
            if group is None:
                continue
            current = winners.get(group)
            if current is None or self.rank_key(firing.rule) < self.rank_key(current.rule):
                winners[group] = firing

        kept, suppressed = [], []
        for firing in with_advice:
            group = firing.rule.group
            if group is None or winners[group] is firing:
                kept.append(firing)
            else:
                suppressed.append((firing, winners[group]))

        kept.sort(key=lambda f: (SEVERITY_ORDER[f.rule.severity],) + self.rank_key(f.rule))
        suppressed.sort(key=lambda pair: self.rank_key(pair[0].rule))
        return kept, suppressed
