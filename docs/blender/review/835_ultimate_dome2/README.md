# Pass 835: ultimate dome round 2 — WAITING

**Script:** `docs/blender/blender_updates/835_ultimate_dome2.update.py`
**Open in Blender:** `C:\Users\Josh\Documents\LanternLive\constructs\ultimate_dome2.blend` (Cam D1 wide (also "look up", "player", "inside"); press play)

J on 826: "the construct of the dome also builds behind the blocks a little too laggy".

**Why it lagged:** in 826 each panel faded in over 4 ticks with up to 2 ticks of random delay, and the bright edge was
keyed only every 4 ticks, so the blocks trailed the edge. Now every block snaps in on the exact tick the front reaches
it (the edge and the blocks share one timing), and the edge is keyed every tick. The dome is 48 bands x 8 sectors (384
pieces instead of about 1,400), so the file plays back smoothly.

Same timeline as 826 (oath, beam up 18-68, top-down from 28, bottom-up from 60, closed at 228, "2:30 later" breakup),
radius 150 for all three. The beam up is the new L1 laser (834).

| Take | Front |
|---|---|
| D1 snap | blocks pop exactly at a thin bright edge line |
| D2 glowing front | no line: the newest blocks glow and settle over 8 ticks, so the blocks are the front |
| D3 spiral | D2, but each band sweeps round the dome, so the front is a spiral |

**For J:** KEEP / IMPROVE / DROP per take; radius 150 or 75 is still your call.

## J's verdict (2026-10-15)

"D1 for the dome" - KEEP. Hand-off: `docs/handoff/2026-10-15-keep-ultimate-dome/`.
