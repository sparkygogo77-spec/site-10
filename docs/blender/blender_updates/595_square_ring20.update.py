# Pass 595: the square emblem ring, 20 takes (Chat C, 2026-10-14; rings are the lanterns area, built here because J
# asked in this chat). J, with his concept image of the square emblem ring: "I need extreme effort put into making the
# ring look good for the square emblem ring head or face, it will have to light up, the rest of the rings are garbage,
# give me 20 takes on the ring, no repeats, stay faithful to this ring".
# Faithful to J's image, in every take: a pixel-noisy grey metal band, faceted and wide under the face, tapering
# toward the palm; a square face wider than the band; a gold frame; a green bar along the top and bottom edges inside
# thin gold outlines; between the bars, side columns of green and a centre square of concentric gold frames round a
# stepped emerald that gets lighter toward the middle. Same grid as the game ring (0.25 model px voxels, face 6 px).
# What changes from take to take (no two alike): the band's shape (octagonal, round, cathedral shoulders, split shank,
# knife edge, ribbed, stepped, twisted, pierced gallery, glowing channel), its metal tone and trim, the face's relief
# (flat, pyramid, inset vault, dome, faceted gem), the number of gold rings, the core shape, the bar and side-column
# patterns, the corners (square, notched, studs, claws), a bezel rim, and which parts glow.
# It lights up: everything starts dark; from frame 20 the light spreads out from the core across the face (and down
# the band channel where there is one) over 24 frames, swells at frame 52, settles and breathes, and goes dark again at
# the end of the loop. Saturated green, never white. A green point light in each face lights the pedestal.
# Each ring turns slowly on its pedestal. Rings shown enlarged (a voxel = 2.4 cm).
# Cameras "Cam T## <name>" (three-quarter from above, like J's image), "Cam T## <name> face" (straight down on the
# face), "Cam row 1".."Cam row 4", "Cam all". Builds LanternLive\lanterns\square_ring20.blend.
import math, os
import bpy
import numpy as np
from mathutils import Matrix

R = math.radians
OUT = os.path.join(FOLDER, "lanterns", "square_ring20.blend")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
if bpy.data.filepath:
    try:
        bpy.ops.wm.save_mainfile()
    except Exception as e:
        print("save current:", e)
old = bpy.data.scenes.get("Square Ring 20")
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new("Square Ring 20")
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
for f, v in ((1, 0.0), (20, 0.0), (44, 1.0), (52, 1.3), (62, 1.0), (82, 0.88), (102, 1.0), (122, 0.88), (142, 1.0),
             (170, 0.95), (188, 0.0), (LOOP, 0.0)):
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


METAL, GOLD, GEM, CORE, DARK = range(5)
MATS = [ring_mat("SR band metal", 0.85, 0.38, 2.0), ring_mat("SR gold", 1.0, 0.24, 0.0),
        ring_mat("SR emerald", 0.0, 0.12, 3.2, coat=0.6), ring_mat("SR core", 0.0, 0.1, 4.0, coat=0.6),
        ring_mat("SR deep green", 0.0, 0.3, 1.2)]

# ------------------------------------------------------------------ palettes
METALS = {"silver": (150, 152, 156), "steel": (112, 118, 126), "gunmetal": (62, 66, 72), "pale": (196, 198, 202),
          "stone": (128, 130, 128)}
GOLD_C = (240, 192, 66)
EM_DARK, EM_LIGHT = np.array((8, 82, 32), float), np.array((40, 196, 84), float)
CORE_C = (96, 255, 132)          # saturated, never white
DARK_C = (6, 48, 20)

