# Pass 611: the 610 relics taken further, 12 green takes (PC chat, 2026-10-19; lanterns 600-699).
# Why: J on 610: build on "Relics" (N1 shrine, N2 reliquary); change "More detail", "Bigger glow", "Mix the ideas",
#   "Smaller port"; "All green"; "12 total". Six shrines, six reliquaries: a detailed take of each, then crosses with 610's
#   other ideas (roots, crystals, floating rings, split shell) and a ruin / second storey / twin balance. Glow x1.5, light
#   leaking from windows, seams and cracks, a bigger core, a small port. Voxels: tools/pixel_lanterns11.py.
# Builds LanternLive\lanterns\relic_lanterns.blend.
import os

PASS = "611"
OUT_NAME = "relic_lanterns.blend"
PL_MODULE = "pixel_lanterns11"
_codes = ["S1", "S2", "S3", "S4", "S5", "S6", "Q1", "Q2", "Q3", "Q4", "Q5", "Q6"]
LAYOUT_OVERRIDE = {c: (4 * (i % 3), 7 * (i // 3)) for i, c in enumerate(_codes)}


def POST_BUILD():
    for code in _codes:                                    # "Bigger glow": brighter lamps inside
        lamp = bpy.data.objects.get(f"{TAG} {code} lamp")
        if lamp:
            lamp.data.driver_remove("energy")
            drive(lamp.data, "energy", "4.0 * (" + CHARGE + ")")


def _find607():
    names = []
    if os.environ.get("KL_REPO"):
        names.append(os.path.join(os.environ["KL_REPO"], "docs", "blender", "blender_updates"))
    if "__file__" in globals():
        names.append(os.path.dirname(os.path.abspath(__file__)))
    names.append(os.path.join(os.path.expanduser("~"), "Documents", "LanternLive", "site-10", "docs", "blender", "blender_updates"))
    names.append("/home/claude/site-10/docs/blender/blender_updates")
    for d in names:
        p = os.path.join(d, "607_pixel_lanterns2.update.py")
        if os.path.exists(p):
            return p
    raise FileNotFoundError("611 needs 607_pixel_lanterns2.update.py next to it (or KL_REPO set)")


_s607 = _find607()
_t607 = open(_s607, encoding="utf-8").read()
_t607 = _t607.replace("(11, 18, 0), (-3, 18, 0)", "(11, 25, 0), (-3, 25, 0)")
_t607 = _t607.replace('("key C", (5, 10, 4.5), 320, 6), ("rim C", (3, 17, 3.5), 220, 6))',
                      '("key C", (5, 10, 4.5), 320, 6), ("rim C", (3, 17, 3.5), 220, 6), ("key D", (5, 17, 4.5), 320, 6), ("rim D", (3, 24, 3.5), 220, 6))')
_t607 = _t607.replace('(14 if " C" in nm else 0)', '(14 if " C" in nm else (21 if " D" in nm else 0))')
_t607 = _t607.replace('cam("Cam all", (4, -11, 7.5), (4, 7.0, 0.6), 30)', 'cam("Cam all", (4, -13, 9.5), (4, 10.5, 0.6), 28)')
_t607 = _t607.replace('"(11, 18, 0)", "(4, -11, 7.5)"', '"(11, 25, 0)", "(4, -13, 9.5)"')
for must in ("(11, 25, 0)", "key D", '(21 if " D" in nm', "(4, -13, 9.5)"):
    assert must in _t607, must
exec(compile(_t607, _s607, "exec"), globals())
