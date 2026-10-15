# Pass 602: lantern set-down, kneel and place

J picked "Kneel and place". Until now there was no set-down: the catalogue only had K3c played backwards as a stand-in.

- Open in Blender: `LanternLive\lanterns\lantern_set_down.blend`. Start on `01 Set down deliberate - 3rd person` and
  press play.
- Each take has three cameras:
  - `NN <take> - 3rd person` (over the right shoulder)
  - `NN <take> - side`
  - `NN <take> - 1st person` (from the eyes; arms, ring and lantern only)
- Same rig and K3 poses as the K3c pick-up (pass 601/213). The Dark Lantern is at its true size: 16 px tall with the
  handle.
- The lantern hangs from the ring hand by its handle and swings against your movement. It touches down when its base
  reaches the ground, rights itself over 4 ticks, then you let go.

| NN | Take | Touchdown | Let go | Done | Notes |
|---|---|---|---|---|---|
| 01 | Set down deliberate (D1) | tick 29 (1.45 s) | 36 | 64 (3.2 s) | kneel, lower, a beat, let go, stand |
| 02 | Set down quick (D2) | 19 | 21 | 36 (1.8 s) | the same, faster |
| 03 | Set down and seal (D3) | 29 | 34 | 76 (3.8 s) | after letting go, the ring hand rests over the lantern and it lights (pulse, then idle glow 0.12) |

- Ring: a small flare as you let go (D3: a longer glow while sealing).
- Lantern glow: off while carried, settles to its idle 0.12 once it stands.
- First person: while you carry the lantern standing, it hangs below the view. Once you kneel and look down, the hand and
  lantern come into view.
- For the game: `lantern_set_down_poses.json` has per tick:
  - the parts (rot, offset_px), as in K3c;
  - the lantern's rig-space rotation and base point;
  - `grounded`, plus the touchdown and release ticks.

Open for J: D1 / D2 / D3, KEEP / IMPROVE / DROP.
