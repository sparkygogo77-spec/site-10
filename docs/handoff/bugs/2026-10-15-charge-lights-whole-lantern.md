# Lantern charge lights the whole glass instead of J's L3 core swirl (J, 2026-10-15 ~21:45 UTC)

Screenshot: `2026-10-15-charge-lights-whole-lantern.png`. J: "the core swirl charge is not the right one, it's not supposed to light the
whole thing". In game (jar 2.1.667/668, Complementary Unbound 5.81 patched, first person, "Overcharged! +25% ring power"):
the lantern's whole glass panel glows one even bright green, edge to edge.

What J picked: **pass 807 L3 core swirl**, KEEP "L3 Core swirl wins this one".
- Spec: `docs/handoff/2026-10-15-keeps-charge-hits/README.md`, `docs/blender/review/807_charge_final/README.md`,
  Blender `LanternLive\lanterns\charge_final.blend` (mode L3).
- The light should be strands winding round the core (weight ((sin+1)/2)^3 x 3, phase 3 angle + 0.55 dz + 2 spin) with a flaring
  heart; the gold cracks flash then settle dim, the dark stitch seams stay dark, the gold frame catches the light. Most of the glass
  stays dark between strands; it should not fill evenly.
- Game commit 31047459 put L3 into `LanternFirstPerson` / `BeamChargeGlow` and the `dark_lantern_swirl_*` frames, i.e. the Dark
  Lantern. Check: which lantern is this in the shot (gold frame, green glass), does it use the L3 strands at all, and is a full-glass
  glow layer (e.g. 088ca166 "glass glows from the start", BeamChargeGlow, overcharge glow) drawn over the strands and washing them out
  under the patched pack. Same root as the glow bug in `2026-10-15-green-glow-interference.md`?
