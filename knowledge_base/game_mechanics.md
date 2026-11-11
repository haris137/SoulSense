# Another Crab's Treasure – Verified Mechanics Reference

This file is the **evidence base** of SOULSENSE. Every rule in
`knowledge_base/rules.py` cites one or more of the fact IDs below (`M-01`, `M-02`, …)
in its `sources` field. A unit test checks that every cited ID really exists here.

*Compiled on 8 Nov 2026 from public guides, reviews, patch notes and the game's wiki
page (list at the bottom). The game is a 2024 release (Aggro Crab, 25 Apr 2024) and has
received patches, so **numbers can drift** – always confirm against your in-game menus.*

**Confidence labels**
- **V** – stated consistently by two or more independent sources
- **S** – stated by a single source (kept, but flagged)
- **G** – a community-guide *recommendation* (opinion), not a hard mechanic

---

## M-01  Basics (V)
Kril is a hermit crab who uses trash as shells. A shell acts as armour, shield and
"spell" at the same time. The game is a Soulslike with dodges, blocks and parries, but
the shell/durability system replaces much of the usual defensive resource management.

## M-02  Microplastics (V)
Microplastics are both currency and experience. On death all carried microplastics are
dropped; they can be recovered by returning to the death site. Dying again before
reaching them makes them disappear permanently. The Assist menu has an option to
prevent microplastic loss on death and (patch notes) a "Recover Microplastics" button.

## M-03  Moon Snail Shells (checkpoints) (V)
Moon Snail Shells are the bonfire equivalent: you rest, heal, refill Heartkelp pods,
level up, spend microplastics and fast-travel. **Resting respawns the common enemies**
(Kotaku). Dying to most bosses offers a respawn at a floating Moon Jelly instead of the
nearest Moon Snail Shell.

## M-04  Stats (V for effects, G for priorities)
Four stats, levelled with microplastics at a Moon Snail Shell:

