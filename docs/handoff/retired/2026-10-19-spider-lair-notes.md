# Retired: spider lair notes 1-4 chat (rounds 8-10), 2026-10-19

## Range / role

Blender modeller chat for J's lair notes 1-4 on the R2 brute (the Dread Warren's lair spider), started by Lantern
coordinator 4. No review-site pass numbers were used (v2.0110 stayed free): everything is in `tools/trials/` and
`LanternLive\trials\`, with picture pages per round. J closed it: "It's good: wrap up".

## Open work

- **Next spider round** (J, move chart kept): "we will need more extending or movement attacks from the spider to make
  it not just stationary": attacks where R2 moves and reaches (charges, leaps, sweeping reaches), on top of S1-S4.
- **Not built yet:** the wall version from the move chart (R2 climbs a wall to you, then S1 from the wall).
- **Known leftovers (measured, all in `trials\spider_anims4_report.json`):** C1's thread climb and flip still have 7
  frames with a leg in the ceiling and 8 touching; D2 has 5 floor frames of 154, D3 2 of 140; P1 3 touching of 168;
  S3's two spike tips meet at you in the scissor (4 frames, by design).
- **For the game (when J says yes; he said "Not yet" to hand-offs):** R2 needs tunnels and pits about 30 wide; the
  orb-web tunnels (`spider_sequence.py --web orb`, J's pick) are 9 wide, so widen them or keep them for small
  spiders. The leg IK recipe below is what the game's spider legs should do.

| Round | Page | File (`LanternLive\trials\`) | Cameras |
|---|---|---|---|
| 8 | https://claude.ai/artifact/FUgD85FBw2CmbaXmSueMxD | `spider_anims2.blend`, `spider_web_layouts.blend` | W1-W3, D1-D3, S1-S3, C1b cam; T0-T3 x-ray |
| 9 | https://claude.ai/artifact/C6YUbn59hLWzFWG46mHN9F | `spider_anims3.blend` | W1-W3, D2, D3, S1-S4, C1b cam |
| 10 (final) | https://claude.ai/artifact/PdEjrfKu9nHxrP9NJNn9bw | `spider_anims4.blend` | W3, D2, D3, P1, C1 cam (+ S1-S4, C1b) |

Videos: `renders_anim2\` (round 9 and the stills), `renders_anim3\` (round 10). Build:
`blender -b --python site-10\tools\trials\spider_anim_tests.py -- <out.blend> [--check] [--stills] [--video] [--only W3,D2,...] [--video-codes ...]`.
Hand-off detail per round: `docs/handoff/2026-10-19-spider-lair/README.md` ("Round 8/9/10"). Research:
`docs/findings/2026-10-19-spider-leg-movement.md`.

## Files

Superseded on J's PC (can go to `_to_delete\`): `trials\spider_anims2.blend`, `trials\spider_anims3.blend` (round 10
holds every take), `trials\renders_anim\` (round 7), `trials\spider_web_lattice\`, `trials\spider_web_natural\`
(T2/T3 not picked; keep `spider_web_orb\` and `spider_web_layouts.blend` for the pick's x-ray). Keep
`trials\renders_web\maps.png`.

## Lessons for the design skill

- **"Legs touching" means legs through the floor.** "When i meant legs touching i meant legs colliding through the
  floor" (round 9). Every creature take reports measured numbers in its video label: legs through floor/ceiling, legs
  touching each other or the body, and for strikes the spike-to-player distance on each hit frame.
- **Strikes land unless they're a ranged construct attack.** "the strike is only okay making no contact if its using
  the yellow constructs and sending webs that way, otherwise i want a contacting strike" (round 8).
- **Movesets by situation, and moving.** "all four as seperate moves but massively depending on distance and
  orientation" (round 9), "more motion and points on each" (round 9), "more extending or movement attacks ... not just
  stationary" (round 10): give a chart of where the player is against the move; strikes travel and hit several times.
- **Research the real animal first.** "then research spider leg movement" (round 9): cite it in `docs/findings/`.
- **Burrows join the network.** "make sure the burrows are accessing part of the pipeline instead of making short new
  ones" (round 9); tunnels "organized or natural grid ... all around" (round 8), T1 orb web picked.
- **Digs quick but readable.** "the bury animation should be a quick one" (round 7) then "slower ... a digging arm
  animation and to smoothly settle into the blocks on all sides and ceilings" (round 9): ~1-2 s, digging strokes,
  feet settle on tunnel walls and ceiling.
- **Size spaces to the creature.** A 36-block spider needs ~30-wide tunnels and pits; narrower and its legs fold
  through its body (round 10).
- **Ceiling capture.** "shoot slow projectile spreading web that captures me on the ceiling and it zips up and patrols
  upside down with the same leg rules all the time" (round 9): this lifted the climbing hold for R2's animations.

## Gotchas

- **Leg IK that never clips** (the recipe in `spider_anim_tests.py`): foot rays hit only the ground (BVH trees of the
  course meshes, never the spider's boxes); aim feet within 36-88% of the leg's reach; reject spots behind the back
  plane (enclosed spaces allow up to 22 blocks); pull a foot back onto a ledge rather than down a drop; catch-up step
  when a planted foot is past 88% of reach or 9 blocks off its spot; then a per-frame knee search (knee out / fore-aft
  / up grid, foot kept planted, small cost for change); body clearance lifts the body until hips are 1.5 clear. Use
  the same sample count in the fixer and the check, or grazes hide between samples.
- **Paths:** never turn 90 degrees in one frame (feet cross); level the body again at the top of a slope.
- **Cutaways:** cast feet and check the floor against the whole ground; only the picture is cut open.
- **Course edges:** pad courses 30 blocks past both ends.
- **Render lock:** wrap headless renders in a script that refuses when `review-site\BLENDER.lock` or `RENDERING`
  exists, writes its PID to BLENDER.lock and removes it after; when locked, run a background wait-then-render.
- **Check mode:** `--check` builds without rendering in 5-20 s; iterate there, render once.
- **Version outputs per round** (blend, render folder, page): round 9's re-render overwrote round 8's stills.
- **Coordinator id:** the id in a start-up brief can be wrong; when SendMessage fails, check `list_sessions {"linked": true}`.
- **Heredocs:** write patch scripts with the Write tool; three heredoc patches broke on quotes and backslashes.
