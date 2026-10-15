# Pass 816: ring-hand gestures, round 2 — WAITING

**Script:** `docs/blender/blender_updates/816_ring_gestures2.update.py` (replaces 814)
**Open in Blender:** `C:\Users\Josh\Documents\LanternLive\combat\ring_gestures2.blend` (Cam X4 Put the ring on - third
person, press play)
**Files here:** `sheet.png` (one check: 8 moments, third person then first person side by side. After it, X3's
first-person hand was moved above the view so the arm no longer fills the screen.), `gestures2_poses.json` (solved
keys, solver error per key, first-person keys)

J on 814: the camera names and the file needed a better description of what each one is for, especially X4 ("as the
ring goes on what"). The animations were subpar; in first person the ring filled the view and glowed white.

**Descriptions in Blender.** Each take is in its own collection, named for what it is for. A board behind each player
gives the name, what it is for and the beats by tick, and there is an "about this file" note at the left. Cameras are
named "Cam X4 Put the ring on - third person" / "- first person".

| Take | What it is for | Beats (20 ticks a second) |
|---|---|---|
| X1 Cast | firing a power (Blast, Beam), once per shot | 1–6 wind-up, 6–10 the arm snaps out, the left arm swings back, the left foot steps; 10–12 flare and bolt; hold to 28; settle by 44 |
| X2 Oath | the lantern oath / a charge-complete emote | fist to the heart by 8, head bowed; 18–23 the fist drives up (overshoot), the head lifts after it (40°, under the 57° limit); a column of light 22–30; held to 46; down by 60 |
| X3 Focus | charging at a lantern / a focus power-up | the ring stops exactly on the brow at 12, the head bows 20° to meet it, the eyes light, two slow breaths, release by 52 |
| X4 Put the ring on | the moment the ring goes into the ring slot | the ring is its own object: held in the left hand (1–8), slid onto the right hand (8–16), click at 16, power-up 18–22 (fist, arms down and out, knees bend, light ring, outline flash), held, stand by 46 |

**Motion fixes.** A small solver places the hand, or the ring, exactly on its target each key: the chest, the brow, the
other hand. The worst miss is 2.3 cm, except 5.5 cm for X4's left hand at the click. Moves have a wind-up, a snap, an
overshoot and a settle; the head and body follow the arm; the weight moves through the legs.

**First person.** Both arms, with the hands placed inside the 26 mm frame at 0.75–1.05 m depth, so they no longer fill
the view. The ring is a darker saturated green, (0.02, 0.85, 0.15), and its glow tops out at 2.4 so it reads green in
the viewport too. The effects stay off the lens: the oath column is thin, X4's light ring stops 1.6 m out, and X3
tints the view green instead.

**For J:** KEEP / IMPROVE / DROP per take.
