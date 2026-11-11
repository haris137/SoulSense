"""
SOULSENSE - Another Crab's Treasure Combat & Build Advisor
Entry point.  Run locally with:   streamlit run app.py
"""
import streamlit as st

st.set_page_config(page_title="SOULSENSE - Another Crab's Treasure Advisor",
                   page_icon="🦀", layout="wide", initial_sidebar_state="expanded")

from components.navigation import build_navigation, render_sidebar_footer   # noqa: E402
from components.result_display import inject_css                            # noqa: E402

inject_css()
page = build_navigation()
render_sidebar_footer()
page.run()
