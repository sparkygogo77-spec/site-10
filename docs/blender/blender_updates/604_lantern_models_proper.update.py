# Pass 604: proper lantern models from J:dark_lantern (PC chat, 2026-10-18; lanterns 600-699).
# Why: J asked for "proper lantern models" from the jar's dark lantern and picked: smooth glass (no stacked-slab
#   ridges), a richer gold frame, and new silhouettes. 6 takes. The jar model is 2,118 1/4-px boxes whose glass is
#   stacked slabs (preview: LanternLive\_previews\J_dark_lantern\).
# Carried from the approved G3 charge and R4 frame (design skill): glass fades to near-black emerald at the very top and
#   bottom, the light lives in the middle band; gold-yellow lightning cracks dim, fading toward the ends; dashes of the
#   darkest green down the middle of the front and each side; polished gold; saturated green, never white (emission
#   peaks at 1.27 on (0.02, 0.9, 0.12), under the ~1.5 mint clip); some yellow in the green flow; about 3 degrees of helix on pinched glass;
#   idle glow about 12%.
# Takes (row A refines the jar's pinched column, row B are new silhouettes):
#   A1 Pinched column: the jar's rounded-triangle pinch made smooth; bevelled collars, a double middle band, three corner
#      ribs, a sculpted triangle bail with the port on top.
#   A2 Hex pinch: six-facet glass with the 3-degree helix; faceted collars, a crown of six points, a ring handle.
#   A3 Gold cage: round pinched glass held by six curved gold ribs that follow it; an arched handle.
#   B1 Tower: two stacked octagonal glass chambers on a square plinth, a spire crown with the port.
#   B2 Orb: squat glass sphere in a gold gimbal (equator band and an upright hoop) on a short pedestal.
#   B3 Hourglass prism: two triangular cones meeting at a gold waist ring, three legs, a triangle bail.
# Each take turns once in 120 frames; the charge sits at idle (0.12) to frame 20, fills to full by frame 80, holds.
# Cameras "Cam <code> <name>" (three-quarter front), "Cam all". Builds LanternLive\lanterns\dark_lantern_proper.blend.
import math, os
import bpy
import bmesh
import numpy as np

R = math.radians
PASS = globals().get("PASS", "604")                # pass 605+ exec this builder with their own PASS, OUT_NAME, PAL
TAG = "L" + PASS
OUT = os.path.join(FOLDER, globals().get("OUT_NAME", "dark_lantern_proper.blend"))
PAL = dict(dict(
    glass=(0.004, 0.035, 0.014), crack=(0.42, 0.26, 0.04), stitch=(0.0, 0.01, 0.004), flow=(0.02, 0.9, 0.12),
    flow2=(0.45, 0.9, 0.04), crack_glow=(0.9, 0.62, 0.08), lamp=(0.3, 1.0, 0.4), port=(0.01, 0.08, 0.02)),
    **globals().get("PAL", {}))
TAU = 2 * math.pi
SEG = 96                                         # divisible by 3, 6 and 8: polygon corners land on vertices
FRAMES = 120
CHARGE = "0.12 if frame < 20 else min(1.0, 0.12 + 0.88 * (frame - 20) / 60)"

if bpy.data.filepath:
    try:
        bpy.ops.wm.save_mainfile()
    except Exception as e:
        print("save current:", e)
old = bpy.data.scenes.get(f"Lantern Models {PASS}")
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new(f"Lantern Models {PASS}")
col = scene.collection
scene.frame_start, scene.frame_end = 1, FRAMES
scene.render.fps = 20
win = bpy.context.window
if win:
    win.scene = scene


def link(o):
    col.objects.link(o)
    return o


def drive(idb, path, expr, index=-1):
    fc = idb.driver_add(path, index) if index >= 0 else idb.driver_add(path)
    fc.driver.type = "SCRIPTED"
    fc.driver.expression = expr                  # "simple" expressions (frame, min, ternary) run without auto-run
    return fc


