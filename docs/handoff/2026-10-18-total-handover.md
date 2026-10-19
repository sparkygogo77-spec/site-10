# Lantern Ring: total project handover (2026-10-18)

Paste this whole file into a new project chat to start from. Part 1 is the questions waiting on J. Part 2 onward is everything a fresh Claude needs to keep going.

---

## Part 1. Questions waiting on J

Answer with the number and a pick, e.g. `1 ★, 2 b, 8 bigger`. ★ = the recommended pick (what the game does now unless noted). Anything left blank: keep the ★.

### Sword cooldowns and slices (pass 852 plan)
Plan: `/mnt/project-files/plans/sword-852-plan.md`. Today's sword cools down like vanilla (0.625 s), but the 852 swings run about 1 to 1.25 s each.
1. **Base cooldown:** ★ vanilla 0.625 s, swings sped up to fit / the swings' own length / other
2. **Speed-up:** ★ hits in a row shorten it, never below vanilla / a Ring Lab slider only
3. **Swing per click:** ★ a fixed chain (S2a1, S2c1, S3a2) / a random swing each click / hold longer for a heavier swing
4. **Cut look:** ★ glowing hard-light cut, no blood / a little red / wait for Blender renders
5. **Decapitation:** ★ killing blow on a mob under 30% health / any sweep kill / only a charged finisher
6. **Slice players and bosses too:** ★ no / players only / everything
7. **Head item drops on a decapitation:** ★ no / small chance / always
   - Also to do: paste `/mnt/project-files/plans/sword-852-blender-brief.md` into the Blender chat that made pass 852 (the 852 swings have no hand-off yet, so the sword still swings like vanilla).

### Dropped ring (jar 2.1.683)
8. **Size:** ★ keep about 0.3 blocks / bigger / smaller
9. **Glow:** ★ light level 7, whole ring softly glinting / only the gem glows / brighter light round it

