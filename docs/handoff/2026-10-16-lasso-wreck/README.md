# Lasso bubble: wreck through blocks, release to deconstruct, crater on throws (J, 2026-10-16 ~01:20 UTC)

J: "i might want lasso to, if i run the orb or circle through any blocks it should just wreck through them and send them flying in the
direction collided with. letting go of right click should deconstruct the sphere. do not disrupt the throwing physics, but if a mob is
thrown into blocks it should create a proper crater based on the direction its going."

1. **Wreck through blocks:** while J swings the lasso bubble/orb (or its ring/circle), any block it passes through breaks and the
   blocks are flung as falling-block debris **in the direction of the collision** (the bubble's velocity at contact), like the ram
   barrier and slam debris. Respect unbreakables (bedrock etc.); no item drops spam (match the slam/crater rules).
2. **Release = deconstruct:** letting go of right-click dissolves the sphere (the construct dissolve fill J loves), instead of it
   lingering.
3. **Keep the throw physics exactly as they are** (0f4deea7 "Lasso bubble: steady physics and working controls"). Don't change
   swing, release speed or arcs.
4. **Thrown mob into blocks = directional crater:** when a thrown mob hits terrain, carve a crater shaped by its travel direction
   (elongated along the velocity, deeper at the impact end, debris flung forward), sized by impact speed; line it like the other
   craters if that's the house rule.
- Test: swing through a wall (blocks fly the right way), release (dissolve), throw a pig into a hillside (crater shape follows the
  direction), screenshots.
