# Giant spider cave: size study (2026-10-19)

J, after the room-boss pitch ("These are awful"): "first lets start with a large generated cave meant for a very
large spider to have enough space to move quickly within, with burrows around the edge giving it tunnels to escape
through and pop back up through another hole in the cave as a defense mechanism, we will work on getting the size
down before animations and modeling".

The titan boss pitch (`2026-10-19-titan-bosses-pitch.md`) is dropped. This is the size step only: no spider model,
no animation.

## What's generated

`tools/trials/spider_cave.py` makes the cave as a block grid. `tools/trials/spider_cave_blend.py` builds the Blender
file from that grid. The same grid also becomes a datapack, so the Blender view and the in-game cave match block for
block.

- **Chamber:** a wide, low dome with a wobbly wall and a nearly flat floor (room to sprint), plus a few rock pillars
  for cover.
- **Burrows:** holes round the edge, alternating floor pits (at 80% of the radius) and wall-base holes. Each one slopes
  down to a **ring tunnel** that loops under the edge of the floor, so the spider can dive into any hole and come up
  out of another.
- **Cut-throughs:** two tunnels cross under the middle of the floor, so it can also escape straight across.
- **Entrance:** one 3-wide, 4-high passage on the west side for the player.

## Takes

| Take | Spider leg span | Across | Dome | Burrows (width) | Ring tunnel | Crossing at 8 blocks/s | Ring lap |
|---|---|---|---|---|---|---|---|
| C1 | 10 | 44 | 18 | 6 (5 wide) | 166 long, 9 under the floor | 5.5 s | 20.8 s |
| C2 | 14 | 64 | 24 | 8 (6 wide) | 234 long, 11 under | 8.0 s | 29.4 s |
| C3 | 20 | 88 | 32 | 10 (8 wide) | 321 long, 14 under | 11.0 s | 40.2 s |

For scale: the Brood Matron was pitched at a 7-block leg span, and the Warren's Brood Heart at 30 across and 20 high.

## Files

- Blender: `LanternLive\trials\spider_cave_C1-C3.blend`. Cameras `01 C1 cutaway` to `06 C3 inside` (odd numbers are
  cut in half to show the tunnels, even numbers stand at the entrance at eye height). Each take has a spider
  stand-in on the floor, one climbing out of the burrow nearest the camera, and a 1.8-block player.
- Maps: `LanternLive\trials\spider_cave\C1_map.png` to `C3_map.png` (floor, holes, tunnels, spider and player to scale).
- Datapack: `LanternLive\test-instances\stormies-spiders\lantern-spider-cave-datapack.zip`. In a flat creative world:
  `/function lantern_cave:c1` (or `c2`, `c3`) builds the cave in a deepslate box just east of you and puts you on a
  ledge at its entrance with night vision. `/function lantern_cave:clear_c1` (etc.) removes it; run it where you
  built. C3 is 131 blocks wide, so use a render distance of 10 chunks or more, or part of it won't build. Not run in
  game yet.

## Waiting on J

Which size feels right (C1, C2, C3, or between), and whether the burrows are the right number and width.
