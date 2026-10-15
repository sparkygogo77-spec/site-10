# Pass 603: corps suits round 4 (Chat D, suits, 2026-10-15). Builds on pass 827 (its rig, suit builders and materials).
# J on 827: "C8b Crest knight is good now the skin needs new textures and the suits dont obey the suitup completely, THE
# SUIT COMING ON THE BRIGHT LIGHT THAT REVEALS IT SHOULD BE THE CORPS COLOR, not green, change the hue to match, for the
# brick C5b suit the hands should be thicker almost like a gauntlet but i want to see new designs, make a few new designs
# based on c8b".
# KEEP word for word: C8b's shape (no cape, crested pauldrons, chest disc, banded arms, the robot faceplate helmet).
# Fixed for every suit:
#   - the suit-up: every piece now forms under the rising light, including the C8 materials and their glowing seams
#     (in 827 the carbon/plated/crystal C8s and their seams were simply there from frame 1);
#   - the bright reveal band is the suit's corps colour (Violet, Blue, Red, Yellow, Orange), not mint green, and the
#     ring flare at the end of the forming is the corps colour too.
# Takes:
#   C8b  as kept (carbon weave, Violet), with the fixed suit-up          T1-T4: C8b's shape in four NEW textures:
#   T1 circuit (dark plate, thin glowing traces, Blue)                    T2 hex plate (raised hex cells, glowing gaps, Red)
#   T3 scale mail (overlapping scales, lit rims, Yellow)                  T4 pinstripe alloy (brushed metal, fine lines, Orange)
#   C5c  C5b brick with thick gauntlet hands (cuff, armoured fist, knuckle ridge), Orange
#   New designs from C8b: N1 Crest Heavy (three-layer gauntlets, big pauldron caps, thigh plates, Violet carbon)
#   N2 Crest Spine (back fins down the spine, forearm blades, a tall head crest, Blue circuit)
#   N3 Crest Warlord (stepped chest chevrons, horns on the faceplate, spiked gauntlets, Red hex plate)
# Cameras "Cam <key>", "Cam <key> shoulder", "Cam <key> back", "Cam row R4". Builds LanternLive\suit\corps_suits4.blend.
import math, os
import bpy
import numpy as np
from mathutils import Matrix

_src = os.path.join(os.environ.get("KL_REPO", "/home/claude/site-10"), "docs", "blender", "blender_updates",
                    "827_corps_suits3.update.py")
_txt = open(_src).read()
exec(compile(_txt[:_txt.index("R3 = [(")], _src, "exec"), globals())     # rig, suit-up, builders, 827 materials
scene.name = "Corps Suits 4"
OUT = os.path.join(FOLDER, "suit", "corps_suits4.blend")
MINT = (0.5, 1.0, 0.65)
EDGE_STRENGTH = 1.5           # 827 used 12; the suit has 3-4 see-through layers whose bands add up, so 1.5 each keeps the corps hue


def edge_rgb(rgb):
    """The reveal band: the corps hue, bright but saturated (never white)."""
    c = np.array(rgb, float)
    return tuple(np.clip(c, 0, 1))