| Stat | Effect |
|------|--------|
| VIT  | +5 HP per point (GameSkinny) |
| RES  | reduces the damage your *shell* takes before it breaks; improves status resistance; also gates stowaways |
| ATK  | +7 % physical strike damage per point (GameSkinny, **S** for the exact number) |
| MSG  | strengthens Umami abilities (the game's magic) |

Guide opinions **disagree** on the first stat: Sportskeeda – VIT to at least 5 first;
GameSkinny – ATK with "a little VIT"; Dot Esports / TheGameCrater – RES. SOULSENSE
therefore gives playstyle-dependent advice (see group `stat_priority`).

## M-05  Respec (V, price S)
- Stats: Moon Snail Shell → Level Up → recycle icon, costs **1 Shark Egg**, refunds all
  spent microplastics. Becomes available after you first visit the treasure map.
- Skills: a refund resets the *whole* tree (1 Shark Egg).
- Adaptations: reset at Grovekeeper Topoda (1 Shark Egg), crystals refunded.
- Pro Game Guides reports a Shark Egg sold in New Carcinia (Upper Crust) for 2,000
  microplastics (**S**); Dot Esports says eggs are in limited supply.

## M-06  Shell statistics (V)
Each shell has **DEF** (its durability), a **weight class** (S/M/L) that changes the
speed of your dodge roll, and one **shell spell** that costs Umami charges. Heavier
shells have more durability but slower dodging; light shells are fragile but mobile.
About 69 shells exist. Examples: *Munch* (spend shell health to restore Kril's health),
*Fizzle* (bubbles that wear health and raise stagger, 1 Umami), *Twist Top* (spin that
damages nearby enemies, 1 Umami), *Rollout* (roll forward, 1 Umami).

## M-07  How shells take damage (V)
Taking a hit damages both your HP and your shell. Blocking sends **all** damage into the
shell. At 0 durability the shell breaks. A perfectly timed block (parry) negates the
damage the shell would have taken. RES lowers the damage dealt to the shell.

## M-08  Being shell-less ("naked") (V)
No shell means no shell spell, far less damage reduction and no block – you rely
on dodging. Players start without a shell; wearing shells is unlocked by defeating the
first boss, Nephro. The skill **Natural Defenses** lets a naked Kril parry. The
adaptation **Snail Sanctum** summons a shell of pure Umami when naked.

## M-09  Shell insurance (V)
Insurance is purchased per shell and makes an insured shell come back with you after
death. Prices vary by shell (e.g. Banana Peel 200, Yoccult 1,500 microplastics). A Baby
Shoe bought at Shellfish Desires is insured automatically.

## M-10  Stagger and Capsize (V)
Attacking fills a yellow **stagger bar** under the enemy's health. When it is full the
enemy is stunned briefly – the main damage window. **Capsized** enemies can be hit on
weak spots with the *Dispatch* skill. The Bubble Bullet adaptation (Lv. 2) can capsize.

## M-11  Dodge i-frames (V, G for the tip)
Dodging has invincibility frames. Guides advise dodging **into** an attack rather than
away from it, because backing away can still leave you in the hitbox.

## M-12  No stamina bar (V)
Dot Esports and GodisaGeek both note the game has no stamina bar; stamina management is
replaced by shell durability. You can attack and dodge freely.

## M-13  Skill tree (V)
Unlocked by speaking to the Moon Snail in its domain; paid for with purple **Umami
Crystals**. Three "Ways": Hermit (defensive/Umami), Predator (attacks), True Crab
(utility/natural defences). Skills used by SOULSENSE:

| Skill | Effect |
|-------|--------|
| Shelleportation | teleport between found Moon Snail Shells |
| Housewarming | each shell's spell can be cast once for free |
| Umami Training | +5 MSG (three copies, +15 total) |
| Circle of Life | killing with an Umami attack returns 1 charge |
| Elusive Prey | brief invincibility when your shell breaks (attacking early ends it) |
| Skedaddle | quick backward dash, unaffected by shell weight |
| Ebb and Flow | spin attack right after a Skedaddle dodge |
| Dispatch | big damage on weak spots of Capsized enemies |
| Spearfishing | throw your fork to reel an enemy in (uses a Barbed Hook; large enemies harder) |
| Wave Breaker | grapple an aimed-at enemy for a momentum blow |
| Parry | release block as an attack lands to parry it |
| Aggravation | after your shell takes a blocked hit, next attack deals more damage |
| Self-Repair | recently lost shell health returns while you deal damage |
| Kintsugi | shell regenerates fully after breaking, once per rest |
| Riposte | counter-attack after a parry; restores 1 Umami charge |
| Natural Defenses | parry even while naked |

(Pro Game Guides lists the skill as "Elusive Pray"; we use "Elusive Prey".)

## M-14  Parry and Riposte (V)
Parry is a **skill**, not a default move (one guide's "you can't parry" refers to the
start of the game). The Grovekeeper Topoda fight is described as the one that teaches
parrying. Parry timing and extra i-frames can be eased in the Assist menu.

## M-15  Umami charges (V)
Shell spells and adaptations spend Umami charges. Charges are returned by Riposte
(after a parry) and Circle of Life (kill with an Umami attack); Housewarming makes the
first cast of each shell's spell free.

## M-16  Adaptations (V, upgrade costs S)
Eight adaptations; you may carry **two**. They cost Umami charges and come from bosses
or side activities: Royal Wave (Magista; briefly increases damage enemies take),
Bubble Bullet (Ceviche Sisters), Eelectrocute (Voltai; shocks nearby enemies),
Snail Sanctum (Petroch), Bobbit Trap (Sands Between), Mantis Punch (Topoda; smashes
Umami-infused objects such as Purple Qubes), Tactical Tentacle (Consortium),
Urchin Toss (Urchin in New Carcinia). Upgrades happen at Grovekeeper Topoda: Lv. 2
costs 25 and Lv. 3 costs 50 purple crystals (HermitGamer, **S**).

## M-17  Healing (V)
Healing uses **Heartkelp pods** with a single button. All pods refill when you rest at a
Moon Snail Shell. Six **Heartkelp Sprouts** are hidden in the world; each adds one pod
(the first is near the Mooncave in the Duchess's castle).

## M-18  Stowaways (V, prices S)
Passive trinkets with a limited capacity (increased at vendors in New Carcinia; the first
increase costs 2,500 microplastics, **S**) and stat requirements.
- Whelk / Whelk+ / Whelk++: +15 / +30 / +45 % shell-spell damage; need 2 / 7 / 13 RES.
- Another Crab: revives you once, then is consumed (3,000 microplastics, **S**).
- Used Bandage: +15 % healing effectiveness.
- Fruit Sticker: more microplastics from kills.
- Rubber Band: lets you ignore electric attacks (trivialises Voltai).

## M-19  Bosses (V)
18–19 bosses depending on how they are counted. Mandatory: Nephro, Magista, Pagurus,
Diseased Lichenthrope, Heikea, Ceviche Sisters, Voltai, Roland, Petroch, Inkerton,
Camtscha, Praya Dubia, Firth. Optional: Royal Shellsplitter, Curdled Carbonara
Connoisseur, Grovekeeper Topoda, The Consortium, Scuttling Sludge Steamroller.
(HermitGamer marks Consortium optional; other lists differ – SOULSENSE does not depend
on it.) **Diseased Lichenthrope, Heikea and Voltai become stronger below 50 % health.**
Camtscha and Praya Dubia have two phases; Firth (final boss) has several.

## M-20  Boss-specific notes
- **Nephro** (V): slow, large sword swings; watch the wind-up; hit from the sides or
  behind. Defeating him unlocks shell-wearing. Level up a few times first.
- **Magista** (S): beaten with a Soda Can shell and by staggering her; grants Royal Wave.
- **Royal Shellsplitter** (S): optional early boss; hits very hard against a shell-less
  Kril, so get shell-wearing first.
- **Heikea** (V): one of the hardest; the fight needs an aggressive playstyle. Must be
  beaten before you can reach Topoda.
- **Grovekeeper Topoda** (V): optional; teaches parry; rewards Mantis Punch and the
  ability to upgrade adaptations.
- **The Consortium** (V): hit weak spots and dodge; you need Mantis Punch to destroy
  the Purple Qube that blocks the way to it.
- **Ceviche Sisters** (V): two shrimp at once that attack constantly.
- **Voltai** (V): attacks from four holes with electronic devices; below 50 % the arena
  fills with trash and poison, giving you less room.
- **Petroch** (V): conjures crystals and has a devastating rolling attack.
- **Inkerton** (V): short-, medium- and long-range attacks.
- **Camtscha, Praya Dubia, Firth** (V): multi-phase, long fights.

## M-21  Assist menu (V)
Options include: more shell durability, less damage taken, lower enemy health, more
damage dealt, extra i-frames and parry timing, slower game speed, and keeping
microplastics on death.

## M-22  Hazard: Sands Between (V)
X marks on the sand in the Sands Between are hidden traps that destroy your shell and
can kill you. The area is also full of enemies.

## M-23  Boss arenas contain shells (V)
Reviews note that good shells are scattered everywhere and boss arenas contain plenty,
so a broken shell can usually be replaced mid-fight.

## M-24  Enemy behaviour (G)
Digital Trends observes that enemies attack quickly and relentlessly, so blocking is
emphasised over dodging in many encounters. Some common enemies (e.g. hammer-swinging
crabs) are as dangerous as bosses (Kotaku).
Sportskeeda also advises memorising enemy attack patterns on a first encounter.

---

## Known disagreements between sources
| Topic | Disagreement | How SOULSENSE handles it |
|-------|--------------|--------------------------|
| First stat to raise | VIT vs ATK vs RES | playstyle-specific rules in group `stat_priority` |
| Parry | "can't parry" vs Parry skill | treated as a learnable skill (M-14) |
| Stowaway capacity | "3 slots" vs "4 points" | no numeric capacity claimed |
| Topoda spelling | Grovekeeper / Gravekeeper | uses *Grovekeeper* |
| Consortium | optional vs mandatory | no rule depends on it |

## Heuristic thresholds (NOT game mechanics)
These numbers are choices made by the system designer so that rules can classify
percentages; they are constants at the top of `rules.py` and are labelled as such in the UI.

| Constant | Value | Meaning |
|----------|-------|---------|
| `SHELL_CRITICAL_PCT` | 30 | shell durability at or below this = *critical* |
| `SHELL_WORN_PCT` | 60 | at or below this = *worn* |
| `HP_LOW_PCT` / `HP_HURT_PCT` | 35 / 60 | HP bands |
| `GROUP_SIZE` | 3 | enemies counted as a "group fight" |
| `MANY_MICROPLASTICS` | 5000 | carrying enough that a death hurts |
| `ENRAGE_HP_PCT` | 50 | phase-change point (M-19) |

## Sources consulted
- Wikipedia entry for the game (release, microplastic loss, Moon Snail Shells, Moon Jelly)
- Pro Game Guides – Umami skill tree list; best shells (Yoccult, Valve, Gacha Capsule)
- HermitGamer – adaptations table; full boss list with locations and rewards
- GameSkinny – stats explained (VIT +5 HP, ATK +7 %); stowaway capacity; Heartkelp sprout
- Sportskeeda – combat tips (stagger bar, i-frames, VIT first, parry/riposte); boss tier list
- Dot Esports / The Escapist / TheGameCrater – stats, respec, shells, Heartkelp sprouts, stowaways
- Digital Trends – best stowaways (Rubber Band, Another Crab); GameSpot, RPGamer, Slant, GodisaGeek, Jimquisition reviews
- Kotaku – Heartkelp, Moon Snail Shell respawn behaviour; best skills guide
- Siliconera / Prima Games / PC Invasion – Nephro, Magista, early shells, shell insurance
- hard-drive.net patch notes – Assist menu additions, Moon Jelly/insurance fixes
