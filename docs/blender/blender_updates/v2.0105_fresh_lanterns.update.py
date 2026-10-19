# Pass v2.0105: fresh lanterns, 12 new designs in green (PC chat, 2026-10-19; J's v2 numbering, v2.0104 is ring-models').
# Why: J dropped all 12 of v2.0103 ("Didnt like all 12"), asked for "New stuff" and picked "Fresh lantern designs":
#   new silhouettes that are not reliquaries, voxel pixel art with polished gold, the lit port kept at the v2.0102 size.
# Takes: F1 classic battery, F2 pagoda, F3 storm lantern, F4 faceted gem, F5 crescent moon, F6 obelisk, F7 hanging bell,
#   F8 pierced star lamp, F9 chalice, F10 clockwork, F11 lighthouse, F12 seed pod. Voxels: tools/pixel_lanterns16.py.
#   Runs 612's builder (607 dithered glass, G3-flare core).
import os

PASS = "v2.0105"
OUT_NAME = "fresh_lanterns.blend"
PL_MODULE = "pixel_lanterns16"
_codes = ["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12"]


def _find612():
    names = []
    if os.environ.get("KL_REPO"):
        names.append(os.path.join(os.environ["KL_REPO"], "docs", "blender", "blender_updates"))
    if "__file__" in globals():
        names.append(os.path.dirname(os.path.abspath(__file__)))
    names.append(os.path.join(os.path.expanduser("~"), "Documents", "LanternLive", "site-10", "docs", "blender", "blender_updates"))
    names.append("/home/claude/site-10/docs/blender/blender_updates")
    for d in names:
        p = os.path.join(d, "612_reliquary_round.update.py")
        if os.path.exists(p):
            return p
    raise FileNotFoundError("v2.0105 needs 612_reliquary_round.update.py next to it (or KL_REPO set)")


_s612 = _find612()
_t612 = open(_s612, encoding="utf-8").read()
_t612 = _t612.replace('PASS = "612"', "PASS = " + repr(PASS))
_t612 = _t612.replace('OUT_NAME = "reliquary_round.blend"', "OUT_NAME = " + repr(OUT_NAME))
_t612 = _t612.replace('PL_MODULE = "pixel_lanterns12"', "PL_MODULE = " + repr(PL_MODULE))
_t612 = _t612.replace("import pixel_lanterns12 as P12", "import pixel_lanterns16 as P12")
_t612 = _t612.replace('_codes = ["R1a", "R1b", "R1c", "R2a", "R2b", "R2c", "R4a", "R4b", "R4c", "R6a", "R6b", "R6c"]',
                      "_codes = " + repr(_codes))
for must in (repr(PASS), repr(OUT_NAME), repr(PL_MODULE), "import pixel_lanterns16 as P12", repr(_codes)):
    assert must in _t612, must
exec(compile(_t612, _s612, "exec"), globals())
