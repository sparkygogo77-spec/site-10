# Hand-off from the Blender thread: construct textures + the G3 R4 lantern (2026-10-13)

J's picks, ready for the coordinator to put in the jar. The Blender thread only makes models, textures and
animation, so the game work is yours. Everything is on branch `claude/lantern-redesign-pass2`, in this folder.

## 1. Construct textures (`textures/`, `textures_32px/`)

J's picks from Blender round 4 (`texture_round4.blend`): "put these in the game".

**Format of each strip**
- 256 px wide (4 × 4 blocks at 64 px a block), with 24 frames stacked vertically.
- Quantized to 256 colours and run through oxipng.
- Its `.mcmeta` sets `interpolate: true` and the frametime J asked me to pick ("make the speed what you think is optimal"):
  - frametime 4 = a 4.8 s loop;
  - H2 uses frametime 5.
- Every strip passed the seam, loop and motion tests.

**How to use them.** Treat a strip as a full-face LAYER sprite, like `construct_ripples_*` (`FlowConstructModel` slices it by world position).

**Jar size**
- The 12 strips are 6.6 MB at 64 px per block, and the jar is around 29.5 MB against a 30 MB limit.
- `textures_32px/` has the same strips at 32 px per block: 3.1 MB for all 12, and they look the same at normal distance.
- Use the 32 px set unless something else gets cut.

| File (construct_…) | Use | J said |
|---|---|---|
| `br1_neon`, `br1_lime`, `br1_emerald`, `br1_jade` | Green Wall bricks (glowing mortar, bevelled lips, a glint). Pick one as the default; the others could be Ring Lab options | "BR1 is good", "great" |
| `h1_neon` | Green constructs, hex | "looks good, smooth" |
| `w1_neon`, `w1_emerald` | Green constructs, woven light | his picks. **W1 neon from afar is how he wants every construct face to look**: dark, rich, translucent |
| `br1_blue`, `h1_blue` | Blue Lantern constructs (Wall, others) | "change the hue to a blue" |
| `brd_neon` | Bricks with sparks rising through (an option) | shown |
| `hw_emerald` | Hex woven with W1 (an option) | shown |
| `h2_neon` | Hex cells breathing one by one (an option) | shown |

Already in the code on this branch, and still needing a jar:
- R2 K1 is the default green construct look, and also the bull and army skin.
- Bricks are back for Walls.
- The Dread Runner is slower.

From the earlier picks brief (`docs/findings/2026-10-13-construct-texture-picks.md`):
- the dissolve fill for constructs disappearing;
- G2 negative and N3 scales for Yellow.

**Still in Blender, not picked yet:** round 5 (`tools/construct_designs5.py`, `texture_round5.blend`), ten "elaborate flow" designs in W1 neon's dark, translucent far look. I'll pass on J's picks.

## 2. The G3 R4 lantern charge (`lantern/`)

J: "G3 R4 easily".

What's in `lantern/`:
- `reference_frames/` and `g3_r4_contact.jpg`: 12 frames across the whole cycle.
- `lantern_light_library.blend`: the lantern, its materials, the charge controller and the lights, marked as Blender assets.
- Blender updates `69_g3`, `71_g3b`, `73`–`75` (in `docs/blender/blender_updates/`): the exact node recipes.
- Models are in `models/`:
  - `dark5_l1.npz`: the Dark Lantern L1, already in game.
  - `ring_sq.npz`: the square ring, already the default.

### Timeline (game ticks at 20/s; Blender at 24 fps)

| Moment | What happens |
|---|---|
| 0–2.5 s | The ring flies in, turns to face the port, and **pushes physically into the port** (seats about 2 px deep). |
| at the seat | **The lantern lights at once**: a soft glow in its own greens spreads out from the port over about 3 s. |
| 0–12 s of charge | Charge eases 0 → 100% (smoothstep). This matches the 12 s target; the game's `charge_time` is currently 6 s, so J's call. |
| next 2 s | Overcharge climax to 140%. |
| hold 1.3 s | Then the **let-go flash**: a pulse on the core, about 0.7 s wide. |
| next 7.5 s | A slow fade to dark ("the colour coming undone": J loves it). |
| end | The ring pulls back out. |

### What the light does (match these in the baked glow frames)

- **Centre:**
  - A spinning ball at the bulge behind the port, flaring with noise.
  - Spin speed is 0.5 + 4.5 × charge radians/s, and it **only ever turns one way**: drive it from accumulated time, not from charge.
  - Strands stay in a middle band of about ±(2.2 + 1.8 × charge) px.
  - The ball grows in brightness, not reach.
- **Colour:**
  - Yellow is mixed into the green flow, and the hottest whites of the flare burn yellow.
  - At the climax it is a **very bright saturated green, never white**.
- **Ends:** the glass fades to near-black emerald at the very top and bottom (exp falloff, about 4.4 + 1.6 × charge px).
- **Gold cracks:**
  - The light runs through them first as one gold flash, then they hold a **dim** gold.
  - They read mostly as dark lines and never get bright.
  - They fill from the centre outwards and reach the edges at about 85% charge.
  - They fade toward the ends like the glass, and the green swallows them from about 95% charge.
- **Stitches:** very frequent dark dashes (darkest green) down the middle of the front (not across the port) and down each side.
- **Gold frame (R4):**
  - Polished gold that reflects the lantern's green, plus a soft green glow only on gold faces turned toward the glass (collar undersides, the edges of the middle band).
  - Green light pools along both sides; the handle stays unlit.
  - In game: no emissive gold. Give the frame a LabPBR specular map (metal) so Complementary reflects the green.
- **Twist:** the pinched glass has a 3° helix, top to bottom. This is a model change: re-run the lantern generator with the twist, voxel-snapped.
- **Light into the ring:** subtle and smooth; the lantern's brightness is the star.

### In game

- The current Dark Lantern glow is `bbmodel/dark_lantern_glow` with 12 baked frames, cross-faded by `LanternFirstPerson`.
- G3 R4 needs re-baked glow frames with the look above:
  - about 16 frames across the charge;
  - plus the climax and let-go flash.
- Plus the ring docking into the port during the charge animation.
