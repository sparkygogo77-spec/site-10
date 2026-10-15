"""Packs J's pass 502 combat poses round 4 and pass 505 dash strike KEEPs (Chat C, on the Blender branch:
docs/blender/review/) into the table the game reads (assets/lanternring/poses/combat4.json).

    python3 tools/combat_poses4.py POSES502_JSON POSES505_JSON OUT_JSON

POSES502_JSON is 502_combat_poses4/combat_poses4_poses.json, POSES505_JSON 505_dash_strike5/dash_strike5_poses.json.
Each pose is six parts in the order head, body, ring arm, free arm, ring leg, free leg (right-handed), each
[xRot, yRot, zRot, x, y, z offset px], plus the ring glow "g" and the body's step forward "f" (blocks). The game's
player model has no shins, so each leg is one bend: its pitch is the mean of thigh and shin (as tools/combat_poses.py).

- "P1B" step-in jab, "P1C" hook, "P2B" blast with the free hand following 25%, "P5A" wall with the free arm relaxed:
  each its whole 40-tick loop (41 ticks, the last the first again); CombatPoses plays the window it needs.
- "R3A3" the flying ring fist dash strike: its first 41 ticks (dash ticks 10-13, the hit at 14, the arms down by 27).
"""
import json, os, sys

P502, P505, OUT = sys.argv[1:4]
PARTS = ("head", "body", "rarm", "larm", "rleg", "lleg")


def part(p, k):
    rot, off = list(p[k]["rot"]), list(p[k]["offset_px"])
    if k in ("rleg", "lleg"):
        shin = p[k.replace("leg", "shin")]["rot"]
        rot[0] = (rot[0] + shin[0]) / 2
    return [round(v, 3) for v in rot + off]


def pack(ticks):
    return {"ticks": [{"g": round(t["glow"], 2), "f": round(t["fwd_blocks"], 3), "p": [part(t["parts"], k) for k in PARTS]}
                      for t in ticks]}


out = {}
t502 = json.load(open(P502))["takes"]
for name in ("P1b", "P1c", "P2b", "P5a"):
    out[name.upper()] = pack(t502[name]["ticks"])
t505 = json.load(open(P505))["takes"]
out["R3A3"] = pack(t505["R3a-3"]["ticks"][:41])

os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(out, open(OUT, "w"), separators=(",", ":"))
print(OUT, os.path.getsize(OUT))
