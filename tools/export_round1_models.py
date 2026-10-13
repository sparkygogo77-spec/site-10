"""Exports J's round-1 Blender picks (2026-10-13) as the Blockbench models the mod draws:

  T3 Pure light (Green) and U3 Pure hope (Blue) construct tools, from Blender passes 204 and 207:
      bbmodel/construct_<tool>_green.bbmodel, bbmodel/construct_<tool>_blue.bbmodel
      (tool = sword, pickaxe, axe, shovel, hoe, hammer)
  B2 Hard-light shell squad armour and the R2 hard-light ravager, from Blender pass 201:
      bbmodel/blue_squad_armour_<role>.bbmodel (role = flyer, flyer_lasso, warrior, rider)
      bbmodel/blue_ravager_r2.bbmodel

and textures/entity/bb/<name>.png. Neighbouring voxels of the same part merge into boxes; every box is one flat
colour per face (box UV, 2 texels per model px). BbModel's prefixes decide how each cube draws:
  "glow_..."            full-bright (rims, inlays, gems, the lance, the bright edges);
  "glass_hardlight_..." translucent and full-bright (BbModel's glass mesh): the see-through hard light. These are
                        the broad faces where J wants the animated construct texture; the flat colour here is
                        its average, painted at the construct textures' alpha (~200), so swap in the animated
                        texture there if the renderer gets that hook;
  anything else         solid, lit, cut-out (the tools' handles).
"core" is avoided on purpose: BbModel treats core cubes as a lantern's pulsing heart.

Axes: Blockbench units = model pixels, +Y up, front faces north (-Z).
  - Tools stand upright: pommel at the bottom, head at the top, the blade flat in the X-Y plane,
    half a pixel per voxel. The pommel gem centre is at y = 1.
  - Armour sits on BlueVillagerModel's boxes: feet at y = 0, one voxel per pixel, one pixel proud of the suit.
  - The ravager is in vanilla-ish proportions, feet at y = 0, facing north.

    python tools/export_round1_models.py src/main/resources/assets/lanternring

It reads the designs straight from the Blender update scripts (needs the bpy wheel to import them headless).
"""
import base64, io, json, math, os, sys, uuid
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
A = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "src/main/resources/assets/lanternring")
ONLY = None
_src = open(os.path.join(HERE, "blockbench_models.py")).read()
exec(_src[_src.index("class Model:"):_src.index("# ---- the Power Battery lantern")])
DENSITY = 2


def flat(rgb, alpha=255):
    c = tuple(int(v) for v in rgb[:3])

    def paint(face, w, h):
        s = {"up": 1.08, "down": 0.8, "north": 1.0, "south": 0.95, "east": 0.92, "west": 0.92}[face]
        cc = tuple(min(255, int(v * s)) for v in c) + (alpha,)
        return [[cc] * w for _ in range(h)]
    return paint


def boxes(cells):
    """Greedy-merge a set of (i, j, k) cells into boxes (i0, j0, k0, i1, j1, k1), inclusive."""
    if not cells:
        return []
    arr = np.array(sorted(cells))
    lo = arr.min(0); hi = arr.max(0)
    m = np.zeros(hi - lo + 1, bool)
    for c in arr:
        m[tuple(c - lo)] = True
    out = []; S = m.shape
    for k in range(S[2]):
        for j in range(S[1]):
            for i in range(S[0]):
                if not m[i, j, k]:
                    continue
                i2 = i
                while i2 + 1 < S[0] and m[i2 + 1, j, k]:
                    i2 += 1
                j2 = j
                while j2 + 1 < S[1] and m[i:i2 + 1, j2 + 1, k].all():
                    j2 += 1
                k2 = k
                while k2 + 1 < S[2] and m[i:i2 + 1, j:j2 + 1, k2 + 1].all():
                    k2 += 1
                m[i:i2 + 1, j:j2 + 1, k:k2 + 1] = False
                out.append((i + lo[0], j + lo[1], k + lo[2], i2 + lo[0], j2 + lo[1], k2 + lo[2]))
    return out


