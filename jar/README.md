# Blender takes test jar

`lantern-ring-blender-takes+26.3.jar` is the latest main (Saw mode, 2.1.640) plus every model and
animation from the Blender pass 400s chat, switchable in the **Ring Lab**. Use it in place of your
current Lantern Ring jar (Minecraft 26.3, Fabric). It is 29.9 MB: the PNGs are shrunk losslessly,
pixel for pixel, with `tools/optimize_jar_assets.py`.

## New Ring Lab rows

| Row | Options | Default | Where to see it |
|---|---|---|---|
| **Ram barrier** | Particles (the old placeholder), R1 glass shell, R2 lattice, R3 particle field, R4 pressure rings | R1 | Fly fast into a wall |
| **Nebula light** | Classic column, L1 strip column, L2 strip orb, L3 strip crystal, L4 core & cage | L1 | Hold the Nebula lantern (Lantern model: Nebula) |
| **Dread Runner kill** | Random (K1-K4), K1 pounce & pin, K2 grab & hurl, K3 fear scream, K4 rake through, Off | Random | Yellow ring, Blast level 4, aim at mobs |

**Rating.** Rate each option KEEP, IMPROVE or DROP and paste the "Copy report" back as usual.

**Nebula light (L1-L4).** It wraps the corps' construct look strip round the light, so changing the
construct look for that corps changes the light too.
- It is drawn on the **held** lantern only; the placed lantern keeps its classic light for now.
- Orange has no construct strip yet, so its light stays classic.

**Dread Runner kills:**
- The runner stops for up to **three** mobs a run and plays the kill on each. Anything after that
  is trampled as before. Players are trampled, never grabbed.
- The kill lands on the clip's hit frame: K1 frame 17, K2 frame 30, K3 frame 20, K4 frame 10.
- K2 throws the body on after the kill.
- The pick takes effect in single player. A server keeps Random.

## What's not in it

The lead Blender chat's newest animations (passes 214-222: sprint, flight takeoff and landings,
charging at the lantern, the hanging lantern, combat poses and combos) exist only as Blender
update scripts on `claude/lantern-redesign-pass2`. They have no game export yet. The construct
tools round 2 designs (D1-D12, pass 950) are the same.

## Checked

`./gradlew build` passes. The game boots in the client game tests (ram barrier, lantern models,
Dread Runner), and `in_game_check.png` shows the screenshots:
- **top row:** R1 on a flyer; the held green and blue Nebula with the L1 light;
- **bottom row:** the Dread Runner mid-kill among the test pigs.

Not checked: how it looks under Complementary.
