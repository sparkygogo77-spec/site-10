# Retired: the spider lair chat (began as the Titan bosses pitch), 2026-10-19

## Range / role

Started by Lantern coordinator 3 as the Fallen Titan room-boss design chat. J turned the first pitch down ("These are
awful") and steered it to a giant-spider cave, which grew into the **spider lair, the Dread Warren's ending**
(placement A). Later the same chat did three more Titan boss rounds, ending with J's "forget the titan,". No review-site
pass numbers were used: everything is in `tools/trials/` and `LanternLive\trials\`.

## Open work (for the fresh chat: "Lair notes 1-4")

J's notes on the R2 animation tests, word for word: "the legs should never collide, the bury animation should be a
quick one instead of that one that isnt animated, the strike is only okay making no contact if its using the yellow
constructs and sending webs that way, otherwise i want a contacting strike, and a more maybe organized or natural grid
system for the tunnels all around".

1. **Legs never collide.** No leg segment may cross another leg or the body on any frame. Add a per-frame numeric check
   (segment-to-segment distance against the leg thickness, like the 842 shield/arm check) to
   `tools/trials/spider_anim_tests.py`, then fix the gait: wider foot rest positions per leg pair, swing arcs that
   lift outward, and the A1 column spiral where the legs bunch.
2. **The burrow dive is a quick animated dig** (A2): a fast dig-in, legs scrabbling and dirt flying, instead of the
   slow glide with frozen tucked legs. The pop-up out of the far hole stays.
3. **The real spider's strike makes contact** (A3): R2's spike must hit the player (it stops 1.5 blocks short now:
   `target = B3(PX - 1.5, 5.5, 40)`). A strike that stops short is only right for the yellow construct spider, and
   then it shoots webs at you from range: add that as a C1b take.
4. **Tunnels on a more organized or natural grid all round** (`burrow_web()` in `tools/trials/spider_sequence.py`):
   now 5 dens + 35 tunnels in a star; J wants it to read as a planned network (or a natural one) round the whole lair.

Not open, but don't lose: none of the datapacks has been run in game; ceiling and wall climbing stays ON HOLD
(Stormie's Spiders decision); game hand-offs: J said "Not yet" (coordinator 3), so the lair brief stays a brief.

The Titan: shelved ("forget the titan,"). The grizzly, Yellow Lantern enderman and blue great white models (round 4)
are kept; the red Grasp is noted for the nether fortress redesign.

## Where everything is

| What | Where |
|---|---|
| Brief for the mc chat | `docs/handoff/2026-10-19-spider-lair/README.md` |
| Design history, rounds 1-7, J's quotes | `docs/plans/trials/2026-10-19-spider-boss-sequence.md`; cave sizes `2026-10-19-spider-cave-size.md`; Titan `2026-10-19-titan-bosses-pitch.md` |
| Pages | spider sequence https://claude.ai/artifact/Li4BpncsnWgGpg86XC4EBL (v7, all videos); cave sizes https://claude.ai/artifact/ALyPbB365wv42KA6qN25vn; Titan bosses https://claude.ai/artifact/3bCtijyZohEWHMqp1WHn9d (rounds 2-4) |
| Generators | `tools/trials/spider_cave.py` (rounds 1-2 domes), `spider_cave_wild.py` (natural caves, `W` = W1-W3), `spider_sequence.py` (`--stack [--short]` = the current lair; `--collapse`, default trap layout = older rounds) |
| Blender builders | `spider_sequence_blend.py` (`--animate` renders the fall videos), `spider_anim_tests.py` (`--video`), `spider_takes_blend.py` (`--round2`), `trial_blender_kit.py` (materials, voxel_mesh, spiders, construct spiders), `titan_bosses_blend.py`, `titan_killer_blend.py`, `titan_killer2_blend.py` |
| Current lair | `LanternLive\trials\spider_stack.blend`: cameras 01 overview cutaway ... 09 burrow web x-ray, 10 fall pov (animated), 11 fall side (animated); frames 1-170. Data `trials\spider_stack\sequence.npz` (and `spider_stack_short\`). Videos `trials\renders_stack\10_fall_pov.mp4`, `11_fall_side.mp4` |
| R2 animation tests | `LanternLive\trials\spider_anims.blend`: cameras 01 A1 walk test (frames 1-220), 02 A2 burrow pop-up (1-150), 03 A3 spike strike (1-90); videos `trials\renders_anim\` |
| Spider takes | `trials\spider_takes_r2.blend` (01 R2, 02 C1a, 03 C1b, 04 C2a), `trials\spider_takes.blend` (R1-R3, C1-C3, T1-T3) |
| Test datapacks (not run) | `test-instances\stormies-spiders\lantern-spider-stack-datapack.zip`, `...-stack-short-datapack.zip` (`/function lantern_seq:build`), older `lantern-spider-cave*-datapack.zip` |
| Titan models | `trials\titan_killer2.blend` (G1 grizzly, E1 Lantern Enderman, S1 blue great white), `titan_bosses_r2.blend`, `titan_killer.blend` |

Rebuild the current lair: `python tools/trials/spider_sequence.py ../trials/spider_stack --stack`, then
`blender -b --python tools/trials/spider_sequence_blend.py -- trials/spider_stack trials/spider_stack.blend [--animate]`
from `LanternLive`.

## Files (stray or superseded on J's PC)

Superseded, can go to `_to_delete\`: `trials\spider_cave_round1\`, `trials\spider_cave\` + `spider_cave_D1-D3.blend`,
`trials\spider_cave_wild\` + `spider_cave_wild_V1-V6.blend`, `trials\spider_sequence\` + `spider_sequence_blockout.blend`,
`trials\spider_collapse\` + `spider_collapse.blend`, `trials\renders_sequence\`, `trials\renders_collapse\`,
`trials\renders\`, `trials\renders_wild\`, `trials\renders_takes\`, and in `test-instances\stormies-spiders\` the
`lantern-spider-cave-datapack.zip`, `-cave-wild-`, `-cave-big-`, `-sequence-`, `-collapse-` zips. Keep `spider_cave_wild4\`
(the W1 lair source) and everything listed above.

## Lessons for the design skill

- **Caves are much bigger than first guesses.** "all too small, caves in the newest updates are way bigger than this":
  arenas for big creatures start at 200+ blocks across; tie them to real heights against biome surfaces.
- **Every generated place is new each time.** "I always need it in a differently generated (if it has to be limited
  multiple we can pick from a few designs of them)": build generators from the seed, not fixed layouts.
- **Hidden, deep, one way in.** "naturally no sign of the hollow dome ... plenty deep with dense overhead": a crack at
  the surface, a winding shaft, thick rock overhead.
- **A boss sequence is a set-piece chain** (J's own design): construct form, a trap that destroys the floor, a fall,
  then the real creature. Falls end in water ("water in some way always in the center").
- **Fights need inputs, not just health bars.** "click 3 times then one right click rapidly to trigger the ejection".
- **Legs must never collide; contact must be real.** Strikes hit unless they're ranged construct attacks.
- **Construct glow at or under emission 1.5** or the yellow washes to white (confirmed again on the construct spiders).
- **Concept rounds: J judges renders, not drawings,** and he will hand you his own creature ideas when the pitches
  miss ("lets get a grizzly bear ..."): ask for the direction after a miss instead of pitching blind again.

## Gotchas

- **Git Bash heredocs mangle Python** with `\\n` or nested quotes ("unexpected EOF"): write patch scripts with the
  Write tool and run them; write text files with `encoding="utf-8"` (cp1252 broke a `·`).
- **`\t` in Markdown paths**: Python strings like `"LanternLive\trials"` turn into tabs; check with `grep -c $'\t'`.
- **Blender 5.2:** `sc.cycles.use_preview_denoising` (not `preview_denoising`); video needs
  `image_settings.media_type = "VIDEO"` before FFMPEG; relative render paths go nowhere, use absolute paths.
- **Parenting in scripts:** set `child.parent = root` without `matrix_parent_inverse`, or parts land at the origin.
- **Big voxel meshes:** weld (`remove_doubles`) then `dissolve_limit(delimit={"MATERIAL"})`; that took a 54 MB .blend to 5.5 MB.
- **numpy shapes:** room masks built from broadcast axes are (1, Y, Z); wrap with `np.broadcast_to(..., (X, Y, Z)).copy()`
  before in-place `&=`.
- **Datapacks:** fill is capped at 32,768 blocks (split slabs in x too); force-load tiles at 200 blocks (256-chunk cap);
  a function chain caps at 65,536 commands, so split into scheduled parts that run `execute at` a marker.
- **Floor finding with stacked caves:** "lowest air in the column" finds the cave below; restrict by y.
