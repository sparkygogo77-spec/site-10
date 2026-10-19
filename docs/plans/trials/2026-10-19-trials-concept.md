# Trials and challenges: concept (2026-10-19)

J (2026-10-19): "draft trials and challenges like a spider cave that has only one proper entrance with larger than
normal and more animated spiders that climb walls with a mother spider deeper all made of fear, I want good
conceptualization."

**Status:** concept only. There are no Blender builds and no code yet. This is a design draft for J to pick from. Builder chats take
the Blender passes later, and the mc chat takes the systems.

**Builds on what already exists:**
- `Corps.YELLOW` is "fear". Its effects already in the game are `FearEffect`, `FearFog`, `FearVignette`, `FearBlind`,
  `FearFrenzy` and `FearNuke`.
- Pass 863 has the fear-consumed mob gear: Y1 scales, Y2 lightning, Y3 dread.
- Pass 854 has the E1c stalkers. J rated E1c2 Skitter and E1c3 Unfolding Crawler IMPROVE.
- J's 845 note asked for "yellow Ender spiders teleporting in from above".
- The Yellow construct strips Y1-Y3 are in `docs/texture_library/yellow/`.

**Picture:** `cave_map.png` (next to this file), a side section of the cave drawn with Pillow.

---

## Part 1. The flagship trial: the Dread Warren (fear spider cave)

### The idea in one line

The Dread Warren is a cave that fear built. Every web, egg and spider in it is yellow hard light: a living construct
with no Lantern behind it. The only steady light inside is your own ring, and the cave wants to put it out.

### The core mechanic: Dread versus Will

Everything in the Warren runs on one meter, **Dread**, from 0 to 100. It shows as the existing `FearVignette`
tightening from the edges of the screen.

**What raises Dread:**
- standing in darkness;
- being bitten;
- seeing a spider drop from the ceiling within 4 blocks;
- the Mother's screams;
- running away (sprinting *away* from a spider that is chasing you).

**What lowers Dread:**
- standing your ground (facing a spider as it charges);
- killing spiders;
- burning webs with green light;
- lit braziers you have rekindled.

**What Dread does:**

| Dread | Effect |
|---|---|
| 0-30 | Normal. The ring light reaches its full radius (about 9 blocks). |
| 30-60 | The light radius shrinks to 6 blocks. Whispers start. Webs at the edge of your vision appear to twitch, and some of them are spiders. |
| 60-85 | The light shrinks to 4 blocks, with flicker. Egg sacs within 12 blocks start hatching. `FearFog` thickens. |
| 85-100 | The ring gutters. Every 3-5 s the light cuts out completely for half a second, and you see only the spiders' yellow glow. At 100 you get `FearBlind` for 3 s and the brood swarms. |

