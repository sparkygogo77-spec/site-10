# Pass 832: icon rings round 3 (Chat C, 2026-10-15, range 800-899).
# J on 825: "R19f [I1b] only not completely boring ring faces". The other nine 825 faces are dropped. R19f and I1b stay
# as they were (for comparison); seven new faces go further: deeper relief, glowing cores, lines that don't run where you
# expect. No black, no white core, nothing taken from an existing emblem.
#   F1 split halo: R19f grown - the halo broken into 8 arcs of two heights, a diamond plate with a glowing inset line,
#      a raised core                 F2 vortex: three gold spiral arms over ripple, winding into a bright core
#   F3 cut key: I1b's octagon gem cut into 16 star facets in three tiers, held by four raised gold claws
#   F4 circuit: gold traces from random walks that turn 45 or 90 degrees at random, glowing nodes at their ends
#   F5 lantern window: a small gold lantern in relief, its cage glowing inside
#   F6 shards: two long crystals laid on a slant, a gold slash beside them
#   F7 R19f + I1b: R19f's square plate and halo, I1b's octagon gem raised in the middle, four gems on the halo
# Cameras "Cam <code> <name>", "... face", "Cam row game", "Cam all". Builds LanternLive\lanterns\icon_rings3.blend.
import math, os
import bpy
import numpy as np
from mathutils import Matrix

R = math.radians
OUT = os.path.join(FOLDER, "lanterns", "icon_rings3.blend")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
if bpy.data.filepath:
    try:
        bpy.ops.wm.save_mainfile()
    except Exception as e:
        print("save current:", e)
old = bpy.data.scenes.get("Icon Rings 3")
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new("Icon Rings 3")
col = scene.collection
scene.render.fps = 20
win = bpy.context.window
if win:
    win.scene = scene
LOOP = 200


def link(o):
    col.objects.link(o)
    return o


def cam(name, loc, look, lens=40):
    c = link(bpy.data.objects.new(name, bpy.data.cameras.new(name)))
    c.location = loc; c.data.lens = lens
    d = np.array(look, float) - np.array(loc, float)
    c.rotation_euler = (math.atan2(math.hypot(d[0], d[1]), -d[2]), 0, math.atan2(d[1], d[0]) - math.pi / 2)
    return c


def lin(rgb):
    return tuple((np.asarray(rgb, float) / 255.0) ** 2.2)


# ------------------------------------------------------------------ the light-up: scene["lit"], keyframed
scene["lit"] = 0.0
for f, v in ((1, 0.0), (20, 0.0), (44, 0.95), (52, 1.15), (62, 1.05), (LOOP, 1.05)):          # J: stays bright, never fades
    scene["lit"] = v; scene.keyframe_insert('["lit"]', frame=f)
try:
    for fc in scene.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = "BEZIER"
except Exception:
    pass


def lit_value(nodes):
    v = nodes.new("ShaderNodeValue")
    fc = v.outputs[0].driver_add("default_value")
    var = fc.driver.variables.new(); var.name = "lit"; var.type = "SINGLE_PROP"
    var.targets[0].id_type = "SCENE"; var.targets[0].id = scene; var.targets[0].data_path = '["lit"]'
    fc.driver.expression = "lit"
    return v.outputs[0]


def attr(N, name, kind="Fac"):
    a = N.new("ShaderNodeAttribute"); a.attribute_name = name
    return a.outputs[kind]