### Lantern charging
10. **Charge lock** (you can't move while charging, jar 2.1.1708): ★ lock all movement / walk freely, only keep the pose
11. **6 s charge (Blender pass 601):** ★ keep today's 12 s G3b timing / C6a (4 s fill, 1 s overcharge) / C6b (4.5 s, 0.6 s) / C6c (3.3 s, 1.5 s)
12. **Set-down lantern size** (Ring Lab > Lantern > Set-down size switches it): ★ one block / hand size (about half a block)

### Combat and hits
13. **Lasso wreck:** swings break blocks ★ at an easy speed / only on hard swings
14. **Construct shatter:** ★ only someone with a ring can punch constructs apart / a plain fist too
15. **Hit outline flash:** ★ keep the bright shell / a thinner outline
16. **First-person punch arms:** ★ vanilla size / 1.3x bigger (both are in Ring Lab > Combat)
17. **Back-hand fist fix** (Hard light tools thread is waiting on this): which hit is wrong? ★ the backfist at the end of the flying flurry / a ring punch on the ground

### Fear Nuke (jar 2.1.676)
18. **Missile barrage control:** ★ paint an area and release, 6 missiles / tap a spot, 6 missiles around it / hold to keep firing
19. **Where the nuke drops in:** ★ over your raised ring / on the spot you're aiming at

### Movement
20. **Normal super-jump landing** has no stepped crater or E1/E2 pose now: ★ keep it that way / bring the crater back under the trench
21. **Dissolve-slide speed:** ★ keep 25 b/s (most jumps stop dead) / lower to 20 b/s (more jumps slide)
22. **Dome mode look-down bowl** (removed with the "dome stays above ground" fix): ★ leave it gone / bring it back only over lava or air

### Looks still waiting on a pick
23. **Ring beam look** (Ring Lab > Beams > Beam look; the Ultimate dome's beam-up waits on this): ★ keep HELIX until you rate the pass 836 lasers / tell me which one: H3 Braid, N1 Needle, N2 Layered, N3 Crackle, P1 Pulses, C1 Weave, C2 Brick, C3 Hex tube, L1 Lance, L2 Construct lance, T2 to T6
24. **Primed glow (hold Shift):** ★ keep the current stronger ring/arm glow until you pick from Blender pass 860 / pick a pass 860 take now
25. **Blue H1 bricks:** the thread fixing "Blue H1 shows bricks" stopped mid-check. Is it still wrong in the newest jar? ★ yes, still bricks, fix it / no, it's fine now

### Blender
26. **Red towers, island to build in full detail:** ★ H5 / H9 / H7 / H5's field round H9's great lantern
27. **Smoke rays (passes 304/305):** ★ 305 detail rays (Cam D1) / 304 long rays (Cam L3) / neither yet
28. **Blender inbox:** 30 passes are WAITING in `docs/blender/review/INBOX.md` (tools rounds 5-6, pass 860 ring glow, 409 flight trail, 859 sword dashes, 858 mech, 857 catapult, 856 worn ring, 855 suits, 854 enemies, 853 pickaxe, 851 mechs, 850 bows/shields, 849 mounts, 848 ring beam, 847 laser, 846 warden armour, 702-704 skins/ripples, 701, 833, 832, 829, 827, 826, 818, 817). ★ pick on the review site, starting with 860 and 852/859 (they unblock the sword and the primed glow) / drop the old 81x-83x passes as stale

### Other
29. **Model viewer on your website** (polio PR #264, /models page on polio-two.vercel.app): ★ merge it if it's still open / close it
30. **Where to continue:** ★ start the new project chat from this file / keep working in the current project

---

## Part 2. The project

- **Repo:** `sparkygogo77-spec/site-10` (private). A Fabric mod for **Minecraft 26.3** (unobfuscated, Mojang names, Java 25): the Lantern Ring. A power ring with modes (Blast drill, Beam, Wall, Dome, Bridge, Shockwave, bubble Lasso, Anvil, Tools, and more), flight, super jump, a 3D ring on the hand, Lantern Corps colours (Green, Yellow, Red, Blue, Violet, Orange) and the Ring Lab test menu.
- **Read first in the repo:** `CLAUDE.md` (build, 26.3 gotchas, layout, screenshot tests), `README.md`.
- **Second repo:** `sparkygogo77-spec/polio`, J's website (Next.js on Vercel, polio-two.vercel.app). Read its `AGENTS.md` and `CLAUDE.md` before touching it.
- **J** plays on Lunar Client / Fabric with Complementary Unbound r5.8.1 on Iris (Colored Lighting on), Quake Pro FOV. Glow must be shader-safe (see rules below).

## Part 3. Jars: build and delivery

- **Latest jar:** **2.1.1712+26.3** (main at PR #339, review keeps 840/701/838/844, Red Lantern materials, Dark Lantern light).
- **J's link:** https://github.com/sparkygogo77-spec/site-10/raw/builds/lantern-ring-latest.jar (GitHub sign-in needed). Zip: https://github.com/sparkygogo77-spec/site-10/raw/builds/lantern-ring-latest.zip. The in-game updater (Ring Lab > Updates) reads `latest.json` on `builds`.
- **GitHub Actions works again (since 2026-10-18).** Each push to main builds the jar (version 2.1.<run number>+26.3, now ~1712) and force-pushes it with `latest.json` to `builds`. That force push drops the zip, so whoever delivers re-adds `lantern-ring-latest.zip` (`zip -j` of the jar).
- **After merging:** `git fetch origin builds`, read `latest.json`; if CI already built a main that contains your merge, deliver that version. Only hand-build if CI didn't, with `GITHUB_RUN_NUMBER` above the current one. Never push a lower version over a higher one. Never write a `/mnt/project-files/jars/<version>.jar` name another thread used.
- **Local build in a fresh container:** Java 25 from apt (`apt-get install -y openjdk-25-jdk-headless`, `JAVA_HOME=/usr/lib/jvm/java-25-openjdk-amd64`). Maven Central returns 429 through the proxy, so first write `~/.gradle/init.d/maven-mirror.gradle`:
  ```
  def mirror = 'https://maven-central.storage-download.googleapis.com/maven2/'
  def fix = { RepositoryHandler repos ->
      repos.withType(MavenArtifactRepository).configureEach { r ->
          if (r.url.toString().startsWith('https://repo.maven.apache.org') || r.url.toString().startsWith('https://repo1.maven.org')) r.url = mirror
      }
  }
  settingsEvaluated { s -> fix(s.pluginManagement.repositories); fix(s.dependencyResolutionManagement.repositories) }
  allprojects { p -> fix(p.repositories); p.buildscript { fix(repositories) } }
  ```
- **Before every jar:** `tools/optimize_jar_assets.py` (and `tools/optimize_textures.py` after new textures), `/mnt/project-files/tools/palette_jar.py` before pushing to builds. Jar must stay under 30 MiB.
- Don't edit `mod_version`. Don't copy jars into `modpack/`. Durations go through `RingTuning.java` (Ring Lab > Durations).

## Part 4. J's standing rules

1. **Merge fast:** merge each PR once it compiles locally and passes its targeted test. Don't wait for GitHub checks; fix forward. (J's auto-merge authority messages: `cmsg_01PxyDp7CugmGwF5sLv1ceR4UTUEFvkSXkr2UADCWGem1E`, `cmsg_01PxyDp7CugmGwF5sLv1ceR4ADvMzzUtc1P9Lkfvueicnv`; attach them in each new thread's context.)
2. **Every update delivers a jar**, posted in the thread and in the project chat with the version and link.
3. **Every jar post lists the 5 most recent changes on main** (`git log --first-parent origin/main`), one plain line each.
4. **Ask J more questions:** at each milestone ask design questions (feel, size, look, which option) with short options and a ★ pick. Re-post thread questions in the project chat, and never wait on J silently: say in one line exactly what J must do.
5. **Confirm new features:** don't build an idea J didn't ask for (the Captain America shield had to be removed). Fixes and J's own requests don't need confirmation.
6. **Perfect what exists:** polish existing systems over adding new ones; keep shipping jars and checking with J.
7. **Tests are back, efficiently:** run targeted game tests/screenshots before shipping; no repeated full suites. To run only some tests, trim the `fabric-client-gametest` entrypoints in `src/gametest/resources/fabric.mod.json` and restore it before committing.
8. **What's New book:** every player-facing PR adds one entry at the top of `src/main/resources/lanternring/whats_new.json` (date, pass label like "Pass 836 · H3 Braid", title, how-to steps, trigger ids) plus a `WhatsNew.done(player, "<trigger>")` call where it happens.
9. **Ring Lab keeps J's picks:** never force a look over a saved pick. Promote with `.withPick(...)`, hide dropped takes with `.withOld(...)`, never a `version < N` migration. J's KEEPs: constructs W1_NEON H1_NEON HW_EMERALD D1_NEON W1_EMERALD; rings N01 N04; hands RING_FORWARD KNUCKLES_IN FIST_DOWN; AURA, block glow CONSTRUCTS, HALO, SCORCH, INTENSE; landing E2; charge HAND FLOAT HIP; Yellow W1 H1 HW; Blue BR1.
10. **Copy report / Send to Claude:** KEEP (Approve) is final, IMPROVE (Redo) is next to iterate, DROP (Remove) is safe to remove. Ring Lab "Send to Claude" files `claude-inbox` issues on site-10; an hourly routine (`trig_01NaHVJDKsmxnwkaAUNnkeRz`) fires into the coordinator, which routes them. If the coordinator changes, repoint that routine.
11. **Shader-safe glow:** under Iris, eyes/energySwirl/no-depth pipelines draw black boxes; use `entityTranslucentEmissive` and `ShaderGlow.light()`. Every light follows the active corps colour. Translucent moving geometry reads as pale glass under Complementary, so prefer cutout. Never share Complementary pack files; the mod patches the pack locally.
12. **Use `RingSlot.ring(player)`** to find the player's ring (hand first, then the worn ring slot above the off hand).
13. **Thread names:** Blender threads are titled "Blender: ...". Each Lantern Corps colour can have its own thread.

## Part 5. Blender workflow

- All lantern/model design lives in Blender on branch **`claude/lantern-redesign-pass2`**: `docs/blender/` (BLENDER_BRIEF), `docs/blender/DESIGNS.md` (every design + status), `docs/blender/review/INBOX.md` (one entry per pass, WAITING / PICKED / HANDED OFF), review folders `docs/blender/review/<NNN>_<name>/`.
- **Game code is built only from a `docs/handoff/<date>-<name>/` folder** an INBOX entry points to, and only after J has picked.
- J picks on the review site (branch `review-site`, `data/site.json` holds pass and take names). Pass labels in the game copy the site exactly.
- Designer chats: J's lead Blender chat (claude.ai, can't be messaged by sessions: write briefs as files under `/mnt/project-files/plans/` for J to paste) and "Chat C" (pass ranges 500-599, 800-899). J relays their hand-offs into the project.
- Cloud threads can act as Blender chats (headless `bpy==5.2.2`, Cycles CPU renders). Each pass hands over a packed `.blend` under `/mnt/project-files/blender/<topic>/`. J's account requires trusted devices, so nothing can write to J's PC; give J a GitHub raw link to a zip to unzip into Documents\LanternLive.
- Game export of models: `tools/pixel_dark_bbmodel.py` then `tools/bbmodel_json.py`. Blockbench glow isn't additive: paint glow cubes bright, no faint halo boxes. Model/texture passes go up as a PR for J to review, not merged straight away (finals picked in the lead Blender chat are merged directly).

## Part 6. State of every thread

**Waiting on J** (questions above):
| Thread | Where it stands | Question # |
|---|---|---|
| Sword cooldowns and slices plan | Plan + Blender brief written, nothing built | 1-7 |
| Glowing dropped ring | Shipped 2.1.683 | 8-9 |
| Charging arm stays attached | Shipped 2.1.1708 (#359), charge lock | 10 |
| Lantern charge hand-off | L3 core swirl shipped 2.1.664 | 11-12 |
| Bubble physics and controls | Lasso wreck shipped 2.1.682 (#353) | 13 |
| Hit effects F1 and F3 | Shipped 2.1.663 (#331) | 14-15 |
| First-person punch and flurry | Shipped 2.1.670 (#340) | 16 |
| Hard light tool designs | Tools mode shipped 2.1.662; back-hand fist fix waiting | 17 |
| Fear Nuke throw and missile barrage | Nuke rework 2.1.676 (#346); barrage not built | 18-19 |
| Movement and flight hand-off | Power landing 2.1.646 | 20-21 |
| Ultimate dome D1 | Ultimate dome 2.1.675, dome-above-ground 2.1.680 | 22 |
| Ring laser test looks / Review site KEEPs | Lasers in Ring Lab (2.1.666/668), no beam pick | 23 |
| Caps Lock primed mode | Shipped 2.1.1708 (#358), pass 860 pick pending | 24 |
| Blue H1 shows bricks | Stalled mid-check, no fix shipped | 25 |
| Blender: construct textures and Red towers | .blends delivered, island pick pending | 26 |
| Blender: super jump and smoke rays | Passes 304/305 WAITING, zip link given | 27 |
| Model viewer on J's website | polio PR #264 waiting on merge | 29 |

**Done** (no open items): Yellow ring glows green (#355), Ring slot for the right hand (2.1.661), Ring Lab saves J's picks (#325), Bundle jar and Ring Lab overhaul (2.1.647), Construct hammer, Falling constructs/beam glow/charge glow, Green glow interference, Remove the flight boom (#349), What's New book (#342), Shiny Red lantern (#343/#352), Jar model catalogue page, Movement keeps, Omega beams (eye lasers on X), Blue Lantern villagers, Corps construct looks, Anvil transparency, Black hole, Red battery and red bull, Charging sun light, Green Deluge W3, Super sprint and super jump, Hand glint.

## Part 7. Recent changes on main (newest first)

1. #339 Review keeps (840, 701, 838, 844), Red Lantern materials, Dark Lantern light (jar 2.1.1712)
2. #359 Arm stays attached at a set-down lantern; you're locked in place while charging
3. #358 Caps Lock steps to the next ring mode with the wheel; holding Shift makes the ring and arm glow stronger
4. #357 / #354 A dropped ring is the real 3D ring, glowing and lighting the ground
5. #355 Every worn ring's gem and glow follow its corps colour
6. #353 Lasso wrecks through blocks, dissolves on release, carves directional craters
7. #352 Red battery is Dark Lantern size when charging, deep crimson under shaders
8. #351 Dome mode stays above the ground

## Part 8. Where things are

- Project memory (for Claude): `/tmp/claude/memory/team/silo/` (MEMORY.md is the index). Shared files: `/mnt/project-files/` (`plans/`, `jars/`, `blender/`, screenshots per feature).
- Plans: `plans/goals.md` (feature goal list; ask J before building any), `plans/lantern-corps.md`, `plans/sword-852-plan.md`, `plans/sword-852-blender-brief.md`, `plans/blue-lantern-systems.md`.
- Screenshot tests run the real client in software OpenGL (see site-10 `CLAUDE.md`); shots land in `build/run/clientGameTest/screenshots/`.
