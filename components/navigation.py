"""
navigation.py - sidebar navigation and page registry.

Streamlit's st.navigation() (v1.36+) lets us register pages as plain Python
functions.  Using it also turns off Streamlit's automatic "pages/" folder
scanning, so the sidebar shows exactly the structure defined here.
"""

import streamlit as st

from components.session import clear_facts, get_facts


def build_navigation():
    from pages import (boss_advisor, combat_advisor, diagnosis, home, knowledge_explorer,
                       profile, progression_advisor, shell_advisor)

    pages = {
        "Start": [
            st.Page(home.render, title="Home", icon="🦀", url_path="home", default=True),
            st.Page(profile.render, title="Player profile", icon="🧭", url_path="profile"),
        ],
        "Advisors": [
            st.Page(combat_advisor.render, title="Combat advisor", icon="⚔️", url_path="combat"),
            st.Page(shell_advisor.render, title="Shell & equipment", icon="🐚", url_path="shells"),
            st.Page(boss_advisor.render, title="Boss preparation", icon="👑", url_path="boss"),
            st.Page(progression_advisor.render, title="Progression & survival", icon="📈", url_path="progression"),
        ],
        "Expert system": [
            st.Page(diagnosis.render, title="Expert diagnosis", icon="🩺", url_path="diagnosis"),
            st.Page(knowledge_explorer.render, title="Knowledge base", icon="📚", url_path="knowledge"),
        ],
    }
    return st.navigation(pages)


def render_sidebar_footer():
    facts = get_facts()
    with st.sidebar:
        st.divider()
        st.caption(f"Answers stored this session: **{len(facts)}**")
        if st.button("Reset all answers"):
            clear_facts()
        st.caption("SOULSENSE is a rule-based expert system for *Another Crab's Treasure*. "
                   "Fan-made and unaffiliated with Aggro Crab.")
