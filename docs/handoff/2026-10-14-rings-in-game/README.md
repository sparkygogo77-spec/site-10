# Hand-off: four rings into the game (J's picks, 2026-10-14)

**From:** Chat C (Blender, passes 500–599 and 800–899).
**For:** the mc project chat (game code).

**Sources:**
- Blender: `C:\Users\Josh\Documents\LanternLive\lanterns\rings_in_game.blend` (Cam row game). It is built by
  `docs/blender/blender_updates/801_rings_in_game.update.py`, which uses the pass-800 builds.
- Models: `docs/handoff/2026-10-14-rings-in-game/assets/`, made by `tools/ring_voxels_bbmodel.py`.

## What J asked for

> "put r19d in game remove the icon on r16a just do no icons"

> "put these two in as well" (a screenshot of R12c and R12b)

> "remove the crowns and send them to be put in game" (R12b and R12c, update)

| Ring Lab option | Take | Look | bbmodel | Cubes | Face top |
|---|---|---|---|---|---|
| `R19D` | R19d | round face, J's concentric square cut in light, a second line of light outside the stone, bigger 7 px face, hex band, cathedral shoulders | `ring_r19d` | 372 | 15 units |
| `R12B` | R12b without the crown (J) | round face, plain 16-facet ripple stone, gold beading round the rim, gold line along a hex band, slim | `ring_r12b_plain` | 410 | 13 units |
| `R12C` | R12c without the crown (J) | as R12b but the band is the weave, no gold band line | `ring_r12c_plain` | 303 | 13 units |
| `R16A` | R16a without the icon (J) | cushion face, plain ripple stone, a line of light inside the bezel, weave band, cathedral shoulders | `ring_r16a_plain` | 276 | 15 units |

All four are original designs; no published emblem is on them. Only R19d keeps a symbol (J's concentric square).

## Code (`RingModels.placement`, `LabSettings.RingModel`)

Add the four values to `LabSettings.RingModel` (`R19D, R12B, R12C, R16A`), and these to `placement()`:

```java
case R19D -> new Placement("ring_r19d", 16f, 1f, 15f / 16f);
case R12B -> new Placement("ring_r12b_plain", 16f, 1f, 13f / 16f);
case R12C -> new Placement("ring_r12c_plain", 16f, 1f, 13f / 16f);
case R16A -> new Placement("ring_r16a_plain", 16f, 1f, 15f / 16f);
```

Copy `assets/bbmodel/*.bbmodel` into `src/main/resources/assets/lanternring/bbmodel/`, and
`assets/textures/entity/bb/*.png` into `src/main/resources/assets/lanternring/textures/entity/bb/`.
The files take about 1.8 MB on disk; the textures are 12–15 KB each.

Layout: the same as `tools/ring_bbmodel.py` (and `ring_square`). 16 units make one skin pixel, one voxel is one unit,
x runs across the finger, y out of the fist (face up), z along the finger, and the band reaches 8 units into the fist.
Bounds: x ±14 to ±16, y −21 to the face top, z ±12 to ±14.

## The glow (J: "the glow should be consistent and get even brighter ... never faded")

- Every cube whose name starts with `glow_` is the stone, a light line or the textured band. The game already draws
  these full-bright in the corps colour (`CorpsTint`).
- On R19d and R16a every cube is glow; on R12b and R12c the gold parts are body cubes.
- Keep them at full brightness at all times, with no fade or pulse when idle. The charge flash can still play on top.
- The Blender preview settles at steady brightness 1.05 after lighting up.

## Textures

Each glow cube is painted with frame 0 of its strip (W1 weave, H1 hex, X5 ripple), shaded as in Blender. The ripple
is centred on the face, as J asked. In game the texture is static; animating it would need the strip, its mcmeta and
an animated entity texture. That's optional, and J hasn't asked for it on the worn ring.

## Ring Lab

Add the four to the Ring Lab ring picker, named "R19d concentric", "R12b crown detail", "R12c crown weave",
"R16a plain". Name R12b and R12c "R12b plain detail" and "R12c plain weave". Keep the current default unless J says
otherwise.
