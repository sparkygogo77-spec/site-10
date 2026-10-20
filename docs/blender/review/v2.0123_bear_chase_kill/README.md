# Pass v2.0123: bear chase, bite, hold and kill; teeth rebuilt

J on v2.0122: "the bear should get progressively lower in preparation for a bit attack as it chases as moving target
and it should bi[te], hold on, and depending on what it is a kill animation of a final crush ... the teeth ... looks like red jello".

- Open in Blender: `C:\Users\Josh\Documents\LanternLive\trials\bear_chase_kill.blend` (camera `Cam <code>`, frames 1-140, 20 a second)
- Script: `docs/blender/blender_updates/v2.0123_bear_chase_kill.update.py` (`bear_chase`: two-pass pose so the
  target's path is built from where the jaws really are; `bear_teeth` rebuilt)
- Checks: all OK (claws included: no limb crosses another, nothing under the floor, planted paws touch); jaws close at
  1.26 blocks on the player, 0.88 on the seal, 0.78 on the crush; pinning paw 0.05 from its spot

| Take | Name | What it is |
|---|---|---|
| BK1 | Bear chase and kill: the player | you sprint away zig-zagging; the bear runs you down and gets lower and lower as it closes, head down and level, lunges and bites you on tick 66 (head tilted), holds on and shakes you, slams you down, pins you under its right forepaw with the claws hooked in, and crushes you with a last bite on tick 114: you go red, flatten and poof, and it roars over you |
| BK2 | Bear chase and kill: a seal | a seal galumphs away across the ice; the bear chases it, sinking lower and lower, bites it on tick 66, lifts it off the ground and shakes it, slams it down, pins it with a paw and crushes it with a final bite on tick 114, then picks it up limp in its jaws and lifts its head to carry it off |
| BP2 | Bear close-up: the new teeth | a close look at the rebuilt mouth (J: "the teeth ... looks like red jello"): the red block mouth is gone; big ivory canines, incisors, premolars and carnassials set in dark pink gums, black lips, a small pink tongue, a dark throat. It snarls wide from tick 60 |
