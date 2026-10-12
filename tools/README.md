# Texture tools

Python 3 + Pillow scripts that drew this mod's textures. Rerun them to tweak colours or sizes.

| Script | Makes | Usage |
| --- | --- | --- |
| `construct_textures.py` | Hard-light centre and rim (Dome, Bridge) and Wall brick at any size | `python tools/construct_textures.py 32 out/` then copy `out/*.png` to `src/main/resources/assets/lanternring/textures/block/` (or a `resourcepacks/constructs_<n>px` pack) |
| `fx_and_ring_textures.py` | Particle sprites and the 3D ring's materials (gold, band, gem, glow) | `python tools/fx_and_ring_textures.py src/main/resources/assets/lanternring` |
| `ring_item_textures.py` | The ring's inventory icon (based on the reference art) | `python tools/ring_item_textures.py <assets_dir> preview.png`. It writes into a `lantern_ring` layout from an early draft; copy `textures/item/power_ring.png` and `icon.png` into `assets/lanternring/` by hand. |
| `contact_sheet.py` | A grid of screenshots for side-by-side comparison | `python tools/contact_sheet.py build/run/clientGameTest/screenshots sheet.png 3 [x0,y0,x1,y1]` |
| `blockbench_models.py` | The lantern held in hand and the Blockbench rings, as Blockbench `.bbmodel` files plus their textures | `python tools/blockbench_models.py src/main/resources/assets/lanternring` (overwrites any edits made in Blockbench) |
| `bbmodel_json.py` | Plain JSON models from the `.bbmodel` files, so the inventory icon, third person, dropped items, item frames and the placed lantern match the Blockbench models | `python tools/bbmodel_json.py src/main/resources/assets/lanternring` (run again after editing a `.bbmodel`) |
