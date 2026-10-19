# Pass v2.0104: Ring models round 1: 12 wild worn-ring designs, smooth hero mesh + 1/4 px voxel twin (PC rings chat,
#   2026-10-19).
# Why: J: "new ring models refined as good of a model I can currently get in blender 12 variations (past ones have all
#   been weak)". Earlier rings were 1/4 px voxel boxes with a flat face (832 icon rings) or glow/animation tests on a
#   placeholder ring (856, 860-865): no real modelled detail, flat materials. J's picks: "Both per take" (smooth hero +
#   its voxel twin), lineup "Wilder", cameras hero close-up + turntable + first person on the fist.
# Every take: a subdivided band swept from a rounded cross-section (comfort fit, micro-bevelled edges), a modelled
#   setting, a refractive faceted gem/lens with an emissive flare core (G3 flare rules: spins one way, a little yellow in
#   the green), layered metal (base + polished edges + darker cavities from a baked curvature map + roughness noise +
#   engraving bump), emission <= 1.5 so the green stays saturated, original marks only (a lantern silhouette with a
#   diamond window; never the GL emblem). No black on rings (825).
# Units: 1 Blender unit = 1 Minecraft px in the ring sources; the first-person ring is the same model scaled to 1/16 m.
# Layout per take (bx = i * 60): hero bay y=0 (static 3/4 close-up, depth of field), turntable bay y=60 (hero left,
#   voxel twin right, both spin once over 1-120), first-person bay y=120 (120 deg eye camera, fist bent back 50, the
#   ring 1 px in from the back of the hand on the punching face, as the jar places it). Sources sit at z=-300.
# Cameras: "Cam <code> hero", "Cam <code> turntable", "Cam <code> - first person". Builds LanternLive\combat\ring_models.blend.
import math, os
import bpy, bmesh
import numpy as np
from mathutils import Matrix, Vector, Euler, noise as mnoise
from mathutils.bvhtree import BVHTree

R = math.radians
SCENE_NAME = "Ring Models"
OUT_REL = "combat/ring_models.blend"
OUT = os.path.join(FOLDER, *OUT_REL.split("/"))
os.makedirs(os.path.dirname(OUT), exist_ok=True)
old = bpy.data.scenes.get(SCENE_NAME)
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new(SCENE_NAME)
win = bpy.context.window
if win:
    win.scene = scene
FRAME_END = 120
scene.frame_start, scene.frame_end = 1, FRAME_END
scene.render.fps = 20
P = 1 / 16
PXF = P * 1.05                                  # first-person rig pixel (as 860)
GLOW = (0.02, 0.9, 0.12)                        # saturated corps green, never white
YEL = (0.75, 0.82, 0.04)
VOX = 0.25                                      # voxel twin: 1/4 px
RIN = 1.05                                      # band inner radius, px
_prefs = bpy.context.preferences.edit


def view_update():
    bpy.context.view_layer.update()


# ------------------------------------------------------------------ node helpers
def _out(n, ident=None):
    if ident:
        for s in n.outputs:
            if s.identifier == ident:
                return s
    return n.outputs[0]


def _set(nt, sock, v):
    if isinstance(v, bpy.types.NodeSocket):
        nt.links.new(v, sock)
    elif v is not None:
        try:
            sock.default_value = v
        except Exception:
            if isinstance(v, (int, float)):
                sock.default_value = (v, v, v, 1)


def inp(n, name):
    for s in n.inputs:
        if s.identifier == name or s.name == name:
            return s
    return None


def setin(nt, n, name, v):
    s = inp(n, name)
    if s is not None:
        _set(nt, s, v)


def math_(nt, op, a, b=0.0, clamp=False):
    n = nt.nodes.new("ShaderNodeMath"); n.operation = op; n.use_clamp = clamp
    _set(nt, n.inputs[0], a); _set(nt, n.inputs[1], b)
    return n.outputs[0]


def mrange(nt, v, a, b, c=0.0, d=1.0, smooth=True):
    n = nt.nodes.new("ShaderNodeMapRange")
    n.interpolation_type = "SMOOTHSTEP" if smooth else "LINEAR"
    _set(nt, n.inputs["Value"], v)
    n.inputs["From Min"].default_value = a; n.inputs["From Max"].default_value = b
    n.inputs["To Min"].default_value = c; n.inputs["To Max"].default_value = d
    return n.outputs["Result"]


def mixc(nt, fac, a, b, blend="MIX"):
    n = nt.nodes.new("ShaderNodeMix"); n.data_type = "RGBA"; n.blend_type = blend; n.clamp_result = True
    _set(nt, n.inputs[0], fac)
    for s in n.inputs:
        if s.identifier == "A_Color":
            _set(nt, s, a if isinstance(a, bpy.types.NodeSocket) else (*a, 1))
        if s.identifier == "B_Color":
            _set(nt, s, b if isinstance(b, bpy.types.NodeSocket) else (*b, 1))
    return _out(n, "Result_Color")


def new_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree
    return m, nt, nt.nodes["Principled BSDF"]


def texco(nt):
    return nt.nodes.new("ShaderNodeTexCoord").outputs["Object"]


def engrave(nt, kind, sc):
    """0..1 engraving mask (1 = cut line), procedural in object space so it sits on the metal."""
    co = texco(nt)
    if kind == "grooves":
        w = nt.nodes.new("ShaderNodeTexWave"); w.wave_type = "BANDS"; w.bands_direction = "X"
        _set(nt, w.inputs["Vector"], co); w.inputs["Scale"].default_value = sc
        return mrange(nt, w.outputs["Fac"], 0.86, 0.97)
    if kind == "rings":
        w = nt.nodes.new("ShaderNodeTexWave"); w.wave_type = "RINGS"; w.rings_direction = "SPHERICAL"
        _set(nt, w.inputs["Vector"], co); w.inputs["Scale"].default_value = sc
        return mrange(nt, w.outputs["Fac"], 0.88, 0.98)
    if kind in ("cells", "dots", "hammer"):
        v = nt.nodes.new("ShaderNodeTexVoronoi")
        v.feature = "DISTANCE_TO_EDGE" if kind == "cells" else "F1"
        _set(nt, v.inputs["Vector"], co); v.inputs["Scale"].default_value = sc
        if kind == "cells":
            return mrange(nt, v.outputs["Distance"], 0.05, 0.0)
        if kind == "dots":
            return mrange(nt, v.outputs["Distance"], 0.2, 0.13)
        return math_(nt, "MULTIPLY", v.outputs["Distance"], 0.35)
    if kind == "knurl":
        hs = []
        for ang in (45, -45):
            mp = nt.nodes.new("ShaderNodeMapping"); _set(nt, mp.inputs["Vector"], co)
            mp.inputs["Rotation"].default_value = (0, R(ang), 0)
            w = nt.nodes.new("ShaderNodeTexWave"); w.wave_type = "BANDS"; w.bands_direction = "X"
            _set(nt, w.inputs["Vector"], mp.outputs[0]); w.inputs["Scale"].default_value = sc
            hs.append(mrange(nt, w.outputs["Fac"], 0.8, 0.95))
        return math_(nt, "MAXIMUM", hs[0], hs[1])
    return 0.0


def metal(name, rgb, rough=0.2, eng=None, esc=6.0, patina=None, cracks=False, brushed=True):
    """Layered metal: base colour with noise, polished bright edges and dark rough cavities (from the baked 'curv'
    attribute), optional engraving (bump + darkened cut), optional patina in the cavities, optional glowing cracks."""
    m, nt, b = new_mat(name)
    b.inputs["Metallic"].default_value = 1.0
    at = nt.nodes.new("ShaderNodeAttribute"); at.attribute_name = "curv"
    cv = at.outputs["Fac"]
    edge = mrange(nt, cv, 0.53, 0.78)
    cav = mrange(nt, cv, 0.47, 0.28)
    nz = nt.nodes.new("ShaderNodeTexNoise"); _set(nt, nz.inputs["Vector"], texco(nt))
    nz.inputs["Scale"].default_value = 2.5; nz.inputs["Detail"].default_value = 8.0
    nzf = nz.outputs["Fac"]
    h = engrave(nt, eng, esc) if eng else 0.0
    base = mixc(nt, mrange(nt, nzf, 0.3, 0.7, 0.0, 1.0), tuple(c * 0.86 for c in rgb), tuple(min(1, c * 1.08) for c in rgb))
    bright = tuple(min(1.0, c * 1.3 + 0.06) for c in rgb)
    col = mixc(nt, math_(nt, "MULTIPLY", edge, 0.75), base, bright)
    dark = tuple(c * 0.22 for c in rgb)
    shade = math_(nt, "MAXIMUM", math_(nt, "MULTIPLY", cav, 0.8), math_(nt, "MULTIPLY", h, 0.85) if eng else 0.0)
    col = mixc(nt, shade, col, dark)
    if patina:
        pm = math_(nt, "MULTIPLY", cav, mrange(nt, nzf, 0.35, 0.65), clamp=True)
        col = mixc(nt, math_(nt, "MAXIMUM", pm, 0.0), col, patina)
        b.inputs["Metallic"].default_value = 0.85
    _set(nt, b.inputs["Base Color"], col)
    r_ = math_(nt, "ADD", rough, math_(nt, "MULTIPLY", math_(nt, "SUBTRACT", nzf, 0.5), 0.2))
    r_ = math_(nt, "ADD", r_, math_(nt, "MULTIPLY", cav, 0.3))
    r_ = math_(nt, "SUBTRACT", r_, math_(nt, "MULTIPLY", edge, 0.1), clamp=True)
    if eng:
        r_ = math_(nt, "ADD", r_, math_(nt, "MULTIPLY", h, 0.25), clamp=True)
    _set(nt, b.inputs["Roughness"], r_)
    # bump: fine brushed lines + noise + the engraving cut
    hgt = math_(nt, "MULTIPLY", nzf, 0.12)
    if brushed:
        w = nt.nodes.new("ShaderNodeTexWave"); w.wave_type = "BANDS"; w.bands_direction = "Z"
        _set(nt, w.inputs["Vector"], texco(nt)); w.inputs["Scale"].default_value = 40.0
        w.inputs["Distortion"].default_value = 6.0; w.inputs["Detail"].default_value = 3.0
        hgt = math_(nt, "ADD", hgt, math_(nt, "MULTIPLY", w.outputs["Fac"], 0.04))
    if eng:
        hgt = math_(nt, "SUBTRACT", hgt, h)
    bu = nt.nodes.new("ShaderNodeBump"); bu.inputs["Strength"].default_value = 0.45
    bu.inputs["Distance"].default_value = 0.02
    _set(nt, bu.inputs["Height"], hgt); _set(nt, b.inputs["Normal"], bu.outputs["Normal"])
    if cracks:
        vo = nt.nodes.new("ShaderNodeTexVoronoi"); vo.feature = "DISTANCE_TO_EDGE"
        _set(nt, vo.inputs["Vector"], texco(nt)); vo.inputs["Scale"].default_value = 3.2
        cm = math_(nt, "MULTIPLY", mrange(nt, vo.outputs["Distance"], 0.05, 0.0), mrange(nt, cv, 0.57, 0.42), clamp=True)
        setin(nt, b, "Emission Color", (*GLOW, 1))
        _set(nt, inp(b, "Emission Strength"), math_(nt, "MULTIPLY", cm, 1.4))
    m["vrgb"] = list(rgb); m["vk"] = "metal"
    return m


