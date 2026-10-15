# Pass 853: Pickaxe rework: 3D pick, block breaking, running crater swing (Chat C, 2026-10-15, range 800-899).
# Source: 844 P1a "Pickaxe: quick mining taps" (IMPROVE, with a note). J's words:
#   "make it a more 3d but still thin and denser axe, maybe new destruction animations given I use physical block drops
#    in my shaders. more variations of the pickaxe since it will be different now. arm animations too, it should cause
#    particles when i break things that keep things light, and if im running through and holding the pickaxe i need
#    extensive animations of swingins the pickaxe and about 8 blocks breaking at a time in small crater domewide swing
#    but it doesnt instantly destroy."
# Kept from P1a: the pixel-stream build from the ring (P takes), the right arm with the ring on the punching face, the
# 120 degree first-person camera with a crosshair, quick taps as the base rhythm.
# New in every take: a real-thickness construct pick (bevelled, faceted, thin and dense), real 1 m stone/dirt blocks that
# crack over a few ticks (pixel cracks spread across the faces), then break into a few physical chunks that fall, bounce
# and settle like item drops, plus a light puff of small construct sparks and stone dust. Construct glow is only on the pick.
#   P1a1 Faceted crescent pick (lofted diamond section, glowing core seen through the glass, glowing points):
#        three quick overhead taps, each one cracks the block further, the third (bigger) breaks it; steps in, mines the next.
#   P1a2 Laminated pick (stacked plates: a glowing core plate between stepped glass plates; spike + chisel back, twisted haft):
#        forehand then backhand diagonal strikes; the first strike cracks the block, cracks keep creeping, the second breaks it.
#   P1a3 Shell-and-core pick (chamfered glass shell over a glowing core, straight diamond spikes, spiral-wrapped haft):
#        one heavy wind-up strike that bites in, the crack spreads over 5 ticks, then a wrist pry bursts the block.
#   R1   Running through a wall with P1a1: steady overhead chops every 9 ticks; each chop carves a dome crater of 8 blocks,
#        cracks spread from the impact outward and the blocks break 5 ticks later.
#   R2   Running through with P1a2: fast alternating diagonal figure-eight, a strike every 7 ticks; cracks run along the
#        swing's diagonal, 4 ticks to break.
#   R3   Running through with P1a3: wide dome arcs, high right over the top to low left, every 10 ticks; the blocks crack
#        along the arc right to left, 6 ticks to break.
# R tunnel: each swing carves the next 8 blocks of a dome arch (3 wide, 2 high, a crown block), nearest the strike first;
# the wall has no column right of the tunnel so the side camera sees in. A review-only point light rides with the player.
# Cameras: "Cam <take>" first person (120 deg, crosshair; moves with the player), "Cam <take> side" third person from the
# right (moves with the player).
# Builds LanternLive\combat\pickaxe_rework.blend (scene "Pickaxe Rework").
import json, math, os
import bpy, bmesh
import numpy as np
from mathutils import Matrix, Euler, Vector

R = math.radians
OUT = os.path.join(FOLDER, "combat", "pickaxe_rework.blend")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
if bpy.data.filepath:
    try:
        bpy.ops.wm.save_mainfile()
    except Exception as e:
        print("save current:", e)
SCN = "Pickaxe Rework"
old = bpy.data.scenes.get(SCN)
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new(SCN)
col = scene.collection
scene.render.fps = 20
win = bpy.context.window
if win:
    win.scene = scene
FORM = 14                 # forming ticks (P takes)
P = 1 / 16
PX = P * 1.05             # first-person pixel (as 844)
G = 16.0                  # drop gravity, m/s^2 (Minecraft items fall fast)
EYE_H = 1.62


def link(o):
    col.objects.link(o)
    return o


def cam(name, loc, look, lens=40, parent=None):
    c = link(bpy.data.objects.new(name, bpy.data.cameras.new(name)))
    c.location = loc; c.data.lens = lens; c.data.clip_start = 0.02
    d = np.array(look, float) - np.array(loc, float)
    c.rotation_euler = (math.atan2(math.hypot(d[0], d[1]), -d[2]), 0, math.atan2(d[1], d[0]) - math.pi / 2)
    if parent is not None:
        c.parent = parent
    return c


def mat(name, rgb, emit=0.0, alpha=1.0, rough=0.4, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*rgb, 1); p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    if emit:
        p.inputs["Emission Color"].default_value = (*rgb, 1); p.inputs["Emission Strength"].default_value = emit
    if alpha < 1:
        p.inputs["Alpha"].default_value = alpha
        try:
            m.surface_render_method = "BLENDED"
        except Exception:
            pass
    return m


SKIN = mat("PK skin", (0.62, 0.42, 0.3)); SLEEVE = mat("PK sleeve", (0.04, 0.28, 0.12))
PANTS = mat("PK pants", (0.1, 0.12, 0.3), rough=0.8)
RINGM = mat("PK ring face", (0.02, 0.85, 0.15), emit=2.0); GOLDM = mat("PK ring gold", (0.95, 0.7, 0.2), rough=0.25, metal=1.0)
GLASS = mat("PK pick glass", (0.02, 0.36, 0.12), emit=0.7, alpha=0.78, rough=0.12)
SHELL = mat("PK pick shell", (0.02, 0.3, 0.1), emit=0.5, alpha=0.62, rough=0.08)
CORE = mat("PK pick core", (0.04, 0.85, 0.2), emit=2.6)
RIM = mat("PK pick rim", (0.06, 1.0, 0.25), emit=4.0)
GRIP = mat("PK pick grip", (0.015, 0.16, 0.06), emit=0.5, rough=0.3)
PIX = mat("PK forming pixel", (0.06, 1.0, 0.28), emit=4.0)
SPARK = mat("PK construct spark", (0.05, 0.95, 0.22), emit=3.5, alpha=0.9)
DUST = mat("PK stone dust", (0.42, 0.42, 0.42), alpha=0.7, rough=1.0)
XH = mat("PK crosshair", (0.85, 0.85, 0.85), emit=1.0)
LABEL = mat("PK label", (0.8, 0.8, 0.8), emit=0.6)
FLOOR = mat("PK floor", (0.2, 0.22, 0.2), rough=0.95)
WALL = mat("PK backdrop", (0.24, 0.26, 0.3), rough=0.95)