def add_forming(m, rgb):
    """Wrap a plain material in the suit-up: only below the rising height, with the corps-coloured band at the edge."""
    N, L = m.node_tree.nodes, m.node_tree.links
    out = N.get("Material Output")
    src = out.inputs["Surface"].links[0].from_socket
    g = N.new("ShaderNodeGroup"); g.node_tree = form
    geo = N.new("ShaderNodeNewGeometry"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs["Position"], sep.inputs[0])
    below = N.new("ShaderNodeMath"); below.operation = "LESS_THAN"
    L.new(sep.outputs["Z"], below.inputs[0]); L.new(g.outputs[0], below.inputs[1])
    dz = N.new("ShaderNodeMath"); dz.operation = "SUBTRACT"; L.new(sep.outputs["Z"], dz.inputs[0]); L.new(g.outputs[0], dz.inputs[1])
    ab = N.new("ShaderNodeMath"); ab.operation = "ABSOLUTE"; L.new(dz.outputs[0], ab.inputs[0])
    band = N.new("ShaderNodeMapRange"); band.inputs["From Min"].default_value = 0.0; band.inputs["From Max"].default_value = 0.05
    band.inputs["To Min"].default_value = EDGE_STRENGTH; band.inputs["To Max"].default_value = 0.0; L.new(ab.outputs[0], band.inputs["Value"])
    edge = N.new("ShaderNodeEmission"); edge.inputs["Color"].default_value = (*edge_rgb(rgb), 1)
    L.new(band.outputs["Result"], edge.inputs["Strength"])
    add = N.new("ShaderNodeAddShader"); L.new(src, add.inputs[0]); L.new(edge.outputs[0], add.inputs[1])
    alpha = 0.92
    p = N.get("Principled BSDF")
    if p is not None:
        alpha = p.inputs["Alpha"].default_value; p.inputs["Alpha"].default_value = 1.0
    am = N.new("ShaderNodeMath"); am.operation = "MULTIPLY"; am.inputs[1].default_value = alpha
    L.new(below.outputs[0], am.inputs[0])
    tr = N.new("ShaderNodeBsdfTransparent"); mix = N.new("ShaderNodeMixShader")
    L.new(am.outputs[0], mix.inputs["Fac"]); L.new(tr.outputs[0], mix.inputs[1]); L.new(add.outputs[0], mix.inputs[2])
    L.new(mix.outputs[0], out.inputs["Surface"])
    try:
        m.surface_render_method = "BLENDED"
    except Exception:
        pass
    return m


