"""Shell and equipment advisor."""
import streamlit as st

from components.input_forms import render_fields, render_section
from components.result_display import (page_header, render_missing, render_recommendations,
                                       render_suppressed, render_summary)
from components.session import run_engine

CATEGORIES = ["shell", "defense"]


def render():
    page_header("Shell & equipment advisor", "Durability, weight, insurance, spells and stowaways.", "🐚")
    with st.expander("Your current shell", expanded=True):
        render_section("shell", "shell")
        render_section("shell_meta", "shell")
    with st.expander("What you are facing and your resources"):
        render_fields(["encounter_type", "attack_style", "umami_charges"], "shell")
        render_fields(["stowaways_equipped"], "shell", columns=1)

    result = run_engine()
    st.divider()
    render_summary(result)
    shell_state = result.derived_facts.get("shell_condition")
    if shell_state:
        st.markdown(f"**Inferred shell condition:** `{shell_state}` "
                    f"(from rule {result.memory.origin('shell_condition')})")
    st.subheader("Recommendations")
    render_recommendations(result, CATEGORIES)
    render_suppressed(result, CATEGORIES)
    render_missing(result)
