"""Home / dashboard page."""
import streamlit as st

from components.result_display import page_header
from components.session import get_facts, load_facts
from knowledge_base.rules import CATEGORIES, DERIVED_FACTS, RULES, rules_by_category
from knowledge_base.scenarios import SCENARIOS


def render():
    page_header("SOULSENSE", "A rule-based combat & build advisor for Another Crab's Treasure.", "🦀")

    grouped = rules_by_category()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("IF-THEN rules", len(RULES))
    c2.metric("Knowledge categories", len(CATEGORIES))
    c3.metric("Inferred fact types", len(DERIVED_FACTS))
    c4.metric("Your answers", len(get_facts()))

    st.subheader("How it works")
    a, b, c = st.columns(3)
    a.markdown("<div class='ss-step'><b>1. Tell it your situation</b><br>Fill in your profile and the "
               "advisor pages. Every answer becomes a <i>fact</i> in working memory. "
               "'Not sure' is always allowed.</div>", unsafe_allow_html=True)
    b.markdown("<div class='ss-step'><b>2. Forward chaining</b><br>The inference engine matches facts "
               "against the rules, resolves conflicts by priority and specificity, fires rules and "
               "chains their conclusions.</div>", unsafe_allow_html=True)
    c.markdown("<div class='ss-step'><b>3. Advice with reasons</b><br>Each recommendation shows the rule "
               "that fired, the values that matched and the game mechanic behind it.</div>",
               unsafe_allow_html=True)

    st.subheader("Try an example player")
    name = st.selectbox("Pick a scenario", list(SCENARIOS), key="w:home:scenario")
    st.caption(SCENARIOS[name]["description"])
    if st.button("Load this scenario", type="primary"):
        load_facts(SCENARIOS[name]["facts"])
    st.caption("After loading, open **Expert diagnosis** (sidebar) to see the full reasoning.")

    st.subheader("What the knowledge base covers")
    cols = st.columns(2)
    for i, (key, title) in enumerate(CATEGORIES.items()):
        cols[i % 2].markdown(f"- **{title}** - {len(grouped[key])} rules")

    st.info("Knowledge comes from published guides, reviews and patch notes (see "
            "`knowledge_base/game_mechanics.md`). Game patches can change numbers - "
            "confirm important details in-game.")
