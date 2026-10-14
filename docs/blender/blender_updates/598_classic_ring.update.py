# Pass 598: a classic-shaped ring with a diamond-shiny stone and four new original marks (Chat C, 2026-10-14; rings are
# the lanterns area, built here because J asked in this chat). J: "make me a classic green lantern ring now, i want it
# to be a shiny piece like diamond surface". The published ring and its emblem are not copied: J chose "a new original
# mark" for the face and N04's glowing light lines (596) for the glow.
# Classic proportions: a chunky band whose shoulders swell into a round bezel, a domed stone cut in eight facets.
# Shiny: the stone is a diamond-like gloss (index 2.42, full clear coat, near-zero roughness) and the metal is polished;
# light panels round the stage give the glints.
# Marks (original, lantern-themed): M1 Lantern, M2 Flame, M3 Oath star (a four-point star in a diamond), M4 Rising
# chevrons. Each in two styles: A light-cut (the mark is cut into the stone as light, a ring of light inside the bezel,
# a dark emerald band with a glowing line along it) and B gold inlay (raised gold mark with a glowing outline, polished
# silver band with gold rims). It lights up as 595-597 do.
# Cameras "Cam C## <name>", "... face", "Cam row 1" (lights cut), "Cam row 2" (gold inlay), "Cam all".
# Builds LanternLive\lanterns\classic_ring.blend.
import math, os
import bpy
import numpy as np
from mathutils import Matrix

R = math.radians
OUT = os.path.join(FOLDER, "lanterns", "classic_ring.blend")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
if bpy.data.filepath:
    try:
        bpy.ops.wm.save_mainfile()
    except Exception as e:
        print("save current:", e)
old = bpy.data.scenes.get("Classic Ring")
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new("Classic Ring")
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
MATS = [ring_mat("CR polished metal", 1.0, 0.1, 0.0, coat=0.5), ring_mat("CR gold", 1.0, 0.12, 0.0, coat=0.3),
        ring_mat("CR diamond emerald", 0.0, 0.02, 1.6, coat=1.0), ring_mat("CR light", 0.0, 0.05, 4.0, coat=1.0),
        ring_mat("CR deep green", 0.0, 0.1, 1.2, coat=1.0)]
for _m in MATS[2:]:
    _p = _m.node_tree.nodes["Principled BSDF"]
    for _nm, _v in (("IOR", 2.42), ("Specular IOR Level", 1.0), ("Transmission Weight", 0.25), ("Coat Roughness", 0.01)):
        if _nm in _p.inputs:
            _p.inputs[_nm].default_value = _v

# ------------------------------------------------------------------ palettes
METALS = {"silver": (150, 152, 156), "steel": (112, 118, 126), "gunmetal": (62, 66, 72), "pale": (196, 198, 202),
          "stone": (128, 130, 128), "gold": (206, 160, 56), "white": (214, 214, 208)}
GOLD_C = (240, 192, 66)
EM_DARK, EM_LIGHT = np.array((8, 82, 32), float), np.array((40, 196, 84), float)
CORE_C = (96, 255, 132)          # saturated, never white
DARK_C = (6, 48, 20)

# ------------------------------------------------------------------ the takes (every one different)
# ------------------------------------------------------------------ the classic-shaped ring, four original marks
# Marks on a 15 x 15 grid ('#' = mark). All original lantern-themed symbols, none a published emblem.
MARKS = {
    "M1": ("Lantern", [
        "......###......",
        ".....#...#.....",
        ".....#...#.....",
        "...#########...",
        "....#######....",
        "....##...##....",
        "....#..#..#....",
        "....#.###.#....",
        "....#..#..#....",
        "....##...##....",
        "....#######....",
        "...#########...",
        "...............",
        "...............",
        "..............."]),
    "M2": ("Flame", [
        ".......#.......",
        "......##.......",
        "......###......",
        ".....####......",
        ".....#####.....",
        "....###.###....",
        "....##...##....",
        "...##..#..##...",
        "...#..###..#...",
        "...#..###..#...",
        "...##..#..##...",
        "....##...##....",
        ".....#####.....",
        "...............",
        "................"[:15]]),
    "M3": ("Oath star", None),
    "M4": ("Rising chevrons", None),
}


