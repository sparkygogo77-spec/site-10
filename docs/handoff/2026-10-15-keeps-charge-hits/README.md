# Hand-off: J's KEEPs from passes 807 and 815 (2026-10-15)

## Lantern charge: L3 core swirl (pass 807) — KEEP, word for word: "L3 Core swirl wins this one"

- Blender: `LanternLive\lanterns\charge_final.blend`. Script: `docs/blender/blender_updates/807_charge_final.update.py`
  (mode `L3`).
- **Timing (G3b, unchanged):**
  - the ring docks into the port; 12 s to full;
  - a 2 s overcharge climax (charge 1.0 → 1.4), held;
  - a slow 7.5 s fade.
- **What L3 adds:** the light strands winding round the core are 3× as strong and spin twice as fast as the charge
  fills, and the heart flares more.
  - Strand phase = 3·angle + 0.55·dz + 2·spin, where spin accumulates (0.5 + 4.5·charge) rad/s.
  - Strand weight = ((sin(phase) + 1) / 2)³ × 3.
- **Kept from G3b:**
  - the gold cracks flash, then settle dim until the green swallows them (charge 0.95–1.3);
  - dark stitch seams;
  - the gold frame catches the light;
  - the 3° helix;
  - the stream into the ring is now saturated green, (0.2, 1.0, 0.35).
- For the game: drive the lantern's glow layers and particles from the block's charge value with these curves; the
  swirl can be an emissive overlay texture scrolled by `spin`.

## Hit effects: F1 construct shatter and F3 outline flash (pass 815) — KEEP, word for word: "the outline flash is good the construct break is good"

- Blender: `LanternLive\combat\hit_effects.blend`. Script: `docs/blender/blender_updates/815_hit_effects.update.py`.
- **F1 construct shatter:** the construct breaks into its pixels from the hit point outward.
  - Each pixel leaves 3 ticks per block of distance later, at 0.22/(0.6 + d) blocks a tick (nearer ones faster).
  - It tumbles and falls (gravity 0.01/tick²) and shrinks out over 16 ticks.
- **F3 outline flash:** a construct-green outline round every part of the hit mob.
  - On for 3 ticks, gone by tick 9.
  - 24 green sparks spray off the hit point (9 ticks); the mob rocks 12°.
  - In game: an entity outline render like glowing, but construct green, only 9 ticks, plus a spark burst.
- F2 (knockback shockwave) and F4 (all three) are not picked; don't build them.
