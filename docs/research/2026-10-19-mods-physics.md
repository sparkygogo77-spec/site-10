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