def block_mat(name, c0, c1, crack_rgb):
    """Minecraft-like block: 16 px per face (colour per pixel), plus pixel cracks driven by the object's "crack"
    property (0 none .. 1 about to break) that spread over the faces as it rises."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; N = nt.nodes; L = nt.links
    bsdf = N["Principled BSDF"]; bsdf.inputs["Roughness"].default_value = 0.92
    tc = N.new("ShaderNodeTexCoord")
    snap = N.new("ShaderNodeVectorMath"); snap.operation = "SNAP"; snap.inputs[1].default_value = (1 / 16,) * 3
    L.new(tc.outputs["Object"], snap.inputs[0])
    oi = N.new("ShaderNodeObjectInfo")
    off = N.new("ShaderNodeVectorMath"); off.operation = "ADD"
    L.new(snap.outputs[0], off.inputs[0])
    sc_ = N.new("ShaderNodeVectorMath"); sc_.operation = "SCALE"; L.new(oi.outputs["Random"], sc_.inputs["Scale"])
    sc_.inputs[0].default_value = (37.0, 11.0, 23.0); L.new(sc_.outputs[0], off.inputs[1])
    wn = N.new("ShaderNodeTexWhiteNoise"); wn.noise_dimensions = "3D"; L.new(off.outputs[0], wn.inputs["Vector"])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.0; L.new(off.outputs[0], nz.inputs["Vector"])
    mixv = N.new("ShaderNodeMix"); mixv.data_type = "FLOAT"; mixv.inputs[0].default_value = 0.45
    L.new(wn.outputs["Value"], mixv.inputs[2]); L.new(nz.outputs["Fac"], mixv.inputs[3])
    ramp = N.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.25; ramp.color_ramp.elements[0].color = (*c0, 1)
    ramp.color_ramp.elements[1].position = 0.75; ramp.color_ramp.elements[1].color = (*c1, 1)
    L.new(mixv.outputs[0], ramp.inputs["Fac"])
    # cracks: voronoi cell edges on the pixel grid, revealed by a noise mask as crack rises
    vo = N.new("ShaderNodeTexVoronoi"); vo.feature = "DISTANCE_TO_EDGE"; vo.inputs["Scale"].default_value = 2.6
    L.new(off.outputs[0], vo.inputs["Vector"])
    attr = N.new("ShaderNodeAttribute"); attr.attribute_type = "OBJECT"; attr.attribute_name = "crack"
    lt = N.new("ShaderNodeMath"); lt.operation = "LESS_THAN"; lt.inputs[1].default_value = 0.045
    L.new(vo.outputs["Distance"], lt.inputs[0])
    nz2 = N.new("ShaderNodeTexNoise"); nz2.inputs["Scale"].default_value = 1.6; L.new(off.outputs[0], nz2.inputs["Vector"])
    cr = N.new("ShaderNodeMath"); cr.operation = "MULTIPLY"; cr.inputs[1].default_value = 1.25
    L.new(attr.outputs["Fac"], cr.inputs[0])
    rv = N.new("ShaderNodeMath"); rv.operation = "LESS_THAN"; L.new(nz2.outputs["Fac"], rv.inputs[0]); L.new(cr.outputs[0], rv.inputs[1])
    cm = N.new("ShaderNodeMath"); cm.operation = "MULTIPLY"; L.new(lt.outputs[0], cm.inputs[0]); L.new(rv.outputs[0], cm.inputs[1])
    mixc = N.new("ShaderNodeMix"); mixc.data_type = "RGBA"
    L.new(cm.outputs[0], mixc.inputs[0]); L.new(ramp.outputs["Color"], mixc.inputs[6])
    mixc.inputs[7].default_value = (*crack_rgb, 1)
    L.new(mixc.outputs[2], bsdf.inputs["Base Color"])
    return m


STONE = block_mat("PK stone", (0.27, 0.27, 0.28), (0.44, 0.44, 0.45), (0.05, 0.05, 0.055))
DIRT = block_mat("PK dirt", (0.27, 0.18, 0.11), (0.43, 0.3, 0.19), (0.07, 0.045, 0.03))

# head: skin from outside, see-through from inside (the eye camera sits in it)
HEAD = bpy.data.materials.new("PK head"); HEAD.use_nodes = True
_n = HEAD.node_tree.nodes; _l = HEAD.node_tree.links
_n["Principled BSDF"].inputs["Base Color"].default_value = (0.55, 0.38, 0.27, 1)
_geo = _n.new("ShaderNodeNewGeometry"); _tr = _n.new("ShaderNodeBsdfTransparent"); _mx = _n.new("ShaderNodeMixShader")
_l.new(_geo.outputs["Backfacing"], _mx.inputs[0]); _l.new(_n["Principled BSDF"].outputs[0], _mx.inputs[1])
_l.new(_tr.outputs[0], _mx.inputs[2]); _l.new(_mx.outputs[0], _n["Material Output"].inputs["Surface"])
try:
    HEAD.surface_render_method = "BLENDED"; HEAD.use_backface_culling = False
except Exception:
    pass

BOXF = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]


def box(name, a, b, m, parent=None, loc=None):
    a = np.array(a, float); b = np.array(b, float)
    v = [(x, y, z) for x in (a[0], b[0]) for y in (a[1], b[1]) for z in (a[2], b[2])]
    me = bpy.data.meshes.new(name); me.from_pydata(v, [], BOXF); me.update(); me.materials.append(m)
    o = link(bpy.data.objects.new(name, me))
    if parent is not None:
        o.parent = parent
    if loc is not None:
        o.location = loc
    return o


def key(o, f, loc=None, rot=None, sc=None):
    if loc is not None:
        o.location = loc; o.keyframe_insert("location", frame=f)
    if rot is not None:
        o.rotation_euler = rot; o.keyframe_insert("rotation_euler", frame=f)
    if sc is not None:
        o.scale = (sc,) * 3 if np.isscalar(sc) else sc; o.keyframe_insert("scale", frame=f)


def key_hide(o, f, hidden):
    o.hide_render = hidden; o.keyframe_insert("hide_render", frame=f)
    o.hide_viewport = hidden; o.keyframe_insert("hide_viewport", frame=f)


def smooth(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


# ------------------------------------------------------------------ mesh pieces (verts, faces, material), tool space
def p_box(a, b, m):
    v = [(x, y, z) for x in (a[0], b[0]) for y in (a[1], b[1]) for z in (a[2], b[2])]
    return (v, list(BOXF), m)


def p_prism(n, r, y0, y1, m, rot=0.0, cx=0.0, cz=0.0):
    """n-sided prism along +Y (a haft, a collar)."""
    ring = [(cx + r * math.cos(rot + 2 * math.pi * i / n), cz + r * math.sin(rot + 2 * math.pi * i / n)) for i in range(n)]
    v = [(x, y0, z) for x, z in ring] + [(x, y1, z) for x, z in ring]
    f = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    f += [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    return (v, f, m)


def p_loft(rings, m, apex0=None, apex1=None):
    """Loft equal-count vertex rings; optional apex points close the ends (pointed tips)."""
    n = len(rings[0]); v = [tuple(p) for r in rings for p in r]; f = []
    for k in range(len(rings) - 1):
        a = k * n; b = (k + 1) * n
        f += [(a + i, a + (i + 1) % n, b + (i + 1) % n, b + i) for i in range(n)]
    if apex0 is not None:
        v.append(tuple(apex0)); c = len(v) - 1
        f += [((i + 1) % n, i, c) for i in range(n)]
    else:
        f.append(tuple(range(n - 1, -1, -1)))
    if apex1 is not None:
        v.append(tuple(apex1)); c = len(v) - 1; b = (len(rings) - 1) * n
        f += [(b + i, b + (i + 1) % n, c) for i in range(n)]
    else:
        b = (len(rings) - 1) * n; f.append(tuple(b + i for i in range(n)))
    return (v, f, m)


def p_plate(poly, z0, z1, m):
    """2D outline (x, y) extruded along Z (an ngon cap each side)."""
    n = len(poly)
    v = [(x, y, z0) for x, y in poly] + [(x, y, z1) for x, y in poly]
    f = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    f += [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    return (v, f, m)


def p_octa(c, rx, ry, rz, m):
    c = np.array(c, float)
    v = [tuple(c + d) for d in ((rx, 0, 0), (-rx, 0, 0), (0, ry, 0), (0, -ry, 0), (0, 0, rz), (0, 0, -rz))]
    f = [(0, 2, 4), (2, 1, 4), (1, 3, 4), (3, 0, 4), (2, 0, 5), (1, 2, 5), (3, 1, 5), (0, 3, 5)]
    return (v, f, m)


def inset(poly, d):
    """Offset a CCW outline inward by d (miter, clamped): the stepped plates of the laminated pick."""
    out = []; n = len(poly)
    for i in range(n):
        p0 = np.array(poly[i - 1]); p1 = np.array(poly[i]); p2 = np.array(poly[(i + 1) % n])
        e1 = p1 - p0; e2 = p2 - p1
        n1 = np.array((-e1[1], e1[0])) / np.linalg.norm(e1); n2 = np.array((-e2[1], e2[0])) / np.linalg.norm(e2)
        nb = n1 + n2; ln = np.linalg.norm(nb)
        nb = nb / ln if ln > 1e-6 else n1
        k = d / max(0.35, float(np.dot(nb, n1)))
        out.append(tuple(p1 + nb * min(k, 2.2 * d)))
    return out


def bevel_piece(pc, w):
    """Chamfer every edge of a piece (bmesh bevel, 1 segment): facets on the shell-and-core pick."""
    v, f, m = pc
    bm = bmesh.new()
    vs = [bm.verts.new(p) for p in v]
    for fc in f:
        try:
            bm.faces.new([vs[i] for i in fc])
        except ValueError:
            pass
    bm.normal_update()
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=w, segments=1, affect="EDGES", profile=0.5, clamp_overlap=True)
    v2 = [tuple(x.co) for x in bm.verts]; idx = {x: i for i, x in enumerate(bm.verts)}
    f2 = [tuple(idx[x] for x in fc.verts) for fc in bm.faces]
    bm.free()
    return (v2, f2, m)


# ------------------------------------------------------------------ the three picks (grip at 0, haft along +Y, head across X)
def pick_crescent():
    """P1a1: lofted crescent, diamond (rhombus) section that tapers to two points; a glowing core loft inside the glass;
    glowing points; hexagonal haft with glow bands; hex collar; bipyramid pommel."""
    out = []
    out.append(p_prism(6, 0.02, -0.02, 0.86, GRIP, rot=R(30)))
    for y in (0.08, 0.26, 0.44):
        out.append(p_prism(6, 0.026, y, y + 0.014, CORE, rot=R(30)))
    out.append(p_prism(8, 0.036, 0.79, 0.895, GLASS, rot=R(22.5)))
    out.append(p_prism(8, 0.039, 0.835, 0.85, RIM, rot=R(22.5)))
    out.append(p_octa((0, -0.03, 0), 0.03, 0.03, 0.03, RIM))

    def sec(s, scale):
        a = abs(s)
        c = np.array((0.31 * s, 0.85 - 0.11 * s * s, 0.0))
        t = np.array((0.31, -0.22 * s, 0.0)); t /= np.linalg.norm(t)
        nrm = np.array((-t[1], t[0], 0.0))
        h = (0.006 + 0.036 * (1 - a ** 1.5)) * scale; w = (0.004 + 0.026 * (1 - a ** 1.3)) * scale
        z = np.array((0, 0, 1.0))
        return [c + nrm * h, c + z * w, c - nrm * h, c - z * w], c, t

    for side in (-1, 1):
        ss = [side * x for x in np.linspace(0.0, 0.74, 9)]
        rings = [sec(s, 1.0)[0] for s in ss]
        out.append(p_loft(rings, GLASS))
        ss2 = [side * x for x in np.linspace(0.74, 1.0, 4)]
        rings2 = [sec(s, 1.0)[0] for s in ss2]
        _, c_end, t_end = sec(side * 1.0, 1.0)
        out.append(p_loft(rings2, RIM, apex1=c_end + t_end * side * 0.05))
        rc = [sec(s, 0.42)[0] for s in [side * x for x in np.linspace(0.02, 0.8, 7)]]
        out.append(p_loft(rc, CORE))
    return out, (0.36, 0.73)          # lead point (x, y) in tool space


PROFILE2 = [(0.37, 0.772), (0.29, 0.832), (0.17, 0.874), (0.05, 0.894), (-0.05, 0.894), (-0.15, 0.884), (-0.235, 0.928),
            (-0.258, 0.918), (-0.258, 0.80), (-0.235, 0.79), (-0.15, 0.824), (-0.05, 0.80), (0.05, 0.80), (0.16, 0.816),
            (0.27, 0.794)]


def pick_laminated():
    """P1a2: three stacked plates and two thin skins: a glowing core plate (its edge shows all round), stepped glass plates
    inset either side; a long spike to +X, a flared chisel back; a twisted square haft; octahedron pommel."""
    out = []
    poly = PROFILE2[::-1] if sum(PROFILE2[i][0] * PROFILE2[(i + 1) % len(PROFILE2)][1] - PROFILE2[(i + 1) % len(PROFILE2)][0]
                                 * PROFILE2[i][1] for i in range(len(PROFILE2))) < 0 else PROFILE2
    out.append(p_plate(poly, -0.007, 0.007, RIM))
    in1 = inset(poly, 0.01); in2 = inset(poly, 0.024)
    for s in (-1, 1):
        out.append(p_plate(in1, s * 0.008, s * 0.019, GLASS))
        out.append(p_plate(in2, s * 0.02, s * 0.027, GLASS))
    for k in range(11):                                        # twisted haft: square segments, 8 deg more each
        y0 = -0.02 + k * 0.074
        out.append(p_prism(4, 0.025, y0, y0 + 0.072, GRIP if k % 4 else CORE, rot=R(45 + 8 * k)))
    out.append(p_octa((0, -0.04, 0), 0.032, 0.035, 0.032, RIM))
    return out, (0.37, 0.772)


def pick_shell():
    """P1a3: a chamfered glass shell (head hub + two straight diamond-section spikes, long front, short back with a chisel
    end), a glowing core of the same shape at half size inside, glowing point caps; a round haft with a spiral wrap."""
    out = []
    out.append(p_prism(12, 0.019, -0.02, 0.86, GRIP))
    for k in range(16):                                        # spiral wrap: small glow blocks round the haft
        a = k * R(52); y = 0.05 + k * 0.034
        out.append(p_box((0.019 * math.cos(a) - 0.008, y, 0.019 * math.sin(a) - 0.008),
                         (0.019 * math.cos(a) + 0.008, y + 0.012, 0.019 * math.sin(a) + 0.008), CORE))
    out.append(p_octa((0, -0.035, 0), 0.026, 0.03, 0.026, RIM))

    def head(scale, m, chamfer):
        yc = 0.845; pcs = []
        hub = p_prism(6, 0.05 * scale, yc - 0.055 * scale, yc + 0.055 * scale, m, rot=R(30))
        pcs.append(hub)
        for side, ln, tipw in ((1, 0.34, 0.0), (-1, 0.22, 0.018)):
            def dia(x, r):
                return [(x, yc + r, 0), (x, yc, r * 0.8), (x, yc - r, 0), (x, yc, -r * 0.8)]
            xs = [side * 0.045 * scale, side * (0.045 + (ln - 0.045) * 0.55) * scale, side * (ln - 0.03) * scale]
            rs = [0.042 * scale, 0.03 * scale, (0.012 + tipw) * scale]
            rings = [dia(x, r) for x, r in zip(xs, rs)]
            if side < 0:
                rings = rings[::-1]
            pcs.append(p_loft(rings, m, apex0=(side * ln * scale, yc, 0) if side < 0 and tipw == 0 else None,
                              apex1=(side * ln * scale, yc, 0) if side > 0 else None))
        return [bevel_piece(p, chamfer) if chamfer else p for p in pcs]

    out += head(1.0, SHELL, 0.006)
    out += head(0.5, CORE, 0.0)
    out.append(p_octa((0.335, 0.845, 0), 0.03, 0.016, 0.014, RIM))
    out.append(p_box((-0.232, 0.828, -0.012), (-0.214, 0.862, 0.012), RIM))
    return out, (0.35, 0.845)


PICKS = {"crescent": pick_crescent, "laminated": pick_laminated, "shell": pick_shell}
PICK_NAME = {"crescent": "faceted crescent pick", "laminated": "laminated pick", "shell": "shell-and-core pick"}


def merge_mesh(name, pieces, parent, origin):
    mats = []; verts = []; faces = []; fm = []
    for v, f, m in pieces:
        if m not in mats:
            mats.append(m)
        base = len(verts)
        verts += [tuple(np.array(p) - origin) for p in v]
        faces += [tuple(base + i for i in fc) for fc in f]; fm += [mats.index(m)] * len(f)
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    for m in mats:
        me.materials.append(m)
    for p, i in zip(me.polygons, fm):
        p.material_index = i
    o = link(bpy.data.objects.new(name, me)); o.parent = parent; o.location = tuple(origin)
    return o


def build_tool(tag, kind, root, nb=6):
    """The pick in sections along its length (grip first), each its own object (origin at its centre) for the build."""
    pcs, lead = PICKS[kind]()
    span = max(max(p[1] for p in v) for v, _, _ in pcs)
    bands = [[] for _ in range(nb)]
    for pc in pcs:
        cy = float(np.mean([p[1] for p in pc[0]]))
        bands[min(nb - 1, max(0, int(cy / span * nb)))].append(pc)
    parts = []
    for k, bl in enumerate(bands):
        if not bl:
            continue
        allv = np.array([p for v, _, _ in bl for p in v])
        c = (allv.min(0) + allv.max(0)) / 2
        parts.append((merge_mesh(f"{tag} tool part {k}", bl, root, c), c))
    return parts, lead, span


# ------------------------------------------------------------------ arm rig (as 844: ring on the punching face)
def ring_on_fist(tag, parent, end_z, px):
    mt = link(bpy.data.objects.new(f"{tag} ring mount", None)); mt.parent = parent
    mt.location = (0, 0, end_z); mt.rotation_euler = (0, 0, R(90))
    c = 0.6 * px
    box(f"{tag} ring band", (1.95 * px, -0.55 * px, 0), (2.25 * px, 0.55 * px, 1.4 * px), GOLDM, mt)
    box(f"{tag} ring frame", (c - 1.25 * px, -1.25 * px, -0.45 * px), (c + 1.25 * px, 1.25 * px, 0), GOLDM, mt)
    box(f"{tag} ring face", (c - 0.95 * px, -0.95 * px, -1.0 * px), (c + 0.95 * px, 0.95 * px, -0.4 * px), RINGM, mt)
    return Vector((0, c, end_z - 1.0 * px))


GRIP_LOC = Vector((0, -1.1 * PX, -10.6 * PX))
SHOULDER = Vector((0.36, 0.12, -0.42))           # from the eye (844's first-person arm)


def make_arm(tag, root):
    sh = link(bpy.data.objects.new(f"{tag} shoulder", None)); sh.parent = root; sh.location = SHOULDER; sh.rotation_mode = "XYZ"
    box(f"{tag} sleeve", (-2 * PX, -2 * PX, -8 * PX), (2 * PX, 2 * PX, 0), SLEEVE, sh)
    box(f"{tag} hand", (-2 * PX, -2 * PX, -12 * PX), (2 * PX, 2 * PX, -8 * PX), SKIN, sh)
    box(f"{tag} knuckles", (-2.05 * PX, 1.2 * PX, -12.05 * PX), (2.05 * PX, 2.05 * PX, -11.1 * PX), SKIN, sh)
    ring_pt = ring_on_fist(tag, sh, -12 * PX, PX)
    grip = link(bpy.data.objects.new(f"{tag} grip", None)); grip.parent = sh
    grip.location = tuple(GRIP_LOC); grip.rotation_mode = "XYZ"
    return sh, grip, ring_pt


def arm_euler(p):
    pitch, yaw, roll, tilt, reach = p
    e_ = Euler((R(pitch), 0, R(yaw)), "XYZ"); e_.rotate_axis("Z", R(roll))
    return e_


def grip_matrix(tilt):
    return Matrix.Translation(GRIP_LOC) @ Matrix.Rotation(R(-tilt), 4, "X")


def tool_matrix(root_loc, p, phi):
    """Tool space -> world, for a root (eye) location, an arm pose and a tool twist."""
    sh = Matrix.Translation(Vector(root_loc) + SHOULDER + Vector((0, p[4], 0))) @ arm_euler(p).to_matrix().to_4x4()
    return sh @ grip_matrix(p[3]) @ Matrix.Rotation(phi, 4, "Y")


def make_body(tag, root):
    """A Minecraft player for the side camera: head (see-through from inside, the eye sits in it), torso set back so
    the eye camera never sees it, legs and a left arm that swing with the run."""
    b = link(bpy.data.objects.new(f"{tag} hips", None)); b.parent = root; b.location = (0, -0.18, -0.87)
    box(f"{tag} torso", (-0.25, -0.125, 0), (0.25, 0.125, 0.75), SLEEVE, b)
    box(f"{tag} head", (-0.25, -0.07, 0.75), (0.25, 0.43, 1.25), HEAD, b)
    legs = []
    for sx in (-1, 1):
        lp = link(bpy.data.objects.new(f"{tag} leg pivot {sx}", None)); lp.parent = b; lp.location = (sx * 0.125, 0, 0)
        lp.rotation_mode = "XYZ"
        box(f"{tag} leg {sx}", (-0.125, -0.125, -0.75), (0.125, 0.125, 0), PANTS, lp)
        legs.append(lp)
    ap = link(bpy.data.objects.new(f"{tag} left arm pivot", None)); ap.parent = b; ap.location = (-0.375, 0, 0.7)
    ap.rotation_mode = "XYZ"
    box(f"{tag} left arm", (-0.125, -0.125, -0.75), (0.125, 0.125, 0), SLEEVE, ap)
    box(f"{tag} left hand", (-0.126, -0.126, -0.75), (0.126, 0.126, -0.5), SKIN, ap)
    return legs, ap


# ------------------------------------------------------------------ world cells and physical drops
class Cells:
    """Unit blocks on a grid (origin ox, oy, 0): each cell has a break tick (None = never)."""
    def __init__(self, ox, oy):
        self.o = Vector((ox, oy, 0.0)); self.brk = {}

    def add(self, ijk):
        self.brk.setdefault(ijk, None)

    def centre(self, ijk):
        return self.o + Vector((ijk[0] + 0.5, ijk[1] + 0.5, ijk[2] + 0.5))

    def solid(self, p, t):
        if p.z < 0:
            return True
        q = p - self.o
        ijk = (math.floor(q.x), math.floor(q.y), math.floor(q.z))
        if ijk not in self.brk:
            return False
        b = self.brk[ijk]
        return b is None or t < b


def sim_drop(cells, p0, v0, w0, half, t0, t1):
    """Ballistic chunk: gravity, bounces off the floor and blocks still standing (restitution 0.35), rolls to a stop
    and settles flat. Returns per-tick (location, rotation)."""
    pos = Vector(p0); vel = Vector(v0); ang = Vector((0, 0, 0)); angv = Vector(w0)
    out = []; dt = 1 / 80; resting = False
    for t in range(t0, t1 + 1):
        out.append((pos.copy(), ang.copy()))
        for _ in range(4):
            tt = t + _ / 4
            if not cells.solid(pos + Vector((0, 0, -half - 0.01)), tt):
                resting = False
            if resting:
                break
            vel.z -= G * dt
            for ax in range(3):
                trial = pos.copy(); trial[ax] += vel[ax] * dt
                probe = trial.copy(); probe[ax] += math.copysign(half, vel[ax] if vel[ax] else -1)
                if cells.solid(probe, tt):
                    if ax == 2 and vel.z < 0:
                        vel.z = -vel.z * 0.35; vel.x *= 0.6; vel.y *= 0.6; angv *= 0.5
                        if abs(vel.z) < 0.7:
                            vel.z = 0.0; vel.x *= 0.5; vel.y *= 0.5
                            if vel.length < 0.15:
                                resting = True; vel = Vector((0, 0, 0)); angv = Vector((0, 0, 0))
                    else:
                        vel[ax] = -vel[ax] * 0.3
                else:
                    pos[ax] = trial[ax]
            ang += angv * dt
        if resting:                                       # settle flat: ease the tumble to the nearest quarter turn
            for ax in (0, 1):
                tgt = round(ang[ax] / (math.pi / 2)) * (math.pi / 2)
                ang[ax] += (tgt - ang[ax]) * 0.5
    return out


CHUNK_MESH = {}


def chunk_mesh(m, seed):
    k = (m.name, seed)
    if k not in CHUNK_MESH:
        r = np.random.default_rng(seed)
        v = [(x * (1 + r.uniform(-0.25, 0.1)), y * (1 + r.uniform(-0.25, 0.1)), z * (1 + r.uniform(-0.25, 0.1)))
             for x in (-0.5, 0.5) for y in (-0.5, 0.5) for z in (-0.5, 0.5)]
        me = bpy.data.meshes.new(f"PK chunk {m.name} {seed}"); me.from_pydata(v, [], BOXF); me.update(); me.materials.append(m)
        CHUNK_MESH[k] = me
    return CHUNK_MESH[k]


SPARK_MESH = None; DUST_MESH = None


def fx_meshes():
    global SPARK_MESH, DUST_MESH
    if SPARK_MESH is None:
        s = 0.5
        SPARK_MESH = bpy.data.meshes.new("PK spark"); SPARK_MESH.from_pydata(
            [(x, y, z) for x in (-s, s) for y in (-s, s) for z in (-s, s)], [], BOXF); SPARK_MESH.materials.append(SPARK)
        DUST_MESH = bpy.data.meshes.new("PK dust"); DUST_MESH.from_pydata(
            [(x, y, z) for x in (-s, s) for y in (-s, s) for z in (-s, s)], [], BOXF); DUST_MESH.materials.append(DUST)
    return SPARK_MESH, DUST_MESH


def puff(tag, at, t, rng, n_spark, n_dust, away, life=7):
    """A light puff: a few small construct sparks (green) and stone dust motes, out and gone in ~life ticks."""
    sm, dm = fx_meshes(); t = t + 1                         # tick -> frame
    for i in range(n_spark + n_dust):
        is_s = i < n_spark
        o = link(bpy.data.objects.new(f"{tag} {'spark' if is_s else 'dust'}", sm if is_s else dm))
        d = Vector(rng.normal(0, 1, 3)); d.z = abs(d.z) + 0.3; d = (d.normalized() + away * 0.6).normalized()
        sp = (1.6 if is_s else 0.6) * rng.uniform(0.6, 1.2); size = 0.035 if is_s else 0.07
        p0 = Vector(at) + Vector(rng.uniform(-0.15, 0.15, 3))
        key(o, 1, loc=p0, sc=0.0001); key(o, max(1, t - 1), loc=p0, sc=0.0001)
        for k in range(life + 1):
            g = 6.0 if is_s else -0.6
            p = p0 + d * sp * (k / 20) - Vector((0, 0, 0.5 * g * (k / 20) ** 2))
            s = size * (1 - (k / life) ** 2) if is_s else size * (0.6 + 0.6 * k / life) * (1 - (k / life) ** 3)
            key(o, t + k, loc=p, sc=max(0.0001, s))


def break_block(tag, cells, ijk, obj, t_crack0, t_break, t_end, rng, n_chunks, away, crack_steps=None, pop=(1.4, 3.0)):
    """Crack over the given ticks (pixel cracks spread), a tiny shudder, then: hide the block, throw physical chunks
    and a light puff."""
    F = 1                                                   # tick -> frame
    obj["crack"] = 0.0
    obj.keyframe_insert('["crack"]', frame=1); obj.keyframe_insert('["crack"]', frame=t_crack0 + F)
    steps = crack_steps or [(t_crack0 + (t_break - t_crack0) * (k + 1) / 4, (k + 1) / 4) for k in range(4)]
    for f, v in steps:
        obj["crack"] = min(1.0, v); obj.keyframe_insert('["crack"]', frame=int(round(f)) + F)
    base = obj.location.copy()
    key(obj, t_crack0 + F, loc=base); key(obj, t_break - 2 + F, loc=base)
    key(obj, t_break - 1 + F, loc=base + Vector(rng.uniform(-0.015, 0.015, 3)))
    key_hide(obj, 1, False); key_hide(obj, t_break + F, True)
    c = cells.centre(ijk); m = obj.data.materials[0]
    for i in range(n_chunks):
        half = rng.uniform(0.09, 0.14)
        o = link(bpy.data.objects.new(f"{tag} chunk", chunk_mesh(m, int(rng.integers(0, 6)))))
        o.rotation_mode = "XYZ"
        p0 = c + Vector(rng.uniform(-0.28, 0.28, 3))
        out = (p0 - c); out.z = 0
        v0 = (out.normalized() if out.length > 1e-3 else Vector((0, 0, 0))) * rng.uniform(0.6, 1.4) + away * rng.uniform(0.8, 1.6)
        v0.z = rng.uniform(*pop)
        w0 = Vector(rng.uniform(-9, 9, 3))
        track = sim_drop(cells, p0, v0, w0, half, t_break, t_end)
        key(o, 1, loc=p0, rot=(0, 0, 0), sc=0.0001); key(o, t_break - 1 + F, sc=0.0001)
        key(o, t_break + F, sc=2 * half * 0.7); key(o, t_break + 1 + F, sc=2 * half)
        last = None
        for k, (p, a) in enumerate(track):
            moved = last is None or (p - last[0]).length > 1e-4 or (a - last[1]).length > 1e-3
            if moved or k == len(track) - 1:
                key(o, t_break + k + F, loc=p, rot=tuple(a))
            last = (p, a)
    puff(tag, c, t_break, rng, 4 if n_chunks >= 5 else 2, 3 if n_chunks >= 5 else 1, away)


BLOCK_MESH = {}


def block_obj(name, cells, ijk, m):
    if m.name not in BLOCK_MESH:
        me = bpy.data.meshes.new(f"PK block {m.name}")
        me.from_pydata([(x, y, z) for x in (-0.5, 0.5) for y in (-0.5, 0.5) for z in (-0.5, 0.5)], [], BOXF)
        me.materials.append(m); BLOCK_MESH[m.name] = me
    o = link(bpy.data.objects.new(name, BLOCK_MESH[m.name])); o.location = cells.centre(ijk)
    o["crack"] = 0.0
    cells.add(ijk)
    return o


# ------------------------------------------------------------------ twist: the leading point faces the strike
def twists_for(poses, roots, hits, side):
    """Per tick tool twist about its length: at each hit the head turns so its point leads the strike (side +1: the +X
    spike leads; 0: whichever point is nearer), held through the strike, eased between strikes in the recovery."""
    def phi_at(h, prev):
        a = tool_matrix(roots[h - 2], poses[h - 2], 0.0) @ Vector((0, 0.85, 0))
        b = tool_matrix(roots[h], poses[h], 0.0) @ Vector((0, 0.85, 0))
        m3 = tool_matrix(roots[h], poses[h], 0.0).to_3x3().inverted()
        vg = m3 @ (b - a)
        ph = math.atan2(-vg.z, vg.x)
        if side == 0:
            alt = ph + math.pi
            ph = min((ph, alt), key=lambda x: abs((x - prev + math.pi) % (2 * math.pi) - math.pi))
        return prev + ((ph - prev + math.pi) % (2 * math.pi) - math.pi)
    phis = []; prev = 0.0
    for h in hits:
        prev = phi_at(h, prev); phis.append(prev)
    n = len(poses); out = []
    for t in range(n):
        nxt = next((i for i, h in enumerate(hits) if h >= t), len(hits) - 1)
        prv = nxt - 1
        if prv < 0 or t >= hits[-1]:
            out.append(phis[nxt] if t < hits[-1] else phis[-1]); continue
        a, b = hits[prv] + 1, max(hits[prv] + 2, hits[nxt] - 3)
        w = smooth((t - a) / (b - a))
        out.append(phis[prv] + (phis[nxt] - phis[prv]) * w)
    return out


def lead_point(m_, lead, side):
    """The pick's point that leads the strike (the +X spike, or whichever is further forward for a two-pointed pick)."""
    a = m_ @ Vector((lead[0], lead[1], 0)); b = m_ @ Vector((-lead[0], lead[1], 0))
    return a if (side or a.y >= b.y) else b


