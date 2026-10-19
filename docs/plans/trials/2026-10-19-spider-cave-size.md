# Giant spider cave: size study (2026-10-19)

J, after the room-boss pitch ("These are awful"): "first lets start with a large generated cave meant for a very
large spider to have enough space to move quickly within, with burrows around the edge giving it tunnels to escape
through and pop back up through another hole in the cave as a defense mechanism, we will work on getting the size
down before animations and modeling".

The titan boss pitch (`2026-10-19-titan-bosses-pitch.md`) is dropped. This is the size step only: no spider model,
no animation.

## Round 3 (current): wild caves V1-V6 at real heights

J on round 2: "give me the y coordinates of the average biome surface block, then where the dome would be placed in
accordance to all of them, while being stretched to the realistic width of an expansive modern cave in minecraft java
versions that naturally spawn, animations and use its legs to traverse angles at very low and steep degrees and around
corners and round columns and smooth and swiftly, I always need it in a differently generated (if it has to be limited
multiple we can pick from a few designs of them".

### Surface heights (Java 1.18+ terrain, sea level 63)

Typical ranges from how the generator shapes each biome, not measured in a world yet. Check against a real seed
before they become spawn rules.

| Biome group | Usual surface y | Middle |
|---|---|---|
| Deep ocean floor | 22 to 38 | 30 |
| Ocean floor | 38 to 52 | 45 |
| River bed | 54 to 60 | 57 |
| Swamp, mangrove, beach | 61 to 66 | 63 |
| Mushroom fields | 63 to 72 | 66 |
| Plains, snowy plains | 63 to 78 | 68 |
| Desert | 63 to 82 | 70 |
| Forest, birch, dark forest | 63 to 90 | 72 |
| Taiga, jungle, savanna | 63 to 95 | 74 |
| Badlands | 65 to 100 | 78 |
| Wooded badlands, savanna plateau | 90 to 130 | 105 |
| Windswept hills | 90 to 150 | 112 |
| Meadow, cherry grove | 90 to 150 | 115 |
| Grove, snowy slopes | 110 to 190 | 145 |
| Stony, jagged, frozen peaks | 130 to 260 | 185 |

Most land sits between y 63 and 80 (middle about 70).

### Where the cave goes

- **Floor about y -24, roof y +18 to +30.** The upper part is stone, the lower part deepslate (the change is at y 0-8).
- **Tunnels and dens bottom out at y -51**, just above the lava level (caves below y -54 fill with lava).
- **Rock overhead:** about 40 blocks under plains and forests (surface ~68), 30 under river beds, 80-90 under
  plateaus and hills, 150+ under peaks.
- **Don't place it under oceans** (ocean floor ~45 leaves only ~15-25 blocks of rock, and aquifers flood) **or in
  the deep dark** (it uses the same depth). Spawn rule to give the mc chat: land surface at y 60 or higher, not deep
  dark, not ocean or river.

### Shape

Big 1.18+ noise caves ("cheese caves") are commonly about 60-150 blocks across their long side and 20-60 high, with
rare bigger ones (estimate, not measured). The cave is now a long, irregular cavern of that kind, built from 3D noise:
- **side lobes** (2-3 smaller chambers bulging off the main one) make corners to go round;
- **round columns** (4-7, hourglass-shaped, 5-11 blocks thick) to circle and climb;
- **slopes of every steepness:** the floor leans across the cave (gentle ramps), noise adds mounds and banks, and
  the walls curve from shallow to vertical to overhanging into the roof. That's the terrain the spider's legs have to
  handle; the leg animation itself comes after the size is settled.
- Same burrow system as round 2: 5 wide holes (11 blocks), dens, a ring tunnel following the outline, one
  cut-through, and the entrance shaft winding down from a crack at the surface.

### Different every time

`tools/trials/spider_cave_wild.py` makes a new cave from any seed. Six are built now so J can see the variety:

| Seed | Size (long × wide) | Height | Columns | Lobes | Drop from roof hole | Tunnels down to |
|---|---|---|---|---|---|---|
| V1 | 154 × 107 | y -28 to 18 | 5 | 3 | 34 | -51 |
| V2 | 153 × 93 | y -28 to 26 | 6 | 3 | 43 | -51 |
| V3 | 151 × 84 | y -24 to 24 | 5 | 2 | 43 | -51 |
| V4 | 193 × 87 | y -28 to 30 | 5 | 2 | 46 | -51 |
| V5 | 163 × 112 | y -25 to 23 | 7 | 3 | 36 | -51 |
| V6 | 141 × 100 | y -24 to 18 | 4 | 2 | 35 | -51 |

In game there are two ways to keep it different:
1. **★ Generate it in the mod from the world seed** (port this recipe to a feature): every cave is new, no fixed
   designs. mc chat work.
2. **A few fixed designs** (the six seeds above as saved structures), picked at random. Less work, and they repeat.

Datapack for testing now: `LanternLive\test-instances\stormies-spiders\lantern-spider-cave-wild-datapack.zip`. In a
normal (not flat) creative world, stand on land and run `/function lantern_wild:random` (or `v1` ... `v6`). It turns
water and lava around the cave into tuff, carves the cave under you at its real heights, and puts you next to the
crack. Render distance 8+ chunks. Not run in game yet.

Blender: `LanternLive\trials\spider_cave_wild_V1-V6.blend` (8.5 MB). Cameras `01 V1 cutaway`, `02 V1 inside` ...
`12 V6 inside`. Cutaways show grass at y 72, stone, then deepslate below y 4.

## Round 2: D1, D2, D3 (superseded)

J on round 1 (C1-C3): "Honestly I think we go even bigger, the tunnel should maybe come in from above and the dens
should be larger tunnels too but naturally no sign of the hollow dome that should be plenty deep with dense overhead
to not be easily accessed regardless of rarity". Burrows: "Fewer, wider holes".

What changed:
- **Bigger:** 110 to 150 blocks across (round 1 was 44 to 88).
- **Buried:** 30-34 blocks of solid rock over the top of the dome. The surface shows nothing but a 3-wide crack.
- **Entrance from above:** the crack opens into a shaft that winds down two turns through the rock (3 wide at the top,
  5 wide lower down) and breaks through the dome roof. From there it's a 33-43 block drop to the floor, so you fly or
  fall in.
- **Fewer, wider burrows:** 5-6 holes, 10-12 blocks wide, alternating floor pits and wall-base holes.
- **Dens:** where each burrow meets the ring tunnel there's a den, a pocket about 1.7 times the tunnel width, for the
  spider to sit in. The ring tunnel and the two cut-through tunnels are as wide as the burrows.

| Take | Spider leg span | Across | Dome | Rock on top | Burrows (width) | Drop from the roof hole | Crossing at 8 blocks/s | Ring lap |
|---|---|---|---|---|---|---|---|---|
| D1 | 24 | 110 | 40 | 30 | 5 (10 wide) | 33 | 13.8 s | 50 s |
| D2 | 28 | 130 | 46 | 32 | 5 (11 wide) | 38 | 16.2 s | 59 s |
| D3 | 32 | 150 | 52 | 34 | 6 (12 wide) | 43 | 18.8 s | 67 s |

The whole rock box is 161 × 101 × 161 (D1) to 207 × 123 × 207 (D3) blocks.

## Round 1: C1, C2, C3 (superseded)

44 / 64 / 88 across, domes 18 / 24 / 32 high, 6-10 burrows 5-8 wide, a side entrance at floor level, about 6 blocks
of rock on top. Files kept in `LanternLive\trials\spider_cave_round1\`.

## How it's generated

`tools/trials/spider_cave.py` makes each take as a block grid. `tools/trials/spider_cave_blend.py` builds the Blender
file from the grid, and the same grid becomes a datapack, so Blender and the game match block for block.

- **Chamber:** a wide, low dome with a wobbly wall, a nearly flat floor (room to sprint) and a few rock pillars for
  cover, kept clear of the drop under the entrance.
- **Burrows** slope down to a **ring tunnel** that loops under the edge of the floor, so the spider can dive into any
  hole and come up out of another. Two **cut-through tunnels** cross under the middle.

## Files

- Blender: `LanternLive\trials\spider_cave_D1-D3.blend` (5.5 MB). Cameras `01 D1 cutaway` to `06 D3 drop-in view`:
  odd numbers are cut in half to show the rock, shaft, burrows and tunnels; even numbers look down from the roof hole
  where the shaft breaks in. Each take has a spider stand-in on the floor, one climbing out of a burrow, and a
  1.8-block player on the floor under the shaft.
- Maps: `LanternLive\trials\spider_cave\D1_map.png` to `D3_map.png`.
- Datapack: `LanternLive\test-instances\stormies-spiders\lantern-spider-cave-datapack.zip`. In a flat creative world,
  `/function lantern_cave:d2` (or `d1`, `d3`) builds the rock box around and above you (render distance 8 chunks or
  more) and puts you on top, next to the crack. `/function lantern_cave:clear_d2` removes it. Not run in game yet.

## Waiting on J

Which of V1-V6 feel right, and whether the cave should be generated fresh every time (mod) or picked from a few fixed designs.
