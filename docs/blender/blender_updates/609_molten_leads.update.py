# Pass 609: J's four 608 leads refined, 3 variations each, drip colour changed up (PC chat, 2026-10-19; lanterns 600-699).
# Why: J circled 608 D1b2 hex, D1b3 tall, D1b5 caged, D1b6 squat; next round "Refine the four (Recommended)"; drip colour
#   "be creative, change it up". Each take keeps its lead's big idea, built differently, and names its drip colour
#   (gold / bright green light / gold cooling to green / dark emerald with gold flecks / milky jade).
# Takes: D1b2a onion dome, D1b2b lancet arches, D1b2c flared skirt; D1b3a belted, D1b3b spire, D1b3c twin chamber;
#        D1b5a lattice, D1b5b domed, D1b5c heavy bars; D1b6a claw feet, D1b6b pagoda, D1b6c fringe.
# Voxels: tools/pixel_lanterns9.py. Runs 607's builder (dithered: solid from every angle) with a 4 x 3 layout.
# Builds LanternLive\lanterns\molten_leads.blend.
import os

PASS = "609"
OUT_NAME = "molten_leads.blend"
PL_MODULE = "pixel_lanterns9"
LAYOUT_OVERRIDE = {"D1b2a": (0, 0), "D1b2b": (4, 0), "D1b2c": (8, 0),
                   "D1b3a": (0, 7), "D1b3b": (4, 7), "D1b3c": (8, 7),
                   "D1b5a": (0, 14), "D1b5b": (4, 14), "D1b5c": (8, 14),
                   "D1b6a": (0, 21), "D1b6b": (4, 21), "D1b6c": (8, 21)}


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
    raise FileNotFoundError("609 needs 607_pixel_lanterns2.update.py next to it (or KL_REPO set)")


_s607 = _find607()
_t607 = open(_s607, encoding="utf-8").read()
# 607 lays out 3 rows; widen its floor, lights and overview camera for 4 rows
_t607 = _t607.replace("(11, 18, 0), (-3, 18, 0)", "(11, 25, 0), (-3, 25, 0)")
_t607 = _t607.replace('("key C", (5, 10, 4.5), 320, 6), ("rim C", (3, 17, 3.5), 220, 6))',
                      '("key C", (5, 10, 4.5), 320, 6), ("rim C", (3, 17, 3.5), 220, 6), ("key D", (5, 17, 4.5), 320, 6), ("rim D", (3, 24, 3.5), 220, 6))')
_t607 = _t607.replace('(14 if " C" in nm else 0)', '(14 if " C" in nm else (21 if " D" in nm else 0))')
_t607 = _t607.replace('cam("Cam all", (4, -11, 7.5), (4, 7.0, 0.6), 30)', 'cam("Cam all", (4, -13, 9.5), (4, 10.5, 0.6), 28)')
_t607 = _t607.replace('"(11, 18, 0)", "(4, -11, 7.5)"', '"(11, 25, 0)", "(4, -13, 9.5)"')    # 607's own checks
for must in ("(11, 25, 0)", "key D", '(21 if " D" in nm', "(4, -13, 9.5)"):
    assert must in _t607, must
exec(compile(_t607, _s607, "exec"), globals())
