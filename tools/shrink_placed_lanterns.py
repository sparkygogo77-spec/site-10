"""Shrinks the placed lantern block models to the size the lantern is in your hand (J, report #2: "the lantern is
HUGE when set down"). tools/bbmodel_json.py writes each lantern a full block tall; this scales it about the middle of
its base so it stands as tall as the held one (LanternFirstPerson.scale x the look's size x its handle height), and
grows the display transforms by as much, so inventory icons, item frames and dropped items stay as they were.

    python tools/shrink_placed_lanterns.py src/main/resources/assets/lanternring

Run it after tools/bbmodel_json.py. Running it twice changes nothing (it works from the model's current height).
Keep PowerBatteryBlock.SHAPE in step with the tallest of these.
"""
import glob, json, math, os, sys

A = sys.argv[1] if len(sys.argv) > 1 else "src/main/resources/assets/lanternring"
HAND = 0.42  # LanternFirstPerson.scale
# (size, handleTop) per look, from LanternFirstPerson's Look records: the held lantern stands HAND * size * handleTop px.
LOOKS = {
    "power_battery": (1.0, 20.0), "dark_lantern": (0.74, 28.5), "classic_lantern": (0.88, 22.0),
    "red_lantern": (0.72, 27.3), "red_battery": (0.42, 51.5), "blue_lantern": (0.72, 26.5),
    "yellow_lantern": (0.8, 24.5), "violet_lantern": (0.85, 20.0), "orange_lantern": (0.85, 16.2),
    "stone_lantern": (0.88, 22.0), "torus_lantern": (0.85, 24.0), "nebula_lantern": (0.85, 21.0),
    "compact_lantern": (0.85, 18.0),
}


def look(name):
    for key in sorted(LOOKS, key=len, reverse=True):
        if name == key or name.startswith(key + "_"):
            return LOOKS[key]
    return None


def r(v):
    return round(v, 4)


def rot(v, deg):
    """Minecraft display rotation of vector v: rotationXYZ, so Rx Ry Rz (z turns first)."""
    x, y, z = v
    a, b, c = (math.radians(d) for d in deg)
    x, y = x * math.cos(c) - y * math.sin(c), x * math.sin(c) + y * math.cos(c)
    x, z = x * math.cos(b) + z * math.sin(b), -x * math.sin(b) + z * math.cos(b)
    y, z = y * math.cos(a) - z * math.sin(a), y * math.sin(a) + z * math.cos(a)
    return x, y, z


def shrink(path, size, top):
    with open(path) as f:
        m = json.load(f)
    els = m.get("elements")
    if not els:
        return
    ys = [v for e in els for v in (e["from"][1], e["to"][1])]
    h = max(ys) - min(ys)
    want = HAND * size * top
    f = want / h
    if abs(f - 1) < 1e-3:
        return
    p = lambda v: [r(8 + (v[0] - 8) * f), r(v[1] * f), r(8 + (v[2] - 8) * f)]
    for e in els:
        e["from"], e["to"] = p(e["from"]), p(e["to"])
        if "rotation" in e and "origin" in e["rotation"]:
            e["rotation"]["origin"] = p(e["rotation"]["origin"])
    # The display transforms scale about the block's middle (8, 8, 8): grow them back by 1/f and move the lantern's
    # middle back to where it was drawn before.
    for d in (m.get("display") or {}).values():
        s = d.get("scale", [1, 1, 1])
        mid_old = (0.0, (min(ys) + max(ys)) / 2 - 8, 0.0)
        mid_new = (0.0, (min(ys) + max(ys)) / 2 * f - 8, 0.0)
        a = rot([mid_old[i] * s[i] for i in range(3)], d.get("rotation", [0, 0, 0]))
        b = rot([mid_new[i] * s[i] / f for i in range(3)], d.get("rotation", [0, 0, 0]))
        t = d.get("translation", [0, 0, 0])
        d["translation"] = [r(max(-80, min(80, t[i] + a[i] - b[i]))) for i in range(3)]
        d["scale"] = [r(min(4, v / f)) for v in s]
    with open(path, "w") as out:
        json.dump(m, out, indent="\t")
        out.write("\n")
    print(f"{os.path.basename(path)}: {r(h)} -> {r(want)} px")


for path in sorted(glob.glob(f"{A}/models/block/*.json")):
    name = os.path.basename(path)[:-5]
    lk = look(name)
    if lk:
        shrink(path, *lk)
