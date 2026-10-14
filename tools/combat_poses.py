"""Packs the Blender combat poses J picked (Chat C, on the Blender branch: docs/blender/review/) into the compact
table the game reads (assets/lanternring/poses/combat.json).

    python3 tools/combat_poses.py SLAM_JSON FLURRY_JSON ROUND4_JSON OUT_JSON

SLAM_JSON is 510_flight_slam4/flight_slam4_poses.json, FLURRY_JSON 509_flying_flurry/flying_flurry_poses.json and
ROUND4_JSON 503_combat_round4/combat_round4_poses.json. Each pose is six parts in the order head, body, ring arm,
free arm, ring leg, free leg (right-handed), each [xRot, yRot, zRot, x, y, z offset px], plus the ring glow "g". The
game's player model has no shins, so each leg is one bend: its pitch is the mean of thigh and shin (as
tools/power_landing_poses.py).

- "slam": per take (H6, H5, H3) the ticks from the trigger to the end of the stand-up; "td" is the touchdown index.
- "flurry": F2 in flight (take A2) from the jab (index 0 = Blender tick 12; cross at 5, backfist at 12), with the
  body's spin about its own axis "s" (radians) for the spinning backfist.
- "absorb": R4's 81-tick loop (brace, catch at 16, hold to 52, release), one pose set (the takes share it) and the
  ring glow of each take.
"""
import json, os, sys

SLAM, FLURRY, ROUND4, OUT = sys.argv[1:5]
PARTS = ("head", "body", "rarm", "larm", "rleg", "lleg")


def part(p, k):
    rot, off = list(p[k]["rot"]), list(p[k]["offset_px"])
    if k in ("rleg", "lleg"):
        shin = p[k.replace("leg", "shin")]["rot"]
        rot[0] = (rot[0] + shin[0]) / 2
    return [round(v, 3) for v in rot + off]


def pose(t):
    return [part(t["parts"], k) for k in PARTS]


out = {"slam": {}, "flurry": {}, "absorb": {}}
slam = json.load(open(SLAM))["takes"]
for name in ("H6", "H5", "H3"):
    take = slam["S3 " + name]
    start = take["trigger"]["trigger_tick"]
    end = take["touchdown_tick"] + take["lock_ticks"] + take["stand_ticks"] + 2
    out["slam"][name] = {"td": take["touchdown_tick"] - start,
                         "ticks": [{"g": t["glow"], "p": pose(t)} for t in take["ticks"][start:end + 1]]}

flurry = json.load(open(FLURRY))["takes"]["A2"]
out["flurry"] = {"ticks": [{"g": t["glow"], "s": round(t["spin_yaw"], 3), "p": pose(t)} for t in flurry["ticks"][12:45]]}

r4 = json.load(open(ROUND4))["takes"]
out["absorb"] = {"ticks": [{"p": pose(t)} for t in r4["R4b"]["ticks"]],
                 "glow": {name: [round(t["glow"], 2) for t in r4[name]["ticks"]] for name in ("R4a", "R4b", "R4c")}}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(out, open(OUT, "w"), separators=(",", ":"))
print(OUT, os.path.getsize(OUT))
