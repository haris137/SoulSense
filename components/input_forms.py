"""
input_forms.py - builds Streamlit input widgets from the fact schema.

Each fact (knowledge_base/facts.py) is rendered with the widget that suits its
kind: dropdown, yes/no radio, slider, number box or multi-select.  Every widget
offers "Not sure" - the answer is then left out of working memory and the
inference engine treats it as UNKNOWN instead of guessing.
"""

import streamlit as st

from components.session import get_facts
from knowledge_base.facts import FACT_SCHEMA

NOT_SURE = "Not sure"

# Which facts each questionnaire section asks for.
SECTIONS = {
    "profile":    ["experience", "playstyle", "game_stage", "current_area",
                   "shells_unlocked", "defeated_topoda"],
    "abilities":  ["skills_known", "adaptations_known", "adaptations_equipped",
                   "stowaways_equipped"],
    "stats":      ["vit", "res", "atk", "msg"],
    "encounter":  ["encounter_type", "attack_style", "enemy_count", "enemy_hp_pct",
                   "stagger_pct", "enemy_capsized"],
    "state":      ["player_hp_pct", "umami_charges", "deaths_in_a_row", "near_moon_snail"],
    "shell":      ["shell_worn", "shell_durability_pct", "shell_weight", "nearby_shells"],
    "shell_meta": ["shell_spell_role", "shell_favorite", "shell_insured"],
    "boss":       ["target_boss"],
    "economy":    ["microplastics", "umami_crystals", "shark_eggs", "stowaway_capacity_free"],
    "build":      ["main_problem", "unhappy_with_build"],
    "survival":   ["heartkelp_pods", "heartkelp_sprouts_found", "tough_enemies_cleared",
                   "unrecovered_microplastics", "open_to_assist", "parry_trouble"],
}


def all_form_facts():
    """Every fact that at least one form asks for (checked by a unit test)."""
    return {name for names in SECTIONS.values() for name in names}


def _store(name, value):
    facts = get_facts()
    if value is None:
        facts.pop(name, None)
    else:
        facts[name] = value


def render_fact(name: str, prefix: str):
    """Draw one input and store its value in the shared answers dictionary."""
    spec = FACT_SCHEMA[name]
    current = get_facts().get(name)
    key = f"w:{prefix}:{name}"
    help_text = spec.help or None

    if spec.kind == "select":
        labels = [NOT_SURE] + [label for _, label in spec.options]
        index = 0 if current not in spec.option_values else spec.option_values.index(current) + 1
        choice = st.selectbox(spec.label, labels, index=index, key=key, help=help_text)
        value = None if choice == NOT_SURE else spec.option_values[labels.index(choice) - 1]

    elif spec.kind == "bool":
        labels = [NOT_SURE, "Yes", "No"]
        index = 0 if current is None else (1 if current else 2)
        choice = st.radio(spec.label, labels, index=index, horizontal=True, key=key, help=help_text)
        value = None if choice == NOT_SURE else (choice == "Yes")

    elif spec.kind in ("int", "number"):
        left, right = st.columns([5, 2])
        unsure = right.checkbox(NOT_SURE, value=current is None, key=key + ":unsure")
        start = spec.default if current is None else current
        start = min(max(start if start is not None else spec.min, spec.min), spec.max)
        if spec.kind == "int":
            number = left.slider(spec.label, spec.min, spec.max, int(start), spec.step,
                                 key=key, disabled=unsure, help=help_text)
        else:
            number = left.number_input(spec.label, spec.min, spec.max, int(start), spec.step,
                                       key=key, disabled=unsure, help=help_text)
        value = None if unsure else int(number)

    else:  # multi - an empty list means "none of these"
        labels = [label for _, label in spec.options]
        selected = [dict(spec.options)[v] for v in (current or []) if v in dict(spec.options)]
        chosen = st.multiselect(spec.label, labels, default=selected, key=key, help=help_text)
        by_label = {label: value for value, label in spec.options}
        value = [by_label[label] for label in chosen]

    _store(name, value)


def render_fields(names, prefix: str, columns: int = 2):
    """Lay several facts out in a grid of columns."""
    cols = st.columns(columns)
    for i, name in enumerate(names):
        with cols[i % columns]:
            render_fact(name, prefix)


def render_section(section: str, prefix: str, columns: int = 2):
    render_fields(SECTIONS[section], prefix, columns)
