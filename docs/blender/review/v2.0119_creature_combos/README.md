# Pass v2.0119: creature combos that move (the polar bear)

J rated v2.0117 rev 2 and v2.0118 "improve all, the animations are too simple" and picked combos, moving attacks, more
body motion and new iterations. Built one creature at a time; this pass is the bear.

- Open in Blender: `C:\Users\Josh\Documents\LanternLive\trials\creature_combos.blend` (camera `Cam <code>`, frames 1-100, 20 a second)
- Script: `docs/blender/blender_updates/v2.0119_creature_combos.update.py` (distance-driven gait: `build_path`, `run_gait`;
  `bear_combo` chains rear-ups and swipes on top)
- Checks: all OK (no limb crosses another, nothing under the floor, planted paws touch)

| Take | Name | What it is |
|---|---|---|
| BC1 | Bear combo 1: charge, rear up, double swipe | the lean sloth bear (PB7) charges 5.2 blocks at you, skids and leans back, rears up and roars, drops with a thud and snow dust, then rakes you twice: right claws on tick 78, left claws on tick 88 (the second knocks you flying). Paws stay planted while it runs and turns; head follows you; fuller face, inward anteater claws |
| BC2 | Bear combo 2: stalk, crouch, lunge, swipe, back off | the blizzard-maned bear (PB8) stalks in low with its head down, stops and crouches, lunges a full stride, rakes you on tick 67, then backs off a stride growling with its head low |
| BC3 | Bear combo 3: circle in, rear up, claw rakes | the old scarred boar (PB9) circles round you, turning as it walks until it faces you, rears up with its huge claws raised and rakes down twice (the second catches you), sways, then drops with a thud |
