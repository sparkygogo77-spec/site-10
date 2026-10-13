# Findings: charge meter, overcharge, summon melt and the everything jar (branch claude/lantern-redesign-pass2)

## Why J was missing blocks and models
- The jade construct blocks (packs constructs_jade_r1/r3/r4), the Dark Lantern and the Blue Lantern edits
  were only on `claude/lantern-redesign-pass2`. J was running the jar built from main, 2.1.556.
- The branch now has main merged in (up to #217, the thumb-up charge pose).
- PR "Lantern redesign pass 2 into main" brings everything to main. Once it's merged, CI's jar
  (builds/lantern-ring-latest.jar) has all of it, and the Ring Lab updater stops rolling J back.

## New on the branch
- **Charge timing (J: 4.5 s on a meter).** RingTuning charge_time now defaults to 4.5 s (the old 3.5 s
  default migrates). The ring fills gradually while charging, so letting go early keeps what it got.
  The HUD (ChargeMeter.lanternMeter) shows "Charging N%" with a bar.
- **Overcharge (J: burns 2/25 charges per battery).**
  - After full there are 10 ticks of grace, then holding on burns 2 of the battery's 25 charges.
  - It then fills up to +25% over charge_over (1.5 s).
  - Data components:
    - `lanternring:overcharge` on the ring is spent before its own charge.
    - `lanternring:battery_burnt` on the battery. The battery shows a bar and tooltip once any charges are gone.
  - A burnt-out battery can't overcharge; normal charging still works.
  - The HUD shows "OVERCHARGE +N%  left/25" in gold.
- **Summoned lantern (J: shouldn't shrink, should disintegrate into construct matter and melt).**
  - It stays full size and slumps onto its foot over 34 ticks (LanternFirstPerson.MELT).
  - It burns bright as it goes.
  - It sheds SHARD and PANE construct particles, and DRIP particles run off its foot.
  - Test: SummonMeltTest.
- **Dark Lantern light.** It runs through the lantern for the whole charge, not just at the end.

## Jar size: important for every thread
- The full build is 37.6 MB. oxipng alone gets it to 33.4 MB, over the 30 MB limit for sending files to J's PC.
- 256-colour palette compression in the jar only (sources stay full colour) brings it to 29.99 MB. It's applied to
  dark_lantern_glow*.png and the construct_ripples_*.png sheets, 4.7 MB down to 1.1 MB, an average error of
  1-4/255 that can't be seen.
- PNGs are 28.9 MB of the jar. The biggest are the per-corps copies: construct_inner_*, shockwave_glass_*,
  construct_rim_* at ~0.6 MB each. Palette-compressing those, or tinting one texture in code, is the next big saving.
- J has the jar: `Documents\LanternLive\lantern-ring-everything.jar`.

## Not yet tested in game
- Holding on after a finished overcharge no longer restarts a charge.
- The shorter gold HUD text.

## Fear Nuke fuse (J: takes way too long to explode)
- fear_nuke_orb 3 s to 2 s, fear_nuke_consume 4 s to 1.5 s: it goes off 3.5 s after the throw instead of 7 s.
  Saved old defaults migrate. Both are still in the Ring Lab's Durations page.

## Merge
- Main is merged in up to #222 (Red self-destruct, Orange Horde, Blue calm flash).
- Conflicts resolved:
  - LanternFirstPerson keeps main's blueGlow/BLUE_REST and drops the window halos, as main did; my Dark charge frames stay.
  - LanternCharge keeps both sides.
  - ShaderPackPatcher VERSION goes to 13, so both sides' patches re-apply.
