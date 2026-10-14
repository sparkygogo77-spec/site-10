"""Packs the lead Blender chat's charge takes (docs/handoff/2026-10-14-lantern-charge/poses/kneel_lean4_poses.json on
branch claude/lantern-redesign-pass2) into the compact file the mod reads (ChargeTakes): only the picked takes, one
row per tick of [rx, ry, rz, ox, oy, oz] for each part (radians; model px from the vanilla pivot), plus the lantern's
tilt (standing on its block) or swing (hanging from the handle).

    python tools/charge_takes_json.py kneel_lean4_poses.json src/client/resources/assets/lanternring/poses/charge_takes.json
"""
import json, sys

PARTS = ("head", "body", "rarm", "larm", "rleg", "lleg", "rshin", "lshin")
PICKED = ("L1c", "K3c")

src = json.load(open(sys.argv[1]))
out = {"parts": list(PARTS), "takes": {}}
for name in PICKED:
    take = src["takes"][name]
    t = {"lantern": take["lantern"], "carry_from_tick": take["carry_from_tick"], "parts": [], "tilt": [], "swing": []}
    for tick in take["ticks"]:
        t["parts"].append([[round(v, 4) for v in tick["parts"][p]["rot"] + tick["parts"][p]["offset_px"]] for p in PARTS])
        t["tilt"].append(round(tick.get("tilt", 0.0), 4))
        t["swing"].append([round(v, 4) for v in tick.get("swing", [0.0, 0.0])])
    out["takes"][name] = t
json.dump(out, open(sys.argv[2], "w"), separators=(",", ":"))
print("wrote", sys.argv[2], {k: len(v["parts"]) for k, v in out["takes"].items()})