def enamel(name, rgb):
    m, nt, b = new_mat(name)
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = 0.4
    setin(nt, b, "Coat Weight", 1.0); setin(nt, b, "Coat Roughness", 0.03)
    m["vrgb"] = list(rgb); m["vk"] = "enamel"
    return m


def glass(name, rgb, ior=1.75, rough=0.0, film=420.0):
    """Gem glass: full transmission, raytraced refraction in EEVEE, thin film for a dispersion-like colour play."""
    m, nt, b = new_mat(name)
    b.inputs["Base Color"].default_value = (*rgb, 1)
    setin(nt, b, "Transmission Weight", 1.0)
    b.inputs["IOR"].default_value = ior
    b.inputs["Roughness"].default_value = rough
    setin(nt, b, "Thin Film Thickness", film); setin(nt, b, "Thin Film IOR", 1.45)
    setin(nt, b, "Dispersion", 0.6)
    for attr, val in (("surface_render_method", "DITHERED"), ("use_raytrace_refraction", True),
                      ("use_screen_refraction", True), ("thickness_mode", "SPHERE")):
        try:
            setattr(m, attr, val)
        except Exception:
            pass
    m["vrgb"] = list(rgb); m["vk"] = "glass"
    return m


def glow_mat(name, s=1.3, rgb=GLOW):
    m, nt, b = new_mat(name)
    b.inputs["Base Color"].default_value = (0.01, 0.12, 0.03, 1)
    setin(nt, b, "Emission Color", (*rgb, 1)); setin(nt, b, "Emission Strength", s)
    m["vrgb"] = list(rgb); m["vk"] = "glow"
    return m


def flare_mat(name, s=1.4):
    """The G3 flare recoloured small: green noise with the hottest bits burning yellow; spins with its object."""
    m, nt, b = new_mat(name)
    b.inputs["Base Color"].default_value = (0.01, 0.1, 0.03, 1)
    nz = nt.nodes.new("ShaderNodeTexNoise"); _set(nt, nz.inputs["Vector"], texco(nt))
    nz.inputs["Scale"].default_value = 3.0; nz.inputs["Detail"].default_value = 6.0
    hot = mrange(nt, nz.outputs["Fac"], 0.6, 0.78)
    setin(nt, b, "Emission Color", mixc(nt, math_(nt, "MULTIPLY", hot, 0.55), GLOW, YEL))
    _set(nt, inp(b, "Emission Strength"), math_(nt, "ADD", 0.9, math_(nt, "MULTIPLY", hot, 0.5)))
    m["vrgb"] = list(GLOW); m["vk"] = "glow"
    return m


def plain(name, rgb, rough=0.6, emit=0.0, erg=None):
    m, nt, b = new_mat(name)
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = rough
    if emit:
        setin(nt, b, "Emission Color", (*(erg or rgb), 1)); setin(nt, b, "Emission Strength", emit)
    return m


# ------------------------------------------------------------------ geometry helpers (all in ring px units)
def mk(name, bm, mats, coll, smooth=True):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for m in mats:
        me.materials.append(m)
    if smooth:
        me.shade_smooth()
    o = bpy.data.objects.new(name, me); coll.objects.link(o)
    return o


def band(name, mats, coll, rin=RIN, w=1.0, t=0.42, sq=3.2, nu=72, nv=16, f=None, arc=None, shift=0, th0=0.0,
         mat_fn=None, cap_mat=0, disp=None):
    """Sweep a superellipse cross-section (width along X, the ring axis; thickness radial) round the X axis.
    th = 0 is the top (+Z, where the setting sits). f(th) -> (width scale, thickness scale, radial lift, twist, x shift).
    The inner surface never goes inside rin. arc=(a0, a1) makes an open band with end caps."""
    bm = bmesh.new()
    closed = arc is None
    rows = []
    for i in range(nu if closed else nu + 1):
        th = (th0 + 2 * math.pi * i / nu) if closed else (arc[0] + (arc[1] - arc[0]) * i / nu)
        ws, ts, dr, tw, dx = f(th) if f else (1, 1, 0, 0, 0)
        prof = []
        for j in range(nv):
            a = 2 * math.pi * j / nv
            ca, sa = math.cos(a), math.sin(a)
            px = math.copysign(abs(ca) ** (2 / sq), ca) * w * ws / 2
            py = math.copysign(abs(sa) ** (2 / sq), sa) * t * ts / 2
            prof.append((px * math.cos(tw) - py * math.sin(tw), px * math.sin(tw) + py * math.cos(tw)))
        lo = min(p[1] for p in prof)
        row = []
        for (px, py) in prof:
            r = rin + dr + (py - lo)
            v = Vector((px + dx, r * math.sin(th), r * math.cos(th)))
            if disp:
                v = disp(v, th)
            row.append(bm.verts.new(v))
        rows.append(row)
    n_r = len(rows)
    for i in range(n_r if closed else n_r - 1):
        i2 = (i + 1) % n_r
        sh = shift if (closed and i2 == 0) else 0
        for j in range(nv):
            j2 = (j + 1) % nv
            fc = bm.faces.new((rows[i][j], rows[i][j2], rows[i2][(j2 + sh) % nv], rows[i2][(j + sh) % nv]))
            fc.material_index = mat_fn(j) if mat_fn else 0
    if not closed:
        for row in (rows[0], rows[-1]):
            fc = bm.faces.new(row); fc.material_index = cap_mat
    return mk(name, bm, mats, coll)


def lathe(name, prof, mats, coll, n=48, wob=None, mat_fn=None, loop=False):
    """Revolve a (r, z) profile round Z (bottom to top; r=0 points become poles). wob(theta) scales the radius
    (hexagons, squares, scallops)."""
    bm = bmesh.new()
    rings = []
    for (r, z) in prof:
        if r < 1e-6:
            rings.append(bm.verts.new((0, 0, z)))
        else:
            rr = []
            for k in range(n):
                a = 2 * math.pi * k / n
                s = wob(a) if wob else 1.0
                rr.append(bm.verts.new((r * s * math.cos(a), r * s * math.sin(a), z)))
            rings.append(rr)
    if loop:
        rings.append(rings[0])
    for i in range(len(rings) - 1):
        A, B = rings[i], rings[i + 1]
        mi = mat_fn(i) if mat_fn else 0
        if isinstance(A, list) and isinstance(B, list):
            for k in range(n):
                fc = bm.faces.new((A[k], A[(k + 1) % n], B[(k + 1) % n], B[k])); fc.material_index = mi
        elif isinstance(A, list):
            for k in range(n):
                fc = bm.faces.new((A[k], A[(k + 1) % n], B)); fc.material_index = mi
        elif isinstance(B, list):
            for k in range(n):
                fc = bm.faces.new((A, B[(k + 1) % n], B[k])); fc.material_index = mi
    return mk(name, bm, mats, coll)


def spline(ctrl, n=24):
    """Catmull-Rom through control points -> n+1 smooth points."""
    c = [Vector(p) for p in ctrl]
    c = [c[0] + (c[0] - c[1])] + c + [c[-1] + (c[-1] - c[-2])]
    out = []
    segs = len(c) - 3
    for k in range(n + 1):
        u = k / n * segs
        i = min(int(u), segs - 1); t = u - i
        p0, p1, p2, p3 = c[i], c[i + 1], c[i + 2], c[i + 3]
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    return out


def tube(name, pts, radii, mats, coll, n=10, closed=False, cap=True):
    """Sweep a circle along points with parallel-transport frames; radii per point (taper to a point with ~0)."""
    pts = [Vector(p) for p in pts]
    if not hasattr(radii, "__len__"):
        radii = [radii] * len(pts)
    m = len(pts)
    T = []
    for i in range(m):
        a = pts[(i - 1) % m] if (closed or i > 0) else pts[i]
        b = pts[(i + 1) % m] if (closed or i < m - 1) else pts[i]
        T.append((b - a).normalized())
    N = T[0].orthogonal().normalized()
    bm = bmesh.new()
    rings = []
    for i in range(m):
        N = (N - T[i] * N.dot(T[i])).normalized()
        B = T[i].cross(N)
        r = max(radii[i], 0.004)
        rings.append([bm.verts.new(pts[i] + r * (math.cos(2 * math.pi * k / n) * N + math.sin(2 * math.pi * k / n) * B)) for k in range(n)])
    for i in range(m if closed else m - 1):
        A, Bq = rings[i], rings[(i + 1) % m]
        for k in range(n):
            bm.faces.new((A[k], A[(k + 1) % n], Bq[(k + 1) % n], Bq[k]))
    if not closed and cap:
        for idx, sgn in ((0, -1), (m - 1, 1)):
            pole = bm.verts.new(pts[idx] + T[idx] * sgn * radii[idx] * 0.6)
            ring = rings[idx]
            for k in range(n):
                bm.faces.new((ring[k], ring[(k + 1) % n], pole) if sgn > 0 else (ring[(k + 1) % n], ring[k], pole))
    return mk(name, bm, mats, coll)


def hull(name, pts, mats, coll):
    bm = bmesh.new()
    for p in pts:
        bm.verts.new(p)
    res = bmesh.ops.convex_hull(bm, input=bm.verts[:])
    junk = [g for g in res["geom_interior"] + res["geom_unused"] if isinstance(g, bmesh.types.BMVert)]
    if junk:
        bmesh.ops.delete(bm, geom=junk, context="VERTS")
    return mk(name, bm, mats, coll, smooth=False)


def brilliant(name, r, mats, coll, n=8, table=0.56, crown=0.34, pav=0.82):
    pts = []
    for k in range(n):
        a = 2 * math.pi * (k + 0.5) / n
        pts.append((table * r * math.cos(a), table * r * math.sin(a), crown * r))
        b = 2 * math.pi * k / n
        pts.append((0.84 * r * math.cos(b), 0.84 * r * math.sin(b), crown * r * 0.5))
        pts.append((0.55 * r * math.cos(a), 0.55 * r * math.sin(a), -pav * r * 0.5))
    for k in range(2 * n):
        a = 2 * math.pi * k / (2 * n)
        pts.append((r * math.cos(a), r * math.sin(a), 0.025 * r)); pts.append((r * math.cos(a), r * math.sin(a), -0.025 * r))
    pts.append((0, 0, -pav * r))
    return hull(name, pts, mats, coll)


def shard(name, length, rad, mats, coll, rng, sides=6, tipoff=0.0):
    pts = []
    for k in range(sides):
        a = 2 * math.pi * k / sides + rng.uniform(-0.12, 0.12)
        rr = rad * rng.uniform(0.85, 1.15)
        pts.append((rr * math.cos(a), rr * math.sin(a), -0.25 * rad))
        pts.append((0.92 * rr * math.cos(a), 0.92 * rr * math.sin(a), length * rng.uniform(0.62, 0.74)))
    pts.append((tipoff * rad, 0, length))
    return hull(name, pts, mats, coll)


