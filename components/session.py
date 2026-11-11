"""
session.py - glue between Streamlit's session state and the expert system.

The player's answers live in ONE dictionary, st.session_state["facts"].
Every page reads and writes the same dictionary, so the profile entered on one
page is automatically used by every advisor.  A missing key means "not sure".
"""

import streamlit as st

from engine.inference_engine import InferenceEngine
from knowledge_base.rules import RULES

_ENGINE = InferenceEngine(RULES)       # built once per server process


def get_facts() -> dict:
    return st.session_state.setdefault("facts", {})


def run_engine():
    """Run forward chaining on the current answers."""
    return _ENGINE.run(dict(get_facts()))


def load_facts(new_facts: dict) -> None:
    """Replace all answers (used by the example buttons) and refresh the widgets."""
    st.session_state["facts"] = dict(new_facts)
    for key in [k for k in st.session_state.keys() if str(k).startswith("w:")]:
        del st.session_state[key]          # forget old widget values
    st.rerun()


def clear_facts() -> None:
    load_facts({})
