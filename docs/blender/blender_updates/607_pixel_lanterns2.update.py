# Pass 607: J's three 606 lanterns made more complex, 3 takes each (PC chat, 2026-10-19; lanterns 600-699).
# Why: J on 606 D1 Vault, D6 Armillary and D5 Crystal: "make these more complex" (4 images: his three in Blender, and a
#   comic reference used ONLY for mood: layered silhouettes, angular fins, a glowing bowl/core, molten drips, strong
#   highlights; no shape, emblem or corps mark copied).
# Every take: hollow see-through glass (35% opaque; Dark Lantern ribs, crazing, gold lightning fading to the ends, dark stitches) with
#   an inner core carrying the G3 flare (a noise ball spinning one way, breathing, yellow in the green, never white);
#   polished gold; layered frames, fins, studs; a sculpted port with swept fins and rivets.
# Voxels: tools/pixel_lanterns7.py (Vault takes at 1/4 px; Armillary and Crystal glass on a 1/2 px grid so every take
#   fits ~2,500 Blockbench boxes; box counts printed).
# Takes: D1a cathedral, D1b molten, D1c bastion (Vault); D6a orrery, D6b cradle, D6c molten (Armillary);
#        D5a faberge, D5b winged, D5c molten (Crystal).
# Each turns once in 120 frames; idle to 20, the charge fills by 80, holds. Cameras "Cam <code> <name>", "Cam all".
# Builds LanternLive\lanterns\pixel_lanterns2.blend.
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
    raise FileNotFoundError("607 needs " + rel + " (set KL_REPO)")


PASS = "607"
OUT_NAME = "pixel_lanterns2.blend"
_s604 = _find("docs/blender/blender_updates/604_lantern_models_proper.update.py")
_t604 = open(_s604, encoding="utf-8").read()
exec(compile(_t604[:_t604.index("# ---- 604 takes")], _s604, "exec"), globals())       # scene, drive, take, CHARGE
sys.path.insert(0, os.path.dirname(_find("tools/pixel_lanterns7.py")))
import importlib
import pixel_lanterns6, pixel_lanterns7
importlib.reload(pixel_lanterns6); importlib.reload(pixel_lanterns7)
PL = pixel_lanterns7


