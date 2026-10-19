# Pass v2.0102: reliquary round 3, 12 takes (PC chat, 2026-10-19; lanterns, J's v2 numbering).
# Why: after v2.0101 (port 1.5x), J asked to build the next pass now: "Make the lit port BIGGER", on the KEEP takes
#   (R2a, R4a, R4b) too, and the red near-black crimson. J's picks: port 2.25x, raised (★), 1 green + 1 crimson of each.
# Takes: R2a, R4a, R4b (KEEP), R1c, R6c, R2b (IMPROVE): 1 = green, 2 = near-black metallic crimson with polished gold;
#   R2b1 = gold arms and shoulders in green, R2b2 = the crimson glass window. Every take: port 2.25x, lifted 1 px, brighter.
# Voxels: tools/pixel_lanterns14.py (on pixel_lanterns13). Runs 612's builder (moving rings on R4a/R4b).
# Builds LanternLive\lanterns\reliquary_round3.blend.
import os

PASS = "v2.0102"
OUT_NAME = "reliquary_round3.blend"
PL_MODULE = "pixel_lanterns14"
_codes = ["R2a1", "R2a2", "R2b1", "R4a1", "R4a2", "R2b2", "R4b1", "R4b2", "R1c1", "R1c2", "R6c1", "R6c2"]


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
    raise FileNotFoundError("v2.0102 needs 612_reliquary_round.update.py next to it (or KL_REPO set)")


_s612 = _find612()
_t612 = open(_s612, encoding="utf-8").read()
_t612 = _t612.replace('PASS = "612"', "PASS = " + repr(PASS))
_t612 = _t612.replace('OUT_NAME = "reliquary_round.blend"', "OUT_NAME = " + repr(OUT_NAME))
_t612 = _t612.replace('PL_MODULE = "pixel_lanterns12"', "PL_MODULE = " + repr(PL_MODULE))
_t612 = _t612.replace("import pixel_lanterns12 as P12", "import pixel_lanterns14 as P12")
_t612 = _t612.replace('_codes = ["R1a", "R1b", "R1c", "R2a", "R2b", "R2c", "R4a", "R4b", "R4c", "R6a", "R6b", "R6c"]',
                      "_codes = " + repr(_codes))
for must in (repr(PASS), repr(OUT_NAME), repr(PL_MODULE), "import pixel_lanterns14 as P12", repr(_codes)):
    assert must in _t612, must
exec(compile(_t612, _s612, "exec"), globals())
