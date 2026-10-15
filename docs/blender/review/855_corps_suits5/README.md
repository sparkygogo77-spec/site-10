# Pass 855: Suits: C8b purples, circuit blues, hex plate variations (WAITING)

**C8b material:** 827's procedural **carbon weave** (built in Blender's shader, no image file). It is a diagonal stripe
pattern mixed half-and-half with a fine checker, which makes a twill weave like carbon fibre. That weave is coloured
from near-black violet (5% of the corps colour) to dark violet (35%). The surface is glossy (roughness 0.2) with a full
clear coat, and a fine grid of thin glowing violet lines (a brick pattern's mortar lines) runs over it at emission 1.8.
It is 92% opaque. The seams, visor and lights are solid violet glowing at 3, and the undersuit is violet at 7%.
Violet = linear RGB (0.6, 0.1, 1.0).

**Script:** `docs/blender/blender_updates/855_corps_suits5.update.py` (builds on 603 → 827)
**Open in Blender:** `C:\Users\Josh\Documents\LanternLive\suit\corps_suits5.blend`, scene "Corps Suits 5". It starts on
`Cam row P`; press play. The suit-up runs from frame 1 to 34, the ring flares at 35, and the clip runs 1-60.
**Cameras:** `Cam <take>`, `Cam <take> shoulder`, `Cam <take> back` for each take. Rows: `Cam row P` (C8b + purples),
`Cam row T1`, `Cam row T2`, `Cam row R5` (all) and `Cam row R5 back`.

J on 603:
- C8b Crest Knight: "keep this material, tell me what it is then try other purples"
- T1 C8b in circuit: "give me brighter yet also darker blues this is too bright"
- T2 C8b in hex plate: no note, so this pass has 3 new variations

Every take keeps C8b's shape and 603's suit-up. The bright light that reveals the suit is each take's corps colour. This
pass fixes a leftover from 603: the seams, undersuit, emblem and mask still had the mint band. Now every piece's band is
in the corps colour. T1 was too bright in 603 because its trace mask was inverted: the whole plate glowed and the traces
were the dark part. The new circuits have near-black plates and only the thin traces glow.

| Take | What | Colour | How it's built |
|---|---|---|---|
| C8b | C8b (as before), reference | Violet (0.6, 0.1, 1.0) | carbon weave as above |
| C8bP1 | C8b in royal purple | royal purple (0.2, 0, 1.0) | same carbon weave recipe, bluer and deeper than violet |
| C8bP2 | C8b in deep plum | deep plum (0.15, 0, 0.42) | same recipe, the darkest: dim plates, seams at 1.5 |
| C8bP3 | C8b in ultraviolet | ultraviolet (0.06, 0, 1.0) | same recipe, at the blue edge of purple |
| T1a | Circuit: navy + electric blue | electric blue traces on a navy-black plate | offset grid of traces with square pads |
| T1b | Circuit: steel black + cobalt | deep cobalt traces on a blue-black steel plate | two crossed grids at different pitches (dense maze), no pads |
| T1c | Circuit: indigo + azure | azure traces on an indigo-black plate | sparse traces with big ringed pads |
| T2a | Hex: fine honeycomb | red | true hexagons 3 px wide, nearly flat, every gap glows |
| T2b | Hex: big domed tiles | red | 8 px tiles domed in deep relief, dark gaps, a lit hex outline inset in each tile |
| T2c | Hex: twinkling cells | red | 5 px bevelled cells, faint gaps, random cells light up and fade (3 s cycle) |

No purple is pink or white, and every one keeps the blue channel at full or near-full with no green.

**For J:** KEEP / IMPROVE / DROP per take. Which purple for C8b, which blue pair, which hex build.