**The counter: Will.** A Green ring can spend charge on a **Will Flare** (the ring's existing charge, no new resource):
- Hold use with the ring arm raised (the FearNuke "constructing" pose).
- The light grows into a green sphere. On release it pulses outward over 8 blocks.
- It burns webs to drifting green ash and staggers spiders, which flip onto their backs for 1 s.
- It knocks Dread down by 25.

This turns the ring into the hero of the cave. The trial is about light being a thing you *spend*.

Other corps play it differently (see decision 2):
- **Red:** rage. Dread rises *slower* while you are attacking, but Red can't flare.
- **Blue:** hope. A slow passive Dread drain.
- **Yellow:** the brood is wary of you. Spiders hesitate, but the Mother hates you more.

### Finding it: one true entrance

- **Where:** it generates rarely, buried in deepslate under dark forests, old-growth spruce taigas and swamps. That puts it near
  y -20 to -50, under the surface.
- **The tell on the surface:** a dead patch. The grass is grey, and there is a ring of trees with yellow cobweb-light threads strung
  between their trunks that glint only at night. Cattle and villagers won't walk through it.
- **The true entrance, the Maw:**
  - a sinkhole in the middle of the dead patch, 5 blocks wide;
  - its rim is ringed with hard-light silk curling *inward* like eyelashes;
  - a spiral of webbed ledges leads down the shaft.
  - It's the only way in that leads to the nest.
- **The false entrances:**
  - 2-3 other openings on hillsides nearby, which look like normal caves with old webs.
  - Each goes 15-30 blocks and ends in a **collapsed throat**: rubble choked with yellow silk.
  - Behind the silk you can hear skittering, but you can't get through. Mining the rubble just collapses more on you,
    and the silk regrows behind you.
  - The lesson: fear lies about where the way in is. These false caves are also where the first scouts find you and
    retreat, *pulling you toward* the Maw.
- **Anti-cheese:**
  - The Warren's blocks are **Dread Stone**, deepslate soaked in fear. You can mine it, but slowly (like obsidian), and
    it **regrows** from the walls in 30 s.
  - Tunnelling straight down to the Mother does work, but you arrive in the arena at Dread 100 with the whole brood
    awake.
  - So the honest path is the fast path.

### Layout: from the Maw to the nest

The cave is a descending chain of **zones**. Each zone teaches one spider behaviour, then the next zone combines it with
the earlier ones. Total depth is about 60 blocks. A careful first run takes about 20-25 minutes.

```
 SURFACE   dead grove        ~ ~ ~ ~ (false cave A)  ...rubble+silk X
 ------------\      /------------------------------------------------------
              \MAW /   Z1  the Maw: spiral ledges down the shaft, web curtains
               |  |        lesson: spiders ON WALLS (they watch, they don't attack)
               |  |____
                \      \__ Z2  the Weave Gallery: tall hall, webs floor to ceiling
                 \________\    lesson: CEILING DROPS (shadows above you)
                        ||
                 _______||_____  Z3  the Hatchery: low wide room, egg sacs in the walls
                /  o  o   o  o \     lesson: HATCHING (Dread makes eggs burst)
                \______________/
                        ||
            ____________||________  Z4  the Bridge of Threads: a chasm, hard-light silk bridges
           |  ~~~~~ abyss ~~~~~   |    lesson: PACKS + WEAVERS (spiders cut the bridges)
           |______________________|
                        ||
                   _____||_____   Z5  the Hollow (rest): a dead Lantern-bearer's camp, a brazier to rekindle
                  |   (*)  ⌂   |      no spiders; checkpoint; lore
                  |____________|
                        ||
          ______________||______________
         /   ^^^^ web dome ceiling ^^^^   \   Z6  the Brood Heart: domed arena, 30 blocks across
        |       . . MOTHER . .             |      the Mother hangs in the dome
        |   pillars        pillars         |
         \__________(heart-crystal)_______/
```

```mermaid
flowchart TD
  S[Dead grove on surface] --> M[Z1 Maw: wall-watchers]
  S -.-> FA[False cave A: collapsed throat]
  S -.-> FB[False cave B: collapsed throat]
  FA -. scouts retreat toward .-> M
  M --> G[Z2 Weave Gallery: ceiling drops]
  G --> H[Z3 Hatchery: Dread hatches eggs]
  H --> B[Z4 Bridge of Threads: packs + weavers]
  B --> R[Z5 the Hollow: rest, brazier, lore]
  R --> A[Z6 Brood Heart: the Mother]
  A --> X[Exit: the Mother's silk lifts you up the Maw]
```

#### Z1: the Maw (descent, 15 blocks)

- **Shape:** a spiral of ledges round a shaft, with web curtains you push through. Each curtain parts like a bead
  curtain and glows briefly where you touched it.
- **Light:** daylight from the sinkhole fades over the first 10 blocks. By the bottom the ring is the only light.
- **The beat:**
  - Spiders are already on the walls *across the shaft*, motionless, eyes lit.
  - When your ring light reaches one, it skitters out of the light, round the shaft wall, and stops again just at
    the edge.
  - They never attack here. They escort you down.
- **Lesson:** spiders climb walls and they don't like your light.

#### Z2: the Weave Gallery (tall hall, 25 tall)

- **Shape:** a long nave with webs strung floor to ceiling like stained glass. The silk is yellow, with slow-gliding
  Y3 dread texture.
- **The beat:**
  - You hear skittering *above*. Shadows of legs slide across the webs you're lit through. That shadow is
    projected from your own ring light, so it only happens because you're carrying the light.
  - Then the first **drop**: a Hunter lets go of the ceiling and falls on a silk thread. It stops 2 blocks above
    your head, hanging upside-down, and stays there for one beat. Then it drops the rest of the way and attacks.
- **Lesson:** look up.

#### Z3: the Hatchery (low wide room)

- **Shape:** a ceiling only 4 blocks high. The walls are honeycombed with **egg sacs**: translucent yellow pods with
  a curled spiderling silhouette inside, pulsing with your heartbeat sound.
- **The beat:**
  - The eggs respond to Dread. While it's under 40 they sleep.
  - Over 40, the nearest ones crack: light leaks out of the cracks first (the gold-crack language from the lantern),
    then broodlings pour out.
  - A Will Flare *can* burn eggs before they hatch, so this is where players learn to spend light to save trouble
    later.
- **Lesson:** your fear feeds the nest.

#### Z4: the Bridge of Threads (chasm)

- **Shape:** a black abyss with no bottom you can see (a fall into it lands in a web net 20 blocks down, at Dread
  +40). The only way across is **hard-light silk bridges**: thick braided strands sagging like rope bridges, glowing
  faintly.
- **The beat:**
  - **Weavers** (see below) cling under the bridges. They cut strands behind you and spin new ones ahead in the
    wrong direction.
  - A **pack** of Hunters comes along the cave walls on either side, moving faster than you can on the bridge.
  - A Green ring can build its own Bridge construct here. That is a deliberate answer, and it costs charge you
    may want for the Mother.
- **Lesson:** packs, flanking, and the cave changing under you.

#### Z5: the Hollow (rest)

- **Shape:** a small dry chamber with no webs.
  - **The camp:** a long-dead Lantern-bearer's camp, a bedroll and a cold brazier.
  - **The ring:** a cracked ring lies in the bedroll. It's a plain grey ring, not a Corps one.
  - **The book:** a journal of 4 pages, ending mid-sentence.
- **The beat:**
  - Rekindling the brazier with the ring sets a **checkpoint**: you respawn here if you die further in. Dread
    resets to 0.
  - It's the only silence in the trial. The music drops out completely and you hear only distant breathing.
- **Purpose:** pacing. You need the exhale before the boss.

#### Z6: the Brood Heart (boss arena)

- **Shape:** a dome 30 blocks across and 20 high.
  - **The ceiling:** one huge web, sagging like a tent.
  - **The pillars:** eight around the edge. They are pillars of fused silk with old prey cocooned in them: villagers
    and an iron golem, shapes you can just make out.
  - **The heart-crystal:** in the middle of the floor, a pulsing yellow crystal half-buried in the stone. This is the
    nest's "lantern", the thing all this fear is charged from.
- **The beat:** on entering, the brazier light behind you goes out, the exit seals with silk, and the Mother is
  revealed (see her section).

### How the cave reads visually

- **Darkness is the canvas.**
  - Dread Stone is near-black deepslate with faint yellow veining, like the lantern's gold lightning cracks. The
    cracks pulse very slowly (frametime 5, loops of 8-10 s), per J's construct rule "never static, but not fast".
  - Nothing in the cave emits block light except the heart-crystal, the rekindled brazier, and the faintly glowing
    silk (light level 1-2, enough to outline and no more).
- **The ring is the lamp.** The ring casts real block light with a radius set by Dread (the 860 rule: block light that
  lights the vicinity and fades, never screen-space rays). This is the most important visual in the trial: J's green
  light pushing into a yellow world.
- **Hard-light silk.**
  - Strands are thin, readable lines, never faint particles. J rejected faint particles for beams; same rule.
  - Each strand is a dark core with saturated yellow edges, 70-90% opaque.
  - Thick strands use a slow Y1 scale texture gliding along their length.
  - Sheets of web are translucent panes, which the ring light catches and sends glinting.
- **Burnt silk.** When green light burns a web, it disintegrates pixel by pixel into falling green-and-yellow ash. This
  is J's loved "cover disintegrating" language.
- **Dread fog.** Low, ground-hugging yellow-grey fog that thickens with Dread (`FearFog`, but layered in the cave).
- **Colour discipline.** Yellow = them, green = you. Nothing in the cave is green except what your ring does.

### The spiders: the Brood

All of them are fear constructs:
- **Bodies:** hard-light shells (Y1/Y3 looks) over a dark core, with darker undersides.
- **Glow:** eyes and joints glow.
- **Death:** they don't bleed. They crack, the light gutters out, and they crumble into silk ash.

**How they move matters more than how they look.** J's E1c note was "animations for movement", and the request says
"more animated".

| Type | Size (vanilla spider = 1x) | Role | Movement and behaviour |
|---|---|---|---|
| **Broodling** | 0.5x | swarm, from eggs | Fast twitchy bursts, then freeze (the E1c "step-step-freeze" read). Comes in groups of 6-12. Weak alone; the danger is that they raise Dread fast. |
| **Hunter** | 1.6x (2.2 blocks across) | the main fighter | Walls and ceilings. Drops on a thread. Leaps 6 blocks at the player from a wall. Circles at the edge of the light before committing. |
| **Weaver** | 1.3x, long thin legs | support | Stays out of reach. Spits silk that slows you (vanilla cobweb, but a hard-light one that a Will Flare burns). Cuts and spins bridges. Rebuilds webs you burned. |
| **Stalker** | 2.5x, stilt legs (from E1c2/E1c3) | mini-boss in Z4 | Tall and slow, always facing you. Unfolds from a folded crouch (E1c3). Only one per run. |
| **Dread Phantom** | 1.0x, translucent | ambush (J's "Ender spiders teleporting in from above") | Blinks in from the ceiling darkness in a puff of yellow static, right behind you. Only spawns when Dread is over 60. |

**The animation language (the "more animated" part):**
- **Legs that plant.**
  - Each leg has its own foot target on the surface (wall, floor or ceiling).
  - The body glides while legs step in alternating sets of four, 1-3 at a time, like a real spider.
  - Feet stay pinned to the block until they lift. This is procedural leg IK, done in code at render time (see
    Part 4), not baked loops, so they cling to any wall shape.
- **Body sway and bob** on each step, and the abdomen lags behind the body a little (secondary motion).
- **Idle twitches:**
  - A leg tests the ground.
  - Pedipalps clean the fangs.
  - The abdomen breathes light: it brightens and dims on a 3 s cycle.
- **Stillness, then sudden motion.** This is the 854 scary rule. Spiders freeze completely when looked at directly
  (like they're unsure), then burst into motion when you look away, or the moment your light flickers.
- **Ceiling drop:** let go, fall on a silk thread that visibly pays out from the spinnerets, stop with a bounce, rotate
  to hang upside-down, then drop onto the target.
- **Turning on a corner:** when a Hunter walks from the floor onto the wall, its body rolls 90 degrees over 4-6 ticks,
  legs reaching ahead to grab the new surface first.
- **Pack behaviour:**
  - Hunters stalk at the light's edge and rotate positions round you.
  - One feints from the front while another drops from behind.
  - If one Hunter is killed in a Will Flare, the others retreat into the dark for 3 s. They fear the green too.
- **Death:**
  - The legs curl inward (the real-spider death pose).
  - The body light gutters out from the abdomen forward.
  - Then the shell cracks along its plates and crumbles.

### The Mother: the Brood Matron

- **Scale:** a 7-block leg span; the body is the size of a horse.
- **Silhouette:**
  - a swollen, lantern-shaped abdomen;
  - the abdomen's glass-like shell is crazed with gold lightning, like a broken Power Battery made of fear;
  - you can see broodlings moving inside it.
- **The idea:** she *is* the nest's lantern. She is fear that learned to make more of itself.
- **The head:**
  - It has a crown of eyes. Eight of them glow, and two are dark and empty.
  - Her front legs are long and scythe-like, held folded like a mantis until she strikes.
- **The voice:** she doesn't hiss. She *whispers*: a layered, reversed-whisper sound. Her biggest attack is a scream that
  pushes Dread up by 30.

**The arena (Z6) is designed around her:** the dome web is her territory, the pillars are cover (and her
perches), and the heart-crystal is her weakness.

**Phase 1: "She is above you"** (100-70% health)
- She stays on the dome ceiling. You see her only as moving shadows on the web and as eight lights.
- She **drops broodlings** in clumps, and **drops herself** at you on a thread, striking with her scythes and
  climbing back up within 2 s.
- To hurt her: hit her while she's down. Or **burn the dome web** with Will Flares or beams: each burnt section is
  ceiling she can no longer walk on.
- Burning about 50% of the dome forces phase 2.

**Phase 2: "She comes down"** (70-35%)
- With not enough ceiling left, she falls to the floor and fights on the ground and the pillars.
- She **spins silk walls** across the arena to split it into lanes (these are fear constructs; Green Wall constructs
  can block them).
- She **cocoons**: one hit from her web shot wraps you. Break out by mashing use (each press flares the ring), or let
  a teammate cut you free.
- Her egg sacs on the pillars hatch whenever Dread is over 60.
- She **feeds on fear**: if a player is at Dread 85+, she heals by draining it from them, shown as a yellow stream from
  player to her abdomen. This is the moment the trial's mechanic pays off. Players who kept their Dread low starve
  her.

**Phase 3: "Lights out"** (35-0%)
- She screams and puts out **every light**:
  - the ring goes dark (it can't be relit for 5 s);
  - your screen goes to `FearBlind`;
  - the only things visible are her glowing abdomen and the heart-crystal.
- She hunts in the dark, and the spiders' eyes are all you see.
- **The counter is will:**
  - Standing still and holding use for 3 s reignites the ring by force: a big green burst, the "charge starting"
    dissolve J loves.
  - The ring then burns *brighter than before* for 10 s: a full overcharge.
  - In that window her shell cracks open where the gold lightning is.
- **The finish:**
  - Get a **Will Flare** or a melee hit to land in the cracked abdomen; that makes her collapse.
  - Then **plunge the ring into the heart-crystal**: hold use while standing on it, a 3 s channel. While you channel,
    the remaining spiders rush you and your teammates defend you.
  - The crystal turns from yellow to green from the inside out, the whole web dome burns in a wave, and every
    spider in the cave crumbles at once.

**After:**
- The nest is silent. A green light now pulses where the yellow crystal was.
- The Mother's last silk thread lowers from the dome, and grabbing it lifts you up a hidden shaft to the surface. That
  is the second exit, and it only exists once she's dead.
- The dead grove on the surface regrows over the next day.

### Sound and pacing beats

| Beat | Sound | Music |
|---|---|---|
| Surface dead grove | wind, no birds, a faint high whine near the threads | none |
| Z1 descent | your footsteps echo; distant skitters, too many legs, too fast | low drone fades in |
| First wall-watcher seen | one sharp dry click, then silence | drone holds |
| Z2 ceiling shadows | skittering directly above, panning across | heartbeat pulse joins |
| First drop | the thread *zips*, a creak as it stops, then nothing for one beat | everything cuts to silence for that beat, then a stab |
| Z3 Hatchery | eggs pulse in time with your heartbeat; it speeds up with Dread | heartbeat leads |
| Z4 bridge | strands creaking under your weight, snaps as they're cut | percussion of legs |
| Z5 the Hollow | true silence, then distant breathing | silence (the exhale) |
| Z6 reveal | the brazier hisses out, the Mother's whisper from every direction | full theme |
| Phase 3 lights out | all sound muffles to a low ring, as if underwater; only her whisper is clear | music drops out |
| Ring relit | a rising green charge tone (the lantern charge sound) | the theme returns in a major key |
| Heart-crystal turns green | a long glassy resonance, webs crackling as they burn | resolve |

**Pacing rule:** every scare is preceded by a quiet beat. The cave is mostly *tension*; actual fights are short and
sharp. That matches J's "fast and snappy" feel: no wind-ups, instant reactions.

### Rewards

- **Dread Silk** (material): drops from spiders, about 1-3 each. It's crafted into Ring Lab cosmetics and the items
  below.
- **Brood Heart Shard** (one per clear): the boss reward. It unlocks the following.

| Reward | What it does | Where |
|---|---|---|
| **Will Flare** (permanent) | The cave's Will Flare becomes a normal Green ring mode outside the trial: a light-pulse that clears webs and fear effects round you, and staggers mobs. | new RingMode |
| **Wallcrawl** | Construct claws let you climb walls (like the Hunters). Hold jump against a wall. | flight/movement upgrade |
| **Silkline** | A Tether variant: a hard-light thread to a ceiling or wall that you swing on or pull yourself up by. | Tether upgrade |
| **Dread Sight** | Briefly see fear-consumed and Yellow entities through walls (a yellow outline). | ring passive |
| **Silk construct look** | A new construct texture, the "W1 weave" language spun as web, unlocked in Green too. | Ring Lab > Constructs |
| **Matron trophy** | A Blockbench lantern-shaped trophy of her abdomen, which glows green now. | block |

---

## Part 2. More trials (one per emotion)

Each trial has its own emotion, biome, a "core meter" like Dread, and its own boss. All of them share the trial
framework in Part 3.

### The Bloodfurnace: Red, rage (Nether basalt deltas)

- **The idea:** a crater-forge where a dead Red corps was smelting rage into weapons. The rage never went out.
- **The meter is Heat:**
  - It **rises when you stand still** and falls when you attack.
  - The trial punishes caution: every second of hiding, lava rises in the crater channels.
- **The zones:**
  - the slag fields, where basalt columns burst with lava when you step on them;
  - the anvil hall, where giant hammers swing on chains and you have to time a dash through;
  - the crucible, a rising lava floor and a climb.
- **The boss: the Furnace Heart.**
  - It's a golem of molten red construct plates round a caged heart.
  - It throws your own rage back: the more damage you deal, the hotter its fists.
  - The counter is to *stop* at the right moment, letting it cool and crack, then hit the exposed heart.
  - So a rage trial is won by *controlling* rage.
- **Rewards:**
  - a **Red battery overcharge** (the 8 s charge goes to 12 s and doubles its blast);
  - **Magma Step**, which leaves burning footprints behind you while sprinting;
  - the R1 magma look upgrade.

### The Drowned Light: Blue, hope (deep ocean, monument-adjacent)

- **The idea:** a sunken lighthouse, and the crew's lights are still drifting down there.
- **The meter is Hope:** it falls over time and rises when you rescue a light.
- **The lights:**
  - Drowned villagers' souls drift in the dark water as small blue lanterns.
  - Lead them by swimming nearby: they follow your ring.
  - Abandon one and it goes out, and Hope drops.
- **The zones:**
  - the wreck field;
  - the kelp cathedral, where the current shifts every 10 s;
  - the drowned stair inside the lighthouse, flooding upward.
- **The boss: the Undertow.**
  - It's a whirlpool shape with a drowned keeper in its eye.
  - It pulls lights out of your escort.
  - The counter is the Renew/Restore modes, which give lights back.
- **Rewards:**
  - **Hope Golem** upgrade (it swims);
  - **Lantern-lit underwater breathing**, a bubble round the ring;
  - the B1-B3 construct looks finalised.

### The Mirror Garden: Violet, love (cherry grove plus an amethyst geode)

- **The idea:** a geode garden where every crystal reflects someone you care about, or wants to be them.
- **The meter is Devotion:**
  - Constructs you build in the garden become **crystal copies of you** that follow you.
  - The more you build, the more copies follow.
  - At the end, some copies turn on you.
- **The zones:**
  - the reflecting pool, where the floor is a mirror showing a different room;
  - the hedge-maze of amethyst, which re-routes when you look away;
  - the choir of crystals, a sound-puzzle where you play notes by striking crystals.
- **The boss: the Beloved.**
  - It's a crystal figure that takes your skin's shape.
  - It fights with *your own* last 5 ring modes.
  - The counter is the Crystal Prison: trap it in a geode while it's mid-attack.
- **Multiplayer:** in a party, each player's copy imitates a *teammate*, which is confusing in a good way.
- **Rewards:**
  - **Mind Link** upgrade;
  - **Crystal Prison** duration up;
  - the V1 crystal and V3 silk looks.

### The Hoard Vault: Orange, avarice (badlands mesa, buried)

- **The idea:** a treasure vault where taking things *costs you*.
- **The meter is Weight:**
  - Every item you pick up in the vault slows you, and gold in your inventory glows and makes noise that wakes
    things.
  - You can drop items anywhere to go faster.
- **The zones:**
  - the counting hall, where coins scatter and chime if you run;
  - the trap corridors, pressure plates you can see but greed makes you hurry;
  - the deep vault, full of loot.
- **The boss: the Hoarder.**
  - It's a construct shaped from **everything you picked up**: your own loot as its armour.
  - The more you took, the tougher it is.
  - A player who took nothing fights a fragile shell.
- **The twist:** you keep only what you carry out, so the choice of how much to take *is* the difficulty slider.
- **Rewards:**
  - **Steal** and **Hoard** upgrades;
  - the Orange construct look (still unpicked: this trial could force the pick).

### The Oath Spire: Green, will (a jagged mountain peak)

- **The idea:** the Green corps' own trial. There are no monsters. The mountain itself is the enemy.
- **The meter is Charge:**
  - There is no recharging and no lantern on the climb.
  - Every construct you make (ladders, bridges, walls against the wind) costs charge you can't get back.
- **The zones:**
  - the scree slope, which collapses under you;
  - the wind wall, a cliff with storm gusts that need a Wall construct to shelter behind;
  - the needle, a vertical pillar to the summit.
- **The summit:** a ruined lantern on a plinth.
  - Speaking the oath means holding use for 10 s while lightning strikes round you. It's the 816 X2 Oath animation
    J already wants.
  - That charges the ring fully and lights the lantern.
- **Rewards:** this is the trial that grants the **"true" Green ring**, with a gold emblem trim and +25% charge
  capacity. It also unlocks the 816 X4 "put the ring on" animation as the start-up pose.

### The Ender Brood: Yellow, the trial's echo (the End, outer islands)

- **The idea:** a short follow-up to the Warren. J's note asked for "yellow Ender spiders teleporting in from above".
  Once the Mother is dead, her brood's survivors fled to the End.
- **The fight:**
  - A floating web-island where Dread Phantoms teleport in.
  - It's a short arena challenge (5 minutes, survive and burn 6 nests).
  - This tests the Warren's lessons with teleporting spiders.
- **The boss:** none. Instead there's a "fear storm" finale where the island's webs drop away.
- **Rewards:** an Ender-silk Silkline (longer range), and a yellow-to-green end crystal trophy.

---

## Part 3. How trials fit the mod

### Triggers: how a player finds a trial

- **The lantern calls you.**
  - Once a player's ring has been charged 5 times at the Power Battery, the lantern shows a faint **compass flicker**.
  - Right-click the lantern while sneaking: the lantern's flare points in the direction of the nearest trial for
    3 s.
  - That's lore-friendly: the light *knows* where its enemies are.
- **Structures are worldgen.** Each trial is a rare structure in its biome, found by exploring or by the lantern hint.
- **Ring Lab > Trials tab:**
  - lists trials found, cleared and best time;
  - lets J **teleport into a test copy** of any trial for tuning (like the existing test menus).

### Difficulty

- **The ring's power level** decides the danger: charge cap, number of upgrades, the Dread rise rate.
- **Hard mode:**
  - Repeat clears unlock a "Deep" variant: more spiders and the Mother's phase 3 is longer.
  - Rewards are cosmetics: corrupted variants of the construct looks.
- **RingTuning entries** for every timing and threshold: the Dread rise rates, the light radii, the Mother's health,
  the regrowth time. J tunes them in the Ring Lab, as with every other power.

### Multiplayer

- **Dread is personal; the nest is shared.** Each player has their own Dread meter, but eggs hatch from the *highest*
  Dread in range. So a scared teammate is a danger to everyone. That's good drama.
- **Teammate actions:**
  - **Cut free:** cocooned players are freed by a teammate's hit.
  - **Calm:** standing next to a player at high Dread slowly lowers it (the "you're not alone" mechanic).
- **Scaling:** spider counts are ×1.0 / ×1.6 / ×2.1 / ×2.5 for 1/2/3/4 players. The Mother's health scales the same.
- **One clear per world:** the boss can be killed once per Warren, and each player who was in the arena gets their
  shard.
- **Mixed corps:**
  - A party of Green, Red and Blue plays the cave together, each with their own counter (flare / rage resistance /
    calm).
  - That gives a reason to party up across corps.

---

## Part 4. What it would take to build

### Blender passes (builder chats; numbers set by the coordinator as v2.01xx)

| Pass (proposed) | Area | What | Notes |
|---|---|---|---|
| Spider body round 1 | `combat\` | Broodling, Hunter, Weaver, Phantom: 3 takes each, voxel, Y1/Y3 shells | Builds on the 854 E1c2 skitter (IMPROVE). Legs must be **separate segment parts** (coxa, femur, tibia, tarsus) so code can do IK. |
| Spider motion round | `combat\` | walk cycle reference, wall turn, ceiling drop on thread, idle twitches, pounce, death curl | Blender is the **reference**. The game runs legs procedurally; Blender sets the timing and the pose targets. |
| Stalker | `combat\` | E1c2/E1c3 IMPROVE round, merged into the cave Stalker | J already wants this round. |
| The Matron | `combat\` | 3 silhouette takes, then phases: ceiling drop, scythe strike, silk shot, scream, lights-out, collapse | The biggest model. Keep it near 2,500 boxes. |
| Cave kit | `constructs\` | silk strands (thin/thick), web sheets, egg sacs (sleeping/cracking/hatched), Dread Stone, pillars with cocoons, heart-crystal (yellow → green) | Silk and web textures: a new Y4 strip in the construct-texture tools. |
| Cave mock-up | `constructs\` | a greybox fly-through of Z1-Z6, rendered first-person with ring light as the only light | It lets J judge the *mood* before anything is built in game. |
| Will Flare | `combat\` | 3 takes of the hold-and-pulse, first and third person | It reuses the FearNuke constructing pose. |
| Rewards | various | Silkline thread, Wallcrawl claws, Matron trophy | later |

### Minecraft systems (mc chat)

1. **The structure:**
   - a jigsaw structure: template pools for each zone, so the Warren varies between worlds;
   - placed with `terrain_adaptation: bury` (or `encapsulate`) so cave carvers don't open extra entrances;
   - zone NBTs built in game or generated by a script;
   - false entrances as separate small structures within 40 blocks.
2. **Blocks:**
   - Dread Stone (slow to mine, regrows);
   - Fear Silk (hard-light web, slows, burnt by green light);
   - Silk Bridge (a walkable strand block);
   - Egg Sac (hatch on Dread);
   - Heart-Crystal (block entity, the boss trigger);
   - Brazier (checkpoint).
3. **The Dread system:**
   - a per-player attachment (0-100) synced to the client;
   - it drives the existing `FearVignette`, `FearFog` and `FearBlind`;
   - a cave-only region check (the structure's bounding box).
4. **Ring light:**
   - **The cheap route:** place and remove invisible `minecraft:light` blocks round the player each few ticks. The mod
     already does block light for beams.
   - **The nicer route:** a dynamic-lights mod (below).
5. **Entities:**
   - five spider entities and the Matron;
   - custom AI goals: edge-of-light stalking, ceiling drop, pack flank, feed-on-fear, silk walls.
6. **Wall and ceiling climbing.** This is the hardest part:
   - **Stage A (cheap, walls only):** vanilla `Spider`-style climbing (`WallClimberNavigation` plus the climbing
     flag). It climbs vertical walls but can't walk on ceilings.
   - **Stage B (real):** a custom movement controller where each spider has a "surface normal". Gravity points into
     the surface it's on, collision runs in that frame, and the renderer rotates the model to the normal. Pathing on
     3D surfaces needs its own small navigator (block-face graph), because vanilla pathfinding is 2D-ish.
   - Ceiling drops are easier than ceiling walking. Spawn spiders on the ceiling, let them hang and drop, and fake the
     rest. That gets 80% of the look for 20% of the work.
7. **Procedural leg IK (client renderer):**
   - each leg raycasts for a foot target near its rest position;
   - it steps when the target is more than about 0.6 of a leg-length away (alternating sets);
   - two-bone IK solves the knee;
   - feet lerp in an arc. That makes spiders cling to any surface shape.
8. **The boss arena:** a phase controller, a dome web made of breakable silk blocks (phase 1 → 2), a lights-out phase
   (a client effect), and the heart-crystal channel.
9. **Sounds:** about 20 new sound events (skitters, thread zip, whisper, scream, egg pulse, silk burn, crystal turning).

### Mods that could help (check 26.3 availability before relying on any)

- **GeckoLib:** animated entity models with bone animation from Blockbench. Good for the Matron's phases and the
  spiders' body animation, and procedural IK can still drive individual leg bones. This is the biggest time-saver if
  it's on 26.3.
- **LambDynamicLights** (Fabric): held-item and entity dynamic lighting. It would make the ring a real moving light
  without placing light blocks. It has to be a soft dependency, since J plays in Lunar.
- **YUNG's API / Lithostitched:** helpers for jigsaw structures and worldgen tweaks.
- **The "Spiders 2.0" mod** (older Forge): a well-known reference for wall/ceiling walking spiders with orientation. Use
  it as reference for the approach only; check its licence before borrowing any code.
- The research chat's survey (`docs/research/2026-10-19-mods-physics.md`) was **not in the repo yet** when this was
  written. Fold its picks in here when it lands.

### Risky parts (in order)

1. **Ceiling walking with collision and pathing.** This is the riskiest system. Start with Stage A plus ceiling *drops*,
   and only build Stage B if J wants spiders running across ceilings in game.
2. **Procedural IK performance.** It's client-only, and fine for about 20 spiders. Cap spiders per zone, and skip IK on
   spiders over 32 blocks away (use a baked walk loop instead).
3. **The one-entrance guarantee against worldgen caves.** Bury plus a protective shell of Dread Stone round the
   structure should do it. Test with many seeds.
4. **The ring-light approach.** The light-block route can flicker on fast movement and costs lighting updates. A
   dynamic-lights mod is nicer but optional. Test both in Lunar with Complementary.
5. **Lights-out in shaders.** Complementary may brighten caves on its own. Check that phase 3 still reads as darkness in
   J's setup.
6. **Jar size (now near 30 MB).** Five spider models, the Matron, a cave kit and sounds will push it. Paletted
   textures, short OGG sounds, and maybe a separate "Trials" resource download.
7. **Scope.** The Warren alone is a large feature. Suggested order:
   - the Dread meter plus the Hatchery-style egg room as a playable vertical slice;
   - then the Hunter with drops;
   - then the full cave;
   - then the Matron.

---

## Decisions for J

1. **Which trial is built first after the Warren?**
   - ★ **The Oath Spire (Green):** no new mobs, it reuses existing constructs, and it delivers the 816 Oath animation.
   - Or the Bloodfurnace (Red).
   - Or the Hoard Vault (Orange, which would force the Orange look pick).
2. **Who can enter the Warren?**
   - ★ **Any corps, each with its own counter:** Green flares, Red resists while attacking, Blue drains Dread, Yellow
     gets a wary brood but a furious Matron.
   - Or Green only (simplest, the classic will-versus-fear story).
3. **How real should the wall-climbing be?**
   - ★ **Walls plus ceiling drops first** (Stage A: vanilla-style climbing, ceiling hang-and-drop, procedural leg IK).
     Ship it, then decide on ceilings.
   - Or full ceiling walking from the start (Stage B: a custom surface movement and navigator; much riskier and
     slower).