def new_proc(name, kind, rgb):
    """Four new suit textures (procedural, corps-tinted, 92% opaque), same UV 'box' mapping as 827's materials."""
    if kind in ("plated", "carbon", "crystal"):
        return proc_mat(name, kind, rgb)
    m = bpy.data.materials.new(name); m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    p = N.get("Principled BSDF")
    uv = N.new("ShaderNodeUVMap"); uv.uv_map = "box"
    sc_ = N.new("ShaderNodeVectorMath"); sc_.operation = "SCALE"; sc_.inputs["Scale"].default_value = 0.25
    L.new(uv.outputs["UV"], sc_.inputs[0])
    c = np.array(rgb)
    p.inputs["Emission Color"].default_value = (*c, 1)
    if kind == "circuit":                    # dark plate, thin glowing traces that turn at right angles, pads
        br = N.new("ShaderNodeTexBrick"); br.inputs["Scale"].default_value = 3.0; br.inputs["Mortar Size"].default_value = 0.012
        br.offset = 0.25; L.new(sc_.outputs[0], br.inputs["Vector"])
        vo = N.new("ShaderNodeTexVoronoi"); vo.feature = "F1"; vo.distance = "CHEBYCHEV"; vo.inputs["Scale"].default_value = 6.0
        L.new(sc_.outputs[0], vo.inputs["Vector"])
        pad = N.new("ShaderNodeMapRange"); pad.inputs["From Min"].default_value = 0.06; pad.inputs["From Max"].default_value = 0.08
        pad.inputs["To Min"].default_value = 1.0; pad.inputs["To Max"].default_value = 0.0; L.new(vo.outputs["Distance"], pad.inputs["Value"])
        tr = N.new("ShaderNodeMath"); tr.operation = "SUBTRACT"; tr.inputs[0].default_value = 1.0; L.new(br.outputs["Fac"], tr.inputs[1])
        mx = N.new("ShaderNodeMath"); mx.operation = "MAXIMUM"; L.new(tr.outputs[0], mx.inputs[0]); L.new(pad.outputs["Result"], mx.inputs[1])
        p.inputs["Base Color"].default_value = (*(c * 0.06 + 0.01), 1); p.inputs["Metallic"].default_value = 0.6
        p.inputs["Roughness"].default_value = 0.35
        em = N.new("ShaderNodeMath"); em.operation = "MULTIPLY"; em.inputs[1].default_value = 1.6; L.new(mx.outputs[0], em.inputs[0])
        L.new(em.outputs[0], p.inputs["Emission Strength"])
    elif kind == "hexplate":                 # raised hex cells, the gaps glow
        vo = N.new("ShaderNodeTexVoronoi"); vo.feature = "DISTANCE_TO_EDGE"; vo.inputs["Scale"].default_value = 5.0
        vo.inputs["Randomness"].default_value = 0.0; L.new(sc_.outputs[0], vo.inputs["Vector"])
        gap = N.new("ShaderNodeMapRange"); gap.inputs["From Min"].default_value = 0.02; gap.inputs["From Max"].default_value = 0.05
        gap.inputs["To Min"].default_value = 1.0; gap.inputs["To Max"].default_value = 0.0; L.new(vo.outputs["Distance"], gap.inputs["Value"])
        cell = N.new("ShaderNodeMapRange"); cell.inputs["From Min"].default_value = 0.05; cell.inputs["From Max"].default_value = 0.4
        cell.inputs["To Min"].default_value = 0.35; cell.inputs["To Max"].default_value = 0.12; L.new(vo.outputs["Distance"], cell.inputs["Value"])
        cm = N.new("ShaderNodeVectorMath"); cm.operation = "SCALE"; cm.inputs[0].default_value = tuple(c)
        L.new(cell.outputs["Result"], cm.inputs["Scale"]); L.new(cm.outputs[0], p.inputs["Base Color"])
        p.inputs["Metallic"].default_value = 0.4; p.inputs["Roughness"].default_value = 0.3
        em = N.new("ShaderNodeMath"); em.operation = "MULTIPLY"; em.inputs[1].default_value = 3.5; L.new(gap.outputs["Result"], em.inputs[0])
        L.new(em.outputs[0], p.inputs["Emission Strength"])
    elif kind == "scales":                   # overlapping scales: each a soft dome, its lower rim lit
        br = N.new("ShaderNodeTexBrick"); br.inputs["Scale"].default_value = 4.0; br.inputs["Mortar Size"].default_value = 0.0
        br.inputs["Brick Width"].default_value = 0.5; br.inputs["Row Height"].default_value = 0.25; br.offset = 0.5
        L.new(sc_.outputs[0], br.inputs["Vector"])
        sp = N.new("ShaderNodeSeparateXYZ"); L.new(sc_.outputs[0], sp.inputs[0])
        rows = N.new("ShaderNodeMath"); rows.operation = "MULTIPLY"; rows.inputs[1].default_value = 16.0; L.new(sp.outputs["Y"], rows.inputs[0])
        fr = N.new("ShaderNodeMath"); fr.operation = "FRACT"; L.new(rows.outputs[0], fr.inputs[0])
        rim = N.new("ShaderNodeMapRange"); rim.inputs["From Min"].default_value = 0.0; rim.inputs["From Max"].default_value = 0.18
        rim.inputs["To Min"].default_value = 1.0; rim.inputs["To Max"].default_value = 0.0; L.new(fr.outputs[0], rim.inputs["Value"])
        shade = N.new("ShaderNodeMapRange"); shade.inputs["To Min"].default_value = 0.08; shade.inputs["To Max"].default_value = 0.4
        L.new(fr.outputs[0], shade.inputs["Value"])
        cm = N.new("ShaderNodeVectorMath"); cm.operation = "SCALE"; cm.inputs[0].default_value = tuple(c)
        L.new(shade.outputs["Result"], cm.inputs["Scale"]); L.new(cm.outputs[0], p.inputs["Base Color"])
        p.inputs["Metallic"].default_value = 0.7; p.inputs["Roughness"].default_value = 0.25
        em = N.new("ShaderNodeMath"); em.operation = "MULTIPLY"; em.inputs[1].default_value = 2.6; L.new(rim.outputs["Result"], em.inputs[0])
        L.new(em.outputs[0], p.inputs["Emission Strength"])
    else:                                    # pinstripe alloy: brushed metal, fine glowing lines every 2 px
        no = N.new("ShaderNodeTexNoise"); no.inputs["Scale"].default_value = 40.0; no.inputs["Detail"].default_value = 2.0
        st = N.new("ShaderNodeVectorMath"); st.operation = "MULTIPLY"; st.inputs[1].default_value = (1.0, 60.0, 1.0)
        L.new(sc_.outputs[0], st.inputs[0]); L.new(st.outputs[0], no.inputs["Vector"])
        sp = N.new("ShaderNodeSeparateXYZ"); L.new(sc_.outputs[0], sp.inputs[0])
        ln = N.new("ShaderNodeMath"); ln.operation = "MULTIPLY"; ln.inputs[1].default_value = 8.0; L.new(sp.outputs["X"], ln.inputs[0])
        fr = N.new("ShaderNodeMath"); fr.operation = "FRACT"; L.new(ln.outputs[0], fr.inputs[0])
        line = N.new("ShaderNodeMapRange"); line.inputs["From Min"].default_value = 0.0; line.inputs["From Max"].default_value = 0.06
        line.inputs["To Min"].default_value = 1.0; line.inputs["To Max"].default_value = 0.0; L.new(fr.outputs[0], line.inputs["Value"])
        shade = N.new("ShaderNodeMapRange"); shade.inputs["To Min"].default_value = 0.12; shade.inputs["To Max"].default_value = 0.3
        L.new(no.outputs["Fac"], shade.inputs["Value"])
        cm = N.new("ShaderNodeVectorMath"); cm.operation = "SCALE"; cm.inputs[0].default_value = tuple(c)
        L.new(shade.outputs["Result"], cm.inputs["Scale"]); L.new(cm.outputs[0], p.inputs["Base Color"])
        p.inputs["Metallic"].default_value = 0.9; p.inputs["Roughness"].default_value = 0.22
        try:
            p.inputs["Anisotropic"].default_value = 0.8
        except Exception:
            pass
        em = N.new("ShaderNodeMath"); em.operation = "MULTIPLY"; em.inputs[1].default_value = 2.4; L.new(line.outputs["Result"], em.inputs[0])
        L.new(em.outputs[0], p.inputs["Emission Strength"])
    p.inputs["Alpha"].default_value = 0.92
    return m


