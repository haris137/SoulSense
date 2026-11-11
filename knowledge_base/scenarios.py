"""
scenarios.py - ready-made example players.

They are used by (1) the "Load an example" buttons in the UI, so a demo or a
viva can start instantly, and (2) the scenario unit tests, which check that the
expected rules fire for each of them.
"""

SCENARIOS = {
    "New crab facing Nephro": {
        "description": "Brand-new player, no shell yet, about to fight the first boss.",
        "facts": {
            "experience": "new", "playstyle": "dodger", "game_stage": "early",
            "current_area": "shallows", "shells_unlocked": False, "shell_worn": False,
            "nearby_shells": False, "vit": 2, "res": 0, "atk": 1, "msg": 0,
            "player_hp_pct": 100, "heartkelp_pods": 3, "heartkelp_sprouts_found": 0,
            "encounter_type": "boss", "target_boss": "nephro", "attack_style": "slow_heavy",
            "deaths_in_a_row": 2, "skills_known": [], "adaptations_known": [],
            "adaptations_equipped": [], "stowaways_equipped": [],
        },
    },
    "Blocker with a cracking shell": {
        "description": "Block-heavy veteran in a fast fight; shell nearly broken, spare shell nearby.",
        "facts": {
            "experience": "veteran", "playstyle": "blocker", "game_stage": "mid",
            "shells_unlocked": True, "shell_worn": True, "shell_durability_pct": 20,
            "shell_weight": "S", "nearby_shells": True, "encounter_type": "tough",
            "attack_style": "fast_relentless", "player_hp_pct": 70, "res": 1, "vit": 8,
            "skills_known": ["parry", "kintsugi"], "umami_crystals": 3,
            "adaptations_known": [], "adaptations_equipped": [], "stowaways_equipped": [],
        },
    },
    "Low on everything at Firth": {
        "description": "Late-game, low HP, no pods and far from a checkpoint before a long boss fight.",
        "facts": {
            "experience": "some", "playstyle": "balanced", "game_stage": "late",
            "shells_unlocked": True, "shell_worn": True, "shell_durability_pct": 55,
            "shell_weight": "M", "shell_spell_role": "self_heal", "player_hp_pct": 25,
            "heartkelp_pods": 0, "near_moon_snail": False, "encounter_type": "boss",
            "target_boss": "firth", "enemy_hp_pct": 100, "skills_known": [],
            "adaptations_known": [], "adaptations_equipped": [], "stowaways_equipped": [],
        },
    },
    "Rich and far from a checkpoint": {
        "description": "Carrying 12,000 microplastics with no Moon Snail Shell nearby.",
        "facts": {
            "experience": "some", "playstyle": "aggressor", "game_stage": "mid",
            "microplastics": 12000, "near_moon_snail": False, "umami_crystals": 4,
            "vit": 6, "skills_known": [], "adaptations_known": [], "adaptations_equipped": [],
            "stowaways_equipped": [],
        },
    },
    "Voltai with a heavy shell": {
        "description": "Electric boss fight, below half health, wearing a worn heavy shell.",
        "facts": {
            "experience": "veteran", "playstyle": "balanced", "game_stage": "mid",
            "shells_unlocked": True, "shell_worn": True, "shell_durability_pct": 45,
            "shell_weight": "L", "encounter_type": "boss", "target_boss": "voltai",
            "attack_style": "electric", "enemy_hp_pct": 40, "player_hp_pct": 80,
            "skills_known": [], "adaptations_known": [], "adaptations_equipped": [],
            "stowaways_equipped": [],
        },
    },
    "Unhappy with the build": {
        "description": "Mid-game player whose shells keep breaking and who wants to respec.",
        "facts": {
            "experience": "some", "playstyle": "blocker", "game_stage": "mid",
            "vit": 10, "res": 0, "atk": 4, "msg": 0, "main_problem": "shells_breaking",
            "unhappy_with_build": True, "shark_eggs": 1, "umami_crystals": 6,
            "microplastics": 3000, "skills_known": [], "adaptations_known": [],
            "adaptations_equipped": [], "stowaways_equipped": [],
            "stowaway_capacity_free": False,
        },
    },
}