def ring_mat(name, metal, rough, emit_k, coat=0.0):
    """Colour from the voxel; emission = glow x (the light front has reached this voxel) x lit x emit_k."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    p = N.get("Principled BSDF")
    c = attr(N, "col", "Color")
    L.new(c, p.inputs["Base Color"])
    p.inputs["Metallic"].default_value = metal; p.inputs["Roughness"].default_value = rough
    if coat:
        try:
            p.inputs["Coat Weight"].default_value = coat
        except Exception:
            pass
    if emit_k:
        lit = lit_value(N)
        # front: the light spreads from the core (dist 0) outward: reached = clamp((lit * 1.5 - dist) * 4)
        a = N.new("ShaderNodeMath"); a.operation = "MULTIPLY"; a.inputs[1].default_value = 1.5; L.new(lit, a.inputs[0])
        b = N.new("ShaderNodeMath"); b.operation = "SUBTRACT"; L.new(a.outputs[0], b.inputs[0]); L.new(attr(N, "dist"), b.inputs[1])
        cpl = N.new("ShaderNodeMath"); cpl.operation = "MULTIPLY"; cpl.use_clamp = True; cpl.inputs[1].default_value = 4.0
        L.new(b.outputs[0], cpl.inputs[0])
        g = N.new("ShaderNodeMath"); g.operation = "MULTIPLY"; L.new(cpl.outputs[0], g.inputs[0]); L.new(attr(N, "glow"), g.inputs[1])
        g2 = N.new("ShaderNodeMath"); g2.operation = "MULTIPLY"; L.new(g.outputs[0], g2.inputs[0]); L.new(lit, g2.inputs[1])
        g3 = N.new("ShaderNodeMath"); g3.operation = "MULTIPLY"; g3.inputs[1].default_value = emit_k; L.new(g2.outputs[0], g3.inputs[0])
        L.new(attr(N, "ecol", "Color"), p.inputs["Emission Color"]); L.new(g3.outputs[0], p.inputs["Emission Strength"])
    return m


METAL, GOLD, GEM, CORE, DARK, BANDTEX = range(6)
TEXDIR = os.path.join(FOLDER, "suit_tex")
RTEX = [("X5E", "x5_emerald", "X5 ripple emerald", 5), ("X5N", "x5_neon", "X5 ripple neon", 5),
        ("X3D1", "x3d1_emerald", "X3D1 ripples", 5), ("W1", "w1_neon", "W1 neon weave", 4), ("H1", "h1_neon", "H1 neon hex", 4)]


def tex_gem_mat(name, key, ft, emit=5.0):
    """The emerald material, with an animated strip on it: UV per voxel face (one tile per 4 model px), frame k of n
    crossfaded into k+1 (the game's interpolate), multiplied by the voxel's own shade so the steps still read."""
    m = ring_mat(name, 0.0, 0.12, emit, coat=0.6)
    N, L = m.node_tree.nodes, m.node_tree.links
    im = bpy.data.images.get("ring strip " + key)
    if im is None:
        im = bpy.data.images.load(os.path.join(TEXDIR, key + "_strip.png")); im.name = "ring strip " + key
        try:
            im.pack()
        except Exception:
            pass
    n = max(1, im.size[1] // max(1, im.size[0]))
    uvn = N.new("ShaderNodeUVMap"); uvn.uv_map = "uv"
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(uvn.outputs["UV"], sep.inputs[0])
    fu = N.new("ShaderNodeMath"); fu.operation = "FRACT"; L.new(sep.outputs[0], fu.inputs[0])
    fv = N.new("ShaderNodeMath"); fv.operation = "FRACT"; L.new(sep.outputs[1], fv.inputs[0])
    tick = N.new("ShaderNodeValue"); fc = tick.outputs[0].driver_add("default_value")
    fc.driver.type = "SCRIPTED"; fc.driver.expression = f"frame/{ft}"
    fl = N.new("ShaderNodeMath"); fl.operation = "FLOOR"; L.new(tick.outputs[0], fl.inputs[0])
    wv = N.new("ShaderNodeMath"); wv.operation = "SUBTRACT"; L.new(tick.outputs[0], wv.inputs[0]); L.new(fl.outputs[0], wv.inputs[1])
    outs = []
    for step in (0, 1):
        tex = N.new("ShaderNodeTexImage"); tex.image = im; tex.interpolation = "Closest"
        k = N.new("ShaderNodeMath"); k.operation = "ADD"; k.inputs[1].default_value = step; L.new(fl.outputs[0], k.inputs[0])
        km = N.new("ShaderNodeMath"); km.operation = "FLOORED_MODULO"; km.inputs[1].default_value = n; L.new(k.outputs[0], km.inputs[0])
        a_ = N.new("ShaderNodeMath"); a_.operation = "SUBTRACT"; a_.inputs[0].default_value = n - 1; L.new(km.outputs[0], a_.inputs[1])
        b_ = N.new("ShaderNodeMath"); b_.operation = "ADD"; L.new(fv.outputs[0], b_.inputs[0]); L.new(a_.outputs[0], b_.inputs[1])
        c_ = N.new("ShaderNodeMath"); c_.operation = "DIVIDE"; c_.inputs[1].default_value = n; L.new(b_.outputs[0], c_.inputs[0])
        cmb = N.new("ShaderNodeCombineXYZ"); L.new(fu.outputs[0], cmb.inputs[0]); L.new(c_.outputs[0], cmb.inputs[1])
        L.new(cmb.outputs[0], tex.inputs["Vector"]); outs.append(tex)
    mc = N.new("ShaderNodeMix"); mc.data_type = "RGBA"; L.new(wv.outputs[0], mc.inputs["Factor"])
    L.new(outs[0].outputs["Color"], mc.inputs[6]); L.new(outs[1].outputs["Color"], mc.inputs[7])
    # shade: the voxel colour scaled up (its green runs ~0.03-0.45 linear), multiplied onto the texture
    sh = N.new("ShaderNodeVectorMath"); sh.operation = "SCALE"; sh.inputs["Scale"].default_value = 3.2
    L.new(attr(N, "col", "Color"), sh.inputs[0])
    mul = N.new("ShaderNodeMix"); mul.data_type = "RGBA"; mul.blend_type = "MULTIPLY"; mul.inputs["Factor"].default_value = 0.85
    L.new(mc.outputs[2], mul.inputs[6]); L.new(sh.outputs[0], mul.inputs[7])
    p = N.get("Principled BSDF")
    L.new(mul.outputs[2], p.inputs["Base Color"])
    em = N.new("ShaderNodeMix"); em.data_type = "RGBA"; em.blend_type = "MULTIPLY"; em.inputs["Factor"].default_value = 0.5
    L.new(mc.outputs[2], em.inputs[6]); L.new(sh.outputs[0], em.inputs[7])
    L.new(em.outputs[2], p.inputs["Emission Color"])
    return m


TEXMAT = {}
MATS = [ring_mat("SR band metal", 0.85, 0.38, 2.0), ring_mat("SR gold", 1.0, 0.24, 0.0),
        ring_mat("SR emerald", 0.0, 0.12, 5.0, coat=0.6), ring_mat("SR core", 0.0, 0.1, 3.6, coat=0.6),
        ring_mat("SR deep green", 0.0, 0.3, 1.2)]

# ------------------------------------------------------------------ palettes
METALS = {"silver": (150, 152, 156), "steel": (112, 118, 126), "gunmetal": (62, 66, 72), "pale": (196, 198, 202),
          "stone": (128, 130, 128), "gold": (206, 160, 56), "white": (214, 214, 208)}
GOLD_C = (240, 192, 66)
EM_DARK, EM_LIGHT = np.array((8, 82, 32), float), np.array((40, 196, 84), float)
CORE_C = (96, 255, 132)          # saturated, never white
DARK_C = (6, 48, 20)

# ------------------------------------------------------------------ the takes (every one different)
BODIES = [
    # ---- J's picks, refined
    dict(code="P01", name="Faithful plus", shape="octa", metal="stone", rings=2, core="2", relief="frames", bars="solid",
         sides="solid", corners="square", glow="rings", stone="speckle", bevel=True, engrave=True),
    dict(code="P02", name="Gold-trimmed plus", shape="octa", metal="silver", trim="gold", rope=True, rings=2, core="2",
         relief="frames", bars="solid", sides="solid", corners="square", bezel=True, glow="all", stone="speckle", bevel=True),
    dict(code="P03", name="Deep frame plus", shape="octa", metal="gunmetal", frame=2, rings=1, core="facet",
         relief="frames", bars="solid", sides="solid", corners="square", glow="all", stone="malachite", bevel=True, engrave=True),
    dict(code="P04", name="Radiant updated", shape="round", metal="pale", rings=3, core="facet", relief="facet",
         bars="gradient", sides="gradient", corners="square", extra="spokes8", glow="all", stone="speckle", bevel=True),
    # ---- Faithful family
    dict(code="N01", name="Faithful gold body", shape="octa", metal="gold", rings=2, core="2", relief="frames",
         bars="solid", sides="solid", corners="square", glow="rings", stone="malachite", bevel=True),
    dict(code="N02", name="Faithful shoulder inlays", shape="octa", metal="stone", inlay=True, rings=2, core="plus",
         relief="frames", bars="solid", sides="cells", corners="square", glow="rings", stone="speckle", bevel=True),
    dict(code="N03", name="Faithful three rings", shape="cathedral", metal="steel", rings=3, core="facet",
         relief="pyramid", bars="solid", sides="gradient", corners="square", glow="core", stone="speckle", engrave=True),
    dict(code="N04", name="Faithful light lines", shape="stepped", metal="stone", rings=2, core="2", relief="frames",
         bars="line", sides="solid", corners="notched", glow="bars", stone="malachite", engrave=True),
    # ---- Gold-trimmed family
    dict(code="N05", name="Gold edge engraved", shape="knife", metal="steel", trim="gold", engrave=True, rings=2,
         core="diamond", relief="dome", bars="gradient", sides="solid", corners="square", glow="rings", stone="speckle", bevel=True),
    dict(code="N06", name="Two-tone", shape="octa", metal="silver", two_tone=True, rings=3, core="2", relief="frames",
         bars="cells", sides="solid", corners="square", bezel=True, glow="all", stone="malachite", bevel=True),
    dict(code="N07", name="Rope and claws", shape="taper", metal="pale", rope=True, rings=2, core="plus", relief="frames",
         bars="solid", sides="cells", corners="claws", bezel=True, glow="rings", stone="speckle"),
    dict(code="N08", name="White gold channel", shape="channel", metal="white", trim="gold", rings=2, core="facet",
         relief="frames", bars="solid", sides="gradient", corners="square", glow="bars", stone="speckle", bevel=True),
    # ---- Deep frame family
    dict(code="N09", name="Deep frame studs", shape="octa", metal="gunmetal", frame=2, rings=1, core="big", relief="frames",
         bars="solid", sides="solid", corners="studs", glow="all", stone="malachite", bevel=True),
    dict(code="N10", name="Deep frame gold body", shape="cathedral", metal="gold", frame=2, rings=1, core="cushion",
         relief="frames", bars="double", sides="solid", corners="square", glow="all", stone="speckle", bevel=True),
    dict(code="N11", name="Deep frame vault", shape="round", metal="steel", frame=2, rings=2, core="big", relief="inset",
         bars="line", sides="solid", corners="square", glow="bars", stone="malachite", engrave=True),
    dict(code="N12", name="Deep frame cathedral", shape="cathedral", metal="gunmetal", frame=2, rings=2, core="facet",
         relief="pyramid", bars="cells", sides="cells", corners="notched", glow="rings", stone="speckle", inlay=True),
    # ---- Radiant family
    dict(code="N13", name="Radiant eight", shape="round", metal="silver", rings=2, core="plus", relief="facet",
         bars="gradient", sides="gradient", corners="square", extra="spokes8", glow="all", stone="malachite", bevel=True),
    dict(code="N14", name="Radiant sunburst", shape="ribbed", metal="pale", rings=3, core="diamond", relief="dome",
         bars="gradient", sides="gradient", corners="square", extra="spokes", glow="all", stone="speckle", bevel=True),
    dict(code="N15", name="Radiant gold", shape="round", metal="gold", rings=2, core="facet", relief="facet",
         bars="solid", sides="solid", corners="square", extra="spokes", glow="rings", stone="malachite", bevel=True, rope=True),
    dict(code="N16", name="Radiant veins", shape="veins", metal="gunmetal", rings=2, core="facet", relief="facet",
         bars="line", sides="gradient", corners="square", extra="spokes8", glow="all", stone="speckle"),
]




def stone_tex(rgb, u, v, style, rng):
    """J's photo: the stone is mottled, with dark flecks (speckle) or soft bands (malachite)."""
    rgb = np.asarray(rgb, float)
    if style == "speckle":
        r = rng.random()
        k = rng.uniform(0.72, 1.22)
        if r < 0.13:
            k = 0.38
        elif r > 0.95:
            k = 1.45
        return rgb * k
    if style == "malachite":
        band = 0.5 + 0.5 * math.sin(0.95 * u + 0.45 * v + 1.8 * math.sin(0.38 * v + 0.2 * u))
        return (EM_DARK * 0.65) * (1 - band) + rgb * 1.18 * band
    return rgb


# ------------------------------------------------------------------ voxel builder (0.25 model px per voxel)
def build_ring(t, rng):
    """Returns occupancy-kind grid, colour grid (linear rgb), glow and dist grids, indexed [x, y, z].
    x: across the face / along the finger (band width); y: across the face; z: up (face on top)."""
    fw = t.get("fw", 24); bh = t.get("bh", 5); frame = t.get("frame", 1)
    NX, NY, NZ = fw + 8, max(fw + 8, 42), 52
    K = np.full((NX, NY, NZ), -1, np.int8)
    C = np.zeros((NX, NY, NZ, 3), np.float32)
    GL = np.zeros((NX, NY, NZ), np.float32); DI = np.zeros((NX, NY, NZ), np.float32)
    xc, yc, zc = NX / 2, NY / 2, 18.0
    ri = 10.4
    metal = np.array(METALS[t["metal"]], float)
    shape = t["shape"]

    def put(x, y, z, k, rgb, glow=0.0, dist=0.0, noise=0.06):
        if 0 <= x < NX and 0 <= y < NY and 0 <= z < NZ:
            K[x, y, z] = k
            c = np.asarray(rgb, float) * (1.0 + rng.uniform(-noise, noise))
            C[x, y, z] = lin(np.clip(c, 0, 255)); GL[x, y, z] = glow; DI[x, y, z] = dist

    # ---- the band (a loop round the x axis, face on top)
    t_top, t_bot, w_top, w_bot = 6.0, 3.0, 18.0, 9.0
    if shape == "taper":
        t_bot, w_bot = 2.4, 6.0
    if shape == "cathedral":
        t_top, w_top = 8.0, 20.0
    for x in range(NX):
        for y in range(NY):
            for z in range(NZ):
                dy, dz = y + 0.5 - yc, z + 0.5 - zc
                th = math.atan2(dy, dz)                       # 0 at the top
                f = (1 - math.cos(th)) / 2                    # 0 top .. 1 bottom
                if shape == "stepped":
                    f = math.floor(f * 5) / 5
                if shape == "cathedral":
                    ff = min(1.0, max(0.0, (f - 0.12) / 0.5))
                else:
                    ff = f
                tt = t_top + (t_bot - t_top) * ff ** 0.8
                ww = w_top + (w_bot - w_top) * ff
                xcen = xc + (2.5 * math.sin(2 * th) if shape == "twist" else 0.0)
                ax = abs(x + 0.5 - xcen)
                if ax > ww / 2:
                    continue
                if shape in ("octa", "stepped", "cathedral", "split", "channel", "ribbed", "gallery", "veins", "taper", "twist"):
                    r = max(abs(dy), abs(dz), (abs(dy) + abs(dz)) / 1.35)
                else:
                    r = math.hypot(dy, dz)
                if shape == "ribbed" and int((th + math.pi) * ri / 2.0) % 2 == 0:
                    tt += 1.2
                if shape == "knife":
                    tt = tt * (1 - 0.55 * (ax / (ww / 2)) ** 2) + 0.6
                if not (ri <= r <= ri + tt):
                    continue
                if shape == "split" and f < 0.33 and ax < 2.0:
                    continue
                if shape == "gallery" and 0.1 < f < 0.32 and r > ri + 1.2 and (int(x + 0.5 * z) % 4 == 0) and ax < ww / 2 - 1.5:
                    continue
                k, rgb, gl, di = METAL, metal * (0.82 + 0.3 * (r - ri) / max(tt, 1e-3)), 0.0, 0.0
                if t.get("trim") == "gold" and ax > ww / 2 - 1.2:
                    k, rgb = GOLD, GOLD_C
                if shape == "channel" and r > ri + tt - 1.5 and ax < 1.2:
                    k, rgb, gl, di = GEM, EM_LIGHT, 0.8, 1.0 + f
                if shape == "veins" and r > ri + tt - 1.2 and int((th + math.pi) * ri / 1.6) % 4 == 0:
                    k, rgb, gl, di = GEM, EM_LIGHT * 0.9, 0.7, 1.0 + f
                if t.get("two_tone") and f > 0.42 and k == METAL:
                    k, rgb = GOLD, np.array(GOLD_C) * 0.92
                if t.get("engrave") and k == METAL and r > ri + tt - 1.0 and abs(ax - (ww / 2 - 2.2)) < 0.55:
                    rgb = np.asarray(rgb, float) * 0.5
                if t.get("rope") and ax > ww / 2 - 1.2:
                    k = GOLD
                    rgb = np.array(GOLD_C) * (0.72 if int((th + math.pi) * ri / 1.1 + x * 0.5) % 2 else 1.05)
                if t.get("inlay") and k == METAL and 0.07 < f < 0.24 and r > ri + tt - 1.0 and ax < 1.6 and int((th + math.pi) * ri / 1.5) % 3 == 0:
                    k, rgb, gl, di = GEM, EM_LIGHT, 0.6, 0.95
                if k == METAL and r < ri + 1.0:
                    rgb = np.asarray(rgb, float) * 1.18             # polished inside
                put(x, y, z, k, rgb, gl, di, noise=0.1 if k == METAL else 0.05)

    # ---- the face
    zf = int(round(zc + ri + t_top)) - 1
    x0, y0 = int(xc - fw / 2), int(yc - fw / 2)
    cs = fw - 2 * bh
    sx = (fw - cs) // 2
    dmax = (cs - 1) // 2
    gold_d = {0} | {2 * k for k in range(1, t["rings"]) if 2 * k < dmax}
    if t["rings"] >= 3 and cs >= 14:
        gold_d = {0} | {k * max(2, dmax // t["rings"]) for k in range(1, t["rings"])}
    relief = t["relief"]
    if t.get("bezel"):
        for u in range(-1, fw + 1):
            for v in range(-1, fw + 1):
                if u in (-1, fw) or v in (-1, fw):
                    for z in (zf - 1, zf):
                        put(x0 + u, y0 + v, z, GOLD, np.array(GOLD_C) * 0.85)
    for u in range(fw):
        for v in range(fw):
            corner = (u in (0, fw - 1)) and (v in (0, fw - 1))
            if t["corners"] == "notched" and (min(u, fw - 1 - u) < 2 and min(v, fw - 1 - v) < 2):
                continue
            cu, cv = u + 0.5 - fw / 2, v + 0.5 - fw / 2
            dist = max(abs(cu), abs(cv)) / (fw / 2)
            # base plate (gold, 2 thick)
            for z in (zf, zf + 1):
                put(x0 + u, y0 + v, z, GOLD, np.array(GOLD_C) * 0.8, 0.0, dist)
            kind, rgb, h, glow = GOLD, GOLD_C, 2, 0.0
            on_frame = min(u, v, fw - 1 - u, fw - 1 - v) < frame
            in_bar = v < bh or v >= fw - bh
            if on_frame:
                kind, h = GOLD, 2
            elif in_bar:
                bv = v if v < bh else fw - 1 - v                 # 0 at the outer edge
                rim = bv == bh - 1 or bv < frame
                if rim:
                    kind, h = GOLD, 2
                else:
                    kind, h = GEM, 1
                    tt_ = abs(cu) / (fw / 2)
                    rgb = EM_DARK + (EM_LIGHT - EM_DARK) * (0.55 if t["bars"] != "gradient" else 1 - tt_)
                    glow = {"bars": 0.9, "all": 0.7}.get(t["glow"], 0.25)
                    if t["bars"] == "cells" and (u - frame) % 5 == 4:
                        kind, h, glow = GOLD, 2, 0.0
                    if t["bars"] == "line" and bv == (bh - 1 + frame) // 2:
                        kind, rgb, glow = CORE, CORE_C, 0.8
                    if t["bars"] == "double" and bv == frame:
                        kind, h, glow = GOLD, 2, 0.0
            else:
                in_center = sx <= u < fw - sx
                if not in_center:
                    su = u if u < sx else fw - 1 - u
                    if su == sx - 1:
                        kind, h = GOLD, 2
                    else:
                        kind, h = GEM, 1
                        vv = (v - bh) / max(1, fw - 2 * bh - 1)
                        rgb = EM_DARK + (EM_LIGHT - EM_DARK) * (0.45 if t["sides"] != "gradient" else 0.2 + 0.8 * (1 - abs(vv - 0.5) * 2))
                        glow = {"all": 0.7, "bars": 0.35}.get(t["glow"], 0.25)
                        if t["sides"] == "cells" and (v - bh) % 4 == 3:
                            kind, h, glow = GOLD, 2, 0.0
                else:
                    a_, b_ = u - sx, v - bh
                    d = min(a_, b_, cs - 1 - a_, cs - 1 - b_)
                    if d in gold_d:
                        kind, h, glow = GOLD, 2, 0.0
                    else:
                        kind, h = GEM, 1
                        rgb = EM_DARK + (EM_LIGHT - EM_DARK) * (d / max(1, dmax)) ** 0.9
                        glow = {"rings": 0.75, "all": 0.8, "bars": 0.45}.get(t["glow"], 0.2) * (0.4 + 0.6 * d / max(1, dmax))
                        core = False
                        ccu, ccv = a_ + 0.5 - cs / 2, b_ + 0.5 - cs / 2
                        if t["core"] == "2":
                            core = d >= dmax
                        elif t["core"] == "plus":
                            core = (abs(ccu) < 1 and abs(ccv) < 2.6) or (abs(ccv) < 1 and abs(ccu) < 2.6)
                        elif t["core"] == "diamond":
                            core = abs(ccu) + abs(ccv) <= 2.6
                        elif t["core"] == "big":
                            core = max(abs(ccu), abs(ccv)) <= 2.0
                        elif t["core"] == "cushion":
                            core = max(abs(ccu), abs(ccv)) <= 2.0 and abs(ccu) + abs(ccv) <= 3.6
                        if core:
                            kind, rgb, glow = CORE, CORE_C, 1.0
                        if t.get("extra") in ("spokes", "spokes8") and not core and abs(abs(ccu) - abs(ccv)) < 0.6 and d >= 1:
                            kind, h, glow = GOLD, 2, 0.0
                        if t.get("extra") == "spokes8" and not core and min(abs(ccu), abs(ccv)) < 0.6 and d >= 1:
                            kind, h, glow = GOLD, 2, 0.0
                        if t["core"] == "facet":
                            m_, s_ = max(abs(ccu), abs(ccv)), abs(ccu) + abs(ccv)
                            if m_ <= 3.6 and s_ <= 5.2:
                                kind = GEM; rgb = EM_DARK + (EM_LIGHT - EM_DARK) * min(1.0, 1.1 - m_ / 4.5)
                                h = 1 + int(round(3.2 - m_ * 0.7)); glow = max(glow, 0.7)
                                if m_ <= 1.0:
                                    kind, rgb, glow = CORE, CORE_C, 1.0
                    # relief inside the centre square
                    if relief == "pyramid":
                        h += min(d, dmax) // 2
                    elif relief == "dome":
                        h += int(round(2.5 * (1 - (max(abs(a_ + 0.5 - cs / 2), abs(b_ + 0.5 - cs / 2)) / (cs / 2)) ** 2)))
                    elif relief == "facet" and d >= 2:
                        h += min(3, d - 1)
            if relief == "inset" and kind == GOLD:
                h += 1
            if kind == GEM and t.get("stone"):
                rgb = stone_tex(rgb, u, v, t["stone"], rng)
            if kind == GOLD:
                edge = min(u, v, fw - 1 - u, fw - 1 - v)
                rgb = np.array(GOLD_C) * (0.86 if edge == 0 else 1.08 if not on_frame else 1.0)
                if t.get("bevel") and edge == 0 and h > 1:
                    h -= 1                                         # bevelled outer edge, as on J's photo
            if relief == "frames" and kind == GOLD and not on_frame:
                h += 0                                            # J's image: thin gold outlines standing proud
            for k in range(h):
                z = zf + 2 + k
                top = k == h - 1
                c_ = rgb if (top or kind != GOLD) else np.array(GOLD_C) * 0.85
                kk = kind if (top or kind == GOLD) else (DARK if kind == GEM else kind)
                if kind == CORE and not top:
                    kk, c_ = GEM, EM_LIGHT
                put(x0 + u, y0 + v, z, kk, c_, glow if top or kind == GEM else 0.0, dist, noise=0.04)
            # corner studs / claws
            if corner and t["corners"] == "studs":
                for k in range(3):
                    put(x0 + u, y0 + v, zf + 2 + h + k - 1, GOLD, GOLD_C)
    if t["corners"] == "claws":
        for (u, v) in ((-1, -1), (fw, -1), (-1, fw), (fw, fw)):
            for k in range(6):
                put(x0 + u, y0 + v, zf - 1 + k, GOLD, GOLD_C)
            du = 1 if u < 0 else -1; dv = 1 if v < 0 else -1
            put(x0 + u + du, y0 + v + dv, zf + 4, GOLD, GOLD_C)
    return K, C, GL, DI, (x0, y0, zf, fw)


# ------------------------------------------------------------------ original rings: face shapes, marks, band builds
MARK_ROWS = {
    "M1": ["......###......", ".....#...#.....", ".....#...#.....", "...#########...", "....#######....",
           "....##...##....", "....#..#..#....", "....#.###.#....", "....#..#..#....", "....##...##....",
           "....#######....", "...#########..."],
    "M2": [".......#.......", "......##.......", "......###......", ".....####......", ".....#####.....",
           "....###.###....", "....##...##....", "...##..#..##...", "...#..###..#...", "...#..###..#...",
           "...##..#..##...", "....##...##....", ".....#####....."],
}
MARK_ROWS["M7"] = ["..#.....#.....#..", "..##...#.#...##..", "..#.#.#...#.#.#..", "..#..#.....#..#..", "..#...........#..",
                   "..#############..", ".................", "..#############.."]
MARK_ROWS["M7"] = [r[1:16] for r in MARK_ROWS["M7"]]
MARK_ROWS["M9"] = ["#############", "............#", "##########..#", "#........#..#", "#.######.#..#", "#.#....#.#..#",
                   "#.#.##.#.#..#", "#.#..#.#.#..#", "#.####.#.#..#", "#......#.#..#", "########.#..#", ".........#..#",
                   "##########..#"]
MARK_ROWS["M9"] = ["." + r + "." for r in MARK_ROWS["M9"]]
MARK_NAMES = {"M0": "No icon", "M1": "Lantern", "M2": "Flame", "M3": "Oath star", "M4": "Rising chevrons", "M5": "Concentric square",
              "M6": "Eye of light", "M7": "Three-point crown", "M8": "Beacon", "M9": "Square spiral"}


def mark_mask(key):
    m = np.zeros((15, 15), bool)
    if key == "M0":
        return m
    if key in MARK_ROWS:
        for r, line in enumerate(MARK_ROWS[key][:15]):
            for c, ch in enumerate(line[:15]):
                m[c, 14 - r] = ch == "#"
        ys = np.where(m.any(axis=0))[0]
        return np.roll(m, int(round(7 - (ys.min() + ys.max()) / 2)), axis=1)
    for i in range(15):
        for j in range(15):
            x, y = i - 7, j - 7
            ax, ay = abs(x), abs(y)
            if key == "M3":
                m[i, j] = (ax == 0 and ay <= 6) or (ay == 0 and ax <= 6) or (ax + ay <= 2) or abs(ax + ay - 7) < 0.5
            elif key == "M4":
                m[i, j] = any(abs(y - (c - ax)) < 0.6 and ax <= 5 for c in (-3, 1, 5)) or max(ax, ay) == 7
            elif key == "M5":                      # J's own concentric square
                m[i, j] = max(ax, ay) in (7, 4) or max(ax, ay) <= 1
            elif key == "M6":                      # a lens-shaped eye with a bright pupil
                lens = abs(ay - (4.5 - ax * ax / 11.0)) < 0.6 and ax <= 7
                m[i, j] = lens or (ax <= 1 and ay <= 1)
            elif key == "M7":                      # three points on a band
                base = -4 <= y <= -3 and ax <= 6
                pts = any(abs(x - px) <= max(0, (y + 3) * -0.0 + (5 - y) * 0.25) and -3 <= y <= 5 - abs(px) // 3
                          for px in (-5, 0, 5))
                m[i, j] = base or (pts and y > -3)
            elif key == "M8":                      # a beacon: a tall line, two cross bars, a light on top
                m[i, j] = (ax == 0 and -6 <= y <= 3) or (y in (-2, 1) and ax <= 3) or (y >= 5 and ax + (y - 6) * 0 <= 1 and y <= 7)
            elif key == "M9":                      # a square spiral
                ring = max(ax, ay)
                m[i, j] = (ring % 2 == 1 and not (x == -ring and y == ring - 1 + 0 * x and ring > 1)) or (x == 0 and y == 0)
    return m


def face_metric(shape, x, y, R):
    ax, ay = abs(x), abs(y)
    if shape == "round":
        return math.hypot(x, y) / R
    if shape == "octagon":
        return max(ax, ay, (ax + ay) / 1.35) / R
    if shape == "emeraldcut":
        return max(ax / 0.78, ay, (ax / 0.78 + ay) / 1.45) / R
    if shape == "hexagon":
        return max(ax * 0.866 + ay * 0.5, ay) / R
    if shape == "diamond":
        return (ax + ay) / (R * 1.28)
    if shape == "cushion":
        return (ax ** 4 + ay ** 4) ** 0.25 / R
    if shape == "oval":
        return math.hypot(x / 1.1, y / 0.84) / R
    if shape == "shield":
        return max(math.hypot(x, max(0.0, y)) / R, (ax * 0.7 + max(0.0, -y)) / (R * 1.08)) if y < 0 else math.hypot(x, y * 0.95) / R
    return max(ax, ay) / R


def build_classic(t, rng):
    """Original rings: a face shape, a mark (light-cut A or gold inlay B), a band build; N04's line of light inside the
    bezel; a domed stone with faceted edges."""
    R = t.get("R", 12.0)
    NX, NY, NZ = 34, 42, 56
    K = np.full((NX, NY, NZ), -1, np.int8)
    C = np.zeros((NX, NY, NZ, 3), np.float32)
    GL = np.zeros((NX, NY, NZ), np.float32); DI = np.zeros((NX, NY, NZ), np.float32)
    xc, yc, zc, ri = NX / 2, NY / 2, 18.0, 10.4
    style = t["style"]
    band_rgb = np.array({"silver": (176, 180, 186), "emerald": (34, 92, 58), "gunmetal": (70, 74, 80)}[t.get("metal", "silver")], float)

    def put(x, y, z, k, rgb, glow=0.0, dist=0.0, noise=0.03):
        if 0 <= x < NX and 0 <= y < NY and 0 <= z < NZ:
            K[x, y, z] = k
            C[x, y, z] = lin(np.clip(np.asarray(rgb, float) * (1.0 + rng.uniform(-noise, noise)), 0, 255))
            GL[x, y, z] = glow; DI[x, y, z] = dist

    band = t.get("band", "chunky")
    t_top, t_bot, w_top, w_bot = {"chunky": (6.5, 4.5, 17.0, 12.0), "slim": (5.0, 2.4, 13.0, 7.0),
                                  "cathedral": (8.0, 3.0, 19.0, 9.0), "split": (6.0, 3.0, 17.0, 9.0)}[band]
    for x in range(NX):
        for y in range(NY):
            for z in range(NZ):
                dy, dz = y + 0.5 - yc, z + 0.5 - zc
                th = math.atan2(dy, dz); f = (1 - math.cos(th)) / 2
                ff = min(1.0, max(0.0, (f - 0.12) / 0.5)) if band == "cathedral" else f
                tt = t_top + (t_bot - t_top) * ff ** 0.8
                ww = w_top + (w_bot - w_top) * ff
                ax = abs(x + 0.5 - xc)
                if ax > ww / 2:
                    continue
                r = max(abs(dy), abs(dz), (abs(dy) + abs(dz)) / 1.3)
                tt_e = tt - 1.6 * max(0.0, (ax - (ww / 2 - 2.0)) / 2.0)
                if not (ri <= r <= ri + tt_e):
                    continue
                if band == "split" and f < 0.33 and ax < 2.0:
                    continue
                k, rgb = METAL, band_rgb * (0.85 + 0.25 * (r - ri) / tt)
                if t.get("goldline") and r > ri + tt_e - 1.0 and ax < 0.6:
                    k, rgb = GOLD, GOLD_C
                if style == "B" and ax > ww / 2 - 1.1:
                    k, rgb = GOLD, GOLD_C
                put(x, y, z, k, rgb)
    zf = int(round(zc + ri + t_top)) - 1
    mm = mark_mask(t["mark"])
    rim_n, stone_n = 1 - 2.2 / R, 1 - (3.2 + (1.4 if t.get("halo") else 0)) / R
    for u in range(-17, 17):
        for v in range(-17, 17):
            cu, cv = u + 0.5, v + 0.5
            rn = face_metric(t["face"], cu, cv, R)
            if rn > 1.0:
                continue
            X, Y = int(xc) + u, int(yc) + v
            dist = min(1.0, rn)
            for z in (zf, zf + 1):
                put(X, Y, z, METAL, band_rgb * 0.9, 0.0, dist)
            if rn > rim_n:
                bead = t.get("beads") and int(((math.atan2(cv, cu) + math.pi) / (2 * math.pi)) * 36) % 2 == 0
                for k in range(4 + (1 if bead else 0)):
                    gold = style == "B" or t.get("gloss") or (bead and k == 4)
                    put(X, Y, zf + 2 + k, GOLD if gold else METAL, GOLD_C if gold else band_rgb * 1.1)
                continue
            if t.get("halo") and rn > rim_n - 1.4 / R:     # a second line of light outside the stone
                for k in range(2):
                    put(X, Y, zf + 2 + k, CORE if k == 1 else GEM, CORE_C if k == 1 else EM_DARK, 0.8, dist)
                continue
            if rn > stone_n:
                for k in range(2):
                    put(X, Y, zf + 2 + k, CORE if k == 1 else GEM, CORE_C if k == 1 else EM_DARK, 0.7, dist)
                continue
            q = rn / stone_n
            sector = int(((math.atan2(cv, cu) + math.pi) / (2 * math.pi)) * t.get("facets", 8)) % 2
            h = 1 + int(round(1.6 * (1 - q ** 2))) + (1 if (sector and q > 0.78) else 0)
            rgb = EM_DARK + (EM_LIGHT - EM_DARK) * min(1.0, 0.55 + 0.6 * (1 - q) + (0.12 if sector else -0.05))
            mi, mj = u + 7, v + 7
            on_mark = 0 <= mi < 15 and 0 <= mj < 15 and mm[mi, mj]
            near = (not on_mark) and any(0 <= mi + a < 15 and 0 <= mj + b < 15 and mm[mi + a, mj + b]
                                         for a in (-1, 0, 1) for b in (-1, 0, 1))
            for k in range(h):
                top = k == h - 1
                kind, c_, gl = GEM, rgb * (1.0 if top else 0.7), 0.35 if top else 0.1
                if top and on_mark and style == "A":
                    kind, c_, gl = CORE, CORE_C, 1.0
                if top and near and style == "B":
                    kind, c_, gl = CORE, CORE_C, 0.8
                put(X, Y, zf + 2 + k, kind, c_, gl, dist * (0.3 if on_mark else 1.0))
            if on_mark and style == "B":
                put(X, Y, zf + 2 + h, GOLD, GOLD_C, 0.0, dist)
    return K, C, GL, DI, (int(xc) - int(R), int(yc) - int(R), zf, int(2 * R))


DARKM_C = (24, 24, 27)          # the icon's black bezel


def build_icon(t, rng):
    """The hotbar icon's head on R19d's band: gold frame, emerald texture panels top and bottom, black bezels with a
    gold line each side, the cut gem in the middle (no round stone)."""
    tt = dict(t); tt.update(face="square", mark="M0", style="A")
    K, C, GL, DI, (x0, y0, zf, fw) = build_classic(tt, rng)
    R = t.get("R", 12.0)
    NX, NY, NZ = K.shape
    xc, yc = NX // 2, NY // 2
    for u in range(-int(R), int(R)):
        for v in range(-int(R), int(R)):
            K[xc + u, yc + v, zf + 2:] = -1

    def put(x, y, z, k, rgb, glow=0.0, dist=0.0):
        K[x, y, z] = k; C[x, y, z] = lin(np.clip(np.asarray(rgb, float) * (1.0 + rng.uniform(-0.03, 0.03)), 0, 255))
        GL[x, y, z] = glow; DI[x, y, z] = dist
    gem = t["cut"]
    for u in range(-int(R), int(R)):
        for v in range(-int(R), int(R)):
            cu, cv = u + 0.5, v + 0.5
            X, Y = xc + u, yc + v
            au, av = abs(cu), abs(cv)
            col = []                                    # (kind, rgb, glow, dist) from the plate up
            if max(au, av) > R - 1.5:                   # gold frame, the tallest part
                col = [(GOLD, GOLD_C, 0, 1)] * 4
            elif av > R * 0.56:                         # emerald panels top and bottom (texture)
                col = [(BANDTEX, EM_DARK * 1.1, 0.55, 0.75)] * 2
            elif av > R * 0.48:                         # gold line between panel and middle
                col = [(GOLD, GOLD_C, 0, 1)] * 3
            elif au > R * 0.66:                         # black bezel
                col = [(METAL, DARKM_C, 0, 1)] * 3
            elif au > R * 0.56:                         # gold inner line
                col = [(GOLD, GOLD_C, 0, 1)] * 3
            else:
                gx, gy = cu / (R * 0.56), cv / (R * 0.48)          # gem space, -1..1
                if gem == "octagon":
                    q = max(abs(gx), abs(gy), (abs(gx) + abs(gy)) / 1.4)
                elif gem == "square":
                    q = max(abs(gx), abs(gy)) / 0.92
                elif gem == "emeraldcut":
                    q = max(abs(gx) / 0.74, abs(gy), (abs(gx) / 0.74 + abs(gy)) / 1.5)
                else:                                     # R19d's concentric square inside the frame
                    q = max(abs(gx), abs(gy)) / 0.95
                if q > 1.0:
                    col = [(METAL, DARKM_C, 0, 1)] * 2
                else:
                    if gem == "octagon":                  # domed like the icon's gem, a light corner top-left
                        h = 2 + int(round(2.2 * (1 - q * q)))
                    elif gem == "concentric":
                        h = 3
                    else:                                 # step cut: a flat table and three steps down
                        h = 5 if q < 0.36 else 4 if q < 0.6 else 3 if q < 0.82 else 2
                    rgb = EM_DARK + (EM_LIGHT - EM_DARK) * min(1.0, 0.45 + 0.65 * (1 - q))
                    col = [(GEM, rgb * 0.7, 0.1, q)] * (h - 1) + [(GEM, rgb, 0.4, q * 0.8)]
                    top = col[-1]
                    if gem == "concentric":
                        ring = max(abs(cu), abs(cv))
                        r_ = ring / (R * 0.48 * 0.95) * 7
                        if round(r_) in (7, 4) or r_ <= 1.3:
                            col[-1] = (CORE, CORE_C, 1.0, q * 0.3)
                    elif q < (0.3 if gem == "octagon" else 0.36):
                        col[-1] = (CORE, CORE_C, 1.0, 0.0)
                    if gem == "octagon" and -0.75 < gx < -0.35 and 0.35 < gy < 0.75:      # the icon's light corner
                        col.append((CORE, (150, 255, 170), 0.6, 0.1))
            for k, (kind, rgb, gl, di) in enumerate(col):
                put(X, Y, zf + 2 + k, kind, rgb, gl, di)
    return K, C, GL, DI, (x0, y0, zf, fw)


# ------------------------------------------------------------------ pass 832 faces (J: R19f and I1b are the only faces
# that aren't "completely boring"): deeper relief, more materials, lines that don't run where you expect.
def _circuit_mask(R, seed=832):
    """Gold traces from random walks: straight runs of 3-7 voxels, turning 45 or 90 degrees at random, ending in nodes."""
    rs = np.random.default_rng(seed)
    n = int(2 * R + 2)
    tr = np.zeros((n, n), bool); nodes = []
    dirs = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
    for w in range(7):
        a = rs.uniform(0, 2 * math.pi); r0 = R * 0.32
        x, y = R + r0 * math.cos(a), R + r0 * math.sin(a); d = int(rs.integers(0, 8))
        for seg in range(int(rs.integers(3, 6))):
            for _ in range(int(rs.integers(3, 8))):
                x += dirs[d][0]; y += dirs[d][1]
                xi, yi = int(round(x)), int(round(y))
                if not (2 <= xi < n - 2 and 2 <= yi < n - 2) or max(abs(xi - R), abs(yi - R)) > R * 0.86:
                    break
                tr[xi, yi] = True
            d = (d + int(rs.choice([-2, -1, 1, 2]))) % 8
        nodes.append((int(round(x)) - R, int(round(y)) - R))
    return tr, nodes


_CIRC = {}


def face832(lay, cu, cv, R, gem_col, panel, GOLDC, rng):
    au, av = abs(cu), abs(cv); r = math.hypot(cu, cv); rn = r / R
    th = math.atan2(cv, cu)
    CORE1 = [(CORE, np.array(CORE_C, float) * 0.85, 1.0, 0.0)]
    if lay == "F1":                                     # R19f grown: split halo of 8 arcs, diamond plate, pyramid core
        if rn > 1.0:
            return None
        if rn > 0.9:
            return GOLDC * 4
        if rn > 0.74:
            k = int(((th + math.pi) / (2 * math.pi)) * 8) % 8
            gap = abs(((th + math.pi) / (2 * math.pi) * 8) % 1 - 0.5) > 0.42
            return GOLDC * 2 if gap else gem_col(4 + (k % 2), 0.85, bright=True)
        d = (au + av) / (R * 0.98)
        if d > 1.0:
            return panel(2)
        if 0.74 < d < 0.82:
            return gem_col(5, 0.25, bright=True)            # the glowing inset line
        if d < 0.3:
            return gem_col(5, d, bright=True)[:-1] + CORE1 * (3 - int(d * 9)) if d < 0.3 else None
        return GOLDC * 4 if d > 0.9 else gem_col(4, d)
    if lay == "F2":                                     # vortex: three gold spiral arms over ripple into a bright core
        if rn > 1.0:
            return None
        if rn > 0.9:
            return GOLDC * 4
        if rn < 0.2:
            return gem_col(4, rn / 0.2, bright=True) + CORE1 * int(round(2 * (1 - rn / 0.2)))
        s = math.sin(3 * th + 7.5 * rn)
        if s > 0.55:
            return GOLDC * (3 + int(round(2 * (1 - rn))))
        if s > 0.1:
            return gem_col(3 + int(round(2 * (1 - rn))), rn, bright=rn < 0.4)
        return panel(2)
    if lay == "F3":                                     # I1b's key cut properly: star facets, gold claws at the corners
        oct_ = max(au, av, (au + av) / 1.41) / R
        if oct_ > 1.0:
            return None
        if oct_ > 0.9:
            return GOLDC * 4
        if au > R * 0.5 and av > R * 0.5 and math.hypot(au - R * 0.62, av - R * 0.62) < R * 0.14:
            return GOLDC * 7                            # four raised claws holding the gem
        q = max(au, av, (au + av) / 1.41) / (R * 0.74)
        if q > 1.0:
            return panel(3)
        sf = ((th + math.pi) / (2 * math.pi)) * 16
        sector = int(sf) % 16
        if abs(sf % 1 - 0.5) > 0.44 and q > 0.2:
            return GOLDC * 5                            # thin gold lines between the facets (check: facets read flat)
        band = 0 if q > 0.66 else 1 if q > 0.33 else 2
        h = 2 + 2 * band + (1 if (sector + band) % 2 else 0)
        lit = (sector + band) % 2 == 0
        return gem_col(h, q * (0.6 if lit else 1.0), glow_top=0.8 if lit else 0.3, bright=band == 2 and lit)
    if lay == "F4":                                     # circuit: gold traces that turn where you don't expect
        if max(au, av) > R:
            return None
        if max(au, av) > R * 0.9:
            return GOLDC * 4
        if "F4" not in _CIRC:
            _CIRC["F4"] = _circuit_mask(int(R))
        tr, nodes = _CIRC["F4"]
        xi, yi = int(math.floor(cu)) + int(R), int(math.floor(cv)) + int(R)
        if max(au, av) < R * 0.24:
            return gem_col(5, max(au, av) / (R * 0.24), bright=max(au, av) < R * 0.12)
        for nx, ny in nodes:
            if math.hypot(cu - nx - 0.5, cv - ny - 0.5) < 1.6:
                return GOLDC * 2 + CORE1 * 2               # glowing node at each trace's end
        if 0 <= xi < tr.shape[0] and 0 <= yi < tr.shape[1] and tr[xi, yi]:
            return GOLDC * 4
        return panel(2)
    if lay == "F5":                                     # a little lantern relief in gold, glowing inside its cage
        if max(au, av) > R:
            return None
        if max(au, av) > R * 0.9:
            return GOLDC * 4
        x, y = cu / R, cv / R                           # y up the face
        if abs(x) < 0.12 and 0.6 < y < 0.72:
            return GOLDC * 5                            # handle
        if 0.44 < y < 0.64 and abs(x) < 0.38 * (1 - (y - 0.44) / 0.3):
            return GOLDC * 6                            # domed cap (check: the lantern read as bars)
        if abs(x) < 0.46 and -0.62 < y < -0.48:
            return GOLDC * 6                            # base
        if abs(x) < 0.34 and -0.48 <= y <= 0.44:
            if abs(x) > 0.25 or any(abs(x - b) < 0.07 for b in (-0.1, 0.1)):
                return GOLDC * 6                        # cage bars
            return gem_col(4, abs(x) / 0.34, bright=True) + CORE1 * (1 if abs(y) < 0.3 else 0)
        return panel(2)
    if lay == "F6":                                     # shards: two long crystals laid on a slant, a gold slash
        if rn > 1.0:
            return None
        if rn > 0.9:
            return GOLDC * 4
        ca, sa = math.cos(R_(32)), math.sin(R_(32))
        a1 = cu * ca + cv * sa; b1 = -cu * sa + cv * ca
        q1 = max(abs(a1) / (R * 0.62), abs(b1) / (R * 0.2), (abs(a1) / (R * 0.62) + abs(b1) / (R * 0.2)) / 1.35)
        a2 = a1 + R * 0.25; b2 = b1 + R * 0.42
        q2 = max(abs(a2) / (R * 0.32), abs(b2) / (R * 0.11), (abs(a2) / (R * 0.32) + abs(b2) / (R * 0.11)) / 1.35)
        if q1 < 1.0:
            return gem_col(4 + int(round(3 * (1 - q1))), q1, bright=q1 < 0.35)
        if q2 < 1.0:
            return gem_col(3 + int(round(2 * (1 - q2))), q2, bright=q2 < 0.3)
        if abs(b1 - R * 0.36) < 0.9 and a1 > -R * 0.2:
            return GOLDC * 3
        return panel(2)
    if lay == "F7":                                     # R19f's plate and halo with I1b's octagon gem and four halo gems
        if rn > 1.0:
            return None
        if rn > 0.88:
            return GOLDC * 4
        if rn > 0.76:
            for k in range(4):
                if math.hypot(cu - R * 0.82 * math.cos(k * math.pi / 2 + math.pi / 4), cv - R * 0.82 * math.sin(k * math.pi / 2 + math.pi / 4)) < R * 0.11:
                    return gem_col(6, 0.3, bright=True)
            return gem_col(3, 0.9, bright=True)
        m = max(au, av) / (R * 0.66)
        if m > 1.0:
            return panel(2)
        if m > 0.92:
            return GOLDC * 4
        o = max(au, av, (au + av) / 1.41) / (R * 0.46)
        if o < 1.0:
            return gem_col(4 + int(round(2.2 * (1 - o * o))), o, bright=o < 0.3)
        if o < 1.12:
            return GOLDC * 5
        return gem_col(3, m)
    return None


def R_(d):
    return math.radians(d)


def build_head(t, rng):
    """Pass 825 heads: R19d's band, a new face per layout; no black anywhere, no white core (ripple covers it)."""
    tt = dict(t); tt.update(face="square", mark="M0", style="A")
    K, C, GL, DI, (x0, y0, zf, fw) = build_classic(tt, rng)
    R = t.get("R", 12.0)
    NX, NY, NZ = K.shape
    xc, yc = NX // 2, NY // 2
    for u in range(-int(R) - 1, int(R) + 1):
        for v in range(-int(R) - 1, int(R) + 1):
            K[xc + u, yc + v, zf + 2:] = -1
    lay = t["layout"]

    def put(x, y, z, k, rgb, glow=0.0, dist=0.0):
        K[x, y, z] = k; C[x, y, z] = lin(np.clip(np.asarray(rgb, float) * (1.0 + rng.uniform(-0.03, 0.03)), 0, 255))
        GL[x, y, z] = glow; DI[x, y, z] = dist
    GOLDC = [(GOLD, GOLD_C, 0, 1)]
    def gem_col(h, q, glow_top=0.45, bright=False):
        rgb = EM_DARK + (EM_LIGHT - EM_DARK) * min(1.0, 0.45 + 0.65 * (1 - q))
        top = (GEM, rgb * (1.25 if bright else 1.0), 1.0 if bright else glow_top, q * 0.6)
        return [(GEM, rgb * 0.7, 0.1, q)] * (h - 1) + [top]
    def panel(h=2):
        return [(BANDTEX, EM_DARK * 1.1, 0.55, 0.75)] * h
    for u in range(-int(R) - 1, int(R) + 1):
        for v in range(-int(R) - 1, int(R) + 1):
            cu, cv = u + 0.5, v + 0.5
            au, av = abs(cu), abs(cv)
            r = math.hypot(cu, cv)
            col = []
            if lay in ("I1b", "I3b"):
                if max(au, av) > R - 1.5:
                    col = GOLDC * 4
                elif av > R * 0.56:
                    col = panel()
                elif av > R * 0.48:
                    col = GOLDC * 3
                elif au > R * 0.66:
                    col = panel(3)                             # I3b: ripple over the old black sides; I1b too (no black)
                elif au > R * 0.56:
                    col = GOLDC * 3
                else:
                    gx, gy = cu / (R * 0.56), cv / (R * 0.48)
                    if lay == "I1b":
                        q = max(abs(gx), abs(gy), (abs(gx) + abs(gy)) / 1.4)
                    else:
                        q = max(abs(gx) / 0.74, abs(gy), (abs(gx) / 0.74 + abs(gy)) / 1.5)
                    if q > 1.0:
                        col = panel(2)                         # around the gem: ripple, not black
                    elif lay == "I1b":
                        col = gem_col(2 + int(round(2.2 * (1 - q * q))), q, bright=q < 0.3)   # the key is ripple, lit
                    else:
                        h = 5 if q < 0.36 else 4 if q < 0.6 else 3 if q < 0.82 else 2
                        col = gem_col(h, q, bright=q < 0.36)
            elif lay in ("R19e", "R19f"):
                rn = r / R
                if rn > 1.0:
                    continue
                if rn > 0.88:
                    col = GOLDC * 4
                elif rn > 0.76:
                    col = panel(2) if lay == "R19e" else gem_col(3, 0.9, bright=True)
                else:
                    m = max(au, av) / (R * 0.66)
                    if m > 1.0:
                        col = panel(2)
                    elif lay == "R19e":                        # a stepped concentric square: four ripple terraces, gold lines
                        step = 0 if m > 0.75 else 1 if m > 0.5 else 2 if m > 0.25 else 3
                        edge = any(abs(m - e) < 0.05 for e in (0.25, 0.5, 0.75))
                        col = GOLDC * (3 + step) if edge else gem_col(2 + step, m, bright=step == 3)
                    else:                                      # a raised square plate, a glowing square line, a square core
                        if 0.62 < m < 0.72 or m < 0.2:
                            col = gem_col(5, 0.2, bright=True)
                        elif m > 0.92:
                            col = GOLDC * 4
                        else:
                            col = gem_col(4, m)
            elif lay.startswith("F"):
                col = face832(lay, cu, cv, R, gem_col, panel, GOLDC, rng)
                if col is None:
                    continue
            else:
                shape = {"N1": "octagon", "N2": "square", "N3": "square", "N4": "square", "N5": "square", "N6": "cushion", "N7": "shield"}[lay]
                rn = face_metric(shape, cu, cv, R)
                if rn > 1.0:
                    continue
                if rn > 0.9:
                    col = GOLDC * 4
                elif lay == "N1":                              # octagon full ripple dome
                    col = gem_col(2 + int(round(3 * (1 - rn * rn))), rn, bright=rn < 0.22)
                elif lay == "N2":                              # an X of gold, four ripple triangles, a raised diamond gem
                    d = (au + av) / R
                    if d < 0.38:
                        col = gem_col(6 - int(d * 6), d, bright=d < 0.15)
                    elif abs(au - av) < 1.0:
                        col = GOLDC * 4
                    else:
                        col = panel(3)
                elif lay == "N3":                              # a gold plus, four ripple quadrants, a centre gem
                    if max(au, av) < R * 0.24:
                        col = gem_col(5, max(au, av) / (R * 0.24), bright=max(au, av) < R * 0.1)
                    elif min(au, av) < 1.0:
                        col = GOLDC * 4
                    else:
                        q = max(au, av) / R
                        col = panel(2 + int(round(1.5 * (1 - q))))
                elif lay == "N4":                              # a stepped pyramid of ripple with gold step lines
                    m = max(au, av) / (R * 0.9)
                    step = 4 - min(4, int(m * 5))
                    edge = any(abs(m - e) < 0.04 for e in (0.2, 0.4, 0.6, 0.8))
                    col = GOLDC * (2 + step) if edge else gem_col(2 + step, m, bright=step == 4)
                elif lay == "N5":                              # a tall centre gem, two small side gems in ripple panels
                    if au < R * 0.3 and av < R * 0.62:
                        q = max(au / (R * 0.3), av / (R * 0.62))
                        col = gem_col(5 if q < 0.5 else 4, q, bright=q < 0.3)
                    elif au < R * 0.38 and av < R * 0.7:
                        col = GOLDC * 3
                    elif abs(au - R * 0.64) < R * 0.16 and av < R * 0.16:
                        q = max(abs(au - R * 0.64) / (R * 0.16), av / (R * 0.16))
                        col = gem_col(4, q, bright=q < 0.4)
                    else:
                        col = panel(2)
                elif lay == "N6":                              # cushion: ripple field, a raised gold inset band, gem centre
                    if 0.55 < rn < 0.64:
                        col = GOLDC * 4
                    elif rn < 0.55:
                        col = gem_col(3 + int(round(2 * (1 - rn / 0.55))), rn / 0.55, bright=rn < 0.15)
                    else:
                        col = panel(2)
                else:                                          # N7 shield: ripple field, a gold chevron, a gem at the top
                    chev = abs((cv + 2) - (R * 0.5 - au * 0.9)) < 1.0
                    if math.hypot(cu, cv - R * 0.35) < R * 0.22:
                        q = math.hypot(cu, cv - R * 0.35) / (R * 0.22)
                        col = gem_col(5, q, bright=q < 0.35)
                    elif chev:
                        col = GOLDC * 4
                    else:
                        col = panel(2 + (1 if cv < 0 else 0))
            for k, (kind, rgb, gl, di) in enumerate(col):
                put(xc + u, yc + v, zf + 2 + k, kind, rgb, gl, di)
    return K, C, GL, DI, (x0, y0, zf, fw)


TEXES = {"W1": ("w1_neon", "W1 neon weave", 4), "H1": ("h1_neon", "H1 neon hex", 4), "X5E": ("x5_emerald", "X5 ripple", 5)}
BASE = {t["code"]: t for t in BODIES}
TAKES = []


def sq(code, base, gem, band, nm):
    d = dict(BASE[base]); d.update(code=code, name=nm, builder="square", gem=gem, band_tex=band, stone=None)
    TAKES.append(d)


def cl(code, face, mark, style, gem, band, bandshape, metal="silver"):
    TAKES.append(dict(code=code, builder="classic", face=face, mark=mark, style=style, gem=gem, band_tex=band,
                      band=bandshape, metal=metal,
                      name=f"{face} {MARK_NAMES[mark]} {'light-cut' if style == 'A' else 'gold'}"))


# J's square picks (P03, N01, N04), now made of the textures
PICK = {"R12": ("round", "M7", "B", "X5E", "H1", "slim"), "R16": ("cushion", "M2", "A", "X5E", "W1", "cathedral"),
        "R19": ("round", "M5", "A", "W1", "H1", "cathedral"), "R25": ("shield", "M9", "A", "X5E", "H1", "split")}
VAR = [("a", "as picked", {}), ("b", "detail pass", dict(beads=True, facets=16, goldline=True)),
       ("c", "band swapped", dict(beads=True, swap=True)), ("d", "big face + halo", dict(R=14.0, halo=True)),
       ("e", "diamond pass", dict(facets=24, gloss=True, beads=True))]
for pk, (face, mark, style, gem, band, bshape) in PICK.items():
    for vk, vname, extra in VAR:
        b_ = ("W1" if band == "H1" else "H1") if extra.get("swap") else band
        cl(f"{pk}{vk}", face, mark, style, gem, b_, bshape)
        TAKES[-1].update({k: v for k, v in extra.items() if k != "swap"})
        TAKES[-1]["name"] = f"{MARK_NAMES[mark]} - {vname}"
TAKES = [dict(t) for t in TAKES if t["code"] == "R19d"]
_base = TAKES[0]
TAKES = []
for code, nm, band in (("I1b", "Icon true - kept", "X5E"), ("R19f", "Square plate and halo - kept", "H1"),
                       ("F1", "Split halo", "H1"), ("F2", "Vortex", "X5E"), ("F3", "Cut key with claws", "X5E"),
                       ("F4", "Circuit", "H1"), ("F5", "Lantern window", "X5E"), ("F6", "Shards", "X5E"),
                       ("F7", "R19f plate, I1b gem", "H1")):
    t = dict(_base); t.update(code=code, builder="head", layout=code, gem="X5E", band_tex=band, keep_metal=True, name=nm, R=12.0, halo=False)
    TAKES.append(t)
BUILD = {"square": build_ring, "classic": build_classic, "icon": build_icon, "head": build_head}


def mesh_from_voxels(name, K, C, GL, DI, vs, mats=None, tile=16.0, centre=(0.0, 0.0, 0.0)):
    occ = K >= 0
    NX, NY, NZ = K.shape
    quads, cols, glows, dists, kinds = [], [], [], [], []
    dirs = [((1, 0, 0), [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)]), ((-1, 0, 0), [(0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0)]),
            ((0, 1, 0), [(0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 1, 0)]), ((0, -1, 0), [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)]),
            ((0, 0, 1), [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]), ((0, 0, -1), [(0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0)])]
    pad = np.zeros((NX + 2, NY + 2, NZ + 2), bool); pad[1:-1, 1:-1, 1:-1] = occ
    for (dx, dy, dz), corners in dirs:
        nb = pad[1 + dx:NX + 1 + dx, 1 + dy:NY + 1 + dy, 1 + dz:NZ + 1 + dz]
        idx = np.argwhere(occ & ~nb)
        if not len(idx):
            continue
        shade = {(0, 0, 1): 1.0, (0, 0, -1): 0.55}.get((dx, dy, dz), 0.8)
        q = np.stack([idx + np.array(c) for c in corners], axis=1).astype(np.float32)
        quads.append(q)
        cc = C[idx[:, 0], idx[:, 1], idx[:, 2]] * shade
        cols.append(cc); glows.append(GL[idx[:, 0], idx[:, 1], idx[:, 2]]); dists.append(DI[idx[:, 0], idx[:, 1], idx[:, 2]])
        kinds.append(K[idx[:, 0], idx[:, 1], idx[:, 2]])
    q = np.concatenate(quads) * vs
    nq = len(q)
    me = bpy.data.meshes.new(name)
    me.from_pydata(q.reshape(-1, 3).tolist(), [], np.arange(nq * 4).reshape(-1, 4).tolist())
    colr = np.concatenate(cols); gl = np.concatenate(glows); di = np.concatenate(dists); kd = np.concatenate(kinds)
    a = me.color_attributes.new("col", "FLOAT_COLOR", "CORNER")
    a.data.foreach_set("color", np.hstack([np.repeat(colr, 4, axis=0), np.ones((nq * 4, 1))]).ravel())
    # emission colour: the voxel's own green pushed toward saturation (never white)
    ec = np.clip(colr * np.array([0.6, 1.6, 0.8]), 0, 1)
    e = me.color_attributes.new("ecol", "FLOAT_COLOR", "CORNER")
    e.data.foreach_set("color", np.hstack([np.repeat(ec, 4, axis=0), np.ones((nq * 4, 1))]).ravel())
    g = me.attributes.new("glow", "FLOAT", "CORNER"); g.data.foreach_set("value", np.repeat(gl, 4))
    d = me.attributes.new("dist", "FLOAT", "CORNER"); d.data.foreach_set("value", np.repeat(di, 4))
    # UVs: each voxel face projected on its own plane, one texture tile per `tile` voxels
    # J: "ripple should absolutely be aligned in the middle first" - UVs are measured from the face centre, so the
    # texture's centre (0.5, 0.5) sits on the core, and one tile spans the whole face
    qv = q / vs - np.asarray(centre, np.float32)
    axis = np.argmin(np.ptp(qv, axis=1), axis=1)
    other = np.array([[1, 2], [0, 2], [0, 1]])[axis]
    uvs = np.stack([np.take_along_axis(qv, np.repeat(other[:, None, 0:1], 4, axis=1), axis=2)[..., 0],
                    np.take_along_axis(qv, np.repeat(other[:, None, 1:2], 4, axis=1), axis=2)[..., 0]], axis=-1) / tile + 0.5
    uvl = me.uv_layers.new(name="uv"); uvl.data.foreach_set("uv", uvs.reshape(-1).astype(np.float32))
    for m in (mats or MATS):
        me.materials.append(m)
    me.polygons.foreach_set("material_index", kd.astype(np.int32))
    me.update()
    return me, nq


# ------------------------------------------------------------------ build all twenty
VS = 0.024                        # one voxel (0.25 model px) shown about 1.5x a block's 1/16
COLS_, SPX, SPY = 5, 2.0, 2.6
PED = bpy.data.materials.new("SR pedestal"); PED.use_nodes = True
PED.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.035, 0.038, 0.042, 1)
PED.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.35
LBL = bpy.data.materials.new("SR label"); LBL.use_nodes = True
_p = LBL.node_tree.nodes["Principled BSDF"]
_p.inputs["Emission Color"].default_value = (0.85, 1.0, 0.9, 1); _p.inputs["Emission Strength"].default_value = 2.0
report = []
for i, t in enumerate(TAKES):
    rng = np.random.default_rng(595 + i)
    K, C, GL, DI, (x0, y0, zf, fw) = BUILD[t["builder"]](t, rng)
    code = t["code"]
    mats = list(MATS) + [MATS[METAL]]
    for slot, tk, emit in ((GEM, t["gem"], 5.6 if t.get("gloss") else 5.0), (BANDTEX, t.get("band_tex"), 3.5)):
        if tk is None:
            continue
        mk = f"{tk} {emit}"
        if mk not in TEXMAT:
            key, tname, ft = TEXES[tk]
            TEXMAT[mk] = tex_gem_mat(f"SR {'stone' if slot == GEM else 'band'} {tk}", key, ft, emit)
            if slot == GEM and t.get("gloss"):           # diamond pass: near-mirror, diamond index, full coat
                _p = TEXMAT[mk].node_tree.nodes["Principled BSDF"]
                for _nm, _v in (("Roughness", 0.02), ("IOR", 2.42), ("Coat Weight", 1.0), ("Coat Roughness", 0.01),
                                ("Specular IOR Level", 1.0)):
                    if _nm in _p.inputs:
                        _p.inputs[_nm].default_value = _v
        mats[slot] = TEXMAT[mk]
    if t.get("band_tex") and not t.get("keep_metal"):
        # J: "a ring made out of the hex": the metal becomes the texture, glowing, lit last (dist 1)
        sel = K == METAL
        GL[sel] = 0.6; DI[sel] = 1.0; K[sel] = BANDTEX
    me, nq = mesh_from_voxels(f"SR {code} {t['name']}", K, C, GL, DI, VS, mats, tile=float(fw),
                              centre=(x0 + fw / 2, y0 + fw / 2, 0.0))
    row, colm = divmod(i, COLS_)
    px, py = colm * SPX, row * SPY
    # pedestal
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.62, depth=0.55, location=(px, py, 0.275))
    pd = bpy.context.active_object
    for c_ in pd.users_collection:
        c_.objects.unlink(pd)
    link(pd); pd.name = f"SR {code} pedestal"; pd.data.materials.append(PED)
    # turntable root, ring centred on it, face up
    root = link(bpy.data.objects.new(f"SR {code} turntable", None)); root.location = (px, py, 0.55)
    o = link(bpy.data.objects.new(f"SR {code} {t['name']}", me)); o.parent = root
    NX, NY, NZ = K.shape
    zs = np.argwhere(K >= 0)[:, 2]
    o.location = (-NX / 2 * VS, -NY / 2 * VS, -zs.min() * VS + 0.02)
    _prefs = bpy.context.preferences.edit; _old = _prefs.keyframe_new_interpolation_type
    _prefs.keyframe_new_interpolation_type = "LINEAR"
    root.rotation_euler = (0, 0, R(-35)); root.keyframe_insert("rotation_euler", frame=1)
    root.rotation_euler = (0, 0, R(-35 + 360)); root.keyframe_insert("rotation_euler", frame=LOOP + 1)
    _prefs.keyframe_new_interpolation_type = _old
    # the face lights its surroundings
    face_z = 0.55 + (zf + 6 - zs.min()) * VS
    pl = bpy.data.lights.new(f"SR {code} glow", "POINT"); pl.color = (0.25, 1.0, 0.4); pl.shadow_soft_size = 0.2
    fcd = pl.driver_add("energy"); var = fcd.driver.variables.new(); var.name = "lit"; var.type = "SINGLE_PROP"
    var.targets[0].id_type = "SCENE"; var.targets[0].id = scene; var.targets[0].data_path = '["lit"]'
    fcd.driver.expression = "lit*6"
    plo = link(bpy.data.objects.new(f"SR {code} glow", pl)); plo.location = (px, py, face_z + 0.3)
    cu = bpy.data.curves.new("SR label " + code, "FONT"); cu.body = f"{code}  {t['name']}"; cu.size = 0.11; cu.align_x = "CENTER"
    tl = link(bpy.data.objects.new("SR label " + code, cu)); tl.location = (px, py - 0.66, 0.18)
    tl.rotation_euler = (R(90), 0, 0); tl.data.materials.append(LBL)
    cam(f"Cam {code} {t['name']}", (px + 1.15, py - 1.55, face_z + 1.35), (px, py, face_z - 0.25), 45)
    cam(f"Cam {code} {t['name']} face", (px, py - 0.05, face_z + 2.4), (px, py, face_z), 40)
    report.append(f"{code} {t['name']}: {nq} faces")
    print(report[-1], flush=True)
