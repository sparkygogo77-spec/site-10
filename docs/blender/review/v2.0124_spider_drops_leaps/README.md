# Pass v2.0124: spider drops, re-attaching and real leaps

J's notes on v2.0120 (L1 IMPROVE, L2 IMPROVE, L3 IMPROVE, L4 notes, the eyes rule), answered with three drops, four
leaps and M3 with its eyes first. Research: `docs/findings/2026-10-20-spider-dragline-drop.md`.

- Open in Blender: `C:\Users\Josh\Documents\LanternLive\trials\spider_anims7.blend` (cameras `<code> cam`; the v2.0110
  KEEPs `M1 cam`, `M3 cam`, `M4 cam` are in the same file)
- Clips: `C:\Users\Josh\Documents\LanternLive\trials\renders_anim6\`
- Build: `blender -b --python site-10\tools\trials\spider_anim_tests.py -- <out.blend> --only M1,M3,M4,M3b,L1a,L1b,L1c,J1,J2,J3,J4 [--check] [--stills] [--video --video-codes ...] --rdir renders_anim6`

New in the rig (`move_take`):
- `eyes=True`: a hit is only scheduled on a frame where a ray from its eyes reaches your head and you are in front of
  its head (M3's first stab failed this; M3b passes).
- `air_v="reach"`: in the air the feet start tucked and slink out over the first 60% of the flight toward the surface
  it will land on, each on its own side; a leg never reaches through rock (it stays tucked until the line is clear).
- `leg_fn`: scripted feet (hand over hand up the thread, front legs grabbing the roof, priming, push-off); runs ease in
  and out over 5 frames, and a foot letting go arcs out and away from the body.
- `flight()`: ballistic keys at 40 blocks/s/s; `pushoff_take()`: crouch, prime, last pair pushes off, soft landing.
- Hits are at least 8 frames apart (two spikes never arrive together).

Leftovers (measured, in the labels): the moment it kicks off or lets go still has 0-5 frames of a leg grazing (J1 is
clean). Not done: a construct (fear-ring) version of the floaty L3, which J said could suit the yellow spider.
