# Hand-off: charging at the lantern (J's picks, 2026-10-14)

From the lead Blender chat, for the game chat that builds lantern charging. The test model is the **Dark Lantern**
(`PowerBatteryBlock`, Dark style); the same rules apply to every lantern style. The ring is on the **right** arm.

**Data.** Pose data is in `poses/kneel_lean4_poses.json` (20 ticks a second). Per tick:
- the solved pose: per part `rot` (radians) and `offset_px` from the vanilla pivot. The shins pivot at the knee, 6 px
  below the hip.
- the lantern: `tilt` when it stands, `swing` when it hangs.
- `glow`, from 0 to 1.

Per take: `lantern`, `body_yaw_rad` and `carry_from_tick`.

**Sources.** Blender source: `docs/blender/blender_updates/213_kneel_lean_round4.update.py`. J's file:
`C:\Users\Josh\Documents\LanternLive\kneel_lean4.blend`.

## 1. L1c: the lean to charge (J's pick)

The lantern stands on a block in front of you. You stand upright, take a half step in, and drive the ring fist straight
into the emblem port.

**Port.** The port is always in the same place on the lantern:
- its centre is at 52% of the body height;
- the opening is 4.8 px across, so a 4 px fist fits;
- it is 3 px deep.

**Fist contact.** Every tick the ring arm (both angles) and the forward lean are solved so the fist lands in the
port's centre, with the ring at the port's mouth.
- The port is a recess: the fist goes into it.
- It is never pushed up from below, and nothing else touches the lantern or the block.

**Push timing.** Keys: `idle` 0, lean 9, push 26, lean 42, push 58, lean 70, `idle` 84. The ring charges from tick 9 to 70.

**Tip and wobble.** Each push tips the lantern away from you about its far bottom edge (`tilt`, top away from the
player), and it wobbles back when you ease off.
- Use a damped spring on the tilt.
- Use the data's `tilt` per tick as the target curve.

## 2. K3c: kneel and pick up (K3b was J's good one; K3c adds real lift-off)

**Kneel.** One knee down, on the ring side:
- ring-side thigh about straight down with the knee folded 86° (shin flat on the floor behind you);
- free-side thigh forward about 81° with the knee folded 81° (shin upright, foot planted).

Earlier files lost the knees and did the splits; J flagged that.

**Lift-off physics.**
- While the hand on the handle is lower than the lantern is tall (handle 15.5 px above the base), the base stays on
  the floor and drags or tips with the hand, like a kickstand.
- Once the base clears the floor, the lantern swings as a pendulum from the handle. It starts from the tilt and spin it
  already had: no snap.

**Lift height.** Raise it to the chest, not overhead (J: "K3 needs to not raise the lantern so high"). The lantern
glows the whole time it is being lifted.

## 3. The charge light: much brighter, running down the whole lantern (J, on L1c)

J: "my lantern should be much brighter than this… it's just using the sphere, I want the light running further down
the model."

**Fill rule** (`glow` = charge 0..1):
- The **glass** lights from the port at the top down to the base as the charge rises. The lit front is at
  `h = 1.05 - 1.15 × charge`, where h runs from 0 at the base to 1 at the top.
- Everything above the front is lit. A bright band about 7% of the height wide runs along the front edge, at 3× the
  base glow.
- Only the dark glass texels light up. The gold frame stays metal: weight by darkness, with full glow for texel
  brightness up to 0.05 and 15% by 0.35.
- Nothing glows at charge 0.

**Brightness and colour.**
- Glass emission: saturated corps colour, about 5× (the green is about RGB 0.2, 1.0, 0.3). The first try at 14×
  washed out to white.
- Inner glow cubes: `1 + 16 × charge`, with the colour half-mixed toward a light lime in the corps hue.

**Light on the world.** A light inside the lantern lights the block and the player, scaling with the charge. In game,
raise the block light level with the charge (for example 7 at idle up to 15 when full), or use a dynamic light if one
is available.

**Suggested implementation.** Add a `charge` blockstate (0–5). Each level gets an emissive overlay layer on the glass,
with the lit front stepping down the body per the rule above, all recoloured per corps (`CorpsTint`). Animate the
band's position between levels for smoothness if using a block entity renderer.

## Not in this hand-off (J hasn't picked yet)

Hanging charge H1–H3, lantern charge C1–C3, leans L1d, L1e and L2c, and suit round 3. They're in `LanternLive` as .blend
files for J to look at.