def pose_at(keys, t):
    for (ta, *a), (tb, *b) in zip(keys, keys[1:]):
        if ta <= t <= tb:
            w = smooth((t - ta) / (tb - ta)) if tb > ta else 1
            return [x + (y - x) * w for x, y in zip(a, b)]
    return list(keys[-1][1:]) if t > keys[-1][0] else list(keys[0][1:])


REST = (96, 14, 0, 22, 0.0)
dump = {"format": "per take: per tick right-arm rotation (pitch, yaw, roll deg; pitch 90 = ahead), reach (m), tool tilt, tool twist (deg), player (eye) position; hits; per block: crack start, break tick. 20 ticks a second.",
        "takes": {}}
SPEC = []


def common_cams(code, root, side_loc, side_look, side_lens, clip=None):
    c = cam(f"Cam {code}", (0, 0, 0), (0, 3, -0.25), 10.4, parent=root)
    c.data.sensor_fit = "HORIZONTAL"; c.data.sensor_width = 36.0
    for nm_, a_, b_ in (("h", (-0.007, -0.0006, -0.2), (0.007, 0.0006, -0.2)), ("v", (-0.0006, -0.007, -0.2), (0.0006, 0.007, -0.2))):
        box(f"PK {code} crosshair {nm_}", a_, b_, XH, c)
    s = cam(f"Cam {code} side", side_loc, side_look, side_lens, parent=root)
    if clip:
        s.data.clip_start = clip
    return c, s


