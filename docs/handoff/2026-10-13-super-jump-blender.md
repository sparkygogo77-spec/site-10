# Super jump: Blender animation (passes 81–84)

This is from the super jump Blender chat. That chat does only the super jump: landings, craters and construct walls. The game side of the super jump is on branch `claude/project-thread-mt98dl`. The placeholder poses are in `SuperJumpPoses.java`, and the original brief is `plans/super-jump-blender-brief.md`.

## J's calls so far

- **Takes:** Take 1 is good, and so is Take 2. Take 3 is dropped, except that its landing (E3) is used for a fall deeper than the jump meant to go.
- **Rising:** the ring fist punches up and starts coming back down as soon as the rise loses momentum. It eases into the fall arm from halfway up and reaches it at the apex. See `full_air()` in pass 84.
- **Falling:** Take 1's fall, with the ring arm aimed at the ground. All three versions, D1a, D1b and D1c, "seemed fine". J's pick between them is still open.
- **Landing:**
  - the ring fist touches the ground: Take 1's E1, with Take 2's E2 as the alternative;
  - E1b (no torso sink) was tried and dropped, so go back to E1;
  - a fall deeper than meant uses E3, held about 1.5 s.
- **Effects:**
  - The rolling hard-light pane wall and the cracked-ground decal are out.
  - The sand crater and spray (L3) are "excellent", so every surface gets its own crater:
    - grass: dirt;
    - stone: a shallow crater with sparks and chips;
    - sand: a wide, shallow crater with spray;
    - water: no crater, just a pad on the water.
  - The ground under the player is a stepped bowl, not flat.
- **The construct where you land:**
  - Not a layer of particles. Instead, a small pad of green construct plates under the player, trapdoor thin, following the crater's steps.
  - A low wall along the pad's edge, as low as a slab and trapdoor thin or half that. The thickness is still to pick:
    - W1: 1/2 thick, 1/2 high;
    - W2: 3/16 thick, 1/2 high;
    - W3: 3/32 thick, 3/8 high.
  - A deeper fall makes a bigger, rounder crater. Its construct walls rise about 2.6 blocks around the player for protection, then fade and leave the crater.
  - Glow is low, in jade. The textures come from J's construct texture picks, which he wants to test in game.

- **In the air:**
  - the ribbon trail off the ring fist while rising is picked: R1, the shortest (2 ticks), locked to the fist;
  - the ring light and fist glow build up toward touchdown (passes 85–86).
- **Rising arm:** G2 + G3 together. The arm rests 15° forward and follows the aim, wearing the square emblem ring (pass 88).
- **Picked in game (2026-10-14):** E2 landing, W2 wall, BR1 emerald bricks; the construct should cover a wider area.
- **Not this chat:** K4 and K5 kneel poses are J's picks for the lead chat's kneel scene.

## Files

- **Blender updates:** `docs/blender/blender_updates/81_super_jump`, `82_super_jump_r2`, `83_super_jump_landings`, `84_super_jump_landings2`, `85_super_jump_air`, `86_super_jump_ribbon`, `87_super_jump_ribbon2`, `88_super_jump_rise` (`.update.py`).
- **Pose data:**
  - **Where:** `docs/blender/super_jump_poses.json` (round 1–2 poses) and `docs/blender/super_jump_landings2_poses.json`. The latter covers idle, D1a–c, E1, E2, E3, F2 and F3.
  - **Format:** each part has `rot` = (xRot, yRot, zRot) in radians, applied as ModelPart rotations. `offset_px` is added to the part's x, y and z in model pixels. The ring arm is `rarm`.
  - **Left-handed:** swap the arms and the legs, and negate yRot, zRot and the x offsets.
- **Timing, in ticks (pass 84):**
  - crouch to armed: 7;
  - armed to full: 18;
  - launch: 5;
  - rise: 20;
  - fall: 28;
  - landing hold: 16 (deep: 30);
  - stand-up: 8.

## Lantern Live add-on 1.1

- `docs/blender/lantern_live_link.py` now remembers what it has run in `applied.json` in the watched folder. Restarting Blender or clicking Watch again no longer replays every old update.
- J's copy is installed.
- If the panel says Watching but nothing applies, click Watch off and on.
- `.update.py` files only run through the watcher. Run Script fails on them with "FOLDER is not defined".

## Next

Waiting on J's picks:
- the fall arm: D1a, D1b or D1c;
- E1 or E2;
- the wall thickness: W1, W2 or W3;
- the construct texture, to test in game.

After that, a game brief with exact poses and effect numbers will go to the coordinator. Pass numbers stay under 100, then 300–399.

## Pass 91 (2026-10-14)

- **J on pass 90:**
  - Coverage: P2, P4a, P4b and P3 are all needed. Each ring gets its own, interchangeable later.
  - Looks: T9, T6, T1 and T2 are good. T3 H1 neon is the only hex look to use. T5 R2 K1 needs an in-game test.
  - The classic textures are out.
  - T4 X3 is too bright and too still.
- **Pass 91 `91_super_jump_x3_motion`:** builds `LanternLive\super_jump_x3_motion.blend` with `tex_*.mp4`. It shows the P3 landing in T4 (X3 as in game), XM1 drift, XM2 currents and XM3 pulse.
  - The textures are movies here, so they play with the timeline.
  - A 4 × 4 block sample wall stands behind each landing.
  - The generator is `tools/super_jump_x3_motion.py`, and the strips are in `docs/blender/models/x3_motion/`.

## Passes 92–93 and the texture library (2026-10-14)

- **J's latest:**
  - Keep H1 blue: it is the hex for every colour, so make crimson and yellow (and all six) versions.
  - The X3 decision is the lead chat's X3D1 glass, so XM1–XM3 are dropped.
  - Red R2 is good.
  - Every good texture is a must in every colour.
  - Needed in every format: strips, particles and landing barrier.
  - Everything goes in one folder for future use.
- **Texture library:** `docs/texture_library/` (see its README). J's copy is in `Documents\LanternLive\texture_library` with the Blender movies, plus `texture_library.zip` containing the whole folder.
- **Pass 92 `92_construct_smoke_rays`:** builds `LanternLive\construct_smoke_rays.blend`.
  - Light comes from real lights in the walls, so it reads under shader packs.
  - Haze makes the light visible, and the smoke volume glows and casts shafts.
  - Takes: S1 wisps, S2 curtain and S3 embers on BR1 emerald, then S1 on H1 crimson, yellow and blue.
  - Watch in Rendered view (EEVEE, volumetric shadows on).
- **Pass 93 `93_red_tower_v2`:** J asked here for the Red towers (pass 202, normally the lead chat's) to be rebuilt with the new textures and the crimson diamond blocks. It builds `LanternLive\red_tower_v2.blend`.
  - **Row A:** diamond accents, R2 bloodfire crimson ribs and X3D1 crimson glass.
  - **Row B:** a diamond body with R1 magma ribs.
- **Watcher:** J's Lantern Live Folder box was empty. I set it again, but the panel still says "Not watching", so I open the scenes in J's Blender by hand for now.