def mark_mask(key):
    name, rows = MARKS[key]
    m = np.zeros((15, 15), bool)
    if rows is not None:
        for r, line in enumerate(rows):
            for c, ch in enumerate(line[:15]):
                m[c, 14 - r] = ch == "#"
        # centre the drawing vertically
        ys = np.where(m.any(axis=0))[0]
        shift = int(round(7 - (ys.min() + ys.max()) / 2))
        m = np.roll(m, shift, axis=1)
        return m
    for i in range(15):
        for j in range(15):
            x, y = i - 7, j - 7
            if key == "M3":   # a four-point star inside a diamond outline
                star = (abs(x) <= 0 and abs(y) <= 6) or (abs(y) <= 0 and abs(x) <= 6) or (abs(x) + abs(y) <= 2)
                m[i, j] = star or abs(abs(x) + abs(y) - 7) < 0.5
            elif key == "M4":  # three chevrons rising, in a thin frame
                m[i, j] = any(abs(y - (c - abs(x))) < 0.6 and abs(x) <= 5 for c in (-3, 1, 5)) or (max(abs(x), abs(y)) == 7)
    return m


TAKES = []
for mk in ("M1", "M2", "M3", "M4"):
    for style in ("A", "B"):
        nm = MARKS[mk][0]
        TAKES.append(dict(code=f"C{len(TAKES) + 1:02d}", name=f"{nm} {'light-cut' if style == 'A' else 'gold inlay'}",
                          mark=mk, style=style))


