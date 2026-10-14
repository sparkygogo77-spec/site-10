# Dread Runner kill animation (Blender pass 420)

Coordinator: "J wants it to be a proper mob with a kill animation made in Blender. Please make
options for J to pick from."

There are four kill takes, animated on the game's own Dread Runner rig: the same parts, pivots and
angle format as `bbmodel/dread_runner_rig.json`. Each clip starts and ends on sprint frame 0, so it
cuts in and out of the run cleanly. J picks one, or several to choose between at random.

## Takes

| Take | What happens | Length | Hit frame |
|---|---|---|---|
| **K1 Pounce & pin** | It drops low, springs, slams both claws down on the mob, pins it and lunges with the head, then rises and runs on | 1.6 s (39 f) | 17 |
| **K2 Grab & hurl** | It seizes the mob in one claw, hoists it overhead, twists and hurls it ahead; the mob tumbles and lands | 1.8 s (43 f) | 30 |
| **K3 Fear scream** | It stops dead, rears up, flings its arms wide and screams; the mob drops where it stands without being touched | 1.9 s (45 f) | 20 |
| **K4 Rake through** | No stop: two overhand claw rakes mid-stride, its legs keep running, and the mob falls behind it | 1.1 s (27 f) | 10 |

The mob in the renders is a plain stand-in (a blocky 2-block figure), not a game mob.

## Where to look

- `renders/takes.gif`: all four takes playing together.
- `renders/kill_k*.gif`: each take alone, at full size, with the frame number. The hit frames are marked HIT.
- `renders/takes.png`: a filmstrip, one row per take: start, wind-up, just before the hit, hit,
  after, end.
- **In Blender:** open `blender/runner_kills.blend` (textures relative, in `blender/textures/`).
  - Cameras: "Cam K1 side" to "Cam K4 side", and "Cam K1 front" to "Cam K4 front".
  - All four play at once on frames 1 to 59; press Space.
  - Each take's hit frame is stored as a scene property: `K1_hit`, etc.

## For the game thread

`rig/dread_runner_rig.json` is the current rig plus a `"clips"` object. It is a drop-in
replacement: `DreadRunnerRenderer` reads only `parts`, `frames` and `stride_seconds`, so the
extra keys are ignored until code uses them.

Each clip is `{seconds, frames, root, target, hit}`, at 24 fps:

| Key | Meaning |
|---|---|
| `frames[i]` | Per-part angles, the same format as the sprint `frames` (generator-frame XYZ degrees) |
| `root[i]` | The runner's offset in model px (x right, y forward, z up), turned with its heading and added to its position; this covers the leaps and lunges |
| `target[i]` | Where the victim's middle should be held, in model px (x right, y forward, z up). It is measured from where a standing mob's middle sits (16 px up), at the runner's position when the clip started. `null` means let go: K2 throws with the velocity of the last two frames; the others just let the mob fall |
| `hit` | The frame to deal the killing damage and play the sound |

A suggested hook-up:
1. When the runner reaches its prey, freeze its AI and record its start position and yaw.
2. Pick a clip and play it, by frame index from the clip's start tick. The existing Catmull-Rom smoothing in
   `DreadRunnerRenderer` works on these frames as they are.
3. While `target` isn't null, move the prey there each tick. Damage it on `hit`.
4. When the clip ends, go back to the sprint.

To regenerate: `python tools/runner_kill_clips.py <rig in> <rig out>`, where the key poses are
in `CLIPS`. Then run `/opt/bl/venv/bin/python tools/blender_edits/runner_kill_scene.py <assets> <rig out> <out dir>`.
Set `ONLY=K2` to render one take, or `LL_NO_RENDER=1` to build the .blend only.

**Not done:** sound, damage, particles at the hit, and how it looks in game. Those belong to the
game thread once J picks.
