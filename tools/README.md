# Texture tools

Python 3 + Pillow scripts that drew this mod's textures. Rerun them to tweak colours or sizes.

| Script | Makes | Usage |
| --- | --- | --- |
| `construct_textures.py` | Hard-light centre and rim (Dome, Bridge) and Wall brick at any size | `python tools/construct_textures.py 32 out/` then copy `out/*.png` and `out/*.png.mcmeta` to `src/main/resources/assets/lanternring/textures/block/` (and `shockwave_glass.png` to `textures/entity/`) (or a `resourcepacks/constructs_<n>px` pack) |
| `fx_and_ring_textures.py` | Particle sprites and the 3D ring's materials (gold, band, gem, glow) | `python tools/fx_and_ring_textures.py src/main/resources/assets/lanternring` |
| `ring_item_textures.py` | The ring's inventory icon (based on the reference art) | `python tools/ring_item_textures.py <assets_dir> preview.png`. It writes into a `lantern_ring` layout from an early draft; copy `textures/item/power_ring.png` and `icon.png` into `assets/lanternring/` by hand. |
| `contact_sheet.py` | A grid of screenshots for side-by-side comparison | `python tools/contact_sheet.py build/run/clientGameTest/screenshots sheet.png 3 [x0,y0,x1,y1]` |
| `blockbench_models.py` | The lantern held in hand and the Blockbench rings, as Blockbench `.bbmodel` files plus their textures | `python tools/blockbench_models.py src/main/resources/assets/lanternring` (overwrites any edits made in Blockbench) |
| `lasso_assets.py` | The Lasso bubble (cracked jade) and rope textures, and its looping hum (needs numpy and ffmpeg) | `python tools/lasso_assets.py src/main/resources/assets/lanternring` |
| `charge_glow_texture.py` | The green swirl around the hand while the Beam charges | `python tools/charge_glow_texture.py src/main/resources/assets/lanternring` |
| `bbmodel_json.py` | Plain JSON models from the `.bbmodel` files, so the inventory icon, third person, dropped items, item frames and the placed lantern match the Blockbench models | `python tools/bbmodel_json.py src/main/resources/assets/lanternring` (run again after editing a `.bbmodel`) |
| `portal_golem_assets.py` | The Portal's swirl texture and the Loot Golem's Blockbench models | `python tools/portal_golem_assets.py src/main/resources/assets/lanternring` |
| `lantern_glare_textures.py` | The dark vignette and the glare drawn on screen while charging at a lantern | `python tools/lantern_glare_textures.py src/main/resources/assets/lanternring` |
| `lantern_port_assets.py` | The small round socket the ring docks into on the Stone and Compact lanterns (model, trims and corps textures) | `python tools/lantern_port_assets.py src/main/resources/assets/lanternring` |
| `corps_textures.py` | Another Lantern Corps' copies of the construct, lantern and ring textures and models (only the green pixels change colour) | `python tools/corps_textures.py src/main/resources/assets/lanternring red` (rerun after changing a green texture) |
| `add_corps.py` | Adds a corps to the shared blockstates, item models and particles, copied from the red entries (run after corps_textures.py) | `python tools/add_corps.py src/main/resources/assets/lanternring violet` |
| `optimize_textures.py` | Shrinks every PNG (pngquant at quality 90-100, then lossless oxipng) so the jar stays small; run it after any script above | `python tools/optimize_textures.py src/main/resources/assets/lanternring/textures` (needs `apt-get install pngquant` and `pip install pyoxipng`) |
