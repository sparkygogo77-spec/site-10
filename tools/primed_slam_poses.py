"""Packs J's pass 518 primed slam poses (Chat C, on the Blender branch: docs/blender/review/518_primed_slam/
primed_slam_poses.json) into assets/lanternring/poses/primed_slam.json.

    python3 tools/primed_slam_poses.py PRIMED_JSON OUT_JSON

Each pose is six parts in the order head, body, ring arm, free arm, ring leg, free leg (right-handed), each
[xRot, yRot, zRot, x, y, z offset px], plus the ring glow "g"; each leg is one bend (the mean of thigh and shin, as
tools/combat_poses.py).

- "P1" (the primed flight slam, shift) and "P2" (the primed super-jump slam, crouch): from the prime to the stand,
  "td" the touchdown index.
- "P1_rebuild" and "P2_rebuild": the ring arm pointing at the crater to rebuild it (from the click).
"""
import json, os, sys

SRC, OUT = sys.argv[1:3]
PARTS = ("head", "body", "rarm", "larm", "rleg", "lleg")
# Per take: (first tick, last tick) of the slam, and of the rebuild gesture.
SPANS = {"P1": ((18, 54), (66, 96)), "P2": ((40, 82), (90, 122))}


def part(p, k):
    rot, off = list(p[k]["rot"]), list(p[k]["offset_px"])
    if k in ("rleg", "lleg"):
        shin = p[k.replace("leg", "shin")]["rot"]
        rot[0] = (rot[0] + shin[0]) / 2
    return [round(v, 3) for v in rot + off]


def ticks(take, a, b):
    return [{"g": round(t["glow"], 2), "p": [part(t["parts"], k) for k in PARTS]} for t in take["ticks"][a:b + 1]]


takes = json.load(open(SRC))["takes"]
out = {}
for name, ((a, b), (ra, rb)) in SPANS.items():
    take = takes[name]
    out[name] = {"td": take["touchdown_tick"] - a, "ticks": ticks(take, a, b)}
    out[name + "_rebuild"] = {"ticks": ticks(take, ra, rb)}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(out, open(OUT, "w"), separators=(",", ":"))
print(OUT, os.path.getsize(OUT))