def build_ring(t, rng):
    """Classic proportions: a chunky band, shoulders swelling into a round bezel, a domed diamond-cut stone with the
    mark on it. Style A: the mark is cut into the stone as light (N04's light lines) with a ring of light inside the
    bezel. Style B: the mark is a raised gold inlay with a glowing outline; polished silver band with gold rims."""
    R = 12.0
    NX, NY, NZ = 34, 42, 54
    K = np.full((NX, NY, NZ), -1, np.int8)
    C = np.zeros((NX, NY, NZ, 3), np.float32)
    GL = np.zeros((NX, NY, NZ), np.float32); DI = np.zeros((NX, NY, NZ), np.float32)
    xc, yc, zc, ri = NX / 2, NY / 2, 18.0, 10.4
    band_rgb = np.array((34, 92, 58), float) if t["style"] == "A" else np.array((176, 180, 186), float)

    def put(x, y, z, k, rgb, glow=0.0, dist=0.0, noise=0.03):
        if 0 <= x < NX and 0 <= y < NY and 0 <= z < NZ:
            K[x, y, z] = k
            C[x, y, z] = lin(np.clip(np.asarray(rgb, float) * (1.0 + rng.uniform(-noise, noise)), 0, 255))
            GL[x, y, z] = glow; DI[x, y, z] = dist

    for x in range(NX):
        for y in range(NY):
            for z in range(NZ):
                dy, dz = y + 0.5 - yc, z + 0.5 - zc
                th = math.atan2(dy, dz); f = (1 - math.cos(th)) / 2
                tt = 6.5 - 2.0 * f
                ww = 17.0 - 5.0 * f
                ax = abs(x + 0.5 - xc)
                if ax > ww / 2:
                    continue
                r = max(abs(dy), abs(dz), (abs(dy) + abs(dz)) / 1.3)
                # rounded outer edge: thinner toward the sides of the band
                tt_e = tt - 1.6 * max(0.0, (ax - (ww / 2 - 2.0)) / 2.0)
                if not (ri <= r <= ri + tt_e):
                    continue
                k, rgb = METAL, band_rgb * (0.85 + 0.25 * (r - ri) / tt)
                if t["style"] == "B" and ax > ww / 2 - 1.1:
                    k, rgb = GOLD, GOLD_C
                if t["style"] == "A" and r > ri + tt_e - 1.0 and abs(ax - 3.0) < 0.5 and f < 0.6:
                    k, rgb = CORE, CORE_C
                    put(x, y, z, k, rgb, 0.55, 1.0 + f); continue
                put(x, y, z, k, rgb)
    zf = int(round(zc + ri + 6.5)) - 1
    mm = mark_mask(t["mark"])
    rs = R - 3.2                                           # stone radius
    for u in range(-13, 13):
        for v in range(-13, 13):
            cu, cv = u + 0.5, v + 0.5
            r = math.hypot(cu, cv)
            if r > R:
                continue
            dist = r / R
            X, Y = int(xc) + u, int(yc) + v
            for z in (zf, zf + 1):
                put(X, Y, z, METAL, band_rgb * 0.9, 0.0, dist)
            if r > R - 2.2:                                # the bezel rim, polished
                rim_rgb = band_rgb * 1.1 if t["style"] == "A" else np.array(GOLD_C)
                for k in range(4):
                    put(X, Y, zf + 2 + k, METAL if t["style"] == "A" else GOLD, rim_rgb)
                continue
            if r > rs:                                     # N04: a line of light inside the bezel
                for k in range(2):
                    put(X, Y, zf + 2 + k, CORE if k == 1 else GEM, CORE_C if k == 1 else EM_DARK, 0.6, dist)
                continue
            # domed, diamond-cut stone: eight facets (alternate sectors one step higher in the middle band)
            sector = int(((math.atan2(cv, cu) + math.pi) / (2 * math.pi)) * 8) % 2
            h = 1 + int(round(1.6 * (1 - (r / rs) ** 2))) + (1 if (sector and r / rs > 0.78) else 0)
            shade = 0.55 + 0.6 * (1 - r / rs) + (0.12 if sector else -0.05)
            rgb = EM_DARK + (EM_LIGHT - EM_DARK) * min(1.0, shade)
            mi, mj = u + 7, v + 7
            on_mark = 0 <= mi < 15 and 0 <= mj < 15 and mm[mi, mj]
            near_mark = any(0 <= mi + a < 15 and 0 <= mj + b < 15 and mm[mi + a, mj + b]
                            for a in (-1, 0, 1) for b in (-1, 0, 1)) and not on_mark
            for k in range(h):
                top = k == h - 1
                kind, c_, gl = GEM, rgb * (1.0 if top else 0.7), 0.16 if top else 0.05
                if top and on_mark and t["style"] == "A":
                    kind, c_, gl = CORE, CORE_C, 1.0
                if top and near_mark and t["style"] == "B":
                    kind, c_, gl = CORE, CORE_C, 0.75
                put(X, Y, zf + 2 + k, kind, c_, gl, dist * (1.0 if not on_mark else 0.3))
            if on_mark and t["style"] == "B":
                put(X, Y, zf + 2 + h, GOLD, GOLD_C, 0.0, dist)
    return K, C, GL, DI, (int(xc) - 13, int(yc) - 13, zf, 26)


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
COLS_, SPX, SPY = 4, 2.0, 0.0
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
    code = t["code"]
    me, nq = mesh_from_voxels(f"SR {code} {t['name']}", K, C, GL, DI, VS)
    row, colm = divmod(i, COLS_)
    px, py = (colm + row * 4) * SPX + row * 1.6, 0.0
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
for r in range(2):
    mx = (r * 4 + 1.5) * SPX + r * 1.6
    cam(f"Cam row {r + 1}", (mx, -6.4, 2.4), (mx, 0, 0.75), 40)
LX = (7 * SPX + 1.6) / 2
cam("Cam all", (LX, -26.0, 8.0), (LX, 0, 0.7), 40)

# ------------------------------------------------------------------ glints for the diamond surface
for k_, (lx_, ly_, lz_) in enumerate(((-3, -4, 5), (LX * 2 + 3, -4, 5), (LX, 6, 6), (LX, -8, 7))):
    al = bpy.data.lights.new(f"CR glint {k_}", "AREA"); al.energy = 220; al.size = 1.2; al.color = (0.95, 1.0, 0.97)
    ao = link(bpy.data.objects.new(f"CR glint {k_}", al)); ao.location = (lx_, ly_, lz_)
    d_ = np.array((LX, 0, 0.8)) - np.array((lx_, ly_, lz_))
    ao.rotation_euler = (math.atan2(math.hypot(d_[0], d_[1]), -d_[2]), 0, math.atan2(d_[1], d_[0]) - math.pi / 2)

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
scene.camera = bpy.data.objects["Cam C01 Lantern light-cut"]
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