def label(code, text, side_cam, d=1.0):
    """Take label in the side camera's top-left corner (d m in front of it, past its clip start)."""
    cu = bpy.data.curves.new("PK label " + code, "FONT"); cu.body = text; cu.size = 0.026 * d; cu.align_x = "LEFT"
    k = 32.0 / side_cam.data.lens * d
    tl = link(bpy.data.objects.new("PK label " + code, cu)); tl.parent = side_cam; tl.location = (-0.5 * k, 0.26 * k, -d)
    tl.data.materials.append(LABEL)


def animate_rig(code, root, sh, grip, troot, legs, larm, roots, poses, phis, speeds):
    stride = 0.0
    for t, p in enumerate(poses):
        f = t + 1
        key(root, f, loc=tuple(roots[t]))
        sh.rotation_euler = arm_euler(p); sh.keyframe_insert("rotation_euler", frame=f)
        key(sh, f, loc=tuple(SHOULDER + Vector((0, p[4], 0))))
        key(grip, f, rot=(R(-p[3]), 0, 0))
        key(troot, f, rot=(0, phis[t], 0))
        stride += speeds[t] / 20
        amp = min(1.0, speeds[t] / 3.0)
        sw = math.sin(stride / 1.1 * math.pi) * R(38) * amp
        key(legs[0], f, rot=(sw, 0, 0)); key(legs[1], f, rot=(-sw, 0, 0))
        key(larm, f, rot=(-sw * 0.9 + R(-8) * amp, 0, R(-4)))


