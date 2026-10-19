# Pass 612: the reliquary round, 12 takes, with parts that really move (PC chat, 2026-10-19; lanterns 600-699).
# Why: J rated 610 and 611 in chat: the reliquary lives (611 Q1 detailed IMPROVE, Q4 floating IMPROVE "make the rings
#   actually move", Q6 twin IMPROVE "creative i guess", 610 N2g IMPROVE "Looks good for the core maybe a more detailed
#   gold portion", N2r IMPROVE); the shrines and other ideas dropped. He picked "Reliquary round": 3 variations each.
# Takes: R1a gilded net, R1b gem crown, R1c gold foot (from Q1); R2a gold arms, R2b gold arms red, R2c gold shoulders
#   (from N2); R4a three spinning rings, R4b gyroscope, R4c satellites (from Q4: rings move); R6a rocking scales,
#   R6b carousel of three, R6c hourglass (from Q6). Moving parts are their own voxel models (one Blockbench bone each),
#   driven by frame. Voxels: tools/pixel_lanterns12.py. Runs 607's builder (dithered, G3-flare core).
# Builds LanternLive\lanterns\reliquary_round.blend.
import math, os

PASS = "612"
OUT_NAME = "reliquary_round.blend"
PL_MODULE = "pixel_lanterns12"
_codes = ["R1a", "R1b", "R1c", "R2a", "R2b", "R2c", "R4a", "R4b", "R4c", "R6a", "R6b", "R6c"]
LAYOUT_OVERRIDE = {c: (4 * (i % 3), 7 * (i // 3)) for i, c in enumerate(_codes)}


def POST_BUILD():
    import numpy as np
    import pixel_lanterns12 as P12
    import pixel_lanterns10 as P10
    for code in _codes:
        root = bpy.data.objects.get(f"{TAG} {code}")
        corps = P10.CORPS[P12.DESIGNS[code][2]]
        P10.STYLE["hue"] = corps[1]
        mat = MAT
        if corps[1] is not None:                         # a corps colour: its own copy of the material, recoloured core
            mat = MAT.copy(); mat.name = f"{TAG} pixel {corps[0]}"
            mix = next(n for n in mat.node_tree.nodes if n.type == "MIX" and getattr(n, "data_type", "") == "RGBA")
            mix.inputs[6].default_value = (*corps[2], 1); mix.inputs[7].default_value = (*corps[3], 1)
            ob = bpy.data.objects.get(f"{TAG} {code} lantern")
            if ob:
                ob.data.materials[0] = mat
            lamp = bpy.data.objects.get(f"{TAG} {code} lamp")
            if lamp:
                lamp.data.color = tuple(min(1.0, 0.35 + 0.65 * c) for c in corps[2])
        for name, fn, pivot, tilt, axis, expr in P12.MOVING.get(code, []):
            part = fn()
            q, c, k, w = P12.quads(part, P12.MID)
            n = len(q)
            q = q.copy(); q[..., 2] -= P12.MID                 # built round (0, 0, MID): move to the pivot's origin
            me = bpy.data.meshes.new(f"{TAG} {code} {name} mesh")
            me.vertices.add(n * 4)
            me.vertices.foreach_set("co", (q.reshape(-1, 3) / 16.0).astype(np.float32).ravel())
            me.loops.add(n * 4)
            me.loops.foreach_set("vertex_index", np.arange(n * 4, dtype=np.int32))
            me.polygons.add(n)
            me.polygons.foreach_set("loop_start", np.arange(0, n * 4, 4, dtype=np.int32))
            me.update()
            lin = np.concatenate([srgb_to_lin(c), np.ones((n, 1))], 1).astype(np.float32)
            me.color_attributes.new("col", "FLOAT_COLOR", "FACE").data.foreach_set("color", lin.ravel())
            me.attributes.new("kind", "FLOAT", "FACE").data.foreach_set("value", k.astype(np.float32))
            me.attributes.new("glow", "FLOAT", "FACE").data.foreach_set("value", w.astype(np.float32))
            me.materials.append(mat)
            hinge = link(bpy.data.objects.new(f"{TAG} {code} {name} hinge", None))   # fixed tilt
            hinge.parent = root
            hinge.location = (pivot[0] / 16.0, pivot[1] / 16.0, pivot[2] / 16.0)
            hinge.rotation_euler = tuple(math.radians(a) for a in tilt)
            hinge.empty_display_size = 0.05
            mv = link(bpy.data.objects.new(f"{TAG} {code} {name}", me))               # spins in the hinge's frame
            mv.parent = hinge
            drive(mv, "rotation_euler", expr, axis)
            print(code, name, "boxes", P12.model_boxes(part))
        P10.STYLE["hue"] = None
    for code in _codes:                                    # brighter lamps inside (611's "Bigger glow")
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
    raise FileNotFoundError("612 needs 607_pixel_lanterns2.update.py next to it (or KL_REPO set)")


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