def write_model(name, parts, scale):
    """parts: {cube name prefix: (rgb, set of (x, y_up, z_north) cells)}; scale = model px per cell."""
    m = Model(name, DENSITY)
    n = 0
    for prefix, (rgb, cells) in parts.items():
        for (i, j, k, i2, j2, k2) in boxes(cells):
            frm = [i * scale, j * scale, k * scale]
            to = [(i2 + 1) * scale, (j2 + 1) * scale, (k2 + 1) * scale]
            m.cube(f"{prefix}_{n}", frm, to, flat(rgb, 200 if prefix.startswith("glass") else 255))
            n += 1
    m.write()
    return n


def load(update):
    import bpy  # noqa: F401  (the update scripts build Blender scenes; run them without rendering)
    os.environ["LL_NO_RENDER"] = "1"
    folder = os.environ.get("LL_FOLDER") or os.path.join(ROOT, "build", "ll_export")
    os.makedirs(folder, exist_ok=True)
    g = {"bpy": bpy, "np": np, "FOLDER": folder, "__name__": "export"}
    path = os.path.join(ROOT, "docs/blender/blender_updates", update)
    src = open(path).read()
    # the design code only; stop before the scene is laid out and saved
    cut = src.index("ROWS = {")
    exec(compile(src[:cut], path, "exec"), g)
    return g


# ------------------------------------------------------------------ tools (T3 Green, U3 Blue)
def export_tools():
    total = 0
    for update, corps, pal in (
        ("204_construct_tools.update.py", "green", dict(core=(84, 197, 111), rim=(140, 255, 166), gem=(5, 191, 56),
                                                         inlay=(38, 255, 89), handle=(80, 170, 120))),
        ("207_construct_tools_blue.update.py", "blue", dict(core=(88, 153, 220), rim=(178, 219, 255), gem=(8, 51, 217),
                                                             inlay=(64, 166, 255), handle=(90, 140, 200)))):
        g = load(update)
        R = {g["HANDLE"]: ("handle", pal["handle"]), g["WRAP"]: ("glow_wrap", pal["rim"]),
             g["BAND"]: ("glow_band", pal["rim"]), g["GEM"]: ("glow_gem", pal["gem"]),
             g["CORE"]: ("glass_hardlight", pal["core"]), g["EDGE"]: ("glow_rim", pal["rim"]),
             g["INLAY"]: ("glow_inlay", pal["inlay"]), g["SPINE"]: ("glow_spine", pal["rim"])}
        for tname, fn in g["TOOLS"]:
            D = fn()
            parts = {}
            vmin = min(v for (u, v) in D)
            for (u, v), r in D.items():
                t = g["THICK"][r]
                prefix, rgb = R[r]
                for w in range(-(t // 2), t - t // 2):
                    parts.setdefault(prefix, (rgb, set()))[1].add((u, v - vmin, w))
            total += write_model(f"construct_{tname}_{corps}", parts, 0.5)
    return total


# ------------------------------------------------------------------ B2 armour + R2 ravager
def export_squad():
    g = load("201_squad_armour.update.py")
    V = g["V"]

    def to_parts(vox, tag):
        parts = {}
        for (x, y, z), (rgb, glow, glass, metal) in vox.items():
            prefix = ("glow_" if glow >= 1.0 else "glass_hardlight_" if glass else "") + tag
            key = (prefix, tuple(rgb))
            parts.setdefault(key, set()).add((x, z, y))     # model (x, y back, z up) -> (x, y up, z north)
        named = {}
        for i, ((prefix, rgb), cells) in enumerate(sorted(parts.items(), key=lambda kv: kv[0])):
            named[f"{prefix}{i}"] = (rgb, cells)
        return named

    total = 0
    for role, extra in (("flyer", "wings"), ("flyer_lasso", "lasso"), ("warrior", "hammer"), ("rider", "lance")):
        v = V()
        g["armour"](v, "B2")
        g[extra](v, "B2")
        total += write_model(f"blue_squad_armour_{role}", to_parts(v, "armour_"), 1.0)
    total += write_model("blue_ravager_r2", to_parts(g["ravager"]("B2"), "ravager_"), 1.0)
    return total


if __name__ == "__main__":
    n = export_tools() + export_squad()
    print("cubes written:", n)