# ------------------------------------------------------------------ P takes: one design each, mining a block, step, the next
P_TAKES = {
    "P1a1": ("Faceted crescent pick: three quick taps, the third breaks", "crescent", 0,
             [(0, *REST), (2, 112, -4, 0, 10, 0), (4, 80, 2, 0, 72, 0.04), (6, 108, -4, 0, 14, 0), (8, 80, 2, 0, 72, 0.04),
              (10, 122, -5, 0, -2, -0.03), (13, 76, 2, 0, 78, 0.07), (14, 78, 2, 0, 74, 0.06), (18, *REST)],
             [4, 8, 13], "taps"),
    "P1a2": ("Laminated pick: forehand, backhand, the cracks creep between", "laminated", 1,
             [(0, *REST), (3, 128, 26, 28, -8, -0.03), (6, 76, -10, -16, 74, 0.05), (8, 88, -14, -10, 52, 0.02),
              (11, 128, -24, -26, -8, -0.03), (14, 76, 10, 16, 74, 0.06), (15, 78, 12, 18, 70, 0.05), (19, *REST)],
             [6, 14], "creep"),
    "P1a3": ("Shell-and-core pick: heavy strike, crack spreads, pry bursts it", "shell", 1,
             [(0, *REST), (5, 148, -6, 0, -40, -0.07), (7, 150, -6, 0, -44, -0.08), (10, 74, 3, 0, 80, 0.08),
              (12, 74, 3, 0, 80, 0.08), (15, 84, 3, 0, 54, 0.01), (16, 86, 3, 0, 50, 0.0), (20, *REST)],
             [10], "pry"),
}
# Readable in first person: a block hit straight below the shoulder hides under the fist, so every strike key swings the
# arm 14 deg in toward the crosshair and 4 deg up: the point lands left of the fist, in view.
for _v in P_TAKES.values():
    _v[3][:] = [k if tuple(k[1:]) == REST else (k[0], k[1] + 4, k[2] + 14, k[3], k[4], k[5]) for k in _v[3]]
