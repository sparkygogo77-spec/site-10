# Pass v2.0103: reliquary round 4, the designs developed, 12 takes, all green (PC chat, 2026-10-19; J's v2 numbering).
# Why: J on v2.0102: "ports are bigger slightly better on the small ones but it shouldnt have been the main focus of the
#   new round". He picked "Develop the designs" and "All green": two new directions for each 612 pick (KEEP R2a, R4a,
#   R4b; IMPROVE R1c, R6c, R2b), the 2.25x lit port kept on every take.
# Takes: R2d winged arms, R2e four arms; R4d rings round a gilded cage, R4e four rings on a claw stand; R4f crowned
#   gyroscope, R4g wide gimbals held by gold arms; R1d tiered pedestal, R1e fully gilded; R6d turning frame, R6e cage of
#   gold rings; R2f cathedral, R2g arms raising a halo. Voxels: tools/pixel_lanterns15.py. Runs 612's builder.
import os

PASS = "v2.0103"
OUT_NAME = "reliquary_round4.blend"
PL_MODULE = "pixel_lanterns15"
_codes = ["R2d", "R2e", "R4d", "R4e", "R4f", "R4g", "R1d", "R1e", "R6d", "R6e", "R2f", "R2g"]


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
    raise FileNotFoundError("v2.0103 needs 612_reliquary_round.update.py next to it (or KL_REPO set)")


_s612 = _find612()
_t612 = open(_s612, encoding="utf-8").read()
_t612 = _t612.replace('PASS = "612"', "PASS = " + repr(PASS))
_t612 = _t612.replace('OUT_NAME = "reliquary_round.blend"', "OUT_NAME = " + repr(OUT_NAME))
_t612 = _t612.replace('PL_MODULE = "pixel_lanterns12"', "PL_MODULE = " + repr(PL_MODULE))
_t612 = _t612.replace("import pixel_lanterns12 as P12", "import pixel_lanterns15 as P12")
_t612 = _t612.replace('_codes = ["R1a", "R1b", "R1c", "R2a", "R2b", "R2c", "R4a", "R4b", "R4c", "R6a", "R6b", "R6c"]',
                      "_codes = " + repr(_codes))
for must in (repr(PASS), repr(OUT_NAME), repr(PL_MODULE), "import pixel_lanterns15 as P12", repr(_codes)):
    assert must in _t612, must
exec(compile(_t612, _s612, "exec"), globals())
