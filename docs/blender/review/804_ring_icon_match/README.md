# Pass 804: a ring that matches the hotbar icon — WAITING

**Script:** `docs/blender/blender_updates/804_ring_icon_match.update.py`
**Open in Blender:** `C:\Users\Josh\Documents\LanternLive\lanterns\ring_icon_match.blend` (Cam row game, press play)
**Files here:** `sheet.png` (check render, frame 90), `icon_r19d_n1.png`, `icon_r19d_n2.png`, `icon_r19d_n3.png`
(16×16), `icons_preview.png` (the three icons at 10×)

J: "why dont i have a ring that looks accurately like the one in my item bar for the face". Two ways to fix it, both here.

## Way 1: the ring matches the icon (Blender)

The icon's head: a square gold frame, emerald panels top and bottom, a black bezel each side with a gold line, and a cut
green gem in the middle (no round stone). Each take builds that head on R19d's band and uses the same light-up as 801
(the gem lights first, then the panels, and it stays bright).

| Take | Gem | Panels |
|---|---|---|
| I1 icon true | octagon, domed, light corner top-left (as in the icon) | X5 ripple emerald |
| I2 square-cut | stepped square: flat table plus 3 steps | X5 ripple emerald |
| I3 emerald-cut | tall cut-corner gem, stepped | W1 neon weave |
| I4 icon frame + R19d | R19d's concentric square, light-cut, inside the icon's frame | H1 neon hex |
| R19d | (unchanged, for comparison) | |

## Way 2: the icon matches R19d (16×16 PNGs)

N1 has a silver rim and band stubs, like today's icon. N2 has a gold rim. N3 is a three-quarter view with the band loop
showing. Each shows R19d's round face with its halo line and the concentric square in core green.

## For J

Pick one take: I1–I4 (the ring changes), or N1–N3 (the icon changes). The pick goes to the mc chat as a
Blockbench model (`tools/ring_voxels_bbmodel.py`) or as the item texture.

## J's verdict (2026-10-15)

"ripple should cover the key, get rid of 12, make 13 extend the ripple to the black sides, no black on the ring, delete
14 and revise design of face on R19d, then give me 7 more rings" - pass 825.