BAY = 40.0
bi = 0
for code, (name, kind, side, keys, hits, mode) in P_TAKES.items():
    rng = np.random.default_rng(853 + bi)
    tag = f"PK {code} fp"; wtag = f"PK {code} world"
    bx = bi * BAY; bi += 1
    seq = keys[-1][0]
    STEP = 7                                               # step forward 1 m between the two blocks
    brk_off = {"taps": hits[-1] + 2, "creep": hits[-1] + 3, "pry": 16}[mode]
    c1 = FORM; c2 = FORM + seq + STEP                      # cycle starts (tick)
    total = c2 + seq + 18
    eye0 = Vector((bx, 0.0, EYE_H))
    roots = []; poses = []; speeds = []
    for t in range(total + 1):
        if t < c1:
            p = list(REST)
        elif t <= c1 + seq:
            p = pose_at(keys, t - c1)
        elif t < c2:
            p = list(REST)
        else:
            p = pose_at(keys, t - c2)
        poses.append(p)
        a = c1 + seq; w = smooth((t - a) / STEP) if t > a else 0.0
        bob = 0.025 * math.sin(w * math.pi)
        dip = 0.0
        for h in hits:
            for cs in (c1, c2):
                if t == cs + h + 1:
                    dip = -0.012
        roots.append(eye0 + Vector((0, w * 1.0, bob + dip)))
        speeds.append(0.0)
    for t in range(1, total + 1):
        speeds[t] = (roots[t].y - roots[t - 1].y) * 20
    hits_abs = [c1 + h for h in hits] + [c2 + h for h in hits]
    phis = twists_for(poses, roots, hits_abs, side)
    # the block: its near face meets the pick's leading point at the first hit
    _, lead = PICKS[kind]()
    h0 = hits_abs[0]
    lp = tool_matrix(roots[h0], poses[h0], phis[h0]) @ Vector((lead[0], lead[1], 0))
    lm = tool_matrix(roots[h0], poses[h0], phis[h0]) @ Vector((-lead[0], lead[1], 0))
    if side == 0 and lm.y > lp.y:
        lp = lm
    zb = max(0, int(math.floor(lp.z)))
    cells = Cells(lp.x - 0.5, lp.y - 0.06)
    objs = {}
    # a low ledge, 2 wide and 3 deep, one block high where the point bites (the near face), a step up at the back
    for i in (-1, 0):
        for j in (0, 1, 2):
            for k in range(0, zb + 1 + (1 if (j == 2 or i == -1 and j == 1) else 0)):
                m = DIRT if k == zb + 1 or (k == zb and i == -1) else STONE
                objs[(i, j, k)] = block_obj(f"{wtag} block {i} {j} {k}", cells, (i, j, k), m)
    box(f"{wtag} floor", (bx - 7, -6, -0.02), (bx + 5, 10, 0), FLOOR)
    box(f"{wtag} backdrop", (bx - 7.2, -8, 0), (bx - 7, 12, 7), WALL)
    blocks_info = []
    for n_, cs in enumerate((c1, c2)):
        ijk = (0, n_, zb); o = objs[ijk]
        tb = cs + brk_off
        hs = [cs + h for h in hits]
        if mode == "taps":                                 # each tap: the crack jumps a stage, held between taps
            steps_ = [(hs[0], 0.34), (hs[1] - 1, 0.34), (hs[1], 0.67), (hs[2] - 1, 0.67), (hs[2], 0.9), (tb - 1, 1.0)]
        elif mode == "creep":
            steps_ = [(hs[0], 0.4), (hs[0] + 3, 0.5), (hs[1] - 1, 0.62), (hs[1], 0.85), (tb - 1, 1.0)]
        else:
            steps_ = [(hs[0], 0.2), (hs[0] + 2, 0.5), (hs[0] + 4, 0.75), (hs[0] + 5, 0.9), (tb - 1, 1.0)]
        o_steps = steps_
        cells.brk[ijk] = tb
        away = Vector((0, -0.35, 0))
        break_block(wtag, cells, ijk, o, hs[0] - 1, tb, total + 1, rng, 6, away, crack_steps=o_steps)
        for h in hs:                                       # contact flecks at each strike
            cp = lead_point(tool_matrix(roots[h], poses[h], phis[h]), lead, side)
            puff(wtag, cp, h, rng, 2, 0, Vector((0, -0.5, 0.3)), life=4)
        blocks_info.append({"cell": list(ijk), "crack_from": hs[0], "break": tb})
    root = link(bpy.data.objects.new(f"PK {code} player", None))
    sh, grip, ring_pt = make_arm(tag, root)
    troot = link(bpy.data.objects.new(f"{tag} tool", None)); troot.parent = grip; troot.rotation_mode = "XYZ"
    parts, _, span = build_tool(tag, kind, troot)
    legs, larm = make_body(f"PK {code} body", root)
    animate_rig(code, root, sh, grip, troot, legs, larm, roots, poses, phis, speeds)
    # pixel stream from the ring (P1a's build), grip first
    pm = bpy.data.meshes.new(f"{tag} px"); s_ = 0.02
    pm.from_pydata([(x, y, z) for x in (-s_, s_) for y in (-s_, s_) for z in (-s_, s_)], [], BOXF); pm.materials.append(PIX)
    m_rest = grip_matrix(REST[3])
    for o, c in parts:
        f_arrive = 3 + int(round((c[1] / span) * (FORM - 5)))
        key(o, 1, sc=0.0001); key(o, f_arrive - 1, sc=0.0001); key(o, f_arrive + 1, sc=1.0)
        for j in range(3):
            px_ = link(bpy.data.objects.new(f"{tag} pixel", pm)); px_.parent = sh
            start = ring_pt + Vector(rng.uniform(-0.015, 0.015, 3))
            end = m_rest @ Vector(c + rng.uniform(-0.03, 0.03, 3))
            f0 = max(1, f_arrive - 4 + j - 1)
            key(px_, 1, loc=start, sc=0.0001); key(px_, f0, loc=start, sc=0.0001); key(px_, f0 + 1, loc=start, sc=1.0)
            key(px_, f0 + 3, loc=(start + end) / 2 + Vector((0, 0.03, -0.03)), sc=1.0)
            key(px_, f_arrive + 1, loc=end, sc=0.5); key(px_, f_arrive + 2, loc=end, sc=0.0001)
    fc, sc_ = common_cams(code, root, (3.6, 1.1, 0.0), (0.1, 1.15, -0.62), 32)
    label(code, f"{code}  {name}", sc_)
    model_at = c1 + brk_off + 2                           # chunks just thrown, the pick still in the follow-through
    dump["takes"][code] = {"name": name, "pick": PICK_NAME[kind], "hits": hits_abs, "blocks": blocks_info,
                           "ticks": [{"arm": [round(x, 2) for x in p[:3]], "tool_tilt": round(p[3], 2), "reach": round(p[4], 3),
                                      "tool_twist": round(math.degrees(phis[t]), 1),
                                      "eye": [round(x, 3) for x in roots[t]]} for t, p in enumerate(poses)]}
    SPEC.append((code, name, f"{PICK_NAME[kind]}; pixel stream build (frames 1-15); hits at frames {', '.join(str(h + 1) for h in hits_abs)}; "
                 f"blocks break at frames {blocks_info[0]['break'] + 1}, {blocks_info[1]['break'] + 1} into 6 physical chunks each",
                 total + 1, model_at + 1))
    print(code, "built", total, "ticks; lead point", tuple(round(x, 2) for x in lp - eye0), "block z", zb, flush=True)


