# Build order: J's movement picks from the review site (2026-10-15)

**From:** Blender modeller, passes 400–499 (movement and flight). **For:** the mc project chat. This is a **BUILD**.
**Base:** the bundle (`docs/handoff/2026-10-14-bundle-jar/`, jar 2.1.647+), which shipped L5 as the landing default with
L4/L6 options, D1 with D2/D3 options, and the R3 dart with free arm A2 plus A1/A3 options. J has now rated them on
https://lantern-review-j.vercel.app (`docs/blender/review/RATINGS.md`).

## 1. Double-tap landing: **L4 is the landing, with 0.3 blocks of carry** (pass 405)

- J: KEEP L4, note "0.3 carry blocks". L5, L6 and the old L2 are DROPPED: remove them from the Ring Lab.
- Use L4's timing and poses (`../2026-10-14-bundle-jar/poses/405_L4.json`): brake 2 ticks, 5-tick drop, absorb
  crouch 2 ticks, stand 7 ticks; touchdown cushion ring radius 1.4.
- **Carry:** L4 as built travels 0.8 blocks forward from the double tap to touchdown. Scale the horizontal travel
  during brake + drop by 0.3 / 0.8 = **0.375**, so it lands **0.3 blocks** from where the tap happened. Total time stays
  ≈ 0.30 s. No run-out.
- Still required (from J, `DECISIONS.md`): descend (sneak) and the double tap must work **while moving forward**, not
  only when still; any flight input during the drop cancels it back into flight.

## 2. Ring arm lead: **D1 default, D3 option** (pass 404)

- J: KEEP D1, KEEP D3, DROP D2. Remove D2 from the Ring Lab. D1 stays the default; D3 (adds up to 35° of bank into
  turns) is the Ring Lab option. Poses: `../2026-10-14-bundle-jar/poses/404_arm_lead_D1-D3.json`.
- Slow flight is the upright body (20° lean); pass 406 shows the same rule there and is still waiting on J's rating —
  don't build 406 yet.

## 3. Running dart free arm: **drop A3** (pass 403)

- J: R3A3 "Drop it". Remove A3 from the Ring Lab; keep A2 (default, his in-game pick) and A1.
- S2a is replaced by pass 407's S2a (section 4).

## 4. Standing take-off: **S2a now settles at 2.2 blocks** (pass 407, added 2026-10-15)

- J: KEEP "S2a Fast spring to 2.2" on the site. Replace the old S2a (3.2 blocks) with it; poses
  `../2026-10-14-bundle-jar/poses/407_S2a.json` (same format as `403_S2a.json`).
- Fast spring: 90% of the climb in 2 ticks, critically damped, never overshoots; hover settles at **2.2 blocks**
  (2.27 at the top of the 0.07 hover bob). Second jump 4 ticks into the first, puff ring, 0.5° shake over 4 ticks, then
  free flight, all as 403.
- S1 and S2b (3.2 blocks) stay as they are; the default stays S2b (J's in-game pick) unless J says otherwise.

## Ring Lab

- Every option label keeps its take code and pass. J's saved choices must not be overwritten
  (`../2026-10-14-j-ring-lab-settings/`): if J's saved landing is L5 or L6, move him to L4 once and mark it changed in the
  Copy report, since those options are gone.

## Report back

Jar version and size; confirm the landing measures ≤ 0.3 blocks of carry and ≈ 0.3 s in game, and S2a hovers at 2.2 blocks.
