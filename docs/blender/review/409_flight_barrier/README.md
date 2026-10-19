# Pass 409: flight barrier and trail, fast vs primed (movement, coordinator) — WAITING

J, in game (2026-10-15): "the barrier when im flying and primed as well as the trail should look better or different from
the fast flying activation". In game, fast flight and primed flight both draw the same placeholder (`RamBarrierFx`: a pale
cracked shockwave-glass cap; its `ram_barrier.bbmodel` hook was never filled).

**Open in Blender:** `C:\Users\Josh\Documents\LanternLive\movement\flight_barrier.blend` (Cam F, P1, P2, P3 = chase;
"Cam <take> side"; frames 1-120). Script: `docs/blender/blender_updates/409_flight_barrier.update.py`.

| Take | Look |
|---|---|
| F | Fast flight, not primed: a thin W1-weave cap the Dome's size (4.5 blocks) with a soft rim; one quiet ribbon off the ring fist |
| P1 | Primed: a six-sided hard-light lance point (1-3.6 blocks ahead), turning slowly one way, lit edges; twin helix ribbons behind |
| P2 | Primed: a domed shield of separate H1 hex plates 1.8 blocks ahead, breathing; a hex afterimage ring drops behind every 4 ticks |
| P3 | Primed: a hollow bullet nose of construct pixels (2-4 blocks ahead) round a dark core; a tail of pixels shrinking out over 0.9 s |

P1-P3 fly 2 s as F, then prime at tick 40: the cap folds away in 4 ticks, the primed look snaps on with a small overshoot and
a flash ring. Fast flat glide at 1 block a tick, ring arm leading. Glow kept moderate (J's glow complaint the same night);
every primed look stays clear of the eyes in first person. `check.png` is the check render (chase, side, first person).

**For J:** pick F (or improve it) for plain fast flight, and one primed look (or a mix: e.g. P1's lance with P3's tail).

**Rev 4 (2026-10-19): P3 only.** J rated P3 IMPROVE: "need better constructs and textures". The nose is now a shell of
staggered, bevelled dark-jade construct bricks (three tones, 12 courses) standing off a glowing mortar surface with a lit
tip, still round the dark core; the tail is the same bricks in three sizes plus bright flecks. F and P2 (DROP) and P1
(see pass 410 for its variations) are unchanged.
