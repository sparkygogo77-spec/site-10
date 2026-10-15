# Pass 820: zig-zag eye beams in the B1 look — WAITING

**Script:** `docs/blender/blender_updates/820_eye_beams.update.py`
**Open in Blender:** `C:\Users\Josh\Documents\LanternLive\combat\eye_beams.blend` (Cam Z1 side, press play; 80 frames;
each take also has "Cam <take> top" and "Cam <take> eyes")
**Files here:** `sheet.png` (one check at tick 22: Cam all on the left, Cam Z1 side on the right. The overview camera was
widened after it.)

J: "omega beams are the zig zag eye beams not this". The ring beam in 806 and 819 was mis-named (it is a ring beam, and
B1 is still the pick for it). His first note on the real ones: "the omega beams are very particle-y and hard to see".
So these are the eye beams, made from B1's picked look instead of particles. Each beam is a solid core inside a
hard-light sheath with two rim lines, and every corner has a bright joint. Twin beams leave both eyes and the eyes
glow while firing.

| Take | Path |
|---|---|
| Z1 corner hunter | straight out, a hard right round a pillar, a hard left, straight into the mob hidden behind it |
| Z2 zig-zag | a sawtooth (8 turns, narrowing as it closes) that homes in on the mob |
| Z3 split | round the corner of a wall, then each beam splits three ways, one mob each |
| Z4 corner hunter + glow | Z1 with B1's soft outer glow round each piece and light along the path |

**Timing (20 ticks a second):** the beams fire at tick 12. The front travels 3 blocks a tick so you can follow it in
Blender; the game can go faster. They hold for 30 ticks, then pull back from the eyes outward. On a hit, the mob gets
the outline flash you kept (815 F3) and a small knock.

**For the game:** each straight piece is a geometry beam (core quad + sheath quad + rims) between two points; the turns
come from the path the power already computes. That drops the particles that made them hard to see.

## J's verdict (2026-10-15)

Z1 corner hunter picked: "Corner hunter and the pattern should continue from there and go through each targer to the
last, if it hits a player it does not continue through them" - pass 829.
