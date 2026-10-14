"""Packs the Blender movement and flight poses (hand-off docs/handoff/2026-10-14-movement-flight/poses/ on the
Blender branch) into the compact table the game reads (assets/lanternring/poses/movement_flight.json).

    python3 tools/movement_flight_poses.py POSES_DIR OUT_JSON

The game's player model has no shins, so each leg is one bend: its pitch is the mean of thigh and shin (the hip to
foot direction for two equal halves), its yaw, roll and offset the thigh's. Each tick is six parts in the order
head, body, ring arm, free arm, ring leg, free leg (right-handed), each [xRot, yRot, zRot, x, y, z offset px].
Sprint keeps one 12-tick stride (the cycle repeats every stride); takeoff keeps F2 from the plant (tick 24);
ground flight keeps H1-H3 from tick 15 (laying out) on.
"""
import json, os, sys

SRC, OUT = sys.argv[1], sys.argv[2]
PARTS = ("head", "body", "rarm", "larm", "rleg", "lleg")


def part(p, k):
    rot, off = list(p[k]["rot"]), list(p[k]["offset_px"])
    if k in ("rleg", "lleg"):
        shin = p[k.replace("leg", "shin")]["rot"]
        rot[0] = (rot[0] + shin[0]) / 2
    return [round(v, 4) for v in rot + off]


def pose(p):
    return [part(p, k) for k in PARTS]


out = {}
sprint = json.load(open(os.path.join(SRC, "sprint_run2_poses.json")))["takes"]
out["sprint"] = {k: [pose(t) for t in sprint[k]["ticks"][:12]] for k in ("S5a", "S5b")}
take = json.load(open(os.path.join(SRC, "flight_takeoff_poses.json")))["takes"]["F2"]["ticks"][24:]
f0, u0 = take[0]["forward"], take[0]["up"]
out["takeoff"] = [{"f": round(t["forward"] - f0, 3), "u": round(t["up"] - u0, 3), "g": t["glow"], "p": pose(t["parts"])} for t in take]
ground = json.load(open(os.path.join(SRC, "ground_flight_poses.json")))
out["ground"] = {}
for k, t in ground["takes"].items():
    ticks = t["ticks"][15:]
    out["ground"][k] = {"hit": t["hit_tick"] - 15, "stop": t["stop_ticks"], "depth": t["crater_depth"],
                        "ticks": [{"f": x["forward"], "g": x["glow"], "a": x["dome_alpha"], "s": x["dome_squash"], "p": pose(x["parts"])} for x in ticks]}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(out, open(OUT, "w"), separators=(",", ":"))
print(OUT, os.path.getsize(OUT))