def emerald_cut(name, w, l, h, mats, coll):
    pts = []
    def rect(sx, sy, z, ch=0.28):
        cx, cy = sx / 2, sy / 2
        c = ch * min(sx, sy) / 2
        for (x, y) in ((cx - c, cy), (cx, cy - c), (cx, -cy + c), (cx - c, -cy), (-cx + c, -cy), (-cx, -cy + c), (-cx, cy - c), (-cx + c, cy)):
            pts.append((x, y, z))
    rect(0.66 * w, 0.72 * l, 0.36 * h); rect(0.86 * w, 0.88 * l, 0.22 * h); rect(w, l, 0.02 * h); rect(w, l, -0.02 * h)
    rect(0.7 * w, 0.76 * l, -0.32 * h); rect(0.36 * w, 0.5 * l, -0.58 * h)
    pts += [(0, 0.18 * l, -0.66 * h), (0, -0.18 * l, -0.66 * h)]
    return hull(name, pts, mats, coll)


def ball(name, r, mats, coll, seg=16, smooth=True):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg * 2, v_segments=seg, radius=r)
    return mk(name, bm, mats, coll, smooth)


def core(name, r, mats, coll, seed=0, amp=0.25):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=3, radius=r)
    for v in bm.verts:
        d = v.co.normalized()
        v.co = d * r * (1 + amp * mnoise.noise(d * 2.2 + Vector((seed, seed * 0.7, 0))))
    return mk(name, bm, mats, coll)


MARK_HALF = [(0, -0.5), (0.32, -0.5), (0.32, -0.42), (0.2, -0.37), (0.3, -0.12), (0.3, 0.17), (0.2, 0.3), (0.3, 0.35),
             (0.3, 0.41), (0.12, 0.45), (0.07, 0.5), (0, 0.5)]
MARK_HOLE = [(0, -0.26), (0.085, 0.03), (0, 0.24), (-0.085, 0.03)]


def mark(name, size, depth, mats, coll):
    """Original lantern mark: a lantern silhouette (base, body, cap, finial) with a diamond window, extruded."""
    outer = MARK_HALF[:-1] + [(-x, y) for (x, y) in reversed(MARK_HALF[1:])]
    outer = [p for k, p in enumerate(outer) if k == 0 or p != outer[k - 1]]
    bm = bmesh.new()
    edges = []
    for loop in (outer, MARK_HOLE):
        vs = [bm.verts.new((x * size, y * size, 0)) for (x, y) in loop]
        edges += [bm.edges.new((vs[k], vs[(k + 1) % len(vs)])) for k in range(len(vs))]
    bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=edges)
    ex = bmesh.ops.extrude_face_region(bm, geom=bm.faces[:])
    bmesh.ops.translate(bm, verts=[g for g in ex["geom"] if isinstance(g, bmesh.types.BMVert)], vec=(0, 0, depth))
    bmesh.ops.translate(bm, verts=bm.verts[:], vec=(0, 0, -depth * 0.55))
    return mk(name, bm, mats, coll, smooth=False)


def orient(o, loc, normal, up):
    z = Vector(normal).normalized(); y = (Vector(up) - z * Vector(up).dot(z)).normalized(); x = y.cross(z)
    o.matrix_world = Matrix.Translation(loc) @ Matrix((x, y, z)).transposed().to_4x4()


def empty(name, coll, loc=(0, 0, 0), parent=None):
    e = bpy.data.objects.new(name, None); coll.objects.link(e); e.empty_display_size = 0.3
    e.location = loc
    if parent:
        e.parent = parent
    return e


def spin_keys(o, axis, turns, f0=1, f1=FRAME_END + 1, base=(0, 0, 0)):
    """Constant one-way spin (linear keys, so it loops)."""
    _prefs.keyframe_new_interpolation_type = "LINEAR"
    ax = "XYZ".index(axis)
    for f, u in ((f0, 0.0), (f1, 1.0)):
        rot = list(base); rot[ax] += 2 * math.pi * turns * u
        o.rotation_euler = rot; o.keyframe_insert("rotation_euler", frame=f)
    _prefs.keyframe_new_interpolation_type = "BEZIER"