# ------------------------------------------------------------------ R takes: running through a wall, dome craters of 8
def r_keys(style, n, T):
    keys = []; hits = []; orders = []
    RD = {"R1": (112, -4, 0, 8, 0.0), "R2": (108, 0, 0, 14, 0.0), "R3": (118, -16, -40, 20, 0.0)}[style]
    for k in range(n):
        s = k * T
        keys.append((s, *RD))
        if style == "R1":
            keys += [(s + 3, 136, -4, 0, -24, -0.05), (s + 5, 78, 2, 0, 74, 0.08), (s + 6, 74, 2, 0, 78, 0.07)]
            hits.append(s + 5); orders.append("centre")
        elif style == "R2":
            sg = 1 if k % 2 == 0 else -1
            keys += [(s + 2, 130, 30 * sg, 30 * sg, -10, -0.04), (s + 4, 74, -14 * sg, -20 * sg, 76, 0.07),
                     (s + 5, 78, -20 * sg, -22 * sg, 66, 0.05)]
            hits.append(s + 4); orders.append("l2r" if sg > 0 else "r2l")
        else:
            keys += [(s + 3, 142, -42, -40, -12, -0.05), (s + 6, 100, 0, -40, 66, 0.08), (s + 7, 80, 40, -40, 72, 0.05)]
            hits.append(s + 6); orders.append("arc")
    keys.append((n * T, *RD))
    return keys, hits, orders, RD


