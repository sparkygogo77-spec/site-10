# Pass v2.0104: Ring models round 1 (12 wild worn rings, hero mesh + voxel twin)

J (2026-10-19): "new ring models refined as good of a model I can currently get in blender 12 variations (past ones
have all been weak)". Picks: "Both per take" (smooth hero + 1/4 px voxel twin), lineup "Wilder", cameras hero +
turntable + first person.

**What was weak before:** 832 icon rings were 1/4 px voxel boxes with a flat face (no bevels, flat colour); 856 and
860-865 were glow/animation tests on a placeholder box ring. None had a modelled ring.

**What's new in every take:** a band swept from a rounded cross-section and subdivided (micro-bevelled edges that catch
light), a modelled setting, a faceted refractive gem or glass lens (EEVEE raytraced refraction + thin-film colour play)
with the G3 flare core inside (green, hottest bits yellow, spins one way), layered metal (base noise + polished edges +
dark rough cavities from a baked curvature map + brushed bump + engraving), emission <= 1.5, original lantern mark
(lantern silhouette with a diamond window) inlaid on the band flanks of W1, W4, W6, W9, W12 and in W11's window.
Studio lighting with softbox strips reflected through sphere probes.

- Open in Blender: `C:\Users\Josh\Documents\LanternLive\combat\ring_models.blend`
- Cameras per take: `Cam Wn hero` (3/4 close-up, depth of field), `Cam Wn turntable` (hero left, voxel twin right,
  frames 1-120), `Cam Wn - first person` (120 deg, the jar's placement, fist bent back 50, frames 1-120).

| Take | Name | What |
|---|---|---|
| W1 | Orrery | gold collet gem inside two precessing silver hoops with moon gems; grooved gold band |
| W2 | Shard burst | knife-edge steel band, cracked jade-steel seat, seven crystal shards erupting off-centre |
| W3 | Talon clasp | three scaled gunmetal talons with gold tips grip a glass orb |
| W4 | Reliquary shrine | hex gold shrine: jade enamel frieze, pillars, glass chamber, domed roof (lantern R2a/R4a/R4b family) |
| W5 | Forged meteor | lumpy hammered iron, green glowing cracks in the dents, raw crystals |
| W6 | Aperture eye | knurled housing, nine iris blades opening and closing over a glowing pupil |
| W7 | Mobius ribbon | two-tone ribbon with a half twist, emerald-cut gem clawed into the twist |
| W8 | Broken halo | band snapped open, glowing ends, floating brilliant with orbiting chips and light arcs |
| W9 | Lantern crown | a miniature gold-and-glass lantern standing on the band |
| W10 | Thorn vine | braided patinated bronze with thorns, leaves cradling a glass seed pod |
| W11 | Knuckle plate | riveted gunmetal plate on gold, square window with a glowing lantern mark (R19f's square face) |
| W12 | Spire | stepped ziggurat band, tall leaning hex crystal spire, satellite gem |

Moving parts: W1 hoops precess, W6 iris breathes, W8 gem bobs and turns with orbiting chips; every flare core spins.
Script: `docs/blender/blender_updates/v2.0104_ring_models.update.py` (env `RM_ONLY=W1,W4` builds a subset).
