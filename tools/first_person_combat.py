"""First-person combat arms (J, 2026-10-15: "no 1st person animation for the punch currently, no flurry either"):
packs assets/lanternring/poses/first_person_combat.json for FirstPersonCombat.

    python3 tools/first_person_combat.py POSES520_JSON OUT_JSON

POSES520_JSON is docs/blender/review/520_first_person_moves/first_person_moves_poses.json on the Blender branch.
Every pose is in RingFirstPerson's view space (blocks; x right, y up, -z ahead), for a right-handed player:
"r" the ring arm, "l" the free arm, each [fist xyz, elbow xyz, back-of-hand xyz] (the arm runs fist -> elbow).

- "FLURRY" / "FLURRY_BIG": the flying flurry F2 (take A2, pass 509) from pass 520's "02 Flying flurry", vanilla size and
  1.3x. Index 0 is Blender tick 12, the jab, like the third-person take in poses/combat.json (cross at 5, backfist at 12).
- "P1B" / "P1C": pass 502's step-in jab and hook. Pass 520 has no first-person punches, so they are keyed here in pass
  520's vanilla style (its guard, its cross), on the 502 takes' own timing (the same 41 indices as poses/combat4.json):
  P1b guard to 6, out by the hit at 8, held to 10, back by 15; P1c guard to 4, wound out right at 8, swung across into
  the hit at 11, held to 13, back by 19. The free fist stays up in the guard. "_BIG" versions use 520's bigger style.
"""
import json, math, os, sys

P520, OUT = sys.argv[1:3]
moves = json.load(open(P520))["moves"]


def r3(v):
    return [round(x, 3) for x in v]


def arm(a):
    return r3(a["fist"]) + r3(a["elbow"]) + r3(a["back"])


def from520(name, start, end):
    ticks = moves[name]["ticks"][start:end]
    # The free arm is stored mirrored, as if it were a right arm (RingFirstPerson.aimArm mirrors it back).
    def mirror(v):
        return [-v[0], v[1], v[2], -v[3], v[4], v[5], -v[6], v[7], v[8]]
    return [{"r": arm(t["right"]), "l": mirror(arm(t["left"]))} for t in ticks]


GUARD = [0.22, -0.3, -0.7, 0.5, -0.8, -0.4, 0.0, 1.0, 0.0]
JAB = [0.04, -0.08, -1.1, 0.32, -0.42, -0.55, 0.0, 1.0, 0.0]
# The hook: wound out to the right, the fist turned in; then the forearm level across the front, coming in from the right.
WIND = [0.55, -0.18, -0.62, 0.9, -0.45, -0.3, -0.3, 1.0, 0.2]
HOOK = [-0.04, -0.1, -0.98, 0.56, -0.17, -0.88, 0.0, 1.0, 0.2]


def smooth(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    out = [x + (y - x) * t for x, y in zip(a, b)]
    n = math.sqrt(sum(x * x for x in out[6:9])) or 1.0
    out[6:9] = [x / n for x in out[6:9]]
    return out


def keyed(keys, n=41):
    """keys: [(tick, pose)]; smooth steps between them, held outside."""
    out = []
    for i in range(n):
        pose = keys[0][1]
        for (ta, a), (tb, b) in zip(keys, keys[1:]):
            if ta <= i <= tb:
                pose = lerp(a, b, smooth((i - ta) / (tb - ta)))
                break
            if i > tb:
                pose = b
        out.append({"r": r3(pose), "l": r3(GUARD)})
    return out


def bigger(ticks):
    """Pass 520's bigger style for keyed poses: points pulled a quarter closer (the arm is drawn 1.3x)."""
    def big(a):
        return r3([a[0] * 1.08, a[1] * 1.04, a[2] * 0.75, a[3] * 1.08, a[4] * 1.04, a[5] * 0.75] + a[6:9])
    return [{"r": big(t["r"]), "l": big(t["l"])} for t in ticks]


out = {
    "FLURRY": {"scale": 1.0, "ticks": from520("02 Flying flurry - vanilla", 12, 45)},
    "FLURRY_BIG": {"scale": 1.3, "ticks": from520("02 Flying flurry - bigger", 12, 45)},
}
p1b = keyed([(6, GUARD), (8, JAB), (10, JAB), (15, GUARD)])
p1c = keyed([(4, GUARD), (8, WIND), (11, HOOK), (13, HOOK), (19, GUARD)])
out["P1B"] = {"scale": 1.0, "ticks": p1b}
out["P1C"] = {"scale": 1.0, "ticks": p1c}
out["P1B_BIG"] = {"scale": 1.3, "ticks": bigger(p1b)}
out["P1C_BIG"] = {"scale": 1.3, "ticks": bigger(p1c)}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(out, open(OUT, "w"), separators=(",", ":"))
print(OUT, os.path.getsize(OUT))
