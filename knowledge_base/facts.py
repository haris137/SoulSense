"""
facts.py - the vocabulary of the expert system.

Every INPUT fact the user can provide is described here once (FactSpec).
The Streamlit forms are generated from this schema, and the unit tests use it
to check that every rule only talks about facts and values that really exist.

Fact kinds
    select  one choice from a list           -> str
    bool    yes / no                         -> bool
    int     small whole number (slider)      -> int
    number  large whole number (number box)  -> int
    multi   several choices from a list      -> list[str]

A value of None always means "the player is not sure" - the fact is then
simply missing from working memory (see engine/working_memory.py).

Facts that are INFERRED by rules (shell_condition, hp_state, ...) are not
listed here; they are declared in rules.py next to the rules that infer them.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class FactSpec:
    name: str
    label: str
    kind: str                                    # select | bool | int | number | multi
    options: List[Tuple[str, str]] = field(default_factory=list)   # (value, label)
    min: int = 0
    max: int = 100
    step: int = 1
    default: Any = None
    help: str = ""

    @property
    def option_values(self) -> List[str]:
        return [value for value, _ in self.options]

    def label_for(self, value: Any) -> str:
        if isinstance(value, bool):
            return "Yes" if value else "No"
        if isinstance(value, list):
            return ", ".join(self.label_for(v) for v in value) or "none"
        return dict(self.options).get(value, str(value))


def _spec(name, label, kind, options=None, **kw) -> FactSpec:
    return FactSpec(name, label, kind, options or [], **kw)


# ---------------------------------------------------------------- option lists
BOSSES = [
    ("nephro", "Nephro, Captain of the Guard"),
    ("royal_shellsplitter", "Royal Shellsplitter (optional)"),
    ("magista", "Magista, Tyrant of Slacktide"),
    ("pagurus", "Pagurus, the Ravenous"),
    ("diseased_lichenthrope", "Diseased Lichenthrope"),
    ("curdled_carbonara_connoisseur", "Curdled Carbonara Connoisseur (optional)"),
    ("heikea", "Heikea, Intimidation Crab"),
    ("topoda", "Grovekeeper Topoda (optional)"),
    ("consortium", "The Consortium"),
    ("scuttling_sludge_steamroller", "Scuttling Sludge Steamroller (optional)"),
    ("ceviche_sisters", "The Ceviche Sisters"),
    ("voltai", "Voltai, the Accumulator"),
    ("roland", "Roland, Venture Crabitalist"),
    ("petroch", "Petroch, the False Moon"),
    ("inkerton", "Inkerton, Crab Hunter"),
    ("camtscha", "Camtscha, the Bleached King"),
    ("praya_dubia", "Praya Dubia, the Ocean's Agony"),
    ("firth", "Firth, the Crab Who Stole the Whorl"),
]

SKILLS = [
    ("shelleportation", "Shelleportation"), ("housewarming", "Housewarming"),
    ("umami_training", "Umami Training"), ("circle_of_life", "Circle of Life"),
    ("elusive_prey", "Elusive Prey"), ("skedaddle", "Skedaddle"),
    ("ebb_and_flow", "Ebb and Flow"), ("dispatch", "Dispatch"),
    ("spearfishing", "Spearfishing"), ("wave_breaker", "Wave Breaker"),
    ("parry", "Parry"), ("aggravation", "Aggravation"),
    ("self_repair", "Self-Repair"), ("kintsugi", "Kintsugi"),
    ("riposte", "Riposte"), ("natural_defenses", "Natural Defenses"),
]

ADAPTATIONS = [
    ("royal_wave", "Royal Wave"), ("bubble_bullet", "Bubble Bullet"),
    ("eelectrocute", "Eelectrocute"), ("snail_sanctum", "Snail Sanctum"),
    ("bobbit_trap", "Bobbit Trap"), ("mantis_punch", "Mantis Punch"),
    ("tactical_tentacle", "Tactical Tentacle"), ("urchin_toss", "Urchin Toss"),
]

STOWAWAYS = [
    ("another_crab", "Another Crab"), ("rubber_band", "Rubber Band"),
    ("used_bandage", "Used Bandage"), ("fruit_sticker", "Fruit Sticker"),
    ("whelk", "Whelk / Whelk+ / Whelk++"),
]

AREAS = [
    ("shallows", "The Shallows"), ("slacktide", "Slacktide"),
    ("sands_between", "The Sands Between"), ("expired_grove", "Expired Grove"),
    ("flotsam_vale", "Flotsam Vale"), ("mouth_of_drain", "The Mouth of the Drain"),
    ("unfathom", "The Unfathom"), ("old_ocean", "The Old Ocean / Trash Island"),
    ("other", "Somewhere else"),
]

# ------------------------------------------------------------------ the schema
FACT_SCHEMA: Dict[str, FactSpec] = {s.name: s for s in [
    # ---- player profile ----------------------------------------------------
    _spec("experience", "How experienced are you with Soulslikes?", "select",
          [("new", "New to the genre"), ("some", "Some experience"), ("veteran", "Veteran")]),
    _spec("playstyle", "Your preferred playstyle", "select",
          [("blocker", "Defensive - I block a lot"), ("dodger", "Evasive - I dodge and roll"),
           ("aggressor", "Aggressive - I attack constantly"),
           ("umami_caster", "Umami - I rely on shell spells / adaptations"),
           ("balanced", "Balanced")]),
    _spec("game_stage", "How far are you in the story?", "select",
          [("early", "Early (Shallows - Slacktide)"),
           ("mid", "Middle (Sands Between - Flotsam Vale)"),
           ("late", "Late (Mouth of the Drain onward)")]),
    _spec("current_area", "Where are you right now?", "select", AREAS),
    _spec("shells_unlocked", "Have you beaten Nephro (shell-wearing unlocked)?", "bool",
          help="Wearing shells unlocks after the first boss."),
    _spec("skills_known", "Umami skills you have learned", "multi", SKILLS,
          help="Only the skills this advisor reasons about are listed."),
    _spec("adaptations_known", "Adaptations you have unlocked", "multi", ADAPTATIONS),
    _spec("adaptations_equipped", "Adaptations you carry (max 2)", "multi", ADAPTATIONS),
    _spec("defeated_topoda", "Have you defeated Grovekeeper Topoda?", "bool"),
    # ---- stats -------------------------------------------------------------
    _spec("vit", "VIT (Vitality)", "int", min=0, max=40, default=3,
          help="Each point adds +5 HP."),
    _spec("res", "RES (Resistance)", "int", min=0, max=40, default=0,
          help="Lowers damage dealt to your shell; gates stowaways."),
    _spec("atk", "ATK (Attack)", "int", min=0, max=40, default=0,
          help="About +7% physical strike damage per point."),
    _spec("msg", "MSG (Umami)", "int", min=0, max=40, default=0,
          help="Strengthens Umami abilities."),
    # ---- resources ---------------------------------------------------------
    _spec("microplastics", "Microplastics you are carrying", "number",
          min=0, max=500000, step=500, default=0),
    _spec("umami_crystals", "Unspent purple Umami Crystals", "int", min=0, max=150, default=0),
    _spec("shark_eggs", "Shark Eggs", "int", min=0, max=10, default=0),
    _spec("heartkelp_pods", "Heartkelp pods you have left", "int", min=0, max=9, default=3),
    _spec("heartkelp_sprouts_found", "Heartkelp Sprouts found (of 6)", "int", min=0, max=6, default=0),
    _spec("stowaways_equipped", "Stowaways equipped", "multi", STOWAWAYS),
    _spec("stowaway_capacity_free", "Do you have unused stowaway capacity?", "bool"),
    # ---- current situation -------------------------------------------------
    _spec("player_hp_pct", "Your HP (%)", "int", min=0, max=100, default=100),
    _spec("shell_worn", "Are you wearing a shell?", "bool"),
    _spec("shell_durability_pct", "Shell durability left (%)", "int", min=0, max=100, default=100),
    _spec("shell_weight", "Shell weight class", "select",
          [("S", "Small (light)"), ("M", "Medium"), ("L", "Large (heavy)")]),
    _spec("shell_insured", "Is this shell insured?", "bool"),
    _spec("shell_favorite", "Is this a shell you want to keep?", "bool"),
    _spec("shell_spell_role", "What does your shell spell mainly do?", "select",
          [("damage", "Deals damage"), ("stagger", "Builds stagger"),
           ("mobility", "Mobility (e.g. roll)"), ("self_heal", "Heals me (Munch)"),
           ("utility", "Other utility"), ("none", "No useful spell")]),
    _spec("umami_charges", "Umami charges available", "int", min=0, max=10, default=0),
    _spec("nearby_shells", "Is there a shell you could pick up nearby?", "bool"),
    _spec("near_moon_snail", "Is a Moon Snail Shell (checkpoint) close?", "bool"),
    _spec("unrecovered_microplastics", "Did you die and leave microplastics at your death site?",
          "bool", help="Yes = they are waiting where you last died."),
    _spec("deaths_in_a_row", "Deaths on this challenge", "int", min=0, max=30, default=0),
    _spec("tough_enemies_cleared", "Have you already cleared the tough enemies nearby?", "bool"),
    _spec("parry_trouble", "Do you struggle with parry timing?", "bool"),
    _spec("open_to_assist", "Are you open to using the Assist menu?", "bool"),
    _spec("unhappy_with_build", "Do you want to redo your stat build?", "bool"),
    _spec("main_problem", "What is your biggest problem right now?", "select",
          [("too_much_damage", "I take too much damage"),
           ("too_little_damage", "I deal too little damage"),
           ("shells_breaking", "My shells break too fast"),
           ("running_out_of_healing", "I run out of healing"),
           ("low_microplastics", "I do not earn enough microplastics"),
           ("none", "Nothing in particular")]),
    # ---- the enemy ---------------------------------------------------------
    _spec("encounter_type", "What are you facing?", "select",
          [("common", "Common enemies"), ("tough", "Tough enemy"), ("boss", "A boss")]),
    _spec("target_boss", "Which boss?", "select", BOSSES),
    _spec("enemy_count", "How many enemies?", "int", min=1, max=8, default=1),
    _spec("attack_style", "How does the enemy attack?", "select",
          [("slow_heavy", "Slow, heavy swings with long wind-ups"),
           ("fast_relentless", "Fast, relentless combos"),
           ("area_slam", "Wide spins or area slams"),
           ("ranged", "Ranged projectiles"),
           ("electric", "Electric attacks"),
           ("mixed", "A mix of everything")]),
    _spec("enemy_hp_pct", "Enemy health left (%)", "int", min=0, max=100, default=100),
    _spec("stagger_pct", "Enemy stagger bar (yellow, %)", "int", min=0, max=100, default=0),
    _spec("enemy_capsized", "Is the enemy capsized?", "bool"),
]}


def label_for(fact: str, value: Any) -> str:
    """Friendly text for a fact value (falls back to str(value))."""
    spec = FACT_SCHEMA.get(fact)
    return spec.label_for(value) if spec else str(value)
