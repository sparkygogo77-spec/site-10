# Mods that could mesh with (or collide with) Lantern Ring (2026-10-19)

J asked for "physics or mods that may collide/mesh well within my pack". This is research only:
nothing has been added to `modpack/` or the code.

**How this was checked:** every "26.3" status below comes from the Modrinth API on 2026-10-19
(`/v2/project/<slug>/version?loaders=["fabric"]&game_versions=["26.3"]`). "Newest" is the newest MC
version the project lists. Conflict risk is judged against our actual mixins
(`lanternring.client.mixins.json`, `lanternring.mixins.json`), listed at the bottom.

**What's in J's pack today:** just Lantern Ring + Fabric API (`modpack/vanilla-fabric/mods/`). On Lunar
Client, Lunar also bundles its own Fabric API, Sodium and Iris (Lunar's Sodium has extra mixins of its
own). Never add a second Sodium/Iris/Fabric API on Lunar. The Complementary shader pack is patched by
`ShaderPackPatcher`/`ShaderPackIds` so the mod's glow works under Iris.

---

## ★ Top 5 to try first

| # | Mod | 26.3 Fabric | Licence | What it adds for Lantern Ring | Conflict risk | Integration opportunity |
|---|---|---|---|---|---|---|
| ★1 | [LambDynamicLights](https://modrinth.com/mod/lambdynamiclights) | ✅ yes | Lambda License (custom, free to use) | Held ring, flying bearer, constructs, Beam and lanterns could actually light up caves and the night around them, not just look bright. Biggest "the light is real" win, and it's Sodium-friendly. | **Low.** Works on light levels, not on any of our render mixins. Under an Iris shader pack the pack's own lighting takes over (dynamic lights mostly show without shaders). | **Yes, best one.** Data-driven, no hard dependency: `assets/lanternring/dynamiclights/item/*.json` (ring, lantern) and `.../entity/*.json` (constructs, allies) give 0-15 light. Java API (`lambdynlights_api`, maven.gegy.dev) can scale light with charge or corps. Docs: lambdaurora.dev/projects/lambdynamiclights/docs/v4 |
| ★2 | [Physics Mod](https://modrinth.com/mod/physicsmod) (Haubna) | ✅ yes (already has 26.4 snapshots) | All Rights Reserved; free tier + paid Pro | Blocks broken by Blast crumble into physical chunks; mobs hurled by Shockwave/Beam die as ragdolls or fracture. Makes Blast and Shockwave feel heavy without us writing physics. | **Medium.** Client-only, so no server desync, but: it doubles up with our own Blast crumbs (30% of blocks already throw texture crumbs), it can be heavy on FPS during a 50-block Blast, ragdolls/fracture are for vanilla mobs (our allies/corps mobs may fall back to normal death), and it's closed source so we can't check its mixins. Test with Blast at max and Shockwave in a crowd. | Maybe: a Ring Lab toggle that turns our own crumbs off when `physicsmod` is loaded (`FabricLoader.isModLoaded`), so they don't stack. No public API. |
| ★3 | [Sound Physics Remastered](https://modrinth.com/mod/sound-physics-remastered) | ✅ yes | GPL-3.0 | Reverb and muffling: Blast boom echoes down its own tunnel, Shockwave thumps in caves, Lasso/charge hum muffles through walls. Cheap way to make every power feel weightier. | **Low.** Works on the sound engine; we have no sound mixins. | No code needed. Our custom sounds just get the effect. |
| ★4 | [Stormie's Spiders](https://modrinth.com/mod/stormies-spiders) (fork of Spiders 2.0) | ✅ yes | LGPL-2.1 | Spiders climb walls and ceilings with real pathfinding: exactly the "wall-climbing spiders" for the planned trials, and a good target for Tether/Dome/Wall. | **Low-med.** Must be on client and server. Our `BroodSpider` extends `ConstructAlly`, not vanilla `Spider`, so it won't pick up the climbing (and won't be disturbed by it). Test that `MobTargetMixin` still keeps climbing wild spiders off the bearer's allies. Listed incompatible with PotsandMimics only. | **Yes.** Soft-dep for the trials: if `isModLoaded`, trial spiders can rely on its climbing instead of us writing it. It also supports Rotation Overrides for other spider-like mobs. |
| ★5 | [Mutant Monsters](https://modrinth.com/mod/mutant-monsters) | ✅ yes | AGPL-3.0 | Big, tough mutant zombies/skeletons/creepers/endermen: proper targets that need Blast, Tether and constructs, not one Beam. Fills the "bosses" gap while the bigger boss mods aren't on 26.3. | **Low.** Content mod, no client render overlap with ours. Mutant Enderman grabbing blocks next to our construct blocks is worth one test. | Small: tag them as "heavy" so Tether/Lasso can't fling them as far. |

---

## Physics / weight

| Mod | 26.3 | Licence | For Lantern Ring | Risk | Integration |
|---|---|---|---|---|---|
| [Physics Mod](https://modrinth.com/mod/physicsmod) | ✅ | ARR | See ★2 | Med | Crumbs toggle |
| [Sound Physics Remastered](https://modrinth.com/mod/sound-physics-remastered) | ✅ | GPL-3.0 | See ★3 | Low | — |
| [Saro's Player Ragdoll](https://modrinth.com/mod/saros-player-ragdoll) | ✅ | ARR | Players knocked down by a Shockwave/Fear power fall as a ragdoll before dying; fun in multiplayer duels. | Med: poses the player model, as do our `PlayerModelMixin`/`AvatarRendererMixin` (flight and charge poses). Test a downed player with a ring on. | No |
| [TNT Logic: Realistic Explosion Physics](https://modrinth.com/mod/tnt-logic-realistic-explosion-physics) | ✅ | E-ML | Explosions cause structural collapse. Only helps if a power uses a real `explode()`; Blast doesn't today. | Low (new, 13k downloads, so less proven) | Only if we add explosive powers |
| [Shake Tweaks](https://modrinth.com/mod/shaketweaks) | ✅ | LGPL-3.0 | Tunes vanilla hurt/hand shake. | Low-med: we already have our own camera kick (`RingShake` via `CameraMixin`); both together could double-shake. | No; our Ring Lab "Screen shake" row covers it |
| [Valkyrien Skies](https://modrinth.com/mod/valkyrien-skies) / [Sable](https://modrinth.com/mod/sable) | ❌ (1.20.1 / 1.21.1) | LGPL / PolyForm Shield | Real rigid-body ships: a moving Bridge or flying construct ship would be amazing. | n/a (no 26.3 port) | Watch Sable; it's the active one (updated 2026-10-03) |

## Visual / light / particles (all fine with Sodium + Iris unless noted)

| Mod | 26.3 | Licence | For Lantern Ring | Risk | Integration |
|---|---|---|---|---|---|
| [LambDynamicLights](https://modrinth.com/mod/lambdynamiclights) | ✅ | Lambda | See ★1 | Low | JSON + API |
| [Entity Texture Features (ETF)](https://modrinth.com/mod/entitytexturefeatures) | ✅ | LGPL-3.0 | Emissive `_e` textures for our entities (golem, hawk, dragon construct, allies) from a resource pack: glowing eyes/lines without code. | Low-med: it renders entity textures, and our `LivingEntityRendererMixin` changes model tint (`getModelTint`). Check corps recolours still apply. | Yes: ship `_e` emissive textures for constructs |
| [Particle Rain](https://modrinth.com/mod/particle-rain) | ✅ | MIT | Prettier weather; storm flights look better. | Low | No |
| [Visuality](https://modrinth.com/mod/visuality) / [Subtle Effects](https://modrinth.com/mod/subtle-effects) | ✅ | MIT / ARR | Small ambient particles (sparkles, embers). | Low, but they add to the particle budget a big Blast already fills. | No |
| [lumaLight](https://modrinth.com/mod/lumalight) | ✅ | MIT | Coloured lighting and bloom **without** a shader pack: could give green glow on low-end PCs. | **Med:** touches lighting/lightmap like our `LightmapExtractorMixin`; small project (26k downloads). Try only without Iris. | Maybe |
| [Skyboxify](https://modrinth.com/mod/skyboxify) / [Better End Sky](https://modrinth.com/mod/better-end-sky) | ✅ | GPL-3.0 / MIT | Space-like skies for flight up high. | **Med:** both draw the sky; we inject `SkyRenderer.extractRenderState` (TAIL) and fog colour (`FogColorMixin`) for Fear/Sun-dim effects. They may hide our sky tints. | No |
| [Elytra Physics](https://modrinth.com/mod/elytra-physics) | ✅ | MIT | Cape-like elytra sway. | Low | No |

## Gameplay that fits the theme

| Mod | 26.3 | Licence | For Lantern Ring | Risk |
|---|---|---|---|---|
| [Stormie's Spiders](https://modrinth.com/mod/stormies-spiders) | ✅ | LGPL-2.1 | See ★4 (trials) | Low-med |
| [Mutant Monsters](https://modrinth.com/mod/mutant-monsters) | ✅ | AGPL-3.0 | See ★5 | Low |
| [Dungeons and Taverns](https://modrinth.com/mod/dungeons-and-taverns) | ✅ | ARR | Structures to fly to and tunnel into; Blast through a dungeon wall. Datapack-style, very safe. | Low |
| [Structory](https://modrinth.com/mod/structory) / [Towns and Towers](https://modrinth.com/mod/towns-and-towers) | ✅ | Stardust / CC-BY-NC-SA | More things worth flying to. | Low |
| [Terralith](https://modrinth.com/mod/terralith) / [Nullscape](https://modrinth.com/mod/nullscape) / [Incendium](https://modrinth.com/mod/incendium) | ✅ | Stardust | Big terrain for flight; Nullscape's alien End feels like "space"; Incendium adds Nether fights. | Low (worldgen only; new worlds) |
| [Friends & Foes](https://modrinth.com/mod/friends-and-foes) | ✅ | CC-BY-NC-ND | Extra mobs incl. Illusioner/Wildfire mini-boss. | Low |
| [Spell Engine](https://modrinth.com/mod/spell-engine) + [Wizards](https://modrinth.com/mod/wizards) | ✅ | GPL / ARR | Rival "magic users" for a ring bearer to duel. | Med: its own casting HUD, keybinds and use-item handling may fight our `startUseItem` cancel in `MinecraftMixin`. |
| [Bosses of Mass Destruction](https://modrinth.com/mod/bosses-of-mass-destruction) | ❌ 1.21.1 (last update 2024) | LGPL-3.0 | Perfect boss arenas for powers. Likely abandoned. | n/a |
| [YUNG's Better Dungeons](https://modrinth.com/mod/yungs-better-dungeons) | ❌ 26.1.2 (updated 2026-09-10, port likely) | LGPL-3.0 | Great tunnel-through dungeons. | n/a yet |
| [When Dungeons Arise](https://modrinth.com/mod/when-dungeons-arise) | ❌ 1.21.1 | ARR | Huge sky/air structures for flight. | n/a |
| [Ad Astra](https://modrinth.com/mod/ad-astra) | ❌ 1.21.1 | Terrarium | Real space/planets (Oa vibes). | n/a |
| [Accessories](https://modrinth.com/mod/accessories) | ❌ 1.21.10 (updated 2026-10-16, port likely) | MIT | A ring **slot** so the ring is worn, not held. Big future integration; Trinkets is dead (1.21.1). | Watch |

---

## ⚠ Known / likely CONFLICTS (avoid or test hard)

| Mod | 26.3 | Why it collides with us | Risk |
|---|---|---|---|
| [First-person Model](https://modrinth.com/mod/first-person-model) | ✅ | Draws the whole body in first person and hides vanilla arms. We cancel `FirstPersonHandsAndItemsRenderer.submitArmWithItem` (HEAD) and draw our own ring arm (`RingFirstPerson`, `RingEmit` first-person ring position). Expect a double arm or a missing ring, and power origins in the wrong place. | **High** |
| [Not Enough Animations](https://modrinth.com/mod/not-enough-animations) | ✅ | Rewrites arm poses in `PlayerModel` and first-person arms. We also pose arms at `PlayerModel.setupAnim` TAIL and in `AvatarRenderer.setupRotations` (charge, flight, aim poses). Whoever runs last wins; flight/charge poses likely break. Very popular, so J may already have it. | **High** |
| [Do a Barrel Roll](https://modrinth.com/mod/do-a-barrel-roll) | ✅ | Elytra flight with camera roll. Our sprint-flight steers "like an elytra" (`FastFlight`, `LocalPlayerMixin.aiStep`) and kicks the camera in `CameraMixin.alignWithEntity`. Two systems rolling the camera; if it treats ring flight as fall-flying, controls fight. | **High** |
| [Better Combat](https://modrinth.com/mod/better-combat) | ✅ | Replaces attacking. We cancel `Minecraft.startAttack`/`continueAttack`/`startUseItem` at HEAD while the ring is in use. Either the ring's left-click actions stop working or Better Combat swings over them. Also animates the player via its own animator (arm poses vs ours). | **Med-high** |
| [Camera Overhaul](https://modrinth.com/mod/cameraoverhaul) | ✅ | Adds camera roll/tilt on movement. Stacks with our `RingShake` kick and flight camera; could feel nauseating at flight speed. Probably works, just too much. | **Med** |
| Any other dynamic-lights mod (e.g. [Dynamic Lights (dynamic-torches)](https://modrinth.com/mod/dynamic-torches)) | ✅ | Two dynamic light mods together conflict with each other; pick LambDynamicLights only. | Med |
| A second Sodium/Iris/Fabric API on Lunar | — | Lunar bundles its own; duplicates can stop Lunar starting (already in `modpack/README.md`). | **High** |
| [Freecam](https://modrinth.com/mod/freecam) | ✅ | Harmless, but our `RingEmit`/aim uses the camera; firing powers while in freecam may aim oddly. | Low |

## Integration opportunities worth a future code task (not done here)

1. **LambDynamicLights JSON** (no hard dependency): ring + lantern items, construct entities, by corps. Smallest effort, biggest visible gain.
2. **[Player Animation Library](https://modrinth.com/mod/player-animation-library)** (✅ 26.3, MIT): if we moved charge/flight/aim poses onto it, we'd layer cleanly with Better Combat and other animated mods instead of fighting them at `setupAnim` TAIL. Bigger refactor; only worth it if J wants Better Combat or NEA in the pack.
3. **`isModLoaded("physicsmod")`** → skip our own Blast crumbs (or a Ring Lab toggle).
4. **Stormie's Spiders** as the trials' climbing backend.
5. **ETF emissive textures** for construct mobs.
6. Watch for 26.3 ports: Accessories (ring slot), YUNG's, Sable.

## Our mixin surface (what other mods could collide with)

Client: `AvatarRenderer` (extractRenderState, setupRotations), `AvatarRenderState`, `Camera.alignWithEntity`,
`EntityRenderDispatcher.getRenderer`, `EntityRenderer.extractRenderState`, `EntityRenderState`,
`FirstPersonHandsAndItemsRenderer.submitArmWithItem` (HEAD cancel), `FogRenderer.computeFogColor`,
`Hud$HeartType.getSprite`, `LightmapRenderStateExtractor.extract`, `LivingEntityRenderer`
(extractRenderState, getModelTint), `LocalPlayer` (shouldStopRunSprinting, aiStep), `Minecraft`
(startUseItem, startAttack, continueAttack, shouldEntityAppearGlowing), `MouseHandler.onScroll`,
`PlayerModel.setupAnim`, `SkyRenderer.extractRenderState`.
Common: `Level.setBlock` (HEAD), `Mob.setTarget` (HEAD cancel), `ShulkerBullet` accessor.

All our injections are `@Inject` (no `@Overwrite`, `@Redirect`), which is the friendliest kind: two mods
injecting at the same method both run. Clashes come from *behaviour* (both posing the arm, both moving
the camera), not from mixin crashes, except where another mod `@Overwrite`s or `@Redirect`s the same
method, which would show up as a crash at launch with `defaultRequire: 1`.

---

# Round 2 (2026-10-19): replacements for our own systems

J: *"the research chat was supposed to find mods that mesh well with replacements for stuff in mine like maybe
flight mechanics"*. For each of our systems: what we do now, the best 26.3 Fabric mod or library that could
replace it or that we could build on, and a ★ verdict. As before, every 26.3 status was checked on the Modrinth API.

**Short version:** for most of our systems, there's nothing on 26.3 that does what we need better. Ring flight,
hard-light constructs and Lasso are too specific to the Green Lantern idea for any existing mod to cover. Two
libraries are real wins: **Player Animation Library** (for poses) and **GeckoLib** (for animated construct models).
One library is worth watching for when it comes out on 26.3: **Sable**, for constructs that move as physics
objects. Effects engines (Veil, AAA Particles/Effekseer, Lodestone) aren't on 26.3 yet.

| Our system | What we do now (1 line) | Best candidate | 26.3 Fabric | Licence | What we'd gain | What we'd lose / rewrite | Conflict risk | ★ Verdict |
|---|---|---|---|---|---|---|---|---|
| **Flight** (`RingFlight` + `FastFlight`, `FlightPoses`, `FlightTrail`) | Server gives creative-style flight while charged; client makes sprint-flight steer like an elytra that skims walls instead of crashing; our own poses and trail. | [Do a Barrel Roll](https://modrinth.com/mod/do-a-barrel-roll) (flight-sim elytra controls: roll, pitch, yaw, banking camera) | ✅ | GPL-3.0 | Real banking turns and barrel rolls in the fast glide, a proven control feel, and its config screen. | Our flight isn't an elytra: DaBR acts on elytra fall-flying, so we'd have to make the ring glide count as fall-flying (or use its API if it exposes one for other mods, so check its docs before deciding). That would mean reworking our wall-skim and landing. | High while both run (two camera rollers) | **★ Keep ours.** Steal the *idea*: add a gentle bank/roll to `FastFlight` turns ourselves. Revisit DaBR only if J wants full flight-sim controls. |
| | | [Enhanced Movement](https://modrinth.com/mod/enhanced-movement) (double jump, dash, ledge grab) | ✅ | MIT | Dash in any direction, a nice "ring burst" feel. | Nothing (it's an add-on), but it's a small mod (8k downloads). | Low-med: also changes movement on `LocalPlayer` | Optional extra, not a replacement |
| | | Jetpack mods ([Iron Jetpacks Refabricated](https://modrinth.com/mod/iron-jetpacks-refabricated), [Jetpack Boots](https://modrinth.com/mod/jetpack-boots)) | ✅ / ✅ | MIT / ARR | Fuel-based thrust flight. | Wrong feel: thrust and hover, not ring flight. | Low | Not worth it |
| **Hard-light constructs** (Wall, Dome, Bridge in `HeldConstructs`/`RingPowers`) | Real blocks placed with `setBlock` (blockstate `corps`), rebuilt per tick for the held Dome, removed after a timer. | [Sable](https://modrinth.com/mod/sable) ("sub-levels": block structures that move, rotate and collide; the base of Create Aeronautics) | ❌ (newest 1.21.1, active) | PolyForm Shield | Constructs that are *objects*: a Wall you can shove, a Bridge that swings, a construct you throw. Exactly the "weight" J wants. | A big rewrite of how constructs exist, and a heavy dependency. PolyForm Shield means we can use it but not compete with it. | Unknown until there's a port | **★ Keep ours; watch Sable.** Valkyrien Skies is stuck on 1.20.1. |
| **Construct models & animation** (`BbModel`/`BbRig`: our own Blockbench loader, bones animated in code) | We read `.bbmodel` files and turn groups into ModelParts; animation is hand-written Java per mob (e.g. DivingHawkModel). | [GeckoLib](https://modrinth.com/mod/geckolib) (or [AzureLib](https://modrinth.com/mod/azurelib)) | ✅ / ✅ | MIT / MIT | Animations made in Blockbench with keyframes and easing, instead of written in code. Faster for new construct mobs (hawk, golem, dragon, bull). Huge user base. | It becomes a required dependency (Lunar users must add it). Our `glow`/`core`/`glass` cube naming would have to move to GeckoLib render layers. Existing mobs would need porting or would stay on BbRig. | Low | **★ Swap for *new* animated constructs**, keep BbModel for static ones. Worth a trial with one mob. |
| **Player poses** (`FlightPoses`, `ChargePoses`, aim pose via `PlayerModelMixin`/`AvatarRendererMixin`) | We set arm/body angles at the end of `PlayerModel.setupAnim`. | [Player Animation Library](https://modrinth.com/mod/player-animation-library) | ✅ | MIT | Poses as animation files, layered with priorities, so they **stop fighting** Better Combat, Not Enough Animations, Emotecraft, etc. (the High conflicts in round 1). Smooth blending in and out. | A rewrite of 3 pose classes, and a new dependency. | Low (that's the point) | **★ Swap, if J wants any animation mods in his pack.** Otherwise keep ours. |
| **First-person ring/hand** (`RingFirstPerson`, `FirstPersonHandsMixin`, `RingEmit`) | We cancel vanilla's arm-with-item render and draw our own fist + 3D ring; powers start from the ring as drawn. | Player Animation Library's first-person mode / [First-person Model](https://modrinth.com/mod/first-person-model) | ✅ / ✅ | MIT / MIT | Nothing we lack. | Exact ring placement (powers leave the ring) would get harder. | High (round 1) | **★ Keep ours.** |
| **Tether / Lasso** (`Lasso` + `LassoFx`) | Server holds a mob in a bubble on a leash; client draws a glowing tube and sphere. | No grappling/rope physics library on 26.3 Fabric (searched "grapple", "rope", "tether": only small block mods). | — | — | — | — | — | **★ Keep ours.** If J wants a *swinging* tether (Spider-Man style), that's a code task: verlet rope in our own code. |
| **Beam/Blast effects + particles** (`ConstructParticle`, `*Fx` classes, `RingFxPayload`) | Server sends one payload; each client draws particles and custom geometry in its Ring Lab style; we patch Complementary for glow. | [Veil](https://modrinth.com/mod/veil) (post-processing, bloom, real dynamic lights; by the Sable team) / [AAA Particles](https://modrinth.com/mod/aaa-particles) (Effekseer effects) / [Lodestone](https://modrinth.com/mod/lodestonelib) | ❌ (1.21.1) / ❌ (26.1.2) / ❌ (1.21.3) | LGPL / MIT / LGPL | Veil: proper bloom *without* a shader pack. Effekseer: effects authored in a VFX tool. | All three would be big renderer dependencies, and Veil vs Iris is a known pain point. | High-ish | **★ Keep ours.** Add [Particle Core](https://modrinth.com/mod/particle-core) (✅, MIT) as a *player-side* optimiser if big Blasts drop FPS. Re-check Veil/AAA when they reach 26.3. |
| **Ring Lab settings UI** (`LabSettings` + `RingLabScreen`, JSON in config) | Custom screen for picking versions and rating them, plus durations/strength rows. | [YACL](https://modrinth.com/mod/yacl) / [Cloth Config](https://modrinth.com/mod/cloth-config) / [MidnightLib](https://modrinth.com/mod/midnightlib) / [Fzzy Config](https://modrinth.com/mod/fzzy-config) | ✅ all | LGPL / LGPL / MIT / TDL-M | A standard settings screen in Mod Menu, with sliders, validation and server sync (Fzzy). | The Lab's KEEP/IMPROVE/DROP rating and "Copy report" are J's review tool; no config library does that. | Low | **★ Keep the Lab.** When the "real settings" from `LabSettings` (its own comment says they will become the mod's real settings) are made, use **YACL or MidnightLib** for that player-facing settings screen and list it in [Mod Menu](https://modrinth.com/mod/modmenu). |
| **Updater** (`RingUpdater`, `JarSwap`, GitHub token) | Reads `latest.json` on the private repo, downloads the new jar, swaps it on exit. | Publish on Modrinth + [Simple Update Checker](https://modrinth.com/mod/simple-update-checker) / [AutoModpack](https://modrinth.com/mod/automodpack) | ✅ / ✅ | LGPL / LGPL | No token in configs; launchers (Prism, Modrinth App) update it for you. | Needs the mod to be *public* on Modrinth, which is J's call. Lunar users still update by hand. | Low | **★ Keep ours while the repo is private.** |
| **Camera shake** (`RingShake` via `CameraMixin`) | A short GTA-style kick when firing, with a Ring Lab strength row. | [Camera Overhaul](https://modrinth.com/mod/cameraoverhaul) / [Shake Tweaks](https://modrinth.com/mod/shaketweaks) | ✅ / ✅ | GPL / LGPL | Movement-based tilt (Camera Overhaul). | Neither offers a shake API for other mods; they would only add their shake on top of ours. | Med (double shake) | **★ Keep ours.** |
| **Data on players/items** (ring components, charge) | Vanilla data components and our own payloads. | [Cardinal Components API](https://modrinth.com/mod/cardinal-components-api) | ✅ | MIT | Nothing we need today; 26.3 components already do this. | — | Low | Keep ours |

---

## Plain-words explanations for J

### #4 Stormie's Spiders
**What you'd see:** normal Minecraft spiders, but they actually climb like spiders. They run up cliffs and
walls, cross ceilings upside down, and find a way round to you instead of getting stuck at the bottom of a wall.
**Why it fits:** the planned trials want enemies that come from above and from every side, which you'd
answer with the Dome, Wall and Shockwave. That's free AI for "a swarm comes over the wall". Our own Brood Spider
ally isn't affected.
**The catch:** it has to be installed on the server too (fine in singleplayer). Spiders on ceilings can be
annoying in normal caves. Trapdoors stop them by default, and you can switch ceiling crawling off.

### #5 Mutant Monsters
**What you'd see:** rare, huge versions of the zombie, skeleton, creeper and enderman. They're mini-bosses
with lots of health that smash the ground, throw blocks and charge you.
**Why it fits:** today almost everything dies to one Beam, so the ring never gets stretched. These are fights
where you'd *need* Tether to hold one off, a Wall to block a charge and Blast to finish it. It's boss-like
content that runs on 26.3 now, while the real boss mods haven't been updated.
**The catch:** they spawn in normal worlds (rarely), so a no-ring player can get flattened. The Mutant Enderman
picks up blocks, so it needs one check near our construct blocks.

### #3 Sound Physics Remastered (the "maybe")
Every sound echoes and muffles realistically: a Blast in a cave rolls down the tunnel, and things behind walls
sound dull. It costs nothing to try and is easy to remove. Some players find caves too echoey, and you can turn
that down in its settings.

## How to test 1, 2 (and 3)

**Instance:** a *separate* Fabric 26.3 instance (Prism or the official launcher + Fabric Loader), **not**
Lunar, so Lunar's bundled mods can't confuse the result. Jars, all from Modrinth, 26.3 Fabric builds:
- Lantern Ring (latest release) + Fabric API
- Sodium + Iris (to match J's Lunar setup)
- **1:** LambDynamicLights
- **2:** Physics Mod (free version)
- **3 (optional):** Sound Physics Remastered

**Steps** (a new creative world, then switch to survival for the cave):
1. **Ring at night in a cave (tests 1):** go to a dark cave at night. Hold the ring, then fly, Beam, place a
   Wall and hold the Dome. *Pass:* the cave lights up green around you and the constructs. Then turn on the
   Lantern Ring Complementary pack and check the same, because under shaders the pack's own light may take over.
2. **Blast at max (tests 2):** Ring Lab to max strength, Blast into a hillside, then once more down into a
   cave. *Watch:* chunks flying (Physics Mod) *and* our own crumbs. Is it too much? Did FPS drop, and for how
   long? Does the 50-block tunnel still finish?
3. **Shockwave in a crowd (tests 2):** `/summon` about 15 zombies and skeletons around you (or a spawner
   area), then Shockwave. *Pass:* mobs fly and die as ragdolls with no stutter. Repeat with our own allies and
   corps mobs nearby, to see whether they fall back to normal deaths.
4. **(3)** Repeat steps 1 and 2 and listen for the echo down the Blast tunnel.
5. Note anything weird and remove one jar at a time to find the culprit.

---

# Round 3 (2026-10-19): Stormie's Spiders, its real extent

J: *"show me the extent of stormies spiders before creating ceiling walking"*. Sources: the
[Modrinth page](https://modrinth.com/mod/stormies-spiders), its source on
[GitHub (demistorm/Stormies-Spiders)](https://github.com/demistorm/Stormies-Spiders) (read, not run) and its
open issues. Version 3.3.0+, LGPL-2.1, Fabric/NeoForge/Forge, 26.3 ✅. It's a fork of Spiders 2.0 (TheCyberBrick)
by way of Nyf's Spiders.

## Watch it
- Modrinth gallery: [crawling up and down walls](https://cdn.modrinth.com/data/3dsI6Hle/images/62085b31996e5a20ef8c084f71c46b147e1dee25_350.webp),
  [crawling down blocks](https://cdn.modrinth.com/data/3dsI6Hle/images/576343dbfbb460ee3e77fda84d72d249f70080d9_350.webp),
  and the page GIF ([spider crawling down a block](https://cdn.modrinth.com/data/cached_images/276629fbefab1efda0319c9d6dcf67bb8456a51e.gif)).
- No ceiling clip in the gallery and no official video found. Spiders 2.0 (same core) has a GIF on its
  [Modpack Index page](https://www.modpackindex.com/mod/19306/spiders-20). Searching YouTube for "Spiders 2.0 mod" shows
  older showcases of the same movement. **The honest way to see ceilings is the 2-minute test below.**

## What it does

| Question | Answer |
|---|---|
| **Walls** | Yes. Spiders attach to any solid face, walk up and down it with their body turned to the wall (not vanilla's "slide up while facing forward"), and go over the top edge smoothly. Stairs too. |
| **Ceilings** | Yes, upside down, **on by default** (`can_crawl_on_ceiling = true`, a toggle). |
| **Overhangs / round corners** | Yes, that's the core of it: it picks the nearest surface within ~2 blocks and smooths its body orientation over ~1.25 blocks, so it rolls from floor → wall → ceiling round an edge instead of snapping. |
| **Pathfinding across ceilings** | Yes. It replaces the spider's navigator with a 3D climber pathfinder (`AdvancedClimberPathNavigator`): paths can run up walls and along ceilings to reach you, and it finds its way round obstacles vanilla gets stuck on. It also gives spiders **+8 follow range**, a better leap-at-target and a shorter attack reach (toggle). |
| **Water / rain** | They avoid water while chasing, swim back to shore if they fall in (or sink, if you switch swimming off). Optional "can't climb in rain" (experimental, off). |
| **Spider-proof blocks** | A "disabled blocks" list: they can't climb over those. Trapdoors are on it by default. Good for trial arenas: a trapdoor lip stops them. |
| **Which mobs** | **The vanilla `Spider` class and anything that extends it**: spiders, cave spiders and modded mobs built on `Spider`. Nothing else gets the climbing. |
| **Can modded mobs opt in?** | **Only partly.** Rotation Overrides (3.3.0+, a config menu) can make *any* mob *look* like it's on the wall, but per its own description it "only adds rotations, no pathfinding changes", and it's client-side only. The same menu can *switch off* the mod for a given spider type. No tags, no public API. To get real climbing a mob must extend `Spider`. |
| **Multiplayer** | Needed on **server and client**. If only the client has it, spiders turn on walls but path like vanilla. If only the server has it, the AI works and a fallback keeps their rotation roughly right. |
| **Performance** | One open issue ([#16](https://github.com/demistorm/Stormies-Spiders/issues/16), 1.21.1 NeoForge, a big pack) reports FPS dropping from 120 to 1-20. Another big-pack user couldn't reproduce it, and the author says it shouldn't cost that much. 3D pathfinding *is* heavier than vanilla's, so a trial that spawns 50 spiders is the thing to measure. |
| **Known conflicts** | [Web](https://github.com/demistorm/Stormies-Spiders/issues/12) (another spider-AI mod: spiders stop attacking at random), PotsandMimics (crashes), Anti-Smooth (jitter). None of these are in J's pack. |

## What it can't do (plainly)
- **It won't make *our* mobs climb.** `BroodSpider` extends `ConstructAlly`, not `Spider`, so it gets nothing.
  Rotation Overrides would only *tilt* it on a wall it can't actually walk up.
- **No API for other mods.** We can't call "climb this wall" from our code or tag our own mobs as climbers.
- **It isn't general ceiling-walking.** Players, zombies and trial bosses stay on the floor. Its climbing
  code lives inside the `Spider` mixin, not in a reusable component.
- **It only climbs real blocks.** Our construct Wall/Dome *are* blocks, so spiders will climb them (and
  Dome lattice/glass may count as solid). That's worth testing, because it might be fun (they swarm the dome) or
  break the Dome's purpose. Particles and drawn-only things like the Shield aren't climbable.
- No guarantee across ceiling gaps: it walks surfaces, it doesn't jump between them.

## What this means for "creating ceiling walking"
- **If the trials only need *vanilla* spiders that climb everywhere:** use Stormie's Spiders as an optional
  extra. That's zero code: spawn vanilla spiders and cave spiders in the trials, and add trapdoor lips where they
  mustn't go.
- **If our own trial mobs (or Brood Spider) must walk ceilings:** the mod can't give that. Two options:
  1. Make the trial climber a subclass of vanilla `Spider` (with our own model/renderer). With the mod installed
     it climbs like Stormie's; without it, it climbs like a vanilla spider. That's cheap, but it's a soft
     dependency for the good version.
  2. Write our own climber, using Stormie's as the reference. Its LGPL-2.1 licence means copying code in
     would bring the LGPL into our mod, so re-implementing the idea ourselves is the cleaner path: attach to the
     nearest face, smooth the orientation, and use a 3D path node set. That's a real chunk of work (its movement
     package is about 10 classes).
- **Quick look before deciding (no code):** in a 26.3 Fabric test instance with Stormie's Spiders, build a
  5×5 stone room with a 4-high ceiling and an overhang outside it, `/summon spider` ×5 at night, stand on the far
  side of the overhang, and watch them go up the wall, across the ceiling and round the lip. Then place a ring
  Wall and Dome and see whether they climb those.