# ------------------------------------------------------------------ additions on top of C8b's shape
def gauntlets(objs, tag, T, Sm, layers=1, spikes=False, thick=0.6):
    cb = lambda part, nm, a, b, inf, m=None: child_box(objs[part], f"{tag} {nm}", a, b, m or T, inf)
    for part in ("rarm", "larm"):
        x0, x1 = arm_x(part)
        cb(part, f"gauntlet cuff {part}", (x0 - thick, 5.2, -2 - thick), (x1 + thick, 7.0, 2 + thick), 0.2)
        cb(part, f"gauntlet cuff rim {part}", (x0 - thick - 0.15, 5.0, -2 - thick - 0.15), (x1 + thick + 0.15, 5.4, 2 + thick + 0.15), 0.1, Sm)
        for k in range(layers):
            d = 0.25 * k
            cb(part, f"gauntlet fist {k} {part}", (x0 - thick + 0.1 + d, 7.0 + 0.6 * k, -2 - thick + 0.1 + d),
               (x1 + thick - 0.1 - d, 10.4, 2 + thick - 0.1 - d), 0.15)
        cb(part, f"knuckle ridge {part}", (x0 - 0.3, 8.7, -2 - thick - 0.5), (x1 + 0.3, 9.7, -2 - thick + 0.1), 0.1, Sm)
        if spikes:
            for k in range(3):
                cb(part, f"knuckle spike {k} {part}", (x0 + 0.4 + k * 1.2, 8.8, -2 - thick - 1.4), (x0 + 1.0 + k * 1.2, 9.5, -2 - thick - 0.4), 0.05, Sm)


def heavy(objs, tag, T, Sm):
    new_suit(objs, tag, "C8b", T, Sm)
    gauntlets(objs, tag, T, Sm, layers=3)
    cb = lambda part, nm, a, b, inf, m=None: child_box(objs[part], f"{tag} {nm}", a, b, m or T, inf)
    for part in ("rarm", "larm"):
        x0, x1 = out_in(part, 2.2)
        cb(part, f"pauldron cap {part}", (x0, -3.4, -3.0), (x1, -1.6, 3.0), 0.2)
        cb(part, f"pauldron cap rim {part}", (x0 - 0.1, -1.7, -3.1), (x1 + 0.1, -1.4, 3.1), 0.05, Sm)
    for part in ("rleg", "lleg"):
        cb(part, f"thigh plate {part}", (-2.4, 0.6, -2.9), (2.4, 4.8, -1.8), 0.2)
        cb(part, f"thigh line {part}", (-0.3, 0.8, -3.2), (0.3, 4.6, -2.9), 0.05, Sm)


