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

## Files

- **Blender updates:** `docs/blender/blender_updates/81_super_jump`, `82_super_jump_r2`, `83_super_jump_landings`, `84_super_jump_landings2` (`.update.py`).
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
