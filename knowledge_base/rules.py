"""
rules.py - the KNOWLEDGE BASE of SOULSENSE.

Every rule is an IF-THEN statement built with the helpers from
engine/rule_matcher.py (eq, le, has, AND, OR, ...).

How to read a rule
    R("SHL-04", "shell", "Swap a failing shell",
      AND(eq("shell_condition", "critical"), is_true("nearby_shells")),
      priority=90, severity="critical", advice="...", sources=("M-07",), why="...")

        IF   shell_condition == 'critical' AND nearby_shells is true
        THEN advise "..."

Two kinds of rule
    * DERIVATION rules  have `asserts={...}`  -> they INFER new facts
      (e.g. durability <= 30 % -> shell_condition = 'critical').  Other rules
      use those facts, which is what makes this FORWARD CHAINING.
    * ADVICE rules      have `advice="..."`   -> they produce a recommendation.

Every rule cites the verified mechanic(s) it is based on (`sources`, ids from
knowledge_base/game_mechanics.md).  Heuristic thresholds that are NOT game
mechanics are the named constants below.
"""

from engine.rule import Rule
from engine.rule_matcher import (AND, OR, count_ge, count_lt, eq, ge, gt, has, has_any,
                                 is_false, is_true, lacks, le, lt, ne, one_of)

# ---------------------------------------------------------------------------
# Designer-chosen thresholds (heuristics, NOT game mechanics - see game_mechanics.md)
# ---------------------------------------------------------------------------
SHELL_CRITICAL_PCT = 30     # shell durability at/below this  -> "critical"
SHELL_WORN_PCT = 60         # at/below this (and above critical) -> "worn"
HP_LOW_PCT = 35             # player HP bands
HP_HURT_PCT = 60
GROUP_SIZE = 3              # this many enemies = a "group fight"
MANY_MICROPLASTICS = 5000   # carrying this much makes a death painful
ENRAGE_HP_PCT = 50          # boss phase change point (M-19)
MANY_DEATHS = 8             # deaths in a row before suggesting the Assist menu

PHASE_CHANGE_BOSSES = ["diseased_lichenthrope", "heikea", "voltai"]     # M-19
LONG_FIGHT_BOSSES = ["camtscha", "praya_dubia", "firth"]                # M-19, M-20
UNDETAILED_BOSSES = ["pagurus", "diseased_lichenthrope", "curdled_carbonara_connoisseur",
                     "scuttling_sludge_steamroller", "roland"]

CATEGORIES = {
    "combat":      "Combat & enemy encounters",
    "shell":       "Shells, durability & defense",
    "weapon":      "Weapon & attack strategies",
    "progression": "Character progression & stats",
    "adaptations": "Adaptations & abilities",
    "survival":    "Healing, resources & survival",
    "boss":        "Boss preparation & strategy",
    "defense":     "Dodging, blocking, parrying & stamina",
}

# Facts that are INFERRED by derivation rules (name -> allowed values)
DERIVED_FACTS = {
    "shell_condition": ["critical", "worn", "healthy"],
    "hp_state": ["low", "hurt", "ok"],
    "group_fight": [True],
    "carrying_much": [True],
    "boss_phase_change": [True],
}


def R(rid, category, name, cond, *, priority=50, advice=None, asserts=None,
      severity="tip", group=None, basis="mechanic", sources=(), why=""):
    """Short constructor so each rule stays compact and readable."""
    return Rule(rid, category, name, cond, priority, advice, asserts or {},
                severity, group, basis, tuple(sources), why)


