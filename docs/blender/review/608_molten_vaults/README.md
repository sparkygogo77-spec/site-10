# Pass 608: molten vault, six variations of 607 D1b (WAITING)

**Script:** `docs/blender/blender_updates/608_molten_vaults.update.py` (runs 607's builder; voxels `tools/pixel_lanterns8.py`)
**Open in Blender:** `C:\Users\Josh\Documents\LanternLive\lanterns\molten_vaults.blend` (Cam all; press play, 120 frames)
**Cameras:** `Cam <code> <name>` for the 6 takes, plus `Cam all`.

J on 607 D1b (Vault: molten): "this one is a keeper, i need more variation". Every take keeps D1b's glass vault between
fluted gold pillars, gold drips from the roof down the panels and off the eaves, the stepped roof, the see-through glass
with the G3-flare core and the sculpted port. Each changes one big thing.

He also found "at a certain angle the lantern is transparent (every single model)". Cause: the material used blended
transparency, which writes no depth, so from some angles Blender drew the far side over the near side. It now uses
dithered transparency: gold is solid from every angle and only the glass is see-through. 607 is rebuilt with the fix (all
takes rev 2).

| Take | What | Boxes |
|---|---|---|
| D1b1 Molten: heavy pour | Twice the drips, thicker; gold pooling on the base steps. | 1,241 |
| D1b2 Molten: hex | Six panels and six pillars, drips between them. | 2,146 |
| D1b3 Molten: tall | Taller, narrower vault, two-tier roof with a spiked crown, longer drips. | 1,024 |
| D1b4 Molten: overflowing bowl | A glowing bowl crown overflows down the roof and off the eaves. | 1,380 |
| D1b5 Molten: caged | Outer cage of gold bars a pixel off the glass, drips caught on the bars, double handle. | 1,143 |
| D1b6 Molten: squat | Lower, broader vault, deep dripping eaves, tall stepped roof, four short feet. | 1,188 |

## For J
Rate each take KEEP / IMPROVE / DROP on the site.