def srgb_to_lin(c):
    c = np.asarray(c, float) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def pixel_mat(name):
    """Painted pixel colours (face attribute "col"). Gold: gloss coat. Glass (kind 4): see-through. Core (kind 6): the G3
    flare, a noise ball spinning one way with a breathing strength, some yellow in the green."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    try:
        m.surface_render_method = "BLENDED"
    except Exception:
        pass
    N, L = m.node_tree.nodes, m.node_tree.links
    b = N["Principled BSDF"]

    def mathn(op, a, bb=None):
        n = N.new("ShaderNodeMath"); n.operation = op
        for i, v in enumerate((a, bb)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                L.new(v, n.inputs[i])
        return n.outputs[0]

    ac = N.new("ShaderNodeAttribute"); ac.attribute_name = "col"
    ak = N.new("ShaderNodeAttribute"); ak.attribute_name = "kind"
    ag = N.new("ShaderNodeAttribute"); ag.attribute_name = "glow"
    L.new(ac.outputs["Color"], b.inputs["Base Color"])
    is_metal = mathn("COMPARE", ak.outputs["Fac"], 1.0); N[is_metal.node.name].inputs[2].default_value = 0.1
    is_glass = mathn("COMPARE", ak.outputs["Fac"], 4.0); N[is_glass.node.name].inputs[2].default_value = 0.1
    is_core = mathn("COMPARE", ak.outputs["Fac"], 6.0); N[is_core.node.name].inputs[2].default_value = 0.1
    L.new(mathn("ADD", mathn("MULTIPLY", is_metal, 0.14), 0.18), b.inputs["Roughness"])
    L.new(mathn("ADD", mathn("MULTIPLY", is_metal, -0.25), 0.6), b.inputs["Coat Weight"])
    L.new(mathn("SUBTRACT", 1.0, mathn("MULTIPLY", is_glass, 0.65)), b.inputs["Alpha"])         # glass 35% opaque: the core shows
    cv = N.new("ShaderNodeValue"); cv.name = "Charge"
    drive(cv.outputs[0], "default_value", CHARGE)
    # the G3 flare on the core: object-space noise turned about Z one way, breathing +-15% every 3 s
    tc = N.new("ShaderNodeTexCoord")
    mp = N.new("ShaderNodeMapping"); L.new(tc.outputs["Object"], mp.inputs["Vector"])
    drive(mp.inputs["Rotation"], "default_value", "frame * 0.09", 2)
    nz = N.new("ShaderNodeTexNoise"); nz.noise_dimensions = "4D"; nz.inputs["Scale"].default_value = 5.0
    nz.inputs["Detail"].default_value = 4.0
    L.new(mp.outputs["Vector"], nz.inputs["Vector"])
    drive(nz.inputs["W"], "default_value", "frame * 0.02")
    flare = N.new("ShaderNodeMapRange"); L.new(nz.outputs["Fac"], flare.inputs[0])
    flare.inputs[1].default_value = 0.35; flare.inputs[2].default_value = 0.7
    flare.inputs[3].default_value = 0.45; flare.inputs[4].default_value = 1.25
    br = N.new("ShaderNodeValue"); br.name = "Breathe"
    drive(br.outputs[0], "default_value", "1.0 + 0.15 * sin(frame * 0.1047)")
    core_e = mathn("MULTIPLY", mathn("MULTIPLY", flare.outputs[0], br.outputs[0]), is_core)
    glow_e = mathn("MULTIPLY", ag.outputs["Fac"], mathn("SUBTRACT", 1.0, is_core))
    strength = mathn("MULTIPLY", mathn("ADD", mathn("MULTIPLY", core_e, 1.3), mathn("MULTIPLY", glow_e, 0.42)), cv.outputs[0])
    L.new(strength, b.inputs["Emission Strength"])
    mix = N.new("ShaderNodeMix"); mix.data_type = "RGBA"                  # some yellow in the core's hottest noise
    L.new(mathn("MULTIPLY", mathn("GREATER_THAN", nz.outputs["Fac"], 0.62), is_core), mix.inputs[0])
    mix.inputs[6].default_value = (0.02, 0.9, 0.12, 1); mix.inputs[7].default_value = (0.45, 0.92, 0.05, 1)
    L.new(mix.outputs[2], b.inputs["Emission Color"])
    return m


MAT = pixel_mat(f"{TAG} pixel")
BOXES = {}


def pixel_mesh(code, parent):
    part, pz = PL.build(code)
    q, c, k, w = PL.quads(part, pz)
    BOXES[code] = PL.model_boxes(part)
    n = len(q)
    me = bpy.data.meshes.new(f"{TAG} {code} mesh")
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
    me.materials.append(MAT)
    o = link(bpy.data.objects.new(f"{TAG} {code} lantern", me))
    o.parent = parent
    return o, pz


LAYOUT = {"D1a": (0, 0), "D1b": (4, 0), "D1c": (8, 0), "D6a": (0, 7), "D6b": (4, 7), "D6c": (8, 7),
          "D5a": (0, 14), "D5b": (4, 14), "D5c": (8, 14)}
for code, (ox, oy) in LAYOUT.items():
    name = PL.DESIGNS[code][0]
    root, lamp = take(code, name, ox, oy)
    o, pz = pixel_mesh(code, root)
    lamp.location = (0, 0, pz / 16.0)                          # inside, at the core: lights the glass and gold from within
    lamp.data.driver_remove("energy")
    drive(lamp.data, "energy", "2.5 * (" + CHARGE + ")")
    print(code, name, "boxes", BOXES[code])

_tail = _t604[_t604.index("# ------------------------------------------------------------------ stage, light, cameras"):]
_tail = _tail.replace("CAMS[code] = cam(f\"Cam {code} {name}\", (ox + 1.5, oy - 3.4, 1.35), (ox, oy, 0.72))",
                      "CAMS[code] = cam(f\"Cam {code} {name}\", (ox + 1.9, oy - 4.4, 1.65), (ox, oy, 1.0))")
_tail = _tail.replace('("key B", (5, 3, 4.5), 320, 6), ("rim B", (3, 10, 3.5), 220, 6))',
                      '("key B", (5, 3, 4.5), 320, 6), ("rim B", (3, 10, 3.5), 220, 6), ("key C", (5, 10, 4.5), 320, 6), ("rim C", (3, 17, 3.5), 220, 6))')
_tail = _tail.replace("floor.from_pydata([(-3, -4, 0), (11, -4, 0), (11, 11, 0), (-3, 11, 0)]",
                      "floor.from_pydata([(-3, -4, 0), (11, -4, 0), (11, 18, 0), (-3, 18, 0)]")
_tail = _tail.replace('CAMS["all"] = cam("Cam all", (4, -9, 5.5), (4, 3.5, 0.6), 30)',
                      'CAMS["all"] = cam("Cam all", (4, -11, 7.5), (4, 7.0, 0.6), 30)')
_tail = _tail.replace('Vector((4, 3.5 if "B" in nm else 0, 0))', 'Vector((4, 7 if "B" in nm else (14 if " C" in nm else 0), 0))')
for must in ("oy - 4.4", "key C", '(14 if " C" in nm', "(11, 18, 0)", "(4, -11, 7.5)"):
    assert must in _tail, must
exec(compile(_tail, _s604, "exec"), globals())
