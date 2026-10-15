# Pass 858: Compact mech: new textures, more detail — WAITING

**Script:** `docs/blender/blender_updates/858_mech_compact.update.py`
**Open in Blender:** `C:\Users\Josh\Documents\LanternLive\constructs\mech_compact.blend` (starts on Cam MS1, press play; frames 1-130)
**Cameras:** "Cam <take>" for each take (MS1 MS2 MS3), "Cam <take> close", and "Cam row MS".

J on 821 MS Compact (0.6 size), IMPROVE: "Different texture, more detailed designs for the robots".
From 810: "mech suit needs a few design iterations as a big robotic suit, do one other size and a few animations for
it, this may be a feature i can give to a villager or any kind of mob potentially".

Three new compact mechs. Each is 0.6 of the full mech (built in full-size units, the whole mech scaled to 0.6), sized
for a villager or a small mob, and none use X3D1. Each has its own texture from `docs/texture_library` and much more
detail than 821 MS: panel seams, rivets, joint drums, working pistons (a sleeve and a lit rod that slide as the joints
move), vent grilles, sensor eyes, antennae and exhausts. Each forms, moves and attacks its own way.

Same timing for every take (20 ticks a second): 1-24 form, 24-30 board, 30-35 seal, 36-76 move, 76-96 attack, 96-126 finisher.

| Take | Design | Texture | Forms | Move / attack / finisher | Pilot | Best frame |
|---|---|---|---|---|---|---|
| MS1 | Workhorse: stocky biped loader; three-eye sensor head with antennae, chest core, radiator fins and two exhaust stacks, vented hips/calves/pauldrons, pistons on knees, ankles and elbows, ram forearms with three-finger hands | W1 neon weave | printed: a scan plane rises from the floor and extrudes each part upward | brisk march with exhaust puffs, head scanning; piston punch (the forearm ram fires the fist out); double ram slam into the ground | villager | 84 |
| MS2 | Crawler: four-legged walker; low hull with a five-eye sensor cluster, raised pod with a glass sensor dome, crystal spikes, two pincer arms with hydraulic jaws, pistons on every leg | V1 crystal | grown like crystal: hull first, legs grow joint by joint, claws, spikes last | diagonal-pair trot; pincer lunge, both claws snap shut; rears up and stomps, crystal spikes burst out in a ring | baby zombie | 107 |
| MS3 | Treadline: tracked mini-mech; twin treads with moving cleats and spoked road wheels, turret cockpit with a barred canopy, headlights, spinning radar dish, engine box and exhausts, four anchors, drill right arm, three-finger grab claw left | R2K1 dark jade | assembled on rails: plates slide in from the sides along two glowing rails | drives and pivot-turns on its treads (the turret keeps facing ahead); drill thrust bursts a stone pillar; anchors punch down and the turret spins a full turn | villager | 108 |

**For J:** KEEP / IMPROVE / DROP for each take.
