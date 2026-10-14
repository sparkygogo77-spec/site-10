"""Packs the Blender double-jump take-off and soft landing poses (pass 403, hand-off
docs/handoff/2026-10-14-bundle-jar/poses/ on the Blender branch) into the compact table the game reads
(assets/lanternring/poses/takeoff_landing.json).

    python3 tools/takeoff_landing_poses.py POSES_DIR OUT_JSON

Each pose is six parts (head, body, ring arm, free arm, ring leg, free leg; right-handed), each
[xRot, yRot, zRot, x, y, z offset px], legs folded to one bend as tools/movement_flight_poses.py does.

- "stand": S1 from the second jump's burst (tick 12) into the hero hover (S1, S2a and S2b share their poses; only
  the height curve differs, which the game works out itself).
- "dart": R3 A2 from the burst (tick 19) until it is laid out flat (tick 30).
- "free": the free arm's [xRot, zRot] per dart tick for A1 and A3 (A2 is in "dart").
- "land": the pass 405 double-tap landings L4, L5 and L6, each from the tap (index 0, Blender tick 15): "p" the
  poses, "touch" the touchdown index (the burst), "f" how far along the take's carry and "u" how much of the height
  is left per tick (0..1). Brake, drop straight in, absorb crouch, stand; no run-out. (Pass 403's L2 is dropped.)
"""
import json, os, sys

SRC, OUT = sys.argv[1], sys.argv[2]
PARTS = ("head", "body", "rarm", "larm", "rleg", "lleg")


def part(p, k):
    rot, off = list(p[k]["rot"]), list(p[k]["offset_px"])
    if k in ("rleg", "lleg"):
        shin = p[k.replace("leg", "shin")]["rot"]
        rot[0] = (rot[0] + shin[0]) / 2
    return [round(v, 3) for v in rot + off]


def pose(t):
    return [part(t["parts"], k) for k in PARTS]


def take(name):
    return json.load(open(os.path.join(SRC, f"403_{name}.json")))


s1 = take("S1")


def landing(name):
    t = json.load(open(os.path.join(SRC, f"405_{name}.json")))
    ticks, tap = t["ticks"], 15
    f0, h0 = ticks[tap]["pos"][1], ticks[tap]["pos"][2]
    carry = ticks[-1]["pos"][1] - f0
    span = ticks[tap:tap + 21]
    return {
        "p": [pose(k) for k in span],
        "touch": t["burst_tick"] - tap,
        "f": [round((k["pos"][1] - f0) / carry, 3) if carry > 1e-6 else 1.0 for k in span],
        "u": [round(k["pos"][2] / h0, 3) for k in span],
        "carry": round(carry, 3),
    }
dart = {a: take(f"R3{a}") for a in ("A1", "A2", "A3")}
b = s1["burst_tick"]
r = dart["A2"]["burst_tick"]
out = {
    "stand": [pose(t) for t in s1["ticks"][b:b + 23]],
    "dart": [pose(t) for t in dart["A2"]["ticks"][r:r + 12]],
    "free": {a: [[round(t["parts"]["larm"]["rot"][0], 3), round(t["parts"]["larm"]["rot"][2], 3)] for t in dart[a]["ticks"][r:r + 12]]
             for a in ("A1", "A3")},
    "land": {n: landing(n) for n in ("L4", "L5", "L6")},
}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(out, open(OUT, "w"), separators=(",", ":"))
print(OUT, os.path.getsize(OUT))