def spine(objs, tag, T, Sm):
    new_suit(objs, tag, "C8b", T, Sm)
    cb = lambda part, nm, a, b, inf, m=None: child_box(objs[part], f"{tag} {nm}", a, b, m or T, inf)
    for k in range(5):                                          # fins down the back, tallest at the shoulders
        h = 2.4 - 0.35 * k
        cb("body", f"spine fin {k}", (-0.35, 0.6 + k * 2.1, 2.6), (0.35, 2.2 + k * 2.1, 2.6 + h), 0.05, Sm if k % 2 == 0 else None)
    for part in ("rarm", "larm"):
        x0, x1 = arm_x(part)
        xo = x0 - 0.9 if part == "rarm" else x1 + 0.3
        cb(part, f"forearm blade {part}", (xo, 4.6, -0.3), (xo + 0.6, 9.6, 0.3), 0.05)
        cb(part, f"forearm blade edge {part}", (xo + (0 if part == "rarm" else 0.45), 5.0, -0.32), (xo + (0.15 if part == "rarm" else 0.6), 9.2, 0.32), 0.04, Sm)
    child_box(objs["head"], f"{tag} helm tall crest", (-0.45, -12.0, -3.4), (0.45, -9.8, 3.0), T, 0.05)
    child_box(objs["head"], f"{tag} helm tall crest light", (-0.47, -11.8, -3.6), (0.47, -11.0, -3.2), Sm)


def warlord(objs, tag, T, Sm):
    new_suit(objs, tag, "C8b", T, Sm)
    gauntlets(objs, tag, T, Sm, layers=2, spikes=True)
    cb = lambda part, nm, a, b, inf, m=None: child_box(objs[part], f"{tag} {nm}", a, b, m or T, inf)
    for k in range(3):                                          # stepped chevrons down the chest (two angled halves each)
        y = 7.4 + k * 1.1
        for sx in (-1, 1):
            xa, xb = (-3.8 + 0.5 * k, -0.2) if sx < 0 else (0.2, 3.8 - 0.5 * k)
            cb("body", f"chevron {k} {sx}", (xa, y, -3.0 - 0.15 * k), (xb, y + 0.7, -2.5), 0.05, Sm if k == 1 else None)
    for sx in (-1, 1):                                          # horns on the faceplate
        child_box(objs["head"], f"{tag} helm horn base {sx}", (sx * 3.8 - 0.6, -8.4, -1.6), (sx * 3.8 + 0.6, -7.2, 0.4), T, 0.05)
        child_box(objs["head"], f"{tag} helm horn {sx}", (sx * 4.6 - 0.4, -10.6, -1.2), (sx * 4.6 + 0.4, -8.2, 0.0), T, 0.05)
        child_box(objs["head"], f"{tag} helm horn tip {sx}", (sx * 5.2 - 0.3, -11.8, -0.9), (sx * 5.2 + 0.3, -10.4, -0.3), Sm)


def c5c(objs, tag, T, Sm):
    new_suit(objs, tag, "C5b", T, Sm)
    gauntlets(objs, tag, T, Sm, layers=2, thick=0.8)        # J: "the hands should be thicker almost like a gauntlet"


R4 = [("C8b", "Crest Knight C8b as kept, suit-up fixed", "Violet", "carbon", lambda o, t, T, Sm: new_suit(o, t, "C8b", T, Sm)),
      ("T1", "C8b in circuit", "Blue", "circuit", lambda o, t, T, Sm: new_suit(o, t, "C8b", T, Sm)),
      ("T2", "C8b in hex plate", "Red", "hexplate", lambda o, t, T, Sm: new_suit(o, t, "C8b", T, Sm)),
      ("T3", "C8b in scale mail", "Yellow", "scales", lambda o, t, T, Sm: new_suit(o, t, "C8b", T, Sm)),
      ("T4", "C8b in pinstripe alloy", "Orange", "pinstripe", lambda o, t, T, Sm: new_suit(o, t, "C8b", T, Sm)),
      ("C5c", "Ribbed Warden - brick, gauntlet hands", "Orange", "lib:br1", c5c),
      ("N1", "Crest Heavy - gauntlets, pauldron caps", "Violet", "carbon", heavy),
      ("N2", "Crest Spine - back fins, forearm blades", "Blue", "circuit", spine),
      ("N3", "Crest Warlord - chevrons, horns, spikes", "Red", "hexplate", warlord)]

