# Pass v2.0116: creatures round 2 at mob size, animated (area Trials)

J's v2.0112 notes (RATINGS.md, DECISIONS.md 2026-10-19 "creatures round 2 picks"): smaller mobs with proper
animations; a 5-block polar bear, skinnier, long sloth arms with claws, "more textured, detailed color picker fur";
a ~7-block Yellow Lantern enderman that carries and uses its lantern, no wings / crown / face, with acquired lava and
water constructs; teleport animation variations; an Orange Lantern enderman's charging prayer hugging its lantern;
the great white kept, scaled down to 6 blocks, plus other shark types; idle, hurt and death clips too.

- Script: `docs/blender/blender_updates/v2.0116_creatures_r2.update.py` (builds everything from nothing)
- Open in Blender: `C:\Users\Josh\Documents\LanternLive\trials\creatures_r2.blend`, cameras `Cam <code>`,
  frames 1-60 (3 s at 20 ticks a second)
- Takes: PB1-PB6 polar bear (idle, walk, sloth swipe, rear up, hurt, death); YE1-YE9 Yellow Lantern enderman (idle,
  teleport static / lantern / fold, lantern slam, lava throw, water cast, hurt, death); OE1-OE3 Orange Lantern
  enderman prayers (kneeling, forehead to the lantern, standing curl); SK1 great whites 22/14/10/6, SK2 mako /
  hammerhead / tiger / thresher, SK3-SK7 10-block great white (cruise, fast swim, bite, hurt, death)

How it's built: voxel parts on a joint hierarchy (bear 1/8 block, enderman one vanilla pixel = 1/7 block, sharks in
six body segments with a hinged jaw). Planted legs are solved with two-bone IK each tick, so paws and feet stay where
they touch down; the swipe hits the player on tick 27, the lantern slam touches the ground on tick 22, the water jet
ends on the player, the shark's jaw closes on the fish on tick 24. Hurt and death use Minecraft's red flash (an object
property "hurt" tints every part). Checks in the scene as `v2_0116_checks`: every frame, no two limbs closer than
their thickness, nothing under the ground, planted feet / knees / lantern at 0.0 blocks.
