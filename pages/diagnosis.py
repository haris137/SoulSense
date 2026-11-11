"""Expert diagnosis: the full result with the complete explanation facility."""
import streamlit as st

from components.result_display import (explain_firing, page_header, render_missing,
                                       render_recommendations, render_suppressed, render_summary,
                                       render_trace, render_working_memory)
from components.session import get_facts, load_facts, run_engine
from knowledge_base.rules import CATEGORIES
from knowledge_base.scenarios import SCENARIOS


def render():
    page_header("Expert diagnosis", "Everything the system concluded from all your answers - and how.", "🩺")
    if not get_facts():
        st.warning("No answers yet. Fill in the Player profile and advisors, or load an example:")
        name = st.selectbox("Example player", list(SCENARIOS), key="w:diag:scenario")
        if st.button("Load example", type="primary"):
            load_facts(SCENARIOS[name]["facts"])

    result = run_engine()
    render_summary(result)

    tabs = st.tabs(["Recommendations", "Forward-chaining trace", "Working memory",
                    "Conflict resolution", "All fired rules"])
    with tabs[0]:
        shown = False
        for key, title in CATEGORIES.items():
            items = result.recommendations_for([key])
            if items:
                shown = True
                st.markdown(f"### {title}")
                render_recommendations(result, [key], empty_hint=False)
        if not shown:
            st.info("No recommendations yet.")
        render_missing(result, limit=8)
    with tabs[1]:
        st.caption("One row per rule firing, in the order the engine fired them. Derivation rules "
                   "(priority 100) fire first so that the facts they infer can trigger advice rules.")
        render_trace(result)
    with tabs[2]:
        render_working_memory(result)
    with tabs[3]:
        st.markdown("**Strategy:** priority, then specificity (number of tests), then knowledge-base order. "
                    "Rules answering the same question share a *group*; only the best advice per group is shown.")
        if result.suppressed:
            render_suppressed(result)
        else:
            st.info("No advice was overruled for these answers.")
    with tabs[4]:
        for firing in result.firings:
            with st.expander(f"{firing.rule.id} - {firing.rule.name}"):
                explain_firing(firing)
