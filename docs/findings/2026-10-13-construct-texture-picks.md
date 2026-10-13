# Construct texture picks: J's choices from the Blender rounds (2026-10-12/13)

From the Blender thread, for the coordinator to put in the jar. I only make the Blender files; the
game work is yours. Everything below is on branch `claude/lantern-redesign-pass2`.

## Already in the code on that branch (needs a jar)

| Change | Where |
|---|---|
| **R2 K1** (dark jade fragments) is the default green construct look | the R1 pack's model now uses `construct_ripples_r2k1` (`resourcepacks/constructs_jade_r1`) |
| R2 K1 is also the skin for the Rage Bull and the army constructs | `ConstructSkins` uses `construct_skin_r2k1.png`; the contrast is now 0.45 + 0.55·crack |
| **Bricks are back** for green Walls (J: "bring back my bricks") | the jade packs no longer swap `construct_brick` |
| Dread Runner is slower (9 s run, was 5 s) with a smooth 0.7 s stride | `RingTuning` dread_run; `DreadRunnerRenderer` uses Catmull-Rom between the rig frames |

## J's picks to implement

All of these come from `tools/construct_designs4.py`. Run `python tools/construct_designs4.py OUT`.

- **Strip format.** Each texture comes out as `face_<design>_<palette>.png`. It is a 256 px wide strip covering 4×4 blocks at 64 px per block. It holds 24 or 32 frames stacked vertically. Every strip tiles and loops cleanly (checks in `tests.json`; all 33 pass).
- **How to use it in game.** Use the strip like `construct_ripples_*`, as a full-face LAYER sprite that `FlowConstructModel` slices by world position. Give it a `.mcmeta` with `"interpolate": true` and the frametime listed below.
- **Speed.** J wants the motion smooth and slow ("they don't have to be so animated"). So the frametimes are 4–5, where the old ones were 2–3.

| Use | Strip(s) | Frametime | J said |
|---|---|---|---|
| Green Wall bricks | `face_BR1_jade` (also `_emerald`, `_lime`, `_neon`, `_forest`) | 4 | "BR1 is good", "BR1 lime looks great, and emerald and jade and neon" |
| Green constructs | `face_H1_neon` | 4 | "H1 neon looks good" (smooth) |
| Green constructs | `face_D1_neon`, `face_W1_emerald`, `face_W1_neon` | 4 | his picks |
| Blue Lantern constructs | `face_BR1_blue`, `face_H1_blue` | 4 | "change the hue to a blue" |
| Yellow Lantern constructs | `face_G2Ng_yellow` (G2 negative: dark lines, brights turned dark), `face_N3_yellow` (scales); `_amber` versions too | 4 | "G2N might be a good yellow lantern design", "N3 is good for yellow too" |
| **Construct going away** | the round-3 "fill3" dissolve: `tools/construct_designs3.py`, `apply_fill(..., "fill3", t)` | — | "the dissolving is great for when the construct goes away" |

- **The dissolve.** It hides the pattern pixel by pixel in random order and leaves a bright sparkling front. In game this fits `Dismissal`: run the dissolve over the dismiss time instead of looping it. The mask is `DISS` and the front is `exp(-((DISS - level)/0.012)^2)`, with `level` going 1 → 0 over the dismissal.
- **Still with J in Blender** (don't implement yet):
  - G2 and O1 gliding versions (`G2g`, `G2s`, `O1g`): he said the old ones moved too fast.
  - N2 jelly v2: rings that blend through each other.
  - The new combinations (`BRD`, `HW`, `DA`, `BR4`, `H2`, `W2`, `D2`).
  - The jelly look: see-through, firm rim, gloss. He's interested, but it isn't picked yet.

## Colours

J wants the textures darker by a decent amount, but still good greens with a better colour blend. The round-4 palettes in `construct_designs4.PALETTES` do this:
- five stops instead of four;
- smoothstep blending between them;
- about 20–25% darker than round 3.

Use those, not the round-3 ones.

## Jar size

Each strip is 1–2.5 MB as a PNG, and the jar sits at about 29.5 MB against a 30 MB limit. So:
- Quantize to 256 colours (FASTOCTREE) and run oxipng, as for the dark lantern glow.
- Or cut the frames to 16, or use 32 px per block (128 px strips), for the less important ones.

## Charging animation (Blender, J deciding)

J's direction:
- The light flowing into the ring should be subtle and smooth.
- The lantern getting super bright, in a cooler way, matters most.

Blender pass 62 shows four options with the 6 s charge and a 1.5 s overcharge climax:
- **A:** heartbeat to white star
- **B:** lightning in the cracks first, then the glass fills
- **C:** rising tide that brims into a halo
- **D:** storm spinning into a blaze

I'll pass on his pick when he makes it.
