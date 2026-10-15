# Pass 824: flying mounts (flying horse, baby dragon, construct ghast) — WAITING

**Script:** `docs/blender/blender_updates/824_flying_mounts.update.py` (replaces 809's jet, bike and big dragon)
**Open in Blender:** `C:\Users\Josh\Documents\LanternLive\constructs\flying_mounts.blend` (Cam F2, press play; 120 frames;
"Cam <take>" follows from behind, "Cam <take> side" is fixed)
**Files here:** `sheet.png` (one check: F1 at tick 80, F2, F3 and F4 at tick 60)

J on 809: "horse is the only flying construct i want right now, maybe well force the lantern user to learn to ride a
flying creature, give me a flying baby dragon to ride on and also a ghast construct (it needs to fit the real model
instead of colliding with it, but since ours is pure construct you can make a new textured ghast instead".

Each mount forms from the ring in ticks 1–20, then moves off.

| Take | Mount | Texture | Motion |
|---|---|---|---|
| F1 flying horse | 809's horse (BR1) with ears, a 6-lock mane and a 4-lock tail | BR1 | gallops (10-tick stride), then runs up into the air to 9 blocks; a light pad flashes under the hooves every 5 ticks so it reads as running on light; mane and tail stream back |
| F2 baby dragon | chubby: big head with nub horns and a jaw, short neck, stubby 3-panel wings, short 4-link tail | X3D1 | a hop, fast little flaps (every 7 ticks), climbs to 7 blocks, glides (70–90), banks 28°; the rider's legs hang either side |
| F3 ghast, real size | the body is the real ghast's 4 × 4 × 4 block cube, with the construct shell 0.12 just outside it (the real model is shown faintly inside for reference) so it covers the model instead of cutting into it; nine tentacles in a 3 × 3 grid with varied lengths; a construct face | W1 | rises 3.5 blocks and drifts forward, bobbing; the tentacles wave and trail as it moves |
| F4 ghast, harnessed | the same size, with a harness frame and straps, four seats with backs, goggles over the eyes | H1 | rises with four riders |

**For J:** KEEP / IMPROVE / DROP per mount.
