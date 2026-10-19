# Pass 608: six variations of 607 D1b (Vault: molten) (PC chat, 2026-10-19; lanterns 600-699).
# Why: J on 607 D1b: "this one is a keeper, i need more variation". He also found "at a certain angle the lantern is
#   transparent (every single model)": the material was BLENDED (no depth), now DITHERED in 607's builder, fixed here too.
# D1b's DNA in every take: glass vault between fluted gold pillars, gold drips from the roof down the panels and off the
#   eaves, stepped roof, see-through glass with the G3-flare core, the sculpted port. Each take changes one big thing:
#   D1b1 heavy pour, D1b2 hex molten, D1b3 tall molten (spiked crown), D1b4 overflowing bowl, D1b5 caged molten,
#   D1b6 squat molten (deep eaves, four feet). Voxels: tools/pixel_lanterns8.py.
# Runs 607's whole builder with its own module and layout. Builds LanternLive\lanterns\molten_vaults.blend.
import os

PASS = "608"
OUT_NAME = "molten_vaults.blend"
PL_MODULE = "pixel_lanterns8"
LAYOUT_OVERRIDE = {"D1b1": (0, 0), "D1b2": (4, 0), "D1b3": (8, 0), "D1b4": (0, 7), "D1b5": (4, 7), "D1b6": (8, 7)}


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
    raise FileNotFoundError("608 needs 607_pixel_lanterns2.update.py next to it (or KL_REPO set)")


_s607 = _find607()
exec(compile(open(_s607, encoding="utf-8").read(), _s607, "exec"), globals())
