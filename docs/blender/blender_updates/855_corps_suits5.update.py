# Pass 855: corps suits round 5 (suits chat 800-899, 2026-10-15). Builds on pass 603 (its rig, C8b shape, suit-up,
# corps-coloured reveal) which builds on 827.
# J's notes on 603:
#   C8b Crest Knight (KEEP the shape, suit-up fixed): "keep this material, tell me what it is then try other purples"
#   T1  C8b in circuit: "give me brighter yet also darker blues this is too bright"
#   T2  C8b in hex plate: no note -> 3 new variations
# C8b's material (the answer for J): 827's procedural "carbon weave" (proc_mat kind "carbon", no image file): a diagonal
# band wave (scale 6) mixed 50/50 with a checker (scale 8), through a colour ramp from 5% to 35% of the corps colour
# (near-black violet to dark violet); glossy (roughness 0.2) with a full clear coat; a fine glowing grid (the mortar
# lines of a brick pattern, scale 2) emitting violet at 1.8; 92% opaque. Seams/visor/lights: solid violet emitting at 3.
# Undersuit: violet at 7%. Violet = linear RGB (0.6, 0.1, 1.0).
# Takes (all keep C8b's shape and 603's suit-up; the reveal band and ring flare are each take's own corps colour):
#   C8b   (as before) reference: carbon weave, Violet
#   C8bP1 the same carbon-weave recipe in royal purple (0.2, 0, 1.0): bluer and deeper than violet, saturated
#   C8bP2 the same recipe in deep plum (0.15, 0, 0.42): the darkest purple, dimmer plates, undersuit and seams
#   C8bP3 the same recipe in ultraviolet (0.06, 0, 1.0): the blue edge of purple
#   T1a   circuit: navy-black plate, electric-blue traces on an offset grid, square pads
#   T1b   circuit: blue-black steel plate, cobalt traces in two crossed grids (a dense maze), no pads
#   T1c   circuit: indigo plate, sparse azure traces with big ringed pads
#   T2a   hex plate: fine 3 px honeycomb, nearly flat, every gap glows steadily
#   T2b   hex plate: big 8 px domed tiles in deep relief, dark gaps, a lit hex outline inset in each tile
#   T2c   hex plate: 5 px bevelled cells, faint gaps, random cells light up and fade (slow twinkle)
# Also fixed (in this pass, every take): 603's corps-colour reveal only reached the bare player parts; the seams,
# undersuit, emblem and mask still had the mint band at strength 12. Here every suit piece gets the corps band at 1.5.
# T1 was too bright in 603 because its trace mask was inverted (the whole plate glowed, the traces were dark).
# Cameras "Cam <key>", "Cam <key> shoulder", "Cam <key> back"; rows "Cam row P", "Cam row T1", "Cam row T2", "Cam row R5".
# Builds LanternLive\suit\corps_suits5.blend.
import math, os
import bpy
import numpy as np

_s603 = os.path.join(os.environ.get("KL_REPO", "/home/claude/site-10"), "docs", "blender", "blender_updates",
                     "603_corps_suits4.update.py")
_t603 = open(_s603).read()
_p603 = _t603[:_t603.index("R4 = [(")]
exec(compile(_p603, _s603, "exec"), globals())     # 827 rig + builders, 603's add_forming / new_proc / gauntlets
_old = bpy.data.scenes.get("Corps Suits 5")
if _old is not None and _old != scene:
    bpy.data.scenes.remove(_old)
scene.name = "Corps Suits 5"
OUT = os.path.join(FOLDER, "suit", "corps_suits5.blend")
SQ3 = math.sqrt(3.0)


def mr(N, L, src, a, b, c, d, clamp=True):
    n = N.new("ShaderNodeMapRange"); n.clamp = clamp
    n.inputs["From Min"].default_value = a; n.inputs["From Max"].default_value = b
    n.inputs["To Min"].default_value = c; n.inputs["To Max"].default_value = d
    L.new(src, n.inputs["Value"])
    return n.outputs["Result"]


