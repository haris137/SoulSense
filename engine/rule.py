"""
rule.py - the data structure for one IF-THEN rule.

IF   <conditions>            (a condition tree, see rule_matcher.py)
THEN <asserts>               new facts added to working memory   (optional)
     <advice>                a recommendation shown to the player (optional)

Extra metadata makes every rule explainable and defensible:
  priority   0-100, used by conflict resolution (higher fires first)
  severity   critical / warning / tip / info  (how the UI colours the advice)
  group      rules that give ALTERNATIVE answers to the same question share a
             group; only the best-ranked advice of a group is shown
  basis      mechanic = follows directly from a verified game mechanic
             guide    = widely repeated community-guide recommendation
             tactic   = general action-combat practice applied to a mechanic
             design   = a classification rule written by the system designer
                        (e.g. 'durability <= 30 % means critical')
  sources    ids of the facts in knowledge_base/game_mechanics.md (e.g. M-12)
  rationale  one or two sentences: why the conclusion follows
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

from engine.rule_matcher import Condition

SEVERITY_ORDER = {"critical": 0, "warning": 1, "tip": 2, "info": 3}
BASES = ("mechanic", "guide", "tactic", "design")


@dataclass
class Rule:
    id: str
    category: str
    name: str
    conditions: Condition
    priority: int = 50
    advice: Optional[str] = None
    asserts: Dict[str, Any] = field(default_factory=dict)
    severity: str = "tip"
    group: Optional[str] = None
    basis: str = "mechanic"
    sources: Tuple[str, ...] = ()
    rationale: str = ""

    @property
    def specificity(self) -> int:
        """How many elementary tests the rule has (more = more specific)."""
        return self.conditions.size()

    @property
    def is_derivation(self) -> bool:
        return bool(self.asserts)

    def if_then(self) -> str:
        """One-line IF-THEN rendering used by the UI and the documentation."""
        then_parts = []
        if self.asserts:
            then_parts.append("infer " + ", ".join(f"{k} = {v!r}" for k, v in self.asserts.items()))
        if self.advice:
            then_parts.append("advise: " + self.advice)
        return f"IF {self.conditions.describe()} THEN " + " AND ".join(then_parts)
