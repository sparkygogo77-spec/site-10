# Pass v2.0101: reliquary round 2, 12 takes (PC chat, 2026-10-19; lanterns, first pass of J's v2 numbering).
# Why: J rated 612 in chat: KEEP R2a gold arms, R4a spinning rings, R4b gyroscope; IMPROVE R1c gold foot, R6c hourglass,
#   R2b red ("Cant see the port on any of these, maybe want darker red for lantern red in this visual so it looks near
#   metallic like the dark lantern"). J asked for v2 numbers ("Start doing v.2 .01xx"): this is v2.0101, after 612.
# Takes: two of each, 1 = green as kept, 2 = near-black metallic crimson with polished gold; R2b1 crimson with a glass
#   window, R2b2 crimson with gold shoulders. Every take: the port 1.5x, raised 1 px and lit (glowing ring + socket).
#   R1c adds an engraved collar with lit gems and gold wire; R6c a heavier gold waist and gold-wound posts.
# Voxels: tools/pixel_lanterns13.py. Runs 612's builder (moving rings on R4a/R4b, 607 dithered glass, G3-flare core).
# Builds LanternLive\lanterns\reliquary_round2.blend.
import os

PASS = "v2.0101"
OUT_NAME = "reliquary_round2.blend"
PL_MODULE = "pixel_lanterns13"
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
    raise FileNotFoundError("v2.0101 needs 612_reliquary_round.update.py next to it (or KL_REPO set)")


_s612 = _find612()
_t612 = open(_s612, encoding="utf-8").read()
_t612 = _t612.replace('PASS = "612"', "PASS = " + repr(PASS))
_t612 = _t612.replace('OUT_NAME = "reliquary_round.blend"', "OUT_NAME = " + repr(OUT_NAME))
_t612 = _t612.replace('PL_MODULE = "pixel_lanterns12"', "PL_MODULE = " + repr(PL_MODULE))
_t612 = _t612.replace("import pixel_lanterns12 as P12", "import pixel_lanterns13 as P12")
_t612 = _t612.replace('_codes = ["R1a", "R1b", "R1c", "R2a", "R2b", "R2c", "R4a", "R4b", "R4c", "R6a", "R6b", "R6c"]',
                      "_codes = " + repr(_codes))
for must in (repr(PASS), repr(OUT_NAME), repr(PL_MODULE), "import pixel_lanterns13 as P12", repr(_codes)):
    assert must in _t612, must
exec(compile(_t612, _s612, "exec"), globals())
