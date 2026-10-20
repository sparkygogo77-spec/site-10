# Pass v2.0121: more bear combos (new iterations of v2.0119)

J left v2.0119 unrated and picked "New iterations": three more bear combos in new styles on the v2.0119 gait (leaps
with tucked legs, bites, a drive-by rake on a curve, a snow shockwave). v2.0120 is the spider chat's pass.

- Open in Blender: `C:\Users\Josh\Documents\LanternLive\trials\creature_combos2.blend` (camera `Cam <code>`, frames 1-100, 20 a second)
- Script: `docs/blender/blender_updates/v2.0121_creature_combos2.update.py` (distance-driven gait: `build_path`, `run_gait`;
  `bear_combo` chains rear-ups and swipes on top)
- Checks: all OK (no limb crosses another, nothing under the floor, planted paws touch)

| Take | Name | What it is |
|---|---|---|
| BC4 | Bear combo 4: run, pounce, pin, bite, back off | the blizzard-maned bear runs two strides, crouches and leaps a full 3.5 blocks with its legs tucked, lands with its front paws on you (tick 44: you go down, pinned), bites down on tick 56, then backs off a stride and roars |
| BC5 | Bear combo 5: drive-by rake, wheel round, roar | the lean sloth bear runs past you on a curve and rakes you sideways with its long claws as it passes (tick 36, you fly sideways), keeps running as it wheels round to face you, then stops and roars |
| BC6 | Bear combo 6: rear, ground slam, double bite | the old scarred boar rears and roars, slams both front paws down (tick 25: a ring of snow rolls out), then steps in biting: one bite on tick 44, a second on tick 62 that knocks you back, and a last roar |
