"""Progression and survival advisor."""
import streamlit as st

from components.input_forms import render_section
from components.result_display import (page_header, render_missing, render_recommendations,
                                       render_suppressed, render_summary)
from components.session import run_engine


def render():
    page_header("Progression & survival", "Stats, skills, resources, healing and staying alive.", "📈")
    tab_prog, tab_surv = st.tabs(["Progression", "Survival"])
    with tab_prog:
        render_section("stats", "prog")
        render_section("economy", "prog")
        render_section("build", "prog")
    with tab_surv:
        render_section("state", "surv")
        render_section("survival", "surv")
        render_section("shell", "surv")
        render_section("shell_meta", "surv")

    result = run_engine()
    st.divider()
    render_summary(result)
    st.subheader("Progression & abilities")
    render_recommendations(result, ["progression", "adaptations"])
    st.subheader("Healing, resources & survival")
    render_recommendations(result, ["survival"], empty_hint=False)
    render_suppressed(result, ["progression", "adaptations", "survival"])
    render_missing(result)
