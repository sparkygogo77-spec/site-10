# Pass 610: original lanterns, six new designs, each in green and one other corps colour (PC chat, 2026-10-19).
# Why: J: "make me original lanterns now"; ideas a mixed bag of ancient relics, alien tech and living/organic; colours
#   "Green + one corps"; 12 takes; style "Anything goes". Nothing starts from the Dark Lantern's pinch or the vault.
# Takes: N1 shrine (+ orange), N2 reliquary (+ red), N3 orbital (+ blue), N4 split shell (+ violet), N5 geode (+ yellow),
#   N6 root heart (+ indigo); codes N1g / N1o etc. Voxels: tools/pixel_lanterns10.py (bronze with verdigris, black
#   steel, obsidian, bark, crystal, gold). Runs 607's builder (dithered, G3-flare core); POST_BUILD gives every non-green
#   take its corps colour on the core, glow and lamp.
# Builds LanternLive\lanterns\original_lanterns.blend.
import os

PASS = "610"
OUT_NAME = "original_lanterns.blend"
PL_MODULE = "pixel_lanterns10"
_codes = ["N1g", "N1o", "N2g", "N2r", "N3g", "N3b", "N4g", "N4v", "N5g", "N5y", "N6g", "N6i"]
LAYOUT_OVERRIDE = {c: (4 * (i % 3), 7 * (i // 3)) for i, c in enumerate(_codes)}


def POST_BUILD():
    import pixel_lanterns10 as P10
    for code in _codes:
        corps = P10.CORPS[code[-1]]
        if code.endswith("g"):
            continue
        ob = bpy.data.objects.get(f"{TAG} {code} lantern")
        if ob is None:
            continue
        m = ob.data.materials[0].copy()
        m.name = f"{TAG} pixel {corps[0]}"
        mix = next(n for n in m.node_tree.nodes if n.type == "MIX" and getattr(n, "data_type", "") == "RGBA")
        mix.inputs[6].default_value = (*corps[2], 1)
        mix.inputs[7].default_value = (*corps[3], 1)
        ob.data.materials[0] = m
        lamp = bpy.data.objects.get(f"{TAG} {code} lamp")
        if lamp:
            lamp.data.color = tuple(min(1.0, 0.35 + 0.65 * c) for c in corps[2])


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
    raise FileNotFoundError("610 needs 607_pixel_lanterns2.update.py next to it (or KL_REPO set)")


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
