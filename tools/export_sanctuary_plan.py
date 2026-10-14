"""Writes a Hope sanctuary take as a block plan for the game, in the same format as the round-1 A3 hand-off
(docs/handoff/2026-10-13-round1-picks/hope_sanctuary_A3.json):

    python tools/export_sanctuary_plan.py A6 OUT.json      (needs the bpy wheel; takes A3..A6 from pass 210)

It runs the design code of docs/blender/blender_updates/210_hope_sanctuary2.update.py headless and records every
voxel object a take builds (the structure, its turbine and the turbine's mark). Blender (x, y, z up) maps to
Minecraft [x, z_up -> y, y -> z]; the stand-in mobs and flyers are left out (the game spawns its own).
"""
import json, os, sys
import numpy as np
import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
TAKE, OUT = sys.argv[1], sys.argv[2]
src = open(os.path.join(HERE, "..", "docs/blender/blender_updates/210_hope_sanctuary2.update.py")).read()
src = src[:src.index("# ================================================================ scene")]
os.environ["LL_NO_RENDER"] = "1"
g = {"bpy": bpy, "np": np, "FOLDER": os.environ.get("LL_FOLDER", "/tmp"), "__name__": "plan"}   # LL_FOLDER: a Lantern Live folder holding hope_tex/
exec(compile(src, "210_hope_sanctuary2", "exec"), g)
NAMES = {v: k for k, v in g["MI"].items()}
seen = []
real = g["voxel_object"]


def record(name, V, origin=(0, 0, 0)):
    o = real(name, V, origin)
    seen.append((name, dict(V), tuple(origin), o))
    return o


g["voxel_object"] = record
g["herd_on_tiers"] = lambda *a, **k: None
g["flyers"] = lambda *a, **k: None
g["take_" + TAKE.lower()](0)
parts = {}
for name, V, origin, o in seen:
    if o.parent is not None:
        par = next(n for n, _, _, oo in seen if oo is o.parent)
        ox, oy, oz = (o.parent.location.x, o.parent.location.y, o.parent.location.z)
    else:
        par, (ox, oy, oz) = None, origin
    blocks = sorted([int(x + ox), int(z + oz), int(y + oy), NAMES[m]] for (x, y, z), m in V.items())
    label = name.replace("HS ", "")
    moving = "turbine" in name
    note = ""
    if moving and par is None:
        note = f"spins about its vertical axis, one turn every 20 s; its blocks are placed with y from {int(oz)} (it sits at {oz} in Blender)"
    elif par:
        note = f"the Hope mark plates through the turbine's hub; they spin with the turbine (parent: {par.replace('HS ', '')})"
    counts = {}
    for b in blocks:
        counts[b[3]] = counts.get(b[3], 0) + 1
    parts[label] = {"moving": moving, "note": note, "counts": counts, "blocks": blocks}
json.dump({"take": f"hope_sanctuary_{TAKE}",
           "axes": "Minecraft axes: [x, y, z] with y up from the structure's floor (0 = floor level, negatives hang below), x east, z south; origin at the structure's centre. The tower's front stairs face north (-z).",
           "block_names": "texture names used in Blender: mod blocks by their texture id, vanilla blocks by id",
           "parts": parts}, open(OUT, "w"), separators=(",", ":"))
print({k: sum(v["counts"].values()) for k, v in parts.items()})
