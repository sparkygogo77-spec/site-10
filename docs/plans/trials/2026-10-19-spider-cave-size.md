# Giant spider cave: size study (2026-10-19)

J, after the room-boss pitch ("These are awful"): "first lets start with a large generated cave meant for a very
large spider to have enough space to move quickly within, with burrows around the edge giving it tunnels to escape
through and pop back up through another hole in the cave as a defense mechanism, we will work on getting the size
down before animations and modeling".

The titan boss pitch (`2026-10-19-titan-bosses-pitch.md`) is dropped. This is the size step only: no spider model,
no animation.

## Round 2 (current): D1, D2, D3

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

Which size (D1, D2, D3), and how the entrance drop and the dens feel.
