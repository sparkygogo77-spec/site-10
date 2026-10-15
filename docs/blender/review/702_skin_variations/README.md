# Pass 702: skin workshop variations, three per texture

J rated 701 at 18:00:
- **KEEP:** BRD, BRJR, BRN, T9 (already in `docs/handoff/2026-10-15-review-keeps/`).
- **DROP:** LANTERNS, RINGS, T3, T5.
- **IMPROVE with no note:** R2K1, T1, T2, T6, T7, X1, X3, X3D1, X5E, X5N. His standing rule for those is three new
  labelled variations each.

- Open in Blender: `LanternLive\constructs\skin_variations.blend`. Cameras are `Cam <code><a|b|c> close` (for example
  `Cam X1b close`); each is the same 8-second close tour as 701: wall, dome, particles, then the suit.
- Every variation keeps the texture's own pattern and animated strip and changes one thing, the same way for every
  texture, so they compare across the board:
  - **a, deeper:** darker and more saturated (value ×0.6, saturation ×1.3, glow ×0.7)
  - **b, brighter:** stronger glow in the texture's own hue (glow ×1.6, saturation ×1.3), never washed to white
  - **c, finer:** the pattern twice as fine, and its animation half the speed
- Built on 701's scene: each variation is a copy of the texture's lane in its own row in front of the workshop.