R_TAKES = {
    "R1": ("Running chops: overhead every 9 ticks, 8-block dome craters", "crescent", 0, 7, 9, 5, 8 / 7),
    "R2": ("Running figure-eight: alternating diagonals every 7 ticks", "laminated", 1, 9, 7, 4, 8 / 7),
    "R3": ("Running dome arcs: high right over to low left every 10 ticks", "shell", 1, 6, 10, 6, 8 / 7),
}
RUN = 16
for code, (name, kind, side, nsw, T, CR, STEP) in R_TAKES.items():
    rng = np.random.default_rng(853 + bi)
    tag = f"PK {code} fp"; wtag = f"PK {code} world"
    bx = bi * BAY; bi += 1
    keys, hits_rel, orders, RD = r_keys(code, nsw, T)
    start = RUN - 3
    total = start + nsw * T + 16
    poses = []
    for t in range(total + 1):
        poses.append(list(RD) if t < start else pose_at(keys, t - start) if t - start <= keys[-1][0] else list(RD))
    hits_abs = [start + h for h in hits_rel]
    # the wall: 4 wide (a solid column on the left, then the tunnel's 3), 3 high, deep enough for every swing; there is no
    # column right of the tunnel, so the side camera sees the tunnel's right-hand blocks crack and break open
    Y0 = 0.0; DEPTH = int(STEP * nsw) + 4
    cells = Cells(bx - 2.5, Y0)
    objs = {}
    for i in range(4):
        for j in range(DEPTH):
            for k in range(3):
                m = DIRT if (k == 2 or rng.random() < 0.12) else STONE
                objs[(i, j, k)] = block_obj(f"{wtag} block {i} {j} {k}", cells, (i, j, k), m)
    box(f"{wtag} floor", (bx - 8, -14, -0.02), (bx + 8, 16, 0), FLOOR)
    # strike pose relative to the eye (root): the leading point of the pick at each hit (twist from a still player)
    still = [Vector((bx, 0, EYE_H))] * (total + 1)
    phis0 = twists_for(poses, still, hits_abs, side)
    _, lead = PICKS[kind]()
    rel = []
    for h in hits_abs:
        m_ = tool_matrix(Vector((0, 0, 0)), poses[h], phis0[h])
        rel.append(lead_point(m_, lead, side))
    # the tunnel is a dome arch 7 blocks in section (3 wide, 2 high, a crown block that opens the roof down the middle);
    # each swing carves the next 8 standing blocks of it, front slice first and nearest the strike first, so a swing
    # takes a whole arch and bites into the next. Steady pace: 8/7 m per swing, the point always at the face.
    ARCH = [(1, 0), (2, 0), (3, 0), (1, 1), (2, 1), (3, 1), (2, 2)]
    selected = {}
    root_y_hit = []; crater_log = []
    queue = [(i, j, k) for j in range(DEPTH) for (i, k) in sorted(ARCH, key=lambda a: (abs(a[0] - 2) + abs(a[1] - 1)))]
    for n_, h in enumerate(hits_abs):
        ry = (cells.o.y - rel[0].y + 0.07) + n_ * STEP
        root_y_hit.append(ry)
        fy = ry + rel[n_].y - 0.07

        def dome(c):
            p = cells.centre(c)
            return ((p.x - bx) / 1.55) ** 2 + ((p.z - 1.05) / 1.45) ** 2 + ((p.y - (fy + 0.5)) / 0.95) ** 2
        pick8 = [c for c in queue if c not in selected][:8]
        o_ = orders[n_]
        if o_ == "centre":
            pick8.sort(key=dome)
        elif o_ == "l2r":
            pick8.sort(key=lambda c: (c[0], -c[2]))
        elif o_ == "r2l":
            pick8.sort(key=lambda c: (-c[0], -c[2]))
        else:
            pick8.sort(key=lambda c: (-c[0] - 0.6 * (c[2] - 2) * (1 if c[0] >= 2 else -1), c[1]))
        for r_, c in enumerate(pick8):
            dly = min(3, int(r_ * 3 / 7)) if code != "R2" else min(2, int(r_ * 2 / 7))
            selected[c] = (h + dly, h + dly + CR)
        crater_log.append({"hit": h, "cells": [list(c) for c in pick8]})
    # player path: sprint in, then the mining pace, keyed every tick (smoothed), with a running bob and hit dips
    ky = [(0, root_y_hit[0] - 6.5)] + list(zip(hits_abs, root_y_hit)) + [(total, root_y_hit[-1] + 1.2)]
    tt = np.arange(total + 1)
    ys = np.interp(tt, [k for k, _ in ky], [v for _, v in ky])
    ys = np.convolve(np.pad(ys, 3, mode="edge"), np.ones(7) / 7, mode="valid")
    roots = []; speeds = []
    stride = 0.0
    for t in range(total + 1):
        sp = (ys[min(total, t + 1)] - ys[max(0, t - 1)]) * 10
        stride += sp / 20
        bob = 0.03 * abs(math.sin(stride / 1.1 * math.pi)) * min(1.0, sp / 3)
        dip = -0.014 if (t - 1) in hits_abs else 0.0
        roots.append(Vector((bx, float(ys[t]), EYE_H + bob + dip))); speeds.append(max(0.0, sp))
    phis = twists_for(poses, roots, hits_abs, side)
    # break schedule: crack from (hit + delay) over CR ticks, then chunks; check the body never enters a standing block
    for c, (t0, t1) in selected.items():
        cells.brk[c] = t1
    for t in range(total + 1):
        for dz in (-1.5, -0.6, 0.2):
            p = roots[t] + Vector((0, 0.3, dz))
            if cells.solid(p, t) and p.z > 0:
                print("WARNING", code, "player inside a block at tick", t, tuple(round(x, 2) for x in p))
                break
    for c, (t0, t1) in sorted(selected.items(), key=lambda kv: kv[1][1]):
        o = objs[c]
        steps = [(t0, 0.25), (t0 + CR * 0.35, 0.5), (t0 + CR * 0.7, 0.78), (t1 - 1, 1.0)]
        # chunks spill out to the sides and down the face, not back into the eye camera
        sd = cells.centre(c) - Vector((bx, cells.centre(c).y, 1.0)); sd.z = 0
        away = Vector((0, 0.25, 0)) + (sd.normalized() * 0.5 if sd.length > 0.1 else Vector((0, 0, 0)))
        break_block(wtag, cells, c, o, t0, t1, total + 1, rng, 4, away, crack_steps=steps, pop=(0.6, 1.6))
    for h in hits_abs:
        cp = lead_point(tool_matrix(roots[h], poses[h], phis[h]), lead, side)
        puff(wtag, cp, h, rng, 2, 0, Vector((0, -0.5, 0.3)), life=4)
    root = link(bpy.data.objects.new(f"PK {code} player", None))
    sh, grip, ring_pt = make_arm(tag, root)
    troot = link(bpy.data.objects.new(f"{tag} tool", None)); troot.parent = grip; troot.rotation_mode = "XYZ"
    build_tool(tag, kind, troot)
    legs, larm = make_body(f"PK {code} body", root)
    animate_rig(code, root, sh, grip, troot, legs, larm, roots, poses, phis, speeds)
    # side camera: from the right, a little high, following the player
    fc, sc_ = common_cams(code, root, (5.4, 0.6, 0.6), (0.0, 1.0, -0.6), 24)
    label(code, f"{code}  {name}  ({PICK_NAME[kind]})", sc_)
    lamp = link(bpy.data.objects.new(f"PK {code} lamp", bpy.data.lights.new(f"PK {code} lamp", "POINT")))
    lamp.data.energy = 60; lamp.data.color = (1.0, 0.95, 0.85); lamp.data.shadow_soft_size = 0.6
    lamp.parent = root; lamp.location = (0.0, 0.2, 0.55)     # review light only (a held torch's worth), moves with the player
    mid = hits_abs[len(hits_abs) // 2]
    model_at = max(t1 for c, (t0, t1) in selected.items() if t0 >= mid and t0 <= mid + 3) + 1
    dump["takes"][code] = {"name": name, "pick": PICK_NAME[kind], "hits": hits_abs, "craters": crater_log,
                           "blocks": [{"cell": list(c), "crack_from": a, "break": b} for c, (a, b) in sorted(selected.items(), key=lambda kv: kv[1])],
                           "ticks": [{"arm": [round(x, 2) for x in p[:3]], "tool_tilt": round(p[3], 2), "reach": round(p[4], 3),
                                      "tool_twist": round(math.degrees(phis[t]), 1),
                                      "eye": [round(x, 3) for x in roots[t]]} for t, p in enumerate(poses)]}
    SPEC.append((code, name, f"{PICK_NAME[kind]}; runs in, {nsw} swings every {T} ticks, hits at frames "
                 f"{', '.join(str(h + 1) for h in hits_abs)}; each swing cracks 8 blocks ({len(selected)} in all), "
                 f"{CR} ticks of cracking before they break into 4 physical chunks each", total + 1, model_at + 1))
    print(code, "built", total, "ticks; blocks broken", len(selected), "; eye y at hits", [round(y, 2) for y in root_y_hit],
          "; craters", [len(c["cells"]) for c in crater_log], flush=True)

with open(os.path.join(FOLDER, "combat", "pickaxe_rework_poses.json"), "w") as fh:
    json.dump(dump, fh, separators=(",", ":"))
with open(os.path.join(FOLDER, "combat", "pickaxe_rework_takes.json"), "w") as fh:
    json.dump(SPEC, fh)

scene.frame_start, scene.frame_end = 1, max(s[3] for s in SPEC)
world = bpy.data.worlds.new("PK world"); world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.32, 0.42, 0.55, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.9
scene.world = world
sun = link(bpy.data.objects.new("PK sun", bpy.data.lights.new("PK sun", "SUN")))
sun.data.energy = 3.0; sun.rotation_euler = (R(28), R(-8), R(-35))
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
    tree = bpy.data.node_groups.new("PK Glow", "CompositorNodeTree")
    tree.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    rl = tree.nodes.new("CompositorNodeRLayers"); go = tree.nodes.new("NodeGroupOutput")
    gl = tree.nodes.new("CompositorNodeGlare")
    if "Type" in gl.inputs:
        gl.inputs["Type"].default_value = "Bloom"
    for nm_, val in (("Size", 0.5), ("Strength", 0.4), ("Threshold", 1.0)):
        if nm_ in gl.inputs:
            gl.inputs[nm_].default_value = val
    tree.links.new(rl.outputs["Image"], gl.inputs["Image"]); tree.links.new(gl.outputs["Image"], go.inputs[0])
    scene.compositing_node_group = tree
except Exception as e:
    print("no glow:", e)
scene.camera = bpy.data.objects["Cam P1a1"]
scene.frame_set(FORM + 6)
try:
    bpy.ops.outliner.orphans_purge(do_recursive=True)
except Exception:
    pass
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("saved", OUT)