RULES = [
    # =====================================================================
    # 1. COMBAT & ENEMY ENCOUNTERS  (CMB)
    # =====================================================================
    R("CMB-01", "combat", "Detect a group fight",
      ge("enemy_count", GROUP_SIZE),
      priority=100, asserts={"group_fight": True}, basis="design",
      why=f"{GROUP_SIZE} or more enemies is treated as a group fight."),

    R("CMB-02", "combat", "Do not fight a group in the open",
      is_true("group_fight"),
      priority=60, severity="warning", basis="tactic", sources=("M-06", "M-16"),
      advice="Three or more enemies: avoid fighting in the open. Back up to a wall or choke point "
             "and prefer area attacks - the Twist Top shell spell or the Eelectrocute adaptation hit "
             "several enemies at once.",
      why="Shell spells and adaptations with area effects exist, and Kril takes damage from every enemy."),

    R("CMB-03", "combat", "Block against relentless attackers",
      AND(eq("attack_style", "fast_relentless"), is_true("shell_worn"),
          ne("shell_condition", "critical")),
      priority=50, group="defense_mode", basis="guide", sources=("M-24", "M-07"),
      advice="Fast, relentless combos leave little room to roll. Lean on blocking (the shell absorbs "
             "the damage instead of Kril) and attack in the gaps - but swap shells before yours breaks.",
      why="Enemies attack quickly, so guides favour blocking over dodging; blocking costs shell durability."),

    R("CMB-04", "combat", "Dodge into slow, telegraphed attacks",
      one_of("attack_style", ["slow_heavy", "area_slam"]),
      priority=45, group="defense_mode", basis="guide", sources=("M-11", "M-20"),
      advice="Slow, telegraphed swings: dodge INTO the attack (invincibility frames), then punish from "
             "the sides or from behind.",
      why="Dodging has i-frames; backing away can still leave you in the hitbox. Slow bosses are hit from the flanks."),

    R("CMB-05", "combat", "Heavy shell versus slow attacks: block or parry",
      AND(one_of("attack_style", ["slow_heavy", "area_slam"]), eq("shell_weight", "L")),
      priority=45, group="defense_mode", sources=("M-06", "M-07"),
      advice="Your heavy shell slows your dodge roll. Against slow, telegraphed attacks it is safer to "
             "block (or parry) than to roll late.",
      why="Shell weight changes dodge-roll speed; the extra durability of a heavy shell suits blocking."),

    R("CMB-06", "combat", "Close the gap on ranged enemies",
      AND(eq("attack_style", "ranged"), has_any("skills_known", ["spearfishing", "wave_breaker"])),
      priority=55, sources=("M-13",),
      advice="Ranged attackers: close the distance with Spearfishing (reels the enemy in, costs a Barbed "
             "Hook) or Wave Breaker (grapple and strike) instead of walking through projectiles.",
      why="Both skills are gap-closers according to the skill tree."),

    R("CMB-07", "combat", "Rubber Band equipped: ignore electricity",
      AND(eq("attack_style", "electric"), has("stowaways_equipped", "rubber_band")),
      priority=40, severity="info", sources=("M-18",),
      advice="Rubber Band is equipped, so you can ignore electric attacks - stay aggressive.",
      why="The Rubber Band stowaway negates electric attacks."),

    R("CMB-08", "combat", "Electric enemy without Rubber Band",
      AND(eq("attack_style", "electric"), lacks("stowaways_equipped", "rubber_band")),
      priority=55, sources=("M-18",),
      advice="Electric attackers: if you own the Rubber Band stowaway, equip it - it lets you ignore "
             "electric attacks.",
      why="The Rubber Band stowaway negates electric attacks."),

    R("CMB-09", "combat", "Learn patterns after repeated deaths",
      AND(eq("encounter_type", "tough"), ge("deaths_in_a_row", 2)),
      priority=50, basis="guide", sources=("M-24",),
      advice="You keep dying to the same tough enemy. Stop trading blows blindly: watch one complete "
             "attack cycle, learn the wind-ups, then re-engage. Some common enemies are as dangerous as bosses.",
      why="Guides stress memorising attack patterns; tough common enemies are comparable to bosses."),

    # =====================================================================
    # 2. SHELLS, DURABILITY & DEFENSE  (SHL)
    # =====================================================================
    R("SHL-01", "shell", "Shell is critical",
      AND(is_true("shell_worn"), le("shell_durability_pct", SHELL_CRITICAL_PCT)),
      priority=100, asserts={"shell_condition": "critical"}, basis="design",
      why=f"Durability at or below {SHELL_CRITICAL_PCT}% is classed as critical."),

    R("SHL-02", "shell", "Shell is worn",
      AND(is_true("shell_worn"), gt("shell_durability_pct", SHELL_CRITICAL_PCT),
          le("shell_durability_pct", SHELL_WORN_PCT)),
      priority=100, asserts={"shell_condition": "worn"}, basis="design",
      why=f"Durability between {SHELL_CRITICAL_PCT}% and {SHELL_WORN_PCT}% is classed as worn."),

    R("SHL-03", "shell", "Shell is healthy",
      AND(is_true("shell_worn"), gt("shell_durability_pct", SHELL_WORN_PCT)),
      priority=100, asserts={"shell_condition": "healthy"}, basis="design",
      why=f"Durability above {SHELL_WORN_PCT}% is classed as healthy."),

    R("SHL-04", "shell", "Swap a failing shell",
      AND(eq("shell_condition", "critical"), is_true("nearby_shells")),
      priority=90, severity="critical", sources=("M-07", "M-08", "M-23"),
      advice="Your shell is about to break and a replacement is nearby - swap now. A broken shell means "
             "no shell spell, no block and much less damage reduction.",
      why="A shell breaks at 0 durability and a shell-less crab relies on dodging only."),

    R("SHL-05", "shell", "Kintsugi cushions a breaking shell",
      AND(eq("shell_condition", "critical"), has("skills_known", "kintsugi")),
      priority=60, sources=("M-13",),
      advice="You know Kintsugi: this shell regenerates fully after it breaks - once per rest. Keep using "
             "it, but remember the free regeneration is spent after one break.",
      why="Kintsugi: shell regenerates fully after breaking once per rest."),

    R("SHL-06", "shell", "Use Elusive Prey when the shell breaks",
      AND(eq("shell_condition", "critical"), has("skills_known", "elusive_prey")),
      priority=60, sources=("M-13",),
      advice="Elusive Prey gives a couple of seconds of invincibility when your shell breaks. Use that "
             "window to reposition or heal - attacking early ends it.",
      why="Elusive Prey: invincible briefly after the shell breaks; attacking early ends the effect."),

    R("SHL-07", "shell", "Shell-less with a shell in reach",
      AND(is_true("shells_unlocked"), is_false("shell_worn"), is_true("nearby_shells")),
      priority=90, severity="critical", sources=("M-08", "M-23"),
      advice="You are shell-less and a shell is within reach - pick it up. Without a shell you have no "
             "spell, no block and much less damage reduction.",
      why="Being naked removes the shell spell and most defence."),

    R("SHL-08", "shell", "Summon Snail Sanctum when naked",
      AND(is_true("shells_unlocked"), is_false("shell_worn"), is_false("nearby_shells"),
          has("adaptations_known", "snail_sanctum"), ge("umami_charges", 1)),
      priority=85, severity="warning", sources=("M-08", "M-16"),
      advice="No shell nearby: cast Snail Sanctum - when you are naked it summons a shell made of pure Umami.",
      why="Snail Sanctum is the adaptation that provides a shell when you have none."),

    R("SHL-09", "shell", "Shells are locked until Nephro",
      is_false("shells_unlocked"),
      priority=70, severity="info", sources=("M-08", "M-20"),
      advice="Wearing shells unlocks when you beat Nephro, the first boss. Until then you fight shell-less: "
             "rely on dodging and level up a few times first.",
      why="Shell-wearing is unlocked by defeating Nephro."),

    R("SHL-10", "shell", "Heavy shell versus a dodge-based style",
      AND(eq("shell_weight", "L"), eq("playstyle", "dodger")),
      priority=55, severity="warning", group="weight_choice", sources=("M-06", "M-13"),
      advice="A heavy shell slows your dodge roll, which clashes with an evasive style. Prefer a light or "
             "medium shell, or learn Skedaddle (a backward dash not affected by shell weight).",
      why="Weight class sets dodge-roll speed; Skedaddle ignores shell weight."),

    R("SHL-11", "shell", "Light shell versus a blocking style",
      AND(eq("shell_weight", "S"), eq("playstyle", "blocker"), one_of("encounter_type", ["tough", "boss"])),
      priority=55, group="weight_choice", sources=("M-06",),
      advice="Light shells are fragile. If you mostly block, a heavier shell holds more durability against "
             "hard hitters, at the price of a slower dodge roll.",
      why="Heavier shells have more durability; light shells break quickly."),

    R("SHL-12", "shell", "Protect a favourite shell with insurance",
      AND(is_true("shell_favorite"), is_false("shell_insured")),
      priority=65, severity="warning", sources=("M-09",),
      advice="You want to keep this shell - buy Shell Insurance. An insured shell comes back with you after "
             "death (prices vary, e.g. 200 for Banana Peel, 1,500 for Yoccult).",
      why="Insurance is the only protection against losing a shell on death."),

    R("SHL-13", "shell", "Use a stagger spell on tough enemies",
      AND(eq("shell_spell_role", "stagger"), ge("umami_charges", 1),
          one_of("encounter_type", ["tough", "boss"])),
      priority=60, sources=("M-06", "M-10"),
      advice="Your shell spell builds stagger (e.g. Fizzle costs 1 Umami and raises stagger). Use it to fill "
             "the yellow bar, then burst the stunned enemy.",
      why="A full stagger bar stuns the enemy briefly - the main damage window."),

    # =====================================================================
    # 3. WEAPON & ATTACK STRATEGIES  (WPN)
    # =====================================================================
    R("WPN-01", "weapon", "Burst when stagger is nearly full",
      ge("stagger_pct", 80),
      priority=70, sources=("M-10",),
      advice="The stagger bar is nearly full: line up your strongest attacks - a full bar stuns the enemy "
             "briefly and that is your main damage window.",
      why="Filling the stagger bar stuns the enemy."),

    R("WPN-02", "weapon", "Dispatch a capsized enemy",
      AND(is_true("enemy_capsized"), has("skills_known", "dispatch")),
      priority=75, sources=("M-10", "M-13"),
      advice="Capsized enemy and you know Dispatch: attack its weak spots for maximum damage.",
      why="Dispatch deals the most damage to weak spots of capsized enemies."),

    R("WPN-03", "weapon", "Capsized without Dispatch",
      AND(is_true("enemy_capsized"), lacks("skills_known", "dispatch")),
      priority=50, sources=("M-10", "M-13"),
      advice="The enemy is capsized - take the free hits. The Dispatch skill would make weak-spot attacks on "
             "capsized enemies much stronger.",
      why="Capsize is an opening; Dispatch exploits it."),

    R("WPN-04", "weapon", "Skedaddle into Ebb and Flow",
      AND(has("skills_known", "skedaddle"), has("skills_known", "ebb_and_flow")),
      priority=50, sources=("M-13",),
      advice="Combo: dodge with Skedaddle (backward dash), then Ebb and Flow gives an immediate powerful "
             "spin attack - a built-in dodge-and-counter.",
      why="Ebb and Flow triggers right after dodging an attack with Skedaddle."),

    R("WPN-05", "weapon", "Block then counter with Aggravation",
      AND(has("skills_known", "aggravation"), one_of("playstyle", ["blocker", "balanced"]),
          ne("shell_condition", "critical")),
      priority=50, sources=("M-13",),
      advice="Aggravation: when your shell takes a blocked hit your next attack hits harder - block, then "
             "counter-attack straight away.",
      why="Aggravation boosts the attack that follows a blocked hit."),

    R("WPN-06", "weapon", "Whelk stowaway for spell builds",
      AND(eq("playstyle", "umami_caster"), lacks("stowaways_equipped", "whelk"), ge("res", 2)),
      priority=45, sources=("M-18",),
      advice="Whelk-family stowaways raise shell-spell damage (+15 / +30 / +45%, needing 2 / 7 / 13 RES). "
             "You meet the first requirement - equip one if you own it.",
      why="Whelk needs 2 RES and boosts shell-spell damage."),

    R("WPN-07", "weapon", "Spearfishing is weak against bosses",
      AND(has("skills_known", "spearfishing"), eq("encounter_type", "boss")),
      priority=30, severity="info", sources=("M-13",),
      advice="Spearfishing struggles with large enemies and each throw uses a Barbed Hook - do not rely on "
             "it against bosses.",
      why="Larger enemies are harder to reel in; the skill uses a Barbed Hook."),

    R("WPN-08", "weapon", "Bubble Bullet capsize combo",
      AND(has("adaptations_equipped", "bubble_bullet"), has("skills_known", "dispatch")),
      priority=45, sources=("M-10", "M-16"),
      advice="An upgraded (Lv. 2) Bubble Bullet can capsize an enemy - follow up with Dispatch on the weak spots.",
      why="Bubble Bullet Lv. 2 capsizes; Dispatch punishes capsized enemies."),

    # =====================================================================
    # 4. CHARACTER PROGRESSION & STAT ALLOCATION  (PRG)
    # =====================================================================
    R("PRG-01", "progression", "Early VIT base",
      AND(lt("vit", 5), eq("game_stage", "early")),
      priority=60, group="stat_priority", basis="guide", sources=("M-04",),
      advice="Raise VIT to at least 5 first (+5 HP per point). Early bosses hit hard and Kril has little HP.",
      why="Sportskeeda recommends VIT to 5 before other stats."),

    R("PRG-02", "progression", "Veteran attackers favour ATK",
      AND(eq("experience", "veteran"), eq("playstyle", "aggressor"), eq("game_stage", "early")),
      priority=60, group="stat_priority", basis="guide", sources=("M-04",),
      advice="As an experienced attacker, favour ATK (about +7% strike damage per point) with a little VIT - "
             "faster kills mean fewer hits taken.",
      why="GameSkinny suggests ATK with a little VIT early; more specific than PRG-01 so it wins for veterans."),

    R("PRG-03", "progression", "RES for blockers",
      AND(eq("playstyle", "blocker"), lt("res", 5)),
      priority=55, group="stat_priority", basis="guide", sources=("M-04", "M-07"),
      advice="Blocking sends damage into the shell. RES lowers the damage your shell takes and unlocks "
             "stowaways such as Whelk - it pays off most for blockers.",
      why="RES reduces shell damage."),

    R("PRG-04", "progression", "ATK once you have a VIT base",
      AND(eq("playstyle", "aggressor"), ge("vit", 5)),
      priority=50, group="stat_priority", basis="guide", sources=("M-04",),
      advice="With a solid VIT base, further points in ATK raise strike damage by about 7% each.",
      why="ATK scales physical strikes."),

    R("PRG-05", "progression", "Umami Training for casters",
      AND(eq("playstyle", "umami_caster"), lacks("skills_known", "umami_training"),
          ge("umami_crystals", 1)),
      priority=55, sources=("M-13",),
      advice="Spend crystals on Umami Training (+5 MSG each, three copies) at the Moon Snail.",
      why="Umami Training raises MSG, which strengthens Umami abilities."),

    R("PRG-06", "progression", "Fix 'I take too much damage'",
      eq("main_problem", "too_much_damage"),
      priority=65, group="stat_priority", basis="guide", sources=("M-04", "M-06"),
      advice="Taking too much damage: add VIT for HP and RES for shell durability, and check the DEF and "
             "weight of the shell you wear.",
      why="VIT adds HP, RES protects the shell, shell DEF is its durability."),

    R("PRG-07", "progression", "Fix 'I deal too little damage'",
      eq("main_problem", "too_little_damage"),
      priority=65, group="stat_priority", basis="guide", sources=("M-04", "M-10"),
      advice="Dealing too little damage: put points into ATK (about +7% per point) and work the stagger bar "
             "to open damage windows.",
      why="ATK scales strikes; stagger creates bonus-damage windows."),

    R("PRG-08", "progression", "Fix 'my shells break too fast'",
      eq("main_problem", "shells_breaking"),
      priority=65, basis="guide", sources=("M-04", "M-06", "M-07", "M-09", "M-13"),
      advice="Shells breaking too fast: RES lowers shell damage, well-timed parries negate it, Self-Repair and "
             "Kintsugi restore shells, heavier shells hold more durability, and insurance protects favourites.",
      why="Each of these mechanics reduces or recovers shell damage."),

    R("PRG-09", "progression", "Spend a big haul at a checkpoint",
      AND(is_true("carrying_much"), is_true("near_moon_snail")),
      priority=85, severity="warning", group="resource_action", sources=("M-02", "M-03"),
      advice="You carry a lot of microplastics and a Moon Snail Shell is close - level up or spend them now. "
             "Everything you carry is dropped when you die.",
      why="Microplastics are lost on death; Moon Snail Shells are where you spend them."),

    R("PRG-10", "progression", "Bank a big haul safely",
      AND(is_true("carrying_much"), is_false("near_moon_snail")),
      priority=85, severity="warning", group="resource_action", basis="guide", sources=("M-02", "M-03"),
      advice="Lots of microplastics and no checkpoint nearby: head back and bank them, and skip optional "
             "fights. Dying drops everything, and dying again before recovering it loses it for good.",
      why="Loss on death is permanent if you die twice before recovery."),

    R("PRG-11", "progression", "Respec with a Shark Egg",
      AND(is_true("unhappy_with_build"), ge("shark_eggs", 1)),
      priority=50, sources=("M-05",),
      advice="Respec at any Moon Snail Shell: Level Up, then the recycle icon. It costs 1 Shark Egg and "
             "refunds the microplastics you spent.",
      why="Stat respec costs one Shark Egg."),

    R("PRG-12", "progression", "Buy a Shark Egg to respec",
      AND(is_true("unhappy_with_build"), eq("shark_eggs", 0), ge("microplastics", 2000)),
      priority=45, basis="guide", sources=("M-05",),
      advice="No Shark Egg yet: one is reported on sale in New Carcinia (Upper Crust) for about 2,000 "
             "microplastics - check the shop. Eggs are limited, so respec only if you must.",
      why="A single source reports the shop price; availability is limited."),

    R("PRG-13", "progression", "Upgrade stowaway capacity",
      AND(is_false("stowaway_capacity_free"), ge("microplastics", 2500)),
      priority=40, basis="guide", sources=("M-18",),
      advice="Your stowaway capacity is full: vendors in New Carcinia sell capacity upgrades (the first "
             "reportedly costs 2,500 microplastics).",
      why="Capacity is raised with microplastics at New Carcinia vendors."),

    # =====================================================================
    # 5. ADAPTATIONS & ABILITIES  (ADP)
    # =====================================================================
    R("ADP-01", "adaptations", "Carry two adaptations",
      AND(count_ge("adaptations_known", 2), count_lt("adaptations_equipped", 2)),
      priority=60, sources=("M-16",),
      advice="You know two or more adaptations but carry fewer than two - equip a second one (you can carry two at once).",
      why="Two adaptations can be carried at once."),

    R("ADP-02", "adaptations", "Out of Umami",
      AND(eq("umami_charges", 0), count_ge("adaptations_equipped", 1)),
      priority=55, severity="warning", sources=("M-15",),
      advice="Out of Umami: adaptations and shell spells need charges. Recover them with Riposte (after a "
             "parry) or Circle of Life (kill with an Umami attack) - and fight with your fork meanwhile.",
      why="Adaptations spend Umami charges; only some skills return them."),

    R("ADP-03", "adaptations", "Royal Wave before a burst",
      AND(has("adaptations_equipped", "royal_wave"), eq("encounter_type", "boss")),
      priority=45, sources=("M-16",),
      advice="Royal Wave makes enemies briefly take increased damage - cast it just before your strongest "
             "attacks or a stagger window.",
      why="Royal Wave: enemies take increased damage from all sources briefly."),

    R("ADP-04", "adaptations", "Eelectrocute for groups",
      AND(is_true("group_fight"), has("adaptations_equipped", "eelectrocute")),
      priority=50, sources=("M-16",),
      advice="Eelectrocute shocks nearby enemies - exactly what a group fight needs.",
      why="Eelectrocute has an area effect."),

    R("ADP-05", "adaptations", "Upgrade adaptations at Topoda",
      AND(is_true("defeated_topoda"), ge("umami_crystals", 25), count_ge("adaptations_known", 1)),
      priority=40, basis="guide", sources=("M-16",),
      advice="Grovekeeper Topoda can upgrade your adaptations (Lv. 2 reportedly costs 25 crystals, Lv. 3 costs 50).",
      why="Upgrades are bought from Topoda with purple crystals."),

    R("ADP-06", "adaptations", "Adaptation upgrades need Topoda",
      AND(is_false("defeated_topoda"), count_ge("adaptations_known", 1), one_of("game_stage", ["mid", "late"])),
      priority=25, severity="info", sources=("M-16", "M-20"),
      advice="Adaptations are upgraded by Grovekeeper Topoda, an optional boss reachable after you beat Heikea.",
      why="Topoda unlocks adaptation upgrades."),

    R("ADP-07", "adaptations", "Housewarming rewards shell swapping",
      AND(eq("playstyle", "umami_caster"), lacks("skills_known", "housewarming"), ge("umami_crystals", 1)),
      priority=45, sources=("M-13", "M-15", "M-23"),
      advice="Learn Housewarming: each shell's spell can be cast once for free, and boss arenas contain "
             "plenty of shells to swap into.",
      why="Housewarming grants a free cast per shell."),

    R("ADP-08", "adaptations", "Shelleportation for banking",
      AND(is_true("carrying_much"), lacks("skills_known", "shelleportation"), ge("umami_crystals", 1)),
      priority=50, sources=("M-13", "M-02"),
      advice="Shelleportation teleports between Moon Snail Shells - the safest way to bank a big microplastic haul.",
      why="Teleporting avoids the walk back while carrying microplastics."),

    R("ADP-09", "adaptations", "Skills that recover shells",
      AND(eq("main_problem", "shells_breaking"), lacks("skills_known", "self_repair"), ge("umami_crystals", 1)),
      priority=55, sources=("M-13",),
      advice="Learn Self-Repair (lost shell health returns as you deal damage) and Kintsugi (full regeneration "
             "after a break, once per rest).",
      why="Both skills directly recover shell durability."),

    # =====================================================================
    # 6. HEALING, RESOURCES & SURVIVAL  (SRV)
    # =====================================================================
    R("SRV-01", "survival", "HP is low",
      le("player_hp_pct", HP_LOW_PCT),
      priority=100, asserts={"hp_state": "low"}, basis="design",
      why=f"HP at or below {HP_LOW_PCT}% is classed as low."),

    R("SRV-02", "survival", "HP is hurt",
      AND(gt("player_hp_pct", HP_LOW_PCT), le("player_hp_pct", HP_HURT_PCT)),
      priority=100, asserts={"hp_state": "hurt"}, basis="design",
      why=f"HP between {HP_LOW_PCT}% and {HP_HURT_PCT}% is classed as hurt."),

    R("SRV-03", "survival", "HP is fine",
      gt("player_hp_pct", HP_HURT_PCT),
      priority=100, asserts={"hp_state": "ok"}, basis="design",
      why=f"HP above {HP_HURT_PCT}% is classed as ok."),

    R("SRV-16", "survival", "Detect a big microplastic haul",
      ge("microplastics", MANY_MICROPLASTICS),
      priority=100, asserts={"carrying_much": True}, basis="design", sources=("M-02",),
      why=f"Carrying {MANY_MICROPLASTICS}+ microplastics makes a death costly (all are dropped)."),

    R("SRV-04", "survival", "Heal with a pod away from a checkpoint",
      AND(eq("hp_state", "low"), ge("heartkelp_pods", 1), is_false("near_moon_snail")),
      priority=80, severity="warning", group="heal_or_rest", sources=("M-17",),
      advice="HP is low and no checkpoint is close: use a Heartkelp pod (one button) at your next safe moment.",
      why="Heartkelp pods are the only portable healing."),

    R("SRV-05", "survival", "Rest at a nearby Moon Snail Shell",
      AND(one_of("hp_state", ["low", "hurt"]), is_true("near_moon_snail")),
      priority=70, group="heal_or_rest", sources=("M-03", "M-17"),
      advice="A Moon Snail Shell is close: resting heals you, refills every Heartkelp pod and saves progress - "
             "but it respawns common enemies.",
      why="Resting restores HP and pods and respawns enemies."),

    R("SRV-06", "survival", "Heal instead of resting to keep a cleared area",
      AND(one_of("hp_state", ["low", "hurt"]), is_true("near_moon_snail"), ge("heartkelp_pods", 1),
          is_true("tough_enemies_cleared")),
      priority=72, group="heal_or_rest", basis="guide", sources=("M-03",),
      advice="You have cleared tough enemies here and resting would respawn them. Heal with a pod instead "
             "and keep the area quiet.",
      why="Resting respawns enemies, so a pod can be cheaper than redoing a hard area."),

    R("SRV-07", "survival", "Munch when out of pods",
      AND(eq("hp_state", "low"), eq("heartkelp_pods", 0), is_false("near_moon_snail"),
          is_true("shell_worn"), eq("shell_spell_role", "self_heal"), ge("shell_durability_pct", 40)),
      priority=75, severity="warning", group="heal_or_rest", sources=("M-06",),
      advice="No pods left: your shell spell (Munch) converts shell durability into HP. Use it while the shell is healthy.",
      why="Munch consumes shell health to restore Kril's health."),

    R("SRV-08", "survival", "Retreat with no healing",
      AND(eq("hp_state", "low"), eq("heartkelp_pods", 0), is_false("near_moon_snail")),
      priority=75, severity="critical", basis="tactic", sources=("M-03", "M-17", "M-18"),
      advice="Low HP, no pods and no checkpoint near: avoid optional fights and retreat toward the nearest Moon "
             "Snail Shell, relying on dodges. An equipped Another Crab will revive you once if you die.",
      why="Only checkpoints refill pods; Another Crab revives once."),

    R("SRV-09", "survival", "Recover dropped microplastics first",
      AND(is_true("unrecovered_microplastics"), ge("deaths_in_a_row", 1)),
      priority=95, severity="critical", sources=("M-02",),
      advice="Go straight to your death site and collect your microplastics. If you die before reaching them "
             "they disappear permanently.",
      why="Dying again before recovery destroys the dropped microplastics."),

    R("SRV-10", "survival", "Consider the Assist menu",
      AND(ge("deaths_in_a_row", MANY_DEATHS), is_true("open_to_assist")),
      priority=30, severity="info", sources=("M-21",),
      advice="Many deaths in a row: the Assist menu offers extra shell durability, lower enemy health, more "
             "forgiving parry timing and keeping microplastics on death. Using it is a valid choice.",
      why="The game ships these accessibility options on purpose."),

    R("SRV-11", "survival", "Sands Between traps",
      eq("current_area", "sands_between"),
      priority=75, severity="warning", sources=("M-22",),
      advice="Sands Between: X marks on the sand are hidden traps that destroy your shell and can kill you - walk around them.",
      why="The hidden traps are a documented hazard of this area."),

    R("SRV-12", "survival", "Hunt Heartkelp Sprouts",
      lt("heartkelp_sprouts_found", 6),
      priority=25, severity="info", sources=("M-17",),
      advice="Six Heartkelp Sprouts exist and each adds a pod; you have found fewer. Explore for the rest "
             "(the first is near the Mooncave in the Duchess's castle).",
      why="Each sprout raises the maximum number of pods."),

    R("SRV-13", "survival", "Boost healing",
      AND(lacks("stowaways_equipped", "used_bandage"),
          OR(le("heartkelp_pods", 2), eq("main_problem", "running_out_of_healing"))),
      priority=35, sources=("M-18", "M-17"),
      advice="Running thin on healing: the Used Bandage stowaway adds 15% healing effectiveness, and Heartkelp "
             "Sprouts add pods.",
      why="Used Bandage: +15% healing effectiveness."),

    R("SRV-14", "survival", "Earn more microplastics",
      eq("main_problem", "low_microplastics"),
      priority=30, basis="guide", sources=("M-18", "M-02"),
      advice="Short on microplastics: a Fruit Sticker stowaway raises kill rewards, and farming near a Moon Snail "
             "Shell lets you bank quickly.",
      why="Fruit Sticker increases microplastics from kills; banking avoids loss on death."),

    R("SRV-15", "survival", "Another Crab as a safety net",
      AND(lacks("stowaways_equipped", "another_crab"), ge("microplastics", 3000), ge("deaths_in_a_row", 3)),
      priority=35, basis="guide", sources=("M-18",),
      advice="Another Crab (reported cost 3,000 microplastics) revives you once when you die, then breaks - a cushion for hard fights.",
      why="One-use revive stowaway."),

    # =====================================================================
    # 7. BOSS PREPARATION & STRATEGY  (BOS)
    # =====================================================================
    R("BOS-01", "boss", "Detect a phase-change boss",
      one_of("target_boss", PHASE_CHANGE_BOSSES),
      priority=100, asserts={"boss_phase_change": True}, sources=("M-19",),
      why="Diseased Lichenthrope, Heikea and Voltai become stronger below 50% health."),

    R("BOS-02", "boss", "Prepare for the 50% phase change",
      is_true("boss_phase_change"),
      priority=60, group="boss_phase", sources=("M-19",),
      advice="This boss gets stronger below 50% health. Keep a spare shell within reach and Heartkelp pods in reserve for phase two.",
      why="Phase-change point documented for these bosses."),

    R("BOS-03", "boss", "Phase two has started",
      AND(is_true("boss_phase_change"), le("enemy_hp_pct", ENRAGE_HP_PCT)),
      priority=70, severity="warning", group="boss_phase", sources=("M-19",),
      advice="Phase two has started - expect harder attacks. Heal when it is safe and replace a worn shell now.",
      why="More specific than BOS-02 so it replaces it once the boss is below 50%."),

    R("BOS-04", "boss", "Boss arenas hold shells",
      eq("encounter_type", "boss"),
      priority=30, severity="info", sources=("M-23", "M-03"),
      advice="Boss arenas usually contain plenty of shells - replace a broken one mid-fight. If you die, most "
             "bosses let you respawn at a nearby Moon Jelly instead of the distant checkpoint.",
      why="Arenas are stocked with shells; Moon Jellies shorten the run back."),

    R("BOS-05", "boss", "Nephro",
      eq("target_boss", "nephro"),
      priority=60, sources=("M-20",),
      advice="Nephro swings a big sword slowly: read the wind-up, dodge, and hit from the sides or from behind. "
             "You fight without a shell (they unlock when he falls), so level up a few times first.",
      why="Documented attack pattern of the first boss."),

    R("BOS-06", "boss", "Magista",
      eq("target_boss", "magista"),
      priority=55, basis="guide", sources=("M-20",),
      advice="Magista: players report success with the Soda Can shell and by staggering her. Beating her gives Royal Wave.",
      why="Single-source guide advice."),

    R("BOS-07", "boss", "Royal Shellsplitter needs a shell",
      AND(eq("target_boss", "royal_shellsplitter"), is_false("shells_unlocked")),
      priority=70, severity="warning", sources=("M-20", "M-08"),
      advice="Royal Shellsplitter hits very hard against a shell-less crab. Beat Nephro first to unlock shell-wearing.",
      why="The optional boss is recommended after getting a shell."),

    R("BOS-08", "boss", "Heikea rewards aggression",
      AND(eq("target_boss", "heikea"), one_of("playstyle", ["blocker", "dodger"])),
      priority=55, basis="guide", sources=("M-20",),
      advice="Heikea's fight needs an aggressive approach: stay close and keep up the pressure rather than "
             "turtling. Beating him is also required before you can reach Topoda.",
      why="Guides say the fight needs aggression; Topoda is gated behind him."),

    R("BOS-09", "boss", "Learn Parry before Topoda",
      AND(eq("target_boss", "topoda"), lacks("skills_known", "parry")),
      priority=70, severity="warning", sources=("M-14", "M-20"),
      advice="Topoda's fight teaches parrying - learn Parry (and ideally Riposte) from the Moon Snail first.",
      why="The fight is built around parry."),

    R("BOS-10", "boss", "Mantis Punch for the Consortium",
      AND(eq("target_boss", "consortium"), lacks("adaptations_known", "mantis_punch")),
      priority=75, severity="warning", sources=("M-16", "M-20"),
      advice="You need Mantis Punch (from Topoda) to smash the Purple Qube that blocks the way to The Consortium.",
      why="Mantis Punch destroys Umami-infused objects such as the Purple Qube."),

    R("BOS-11", "boss", "Ceviche Sisters are a group fight",
      eq("target_boss", "ceviche_sisters"),
      priority=55, basis="tactic", sources=("M-20",),
      advice="Two shrimp attack at once and constantly: treat it as a group fight, focus one target and keep moving.",
      why="The fight has two attackers with constant general attacks."),

    R("BOS-12", "boss", "Voltai",
      eq("target_boss", "voltai"),
      priority=55, sources=("M-20", "M-18"),
      advice="Voltai attacks from four holes with electronic devices; below 50% the arena fills with trash and "
             "poison, giving you less room. The Rubber Band stowaway ignores her electric attacks.",
      why="Documented arena behaviour and the Rubber Band counter."),

    R("BOS-13", "boss", "Petroch's rolling attack",
      eq("target_boss", "petroch"),
      priority=50, sources=("M-20",),
      advice="Petroch conjures crystals and has a devastating rolling attack: learn its timing and dodge the roll.",
      why="Documented attack pattern."),

    R("BOS-14", "boss", "Heavy shell against Petroch",
      AND(eq("target_boss", "petroch"), eq("shell_weight", "L")),
      priority=60, sources=("M-20", "M-06"),
      advice="A heavy shell makes Petroch's roll harder to dodge - consider a lighter shell for this fight.",
      why="Shell weight sets dodge speed."),

    R("BOS-15", "boss", "Inkerton mixes ranges",
      eq("target_boss", "inkerton"),
      priority=50, sources=("M-20",),
      advice="Inkerton mixes short-, medium- and long-range attacks: arrive with full pods and a fresh shell. "
             "Spearfishing or Wave Breaker can close the gap if you know them.",
      why="Documented range mix; the skills are gap-closers."),

    R("BOS-16", "boss", "Long multi-phase fights",
      AND(one_of("target_boss", LONG_FIGHT_BOSSES), le("heartkelp_pods", 3)),
      priority=65, severity="warning", sources=("M-19", "M-17"),
      advice="Multi-phase boss and you carry few Heartkelp pods: rest at a Moon Snail Shell to refill them first, "
             "and look for the remaining Heartkelp Sprouts.",
      why="Camtscha, Praya Dubia and Firth have several phases."),

    R("BOS-17", "boss", "Repeated boss deaths",
      AND(eq("encounter_type", "boss"), ge("deaths_in_a_row", 4)),
      priority=50, basis="guide", sources=("M-24", "M-21"),
      advice="Several deaths in a row: watch one full attack cycle, swap to a shell or stowaway that counters the "
             "boss, and consider the Assist menu if the fight stops being fun.",
      why="Pattern learning plus the game's own accessibility options."),

    R("BOS-18", "boss", "Bosses without detailed notes",
      one_of("target_boss", UNDETAILED_BOSSES),
      priority=10, severity="info", sources=("M-19",),
      advice="This knowledge base has no verified boss-specific mechanics for this boss - the general boss, shell "
             "and survival rules above apply.",
      why="Honest fallback instead of inventing information."),

    # =====================================================================
    # 8. DODGING, BLOCKING, PARRYING & STAMINA  (DEF)
    # =====================================================================
    R("DEF-01", "defense", "There is no stamina bar",
      one_of("experience", ["some", "veteran"]),
      priority=20, severity="info", sources=("M-12",),
      advice="Unlike most Soulslikes there is no stamina bar: attacking and dodging do not drain a meter, so do not "
             "hold back. Manage shell durability instead.",
      why="Stamina management is replaced by shell durability."),

    R("DEF-02", "defense", "Shell-less: dodge into attacks",
      AND(is_true("shells_unlocked"), is_false("shell_worn"), is_false("nearby_shells")),
      priority=70, severity="warning", basis="guide", sources=("M-08", "M-11"),
      advice="Shell-less with none in reach: you cannot block, so dodge INTO attacks (i-frames) and look for a shell quickly.",
      why="Naked Kril relies entirely on dodging."),

    R("DEF-03", "defense", "Parry without a shell",
      AND(is_false("shell_worn"), has("skills_known", "natural_defenses")),
      priority=50, severity="info", sources=("M-13",),
      advice="Natural Defenses lets you parry even without a shell - release block just as the attack lands.",
      why="Natural Defenses grants shell-less parrying."),

    R("DEF-04", "defense", "Learn Parry",
      AND(eq("playstyle", "blocker"), lacks("skills_known", "parry"), ge("umami_crystals", 1)),
      priority=60, sources=("M-13", "M-07"),
      advice="Learn Parry at the Moon Snail: a well-timed parry negates the damage a plain block would deal to your shell.",
      why="Parrying avoids shell damage; blockers lose the most durability."),

    R("DEF-05", "defense", "Parry timing help",
      AND(has("skills_known", "parry"), is_true("parry_trouble")),
      priority=60, sources=("M-14", "M-21"),
      advice="Parry means releasing block just as the attack lands, not holding it. Practise on slow attackers; the "
             "Assist menu can widen parry timing and add i-frames.",
      why="Parry is timing-based and the game offers an assist for it."),

    R("DEF-06", "defense", "Conserve a worn shell",
      AND(one_of("shell_condition", ["worn", "critical"]), eq("playstyle", "blocker")),
      priority=65, severity="warning", group="defense_mode", sources=("M-07",),
      advice="Your shell is worn and you rely on blocking, which sends all damage into it. Mix in dodges and parries "
             "to conserve durability.",
      why="Blocking drains the shell; a break removes your main defence."),

    R("DEF-07", "defense", "Parry relentless combos",
      AND(eq("attack_style", "fast_relentless"), has("skills_known", "parry"),
          one_of("playstyle", ["blocker", "balanced"]), is_true("shell_worn")),
      priority=60, group="defense_mode", sources=("M-07", "M-14"),
      advice="Against fast combos a well-timed parry costs your shell nothing, where blocking every hit would "
             "wear it down. Parry the finishers and counter.",
      why="A perfectly timed block negates shell damage; more specific than CMB-03."),

    R("DEF-08", "defense", "Learn Riposte",
      AND(has("skills_known", "parry"), lacks("skills_known", "riposte"), ge("umami_crystals", 1)),
      priority=50, sources=("M-13", "M-15"),
      advice="Learn Riposte: after a parry you counter-attack and regain 1 Umami charge.",
      why="Riposte rewards a parry with damage and Umami."),

    R("DEF-09", "defense", "Learn Skedaddle",
      AND(eq("playstyle", "dodger"), lacks("skills_known", "skedaddle"), ge("umami_crystals", 1)),
      priority=45, sources=("M-13", "M-06"),
      advice="Learn Skedaddle: a quick backward dash that ignores shell weight, and the start of the Ebb and Flow combo.",
      why="Skedaddle is unaffected by shell weight."),
]


# ---------------------------------------------------------------------------
# Small helpers used by the UI and the tests
# ---------------------------------------------------------------------------
def rules_by_category():
    grouped = {key: [] for key in CATEGORIES}
    for rule in RULES:
        grouped[rule.category].append(rule)
    return grouped


def get_rule(rule_id):
    return next((r for r in RULES if r.id == rule_id), None)
