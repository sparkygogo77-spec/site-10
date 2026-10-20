# Pass v2.0122: bear attacks with the real paw, claws and teeth

J on every bear combo (v2.0119, v2.0121): "they are all pretty bad" - a detailed black/white paw, separate long
sharp curved claws, real teeth, one wide side swipe perfected along the ground, and others of equal depth.

- Open in Blender: `C:\Users\Josh\Documents\LanternLive\trials\bear_attacks.blend` (camera `Cam <code>`, frames 1-100, 20 a second)
- Script: `docs/blender/blender_updates/v2.0122_bear_attacks.update.py` (`bear_front_paw`, `bear_teeth`,
  `bear_attack`: paws on Catmull-Rom spline paths solved with IK, single values eased key to key)
- Checks: all OK (claws included: no limb crosses another, nothing under the floor, planted paws touch); BA1 claws
  skim 0.2 blocks above the snow, 0.02 blocks from the player on the hit tick

| Take | Name | What it is |
|---|---|---|
| BA1 | Bear attack 1: wide side swipe along the ground | steps in, shifts its weight onto its left side, lifts the right paw and swings it wide out to the side with the claws turned outward, then arcs it low along the ground and in across to you: the claws rake the snow (it sprays) and hit you on tick 51, knocking you inward; the shoulder dips into the swing, the body twists through it and the paw follows through past you before it sets down. Head tracks you, lips peel back over the teeth |
| BA2 | Bear attack 2: tilted bite and head shake | steps in, lowers and tilts its head sideways like a real bear, opens wide (long upper and lower canines, incisors and molars, black lips), lunges and bites on tick 48, shakes its head dragging you side to side, and flings you on tick 61 |
| BA3 | Bear attack 3: two-paw hammer hook and pin | steps in, half rears with both arms coming up and forward, then hammers both paws down onto you (tick 50): the claws curl and hook in, you are pinned flat and dragged back under its chest, then it lifts its paws |
| BP1 | Bear close-up: the new paw, claws and teeth | a close look at the new forepaw: it lifts the right paw and turns the black pads to you (main pad, carpal pad, five toe pads) under the white fur and guard-hair fringe, flexes its five separate long curved claws twice, then turns its head and snarls to show the teeth |
