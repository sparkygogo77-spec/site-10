# Pass 952: the Titanic construct with detail, and J's textures on it

J, 2026-11-09, on 951: "now add detail to the 1 to 1 one"; then "add and correct and polish some of my existing
textures and display it on one of them, rename the files to align with our choices and names for them in here and make
the cameras named accordingly to each option".

**Open:** `C:\Users\Josh\Documents\LanternLive\constructs\952_titanic_detail.blend`, camera
`1 D1 Half-block - bow quarter`, frames 1-110 (forms 1-80 by F2 circles, holds to 110).
**Script:** `docs/blender/blender_updates/952_titanic_detail.update.py`.
**Textures:** `C:\Users\Josh\Documents\LanternLive\constructs\titanic_textures\` (packed into the .blend too).

## Takes (same ship, same size: 269 x 28 x 53 blocks, 63 to the mast tops)

| Take | How the detail is carried | Faces | Cameras |
|---|---|---|---|
| D1 Half-block | whole ship re-cut at 2 voxels a block + the detail | 164,820 | 1-5 |
| D2 Quarter-block | whole ship re-cut at 4 voxels a block + the detail | 638,324 | 6-10 |
| D3 Overlay | 951's 1-block ship unchanged + the detail as a thin quarter-block layer | 34,058 + 96,944 | 11-15 |
| D4 Textured | D1's ship in BR1 bricks (hull), W1 weave (decks, cabins), H1 hex (funnels), polished | 164,820 | 16-20 |

Each take's five cameras, in order: `- bow quarter`, `- off the bow`, `- boat deck` (standing on the deck, a 2-block
player in view), `- funnels`, `- stern`. Example: `9 D2 Quarter-block - funnels`.

**The detail (all four):** deck railings with posts, mast stays and shrouds, the two-wire aerial between the masts, four
stays and a steam pipe on each funnel, a davit pair on every lifeboat, six cargo cranes, the docking bridge across the
poop, 26 ventilators, a skylight dome, bow anchors, a waterline band, a thin yellow sheer line, lit portholes (3 rows)
and cabin windows (3 rows), bridge windows.

## The textures (`tools/titanic_textures.py`; originals untouched)

New files `construct_<tex>_green_ship.png` beside the originals in `docs/texture_library/green/<tex>/`.
What changed: each frame blended with its neighbours (smoother, slower; frametime 4 -> 5), highlights pulled back from
pale mint to saturated green (red <= 0.30 x green, blue <= 0.50 x green), 12% darker.

| Texture | Brightest pixel before -> after | Motion per frame before -> after | Loop jump vs a normal step | Tile seam vs worst inner row |
|---|---|---|---|---|
| BR1 bricks | (131, 227, 165) -> (59, 199, 99) | 3.31 -> 1.61 | 0.81 vs 1.64 | x 27.2 vs 27.7, y 56.0 vs 58.4 |
| W1 weave | (33, 229, 86) -> (29, 201, 75) | 1.73 -> 1.43 | 1.40 vs 1.43 | x 17.1 vs 22.9, y 10.1 vs 20.0 |
| H1 hex | (150, 240, 182) -> (63, 211, 105) | 3.33 -> 2.32 | 0.39 vs 2.40 | x 8.3 vs 13.5, y 0.9 vs 17.3 |

No loop jump is bigger than a normal step, no seam is bigger than the texture's own worst row, and motion is above 0.

## Renamed

| Was | Now |
|---|---|
| `constructs\titanic_construct.blend` | `constructs\951_titanic_forming.blend` |
| `951_titanic_construct.update.py`, review folder `951_titanic_construct/` | `951_titanic_forming...` |
| cameras `Cam F1`, `Cam F1 close`, `Cam F1 side`, `Cam SZ` ... | `1 F1 Seeds - bow quarter`, `2 F1 Seeds - off the bow`, `3 F1 Seeds - side` ... `16 SZ Sizes - all three` |

The old `constructs\titanic_construct.blend` is still in LanternLive (this chat can't move files there): safe to delete.

## For the game (not built yet)

- D3 is the cheapest: the 1-block ship as now + one extra thin mesh. D2 is 19 times the faces of the 1-block ship.
- D4's texture rule: 32 px a block fixed in the world, one tile = 4 blocks, hull = BR1, decks and cabins = W1, funnels = H1.