# ------------------------------------------------------------------ materials
def gold_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.95, 0.64, 0.2, 1)
    b.inputs["Metallic"].default_value = 1.0
    b.inputs["Roughness"].default_value = 0.22
    return m


def glass_mat(name, z0, z1):
    """Dark emerald glass lit by the charge in its middle band; gold cracks and dark stitches. Object-space z0..z1."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    b = N["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.08
    b.inputs["Coat Weight"].default_value = 1.0
    b.inputs["Coat Roughness"].default_value = 0.03

    def node(kind, **kw):
        n = N.new(kind)
        for k, v in kw.items():
            setattr(n, k, v)
        return n

    def math_(op, a, bb=None, c=None):
        n = node("ShaderNodeMath", operation=op)
        for i, v in enumerate((a, bb, c)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                L.new(v, n.inputs[i])
        return n.outputs[0]

    def mrange(v, a, bb, c, d, smooth=True):
        n = node("ShaderNodeMapRange")
        if smooth:
            n.interpolation_type = "SMOOTHSTEP"
        L.new(v, n.inputs[0])
        for i, x in zip((1, 2, 3, 4), (a, bb, c, d)):
            n.inputs[i].default_value = x
        return n.outputs[0]

    tc = node("ShaderNodeTexCoord")
    sep = node("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sep.inputs[0])
    h = mrange(sep.outputs["Z"], z0, z1, 0.0, 1.0, smooth=False)                 # 0 bottom .. 1 top
    cv = node("ShaderNodeValue"); cv.name = "Charge"
    drive(cv.outputs[0], "default_value", CHARGE)
    dmid = math_("ABSOLUTE", math_("SUBTRACT", h, 0.5))
    band = math_("POWER", mrange(dmid, 0.04, 0.36, 1.0, 0.0), 1.6)    # light in the middle band, near-black ends
    # gold lightning cracks: jagged (noise-bent) Voronoi edges in patches, dim, filling from the centre with the charge
    jag = node("ShaderNodeTexNoise"); jag.inputs["Scale"].default_value = 9.0; jag.inputs["Detail"].default_value = 6.0
    L.new(tc.outputs["Object"], jag.inputs["Vector"])
    bent = node("ShaderNodeVectorMath", operation="MULTIPLY_ADD"); L.new(jag.outputs["Color"], bent.inputs[0])
    bent.inputs[1].default_value = (0.09, 0.09, 0.09); L.new(tc.outputs["Object"], bent.inputs[2])
    vor = node("ShaderNodeTexVoronoi", feature="DISTANCE_TO_EDGE"); vor.inputs["Scale"].default_value = 4.0
    L.new(bent.outputs[0], vor.inputs["Vector"])
    patch = node("ShaderNodeTexNoise"); patch.inputs["Scale"].default_value = 2.2
    L.new(tc.outputs["Object"], patch.inputs["Vector"])
    reach = math_("SUBTRACT", dmid, math_("MULTIPLY_ADD", cv.outputs[0], 0.4, 0.06))   # cracks reach the ends near full
    crack = mrange(vor.outputs["Distance"], 0.0, 0.018, 1.0, 0.0)
    crack = math_("MULTIPLY", crack, mrange(patch.outputs["Fac"], 0.45, 0.58, 0.0, 1.0))
    crack = math_("MULTIPLY", crack, mrange(reach, -0.04, 0.0, 1.0, 0.0))
    crack = math_("MULTIPLY", crack, mrange(dmid, 0.3, 0.5, 1.0, 0.25))                 # fade toward the ends
    # stitches: dashes of the darkest green down the front, back and both sides
    ang = math_("ARCTAN2", sep.outputs["Y"], sep.outputs["X"])
    line = mrange(math_("COSINE", math_("MULTIPLY", ang, 4.0)), 0.988, 1.0, 0.0, 1.0)
    dash = math_("LESS_THAN", math_("FRACT", math_("MULTIPLY", h, 34.0)), 0.55)
    stitch = math_("MULTIPLY", math_("MULTIPLY", line, dash), mrange(band, 0.0, 0.25, 0.0, 1.0))
    # base colour: near-black emerald, gold in the cracks, darkest green in the stitches
    base = node("ShaderNodeMix", data_type="RGBA"); L.new(crack, base.inputs[0])
    base.inputs[6].default_value = (*PAL["glass"], 1); base.inputs[7].default_value = (*PAL["crack"], 1)
    base2 = node("ShaderNodeMix", data_type="RGBA"); L.new(stitch, base2.inputs[0])
    L.new(base.outputs[2], base2.inputs[6]); base2.inputs[7].default_value = (*PAL["stitch"], 1)
    L.new(base2.outputs[2], b.inputs["Base Color"])
    # the green flow: slow 4D noise (one way), some yellow in it
    noi = node("ShaderNodeTexNoise", noise_dimensions="4D"); noi.inputs["Scale"].default_value = 3.0
    L.new(tc.outputs["Object"], noi.inputs["Vector"])
    drive(noi.inputs["W"], "default_value", "frame * 0.012")
    flow = node("ShaderNodeMix", data_type="RGBA"); L.new(mrange(noi.outputs["Fac"], 0.55, 0.75, 0.0, 0.35), flow.inputs[0])
    flow.inputs[6].default_value = (*PAL["flow"], 1); flow.inputs[7].default_value = (*PAL["flow2"], 1)
    em = node("ShaderNodeMix", data_type="RGBA"); L.new(crack, em.inputs[0])                # cracks glow dim gold
    L.new(flow.outputs[2], em.inputs[6]); em.inputs[7].default_value = (*PAL["crack_glow"], 1)
    L.new(em.outputs[2], b.inputs["Emission Color"])
    breathe = mrange(noi.outputs["Fac"], 0.3, 0.7, 0.75, 1.15)
    glow = math_("MULTIPLY", math_("MULTIPLY", band, cv.outputs[0]), breathe)
    glow = math_("MULTIPLY", glow, math_("SUBTRACT", 1.0, math_("MULTIPLY", stitch, 0.9)))
    crack_dim = math_("SUBTRACT", 1.0, math_("MULTIPLY", crack, 0.75))                 # cracks never get bright
    L.new(math_("MULTIPLY", math_("MULTIPLY", glow, crack_dim), 1.1), b.inputs["Emission Strength"])
    return m


GOLD = gold_mat(f"{TAG} gold")
PORT = bpy.data.materials.new(f"{TAG} port light")
PORT.use_nodes = True
_pb = PORT.node_tree.nodes["Principled BSDF"]
_pb.inputs["Base Color"].default_value = (*PAL["port"], 1)
_pb.inputs["Emission Color"].default_value = (*PAL["flow"], 1)
drive(_pb.inputs["Emission Strength"], "default_value", "1.2 * (" + CHARGE + ")")


# ------------------------------------------------------------------ geometry
def poly_shape(n, roundness):
    """Radius factor round the axis: a rounded n-gon with a flat face toward the front (-Y). n=0 is a circle."""
    if n == 0:
        return lambda th: 1.0
    step = TAU / n
    off = -math.pi / 2 - step / 2

    def f(th):
        a = ((th - off) % step) - step / 2
        return (1 - roundness) * math.cos(step / 2) / math.cos(a) + roundness
    return f


def lathe(name, prof, shape, closed=False, twist=0.0, z_span=(0.0, 1.0), mat=None, sharp=None, parent=None):
    """Surface of revolution through (r, z) points; shape() bends the circle into a polygon; twist (radians) turns the
    section from z_span[0] to z_span[1] (the helix)."""
    za, zb = z_span
    verts = []
    for r, z in prof:
        tw = twist * (z - za) / max(zb - za, 1e-6)
        for j in range(SEG):
            th = TAU * j / SEG
            s = r * shape(th)
            verts.append((s * math.cos(th + tw), s * math.sin(th + tw), z))
    faces = []
    rows = len(prof) if closed else len(prof) - 1
    for i in range(rows):
        i2 = (i + 1) % len(prof)
        for j in range(SEG):
            j2 = (j + 1) % SEG
            faces.append((i * SEG + j, i * SEG + j2, i2 * SEG + j2, i2 * SEG + j))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bm.faces.ensure_lookup_table()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
    me.shade_smooth()
    if sharp is not None:
        me.set_sharp_from_angle(angle=sharp)
    if mat:
        me.materials.append(mat)
    o = link(bpy.data.objects.new(name, me))
    o.parent = parent
    return o


def glass_profile(z0, z1, r_end, r_mid, pinch=1.0, n=28, cap=0.03):
    """Pinched glass: r_end at both ends, r_mid at the waist, closed with rounded caps."""
    pts = [(0.0, z0)]
    for k in range(n + 1):
        h = k / n
        w = math.sin(math.pi * h) ** pinch
        r = r_end + (r_mid - r_end) * w
        ec = min(h, 1 - h) / max(cap / (z1 - z0), 1e-6)        # round the rim into the caps
        if ec < 1:
            r *= 0.8 + 0.2 * math.sqrt(max(ec, 0))
        pts.append((r, z0 + (z1 - z0) * h))
    pts.append((0.0, z1))
    return pts


def collar(name, r, z, h, shape, parent, lip=0.012, depth=0.035):
    """A bevelled gold collar ring hugging radius r at height z (thickness h)."""
    ri, ro = r - 0.006, r + depth
    prof = [(ri, z), (ro - lip, z), (ro, z + lip), (ro, z + h - lip), (ro - lip, z + h), (ri, z + h)]
    return lathe(name, prof, shape, closed=True, mat=GOLD, parent=parent, sharp=R(50))


def tube(name, pts, radius, parent, mat=None):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = radius; cu.bevel_resolution = 3; cu.use_fill_caps = True
    sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1)
    for p, c in zip(sp.points, pts):
        p.co = (c[0], c[1], c[2], 1)
    cu.materials.append(mat or GOLD)
    o = link(bpy.data.objects.new(name, cu))
    o.parent = parent
    return o


def port(name, z, parent, r=0.05):
    """The ring port on top: a gold socket with a lit core."""
    lathe(name + " socket", [(r * 0.55, z), (r, z), (r, z + 0.035), (r * 0.7, z + 0.05), (r * 0.55, z + 0.05)],
          poly_shape(0, 0), closed=True, mat=GOLD, parent=parent)
    lathe(name + " light", [(0.0, z + 0.02), (r * 0.52, z + 0.02), (r * 0.52, z + 0.045), (0.0, z + 0.045)],
          poly_shape(0, 0), closed=True, mat=PORT, parent=parent)


def bail(name, top_z, half_w, height, parent, shape="tri", r=0.014, y=0.0):
    if shape == "tri":
        pts = [(-half_w, y, top_z), (-half_w * 0.35, y, top_z + height * 0.9), (0, y, top_z + height),
               (half_w * 0.35, y, top_z + height * 0.9), (half_w, y, top_z)]
        # round the triangle's corners
        sm = [pts[0]]
        for a, b in zip(pts, pts[1:]):
            for k in range(1, 9):
                t = k / 8
                sm.append(tuple(a[i] + (b[i] - a[i]) * t for i in range(3)))
        pts = sm
    else:                                                    # arch
        pts = [(half_w * math.cos(math.pi * k / 24), y, top_z + height * math.sin(math.pi * k / 24)) for k in range(25)]
    return tube(name, pts, r, parent)


def glass(name, prof, shape, parent, twist=0.0, sharp=None):
    zs = [p[1] for p in prof]
    z0, z1 = min(zs), max(zs)
    return lathe(name, prof, shape, twist=twist, z_span=(z0, z1), mat=glass_mat(name + " mat", z0, z1),
                 parent=parent, sharp=sharp)


def r_at(prof, z):
    best = min(prof[1:-1], key=lambda p: abs(p[1] - z))
    return best[0]


# ------------------------------------------------------------------ the takes
TAKES = {}


def take(code, name, ox, oy):
    root = link(bpy.data.objects.new(f"{TAG} {code}", None))
    root.location = (ox, oy, 0)
    root.empty_display_size = 0.2
    drive(root, "rotation_euler", f"(frame - 1) * {TAU / FRAMES:.6f}", 2)             # one turn in 120 frames
    lamp = link(bpy.data.objects.new(f"{TAG} {code} lamp", bpy.data.lights.new(f"{TAG} {code} lamp", "POINT")))
    lamp.data.color = PAL["lamp"]; lamp.data.shadow_soft_size = 0.15
    lamp.parent = root
    drive(lamp.data, "energy", "6.0 * (" + CHARGE + ")")
    TAKES[code] = (name, root, lamp)
    return root, lamp


# ---- 604 takes (passes 605+ exec everything above this line, their own takes, then from "stage, light" on)
# A1 Pinched column
root, lamp = take("A1", "Pinched column", 0, 0)
tri = poly_shape(3, 0.55)
gp = glass_profile(0.13, 1.0, 0.27, 0.215, pinch=1.4)
glass(f"{TAG} A1 glass", gp, tri, root, twist=R(3))
for nm, z, h in (("bottom", 0.06, 0.09), ("top", 0.97, 0.09)):
    collar(f"{TAG} A1 collar {nm}", 0.27, z, h, tri, root, depth=0.04)
for k, z in enumerate((0.505, 0.585)):
    collar(f"{TAG} A1 band {k}", r_at(gp, z), z - 0.02, 0.035, tri, root, depth=0.025)
step = TAU / 3
for k in range(3):                                           # corner ribs follow the glass
    th = -math.pi / 2 + math.pi / 3 + k * step              # corners sit between the flat faces
    pts = []
    for r, z in gp[1:-1]:
        if 0.14 <= z <= 0.99:
            rr = (r * tri(th)) + 0.012
            pts.append((rr * math.cos(th), rr * math.sin(th), z))
    tube(f"{TAG} A1 rib {k}", pts, 0.011, root)
lathe(f"{TAG} A1 cap", [(0.0, 1.06), (0.2, 1.06), (0.12, 1.1), (0.0, 1.1)], tri, closed=True, mat=GOLD, parent=root)
port(f"{TAG} A1 port", 1.1, root)
bail(f"{TAG} A1 bail", 1.08, 0.21, 0.42, root, "tri")
lamp.location = (0, 0, 0.55)

# A2 Hex pinch (helix)
root, lamp = take("A2", "Hex pinch", 4, 0)
hexs = poly_shape(6, 0.06)
gp = glass_profile(0.12, 1.02, 0.25, 0.18, pinch=1.0)
glass(f"{TAG} A2 glass", gp, hexs, root, twist=R(3), sharp=R(35))
collar(f"{TAG} A2 collar bottom", 0.25, 0.05, 0.09, hexs, root, depth=0.045)
collar(f"{TAG} A2 collar top", 0.25, 0.99, 0.08, hexs, root, depth=0.045)
collar(f"{TAG} A2 waist", r_at(gp, 0.57), 0.55, 0.04, hexs, root, depth=0.03)
for k in range(6):                                           # crown of six points
    th = -math.pi / 2 + k * TAU / 6 + TAU / 12
    rr = 0.27
    tube(f"{TAG} A2 crown {k}", [(rr * math.cos(th), rr * math.sin(th), 1.07),
                                (rr * 0.92 * math.cos(th), rr * 0.92 * math.sin(th), 1.15)], 0.012, root)
lathe(f"{TAG} A2 cap", [(0.0, 1.07), (0.22, 1.07), (0.1, 1.12), (0.0, 1.12)], hexs, closed=True, mat=GOLD, parent=root,
      sharp=R(40))
port(f"{TAG} A2 port", 1.12, root)
ring = [(0.13 * math.cos(TAU * k / 48), 0.0, 1.32 + 0.13 * math.sin(TAU * k / 48)) for k in range(49)]
tube(f"{TAG} A2 ring handle", ring, 0.016, root)
tube(f"{TAG} A2 ring stem", [(0, 0, 1.17), (0, 0, 1.19)], 0.02, root)
lamp.location = (0, 0, 0.57)

# A3 Gold cage
root, lamp = take("A3", "Gold cage", 8, 0)
rnd = poly_shape(0, 0)
gp = glass_profile(0.12, 1.0, 0.24, 0.17, pinch=1.6)
glass(f"{TAG} A3 glass", gp, rnd, root)
collar(f"{TAG} A3 collar bottom", 0.24, 0.05, 0.08, rnd, root, depth=0.05)
collar(f"{TAG} A3 collar top", 0.24, 0.98, 0.07, rnd, root, depth=0.05)
for k in range(6):
    th = -math.pi / 2 + k * TAU / 6
    pts = []
    for r, z in gp[1:-1]:
        rr = r + 0.02 + 0.02 * math.sin(math.pi * (z - 0.12) / 0.88)            # bows out a little from the glass
        pts.append((rr * math.cos(th), rr * math.sin(th), z))
    tube(f"{TAG} A3 cage {k}", pts, 0.012, root)
lathe(f"{TAG} A3 dome", [(0.0, 1.05)] + [(0.27 * math.cos(R(a)), 1.05 + 0.08 * math.sin(R(a))) for a in range(0, 91, 10)][::-1][:-1]
      + [(0.0, 1.13)], rnd, mat=GOLD, parent=root)
port(f"{TAG} A3 port", 1.12, root)
bail(f"{TAG} A3 bail", 1.08, 0.23, 0.32, root, "arch")
lamp.location = (0, 0, 0.56)

# B1 Tower
root, lamp = take("B1", "Tower", 0, 7)
octs = poly_shape(8, 0.05)
sq = poly_shape(4, 0.08)
lathe(f"{TAG} B1 plinth", [(0.0, 0.0), (0.3, 0.0), (0.3, 0.06), (0.27, 0.09), (0.0, 0.09)], sq, closed=True, mat=GOLD,
      parent=root, sharp=R(40))
g1 = glass_profile(0.11, 0.6, 0.19, 0.215, pinch=0.8, cap=0.02)
g2 = glass_profile(0.68, 1.12, 0.17, 0.19, pinch=0.8, cap=0.02)
glass(f"{TAG} B1 glass low", g1, octs, root, sharp=R(30))
glass(f"{TAG} B1 glass high", g2, octs, root, sharp=R(30))
collar(f"{TAG} B1 collar low", 0.2, 0.08, 0.05, octs, root, depth=0.03)
collar(f"{TAG} B1 collar mid", 0.2, 0.59, 0.1, octs, root, depth=0.035)
collar(f"{TAG} B1 collar high", 0.18, 1.1, 0.05, octs, root, depth=0.03)
for k in range(8):                                           # corner posts between the chambers' facets
    th = -math.pi / 2 + k * TAU / 8 + TAU / 16
    for za, zb, rr in ((0.12, 0.59, 0.225), (0.69, 1.1, 0.2)):
        tube(f"{TAG} B1 post {k} {za}", [(rr * math.cos(th), rr * math.sin(th), za), (rr * math.cos(th), rr * math.sin(th), zb)],
             0.008, root)
lathe(f"{TAG} B1 spire", [(0.0, 1.15), (0.2, 1.15), (0.12, 1.25), (0.05, 1.42), (0.0, 1.46)], octs, mat=GOLD, parent=root,
      sharp=R(40))
port(f"{TAG} B1 port", 1.24, root, r=0.045)
lamp.location = (0, 0, 0.36)

# B2 Orb
root, lamp = take("B2", "Orb", 4, 7)
orb = [(0.0, 0.2)] + [(0.37 * math.sin(math.pi * k / 30), 0.57 - 0.37 * math.cos(math.pi * k / 30)) for k in range(1, 30)] \
      + [(0.0, 0.94)]
glass(f"{TAG} B2 glass", orb, rnd, root)
lathe(f"{TAG} B2 pedestal", [(0.0, 0.0), (0.24, 0.0), (0.24, 0.04), (0.09, 0.1), (0.07, 0.2), (0.12, 0.24), (0.0, 0.24)], rnd,
      closed=True, mat=GOLD, parent=root)
eq = [(0.395 * math.cos(TAU * k / 96), 0.395 * math.sin(TAU * k / 96), 0.57) for k in range(97)]
tube(f"{TAG} B2 equator", eq, 0.022, root)
hoop = [(0.42 * math.cos(TAU * k / 96), 0.0, 0.57 + 0.42 * math.sin(TAU * k / 96)) for k in range(97)]
h_o = tube(f"{TAG} B2 hoop", hoop, 0.016, root)
h_o.rotation_euler = (0, 0, R(45))
lathe(f"{TAG} B2 crown", [(0.0, 0.93), (0.1, 0.93), (0.1, 0.99), (0.06, 1.01), (0.0, 1.01)], rnd, closed=True, mat=GOLD,
      parent=root)
port(f"{TAG} B2 port", 1.0, root, r=0.04)
bail(f"{TAG} B2 bail", 1.0, 0.13, 0.22, root, "arch")
lamp.location = (0, 0, 0.57)

# B3 Hourglass prism
root, lamp = take("B3", "Hourglass prism", 8, 7)
tri_s = poly_shape(3, 0.12)
hg = [(0.0, 0.16)] + [(0.33 - 0.21 * (1 - abs(1 - 2 * k / 30)) ** 1.15, 0.16 + 0.9 * k / 30) for k in range(31)] + [(0.0, 1.06)]
glass(f"{TAG} B3 glass", hg, tri_s, root, twist=R(3), sharp=R(40))
collar(f"{TAG} B3 waist", 0.12, 0.585, 0.05, tri_s, root, depth=0.04)
collar(f"{TAG} B3 base ring", 0.33, 0.12, 0.05, tri_s, root, depth=0.03)
collar(f"{TAG} B3 top ring", 0.33, 1.04, 0.05, tri_s, root, depth=0.03)
for k in range(3):                                           # three legs from the base ring's corners
    th = -math.pi / 2 + math.pi / 3 + k * TAU / 3
    c, s = math.cos(th), math.sin(th)
    rr = 0.33 * tri_s(th) + 0.02
    tube(f"{TAG} B3 leg {k}", [(rr * c, rr * s, 0.13), ((rr + 0.04) * c, (rr + 0.04) * s, 0.05),
                              ((rr + 0.07) * c, (rr + 0.07) * s, 0.0)], 0.018, root)
lathe(f"{TAG} B3 cap", [(0.0, 1.09), (0.3, 1.09), (0.16, 1.13), (0.0, 1.13)], tri_s, closed=True, mat=GOLD, parent=root,
      sharp=R(40))
port(f"{TAG} B3 port", 1.13, root)
bail(f"{TAG} B3 bail", 1.11, 0.24, 0.38, root, "tri")
lamp.location = (0, 0, 0.6)

# ------------------------------------------------------------------ stage, light, cameras
w = bpy.data.worlds.new(f"{TAG} world")
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.01, 0.012, 0.014, 1)
scene.world = w
for nm, loc, e, size in (("key A", (5, -4, 4.5), 320, 6), ("rim A", (3, 3, 3.5), 220, 6),
                         ("key B", (5, 3, 4.5), 320, 6), ("rim B", (3, 10, 3.5), 220, 6)):
    ld = bpy.data.lights.new(f"{TAG} " + nm, "AREA"); ld.energy = e; ld.size = size
    lo = link(bpy.data.objects.new(f"{TAG} " + nm, ld)); lo.location = loc
    lo.rotation_euler = (lo.location * -1 + __import__("mathutils").Vector((4, 3.5 if "B" in nm else 0, 0))).to_track_quat("-Z", "Y").to_euler()
floor = bpy.data.meshes.new(f"{TAG} floor")
floor.from_pydata([(-3, -4, 0), (11, -4, 0), (11, 11, 0), (-3, 11, 0)], [], [(0, 1, 2, 3)])
fm = bpy.data.materials.new(f"{TAG} floor"); fm.use_nodes = True
fm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.01, 0.011, 0.013, 1)
fm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.55
floor.materials.append(fm)
link(bpy.data.objects.new(f"{TAG} floor", floor))


def cam(name, loc, look, lens=50):
    c = link(bpy.data.objects.new(name, bpy.data.cameras.new(name)))
    c.location = loc; c.data.lens = lens
    d = np.array(look, float) - np.array(loc, float)
    c.rotation_euler = (math.atan2(math.hypot(d[0], d[1]), -d[2]), 0, math.atan2(d[1], d[0]) - math.pi / 2)
    return c


CAMS = {}
for code, (name, root, _l) in TAKES.items():
    ox, oy, _ = root.location
    CAMS[code] = cam(f"Cam {code} {name}", (ox + 1.5, oy - 3.4, 1.35), (ox, oy, 0.72))
CAMS["all"] = cam("Cam all", (4, -9, 5.5), (4, 3.5, 0.6), 30)
scene.camera = CAMS["all"]

scene.render.engine = "BLENDER_EEVEE"
try:
    scene.eevee.use_raytracing = True                         # gold picks up the green glass
except Exception:
    pass
scene.view_settings.view_transform = "Standard"              # AgX washes bright green toward white
try:
    tree = bpy.data.node_groups.new(f"{TAG} bloom", "CompositorNodeTree")
    tree.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    rl = tree.nodes.new("CompositorNodeRLayers"); rl.scene = scene
    gl = tree.nodes.new("CompositorNodeGlare")
    try:
        gl.inputs["Type"].default_value = "Bloom"
    except Exception:
        gl.glare_type = "BLOOM"
    for nm, v in (("Threshold", 0.7), ("Strength", 0.55), ("Size", 0.5)):
        try:
            gl.inputs[nm].default_value = v
        except Exception:
            pass
    go = tree.nodes.new("NodeGroupOutput")
    tree.links.new(rl.outputs["Image"], gl.inputs["Image"]); tree.links.new(gl.outputs["Image"], go.inputs[0])
    scene.compositing_node_group = tree
except Exception as e:
    print("bloom:", e)

# one check render per take (LL_CHECK_DIR set by the PC chat; the review renderer makes the real clips)
chk = os.environ.get("LL_CHECK_DIR")
if chk:
    os.makedirs(chk, exist_ok=True)
    scene.render.resolution_x = scene.render.resolution_y = 640
    scene.frame_set(int(os.environ.get("LL_CHECK_FRAME", "118")))
    for code in list(TAKES) + ["all"]:
        scene.camera = CAMS[code]
        scene.render.filepath = os.path.join(chk, f"{PASS}_{code}.png")
        bpy.ops.render.render(write_still=True, scene=scene.name)
    scene.camera = CAMS["all"]
try:
    bpy.ops.outliner.orphans_purge(do_recursive=True)
except Exception:
    pass
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("saved", OUT)
