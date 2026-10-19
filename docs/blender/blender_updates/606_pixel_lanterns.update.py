# Pass 606: new pixel lanterns with polished gold (PC chat, 2026-10-18; lanterns 600-699).
# Why: J dropped every smooth take of 604 and 605: "do new lanterns, the depth of the dark lantern is just the level of
#   complexity and pixelated design, but of course i was expecting a more polished version of the gold on them"; he
#   ticked "too smooth, want pixel art" and "too plain / too toy-like".
# So: six new designs on the Dark Lantern's own grid (0.25 px voxels) with its glass (glassy ribs, crazed middle with
#   proud plates and gold veins, branching gold lightning, dark dashed stitches), and polished gold (lit lips, the mid
#   tone following the light, a specular column, deep undersides, engraved lines). Voxels come from
#   tools/pixel_lanterns6.py, the same format a Blockbench export takes (box counts printed per take).
# Takes: D1 Vault, D2 Bell, D3 Gourd, D4 Hex classic, D5 Crystal, D6 Armillary (see tools/pixel_lanterns6.py).
# Each turns once in 120 frames; idle glow 12% to frame 20, the charge fills by 80, holds. Glow gathers round the port.
# Cameras "Cam <code> <name>", "Cam all". Builds LanternLive\lanterns\pixel_lanterns.blend.
import math, os, sys
import bpy
import numpy as np


def _find(rel):
    names = []
    if os.environ.get("KL_REPO"):
        names.append(os.environ["KL_REPO"])
    if "__file__" in globals():
        names.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
    names.append(os.path.join(os.path.expanduser("~"), "Documents", "LanternLive", "site-10"))
    names.append("/home/claude/site-10")
    for d in names:
        p = os.path.join(d, *rel.split("/"))
        if os.path.exists(p):
            return p
    raise FileNotFoundError("606 needs " + rel + " (set KL_REPO)")


PASS = "606"
OUT_NAME = "pixel_lanterns.blend"
_s604 = _find("docs/blender/blender_updates/604_lantern_models_proper.update.py")
_t604 = open(_s604, encoding="utf-8").read()
exec(compile(_t604[:_t604.index("# ---- 604 takes")], _s604, "exec"), globals())       # scene, drive, take, CHARGE
sys.path.insert(0, os.path.dirname(_find("tools/pixel_lanterns6.py")))
import importlib
import pixel_lanterns6 as PL
importlib.reload(PL)


def srgb_to_lin(c):
    c = np.asarray(c, float) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def pixel_mat(name):
    """Painted pixel colours (face attribute "col"); gold faces get a gloss coat; glass glows with the charge."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    b = N["Principled BSDF"]
    ac = N.new("ShaderNodeAttribute"); ac.attribute_name = "col"
    ak = N.new("ShaderNodeAttribute"); ak.attribute_name = "kind"
    ag = N.new("ShaderNodeAttribute"); ag.attribute_name = "glow"
    L.new(ac.outputs["Color"], b.inputs["Base Color"])
    metal = N.new("ShaderNodeMath"); metal.operation = "COMPARE"; metal.inputs[1].default_value = 1.0
    metal.inputs[2].default_value = 0.1
    L.new(ak.outputs["Fac"], metal.inputs[0])
    rough = N.new("ShaderNodeMapRange"); L.new(metal.outputs[0], rough.inputs[0])
    rough.inputs[3].default_value = 0.18; rough.inputs[4].default_value = 0.32
    L.new(rough.outputs[0], b.inputs["Roughness"])
    coat = N.new("ShaderNodeMapRange"); L.new(metal.outputs[0], coat.inputs[0])
    coat.inputs[3].default_value = 0.6; coat.inputs[4].default_value = 0.35
    L.new(coat.outputs[0], b.inputs["Coat Weight"])
    b.inputs["Emission Color"].default_value = (0.02, 0.9, 0.12, 1)
    cv = N.new("ShaderNodeValue"); cv.name = "Charge"
    drive(cv.outputs[0], "default_value", CHARGE)
    e1 = N.new("ShaderNodeMath"); e1.operation = "MULTIPLY"
    L.new(ag.outputs["Fac"], e1.inputs[0]); L.new(cv.outputs[0], e1.inputs[1])
    e2 = N.new("ShaderNodeMath"); e2.operation = "MULTIPLY"; e2.inputs[1].default_value = 0.85   # peak 1.19 at the socket
    L.new(e1.outputs[0], e2.inputs[0])
    L.new(e2.outputs[0], b.inputs["Emission Strength"])
    return m


MAT = pixel_mat(f"{TAG} pixel")
BOXES = {}


def pixel_mesh(code, parent):
    part, pz = PL.build(code)
    q, c, k, w = PL.quads(part, pz)
    BOXES[code] = PL.box_count(part)
    n = len(q)
    verts = (q.reshape(-1, 3) / 16.0).astype(np.float32)
    me = bpy.data.meshes.new(f"{TAG} {code} mesh")
    me.vertices.add(n * 4)
    me.vertices.foreach_set("co", verts.ravel())
    me.loops.add(n * 4)
    me.loops.foreach_set("vertex_index", np.arange(n * 4, dtype=np.int32))
    me.polygons.add(n)
    me.polygons.foreach_set("loop_start", np.arange(0, n * 4, 4, dtype=np.int32))
    me.update()
    lin = np.concatenate([srgb_to_lin(c), np.ones((n, 1))], 1).astype(np.float32)
    ca = me.color_attributes.new("col", "FLOAT_COLOR", "FACE"); ca.data.foreach_set("color", lin.ravel())
    ka = me.attributes.new("kind", "FLOAT", "FACE"); ka.data.foreach_set("value", k.astype(np.float32))
    ga = me.attributes.new("glow", "FLOAT", "FACE"); ga.data.foreach_set("value", w.astype(np.float32))
    me.materials.append(MAT)
    o = link(bpy.data.objects.new(f"{TAG} {code} lantern", me))
    o.parent = parent
    return o, pz


LAYOUT = {"D1": (0, 0), "D2": (4, 0), "D3": (8, 0), "D4": (0, 7), "D5": (4, 7), "D6": (8, 7)}
for code, (ox, oy) in LAYOUT.items():
    name = PL.DESIGNS[code][0]
    root, lamp = take(code, name, ox, oy)
    o, pz = pixel_mesh(code, root)
    lamp.location = (0, -0.6, pz / 16.0)                       # in front of the port, so the gold catches the green
    lamp.data.driver_remove("energy")
    drive(lamp.data, "energy", "1.5 * (" + CHARGE + ")")
    print(code, name, "boxes", BOXES[code])

# ------------------------------------------------------------------ stage, light, cameras (604's, framed for 2-block lanterns)
_tail = _t604[_t604.index("# ------------------------------------------------------------------ stage, light, cameras"):]
_tail = _tail.replace("CAMS[code] = cam(f\"Cam {code} {name}\", (ox + 1.5, oy - 3.4, 1.35), (ox, oy, 0.72))",
                      "CAMS[code] = cam(f\"Cam {code} {name}\", (ox + 1.9, oy - 4.3, 1.6), (ox, oy, 0.95))")
assert "oy - 4.3" in _tail
exec(compile(_tail, _s604, "exec"), globals())
