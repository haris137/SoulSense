"""Knowledge base / rules explorer."""
import os

import streamlit as st

from components.result_display import page_header
from components.session import load_facts
from engine.rule_analysis import synthesize_example
from knowledge_base.facts import FACT_SCHEMA
from knowledge_base.rules import CATEGORIES, RULES

MECHANICS = os.path.join(os.path.dirname(os.path.dirname(__file__)), "knowledge_base", "game_mechanics.md")


def render():
    page_header("Knowledge base", f"All {len(RULES)} rules, the facts they use and the evidence behind them.", "📚")
    tab_rules, tab_facts, tab_mech, tab_how = st.tabs(["Rules", "Facts", "Verified mechanics", "How inference works"])

    with tab_rules:
        c1, c2, c3 = st.columns([2, 2, 3])
        cat = c1.selectbox("Category", ["All"] + list(CATEGORIES.values()), key="w:kb:cat")
        kind = c2.selectbox("Type", ["All", "Advice rules", "Derivation rules"], key="w:kb:kind")
        text = c3.text_input("Search text", key="w:kb:text").lower()
        shown = [r for r in RULES
                 if (cat == "All" or CATEGORIES[r.category] == cat)
                 and (kind == "All" or (kind == "Derivation rules") == r.is_derivation or
                      (kind == "Advice rules" and r.advice))
                 and (not text or text in (r.id + r.name + (r.advice or "")).lower())]
        st.caption(f"{len(shown)} of {len(RULES)} rules")
        st.dataframe([{"ID": r.id, "Category": CATEGORIES[r.category], "Name": r.name,
                       "Priority": r.priority, "Tests": r.specificity, "Severity": r.severity,
                       "Group": r.group or "-", "Evidence": r.basis,
                       "IF": r.conditions.describe()} for r in shown],
                     hide_index=True)
        if shown:
            chosen = st.selectbox("Inspect a rule", [f"{r.id} - {r.name}" for r in shown], key="w:kb:pick")
            rule = next(r for r in shown if chosen.startswith(r.id))
            st.code(rule.if_then(), language=None)
            st.markdown(f"**Why:** {rule.rationale}")
            st.markdown(f"**Evidence:** {rule.basis}" + (f" · mechanics {', '.join(rule.sources)}" if rule.sources else ""))
            example = synthesize_example(rule, RULES, FACT_SCHEMA)
            if example:
                st.markdown("**Example input that fires this rule:**")
                st.json(example)
                if st.button("Load this example into my session", key="w:kb:load"):
                    load_facts(example)

    with tab_facts:
        st.caption("Inputs the user can provide. Derived facts are produced by derivation rules.")
        st.dataframe([{"Fact": s.name, "Question": s.label, "Type": s.kind,
                       "Values": ", ".join(s.option_values) if s.options else f"{s.min}-{s.max}"}
                      for s in FACT_SCHEMA.values()], hide_index=True)

    with tab_mech:
        try:
            with open(MECHANICS, encoding="utf-8") as fh:
                st.markdown(fh.read())
        except OSError:
            st.error("game_mechanics.md not found.")

    with tab_how:
        st.markdown("""
**Forward chaining** repeats *match → resolve → act*:

1. **Match** - every rule not yet fired is tested against working memory. Rules whose conditions are true form the *conflict set*.
2. **Resolve** - one rule is chosen: highest **priority**, then most **specific** (most tests), then earliest in the knowledge base.
3. **Act** - the rule fires: it may infer new facts (which can make other rules match) and/or add a recommendation.

The loop stops when nothing new matches. Each rule fires at most once, so it always terminates.

**Unknown answers** use three-valued logic (true / false / unknown). A rule with an unknown condition does not fire; the app tells you which answers would let it be evaluated.

**Recommendation conflicts** - rules that answer the same question (e.g. *block or dodge?*) share a group; only the best-ranked advice is shown and the rest are listed as overruled.
""")
