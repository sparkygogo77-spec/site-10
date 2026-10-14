"""Packs the Blender power landing poses (hand-off docs/handoff/2026-10-14-power-landing/poses/ on the Blender
branch) into the compact table the game reads (assets/lanternring/poses/power_landing.json).

    python3 tools/power_landing_poses.py POSES_DIR OUT_JSON

Each take keeps its ticks from touchdown on (index 0 = touchdown), each six parts in the order head, body, ring
arm, free arm, ring leg, free leg (right-handed), each [xRot, yRot, zRot, x, y, z offset px], plus the ring glow.
The game's player model has no shins, so each leg is one bend: its pitch is the mean of thigh and shin, its yaw,
roll and offset the thigh's (as tools/movement_flight_poses.py).
"""
import json, os, sys

SRC, OUT = sys.argv[1], sys.argv[2]
PARTS = ("head", "body", "rarm", "larm", "rleg", "lleg")
TAKES = {"A3": "A3_dissolve.json", "B2": "B2_plough.json", "D0": "D0_stop_dead.json"}


def part(p, k):
    rot, off = list(p[k]["rot"]), list(p[k]["offset_px"])
    if k in ("rleg", "lleg"):
        shin = p[k.replace("leg", "shin")]["rot"]
        rot[0] = (rot[0] + shin[0]) / 2
    return [round(v, 4) for v in rot + off]


out = {}
for name, file in TAKES.items():
    take = json.load(open(os.path.join(SRC, file)))
    ticks = take["ticks"][take["touchdown_tick"]:]
    out[name] = {"slide": take["slide_ticks"], "ticks": [{"g": t["glow"], "p": [part(t["parts"], k) for k in PARTS]} for t in ticks]}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(out, open(OUT, "w"), separators=(",", ":"))
print(OUT, os.path.getsize(OUT))
