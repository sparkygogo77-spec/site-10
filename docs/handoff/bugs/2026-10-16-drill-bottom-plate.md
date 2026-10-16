# Blast drill: remove the bottom plate; keep its light (J, 2026-10-16 ~00:30 UTC)

Screenshot `2026-10-16-drill-bottom-plate.png` (Blast mode 3x3, first person, underground, patched Complementary).
J: "remove bottom plate from the drills now" and "also the light emanating from this one looks great".

- Remove: the flat translucent green plate under/behind the drill (the large flat construct panel lower left of the drill in the
  shot). It's not in `blast_drill*.bbmodel` (no flat elements there), so it's drawn separately: check `BlastDrillFx`, the
  construct pad/lining the Blast lays in its tunnel ("Line every landing's crater with the construct pad"), and the barrier
  surface under the drill. Remove it for every drill (D1-D3 and the default).
- Keep (J likes it): the light the drill gives off, as in this shot. Don't change the drill's glow while removing the plate.
