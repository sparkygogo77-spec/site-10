# Mutant Monsters as Fallen Titan bosses (research, 2026-10-19)

J picked "New: Mutant Monsters bosses" for the Fallen Titan trial (`docs/plans/trials/2026-10-19-trials-concept.md`,
"★ 1. The Fallen Titan"). It's ★5 in `2026-10-19-mods-physics.md`. Sources: the Modrinth API, and the mod's own
source on the `26.3.x` branch of [Fuzss/mutant-monsters](https://github.com/Fuzss/mutant-monsters) (read, not run).
Our side was checked against `origin/main`.

## 26.3 Fabric build (Modrinth API, today)

| Jar | Version | Size | Notes |
|---|---|---|---|
| [Mutant Monsters](https://modrinth.com/mod/mutant-monsters) | **26.3.1** (2026-10-06, release) | 1.37 MB | AGPL-3.0 (Affero General Public Licence). 5.2 M downloads. Needed on client **and** server. |
| [Puzzles Lib](https://modrinth.com/mod/puzzles-lib) | 26.3.15 | 1.09 MB | required |
| [Forge Config API Port](https://modrinth.com/mod/forge-config-api-port) | 26.3.1 | 0.61 MB | required |
| Fabric API | 0.164.0+26.3 | (already in the Stormie's instance) | required |

So a player needs **3 extra jars** besides Fabric API. All three are by Fuzss and kept up to date (Puzzles Lib updated 2026-10-14).

## 1. Which mutants fit the Fallen Titan

Health is in hit points (2 = one heart). All mutants take no fall damage and only spawn one at a time.

| Mutant | Health | Size (wide × tall) | Attacks, in numbers | Knockback resistance |
|---|---|---|---|---|
| **Mutant Zombie** | 150 (75 hearts) | 1.8 × 3.2 | Punch 12. **Ground slam**: seismic waves, 9-12 at the first wave, 6-8 on the ripples, 1 in 5 chance of Hunger. **Grab and throw** (flings you 1.6 up). Roar (6 s) raises nearby dead zombies. **3 lives**: "dies", gets back up 7 s later with 37 health. Only **fire** finishes it (burning when it dies, or flint and steel on the body). Heals 2 every 5 s at night. Can't be hurt by other zombies. | 1.0 (none) |
| **Mutant Enderman** | 200 (100 hearts), boss-level XP | 1.2 × 4.2 | Melee 7 (heals it 2). **Block frenzy** (10-14 s): rips real blocks out within 2.5 blocks, holds up to 4 at once, throws them for 4-6 each. Teleports away when hurt (1 in 3 to 1 in 6 per hit), **telesmash**, a teleport burst (4 + Blindness), a scream (8 s) and a **clone phase** (30 s of fake copies). Sees 96 blocks. Neutral until angered. | 1.0 |
| **Mutant Skeleton** | 150 (75 hearts) | 1.2 × 3.6 | Melee 3 + throw, **rib constrict** 7, a big crossbow shot and a **multi-shot**. Arrows can carry Poison, Hunger or Slowness. Sees 48 blocks. Heals 2 per 5 s at night. | 0.75 |
| **Mutant Creeper** | 120 (60 hearts) | 2.0 × 2.8 | Hit 5. **Jump attack** with a power-4 blast (6 if charged). **Charges up** to heal 30. Lays creeper-minion eggs (up to 4, fewer as it weakens). Dying takes 5 s and ends in a **power-8 blast** (12 charged; a vanilla creeper is 3). Fire-immune when charged, and thorns 2 against melee. | 1.0 |
| Mutant Snow Golem / Spider Pig | 80 / 40 | | Player-made pets, not enemies. **Don't fit.** | |

**Fit, room by room** (the Titan's shape from the concept):

1. **The boot, half sunk in mud → Mutant Zombie.** It's the "dead body that won't stay down". Its slam turns grass to
   dirt (the `turns_into_dirt` tag), which reads as mud. The room teaches the rule "burn it": a brazier or the
   Titan's dead lantern-heart embers. That's a puzzle, not just a health bar.
2. **The leg, a vertical climb → Mutant Skeleton.** It shoots down the hollow shin from 48 blocks. The player climbs
   behind Wall and Shield, so the ring's defensive tools matter.
3. **The chest cavity → Mutant Enderman (best fit ★).** It tears real blocks out of the cracked chest and throws them.
   **It can't grab our construct blocks** (see section 2). So every Wall or Bridge you build to "repair" the
   Titan is also the one thing it can't rip out. That's the trial's ring twist made into a fight.
4. **The arm, a broken bridge → Mutant Creeper.** You construct the bridge back while it jump-blasts you. Construct
   blocks shrug off explosions, so the bridge survives and the stone around it doesn't. Its 5-second death blast
   (power 8) can be the moment the old arm falls away.
5. **The head and pilot fight → no.** At 3-4 blocks tall they are ants next to a 60-block Titan. The finale stays the
   yellow fear storm we design. Optional extra: a few mutant zombies under the Titan's feet as things to stomp,
   which sells the scale.

## 2. Compatibility with our code

| Our system | What happens | Action |
|---|---|---|
| **`MobTargetMixin`** (cancels `Mob.setTarget` for Mind Link, Soul Stone and Red Sanctuary) | Mutants pick targets through goals that call `Mob.setTarget`, so **sparing works**. **But** their area attacks don't use the target: the Zombie's seismic waves hit everything in the box except zombies, and the Enderman's teleport burst and the Creeper's blasts hit everyone. A Mind-Linked mutant still hurts its owner standing close. | Accept, or note it in the Ring Lab text. Test 1 below. |
| **`ConstructAlly`** allies (`isBadMob`) | Mutants extend `Monster`, so they count as `Enemy` and **allies attack them**. The Mutant Enderman is a `NeutralMob`, so allies **ignore it until it's angry** (same as vanilla endermen). The Zombie's waves and the Creeper's blasts will hurt allies. | None. Test 2. |
| **Construct blocks** (Light Construct, Construct Brick, all Ghost blocks) | All have strength **-1** (unbreakable) and blast resistance 3,600,000. The Enderman only grabs a full-cube block with **hardness 0 to 50** and no block entity, so it **can't grab any construct**. The Ghost Mimic has a block entity too. Mutant blasts don't break them. Mutants smash `LeavesBlock` blocks they walk into, but our Ghost Leaves extends `TransparentBlock`, so it's safe. | None. Test 3 confirms. |
| **Lasso / Tether** (`Lasso.java`) | It moves its catch with `setDeltaMovement`, which **ignores knockback resistance**. A 200-health Mutant Enderman flies exactly like a zombie. The slam deals *fall* damage, and every mutant is in `#minecraft:fall_damage_immune`: whether the slam still hurts them needs a test. The Enderman may **teleport out** of a catch when it's hurt. | Small code job: a `lanternring:heavy` entity tag (optional entry `#mutantmonsters:mutants`, plus warden and ravager) that cuts throw speed and adds weight. Test 4. |
| **Omega Beam "unmake"** (`OmegaBeams.java`) | Only the Ender Dragon and Wither count as bosses there. Any other mob, mutants included, gets **erased in one hit**. | Use the same `heavy` tag: heavy mobs take the 30-damage burn instead. |
| Natural spawning | By default mutants spawn anywhere their vanilla mob does, at **5%** of its spawn weight. In J's survival world, mutant zombies would turn up at night. | For trial-only bosses, set the four weights in the mod's config to 0. Trials then spawn them by ID. |
| Licence | AGPL-3.0: **don't copy its code** into ours. Spawning its mobs by ID from a datapack, or behind `FabricLoader.isModLoaded("mutantmonsters")`, is fine (no linking). | Soft dependency only. |
| Mixins | It has one mixin (`Entity.startRiding`, for carrying creeper eggs). No overlap with ours. | None. |

## 3. Verdict: keep ours or swap

| Part of the Titan | Verdict | Why |
|---|---|---|
| The Titan itself, the climb inside it, piloting | **Keep ours** | No mod has a pilotable 60-block construct. That's our build (mech starting point). |
| The fear-storm finale | **Keep ours** | It's yellow constructs and the Warren's Matron echo: our own look. |
| Room bosses (boot, leg, chest, arm) | **Use Mutant Monsters as an optional source ★** | Four finished bosses with real move sets and animations, on 26.3 today. Zero model work for us. |
| Without the mod installed | **Our own fallback** | The rooms still need something: vanilla stand-ins (a ravager in the boot, a skeleton squad in the leg) or later our own versions. That's the same "soft dependency" pattern as Stormie's Spiders. |

Code it needs (small, mc build chat, only once J has watched it): the `heavy` tag for Lasso and Omega Beam, and the
trial spawner picking "mutant if loaded, else fallback".

## 4. Test world plan

**Own instance ★: `C:\Users\Josh\Documents\LanternLive\test-instances\mutant-monsters\`.** Keeping it apart from
`stormies-spiders` keeps each test clean. Both are small, and the mods don't overlap (the spiders mod touches only
spiders), so sharing would also work.

- **Ready now:** `lantern-mutant-test-datapack.zip` (and the unzipped folder). It hasn't been run yet, so if a line
  errors, the chat shows which line.
  - `/function lantern_mm:build` builds a 31×31 stone-brick arena east of you, with a cobble and log pile for the
    Enderman to grab. It sets midnight, normal difficulty and mob griefing on.
  - `zombie`, `enderman`, `skeleton`, `creeper` summon one at the far end; `all` summons all four.
  - `reset` clears every mutant and leftover, then rebuilds the arena.
- **Not done (needs J's OK to download):** the `mods\` folder: Fabric API 0.164.0+26.3 (copy from the Stormie's instance),
  Mutant Monsters 26.3.1, Puzzles Lib 26.3.15, Forge Config API Port 26.3.1 (about 3 MB from Modrinth, sha512 checked)
  and our `lantern-ring-2.1.1712+26.3.jar`. J adds the launcher installation himself (game directory = that folder,
  Fabric Loader 0.19.5 for 26.3 is already installed) and makes a creative flat world with cheats on.

**What to watch (about 10 minutes):**
1. **Mind Link a Mutant Zombie**, stand next to it while it slams something else: does the wave hurt you?
2. **Allies:** summon a construct army, then `zombie`. Do they fight it, and how fast do they die to the waves? Then
   `enderman`: do they leave it alone until it's angry?
3. **Constructs vs the Enderman:** build a Wall and Dome next to the cobble pile, hit the Enderman with a Blast from
   range (indirect damage starts its block frenzy). It should take cobble and logs but never a construct block.
   Then `creeper`, and let it die next to a Wall: the stone goes, the Wall stays.
4. **Lasso on heavies:** catch each mutant and slam it. Does it fly too far? Does the slam hurt them (fall-damage
   immunity)? Does the Enderman teleport out of the bubble?
5. **Feel:** which one is the most fun to fight with the ring? That picks the first Titan room to build.