LX = 2.0 * SPX
cam("Cam row game", (LX, -9.5, 4.5), (LX, 1.3, 0.75), 35)
cam("Cam all", (LX, -26.0, 8.0), (LX, 0, 0.7), 40)

# ------------------------------------------------------------------ stage, light, bloom
scene.frame_start, scene.frame_end = 1, LOOP
bpy.ops.mesh.primitive_plane_add(size=1, location=(LX, 0, 0))
g = bpy.context.active_object
for c_ in g.users_collection:
    c_.objects.unlink(g)
link(g); g.name = "SR floor"; g.scale = (60, 60, 1); g.data.materials.append(PED)
world = bpy.data.worlds.new("SR world"); world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.05, 0.055, 0.06, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0
scene.world = world
for nm, rot, en in (("key", (R(40), R(-15), R(-30)), 4.5), ("rim", (R(-55), R(10), R(150)), 1.8)):
    s = link(bpy.data.objects.new("SR " + nm, bpy.data.lights.new("SR " + nm, "SUN")))
    s.data.energy = en; s.rotation_euler = rot
try:
    scene.render.engine = "BLENDER_EEVEE"
except Exception:
    scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x, scene.render.resolution_y = 1600, 900
try:
    scene.view_settings.view_transform = "Standard"
except Exception:
    pass
