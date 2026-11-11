"""Combat advisor: encounter-level tactics."""
import streamlit as st

from components.input_forms import render_section
from components.result_display import (page_header, render_missing, render_recommendations,
                                       render_suppressed, render_summary)
from components.session import run_engine

CATEGORIES = ["combat", "weapon", "defense"]


def render():
    page_header("Combat advisor", "Describe the fight you are in and get tactics.", "⚔️")
    with st.expander("The enemy", expanded=True):
        render_section("encounter", "combat")
    with st.expander("You and your shell", expanded=True):
        render_section("state", "combat")
        render_section("shell", "combat")

    result = run_engine()
    st.divider()
    render_summary(result)
    st.subheader("Recommendations")
    render_recommendations(result, CATEGORIES)
    render_suppressed(result, CATEGORIES)
    render_missing(result)
    st.caption("Uses your Player profile too (playstyle, skills, stowaways).")
