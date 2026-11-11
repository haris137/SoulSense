"""Boss preparation advisor."""
import streamlit as st

from components.input_forms import render_fields, render_section
from components.result_display import (page_header, render_missing, render_recommendations,
                                       render_suppressed, render_summary)
from components.session import get_facts, run_engine

CATEGORIES = ["boss", "shell", "defense", "weapon"]


def render():
    page_header("Boss preparation", "Pick a boss and get preparation tips for your current setup.", "👑")
    get_facts()["encounter_type"] = "boss"          # this page is always about a boss fight
    st.caption("Using this page marks the encounter as a boss fight.")
    render_section("boss", "boss", columns=1)
    with st.expander("Boss fight state", expanded=True):
        render_fields(["enemy_hp_pct", "deaths_in_a_row", "attack_style", "heartkelp_pods",
                       "umami_charges"], "boss")
    with st.expander("Your shell"):
        render_section("shell", "boss")

    result = run_engine()
    st.divider()
    render_summary(result)
    st.subheader("Recommendations")
    render_recommendations(result, CATEGORIES)
    render_suppressed(result, CATEGORIES)
    render_missing(result)