def math_(N, L, op, a, b=None):
    n = N.new("ShaderNodeMath"); n.operation = op
    for i, v in enumerate((a, b)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            n.inputs[i].default_value = v
        else:
            L.new(v, n.inputs[i])
    return n.outputs[0]


def vmath(N, L, op, *ins):
    n = N.new("ShaderNodeVectorMath"); n.operation = op
    for i, v in enumerate(ins):
        if isinstance(v, tuple):
            n.inputs[i].default_value = v
        else:
            L.new(v, n.inputs[i])
    return n.outputs["Value" if op in ("DOT_PRODUCT", "LENGTH", "DISTANCE") else "Vector"]


def base_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    p = N.get("Principled BSDF")
    uv = N.new("ShaderNodeUVMap"); uv.uv_map = "box"          # 1.0 = 32 model px (827's TILE)
    p.inputs["Alpha"].default_value = 0.92
    return m, N, L, p, uv.outputs["UV"]


# ------------------------------------------------------------------ C8b's carbon weave in other purples
def carbon(name, rgb):
    """827's carbon-weave recipe unchanged (proc_mat kind 'carbon'), in another colour."""
    return proc_mat(name, "carbon", rgb)


# ------------------------------------------------------------------ circuit, rebuilt: dark plate, bright thin traces
def circuit(name, base, line, strength, style):
    m, N, L, p, uv = base_mat(name)
    p.inputs["Base Color"].default_value = (*base, 1); p.inputs["Emission Color"].default_value = (*line, 1)
    p.inputs["Metallic"].default_value = 0.75; p.inputs["Roughness"].default_value = 0.3
    v = vmath(N, L, "SCALE", uv); v.node.inputs["Scale"].default_value = 0.25

    def traces(vec, scale, mortar, offset=0.25):
        br = N.new("ShaderNodeTexBrick"); br.inputs["Scale"].default_value = scale; br.inputs["Mortar Size"].default_value = mortar
        br.offset = offset; L.new(vec, br.inputs["Vector"])
        return math_(N, L, "MINIMUM", br.outputs["Fac"], 1.0)        # 1 on the mortar lines (the traces), 0 on the plate

    def pads(vec, scale, r0, r1, ring=False):
        vo = N.new("ShaderNodeTexVoronoi"); vo.feature = "F1"; vo.distance = "CHEBYCHEV"
        vo.inputs["Scale"].default_value = scale; L.new(vec, vo.inputs["Vector"])
        d = vo.outputs["Distance"]
        if not ring:
            return mr(N, L, d, r0, r1, 1.0, 0.0)
        a = mr(N, L, d, r0 * 0.55, r0 * 0.65, 1.0, 0.0)             # a solid centre ...
        b = mr(N, L, math_(N, L, "ABSOLUTE", math_(N, L, "SUBTRACT", d, r0)), 0.0, r1 - r0, 1.0, 0.0)   # ... and a ring
        return math_(N, L, "MAXIMUM", a, b)

    if style == "a":       # offset grid, square pads
        g = math_(N, L, "MAXIMUM", traces(v, 4.0, 0.016), pads(v, 7.0, 0.07, 0.085))
    elif style == "b":     # two crossed grids at different pitches: a dense maze, no pads
        sw = N.new("ShaderNodeSeparateXYZ"); L.new(v, sw.inputs[0])
        cw = N.new("ShaderNodeCombineXYZ"); L.new(sw.outputs["Y"], cw.inputs["X"]); L.new(sw.outputs["X"], cw.inputs["Y"])
        L.new(sw.outputs["Z"], cw.inputs["Z"])
        g = math_(N, L, "MAXIMUM", traces(v, 5.0, 0.014, 0.5), traces(cw.outputs[0], 3.3, 0.02, 0.33))
    else:                  # sparse traces and big ringed pads
        g = math_(N, L, "MAXIMUM", traces(v, 2.5, 0.012, 0.5), pads(v, 4.0, 0.11, 0.14, ring=True))
    L.new(math_(N, L, "MULTIPLY", g, strength), p.inputs["Emission Strength"])
    return m


# ------------------------------------------------------------------ real hexagon cells (603's "hex" was a square grid)
def hex_cells(N, L, uv, cell_px):
    """Returns (edge, cell_rand): edge = 0 on a cell's border .. 0.5 at its centre; cell_rand = one random value per cell."""
    p = vmath(N, L, "SCALE", uv); p.node.inputs["Scale"].default_value = 32.0 / cell_px
    s = (1.0, SQ3, 0.0); h = (0.5, SQ3 / 2, 0.0)
    a = vmath(N, L, "SUBTRACT", vmath(N, L, "WRAP", p, s, (0.0, 0.0, 0.0)), h)
    b = vmath(N, L, "SUBTRACT", vmath(N, L, "WRAP", vmath(N, L, "SUBTRACT", p, h), s, (0.0, 0.0, 0.0)), h)
    nearer_a = math_(N, L, "LESS_THAN", vmath(N, L, "DOT_PRODUCT", a, a), vmath(N, L, "DOT_PRODUCT", b, b))
    mx = N.new("ShaderNodeMix"); mx.data_type = "VECTOR"
    L.new(nearer_a, mx.inputs[0]); L.new(b, mx.inputs[4]); L.new(a, mx.inputs[5])
    gv = mx.outputs[1]
    ag = vmath(N, L, "ABSOLUTE", gv)
    sx = N.new("ShaderNodeSeparateXYZ"); L.new(ag, sx.inputs[0])
    hd = math_(N, L, "MAXIMUM", vmath(N, L, "DOT_PRODUCT", ag, (0.5, SQ3 / 2, 0.0)), sx.outputs["X"])
    edge = math_(N, L, "SUBTRACT", 0.5, hd)
    wn = N.new("ShaderNodeTexWhiteNoise"); wn.noise_dimensions = "3D"
    L.new(vmath(N, L, "SUBTRACT", p, gv), wn.inputs["Vector"])
    return edge, wn.outputs["Value"]


def hexplate(name, rgb, glow, style):
    m, N, L, p, uv = base_mat(name)
    c = np.array(rgb)
    p.inputs["Emission Color"].default_value = (*glow, 1)
    p.inputs["Metallic"].default_value = 0.55; p.inputs["Roughness"].default_value = 0.28
    bump = N.new("ShaderNodeBump"); L.new(bump.outputs["Normal"], p.inputs["Normal"])
    cm = N.new("ShaderNodeVectorMath"); cm.operation = "SCALE"; cm.inputs[0].default_value = tuple(c)
    L.new(cm.outputs[0], p.inputs["Base Color"])
    if style == "a":       # fine honeycomb, nearly flat, every gap glows
        edge, rnd = hex_cells(N, L, uv, 3.0)
        gap = mr(N, L, edge, 0.03, 0.075, 1.0, 0.0)
        L.new(mr(N, L, rnd, 0.0, 1.0, 0.1, 0.18), cm.inputs["Scale"])
        L.new(mr(N, L, edge, 0.0, 0.08, 0.0, 1.0), bump.inputs["Height"]); bump.inputs["Strength"].default_value = 0.15
        L.new(math_(N, L, "MULTIPLY", gap, 2.2), p.inputs["Emission Strength"])
    elif style == "b":     # big domed tiles, dark gaps, a lit outline inset inside each tile
        edge, rnd = hex_cells(N, L, uv, 8.0)
        dome = math_(N, L, "POWER", mr(N, L, edge, 0.02, 0.5, 0.0, 1.0), 0.5)
        L.new(dome, bump.inputs["Height"]); bump.inputs["Strength"].default_value = 0.85
        gapdark = mr(N, L, edge, 0.0, 0.03, 0.0, 1.0)
        L.new(math_(N, L, "MULTIPLY", gapdark, mr(N, L, rnd, 0.0, 1.0, 0.16, 0.26)), cm.inputs["Scale"])
        inset = mr(N, L, math_(N, L, "ABSOLUTE", math_(N, L, "SUBTRACT", edge, 0.13)), 0.0, 0.022, 1.0, 0.0)
        L.new(math_(N, L, "MULTIPLY", inset, 2.6), p.inputs["Emission Strength"])
        p.inputs["Roughness"].default_value = 0.2; p.inputs["Metallic"].default_value = 0.7
    else:                  # bevelled cells, faint gaps, random cells light up and fade (slow twinkle)
        edge, rnd = hex_cells(N, L, uv, 5.0)
        L.new(mr(N, L, edge, 0.0, 0.1, 0.0, 1.0), bump.inputs["Height"]); bump.inputs["Strength"].default_value = 0.45
        gap = mr(N, L, edge, 0.02, 0.05, 1.0, 0.0)
        t = N.new("ShaderNodeValue"); t.label = "time (frame / 60)"
        fc = t.outputs[0].driver_add("default_value"); fc.driver.type = "SCRIPTED"; fc.driver.expression = "frame / 60"
        ph = math_(N, L, "FRACT", math_(N, L, "SUBTRACT", math_(N, L, "MULTIPLY", rnd, 3.0), t.outputs[0]))
        # each cell is lit for a quarter of its 3 s cycle: fades in fast, fades out slowly
        lit = math_(N, L, "MINIMUM", mr(N, L, ph, 0.0, 0.03, 0.0, 1.0), mr(N, L, ph, 0.08, 0.25, 1.0, 0.0))
        face = math_(N, L, "MULTIPLY", lit, mr(N, L, edge, 0.05, 0.09, 0.0, 1.0))
        L.new(math_(N, L, "ADD", math_(N, L, "MULTIPLY", gap, 0.6), math_(N, L, "MULTIPLY", face, 1.6)), p.inputs["Emission Strength"])
        L.new(math_(N, L, "ADD", mr(N, L, rnd, 0.0, 1.0, 0.1, 0.2), math_(N, L, "MULTIPLY", lit, 0.25)), cm.inputs["Scale"])
    return m


# ------------------------------------------------------------------ the takes
# (key, label, corps name, corps rgb (reveal band, ring, undersuit, emblem), seam/emblem/ring strength, build)
VIOLET = CORPS["Violet"][1]
CORPS["Royal purple"] = ("royal purple", (0.2, 0.0, 1.0))
CORPS["Plum purple"] = ("deep plum", (0.15, 0.0, 0.42))
CORPS["Ultraviolet"] = ("ultraviolet", (0.06, 0.0, 1.0))
CORPS["Blue T1a"] = ("electric blue", (0.0, 0.16, 1.0))
CORPS["Blue T1b"] = ("cobalt", (0.0, 0.04, 1.0))
CORPS["Blue T1c"] = ("azure", (0.0, 0.36, 1.0))
RED_GLOW = (1.0, 0.02, 0.03)

R5 = [("C8b", "C8b (as before)", "Violet", "carbon weave", 3.0, lambda n, c: carbon(n, c)),
      ("C8bP1", "C8b in royal purple", "Royal purple", "carbon weave", 1.8, lambda n, c: carbon(n, c)),
      ("C8bP2", "C8b in deep plum", "Plum purple", "carbon weave", 1.5, lambda n, c: carbon(n, c)),
      ("C8bP3", "C8b in ultraviolet", "Ultraviolet", "carbon weave", 2.0, lambda n, c: carbon(n, c)),
      ("T1a", "circuit: navy + electric blue", "Blue T1a", "circuit, offset grid + pads", 2.2,
       lambda n, c: circuit(n, (0.002, 0.006, 0.03), c, 2.6, "a")),
      ("T1b", "circuit: steel black + cobalt", "Blue T1b", "circuit, crossed maze", 2.4,
       lambda n, c: circuit(n, (0.004, 0.006, 0.013), c, 3.0, "b")),
      ("T1c", "circuit: indigo + azure", "Blue T1c", "circuit, sparse + ringed pads", 2.0,
       lambda n, c: circuit(n, (0.008, 0.003, 0.035), c, 2.3, "c")),
      ("T2a", "hex: fine honeycomb", "Red", "hex 3px, flat, glowing gaps", 3.0, lambda n, c: hexplate(n, c, RED_GLOW, "a")),
      ("T2b", "hex: big domed tiles", "Red", "hex 8px, domed, inset outlines", 3.0, lambda n, c: hexplate(n, c, RED_GLOW, "b")),
      ("T2c", "hex: twinkling cells", "Red", "hex 5px, bevelled, cells light up", 3.0, lambda n, c: hexplate(n, c, RED_GLOW, "c"))]

TAKE = {}
for j, (dk, dname, cname, look, e, build) in enumerate(R5):
    ringm = set_corps(cname)
    rgb = CORPS[cname][1]
    EMBLEM.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 6.0 if dk == "C8b" else e
    T = add_forming(build(f"Suit5 {dk}", rgb), rgb)
    Sm = suit_mat(f"Suit5 {dk} seam", None, rgb, emit=e, solid=True)          # seams form with the suit too
    place(dk, f"{dk}  {dname}", f"{CORPS[cname][0]}, {look}", 0.0, j * 1.6,
          lambda objs, tag, T=T, Sm=Sm: new_suit(objs, tag, "C8b", T, Sm))
    recolour_ring(dk, ringm)
    TAKE[dk] = (cname, e)


# ------------------------------------------------------------------ the reveal band in the corps colour on EVERY piece
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
    dk = next((k for k in TAKE if o.name.startswith(f"S594 {k} ") or o.name.startswith(f"KL S594 {k} ")), None)
    if dk is None:
        continue
    for i, m in enumerate(o.data.materials):
        m2 = corps_copy(m, TAKE[dk][0])
        if m2 is not m:
            if o.data.users > 1:
                o.data = o.data.copy()
            o.data.materials[i] = m2

for dk, (cname, e) in TAKE.items():                           # every corps ring flares as the forming ends
    rm = bpy.data.materials.get(f"KL ring {cname}")
    if rm is None:
        continue
    base = 3.0 if dk == "C8b" else e
    s = rm.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
    for _f, _e in ((1, base), (FORM_END - 3, base), (FORM_END + 1, base * 10), (FORM_END + 10, base), (LOOP, base)):
        s.default_value = _e; s.keyframe_insert("default_value", frame=_f)

STEP = 1.6 * SPX
for nm, a, b in (("P", 0, 3), ("T1", 4, 6), ("T2", 7, 9)):
    cx = (a + b) / 2 * STEP
    cam(f"Cam row {nm}", (cx, -((b - a) * STEP * 0.8 + 3.5), 1.8), (cx, 0, 1.1), 35)
MIDX = (len(R5) - 1) / 2 * STEP
cam("Cam row R5", (MIDX, -30.0, 3.0), (MIDX, 0, 1.15), 35)
cam("Cam row R5 back", (MIDX, 30.0, 3.0), (MIDX, 0, 1.15), 35)
scene.frame_start, scene.frame_end = 1, LOOP
bpy.ops.mesh.primitive_plane_add(size=300, location=(MIDX, 0, 0))
g = bpy.context.active_object
for c in g.users_collection:
    c.objects.unlink(g)
link(g); g.name = "S855 floor"; g.data.materials.append(mat("S855 floor", (0.05, 0.055, 0.06), rough=0.8))
world = bpy.data.worlds.new("S855 world"); world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.03, 0.035, 0.045, 1)
scene.world = world
key = bpy.data.lights.new("S855 key", "AREA"); key.energy = 30000; key.size = 160
ko = link(bpy.data.objects.new("S855 key", key)); ko.location = (MIDX, -14, 9); ko.rotation_euler = (R(50), 0, 0)
rim = bpy.data.lights.new("S855 rim", "AREA"); rim.energy = 12000; rim.size = 160
ro = link(bpy.data.objects.new("S855 rim", rim)); ro.location = (MIDX, 14, 7); ro.rotation_euler = (R(-50), 0, 0)
try:
    scene.render.engine = "BLENDER_EEVEE"
except Exception:
    scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x, scene.render.resolution_y = 1600, 900
try:
    scene.view_settings.view_transform = "Standard"
except Exception:
    pass
scene.camera = bpy.data.objects["Cam row P"]
scene.frame_set(60)
try:
    bpy.ops.outliner.orphans_purge(do_recursive=True)
except Exception:
    pass
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("saved", OUT)