try:
    tree = bpy.data.node_groups.new("SR Glow", "CompositorNodeTree")
    tree.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    rl = tree.nodes.new("CompositorNodeRLayers"); go = tree.nodes.new("NodeGroupOutput")
    gl = tree.nodes.new("CompositorNodeGlare")
    if "Type" in gl.inputs:
        gl.inputs["Type"].default_value = "Bloom"
    for nm_, val in (("Size", 0.5), ("Strength", 0.45), ("Threshold", 1.0)):
        if nm_ in gl.inputs:
            gl.inputs[nm_].default_value = val
    tree.links.new(rl.outputs["Image"], gl.inputs["Image"]); tree.links.new(gl.outputs["Image"], go.inputs[0])
    scene.compositing_node_group = tree
except Exception as e:
    print("no glow:", e)
scene.camera = bpy.data.objects["Cam row game"]
scene.frame_set(70)
try:
    bpy.ops.outliner.orphans_purge(do_recursive=True)
except Exception:
    pass
bpy.ops.wm.save_as_mainfile(filepath=OUT)


def _after():
    try:
        sc = bpy.context.scene
        if hasattr(sc, "lantern_live_watch") and not sc.lantern_live_watch:
            sc.lantern_live_watch = True
        for w in bpy.context.window_manager.windows:
            for a in w.screen.areas:
                if a.type == "VIEW_3D":
                    for sp in a.spaces:
                        if sp.type == "VIEW_3D":
                            sp.region_3d.view_perspective = "CAMERA"
                            sp.shading.type = "MATERIAL"
                    with bpy.context.temp_override(window=w, area=a):
                        if not bpy.context.screen.is_animation_playing:
                            bpy.ops.screen.animation_play()
                    return None
    except Exception as e:
        print("after:", e)
    return None


if bpy.app.background is False:
    bpy.app.timers.register(_after, first_interval=4.0)
print("saved", OUT)