# ------------------------------------------------------------------ the takes (every one different)
TAKES = [
    dict(name="Faithful", shape="octa", metal="stone", rings=2, core="2", relief="frames", bars="solid", sides="solid",
         corners="square", glow="rings"),
    dict(name="Stepped pyramid", shape="octa", metal="silver", rings=3, core="2", relief="pyramid", bars="solid",
         sides="solid", corners="square", glow="core"),
    dict(name="Inset vault", shape="round", metal="steel", rings=2, core="plus", relief="inset", bars="line",
         sides="solid", corners="square", glow="bars"),
    dict(name="Cells", shape="taper", metal="silver", rings=2, core="2", relief="frames", bars="cells", sides="cells",
         corners="square", glow="all"),
    dict(name="Cathedral", shape="cathedral", metal="silver", rings=3, core="diamond", relief="frames", bars="solid",
         sides="solid", corners="square", bezel=True, glow="rings"),
    dict(name="Split shank", shape="split", metal="pale", rings=2, core="2", relief="frames", bars="gradient",
         sides="solid", corners="notched", glow="rings"),
    dict(name="Light channel", shape="channel", metal="gunmetal", rings=2, core="2", relief="frames", bars="solid",
         sides="gradient", corners="square", glow="bars"),
    dict(name="Studded", shape="octa", metal="gunmetal", rings=2, core="plus", relief="pyramid", bars="solid",
         sides="solid", corners="studs", glow="rings"),
    dict(name="Notched steps", shape="stepped", metal="steel", rings=3, core="plus", relief="frames", bars="cells",
         sides="solid", corners="notched", glow="core"),
    dict(name="Grand face", shape="cathedral", metal="stone", fw=28, rings=4, core="2", relief="pyramid",
         bars="solid", sides="gradient", corners="square", glow="all"),
    dict(name="Twin bars", shape="octa", metal="pale", bh=4, rings=3, core="diamond", relief="frames",
         bars="double", sides="solid", corners="square", glow="bars"),
    dict(name="Ribbed shank", shape="ribbed", metal="silver", rings=2, core="2", relief="dome", bars="solid",
         sides="gradient", corners="square", glow="rings"),
    dict(name="Knife edge", shape="knife", metal="pale", rings=2, core="2", relief="dome", bars="gradient",
         sides="cells", corners="notched", glow="core"),
    dict(name="Gold-trimmed band", shape="octa", metal="silver", trim="gold", rings=2, core="2", relief="frames",
         bars="solid", sides="solid", corners="square", bezel=True, glow="all"),
    dict(name="Pierced gallery", shape="gallery", metal="stone", rings=2, core="plus", relief="inset", bars="cells",
         sides="solid", corners="square", glow="rings"),
    dict(name="Twisted shank", shape="twist", metal="steel", rings=2, core="diamond", relief="frames", bars="cells",
         sides="gradient", corners="studs", glow="bars"),
    dict(name="Deep frame", shape="octa", metal="gunmetal", frame=2, rings=1, core="big", relief="frames",
         bars="solid", sides="solid", corners="square", glow="all"),
    dict(name="Glowing veins", shape="veins", metal="gunmetal", rings=3, core="2", relief="pyramid", bars="line",
         sides="solid", corners="square", glow="rings"),
    dict(name="Claw bezel", shape="taper", metal="silver", rings=2, core="2", relief="frames", bars="solid",
         sides="cells", corners="claws", bezel=True, glow="rings"),
    dict(name="Radiant", shape="round", metal="pale", rings=2, core="plus", relief="facet", bars="gradient",
         sides="gradient", corners="square", extra="spokes", glow="all"),
]


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
                        if core:
                            kind, rgb, glow = CORE, CORE_C, 1.0
                        if t.get("extra") == "spokes" and not core and abs(abs(ccu) - abs(ccv)) < 0.6 and d >= 1:
                            kind, h, glow = GOLD, 2, 0.0
                    # relief inside the centre square
                    if relief == "pyramid":
                        h += min(d, dmax) // 2
                    elif relief == "dome":
                        h += int(round(2.5 * (1 - (max(abs(a_ + 0.5 - cs / 2), abs(b_ + 0.5 - cs / 2)) / (cs / 2)) ** 2)))
                    elif relief == "facet" and d >= 2:
                        h += min(3, d - 1)
            if relief == "inset" and kind == GOLD:
                h += 1
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


def mesh_from_voxels(name, K, C, GL, DI, vs):
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
    for m in MATS:
        me.materials.append(m)
    me.polygons.foreach_set("material_index", kd.astype(np.int32))
    me.update()
    return me, nq


# ------------------------------------------------------------------ build all twenty
VS = 0.024                        # one voxel (0.25 model px) shown about 1.5x a block's 1/16
COLS_, SPX, SPY = 5, 2.0, 0.0
PED = bpy.data.materials.new("SR pedestal"); PED.use_nodes = True
PED.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.035, 0.038, 0.042, 1)
PED.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.35
LBL = bpy.data.materials.new("SR label"); LBL.use_nodes = True
_p = LBL.node_tree.nodes["Principled BSDF"]
_p.inputs["Emission Color"].default_value = (0.85, 1.0, 0.9, 1); _p.inputs["Emission Strength"].default_value = 2.0
report = []
for i, t in enumerate(TAKES):
    rng = np.random.default_rng(595 + i)
    K, C, GL, DI, (x0, y0, zf, fw) = build_ring(t, rng)
    code = f"T{i + 1:02d}"
    me, nq = mesh_from_voxels(f"SR {code} {t['name']}", K, C, GL, DI, VS)
    row, colm = divmod(i, COLS_)
    px, py = i * SPX + row * 1.6, 0.0
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
for r in range(4):
    mx = (r * 5 + 2) * SPX + r * 1.6
    cam(f"Cam row {r + 1}", (mx, -7.2, 2.6), (mx, 0, 0.75), 40)
LX = (19 * SPX + 3 * 1.6) / 2
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
scene.camera = bpy.data.objects["Cam T01 Faithful"]
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
