"""
result_display.py - shows inference results and the explanation facility.

For each recommendation the user can open "Why this advice?" to see
  * the rule id, priority and specificity,
  * every condition with the actual value that made it match,
  * the verified mechanic(s) behind it,
  * which other rules' conclusions it relied on (the chain),
  * why it won the conflict-resolution step.
"""

import html
import os

import streamlit as st

from knowledge_base.facts import FACT_SCHEMA
from knowledge_base.rules import CATEGORIES

SEVERITY_LABEL = {"critical": "Critical", "warning": "Important", "tip": "Tip", "info": "Good to know"}
BASIS_LABEL = {"mechanic": "Verified mechanic", "guide": "Community-guide advice",
               "tactic": "General tactic on a verified mechanic",
               "design": "Designer classification"}


def inject_css():
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "style.css")
    try:
        with open(path, encoding="utf-8") as fh:
            st.markdown(f"<style>{fh.read()}</style>", unsafe_allow_html=True)
    except OSError:
        pass                                    # styling is optional


def page_header(title: str, subtitle: str, icon: str = ""):
    st.markdown(f"<div class='ss-hero'><h1>{icon} {html.escape(title)}</h1>"
                f"<p>{html.escape(subtitle)}</p></div>", unsafe_allow_html=True)


def render_summary(result):
    facts = len(result.memory.user_facts())
    cols = st.columns(4)
    cols[0].metric("Answers given", facts)
    cols[1].metric("Rules fired", f"{len(result.firings)} / {result.rules_total}")
    cols[2].metric("Recommendations", len(result.recommendations))
    cols[3].metric("Inference cycles", result.cycles)


def _card(firing):
    rule = firing.rule
    sev = rule.severity
    st.markdown(
        f"<div class='ss-card ss-{sev}'>"
        f"<div class='ss-meta'><span class='ss-badge ss-b-{sev}'>{SEVERITY_LABEL[sev]}</span>"
        f"<span class='ss-id'>{rule.id}</span><span class='ss-cat'>{html.escape(CATEGORIES[rule.category])}</span></div>"
        f"<div class='ss-title'>{html.escape(rule.name)}</div>"
        f"<div class='ss-text'>{html.escape(rule.advice)}</div></div>",
        unsafe_allow_html=True)
    with st.expander(f"Why this advice?  ({rule.id})"):
        explain_firing(firing)


def explain_firing(firing):
    rule = firing.rule
    st.markdown(f"**Rule {rule.id} - {rule.name}**  ·  priority {rule.priority}  ·  "
                f"specificity {rule.specificity}  ·  fired in cycle {firing.cycle}")
    st.markdown("**IF** (every line shows the actual value that was tested)")
    st.code("\n".join(firing.match.lines), language=None)
    st.markdown("**THEN** " + (rule.advice or ""))
    if firing.asserted:
        st.markdown("Inferred: " + ", ".join(f"`{k} = {v}`" for k, v in firing.asserted.items()))
    st.markdown(f"**Why it follows:** {rule.rationale}")
    st.markdown(f"**Evidence type:** {BASIS_LABEL[rule.basis]}"
                + (f"  ·  mechanics: {', '.join(rule.sources)}" if rule.sources else ""))
    if firing.depends_on_rules:
        st.markdown("**Chain:** this rule used conclusions inferred by "
                    + ", ".join(f"`{r}`" for r in firing.depends_on_rules))
    st.markdown(f"**Conflict resolution:** selected because of *{firing.reason}*.")
    if len(firing.candidates) > 1:
        st.caption("Rules matching in that cycle (best first): " + ", ".join(firing.candidates))


def render_recommendations(result, categories=None, empty_hint=True):
    items = result.recommendations_for(categories)
    if not items:
        if empty_hint:
            st.info("No recommendation yet - fill in more answers above. "
                    "Anything marked 'Not sure' is simply skipped.")
        return
    for firing in items:
        _card(firing)


def render_suppressed(result, categories=None):
    rows = [(s, w) for s, w in result.suppressed
            if not categories or s.rule.category in categories]
    if not rows:
        return
    with st.expander(f"Advice overruled by conflict resolution ({len(rows)})"):
        st.caption("These rules matched too, but another rule answering the same question "
                   "ranked higher (priority, then specificity, then rule order).")
        for loser, winner in rows:
            st.markdown(f"- `{loser.rule.id}` *{loser.rule.name}* was overruled by "
                        f"`{winner.rule.id}` *{winner.rule.name}* (group `{loser.rule.group}`)")


def render_missing(result, limit=6):
    missing = result.missing_inputs()
    if not missing:
        return
    with st.expander(f"Answer more to unlock {len(result.unevaluated)} rules that could not be evaluated"):
        st.caption("Most useful missing answers (number of rules waiting for each):")
        for fact, count in missing.most_common(limit):
            label = FACT_SCHEMA[fact].label if fact in FACT_SCHEMA else fact
            st.markdown(f"- **{label}** - {count} rule(s)")


def render_trace(result):
    """The full forward-chaining trace, one row per rule firing."""
    rows = []
    for f in result.firings:
        rows.append({
            "Cycle": f.cycle,
            "Rule": f.rule.id,
            "Name": f.rule.name,
            "Priority": f.rule.priority,
            "Specificity": f.rule.specificity,
            "Won because": f.reason,
            "Inferred": ", ".join(f"{k}={v}" for k, v in f.asserted.items()) or "-",
            "Competing rules": max(len(f.candidates) - 1, 0),
        })
    if rows:
        st.dataframe(rows, hide_index=True)
    else:
        st.info("No rule fired yet.")


def render_working_memory(result):
    user = result.memory.user_facts()
    inferred = result.memory.inferred_facts()
    left, right = st.columns(2)
    with left:
        st.markdown("**Answers (user facts)**")
        st.dataframe([{"Fact": FACT_SCHEMA[k].label if k in FACT_SCHEMA else k,
                       "Value": FACT_SCHEMA[k].label_for(v) if k in FACT_SCHEMA else str(v)}
                      for k, v in user.items()] or [{"Fact": "-", "Value": "-"}],
                     hide_index=True)
    with right:
        st.markdown("**Conclusions (inferred facts)**")
        st.dataframe([{"Fact": k, "Value": str(v), "Inferred by": result.memory.origin(k)}
                      for k, v in inferred.items()] or [{"Fact": "-", "Value": "-", "Inferred by": "-"}],
                     hide_index=True)
