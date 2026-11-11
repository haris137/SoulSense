"""
working_memory.py - the expert system's "blackboard".

Working memory stores every FACT the system currently knows:
  * USER facts      - answers typed into the Streamlit forms.
  * INFERRED facts  - conclusions asserted by rules during forward chaining.

Design decisions (all of them are documented in the README):
  * A fact whose value is None means "the user is not sure".  We simply do not
    store it, so the matcher treats the fact as UNKNOWN (three-valued logic).
  * Memory is MONOTONIC: facts are only added, never retracted or overwritten.
    This guarantees that forward chaining terminates.
  * User facts are ground truth: a rule can never overwrite them.
  * If two rules try to assert different values for the same inferred fact,
    the first one (which is the higher-ranked rule) wins and the second
    attempt is reported as "blocked".  The explanation facility shows this.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

USER = "user"
INFERRED = "inferred"

# Results of assert_inferred()
ADDED = "added"
UNCHANGED = "unchanged"
BLOCKED = "blocked"


@dataclass
class FactRecord:
    """One stored fact plus where it came from."""
    name: str
    value: Any
    source: str                      # USER or INFERRED
    rule_id: Optional[str] = None    # which rule inferred it (if INFERRED)
    order: int = 0                   # insertion order, used for tracing


class WorkingMemory:
    """Stores facts and remembers who asserted them."""

    def __init__(self, initial_facts: Optional[Dict[str, Any]] = None):
        self._facts: Dict[str, FactRecord] = {}
        self._counter = 0
        self.log: List[str] = []     # human-readable history of changes
        for name, value in (initial_facts or {}).items():
            self.assert_user_fact(name, value)

    # ------------------------------------------------------------------ writes
    def assert_user_fact(self, name: str, value: Any) -> bool:
        """Store an answer given by the user.  None ("not sure") is ignored."""
        if value is None:
            return False
        self._counter += 1
        self._facts[name] = FactRecord(name, value, USER, None, self._counter)
        self.log.append(f"USER   asserted {name} = {value!r}")
        return True

    def assert_inferred(self, name: str, value: Any, rule_id: str) -> str:
        """
        Store a conclusion drawn by a rule.

        Returns ADDED, UNCHANGED (same value already present) or BLOCKED
        (a different value is already present - user answers and
        higher-ranked rules win).
        """
        existing = self._facts.get(name)
        if existing is not None:
            if existing.value == value:
                return UNCHANGED
            self.log.append(
                f"{rule_id} tried {name} = {value!r} but {existing.value!r} "
                f"was already asserted by {existing.rule_id or 'the user'} -> blocked")
            return BLOCKED
        self._counter += 1
        self._facts[name] = FactRecord(name, value, INFERRED, rule_id, self._counter)
        self.log.append(f"{rule_id} inferred {name} = {value!r}")
        return ADDED

    # ------------------------------------------------------------------- reads
    def has(self, name: str) -> bool:
        return name in self._facts

    def get(self, name: str, default: Any = None) -> Any:
        record = self._facts.get(name)
        return record.value if record else default

    def origin(self, name: str) -> Optional[str]:
        """'user', or the id of the rule that inferred the fact, or None."""
        record = self._facts.get(name)
        if record is None:
            return None
        return USER if record.source == USER else record.rule_id

    def record(self, name: str) -> Optional[FactRecord]:
        return self._facts.get(name)

    def snapshot(self) -> Dict[str, Any]:
        return {n: r.value for n, r in self._facts.items()}

    def user_facts(self) -> Dict[str, Any]:
        return {n: r.value for n, r in self._facts.items() if r.source == USER}

    def inferred_facts(self) -> Dict[str, Any]:
        return {n: r.value for n, r in self._facts.items() if r.source == INFERRED}

    def __len__(self) -> int:
        return len(self._facts)
