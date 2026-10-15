# Pass 704: ripple packing for 702's X5Ea, X5Eb and X5Na, three takes each

J rated 702 at 20:56: X5Ea, X5Eb and X5Na IMPROVE with no notes (three new variations each); X5Ec dropped. His 701 X5E
note still applies: "we need textures where the ripples are more efficiently packed onto big texture surfaces".

- Open in Blender: `C:\Users\Josh\Documents\LanternLive\constructs\skin_variations3.blend`. Cameras are
  `Cam <code> close` (for example `Cam X5Na2 close`), the same 8-second close tour: wall, dome, particles, suit.
- Each take keeps its 702 parent's colour and grading (a = deeper, b = brighter) and changes the packing:
  - **1 grid:** one ripple source per block (16 per tile instead of 1), neighbours out of step so the rings interlock
  - **2 honeycomb:** sources on a hex lattice, about two per block, rings meeting their six neighbours along clean lines
  - **3 interference:** seven sources per tile whose waves add into a moving lattice over the whole surface
- Takes: X5Ea1-3 (emerald, deeper), X5Eb1-3 (emerald, brighter), X5Na1-3 (neon, deeper).
- Textures: `tools/construct_designs11.py`; the strips sit next to the blend in `LanternLive\suit_tex\`
  (x5g/x5h/x5i, emerald and neon), not packed, so the .blend stays under the upload limit.
- Pass 703's ripple takes are now called X5Pa-c so they don't clash with 702's X5Ea-c.

Render on J's PC: double-click `C:\Users\Josh\Documents\LanternLive\RENDER.cmd` (one run at a time).
