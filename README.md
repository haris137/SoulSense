# SOULSENSE – Another Crab's Treasure Combat & Build Advisor

A **rule-based expert system** (Python + Streamlit) that advises players of *Another Crab's Treasure* on
combat, shells, attacks, stats, adaptations, healing and boss fights. It contains **95 IF-THEN rules**
in 8 categories, a **forward-chaining inference engine**, **conflict resolution**, and an
**explanation facility** that shows which rules fired and why.

> Fan-made project, not affiliated with Aggro Crab. No machine learning is used.

**Live URL:** [https://your-app-name.vercel.app](https://your-app-name.vercel.app)

---

## 1. Quick start

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt                         # installs streamlit only
streamlit run app.py                                    # opens http://localhost:8501
```

Run the tests (standard library only, no extra installs):

```bash
python -m unittest discover -s tests -v
```

Try the engine without a browser:

```bash
python tools/run_cli.py                                 # list example players
python tools/run_cli.py "Blocker with a cracking shell"
```

Regenerate the documentation from the knowledge base:

```bash
python tools/generate_docs.py     # writes docs/RULES.md and code_explanation.pdf (needs reportlab)
```

## 2. Project structure

```
SOULSENSE/
├── app.py                      entry point (page config, CSS, navigation)
├── engine/
│   ├── working_memory.py       facts + their origin (user / inferred)
│   ├── rule_matcher.py         conditions: AND / OR / NOT, 16 operators, 3-valued logic
│   ├── rule.py                 the Rule dataclass
│   ├── conflict_resolver.py    priority > specificity > KB order; advice groups
│   ├── inference_engine.py     forward-chaining loop, trace, missing-input analysis
│   └── rule_analysis.py        builds an example input for any rule (proves no dead rules)
├── knowledge_base/
│   ├── rules.py                the 95 rules + named thresholds
│   ├── facts.py                every user input (type, options, label)
│   ├── scenarios.py            six example players
│   └── game_mechanics.md       verified mechanics M-01..M-24 + sources + known disagreements
├── components/                 session.py, input_forms.py, result_display.py, navigation.py
├── pages/                      home, profile, combat_advisor, shell_advisor, boss_advisor,
│                               progression_advisor, diagnosis, knowledge_explorer
├── tests/                      test_engine, test_rules, test_scenarios, test_ui_smoke
├── tools/                      run_cli.py, generate_docs.py
├── docs/RULES.md               every rule: IF, THEN, priority, evidence, example input
├── assets/style.css            styling (works in light and dark themes)
├── code_explanation.pdf        architecture, modules, workflow, rules, testing, viva Q&A
├── requirements.txt            streamlit>=1.36,<2
└── .streamlit/config.toml      theme
```

## 3. Expert-system architecture

| Component | Where | Role |
|-----------|-------|------|
| Knowledge base | `knowledge_base/rules.py` | 95 IF-THEN rules |
| Working memory | `engine/working_memory.py` | user facts + inferred facts, each with its origin |
| Rule matcher | `engine/rule_matcher.py` | evaluates condition trees (AND/OR/NOT, `== != < <= > >= in contains count…`) |
| Inference engine | `engine/inference_engine.py` | forward chaining |
| Conflict resolver | `engine/conflict_resolver.py` | decides which rule/advice wins |
| Explanation facility | `components/result_display.py` | "Why this advice?" panels and the full trace |

### Forward chaining

Data-driven *match → resolve → act* cycle, repeated until nothing new matches:

1. **Match** – every not-yet-fired rule is tested against working memory. True rules form the *conflict set*.
2. **Resolve** – the conflict resolver picks one rule.
3. **Act** – the rule fires: it infers new facts and/or records advice. New facts can make other rules match.

Example chain: `SHL-01` infers `shell_condition = critical` from `shell_durability_pct <= 30`;
only then can `SHL-04` ("swap your failing shell") match. Each rule fires at most once and memory never
shrinks, so the loop always terminates.

### Conflict resolution

* **Which rule fires next:** highest **priority** → most **specific** (more tests) → earlier in the knowledge base.
  The deciding reason is stored and shown for every firing.
* **Contradictory advice:** rules answering the same question share a **group** (`defense_mode`, `weight_choice`,
  `stat_priority`, `resource_action`, `heal_or_rest`, `boss_phase`). Only the best-ranked advice per group is shown;
  the rest are listed as *overruled by rule X* so nothing is hidden.
* **Conflicting inferred facts:** the first (higher-ranked) assertion wins; user answers are never overwritten.

### Missing or uncertain input

Every field has "Not sure". Unknown facts make conditions *unknown* (three-valued logic), so those rules do not
fire – and the UI shows which answers would unlock them. Empty input never crashes the app.

## 4. The knowledge base

| Category | Rules |
|----------|------:|
| Combat & enemy encounters | 9 |
| Shells, durability & defense | 13 |
| Weapon & attack strategies | 8 |
| Character progression & stats | 13 |
| Adaptations & abilities | 9 |
| Healing, resources & survival | 16 |
| Boss preparation & strategy | 18 |
| Dodging, blocking, parrying & stamina | 9 |

Complete list with conditions, conclusions, priorities and an example input for each rule: **[docs/RULES.md](docs/RULES.md)**
(also in the Streamlit "Knowledge base" page and in `code_explanation.pdf`).

### How the game facts were handled

* Every rule cites verified mechanic ids (`M-xx`) from [`knowledge_base/game_mechanics.md`](knowledge_base/game_mechanics.md),
  which lists the public sources used. A test fails if a rule cites an id that does not exist.
* Each rule is labelled **mechanic** (verified), **guide** (community recommendation), **tactic** (general practice on a
  mechanic) or **design** (a classification the designer chose, e.g. "durability ≤ 30 % = critical").
* Where guides **disagree** (which stat first, whether you can parry, stowaway capacity, Topoda's spelling…) the knowledge base
  says so instead of picking a side. Prices/costs found in only one source are marked as such.
* Bosses without verified mechanics get an honest "no specific data" rule (`BOS-18`) rather than invented advice.
* The knowledge was compiled from public guides, reviews and patch notes in Nov 2026 – **not** from the game files.
  Patches may change numbers; verify important details in-game.

## 5. Testing

`python -m unittest discover -s tests -v` runs 55 tests:

* **test_engine** – memory semantics, every operator, three-valued logic, conflict ordering, group suppression, 2- and 3-step chaining, refraction, blocked inference, missing-input tracing.
* **test_rules** – ≥ 50 rules, unique ids, all categories populated, only known facts and **valid option values** (typo guard), every derived fact is inferred by some rule, cited mechanics exist, advice texts unique, forms cover every fact, and **every rule is reachable** (an input is synthesised and the engine really fires the rule).
* **test_scenarios** – six realistic players trigger the expected rules; conflicts resolve as documented; empty/partial/"not sure" input handled.
* **test_ui_smoke** – every Streamlit page renders for every scenario, forms don't alter stored answers, no duplicate widget keys. Uses Streamlit's own `AppTest` when Streamlit is installed, otherwise a fake `streamlit` module.

## 6. Deployment (Streamlit Community Cloud)

Streamlit Community Cloud serves the app on a public HTTPS URL (reachable over the internet, not just localhost).

1. Create a **public GitHub repository** and push this folder so that `app.py` is in the repository root:
   ```bash
   git init && git add . && git commit -m "SOULSENSE"
   git branch -M main
   git remote add origin https://github.com/<you>/soulsense.git
   git push -u origin main
   ```
2. Go to **https://share.streamlit.io**, sign in with GitHub and click **Create app**.
3. Choose the repository, branch `main` and main file path `app.py`.
4. Click **Deploy**. Dependencies come from `requirements.txt` (only `streamlit`).
5. Copy the public URL (looks like `https://<name>.streamlit.app`) into the *Live URL* line at the top of this README
   and commit the change.

Troubleshooting: if the build fails, open **Manage app → Logs**. The app needs Streamlit ≥ 1.36 (for `st.navigation`).

## 7. Limitations

* Advice is only as good as the player's answers; the system cannot read the game screen.
* Coverage is intentionally limited to what could be verified: many bosses and shells have no dedicated rules.
* The "Not sure" option lowers the number of rules that can fire – by design.
