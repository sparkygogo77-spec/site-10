# Hand-off: Dread Warren mineshaft entrances (passes v2.0114 and v2.0115)

For the mc build chat (game code on `main`). J picked this as the next job, 2026-10-20: "the minecraft entrance".
Design chat: Dread Warren look 2 (retired, note `docs/handoff/retired/2026-10-20-dread-warren-look-2.md`).

## What J decided (his words, DECISIONS.md 2026-10-20)

- "it should be natural mineshafts that have the additional portion of ours attached to it, meaning we need a whole
  mine shaft designed fairly high but preferredly in caves as usual under and maybe appearing on the walls of rivines,
  if there is one spider thing, make there be like the same radius of the entire structure of cave structures effected
  by the chance of being an entrance proportional to 200 blocks wide is it?"
- "try to make it look natural, it should be calculated to be as common as a certain rivine is mountain is, it should
  be random though It shouldnt be obvious that whatever it is associated with spawns the tunnel systems for the spider
  one we have for example." (v2.0113 W1a5a)
- On v2.0114 W1a7a, W1a7b, W1a7c: "all three are good, more scenarios like this, perfect utilization of existing
  generations,it will be textured naturally or can you attempt updated themed modern looking shafts even though
  naturally generated modern ones would be perfect, the cave would need texturing". All three KEEP.

## What to build

1. **Worldgen:** a structure piece that attaches to a vanilla mineshaft dead end (mineshafts generate as usual: in
   caves, sometimes cut open on a ravine wall). It only appears on mineshafts within a Dread Warren's own radius
   (about 200 blocks across; the lair cave is about 230 x 160), with a chance per dead end, never on every one.
2. **No tell:** nothing about the mineshaft above (blocks, signs, mobs, light) may reveal that a Warren is below. The
   piece is our section past the dead end: a short drop or crawl into the Warren's first cave.
3. **Blocks:** old dark timber matching vanilla mineshaft wood, then dread stone lining once inside ours. A modern
   themed shaft (v2.0115 take) would need new blocks: build the natural one first, ask J before the modern one.
4. **Webs:** never across the walkway (J: "THE WEBBING ON THE INSIDE SHOULDNTBE HERE"); webs only on walls, and only in
   danger (game rule).

## References

- Takes: `https://lantern-review-j.vercel.app/#report/v2.0114` (W1a7a-c KEEP) and `#report/v2.0115` (5 more scenarios:
  textured mine and ravine, a modern shaft, a dungeon cracked into ours, a dripstone cave; unrated when written).
- Specs: `docs/blender/review/specs/v2.0114.json`, `v2.0115.json`; blends in `LanternLive\trials\dread_warren_r*.blend`.
- The Warren and lair briefs: `docs/handoff/2026-10-19-dread-warren-spiders/`, `docs/handoff/2026-10-19-spider-lair/`
  (J said "Not yet" to building the spiders and the lair; this entrance is the first Warren piece he asked for).
- Before building: `git log origin/main | grep -i "v2.0114"` (not built yet when written). Every player-facing change
  gets a What's New entry and a Ring Lab label "Pass v2.0114 · Warren mineshaft entrance".