TAG_CORPS = {}
for j, (dk, dname, cname, look, fn) in enumerate(R4):
    ringm = set_corps(cname)
    rgb = CORPS[cname][1]
    if look.startswith("lib:"):
        T, Sm = ARMOR[(cname, look[4:])], SEAM[(cname, look[4:])]
    else:
        T = add_forming(new_proc(f"Suit4 {look} {cname}", look, rgb), rgb)
        Sm = suit_mat(f"Suit4 {look} seam {cname}", None, rgb, emit=3.0, solid=True)     # seams form with the suit too
    place(dk, f"{dk}  {dname}", f"{cname}, {look.replace('lib:', '')}", 0.0, j * 1.6,
          lambda objs, tag, fn=fn, T=T, Sm=Sm: fn(objs, tag, T, Sm))
    recolour_ring(dk, ringm)
    TAG_CORPS[f"KL S594 {dk}"] = cname


# ------------------------------------------------------------------ the reveal band and ring flare in the corps colour
def is_mint(node):
    c = node.inputs["Color"].default_value
    return abs(c[0] - MINT[0]) < 0.02 and abs(c[1] - MINT[1]) < 0.02 and abs(c[2] - MINT[2]) < 0.02


def corps_copy(m, cname):
    if m is None or not m.use_nodes or not any(n.type == "EMISSION" and is_mint(n) for n in m.node_tree.nodes):
        return m
    nm = f"{m.name} [{cname}]"
    m2 = bpy.data.materials.get(nm)
    if m2 is None:
        m2 = m.copy(); m2.name = nm
        for n in m2.node_tree.nodes:
            if n.type == "EMISSION" and is_mint(n):
                n.inputs["Color"].default_value = (*edge_rgb(CORPS[cname][1]), 1)
            if n.type == "MATH" and n.operation == "MULTIPLY" and abs(n.inputs[1].default_value - 12.0) < 1e-6:
                n.inputs[1].default_value = EDGE_STRENGTH
    return m2


for o in list(bpy.data.objects):
    if o.type != "MESH":
        continue
    pre = next((p for p in TAG_CORPS if o.name.startswith(p + " ")), None)
    if pre is None:
        continue
    for i, m in enumerate(o.data.materials):
        m2 = corps_copy(m, TAG_CORPS[pre])
        if m2 is not m:
            if o.data.users > 1:
                o.data = o.data.copy()
            o.data.materials[i] = m2

for cname in set(TAG_CORPS.values()):                       # every corps ring flares as the forming ends
    rm = bpy.data.materials.get(f"KL ring {cname}")
    if rm is None:
        continue
    s = rm.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
    for _f, _e in ((1, 3.0), (FORM_END - 3, 3.0), (FORM_END + 1, 30.0), (FORM_END + 10, 3.0), (LOOP, 3.0)):
        s.default_value = _e; s.keyframe_insert("default_value", frame=_f)

MIDX = (len(R4) - 1) / 2 * 1.6 * SPX
cam("Cam row R4", (MIDX, -18.0, 2.4), (MIDX, 0, 1.15), 34)
cam("Cam row R4 back", (MIDX, 18.0, 2.4), (MIDX, 0, 1.15), 34)
scene.frame_start, scene.frame_end = 1, LOOP
bpy.ops.mesh.primitive_plane_add(size=300, location=(MIDX, 0, 0))
g = bpy.context.active_object
for c in g.users_collection:
    c.objects.unlink(g)
link(g); g.name = "S603 floor"; g.data.materials.append(mat("S603 floor", (0.05, 0.055, 0.06), rough=0.8))
world = bpy.data.worlds.new("S603 world"); world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.03, 0.035, 0.045, 1)
scene.world = world
key = bpy.data.lights.new("S603 key", "AREA"); key.energy = 30000; key.size = 160
ko = link(bpy.data.objects.new("S603 key", key)); ko.location = (MIDX, -14, 9); ko.rotation_euler = (R(50), 0, 0)
rim = bpy.data.lights.new("S603 rim", "AREA"); rim.energy = 12000; rim.size = 160
ro = link(bpy.data.objects.new("S603 rim", rim)); ro.location = (MIDX, 14, 7); ro.rotation_euler = (R(-50), 0, 0)
try:
    scene.render.engine = "BLENDER_EEVEE"
except Exception:
    scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x, scene.render.resolution_y = 1600, 900
try:
    scene.view_settings.view_transform = "Standard"
except Exception:
    pass
scene.camera = bpy.data.objects["Cam row R4"]
scene.frame_set(60)
try:
    bpy.ops.outliner.orphans_purge(do_recursive=True)
except Exception:
    pass
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("saved", OUT)
