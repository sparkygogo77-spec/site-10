# Nebula light wrapped in our construct strips (Blender pass 430)

J (2026-10-14 03:24), on the lean takes N1-N4: "Throw it to blender and let it wrap our textures
around the light source."

**What it is.** The light source inside the Nebula is now a shape with the corps' own construct
look strip wrapped round it. The strip is the same `construct_ripples_<strip>` its constructs use,
so there is one strip per corps and no copies.

**Cost.** The light needs no texture of its own. It samples the strip from the block atlas, which
already animates it. That frees the old light textures, about 1.5 MB:
- `textures/entity/bb/nebula_light_f*.png`, 0.77 MB;
- `textures/block/nebula_light*`, 0.72 MB.

**How it wraps.** The strip's square frame goes once round the shape, so its own seamless tiling
closes the wrap and there is no seam. Down the shape the texels are square at the widest ring.
The strip animates at its own speed (frametime 4-5), and the light keeps today's slow turn, so it
glides one way and is never static or fast.

## Takes (J picks the shape)

| Take | Look | Panels |
|---|---|---|
| **L1 Column** | Today's light column, wrapped in the strip | 24 |
| **L2 Orb** | A ball of light in the middle band; the ends of the glass stay dark | 240 |
| **L3 Crystal** | An eight-sided crystal with pointed ends | 40 |
| **L4 Core & cage** | A thin core inside a barred sleeve, both wrapped; the bars turn over the core | 28 |

Corps strips shown are each corps' Ring Lab default:
- green W1 neon
- blue B1
- red R1
- yellow Y1
- violet V1

Orange has no construct look yet, so it keeps its current light until one is picked.

## Where to look

- `renders/takes.png` and `renders/takes.gif`: the four shapes in green, turning.
- `renders/closeups.png` and `renders/L*.png`: each shape close up.
- `renders/corps_<take>.png`: each shape in all five corps.
- `renders/green_looks.png`: L1 in every green look, in this order:
  - W1 neon, H1 neon, HW emerald;
  - X5 emerald, X5 neon, X3 emerald, X1 emerald;
  - X3 D1 emerald.

  The light follows whichever look J picks for constructs.
- **In Blender:** open `blender/nebula_strip_light.blend` (textures relative, in `blender/textures/`).
  - Cameras: "Cam takes", "Cam L1" to "Cam L4", "Cam corps L1" to "Cam corps L4", and "Cam green looks".
  - Space plays 24 frames.

**Preview settings.** The previews thin the lean N1 glass to 55% so the light shows. The env var
`GLASS_ALPHA=1` gives the glass as shipped. Which glass goes on it is the game thread's call.

## Wiring it in (game thread)

**The shapes.** `tools/nebula_light_profiles.json` holds the four profiles:
- each part is `[y, radius]` pairs, top to bottom, in nebula_lantern.bbmodel px, turned round x = z = 0;
- each part has `segments` quads round the axis; `every: 2` draws every other one (the cage);
- **u** = `1 - k/segments` at angle `360*k/segments`, measured from north toward east (+X), so
  it runs left to right seen from outside;
- **v** = arc length down the profile / (2π × the widest radius);
- u and v are fractions of ONE frame, which is the atlas sprite's `u0..u1` and `v0..v1`.

**Held lantern** (`LanternFirstPerson`, the `look == NEBULA` branch):
1. Replace the `nebula_light` BbModel with these quads. BbModel reads box UV only, so it can't do
   this wrap; draw the quads directly.
2. Map UVs with `sprite.getU(u)` and `sprite.getV(v)`. The sprite is the corps' strip on the block
   atlas, the same strip `ConstructLooks.strip()` gives a LIGHT_CONSTRUCT of that corps. Green
   with the R2 K1 look (no strip) falls back to `w1_neon`.
3. Keep today's slow `rotateDegrees(Axis.YP, now * 1.2f)` and the breath and charge glow, at full-bright light.
4. Strips have see-through texels. The Blender preview fills them with the strip's own darkest tone,
   so the light reads solid. Either draw the same quads first in that dark tone, or draw the strip
   with alpha forced to 255.

**Placed block:**
1. `python tools/nebula_light_block.py OUT` writes `nebula_light_<take>.bbmodel` for each take.
   - The panels are thin, tilted and turned, with per-face UVs in 16ths of one frame.
   - The cubes are named `glow_light...`, so the block draws them full-bright.
   - It prints how close each panel is to the true shape: L1 and L4 exact, L2 within 0.08 px, L3 within 0.33 px.
   - The same files are already in `bbmodel/`.
2. Copy the pick to `src/main/resources/assets/lanternring/bbmodel/`.
3. In `tools/bbmodel_json.py`, load it in place of `nebula_light`, and set each corps model's
   `"l"` texture to `lanternring:block/construct_ripples_<that corps' strip>`.
4. **Two unchecked points:**
   - The tilted panels (L2, L3) rely on 26.x free element angles applying X then Y, as the
     converter already assumes. L1 and L4 only turn about Y.
   - A placed block's model is fixed, so it shows the corps' default strip. Following a Ring Lab
     change live would need a sprite swap like `ConstructLooks` does.

**Delete once it's in:**
- `textures/entity/bb/nebula_light_f*.png`;
- `textures/block/nebula_light*.png` and their `.mcmeta` files;
- `bbmodel/nebula_light.bbmodel`;
- the `nebula_light` painter in `tools/blockbench_models.py`.

**To regenerate:**
1. Edit `tools/nebula_light_profiles.json`.
2. Run `python tools/nebula_light_block.py OUT`.
3. Run `/opt/bl/venv/bin/python tools/blender_edits/nebula_strip_light.py <assets> <glass take assets> OUT`.
   Add `GIF=1` for the GIF frames.

**Not checked in game yet:** how it looks under Complementary.
