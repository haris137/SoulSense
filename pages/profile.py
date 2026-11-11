"""Player profile and gameplay questionnaire."""
import streamlit as st

from components.input_forms import SECTIONS, render_section
from components.result_display import page_header
from components.session import get_facts


def render():
    page_header("Player profile", "Answers here are shared with every advisor. "
                "Leave anything you do not know on 'Not sure'.", "🧭")
    tab1, tab2, tab3 = st.tabs(["About you", "Abilities & gear", "Stats"])
    with tab1:
        render_section("profile", "profile")
    with tab2:
        render_section("abilities", "profile", columns=1)
        st.caption("Only the skills, adaptations and stowaways the knowledge base reasons about are listed.")
    with tab3:
        render_section("stats", "profile")

    asked = SECTIONS["profile"] + SECTIONS["abilities"] + SECTIONS["stats"]
    given = sum(1 for name in asked if name in get_facts())
    st.progress(given / len(asked), text=f"Profile completeness: {given} of {len(asked)} questions answered")
    st.success("Now open any advisor in the sidebar - it will use these answers.")
