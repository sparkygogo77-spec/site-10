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
| D4 Quarter-block textured (rev 2) | D2's ship in the ship textures below | same meshes as D2 | 16-20 |
| D5 Overlay textured | D3's ship in the ship textures below | same meshes as D3 | 21-25 |

Each take's five cameras, in order: `- bow quarter`, `- off the bow`, `- boat deck` (standing on the deck, a 2-block
player in view), `- funnels`, `- stern`. Example: `9 D2 Quarter-block - funnels`.

**The detail (all four):** deck railings with posts, mast stays and shrouds, the two-wire aerial between the masts, four
stays and a steam pipe on each funnel, a davit pair on every lifeboat, six cargo cranes, the docking bridge across the
poop, 26 ventilators, a skylight dome, bow anchors, a waterline band, a thin yellow sheer line, lit portholes (3 rows)
and cabin windows (3 rows), bridge windows.

## Rev 2 (J's notes on D4, 2026-11-09)

"the bricks dont fit on the hull for D4 or the hexagons anywhere really but the cross hatched pattern looks good up
close but further away you can see the pattern form so maybe we enlarge the texture ... only marginally larger can i
have a slider" / "the color contrasting choice of green looks good on D3 especially for the hull being darker" / "D2
quarter block might be a must i want to try D3 as well" / then: "now the hull looks too dark and your new textures are
copies of mine but not as good".

- **Hull:** bricks and hex are gone. Three new platings drawn for the ship (`tools/titanic_textures.py`,
  `docs/texture_library/green/hp1..hp3/`): HP1 riveted strakes, HP2 inlaid armour panels, HP3 flow plating.
- **Decks and cabins:** his own W1 weave, untouched, 1.25x bigger. The "polished" copies of BR1 / W1 / H1 from rev 1
  are deleted from the repo.
- **Funnels, tips, rails, stripes:** D3's plain greens.
- **Sliders** (Properties editor > Scene tab > Custom Properties):

| Slider | Default | What it does |
|---|---|---|
| hull_texture | 1 | 1 HP1 riveted strakes, 2 HP2 inlaid armour panels, 3 HP3 flow plating |
| hull_texture_size | 1.0 | 1 = 32 px a block; 2 = twice as big |
| deck_texture_size | 1.25 | the weave's size |
| hull_brightness | 2.4 | 2.4 matches D3's hull; lower is darker |
| deck_brightness | 1.0 | the weave's brightness |
| texture_strength | 1.0 | 0 = D3's plain greens, 1 = full texture |

| New plating | Loop jump vs a normal step | Tile seam vs worst inner row |
|---|---|---|
| HP1 | 0.25 vs 0.25 | x 2.3 vs 3.6, y 17.2 vs 25.8 |
| HP2 | 0.26 vs 0.25 | x 0.0 vs 10.7, y 0.0 vs 22.3 |
| HP3 | 1.01 vs 1.02 | x 0.3 vs 0.3, y 13.7 vs 17.4 |

The files `construct_br1_green_ship.png`, `construct_w1_green_ship.png`, `construct_h1_green_ship.png` in
`LanternLive\constructs\titanic_textures\` are no longer used: safe to delete.

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
