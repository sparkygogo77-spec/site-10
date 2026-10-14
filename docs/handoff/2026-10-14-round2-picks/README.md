# J's round-2 picks (2026-10-14), for the coordinator

J: "put all of the good models I like in the game already". Picked in chat on 2026-10-14.

| Item | Pick | What's here |
|---|---|---|
| Hope sanctuary | **A6 battery + cone** (replaces A3) | `hope_sanctuary_A6.json`: the A3 lotus base with a tall hourglass Power Battery on top and an open flyer cone round it (16 ribs, lit rings, landing ring + rail at the top, 11 hoops spiralling up between battery and wall, guide lights, perches): 16,298 blocks. Turbine 348 + 68 mark blocks, moving, y from 22. Same format and axes as the A3 plan; made by `tools/export_sanctuary_plan.py A6` (checked: it reproduces the A3 plan block for block). Picture: `sanctuary_A6.jpg` |
| Blast Drill models | **D1 auger, D2 tiered, D3 crystal, all in construct brick** | `bbmodel/blast_drill_d1/_d2/_d3.bbmodel` + `textures/entity/bb/blast_drill_d*.png`, same frame as `blast_drill.bbmodel`. Ring Lab option Drill model = Classic / D1 / D2 / D3. Lay the corps' `construct_brick` texture on the `glass_hardlight_*` cubes (box-projected, full-bright); keep `glow_*` and `dark_core` as they are. Picture (Blender): `drills_brick.jpg`, column a |
| Green Deluge liquid | **W3 solid light** | `textures/block/hardlight_still.png` / `hardlight_flow.png` (+ mcmeta), written by `tools/hardlight_liquid_textures.py <assets> W3`. Register them in place of vanilla water for `ModFluids.SOURCE/FLOWING` (still, flow, still as overlay), tint unchanged; light 15 sources / 12 flowing; under Iris a glowing ID instead of water. See `../2026-10-14-green-deluge-brighter.md` |
| Red battery handle | **C1 arched runes** (as shipped in the final hand-off) | nothing new; see `../2026-10-13-red-battery-final/` |
