# Blender review folders

One folder per pass, `docs/blender/review/<NNN>_<name>/`, holding:
- `README.md`: what it is, J's request in his words, the takes (one line each), the cameras and frames to look at,
  any numbers the game needs (radii, ticks, speeds), and the open questions for J.
- `sheet.png`: a contact sheet of spot-check renders (Cycles 8–12 samples, 800×450 frames), and optionally `preview.gif`.
- `<name>_poses.json` if it animates the player (per tick, per part `rot` + `offset_px`).

Keep each folder under 5 MB; the .blend itself goes to J's LanternLive folder, not the repo. The script that rebuilds it
is always `docs/blender/blender_updates/<NNN>_<name>.update.py`. Log every delivery in `INBOX.md`.
