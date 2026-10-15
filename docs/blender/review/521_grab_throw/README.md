# Pass 521: grab and throw with a construct hand

J (503): "grab-throw later". Picked now: a construct hand grabs the mob and throws it where you look.

- Open in Blender: `LanternLive\combat\grab_throw.blend`. Start on `01 Reach and fling - 3rd person` and press play.
- Each take has three cameras: `NN <take> - 3rd person`, `NN <take> - side` and `NN <take> - 1st person` (from the eyes:
  arms, ring, hand and mob).
- The crosshair is 12° right of the mob. The throw goes along the crosshair, not back the way the mob came.

| NN | Take | Grab | Release | Hits wall | Throw speed |
|---|---|---|---|---|---|
| 01 | Reach and fling (G1) | 18 | 36 | 44 | 1.9 blocks a tick |
| 02 | Overhead whip (G2) | 18 | 38 | 45 | 2.2 (slightly down) |
| 03 | Spin throw (G3) | 18 | 44 (after one full turn, 24–44) | 51 | 2.0 |

How each take plays out:
1. **Forming (ticks 9–12):** a construct hand (dark-jade fragments, see-through) forms a block in front of the ring fist.
2. **Reach (12–18):** it shoots 6 blocks to the mob on a thin tether, and the fingers and thumb close on the grab at 17–18.
3. **Carry:**
   - G1: yanks the mob up in front of you, winds back over your right shoulder, then flings.
   - G2: arcs it up over your head and behind you, then whips it back over and down the crosshair.
   - G3: pulls it to arm's length (3.4 blocks); you spin once with it.
4. **Release:** the hand opens and dissolves into pixels within 8 ticks. The ring flares on the throw.
5. **Flight and impact:**
   - The mob flies with gravity 0.08 and drag 0.98, tumbling.
   - It hits a stone wall 16 blocks out and craters a 3×3 in its face: the centre lights on impact and is gone 4 ticks
     later, and the ring of 8 is gone at 6, as pixels.
   - The mob sticks in the hole and flashes hurt on the grab and the hit.

For the game: `grab_throw_poses.json` has, per tick:
- the parts (rot, offset_px) and body yaw;
- the construct hand's position (blocks from your feet), scale and grip 0..1;
- the mob's position and the ring glow;
- the grab, release and hit ticks and the crater cells.

Open for J: G1 / G2 / G3, KEEP / IMPROVE / DROP.
