"""
Command-line demo of the inference engine (no Streamlit needed).

    python tools/run_cli.py                      # list scenarios
    python tools/run_cli.py "Low on everything at Firth"
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.inference_engine import InferenceEngine
from knowledge_base.rules import RULES
from knowledge_base.scenarios import SCENARIOS


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in SCENARIOS:
        print("Scenarios:")
        for name, data in SCENARIOS.items():
            print(f'  "{name}" - {data["description"]}')
        return
    scenario = SCENARIOS[sys.argv[1]]
    result = InferenceEngine(RULES).run(scenario["facts"])
    print(f'Scenario: {sys.argv[1]}\n{scenario["description"]}\n')
    print(f"{len(result.firings)} rules fired in {result.cycles} cycles; "
          f"inferred facts: {result.derived_facts}\n")
    print("=== RECOMMENDATIONS (most urgent first) ===")
    for f in result.recommendations:
        print(f"[{f.rule.severity.upper():8}] {f.rule.id}: {f.rule.advice}")
    if result.suppressed:
        print("\n=== OVERRULED BY CONFLICT RESOLUTION ===")
        for loser, winner in result.suppressed:
            print(f"{loser.rule.id} overruled by {winner.rule.id} (group {loser.rule.group})")
    print("\n=== FULL EXPLANATION OF THE FIRST RECOMMENDATION ===")
    print(result.explain(result.recommendations[0].rule.id))


if __name__ == "__main__":
    main()
