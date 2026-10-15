# Pass 701: skin workshop close-ups, animated

J on the site's pass 593 cards: "these i need to see animated on the site and closer up for each thing".

- Open in Blender: `LanternLive\constructs\skin_workshop_close.blend`. Pick a `Cam <code> close` camera and press play
  (160 frames, 8 s).
- Nothing in the designs changed. It's pass 593's scene with new cameras only:
  - **`Cam <code> close`**, one per texture (23): a slow close arc on each thing in turn.
    - frames 1–40: the 3×2 wall
    - frames 41–80: the dome
    - frames 81–120: the particle sphere
    - frames 121–160: the suit (after it has formed)
    - The textures play as the game strips do, so the animation shows.
  - **`Cam wall W1 close` … `Cam wall W5 close`:** each particle wall on a slow 6-second arc, 5 blocks out (the old
    camera was 7 out).
  - Rings and lanterns keep their stills.
- Spec `specs/701.json` replaces 593 on the site (593's spec now has `superseded_by: 701`).
