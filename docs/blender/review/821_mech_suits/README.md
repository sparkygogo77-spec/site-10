# Pass 821: construct mech suits — WAITING

**Script:** `docs/blender/blender_updates/821_mech_suits.update.py`
**Open in Blender:** `C:\Users\Josh\Documents\LanternLive\constructs\mech_suits.blend` (Cam MA, press play; 130 frames;
also "Cam <take> close" and "Cam <take> back")
**Files here:** `sheet.png` (one check: rows MA, MB, MC, MS at ticks 30, 56, 86, 112. It was seen from behind, and the
pilots' heads stuck out of the cockpit roofs. After it: the cameras moved in front, and the seats dropped so each pilot
sits inside.)

J on 810 G5: "mech suit needs a few design iterations as a big robotic suit, do one other size and a few animations
for it, this may be a feature i can give to a villager or any kind of mob potentially".

| Take | Design | Size | Texture | Pilot |
|---|---|---|---|---|
| MA | Titan frame: square chest cockpit with a glass canopy, straight legs, block fists with glowing knuckles, shoulder blocks with vents | ~4 blocks | BR1 | player |
| MB | Strider: reverse-knee legs, slim waist, raised pod cockpit with a visor slit, long arms with three-claw hands, antennae | ~4 blocks | H1 | villager |
| MC | Juggernaut: very wide plated pauldrons, hammer fists, barred canopy, two back thrusters | ~4 blocks | W1 | zombie |
| MS | Compact: the Titan frame at 0.6 size, the other size, made for mobs | ~2.4 blocks | X3D1 | villager (scaled to fit) |

**Animations, all four in a row (20 ticks a second):**

| Ticks | Animation | What happens |
|---|---|---|
| 1–24 | form | the mech builds round the pilot from the feet up, with pixels streaming from the core |
| 24–30 | board | the pilot is lifted into the cockpit and sits |
| 30–35 | seal | the canopy swings shut |
| 36–76 | walk | four heavy steps, 10 ticks each, each 0.9 × size long; the body bobs and sways; a dust ring at each footfall |
| 76–96 | punch | the torso twists back 25°, then a big right punch twisting 20° into it, a shock ring, recoil |
| 96–126 | stomp | crouch, jump 1.6 × size (MC's thrusters fire), land deep, a ground ring to 5 × size |

**For J:** KEEP / IMPROVE / DROP per design and size, and which mobs should get one.