def bob_keys(o, amp, base_z, period=60):
    _prefs.keyframe_new_interpolation_type = "BEZIER"
    for f in range(1, FRAME_END + 2, period // 2):
        o.location.z = base_z + amp * (1 if (f // (period // 2)) % 2 else -1)
        o.keyframe_insert("location", index=2, frame=f)


def bumpf(th, p=6):
    return max(0.0, math.cos(th)) ** p


def flank_marks(tag, coll, root, mats, w_top, t_top, size=None, rin=RIN):
    """Inlaid marks on both band flanks at the top shoulder: the +X flank faces the back of the hand in first person."""
    s = size or t_top * 0.82
    for sgn in (1, -1):
        m_ = mark(f"{tag} mark {'+' if sgn > 0 else '-'}", s, 0.07, mats, coll)
        orient(m_, Vector((sgn * w_top / 2, 0, rin + t_top / 2)), (sgn, 0, 0), (0, 0, 1))
        m_.parent = root


# ------------------------------------------------------------------ bake: subdivision applied + curvature attribute
def finish(o, sub=2):
    if sub:
        md = o.modifiers.new("Subdivision", "SUBSURF"); md.levels = sub; md.render_levels = sub
        md.quality = 3


def curvature(me):
    n = len(me.vertices)
    if n == 0 or len(me.edges) == 0:
        return
    co = np.empty(n * 3); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    nr = np.empty(n * 3); me.vertices.foreach_get("normal", nr); nr = nr.reshape(-1, 3)
    ed = np.empty(len(me.edges) * 2, dtype=np.int64); me.edges.foreach_get("vertices", ed); ed = ed.reshape(-1, 2)
    acc = np.zeros(n); cnt = np.zeros(n)
    for a, b in ((0, 1), (1, 0)):
        d = co[ed[:, b]] - co[ed[:, a]]
        L = np.linalg.norm(d, axis=1) + 1e-9
        c = -np.einsum("ij,ij->i", d, nr[ed[:, a]]) / L        # >0: the neighbour falls away = convex edge
        np.add.at(acc, ed[:, a], c); np.add.at(cnt, ed[:, a], 1)
    cv = acc / np.maximum(cnt, 1)
    for _ in range(2):                                           # blur twice so edges read as soft bands
        s = np.zeros(n); k = np.zeros(n)
        np.add.at(s, ed[:, 0], cv[ed[:, 1]]); np.add.at(s, ed[:, 1], cv[ed[:, 0]])
        np.add.at(k, ed[:, 0], 1); np.add.at(k, ed[:, 1], 1)
        cv = 0.5 * cv + 0.5 * s / np.maximum(k, 1)
    cv = np.clip(0.5 + cv * 3.0, 0, 1)
    at = me.color_attributes.get("curv") or me.color_attributes.new("curv", "FLOAT_COLOR", "POINT")
    cols = np.ones((n, 4)); cols[:, 0] = cols[:, 1] = cols[:, 2] = cv
    at.data.foreach_set("color", cols.ravel())


def bake(o):
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(o.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
    old_me = o.data
    o.modifiers.clear(); o.data = me
    if old_me.users == 0:
        bpy.data.meshes.remove(old_me)
    curvature(me)


# ------------------------------------------------------------------ voxel twin
def voxelize(name, root, parts, coll):
    """Voxel twin at 1/4 px: a cell is solid if its centre is inside a part (ray parity) or within 0.45 voxel of its
    surface (so thin prongs and hoops survive). Kind/colour from the nearest face's material; glow > glass > metal.
    Faces shaded like J's pixel metal: lit tops, mid sides, dark undersides, a little per-voxel jitter."""
    inv = root.matrix_world.inverted()
    pri = {"glow": 3, "glass": 2, "enamel": 1, "metal": 0}
    cells = {}
    for o in parts:
        if o.type != "MESH" or len(o.data.polygons) == 0:
            continue
        mw = inv @ o.matrix_world
        vs = [mw @ v.co for v in o.data.vertices]
        polys = [tuple(p.vertices) for p in o.data.polygons]
        mats = [o.data.materials[p.material_index] if o.data.materials else None for p in o.data.polygons]
        bvh = BVHTree.FromPolygons(vs, polys)
        lo = np.min(np.array(vs), axis=0); hi = np.max(np.array(vs), axis=0)
        i0 = np.floor(lo / VOX).astype(int) - 1; i1 = np.ceil(hi / VOX).astype(int) + 1
        dirv = Vector((1, 0.0013, 0.0007)).normalized()
        for ix in range(i0[0], i1[0]):
            for iy in range(i0[1], i1[1]):
                for iz in range(i0[2], i1[2]):
                    c = Vector(((ix + 0.5) * VOX, (iy + 0.5) * VOX, (iz + 0.5) * VOX))
                    near = bvh.find_nearest(c, VOX * 0.45)
                    solid = near[0] is not None
                    fidx = near[2] if solid else None
                    if not solid:
                        hits, org = 0, c.copy()
                        for _ in range(16):
                            loc, nrm, idx, dist = bvh.ray_cast(org, dirv)
                            if loc is None:
                                break
                            hits += 1; org = loc + dirv * 1e-4
                        solid = hits % 2 == 1
                        if solid:
                            fidx = bvh.find_nearest(c)[2]
                    if not solid:
                        continue
                    m = mats[fidx] if fidx is not None else None
                    if m is None or "vk" not in m:
                        continue
                    k = (ix, iy, iz)
                    if k not in cells or pri[m["vk"]] > pri[cells[k]["vk"]]:
                        cells[k] = m
    # one material per (kind, colour)
    vm = {}
    bm = bmesh.new()
    tone = []
    fmat = []
    rng = np.random.default_rng(len(cells))
    dirs = [((1, 0, 0), 1.06), ((-1, 0, 0), 0.9), ((0, 1, 0), 0.96), ((0, -1, 0), 1.0), ((0, 0, 1), 1.28), ((0, 0, -1), 0.55)]
    for k, m in cells.items():
        key = (m["vk"], tuple(round(c, 3) for c in m["vrgb"]))
        if key not in vm:
            vm[key] = len(vm)
        jit = float(rng.uniform(0.92, 1.08))
        for (d, sh) in dirs:
            nb = (k[0] + d[0], k[1] + d[1], k[2] + d[2])
            if nb in cells and cells[nb]["vk"] == m["vk"]:
                continue
            c = Vector(((k[0] + 0.5) * VOX, (k[1] + 0.5) * VOX, (k[2] + 0.5) * VOX))
            n = Vector(d); ax = [i for i in range(3) if d[i] == 0]
            a = Vector([1.0 if i == ax[0] else 0.0 for i in range(3)]); b = Vector([1.0 if i == ax[1] else 0.0 for i in range(3)])
            h = VOX / 2
            q = [bm.verts.new(c + n * h + (sa * a + sb * b) * h) for (sa, sb) in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
            fc = bm.faces.new(q)
            fc.normal_update()
            if fc.normal.dot(n) < 0:
                fc.normal_flip()
            fc.material_index = vm[key]
            tone.append(sh * jit)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    at = me.color_attributes.new("tone", "FLOAT_COLOR", "CORNER")
    cols = np.repeat(np.array(tone), 4)
    arr = np.ones((len(cols), 4)); arr[:, 0] = arr[:, 1] = arr[:, 2] = cols
    at.data.foreach_set("color", arr.ravel())
    for (kind, rgb), idx in sorted(vm.items(), key=lambda kv: kv[1]):
        me.materials.append(vox_mat(kind, rgb))
    o = bpy.data.objects.new(name, me); coll.objects.link(o)
    return o, len(cells)


_VOXM = {}


def vox_mat(kind, rgb):
    key = (kind, rgb)
    if key in _VOXM:
        return _VOXM[key]
    m, nt, b = new_mat(f"RM vox {kind} {rgb}")
    at = nt.nodes.new("ShaderNodeAttribute"); at.attribute_name = "tone"
    col = mixc(nt, 1.0, rgb, at.outputs["Color"], blend="MULTIPLY")
    _set(nt, b.inputs["Base Color"], col)
    if kind == "metal":
        b.inputs["Metallic"].default_value = 0.7; b.inputs["Roughness"].default_value = 0.32
    elif kind == "glass":
        b.inputs["Roughness"].default_value = 0.08; b.inputs["Alpha"].default_value = 0.82
        setin(nt, b, "Emission Color", (*rgb, 1)); setin(nt, b, "Emission Strength", 0.35)
        try:
            m.surface_render_method = "DITHERED"
        except Exception:
            pass
    elif kind == "glow":
        setin(nt, b, "Emission Color", (*GLOW, 1)); setin(nt, b, "Emission Strength", 1.25)
    else:
        b.inputs["Roughness"].default_value = 0.3
    _VOXM[key] = m
    return m


# ------------------------------------------------------------------ palettes
GOLD = (0.95, 0.62, 0.2)
SILVER = (0.86, 0.87, 0.88)
STEEL = (0.55, 0.58, 0.6)
GUN = (0.3, 0.32, 0.34)
IRON = (0.34, 0.32, 0.3)
BRONZE = (0.62, 0.36, 0.15)
JADE_STEEL = (0.26, 0.38, 0.31)
G_EMER = (0.08, 0.75, 0.25)
G_BRIGHT = (0.25, 0.95, 0.4)
G_LIME = (0.55, 0.95, 0.2)
G_DEEP = (0.03, 0.45, 0.16)
JADE_ENAMEL = (0.02, 0.24, 0.08)


# ------------------------------------------------------------------ the twelve takes
def setting_core(tag, coll, root, loc, r, seed, scale=(1, 1, 1)):
    c = core(f"{tag} core", r * 1.35, [flare_mat(f"{tag} flare")], coll, seed)
    c.location = loc; c.scale = scale; c.parent = root
    spin_keys(c, "Z", 1.0)
    return c


def W1(tag, coll, root, rng):
    """Orrery: a gold collet gem inside two precessing silver hoops, each carrying a small moon gem."""
    gold = metal(f"{tag} gold", GOLD, 0.16, "grooves", 7.0)
    gold2 = metal(f"{tag} gold polished", GOLD, 0.1)
    silv = metal(f"{tag} silver", SILVER, 0.08)
    gl = glass(f"{tag} gem", G_EMER, 1.78)
    parts = []
    f = lambda th: (1 + 0.35 * bumpf(th), 1 + 0.65 * bumpf(th), 0, 0, 0)
    parts.append(band(f"{tag} band", [gold], coll, w=1.0, t=0.42, f=f))
    parts.append(lathe(f"{tag} collet", [(0, 1.3), (0.6, 1.3), (0.74, 1.52), (0.8, 1.8), (0.75, 1.9), (0.66, 1.88),
                                         (0.58, 1.66), (0.0, 1.5)], [gold2], coll))
    for k in range(4):
        a = R(45 + 90 * k)
        parts.append(tube(f"{tag} prong {k}", spline([(0.74 * math.cos(a), 0.74 * math.sin(a), 1.78),
                                                      (0.79 * math.cos(a), 0.79 * math.sin(a), 1.98),
                                                      (0.62 * math.cos(a), 0.62 * math.sin(a), 2.12)], 8),
                          [0.085] * 6 + [0.07, 0.06, 0.06], [gold2], coll, n=8))
    g = brilliant(f"{tag} gem", 0.74, [gl], coll); g.location = (0, 0, 1.96); parts.append(g)
    parts.append(setting_core(tag, coll, root, (0, 0, 1.86), 0.21, 1))
    for h, (tilt, dirn) in enumerate(((R(32), 1), (R(-38), -1))):
        piv = empty(f"{tag} hoop pivot {h}", coll, (0, 0, 2.02), root)
        spin_keys(piv, "Z", 0.5 * dirn, base=(0, 0, R(60 * h)))
        tip = empty(f"{tag} hoop tilt {h}", coll, (0, 0, 0), piv); tip.rotation_euler = (tilt, 0, 0)
        ring_pts = [(1.1 * math.cos(2 * math.pi * k / 48), 1.1 * math.sin(2 * math.pi * k / 48), 0) for k in range(48)]
        hp = tube(f"{tag} hoop {h}", ring_pts, 0.055, [silv], coll, n=8, closed=True); hp.parent = tip
        moon = ball(f"{tag} moon {h}", 0.13, [gl], coll, 8); moon.location = (1.1 * math.cos(R(110 * h + 40)), 1.1 * math.sin(R(110 * h + 40)), 0)
        moon.parent = tip
        parts += [hp, moon]
    flank_marks(tag, coll, root, [glow_mat(f"{tag} mark", 1.2)], 1.35, 0.42 * 1.65)
    return parts


def W2(tag, coll, root, rng):
    """Shard burst: a knife-edge steel band; a cracked jade-steel seat with seven crystal shards erupting off-centre."""
    steel = metal(f"{tag} steel", STEEL, 0.12)
    seat_m = metal(f"{tag} seat", JADE_STEEL, 0.3, "cells", 4.5)
    gms = [glass(f"{tag} shard emerald", G_EMER, 1.7), glass(f"{tag} shard bright", G_BRIGHT, 1.6),
           glass(f"{tag} shard lime", G_LIME, 1.65)]
    parts = []
    f = lambda th: (1 + 0.2 * bumpf(th), 1 + 0.7 * bumpf(th, 4), 0, 0.18 * math.sin(3 * th), 0.06 * math.sin(2 * th))
    parts.append(band(f"{tag} band", [steel], coll, w=0.9, t=0.5, sq=1.55, f=f, nu=80))
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.78)
    for v in bm.verts:
        v.co *= 1 + 0.22 * mnoise.noise(v.co * 2.0 + Vector((3, 1, 0)))
        v.co.z *= 0.55
    seat = mk(f"{tag} seat", bm, [seat_m], coll); seat.location = (0.08, 0.05, 1.62); parts.append(seat)
    big = shard(f"{tag} shard main", 2.3, 0.36, [gms[0]], coll, rng); big.location = (0.0, 0.0, 1.55)
    big.rotation_euler = (R(9), R(-12), 0); parts.append(big)
    parts.append(setting_core(tag, coll, root, (0.12, -0.12, 2.25), 0.2, 2, (0.8, 0.8, 2.6)))
    parts[-1].rotation_euler = (R(9), R(-12), 0)
    for k in range(6):
        az = R(k * 60 + rng.uniform(-20, 20)); el = R(rng.uniform(28, 62))
        L = rng.uniform(0.75, 1.75); rad = rng.uniform(0.11, 0.24)
        s = shard(f"{tag} shard {k}", L, rad, [gms[k % 3]], coll, rng, sides=int(rng.choice([5, 6, 7])))
        d = Vector((math.sin(el) * math.cos(az), math.sin(el) * math.sin(az), math.cos(el)))
        s.location = Vector((0.05, 0.03, 1.66)) + d * 0.35
        s.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
        parts.append(s)
    return parts


def W3(tag, coll, root, rng):
    """Talon clasp: three scaled gunmetal talons with gold tips curl up from the band and grip a glass orb."""
    gun = metal(f"{tag} gunmetal", GUN, 0.22, "cells", 9.0)
    gold = metal(f"{tag} gold", GOLD, 0.12)
    gl = glass(f"{tag} orb", G_EMER, 1.5, film=300)
    parts = []
    f = lambda th: (1 + 0.15 * bumpf(th), 1 + 0.5 * bumpf(th), 0, 0, 0)
    parts.append(band(f"{tag} band", [gun], coll, w=1.05, t=0.46, sq=2.6, f=f))
    orb = ball(f"{tag} orb", 0.8, [gl], coll, 24); orb.location = (0, 0, 2.3); parts.append(orb)
    parts.append(setting_core(tag, coll, root, (0, 0, 2.3), 0.3, 3))
    parts.append(lathe(f"{tag} cradle", [(0.0, 1.5), (0.55, 1.5), (0.7, 1.6), (0.66, 1.72), (0.5, 1.68), (0.0, 1.62)], [gold], coll))
    for k in range(3):
        a = R(90 + 120 * k)
        ca, sa = math.cos(a), math.sin(a)
        ctrl = [(0.5 * ca, 0.5 * sa, 1.5), (0.95 * ca, 0.95 * sa, 1.85), (1.02 * ca, 1.02 * sa, 2.35),
                (0.72 * ca + 0.15 * -sa, 0.72 * sa + 0.15 * ca, 2.95), (0.3 * ca + 0.25 * -sa, 0.3 * sa + 0.25 * ca, 3.12)]
        pts = spline(ctrl, 28)
        rad = [0.2 * (1 - i / 28) ** 0.8 + 0.012 for i in range(29)]
        parts.append(tube(f"{tag} talon {k}", pts, rad, [gun], coll, n=10))
        parts.append(tube(f"{tag} tip {k}", pts[20:], [r * 1.12 for r in rad[20:]], [gold], coll, n=10))
    return parts


def W4(tag, coll, root, rng):
    """Reliquary: a hexagonal gold shrine on the band (jade enamel frieze, six pillars, glass chamber with the flare,
    domed roof with pinnacles), dotted gold band with inlaid lantern marks (matches lantern KEEPs R2a/R4a/R4b)."""
    gold = metal(f"{tag} gold", GOLD, 0.14)
    gold_d = metal(f"{tag} gold dotted", GOLD, 0.18, "dots", 10.0)
    en = enamel(f"{tag} enamel", JADE_ENAMEL)
    gl = glass(f"{tag} chamber", G_BRIGHT, 1.5, film=350)
    hexw = lambda a: math.cos(math.pi / 6) / math.cos(((a + math.pi / 6) % (math.pi / 3)) - math.pi / 6)
    parts = []
    f = lambda th: (1 + 0.45 * bumpf(th, 4), 1 + 0.7 * bumpf(th, 4), 0, 0, 0)
    parts.append(band(f"{tag} band", [gold_d], coll, w=1.0, t=0.44, f=f))
    parts.append(lathe(f"{tag} base", [(0, 1.35), (1.0, 1.35), (1.04, 1.42), (1.0, 1.62), (0.9, 1.66), (0.86, 1.74), (0, 1.74)],
                       [gold], coll, n=60, wob=hexw))
    parts.append(lathe(f"{tag} frieze", [(0, 1.44), (1.04, 1.44), (1.06, 1.47), (1.06, 1.57), (1.04, 1.6), (0, 1.6)],
                       [en], coll, n=60, wob=hexw))
    parts.append(lathe(f"{tag} chamber", [(0, 1.72), (0.52, 1.72), (0.6, 1.95), (0.6, 2.38), (0.52, 2.6), (0, 2.6)], [gl], coll))
    parts.append(setting_core(tag, coll, root, (0, 0, 2.16), 0.27, 4))
    for k in range(6):
        a = R(60 * k)
        p0 = Vector((0.74 * math.cos(a), 0.74 * math.sin(a), 1.72))
        parts.append(tube(f"{tag} pillar {k}", [p0, p0 + Vector((0, 0, 0.45)), p0 + Vector((0, 0, 0.9))], 0.075, [gold], coll, n=8))
        cap = ball(f"{tag} capital {k}", 0.11, [gold], coll, 8); cap.location = p0 + Vector((0, 0, 0.92)); parts.append(cap)
        pin = lathe(f"{tag} pinnacle {k}", [(0, 0), (0.08, 0), (0.05, 0.12), (0.02, 0.3), (0, 0.34)], [gold], coll, n=12)
        pin.location = p0 + Vector((0, 0, 0.98)); parts.append(pin)
    parts.append(tube(f"{tag} crown", [(0.74 * hexw(2 * math.pi * k / 60) * math.cos(2 * math.pi * k / 60),
                                       0.74 * hexw(2 * math.pi * k / 60) * math.sin(2 * math.pi * k / 60), 2.62) for k in range(60)],
                      0.08, [gold], coll, n=8, closed=True))
    parts.append(lathe(f"{tag} roof", [(0, 2.6), (0.7, 2.6), (0.72, 2.66), (0.55, 2.82), (0.3, 2.96), (0.12, 3.05),
                                       (0.09, 3.2), (0.0, 3.24)], [gold], coll, n=60, wob=hexw))
    fin = ball(f"{tag} finial", 0.12, [gl], coll, 10); fin.location = (0, 0, 3.32); parts.append(fin)
    flank_marks(tag, coll, root, [glow_mat(f"{tag} mark", 1.2)], 1.45, 0.44 * 1.7)
    return parts


def W5(tag, coll, root, rng):
    """Forged meteor: a lumpy hammered iron band with glowing green cracks in its dents and raw crystals bursting out."""
    iron = metal(f"{tag} iron", IRON, 0.38, "hammer", 5.0, cracks=True, brushed=False)
    gms = [glass(f"{tag} crystal", G_BRIGHT, 1.6), glass(f"{tag} crystal lime", G_LIME, 1.6)]
    parts = []
    def f(th):
        n1 = mnoise.noise(Vector((math.cos(th) * 1.3, math.sin(th) * 1.3, 0.5)))
        return (1.1 + 0.25 * n1 + 0.2 * bumpf(th), 1.15 + 0.35 * n1 + 0.6 * bumpf(th, 3), 0.04 * n1, 0.1 * n1, 0.08 * n1)
    def disp(v, th):
        return v + v.normalized() * 0.07 * mnoise.noise(v * 2.6 + Vector((7, 2, 1)))
    parts.append(band(f"{tag} band", [iron], coll, w=1.1, t=0.5, sq=2.2, nu=96, nv=20, f=f, disp=disp))
    for k, (az, el, L, rad) in enumerate(((R(20), R(14), 1.5, 0.3), (R(150), R(40), 1.0, 0.22), (R(260), R(55), 0.8, 0.18))):
        s = shard(f"{tag} crystal {k}", L, rad, [gms[k % 2]], coll, rng, sides=6, tipoff=0.3)
        d = Vector((math.sin(el) * math.cos(az), math.sin(el) * math.sin(az), math.cos(el)))
        s.location = Vector((0.1 * (k - 1), 0.0, 1.45)) + d * 0.1
        s.rotation_euler = d.to_track_quat("Z", "Y").to_euler(); parts.append(s)
    parts.append(setting_core(tag, coll, root, Vector((0.0, 0.0, 1.45)) + Vector((math.sin(R(14)) * math.cos(R(20)), math.sin(R(14)) * math.sin(R(20)), math.cos(R(14)))) * 0.7,
                              0.16, 5, (0.8, 0.8, 1.8)))
    parts[-1].rotation_euler = Vector((math.sin(R(14)) * math.cos(R(20)), math.sin(R(14)) * math.sin(R(20)), math.cos(R(14)))).to_track_quat("Z", "Y").to_euler()
    return parts


def W6(tag, coll, root, rng):
    """Aperture eye: a knurled gunmetal housing with nine silver iris blades that slowly open and close over a glowing
    pupil lens; wide flat silver band with inlaid marks."""
    silv = metal(f"{tag} silver", SILVER, 0.1)
    gun = metal(f"{tag} housing", GUN, 0.25, "knurl", 30.0)
    ring_m = metal(f"{tag} bezel", SILVER, 0.12, "rings", 9.0)
    blade_m = metal(f"{tag} blade", STEEL, 0.14)
    en = enamel(f"{tag} backing", JADE_ENAMEL)
    gl = glass(f"{tag} pupil", G_BRIGHT, 1.5)
    parts = []
    f = lambda th: (1 + 0.2 * bumpf(th), 1 + 0.6 * bumpf(th, 4), 0, 0, 0)
    parts.append(band(f"{tag} band", [silv], coll, w=1.25, t=0.36, sq=5.0, f=f))
    parts.append(lathe(f"{tag} housing", [(0, 1.3), (1.0, 1.3), (1.1, 1.38), (1.12, 1.72), (1.04, 1.82), (0.9, 1.82), (0.88, 1.76), (0, 1.76)], [gun], coll, n=64))
    parts.append(lathe(f"{tag} bezel ring", [(0.84, 1.8), (1.04, 1.8), (1.06, 1.86), (1.0, 1.94), (0.86, 1.94), (0.82, 1.88)], [ring_m], coll, n=64, loop=True))
    parts.append(lathe(f"{tag} backing", [(0, 1.75), (0.88, 1.75), (0.88, 1.82), (0, 1.82)], [en], coll, n=48))
    pup = lathe(f"{tag} pupil", [(0, 1.8)] + [(0.34 * math.cos(R(a)), 1.8 + 0.3 * math.sin(R(a))) for a in range(0, 91, 10)], [gl], coll, n=40)
    parts.append(pup)
    parts.append(setting_core(tag, coll, root, (0, 0, 1.86), 0.15, 6))
    for k in range(9):
        a0 = 2 * math.pi * k / 9
        piv = empty(f"{tag} blade pivot {k}", coll, (0.79 * math.cos(a0), 0.79 * math.sin(a0), 1.86 + 0.006 * k), root)
        piv.rotation_euler = (R(4), 0, a0)
        _prefs.keyframe_new_interpolation_type = "BEZIER"
        for fr, ang in ((1, 0), (30, R(16)), (60, R(4)), (90, R(18)), (121, 0)):
            piv.rotation_euler = (R(4), 0, a0 + ang); piv.keyframe_insert("rotation_euler", index=2, frame=fr)
        # blade: a curved leaf from the pivot sweeping in toward the centre
        cl = spline([(0, 0, 0), (-0.23, 0.23, 0), (-0.56, 0.29, 0), (-0.76, 0.1, 0)], 14)
        bm = bmesh.new(); top = []; bot = []
        for i, c in enumerate(cl):
            t = i / 14
            wdt = 0.06 + 0.17 * math.sin(math.pi * min(1, t * 1.15)) ** 0.7
            nxt = cl[min(i + 1, 14)] - cl[max(i - 1, 0)]
            side = Vector((-nxt.y, nxt.x, 0)).normalized()
            for zz, lst in ((0.022, top), (-0.022, bot)):
                lst.append((bm.verts.new(c + side * wdt + Vector((0, 0, zz))), bm.verts.new(c - side * wdt + Vector((0, 0, zz)))))
        for i in range(14):
            for lst, flip in ((top, False), (bot, True)):
                q = (lst[i][0], lst[i + 1][0], lst[i + 1][1], lst[i][1])
                bm.faces.new(q[::-1] if flip else q)
            bm.faces.new((top[i][0], bot[i][0], bot[i + 1][0], top[i + 1][0]))
            bm.faces.new((top[i][1], top[i + 1][1], bot[i + 1][1], bot[i][1]))
        for e in (0, 14):
            bm.faces.new((top[e][0], top[e][1], bot[e][1], bot[e][0]))
        bl = mk(f"{tag} blade {k}", bm, [blade_m], coll); bl.parent = piv; parts.append(bl)
    flank_marks(tag, coll, root, [glow_mat(f"{tag} mark", 1.2)], 1.25 * 1.2, 0.36 * 1.6)
    return parts


def W7(tag, coll, root, rng):
    """Mobius: a flat two-tone ribbon (gold face / silver face) with a half twist, standing on edge at the top where an
    emerald-cut gem is clawed into the twist."""
    gold = metal(f"{tag} gold", GOLD, 0.12)
    silv = metal(f"{tag} silver", SILVER, 0.1, "grooves", 9.0)
    gl = glass(f"{tag} gem", G_EMER, 1.62)
    parts = []
    f = lambda th: (1.0, 1.0, 0, ((th - math.pi) % (2 * math.pi)) / 2, 0)
    parts.append(band(f"{tag} ribbon", [gold, silv], coll, w=1.4, t=0.32, sq=4.5, nu=96, nv=16, f=f, th0=math.pi, shift=8,
                      mat_fn=lambda j: 0 if j < 8 else 1))
    top = RIN + 1.4 + 0.05
    g = emerald_cut(f"{tag} gem", 0.95, 1.3, 0.9, [gl], coll); g.location = (0, 0, top + 0.42); parts.append(g)
    parts.append(setting_core(tag, coll, root, (0, 0, top + 0.36), 0.2, 7, (1, 1.3, 0.8)))
    for k, (sx, sy) in enumerate(((1, 1), (1, -1), (-1, 1), (-1, -1))):
        parts.append(tube(f"{tag} claw {k}", spline([(sx * 0.12, sy * 0.25, top - 0.25), (sx * 0.42, sy * 0.58, top + 0.3),
                                                     (sx * 0.4, sy * 0.6, top + 0.55), (sx * 0.3, sy * 0.48, top + 0.66)], 10),
                          [0.09] * 8 + [0.075, 0.06, 0.05], [gold], coll, n=8))
    return parts


def W8(tag, coll, root, rng):
    """Broken halo: the band snapped open at the top, its ends glowing; a brilliant floats in the gap, bobbing and
    turning, three chips orbit it and two thin light arcs tie it to the ends."""
    silv = metal(f"{tag} silver", (0.9, 0.92, 0.95), 0.07)
    gl = glass(f"{tag} gem", G_EMER, 1.85, film=480)
    chip = glass(f"{tag} chip", G_LIME, 1.7)
    gm = glow_mat(f"{tag} end glow", 1.35)
    arcm = glow_mat(f"{tag} arc", 1.1)
    parts = []
    def f(th):
        e = max(0.0, 1 - min(abs(abs(th) - R(30)), R(40)) / R(40))
        return (1 + 0.35 * e, 1 + 0.55 * e, 0, 0, 0)
    parts.append(band(f"{tag} half a", [silv, gm], coll, w=1.0, t=0.48, sq=3.0, nu=40, arc=(R(30), R(176)), f=f, cap_mat=1))
    parts.append(band(f"{tag} half b", [silv, gm], coll, w=1.0, t=0.48, sq=3.0, nu=40, arc=(R(-176), R(-30)), f=f, cap_mat=1))
    holder = empty(f"{tag} float", coll, (0, 0, 2.05), root)
    bob_keys(holder, 0.08, 2.05)
    spinner = empty(f"{tag} float spin", coll, (0, 0, 0), holder); spin_keys(spinner, "Z", 0.5)
    g = brilliant(f"{tag} gem", 0.7, [gl], coll); g.parent = spinner; parts.append(g)
    c = core(f"{tag} core", 0.2, [flare_mat(f"{tag} flare")], coll, 8); c.parent = spinner; c.location = (0, 0, -0.08)
    parts.append(c)
    orb = empty(f"{tag} chips", coll, (0, 0, 0), holder); orb.rotation_euler = (R(18), 0, 0)
    oz = empty(f"{tag} chips spin", coll, (0, 0, 0), orb); spin_keys(oz, "Z", -1.0)
    for k in range(3):
        a = R(120 * k)
        b_ = brilliant(f"{tag} chip {k}", 0.13, [chip], coll, n=6); b_.parent = oz
        b_.location = (1.0 * math.cos(a), 1.0 * math.sin(a), 0.05 * k); parts.append(b_)
    for sgn in (1, -1):
        r0 = RIN + 0.48 * 1.55
        a0 = Vector((0, sgn * r0 * math.sin(R(30)), r0 * math.cos(R(30))))
        mid = Vector((0.12 * sgn, sgn * 0.75, 1.95))
        pts = spline([a0, mid, Vector((0, sgn * 0.5, 2.05))], 16)
        pts = [p + Vector((0.04 * mnoise.noise(p * 5 + Vector((sgn, 0, 0))), 0, 0.04 * mnoise.noise(p * 5 + Vector((0, sgn, 1))))) for p in pts]
        parts.append(tube(f"{tag} arc {sgn}", pts, 0.028, [arcm], coll, n=6))
    return parts


def W9(tag, coll, root, rng):
    """Lantern crown: a miniature gold-and-glass lantern stands on the band (stepped base, ribbed glass body with the
    flare inside, domed cap, carry handle); engraved gold band with inlaid lantern marks."""
    gold = metal(f"{tag} gold", GOLD, 0.13)
    gold_e = metal(f"{tag} gold engraved", GOLD, 0.16, "grooves", 8.0)
    gl = glass(f"{tag} glass", G_EMER, 1.5, film=360)
    parts = []
    f = lambda th: (1 + 0.4 * bumpf(th, 4), 1 + 0.65 * bumpf(th, 4), 0, 0, 0)
    parts.append(band(f"{tag} band", [gold_e], coll, w=1.0, t=0.44, f=f))
    parts.append(lathe(f"{tag} base", [(0, 1.42), (0.78, 1.42), (0.84, 1.5), (0.8, 1.56), (0.64, 1.6), (0.68, 1.68), (0.62, 1.72), (0, 1.72)], [gold], coll))
    parts.append(lathe(f"{tag} body", [(0, 1.7), (0.48, 1.7), (0.58, 1.95), (0.58, 2.35), (0.48, 2.6), (0, 2.6)], [gl], coll))
    parts.append(setting_core(tag, coll, root, (0, 0, 2.15), 0.24, 9))
    for k in range(6):
        a = R(60 * k + 30)
        ca, sa = math.cos(a), math.sin(a)
        parts.append(tube(f"{tag} rib {k}", spline([(0.5 * ca, 0.5 * sa, 1.7), (0.61 * ca, 0.61 * sa, 1.95), (0.61 * ca, 0.61 * sa, 2.35), (0.5 * ca, 0.5 * sa, 2.6)], 14),
                          0.045, [gold], coll, n=8))
    parts.append(tube(f"{tag} girdle", [(0.6 * math.cos(2 * math.pi * k / 40), 0.6 * math.sin(2 * math.pi * k / 40), 2.15) for k in range(40)], 0.045, [gold], coll, n=8, closed=True))
    parts.append(lathe(f"{tag} cap", [(0, 2.57), (0.58, 2.57), (0.62, 2.64), (0.46, 2.77), (0.24, 2.87), (0.1, 2.9), (0.0, 2.92)], [gold], coll))
    parts.append(tube(f"{tag} handle", [(0.3 * math.cos(R(a)), 0, 2.86 + 0.3 * math.sin(R(a))) for a in range(0, 181, 10)], 0.045, [gold], coll, n=8))
    flank_marks(tag, coll, root, [glow_mat(f"{tag} mark", 1.2)], 1.4, 0.44 * 1.65)
    return parts


def W10(tag, coll, root, rng):
    """Thorn vine: three braided bronze strands with a green patina and thorns, two leaves cradling a glass seed pod."""
    br = metal(f"{tag} bronze", BRONZE, 0.3, patina=(0.12, 0.42, 0.3))
    leaf_m = metal(f"{tag} leaf", (0.5, 0.42, 0.18), 0.28, "cells", 6.0, patina=(0.1, 0.4, 0.22))
    gl = glass(f"{tag} pod", G_BRIGHT, 1.45, film=300)
    parts = []
    rc = RIN + 0.27
    for s in range(3):
        pts = []
        for i in range(120):
            th = 2 * math.pi * i / 120
            ph = 5 * th + 2 * math.pi * s / 3
            rr = rc + 0.16 * math.cos(ph)
            pts.append(Vector((0.2 * math.sin(ph), rr * math.sin(th), rr * math.cos(th))))
        parts.append(tube(f"{tag} strand {s}", pts, 0.13, [br], coll, n=8, closed=True))
        for t in range(9):
            i = (t * 13 + s * 5) % 120
            p = pts[i]
            out = Vector((rng.uniform(-0.6, 0.6), p.y, p.z)).normalized()
            th_ = lathe(f"{tag} thorn {s}.{t}", [(0, 0), (0.07, 0), (0.035, 0.12), (0, 0.27)], [br], coll, n=8)
            orient(th_, p + out * 0.08, out, Vector((1, 0, 0)) if abs(out.x) < 0.9 else Vector((0, 0, 1)))
            parts.append(th_)
    for sgn in (1, -1):
        bm = bmesh.new(); rows = []
        for i in range(13):
            t = i / 12
            wd = 0.36 * math.sin(math.pi * t) ** 0.8 + 0.01
            y = 1.15 * t; z = 0.35 * t * t
            rows.append([bm.verts.new((u * wd, y, z - 0.06 * (u * u) + 0.03)) for u in (-1, -0.5, 0, 0.5, 1)])
        for i in range(12):
            for j in range(4):
                bm.faces.new((rows[i][j], rows[i][j + 1], rows[i + 1][j + 1], rows[i + 1][j]))
        lf = mk(f"{tag} leaf {sgn}", bm, [leaf_m], coll)
        sol = lf.modifiers.new("Solidify", "SOLIDIFY"); sol.thickness = 0.05; sol.offset = 0
        lf.location = (0, 0.1 * sgn, 1.5); lf.rotation_euler = (R(-15), 0, R(90 if sgn > 0 else -90)); parts.append(lf)
    pod = ball(f"{tag} pod", 0.5, [gl], coll, 20); pod.location = (0, 0, 2.05); pod.scale = (0.85, 0.85, 1.3); parts.append(pod)
    parts.append(setting_core(tag, coll, root, (0, 0, 2.05), 0.2, 10, (1, 1, 1.5)))
    for k in range(3):
        a = R(120 * k + 20)
        parts.append(tube(f"{tag} sepal {k}", spline([(0.1 * math.cos(a), 0.1 * math.sin(a), 1.45), (0.46 * math.cos(a), 0.46 * math.sin(a), 1.75),
                                                      (0.42 * math.cos(a), 0.42 * math.sin(a), 2.2)], 10),
                          [0.09, 0.1, 0.1, 0.09, 0.08, 0.07, 0.06, 0.05, 0.04, 0.03, 0.01], [leaf_m], coll, n=8))
    return parts


def W11(tag, coll, root, rng):
    """Knuckle plate: a curved gunmetal armour plate on a gold under-plate across the knuckles, riveted, with a square
    gold window (the square emblem ring, R19f) holding a glowing inlaid lantern mark under flat glass."""
    gun = metal(f"{tag} gunmetal", (0.36, 0.38, 0.4), 0.2, "grooves", 5.0)
    gold = metal(f"{tag} gold", GOLD, 0.13)
    gl = glass(f"{tag} window", G_EMER, 1.5, film=0)
    en = enamel(f"{tag} window floor", JADE_ENAMEL)
    parts = []
    parts.append(band(f"{tag} band", [gun], coll, w=1.0, t=0.42, sq=3.4))
    parts.append(band(f"{tag} underplate", [gold], coll, rin=RIN + 0.36, w=2.6, t=0.18, sq=6.0, nu=36, arc=(R(-62), R(62))))
    parts.append(band(f"{tag} plate", [gun], coll, rin=RIN + 0.5, w=2.3, t=0.26, sq=6.0, nu=36, arc=(R(-54), R(54)),
                      f=lambda th: (1 - 0.15 * (1 - math.cos(th)), 1 + 0.4 * bumpf(th, 2), 0, 0, 0)))
    sqw = lambda a: 1.0 / max(abs(math.cos(a)), abs(math.sin(a))) ** 0.92
    zb = RIN + 0.5 + 0.26 * 1.4
    parts.append(lathe(f"{tag} frame", [(0, zb - 0.1), (0.62, zb - 0.1), (0.68, zb + 0.02), (0.62, zb + 0.14), (0.52, zb + 0.14),
                                        (0.5, zb + 0.06), (0, zb + 0.06)], [gold], coll, n=64, wob=sqw))
    parts.append(lathe(f"{tag} floor", [(0, zb + 0.04), (0.5, zb + 0.04), (0.5, zb + 0.06), (0, zb + 0.06)], [en], coll, n=64, wob=sqw))
    mk_ = mark(f"{tag} mark", 0.72, 0.06, [glow_mat(f"{tag} mark", 1.3)], coll); mk_.location = (0, 0, zb + 0.07); parts.append(mk_)
    parts.append(lathe(f"{tag} glass", [(0, zb + 0.08), (0.5, zb + 0.08), (0.5, zb + 0.13), (0.44, zb + 0.16), (0, zb + 0.16)], [gl], coll, n=64, wob=sqw))
    for k, (x, th) in enumerate(((0.95, 40), (-0.95, 40), (0.95, -40), (-0.95, -40), (0.0, 48), (0.0, -48))):
        rr = RIN + 0.5 + 0.28
        rv = ball(f"{tag} rivet {k}", 0.09, [gold], coll, 8); rv.location = (x, rr * math.sin(R(th)), rr * math.cos(R(th))); parts.append(rv)
    return parts


def W12(tag, coll, root, rng):
    """Spire: a stepped ziggurat band; a tall hexagonal crystal spire leans off-centre out of a gold claw collar, a
    small brilliant rides the opposite shoulder."""
    silv = metal(f"{tag} silver", SILVER, 0.1, "grooves", 6.0)
    gold = metal(f"{tag} gold", GOLD, 0.12)
    gl = glass(f"{tag} spire", G_EMER, 1.7, film=380)
    gl2 = glass(f"{tag} satellite", G_LIME, 1.9)
    parts = []
    def f(th):
        a = abs(((th + math.pi) % (2 * math.pi)) - math.pi)
        s1 = 1 / (1 + math.exp((a - R(70)) * 14)); s2 = 1 / (1 + math.exp((a - R(38)) * 14))
        return (1 + 0.25 * s1 + 0.2 * s2, 1 + 0.5 * s1 + 0.5 * s2, 0, 0, 0)
    parts.append(band(f"{tag} band", [silv], coll, w=1.0, t=0.4, sq=4.0, nu=96, f=f))
    tilt = (0, R(18), 0)
    base = Vector((0.15, 0, 1.62))
    sp = shard(f"{tag} spire", 2.35, 0.33, [gl], coll, rng, sides=6); sp.location = base; sp.rotation_euler = tilt; parts.append(sp)
    c = setting_core(tag, coll, root, base + Euler(tilt).to_matrix() @ Vector((0, 0, 0.9)), 0.15, 12, (0.8, 0.8, 3.0))
    c.rotation_euler = tilt; parts.append(c)
    col_ = lathe(f"{tag} collar", [(0.0, -0.05), (0.45, -0.05), (0.5, 0.05), (0.44, 0.22), (0.38, 0.26), (0.36, 0.12), (0.0, 0.1)], [gold], coll)
    col_.location = base; col_.rotation_euler = tilt; parts.append(col_)
    M = Matrix.Translation(base) @ Euler(tilt).to_matrix().to_4x4()
    for k in range(3):
        a = R(120 * k + 30)
        pts = [M @ Vector((0.42 * math.cos(a), 0.42 * math.sin(a), 0.2)), M @ Vector((0.4 * math.cos(a), 0.4 * math.sin(a), 0.5)),
               M @ Vector((0.3 * math.cos(a), 0.3 * math.sin(a), 0.72))]
        parts.append(tube(f"{tag} claw {k}", spline(pts, 8), [0.08] * 6 + [0.06, 0.045, 0.03], [gold], coll, n=8))
    r_s = RIN + 0.4 * 1.75
    sat_loc = Vector((0, -r_s * math.sin(R(55)), r_s * math.cos(R(55))))
    out = sat_loc.normalized()
    cl = lathe(f"{tag} sat collet", [(0, -0.12), (0.26, -0.12), (0.3, 0.04), (0.26, 0.08), (0, 0.02)], [gold], coll, n=32)
    orient(cl, sat_loc + out * 0.05, out, (1, 0, 0)); parts.append(cl)
    sg = brilliant(f"{tag} satellite", 0.3, [gl2], coll); orient(sg, sat_loc + out * 0.16, out, (1, 0, 0)); parts.append(sg)
    flank_marks(tag, coll, root, [glow_mat(f"{tag} mark", 1.2)], 1.45, 0.4 * 2.0, size=0.55)
    return parts


TAKES = [
    ("W1", "Orrery", W1, "gold collet gem inside two precessing silver hoops with moon gems; grooved gold band, inlaid marks"),
    ("W2", "Shard burst", W2, "knife-edge steel band, cracked jade-steel seat, seven crystal shards erupting off-centre"),
    ("W3", "Talon clasp", W3, "three scaled gunmetal talons with gold tips grip a glass orb with the flare inside"),
    ("W4", "Reliquary shrine", W4, "hex gold shrine: jade enamel frieze, six pillars, glass chamber, domed roof, pinnacles"),
    ("W5", "Forged meteor", W5, "lumpy hammered iron band, green glowing cracks in the dents, raw crystals bursting out"),
    ("W6", "Aperture eye", W6, "knurled housing, nine iris blades opening and closing over a glowing pupil lens"),
    ("W7", "Mobius ribbon", W7, "two-tone gold/silver ribbon with a half twist; emerald-cut gem clawed into the twist"),
    ("W8", "Broken halo", W8, "band snapped open, glowing ends; a floating brilliant bobs in the gap with orbiting chips"),
    ("W9", "Lantern crown", W9, "a miniature gold-and-glass lantern stands on the band, flare inside; inlaid marks"),
    ("W10", "Thorn vine", W10, "three braided patinated bronze strands with thorns; leaves cradle a glass seed pod"),
    ("W11", "Knuckle plate", W11, "curved riveted gunmetal plate on gold, square window with a glowing lantern mark"),
    ("W12", "Spire", W12, "stepped ziggurat band, tall hex crystal spire leaning off-centre, satellite gem on a shoulder"),
]
ONLY = [t.strip() for t in os.environ.get("RM_ONLY", "").split(",") if t.strip()]
if ONLY:
    TAKES = [t for t in TAKES if t[0] in ONLY]


# ------------------------------------------------------------------ stage pieces
def link_new(coll, name, data):
    o = bpy.data.objects.new(name, data); coll.objects.link(o)
    return o


def look_at(o, target):
    d = Vector(target) - o.location
    o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def camera(coll, name, loc, target, lens):
    c = link_new(coll, name, bpy.data.cameras.new(name))
    c.location = loc; look_at(c, target); c.data.lens = lens; c.data.clip_start = 0.02; c.data.sensor_width = 36
    return c


CYC = plain("RM cyc", (0.035, 0.045, 0.042), 0.55)
SOFT = plain("RM softbox", (0, 0, 0), 1.0, emit=6.0, erg=(1.0, 0.97, 0.92))
SOFT_G = plain("RM softbox green", (0, 0, 0), 1.0, emit=2.0, erg=(0.4, 1.0, 0.55))
SKIN = plain("RM skin", (0.62, 0.42, 0.31), 0.7)
SHIRT = plain("RM shirt", (0.05, 0.3, 0.14), 0.8)
SKY = plain("RM sky", (0, 0, 0), 1.0, emit=1.0, erg=(0.32, 0.48, 0.78))
GRASS = plain("RM grass", (0.17, 0.3, 0.1), 0.95)
XH = plain("RM crosshair", (1, 1, 1), 0.5, emit=1.0, erg=(1, 1, 1))


def box_mesh(name, a, b, m, coll):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector([a[i] + (b[i] - a[i]) * (v.co[i] + 0.5) for i in range(3)])
    return mk(name, bm, [m], coll, smooth=False)


def cyc(name, coll, center, floor_z=-2.4):
    bm = bmesh.new(); rows = []
    prof = [(-24, floor_z), (4, floor_z)] + [(4 + 5 * math.sin(R(a)), floor_z + 5 - 5 * math.cos(R(a))) for a in range(10, 91, 10)] + [(9, 16)]
    for (y, z) in prof:
        rows.append([bm.verts.new((center[0] + x, center[1] + y, center[2] + z)) for x in (-30, 30)])
    for i in range(len(rows) - 1):
        bm.faces.new((rows[i][0], rows[i][1], rows[i + 1][1], rows[i + 1][0]))
    return mk(name, bm, [CYC], coll)


def area(coll, name, loc, target, energy, size, rgb=(1, 0.97, 0.93)):
    l = link_new(coll, name, bpy.data.lights.new(name, "AREA"))
    l.data.energy = energy; l.data.size = size; l.data.color = rgb
    l.location = loc; look_at(l, target)
    return l


def card(coll, name, loc, target, sx, sy, m):
    bm = bmesh.new()
    for (x, y) in ((-sx, -sy), (sx, -sy), (sx, sy), (-sx, sy)):
        bm.verts.new((x / 2, y / 2, 0))
    bm.faces.new(bm.verts[:])
    o = mk(name, bm, [m], coll, smooth=False); o.location = loc; look_at(o, target)
    o.rotation_euler.rotate_axis("X", math.pi)                  # face the target
    o.visible_camera = False; o.visible_shadow = False
    return o


def studio(coll, tag, c, s=1.0):
    c = Vector(c)
    area(coll, f"{tag} key", c + Vector((-7, -8, 9)) * s, c, 2600 * s * s, 5 * s)
    area(coll, f"{tag} fill", c + Vector((9, -6, 2.5)) * s, c, 700 * s * s, 8 * s, (0.95, 0.98, 1.0))
    area(coll, f"{tag} rim", c + Vector((2, 8, 7)) * s, c, 2200 * s * s, 3 * s)
    card(coll, f"{tag} strip l", c + Vector((-8, -1, 2)) * s, c, 1.2 * s, 9 * s, SOFT)
    card(coll, f"{tag} strip r", c + Vector((8, -2, 1.5)) * s, c, 1.0 * s, 8 * s, SOFT)
    card(coll, f"{tag} top", c + Vector((0, 0, 11)) * s, c, 7 * s, 5 * s, SOFT)
    card(coll, f"{tag} green kicker", c + Vector((0, 9, 0.5)) * s, c, 6 * s, 2 * s, SOFT_G)
    try:
        pr = link_new(coll, f"{tag} probe", bpy.data.lightprobes.new(f"{tag} probe", "SPHERE"))
        pr.location = c
        for attr, val in (("influence_distance", 9.0 * s), ("clip_start", 0.5)):
            try:
                setattr(pr.data, attr, val)
            except Exception:
                pass
    except Exception as e:
        print("probe:", e)


def instance(coll, name, src, loc=(0, 0, 0), rot=(0, 0, 0), scale=1.0, parent=None):
    e = bpy.data.objects.new(name, None); coll.objects.link(e)
    e.instance_type = "COLLECTION"; e.instance_collection = src
    if parent:
        e.parent = parent
    e.location = loc; e.rotation_euler = rot; e.scale = (scale, scale, scale)
    return e


# ------------------------------------------------------------------ build
SRC_ALL = bpy.data.collections.new("RM ring sources (instanced)"); scene.collection.children.link(SRC_ALL)
STAGE = bpy.data.collections.new("RM stages"); scene.collection.children.link(STAGE)
BAY = 60.0
scene.frame_set(1)
STATS = {}
for bi, (code, name, builder, line) in enumerate(TAKES):
    tag = f"RM {code}"
    src = bpy.data.collections.new(f"{code} {name} ring"); SRC_ALL.children.link(src)
    root = empty(f"{tag} root", src)
    rng = np.random.default_rng(1030 + bi)
    parts = builder(tag, src, root, rng)
    for o in src.objects:
        if o.type == "MESH" and o.parent is None and o is not root:
            o.parent = root
    for o in parts:
        if o.type == "MESH":
            nm = o.name
            gem = any(k in nm for k in (" gem", " shard", " crystal", " spire", " satellite", " chip", " core")) and not any(
                k in nm for k in (" pod", " orb"))
            if " core" in nm:
                sub = 1
            elif gem or " mark" in nm:
                sub = 0
            else:
                sub = 1 if (" hoop" in nm or " strand" in nm or " thorn" in nm) else 2
            finish(o, sub)
    view_update()
    for o in src.objects:
        if o.type == "MESH":
            bake(o)
    view_update()
    vox, nvox = voxelize(f"{tag} voxel twin", root, [o for o in src.objects if o.type == "MESH"], STAGE)
    tris = sum(len(o.data.polygons) for o in src.objects if o.type == "MESH")
    STATS[code] = (tris, nvox)
    print(f"RM {code}: {tris} faces, voxel twin {nvox} voxels")
    srcloc = Vector((bi * BAY, 0, -300))
    root.location = srcloc
    src.instance_offset = srcloc
    bx = bi * BAY
    # hero bay: static 3/4 close-up with depth of field
    hc = Vector((bx, 0, 0))
    cyc(f"{tag} hero cyc", STAGE, hc); studio(STAGE, f"{tag} hero", hc)
    hero = instance(STAGE, f"{tag} hero ring", src, hc, (R(34), 0, R(34)))
    hcam = camera(STAGE, f"Cam {code} hero", hc + Vector((0, -19, 4.6)), hc + Vector((0, 0, 1.0)), 70)
    hcam.data.dof.use_dof = True; hcam.data.dof.focus_object = hero; hcam.data.dof.aperture_fstop = 4.0
    # turntable bay: hero model left, voxel twin right, both one turn over the clip
    tc = Vector((bx, 60, 0))
    cyc(f"{tag} turntable cyc", STAGE, tc); studio(STAGE, f"{tag} turntable", tc)
    for k, (dx, label) in enumerate(((-3.3, "hero"), (3.3, "voxel"))):
        sp = empty(f"{tag} turntable spin {label}", STAGE, tc + Vector((dx, 0, 0)))
        spin_keys(sp, "Z", 1.0, base=(0, 0, R(30)))
        if label == "hero":
            instance(STAGE, f"{tag} turntable ring", src, (0, 0, 0), parent=sp)
        else:
            vox.parent = sp; vox.location = (0, 0, 0)
    camera(STAGE, f"Cam {code} turntable", tc + Vector((0, -16.5, 4.6)), tc + Vector((0, 0, 0.8)), 50)
    # first-person bay: 120 deg eye camera, fist bent back 50 deg, ring on the punching face 1 px in from the back
    eye = Vector((bx, 120, 1.62))
    fc = camera(STAGE, f"Cam {code} - first person", eye, eye + Vector((0, 3, 0)), 18 / math.tan(R(60)))
    fc.rotation_euler = (R(90 - 6), 0, 0); fc.data.sensor_fit = "HORIZONTAL"
    for nm_, a_, b_ in (("h", (-0.007, -0.0006, -0.2), (0.007, 0.0006, -0.2)), ("v", (-0.0006, -0.007, -0.2), (0.0006, 0.007, -0.2))):
        xh = box_mesh(f"Cam {code} crosshair {nm_}", a_, b_, XH, STAGE); xh.parent = fc
    box_mesh(f"{tag} fp ground", (bx - 30, 118, -0.02), (bx + 30, 176, 0), GRASS, STAGE)
    sk = box_mesh(f"{tag} fp sky", (bx - 29.5, 175, -5), (bx + 29.5, 176, 60), SKY, STAGE)
    for sx_ in (-1, 1):
        box_mesh(f"{tag} fp sky side {sx_}", (bx + sx_ * 29.5 - 0.5, 118, -5), (bx + sx_ * 29.5 + 0.5, 176, 60), SKY, STAGE)
    area(STAGE, f"{tag} fp sun", eye + Vector((-1.2, -0.6, 2.2)), eye + Vector((0.2, 0.6, -0.3)), 260, 2.5)
    area(STAGE, f"{tag} fp sky fill", eye + Vector((1.5, 3, 1.5)), eye + Vector((0.2, 0.6, -0.3)), 90, 4, (0.7, 0.8, 1.0))
    hand = box_mesh(f"{tag} fp hand", (-2 * PXF, -2 * PXF, -4 * PXF), (2 * PXF, 2 * PXF, 0), SKIN, STAGE)
    box_mesh(f"{tag} fp knuckles", (-2.05 * PXF, 1.2 * PXF, -4.05 * PXF), (2.05 * PXF, 2.05 * PXF, -3.1 * PXF), SKIN, STAGE).parent = hand
    sleeve = box_mesh(f"{tag} fp sleeve", (-2.05 * PXF, -2.05 * PXF, 0), (2.05 * PXF, 2.05 * PXF, 0.7), SHIRT, STAGE)
    hand.rotation_mode = "QUATERNION"; sleeve.rotation_mode = "QUATERNION"
    ring_local = Vector((0, 0.6 * PXF, -4 * PXF + 0.55 * PXF))
    rmat = Matrix(((0, 1, 0), (1, 0, 0), (0, 0, -1)))          # columns: ring X -> hand Y, ring Y -> hand X, ring Z -> hand -Z
    ri = instance(STAGE, f"{tag} fp ring", src, ring_local, rmat.to_euler(), PXF, parent=hand)
    Rc = Matrix.Rotation(R(-6), 3, "X")
    cs = lambda x, y, d: eye + Rc @ Vector((x, d, y))
    upc = Rc @ Vector((0, 0, 1))
    for f in list(range(1, FRAME_END + 2, 10)):
        u = 2 * math.pi * (f - 1) / FRAME_END
        T = cs(0.2 + 0.01 * math.sin(u), -0.16 + 0.012 * math.sin(2 * u), 0.56)
        S = cs(0.42, -0.62, 0.05)
        a = (T - S).normalized()
        upp = (upc - a * a.dot(upc)).normalized()
        bnd = R(50 + 6 * math.sin(u))
        punch = (a * math.cos(bnd) + upp * math.sin(bnd)).normalized()
        back = (upp * math.cos(bnd) - a * math.sin(bnd)).normalized()
        roll = Matrix.Rotation(R(16 * math.sin(u)), 3, a)
        punch = roll @ punch; back = roll @ back
        Z = -punch; Y = back; X = Y.cross(Z)
        Rh = Matrix((X, Y, Z)).transposed()
        H = T - Rh @ ring_local
        hand.location = H; hand.rotation_quaternion = Rh.to_quaternion()
        hand.keyframe_insert("location", frame=f); hand.keyframe_insert("rotation_quaternion", frame=f)
        Zs = -a; Ys = roll @ upp; Xs = Ys.cross(Zs)
        sleeve.location = H; sleeve.rotation_quaternion = Matrix((Xs, Ys, Zs)).transposed().to_quaternion()
        sleeve.keyframe_insert("location", frame=f); sleeve.keyframe_insert("rotation_quaternion", frame=f)

# ------------------------------------------------------------------ world, render, bloom, save
world = bpy.data.worlds.new(SCENE_NAME + " world"); world.use_nodes = True
wn = world.node_tree; bg = wn.nodes["Background"]
lp = wn.nodes.new("ShaderNodeLightPath")
tcw = wn.nodes.new("ShaderNodeTexCoord")
sep = wn.nodes.new("ShaderNodeSeparateXYZ"); wn.links.new(tcw.outputs["Generated"], sep.inputs[0])
ramp = wn.nodes.new("ShaderNodeValToRGB")
mr = wn.nodes.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = -1.0; mr.inputs["From Max"].default_value = 1.0
wn.links.new(sep.outputs["Z"], mr.inputs["Value"]); wn.links.new(mr.outputs["Result"], ramp.inputs["Fac"])
ramp.color_ramp.elements[0].color = (0.012, 0.014, 0.014, 1); ramp.color_ramp.elements[0].position = 0.35
ramp.color_ramp.elements[1].color = (0.75, 0.78, 0.8, 1); ramp.color_ramp.elements[1].position = 0.92
el = ramp.color_ramp.elements.new(0.55); el.color = (0.05, 0.07, 0.06, 1)
mixw = wn.nodes.new("ShaderNodeMix"); mixw.data_type = "RGBA"
wn.links.new(lp.outputs["Is Camera Ray"], mixw.inputs[0])
for s in mixw.inputs:
    if s.identifier == "A_Color":
        wn.links.new(ramp.outputs["Color"], s)
    if s.identifier == "B_Color":
        s.default_value = (0.01, 0.012, 0.012, 1)
for s in mixw.outputs:
    if s.identifier == "Result_Color":
        wn.links.new(s, bg.inputs["Color"])
bg.inputs["Strength"].default_value = 1.0
scene.world = world
try:
    scene.render.engine = "BLENDER_EEVEE"
except Exception:
    scene.render.engine = "BLENDER_EEVEE_NEXT"
ee = scene.eevee
for attr, val in (("use_raytracing", True), ("ray_tracing_method", "SCREEN"), ("use_shadows", True),
                  ("taa_render_samples", 64), ("use_fast_gi", True), ("shadow_ray_count", 2), ("shadow_step_count", 8)):
    try:
        setattr(ee, attr, val)
    except Exception:
        pass
try:
    ee.ray_tracing_options.resolution_scale = "1"
    ee.ray_tracing_options.trace_max_roughness = 0.6
except Exception:
    pass
scene.render.resolution_x, scene.render.resolution_y = 1600, 900
try:
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
except Exception:
    pass
try:
    tree = bpy.data.node_groups.new(SCENE_NAME + " Glow", "CompositorNodeTree")
    tree.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    rl = tree.nodes.new("CompositorNodeRLayers"); go = tree.nodes.new("NodeGroupOutput")
    gl_ = tree.nodes.new("CompositorNodeGlare")
    if "Type" in gl_.inputs:
        gl_.inputs["Type"].default_value = "Bloom"
    for nm_, val in (("Size", 0.45), ("Strength", 0.35), ("Threshold", 1.0)):
        if nm_ in gl_.inputs:
            gl_.inputs[nm_].default_value = val
    tree.links.new(rl.outputs["Image"], gl_.inputs["Image"]); tree.links.new(gl_.outputs["Image"], go.inputs[0])
    scene.compositing_node_group = tree
except Exception as e:
    print("no glow:", e)
scene.camera = bpy.data.objects[f"Cam {TAKES[0][0]} hero"]
scene.frame_set(1)
try:
    bpy.ops.outliner.orphans_purge(do_recursive=True)
except Exception:
    pass
print("RM STATS", STATS)
if not os.environ.get("RM_NOSAVE"):
    bpy.ops.wm.save_as_mainfile(filepath=OUT)
