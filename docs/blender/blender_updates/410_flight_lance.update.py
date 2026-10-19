# Pass 410: the primed flight lance, three new builds (movement range, 2026-10-19). J rated pass 409 P1 "hex lance + twin
# helix" IMPROVE with no note, so this is three new labelled variations of it, each built a different way (rules: an
# IMPROVE with no note = 3 new takes, siblings of the rated one). P1 stays the baseline in pass 409.
#   P1a = nested hex rings: seven hard-light hex frames stacked into a lance, turning in alternating directions; a faint
#         hex hull between them; a braid of three ribbons winds in behind and pulls tight.
#   P1b = crystal spear: three layers of separate dark-jade facets (gaps between, lit edges) round an eight-sided spear
#         that turns slowly; flat diamond shards peel off the back and tumble away.
#   P1c = twin blade: two crossed leaf blades with a bright centre line, turning one way; four long thin streaks trail
#         from the blade tails.
# Same lead-in as 409: every lane flies 2 s as the thin fast-flight cap (F, not a take: J dropped it), primes at tick
# 40 (the cap folds away in 4 ticks, the lance snaps on with a small overshoot and a flash ring), then flies 4 s primed.
# Fast flat glide at 1 block a tick, ring arm leading. Cameras: "Cam P1a|P1b|P1c" (chase), "Cam <take> side",
# "Cam <take> fp" (an eye camera just in front of the face, 120 degrees wide like the game).
import json, math, os
import bpy
import numpy as np
from mathutils import Matrix

R = math.radians
OUT = os.path.join(FOLDER, "flight_barrier2.blend")
if bpy.data.filepath:
    try:
        bpy.ops.wm.save_mainfile()
    except Exception as e:
        print("save current:", e)
old = bpy.data.scenes.get("Flight Barrier 2")
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new("Flight Barrier 2")
col = scene.collection
scene.render.fps = 20
win = bpy.context.window
if win:
    win.scene = scene

def link(o):
    col.objects.link(o)
    return o


# ------------------------------------------------------------------ rig (Minecraft model space: px, y down, -z forward)
PIVOT = {"head": (0, 0, 0), "body": (0, 0, 0), "rarm": (-5, 2, 0), "larm": (5, 2, 0),
         "rleg": (-1.9, 12, 0), "lleg": (1.9, 12, 0), "rshin": (-1.9, 18, 0), "lshin": (1.9, 18, 0)}
BOX = {"head": ((-4, -8, -4), (4, 0, 4)), "body": ((-4, 0, -2), (4, 12, 2)), "rarm": ((-3, -2, -2), (1, 10, 2)),
       "larm": ((-1, -2, -2), (3, 10, 2)), "rleg": ((-2, 0, -2), (2, 6, 2)), "lleg": ((-2, 0, -2), (2, 6, 2)),
       "rshin": ((-2, 0, -2), (2, 6, 2)), "lshin": ((-2, 0, -2), (2, 6, 2))}
PARTS = ("head", "body", "rarm", "larm", "rleg", "lleg", "rshin", "lshin")


def euler_of(Rm):
    """XYZ euler (x, y, z) of R = Rz @ Ry @ Rx, the inverse of rot()."""
    y = math.asin(max(-1.0, min(1.0, -Rm[2, 0])))
    return (math.atan2(Rm[2, 1], Rm[2, 2]), y, math.atan2(Rm[1, 0], Rm[0, 0]))
GROUND = 24.0
A = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]], float)      # MC model axes -> Blender axes (x, z, -y)


def rot(x, y, z):
    cx, sx, cy, sy, cz, sz = math.cos(x), math.sin(x), math.cos(y), math.sin(y), math.cos(z), math.sin(z)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def corners(part, pivot, r):
    a, b = BOX[part]
    pts = np.array([[x, y, z] for x in (a[0], b[0]) for y in (a[1], b[1]) for z in (a[2], b[2])], float)
    return pts @ rot(*r).T + np.asarray(pivot, float)


def solve(p):
    """Pose (ring = right side) -> per part rotation and pivot. The body turns about the hips, the legs hang from the
    hips, grounded poses drop the hips until the lowest foot touches, `sink` lowers the torso into the legs."""
    rot_ = {"body": p.get("body", (0, 0, 0)), "head": p.get("head", (0, 0, 0))}
    # the neck bends at most ~57 degrees back from the body, so a flat flyer looks ahead instead of folding the head
    # back into his own chest (J, F3)
    hb = rot_["head"]; rot_["head"] = (max(hb[0], rot_["body"][0] - 1.0), hb[1], hb[2])
    for k, part, sgn in (("ring", "rarm", 1), ("free", "larm", -1), ("ringleg", "rleg", 1), ("freeleg", "lleg", -1)):
        x, y, z = p.get(k, (0, 0, 0))
        rot_[part] = (x, sgn * y, sgn * z)
    Rb = rot(*rot_["body"])
    sink = float(p.get("sink", 0.0))
    piv = {}

    def place(d):
        hip = np.array([0.0, 12.0 + d, -float(p.get("fwd", 0.0))])
        neck = hip + Rb @ np.array([0.0, -12.0, 0.0]) + np.array([0.0, sink, 0.0])
        piv["body"] = neck; piv["head"] = neck.copy()
        piv["rarm"] = neck + Rb @ np.array([-5.0, 2.0, 0.0]); piv["larm"] = neck + Rb @ np.array([5.0, 2.0, 0.0])
        piv["rleg"] = hip + Rb @ np.array([-1.9, 0.0, 0.0]) * np.array([1, 0, 1]) + np.array([0, 0, 0])
        piv["lleg"] = hip + Rb @ np.array([1.9, 0.0, 0.0]) * np.array([1, 0, 1])
        for leg, shin in (("rleg", "rshin"), ("lleg", "lshin")):
            piv[shin] = piv[leg] + rot(*rot_[leg]) @ np.array([0.0, 6.0, 0.0])

    for leg, shin, kk in (("rleg", "rshin", "ringknee"), ("lleg", "lshin", "freeknee")):
        k = float(p.get(kk, 0.0))
        rot_[shin] = euler_of(rot(*rot_[leg]) @ rot(k, 0, 0))
    place(0.0)
    d = 0.0
    if p.get("grounded", True):
        low = max(corners(k, piv[k], rot_[k])[:, 1].max() for k in ("rleg", "lleg", "rshin", "lshin"))
        d = GROUND - low
        place(d)
    return {k: (np.asarray(rot_[k], float), piv[k]) for k in PARTS}


def hand_point(sol, part="rarm"):
    r, pv = sol[part]
    return np.array([-1.0 if part == "rarm" else 1.0, 10.0, 0.0]) @ rot(*r).T + pv


def to_bl(v):
    v = np.asarray(v, float)
    return A @ np.array([v[0], v[1] - GROUND, v[2]]) / 16.0


def mat(name, rgb, emit=0.0, rough=0.6, metal=0.0, alpha=1.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes.get("Principled BSDF")
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


SKIN = mat("KL skin", (0.62, 0.42, 0.3)); SHIRT = mat("KL shirt", (0.04, 0.28, 0.12))
PANTS = mat("KL pants", (0.03, 0.05, 0.09)); HAIR = mat("KL hair", (0.08, 0.05, 0.03))
RINGM = mat("KL ring", (0.1, 1.0, 0.25), emit=3.0)
SHOES = mat("KL shoes", (0.12, 0.12, 0.13))
PART_MAT = {"head": SKIN, "body": SHIRT, "rarm": SHIRT, "larm": SHIRT, "rleg": PANTS, "lleg": PANTS,
            "rshin": PANTS, "lshin": PANTS}


def box_mesh(name, a, b, m):
    a = np.array(a, float); b = np.array(b, float)
    pts = [np.array([x, y, z]) for x in (a[0], b[0]) for y in (a[1], b[1]) for z in (a[2], b[2])]
    verts = [tuple(A @ p / 16.0) for p in pts]
    faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    me.materials.append(m)
    return me


def make_player(tag):
    objs = {}
    for k in PARTS:
        a, b = BOX[k]
        o = link(bpy.data.objects.new(f"KL {tag} {k}", box_mesh(f"KL {tag} {k}", a, b, PART_MAT[k])))
        o.rotation_mode = "XYZ"
        objs[k] = o
    # details as children: hair cap, hands, ring
    for k, (a, b), m in (("head", ((-4.05, -8.05, -4.05), (4.05, -6.5, 4.05)), HAIR),
                         ("rarm", ((-3.02, 7, -2.02), (1.02, 10.02, 2.02)), SKIN),
                         ("larm", ((-1.02, 7, -2.02), (3.02, 10.02, 2.02)), SKIN),
                         ("rarm", ((-3.4, 6.2, -2.4), (1.4, 7.4, 2.4)), RINGM),
                         ("rshin", ((-2.02, 4.5, -2.02), (2.02, 6.02, 2.02)), SHOES),
                         ("lshin", ((-2.02, 4.5, -2.02), (2.02, 6.02, 2.02)), SHOES)):
        c = link(bpy.data.objects.new(f"KL {tag} {k} detail", box_mesh(f"KL {tag} {k} d", a, b, m)))
        c.parent = objs[k]
        if m is RINGM:
            objs["ring"] = c
    return objs


def set_pose(objs, sol, origin, frame, side=0.0):
    rs = np.array([[math.cos(side), -math.sin(side), 0], [math.sin(side), math.cos(side), 0], [0, 0, 1]])
    for k in PARTS:
        r, pv = sol[k]
        Rb = rs @ (A @ rot(*r) @ A.T)
        loc = rs @ to_bl(pv) + np.asarray(origin)
        o = objs[k]
        M = np.eye(4); M[:3, :3] = Rb; M[:3, 3] = loc
        from mathutils import Matrix
        o.matrix_world = Matrix(M.tolist())
        o.keyframe_insert("location", frame=frame); o.keyframe_insert("rotation_euler", frame=frame)


def cam(name, loc, look, lens=40):
    c = link(bpy.data.objects.new(name, bpy.data.cameras.new(name)))
    c.location = loc; c.data.lens = lens
    d = np.array(look, float) - np.array(loc, float)
    c.rotation_euler = (math.atan2(math.hypot(d[0], d[1]), -d[2]), 0, math.atan2(d[1], d[0]) - math.pi / 2)
    return c



def smooth(t):
    return t * t * (3 - 2 * t)


def mixp(a, b, w):
    keys = set(a) | set(b)
    out = {}
    for k in keys:
        va, vb = a.get(k), b.get(k)
        if k in ("grounded",):
            continue
        if isinstance(va, tuple) or isinstance(vb, tuple):
            va = np.array(va if va is not None else (0, 0, 0), float); vb = np.array(vb if vb is not None else (0, 0, 0), float)
            out[k] = tuple(va + (vb - va) * w)
        else:
            va = 0.0 if va is None else va; vb = 0.0 if vb is None else vb
            out[k] = va + (vb - va) * w
    return out

def set_pose_w(objs, sol, origin, frame, byaw, phi, roll):
    """Like set_pose, plus a bank: roll about the travel direction, so the top of the body tips into the turn."""
    def Rz(a):
        return np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])
    Ry = np.array([[math.cos(roll), 0, math.sin(roll)], [0, 1, 0], [-math.sin(roll), 0, math.cos(roll)]])
    W = Rz(phi) @ Ry @ Rz(byaw - phi)
    chest = np.array([0, 0, 1.0])
    for k in PARTS:
        r, pv = sol[k]
        Rb = W @ (A @ rot(*r) @ A.T)
        loc = W @ (to_bl(pv) - chest) + chest + np.asarray(origin)
        M = np.eye(4); M[:3, :3] = Rb; M[:3, 3] = loc
        objs[k].matrix_world = Matrix(M.tolist())
        objs[k].keyframe_insert("location", frame=frame); objs[k].keyframe_insert("rotation_euler", frame=frame)




# ================================================================== pass 410: three primed lance builds
import bmesh, random

T_END = 120
T_PRIME = 40                 # the tick the flyer primes (shift)
V = 1.0                      # blocks a tick: fast flight
LEAD = 1.6
KEYS = [(0, 0), (30, 0), (50, 12), (70, 12), (90, -10), (120, -10)]   # (tick, heading deg clockwise)
TAKES = ["P1a", "P1b", "P1c"]
NAMES = {"P1a": "primed lance: nested hex rings + braid", "P1b": "primed lance: crystal facets + peeling shards",
         "P1c": "primed lance: twin crossed blades + streaks"}
GREEN = (0.10, 1.0, 0.30)
DEEP = (0.02, 0.35, 0.10)
LIME = (0.45, 1.0, 0.25)
random.seed(410)


def course(t):
    t = max(0.0, min(KEYS[-1][0], t))
    for (t0, h0), (t1, h1) in zip(KEYS, KEYS[1:]):
        if t0 <= t <= t1:
            w = smooth((t - t0) / (t1 - t0)) if t1 > t0 else 1.0
            return h0 + (h1 - h0) * w
    return KEYS[-1][1]


def Rz(a):
    return np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])


GLIDE = dict(body=(1.42, 0, 0), head=(-1.25, 0, 0), ringleg=(1.38, 0, 0.03), ringknee=0.25, freeleg=(1.3, 0, -0.03),
             freeknee=0.4, grounded=False)


def pose_at(take, t):
    """The flat fast glide: ring arm straight ahead past the head (it leads), free arm back along the side.
    Primed (after T_PRIME): the free arm pulls in tight and the legs close up, a little more tucked."""
    p = dict(GLIDE)
    k = smooth(min(1.0, max(0.0, (t - T_PRIME) / 4.0)))
    dyaw = R(course(t) - course(t - LEAD))
    p["ring"] = (-math.pi + 0.06, dyaw, 0.06)
    p["free"] = (0.12 - 0.1 * k, 0, -0.16 + 0.1 * k)
    p["ringleg"] = (1.38, 0, 0.03 - 0.03 * k); p["freeleg"] = (1.3 + 0.08 * k, 0, -0.03 + 0.03 * k)
    return p


# ------------------------------------------------------------------ construct materials (procedural, see-through)
def cmat(name, pattern, rgb, alpha, emit, scale=4.0):
    """Hard-light construct surface: darker body, the pattern's lines glow; alpha follows the pattern."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    P = N.get("Principled BSDF")
    tc = N.new("ShaderNodeTexCoord")
    if pattern == "hex":
        vo = N.new("ShaderNodeTexVoronoi"); vo.feature = "DISTANCE_TO_EDGE"; vo.inputs["Scale"].default_value = scale
        L.new(tc.outputs["Object"], vo.inputs["Vector"])
        mr = N.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.0; mr.inputs["From Max"].default_value = 0.08
        mr.inputs["To Min"].default_value = 1.0; mr.inputs["To Max"].default_value = 0.0
        L.new(vo.outputs["Distance"], mr.inputs["Value"]); fac = mr.outputs["Result"]
    elif pattern == "weave":
        w1 = N.new("ShaderNodeTexWave"); w1.inputs["Scale"].default_value = scale; w1.wave_type = "BANDS"
        w2 = N.new("ShaderNodeTexWave"); w2.inputs["Scale"].default_value = scale; w2.wave_type = "BANDS"
        w2.bands_direction = "Y"
        L.new(tc.outputs["Object"], w1.inputs["Vector"]); L.new(tc.outputs["Object"], w2.inputs["Vector"])
        mx = N.new("ShaderNodeMath"); mx.operation = "MAXIMUM"
        p1 = N.new("ShaderNodeMath"); p1.operation = "POWER"; p1.inputs[1].default_value = 6.0
        p2 = N.new("ShaderNodeMath"); p2.operation = "POWER"; p2.inputs[1].default_value = 6.0
        L.new(w1.outputs["Fac"], p1.inputs[0]); L.new(w2.outputs["Fac"], p2.inputs[0])
        L.new(p1.outputs[0], mx.inputs[0]); L.new(p2.outputs[0], mx.inputs[1]); fac = mx.outputs[0]
    else:   # "solid": an even glow (rims, lines, pixels)
        v = N.new("ShaderNodeValue"); v.outputs[0].default_value = 1.0; fac = v.outputs[0]
    P.inputs["Base Color"].default_value = (rgb[0] * 0.25, rgb[1] * 0.25, rgb[2] * 0.25, 1)
    P.inputs["Emission Color"].default_value = (*rgb, 1)
    P.inputs["Roughness"].default_value = 0.25
    em = N.new("ShaderNodeMath"); em.operation = "MULTIPLY_ADD"
    em.inputs[1].default_value = emit; em.inputs[2].default_value = emit * 0.18
    L.new(fac, em.inputs[0]); L.new(em.outputs[0], P.inputs["Emission Strength"])
    al = N.new("ShaderNodeMath"); al.operation = "MULTIPLY_ADD"
    al.inputs[1].default_value = alpha * 0.7; al.inputs[2].default_value = alpha * 0.3
    L.new(fac, al.inputs[0]); L.new(al.outputs[0], P.inputs["Alpha"])
    try:
        m.surface_render_method = "BLENDED"
    except Exception:
        pass
    m.use_backface_culling = False
    return m


M_CAP = cmat("RB410 cap weave", "weave", GREEN, 0.16, 1.0, 5.0)
M_RIM = cmat("RB410 rim", "solid", GREEN, 0.8, 2.5)
M_HULL = cmat("RB410 hex hull", "hex", GREEN, 0.12, 1.3, 3.0)
M_EDGE = cmat("RB410 edge", "solid", GREEN, 0.9, 2.0)
M_FRAME = cmat("RB410 frame", "solid", GREEN, 0.85, 1.4)
M_FACET = [cmat(f"RB410 facet {i}", "solid", c, 0.55, e) for i, (c, e) in
           enumerate((((0.03, 0.42, 0.16), 0.4), ((0.02, 0.30, 0.12), 0.3), ((0.05, 0.55, 0.20), 0.55)), start=1)]
M_BLADE = cmat("RB410 blade", "hex", GREEN, 0.3, 1.0, 2.2)
M_LINE = cmat("RB410 centre line", "solid", GREEN, 0.9, 2.0)
M_TRAIL = cmat("RB410 trail", "solid", GREEN, 0.7, 1.4)
M_SHARD = cmat("RB410 shard", "solid", (0.12, 1.0, 0.30), 0.75, 1.6)
M_FLASH = cmat("RB410 prime flash", "solid", LIME, 0.5, 3.5)
STONE = mat("RB410 stone", (0.32, 0.32, 0.34)); LABEL = mat("RB410 label", (0.85, 1.0, 0.9), emit=2.0)


def mesh_from_bm(name, bm, m):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); me.materials.append(m)
    return me


def cap_mesh(name, r, half_deg, m):
    """A spherical cap of radius r round the flyer's middle, opening forward (-Y), half-angle half_deg."""
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=40, v_segments=24, radius=r)
    c = math.cos(R(half_deg))
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if (-v.co.y) / r < c], context="VERTS")
    return mesh_from_bm(name, bm, m)


def ring_curve(name, r, m, depth=0.05, sides=48, y=0.0):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = depth
    sp = cu.splines.new("POLY"); sp.points.add(sides - 1); sp.use_cyclic_u = True
    for i in range(sides):
        a = 2 * math.pi * i / sides
        sp.points[i].co = (r * math.cos(a), y, r * math.sin(a), 1)
    cu.materials.append(m)
    return cu


def hex_ring_curve(name, r, m, depth=0.035):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = depth
    sp = cu.splines.new("POLY"); sp.points.add(5); sp.use_cyclic_u = True
    for i in range(6):
        a = 2 * math.pi * i / 6 + math.pi / 6
        sp.points[i].co = (r * math.cos(a), 0, r * math.sin(a), 1)
    cu.materials.append(m)
    return cu


def key_scale(o, frame, s):
    o.scale = (s, s, s) if not isinstance(s, tuple) else s
    o.keyframe_insert("scale", frame=frame)


def spawn(name, data, loc, rot_z, frame, life, size=1.0, drift=(0, 0, 0)):
    """A short-lived piece: appears at `frame`, shrinks to nothing over `life` ticks while drifting."""
    o = link(bpy.data.objects.new(name, data)); o.rotation_mode = "XYZ"; o.rotation_euler = (0, 0, rot_z)
    o.location = tuple(loc)
    if frame > 1:
        key_scale(o, frame - 1, 0.0)
    key_scale(o, frame, size)
    o.keyframe_insert("location", frame=frame)
    o.location = tuple(np.asarray(loc) + np.asarray(drift) * life)
    o.keyframe_insert("location", frame=frame + life)
    key_scale(o, frame + life, 0.0)
    return o


# ------------------------------------------------------------------ the three lance builds
def hex_hull():
    """P1a: a faint six-sided hull, apex 3.8 blocks ahead of the chest, 1.2 wide at the hips."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=False, segments=6, radius1=1.2, radius2=0.0, depth=2.9)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(R(90), 3, "X"))
    bmesh.ops.translate(bm, verts=bm.verts, vec=(0, -2.35, 0))
    return mesh_from_bm("RB410 hull", bm, M_HULL)


def nested_rings():
    """P1a: seven hex frames, radius 1.2 at the hips shrinking to 0.18 near the apex, spaced along the travel line."""
    out = []
    for i in range(7):
        w = i / 6.0
        r = 1.2 * (1 - w) ** 0.85 + 0.18 * w
        y = -0.9 - 2.8 * w ** 0.9
        cu = hex_ring_curve(f"RB410 frame {i}", r, M_FRAME, 0.045 - 0.02 * w)
        out.append((cu, y, 5.0 * (1 if i % 2 == 0 else -1) * (0.7 + 0.15 * i)))
    return out


def crystal_facets():
    """P1b: three layers of eight separate kite facets, each narrower and shorter toward the nose, every layer
    turned half a facet from the one below, a slim gap between neighbours. Returns (mesh, edge mesh)."""
    bm = bmesh.new(); eb = bmesh.new()
    layers = ((1.15, -1.7, -3.9, 0.0), (0.82, -2.1, -3.6, math.pi / 8), (0.48, -2.5, -3.3, 0.0))
    for li, (rb, yb, yt, off) in enumerate(layers):
        for k in range(8):
            th = off + 2 * math.pi * k / 8
            half = 0.34 * math.pi / 4
            pts = []
            for dth, rr, yy in ((-half, rb, yb), (half, rb, yb), (0.0, rb * 0.42, (yb + yt) * 0.5 - 0.1), (0.0, 0.0, yt)):
                pts.append((rr * math.cos(th + dth), yy, rr * math.sin(th + dth)))
            # facet = two triangles: base-left, base-right, shoulder, plus shoulder, nose
            for b_ in (bm, eb):
                v = [b_.verts.new(p) for p in pts]
                f1 = b_.faces.new((v[0], v[1], v[2])); f2 = b_.faces.new((v[0], v[2], v[3])); f3 = b_.faces.new((v[1], v[3], v[2]))
                if b_ is bm:
                    for f in (f1, f2, f3):
                        f.material_index = (li + k) % 3
    return bm, eb


def blade_mesh(name, m):
    """P1c: a leaf-shaped flat blade in the x-y plane: apex 4.1 ahead, widest 0.55 about 1.1 blocks back, notched tail."""
    bm = bmesh.new()
    pts = [(0, -4.1), (0.55, -3.0), (0.45, -1.9), (0.0, -1.55), (-0.45, -1.9), (-0.55, -3.0)]
    v = [bm.verts.new((x, y, 0)) for x, y in pts]
    bm.faces.new(v)
    return mesh_from_bm(name, bm, m)


def line_mesh(name, length, width, m):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(width, length, width), verts=bm.verts)
    return mesh_from_bm(name, bm, m)


# ------------------------------------------------------------------ glow (compositor bloom), shared meshes
try:
    tree = bpy.data.node_groups.new("RB410 Glow", "CompositorNodeTree")
    tree.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    rl = tree.nodes.new("CompositorNodeRLayers"); go = tree.nodes.new("NodeGroupOutput")
    gl = tree.nodes.new("CompositorNodeGlare")
    if "Type" in gl.inputs:
        gl.inputs["Type"].default_value = "Bloom"
    for nm, val in (("Size", 0.5), ("Strength", 0.3), ("Threshold", 1.2)):
        if nm in gl.inputs:
            gl.inputs[nm].default_value = val
    tree.links.new(rl.outputs["Image"], gl.inputs["Image"]); tree.links.new(gl.outputs["Image"], go.inputs[0])
    scene.compositing_node_group = tree
except Exception as e:
    print("no glow:", e)

CAP = cap_mesh("RB410 cap", 4.5, 38, M_CAP)
RIM = ring_curve("RB410 cap rim", 4.5 * math.sin(R(38)), M_RIM, 0.06, y=-4.5 * math.cos(R(38)))
HULL = hex_hull()
FRAMES = nested_rings()
_fb, _eb = crystal_facets()
FACETS = bpy.data.meshes.new("RB410 facets"); _fb.to_mesh(FACETS); _fb.free()
for m_ in M_FACET:
    FACETS.materials.append(m_)
FACET_EDGES = bpy.data.meshes.new("RB410 facet edges"); _eb.to_mesh(FACET_EDGES); _eb.free(); FACET_EDGES.materials.append(M_EDGE)
BLADE = blade_mesh("RB410 blade", M_BLADE)
BLADE_EDGE = bpy.data.meshes.new("RB410 blade edge")
BLADE_EDGE.from_pydata([v.co[:] for v in BLADE.vertices], [], [tuple(p.vertices) for p in BLADE.polygons])
BLADE_EDGE.update(); BLADE_EDGE.materials.append(M_EDGE)
BLADE_LINE = line_mesh("RB410 blade centre line", 2.2, 0.045, M_LINE)
_bm = bmesh.new(); bmesh.ops.create_cube(_bm, size=1.0)
bmesh.ops.scale(_bm, vec=(0.09, 1.05, 0.09), verts=_bm.verts)
TRAIL_BITS = mesh_from_bm("RB410 trail strip", _bm, M_TRAIL)
_bm = bmesh.new(); bmesh.ops.create_icosphere(_bm, subdivisions=1, radius=0.2)
bmesh.ops.scale(_bm, vec=(0.35, 1.25, 0.12), verts=_bm.verts)
SHARD = mesh_from_bm("RB410 shard", _bm, M_SHARD)
FLASH = ring_curve("RB410 flash", 1.0, M_FLASH, 0.05)


def parented(name, data, mover, local=(0, 0, 0)):
    o = link(bpy.data.objects.new(name, data)); o.parent = mover; o.location = local; o.rotation_mode = "XYZ"
    return o


LANE = 70.0
for li, take in enumerate(TAKES):
    ox = li * LANE
    objs = make_player(take)
    rm = mat(f"RB410 ring {take}", (0.1, 1.0, 0.25), emit=6.0); objs["ring"].data.materials[0] = rm
    mover = link(bpy.data.objects.new(f"RB410 {take} mover", None)); mover.empty_display_size = 0.1
    mover.rotation_mode = "XYZ"
    chest = (0, 0, 1.0)
    cap = parented(f"RB410 {take} fast cap", CAP, mover, chest)
    rim = parented(f"RB410 {take} fast cap rim", RIM, mover, chest)
    primed = []
    if take == "P1a":
        primed = [parented(f"RB410 {take} hull", HULL, mover, chest)]
        for i, (cu, y, rate) in enumerate(FRAMES):
            o = parented(f"RB410 {take} frame {i}", cu, mover, (chest[0], chest[1] + y, chest[2])); o["spin"] = rate
            primed.append(o)
    elif take == "P1b":
        fo = parented(f"RB410 {take} facets", FACETS, mover, chest); fo["spin"] = 3.0
        so = fo.modifiers.new("thick", "SOLIDIFY"); so.thickness = 0.03; so.offset = 0.0
        eo = parented(f"RB410 {take} facet edges", FACET_EDGES, mover, chest); eo["spin"] = 3.0
        wf = eo.modifiers.new("edges", "WIREFRAME"); wf.thickness = 0.025; wf.use_replace = True
        primed = [fo, eo]
    elif take == "P1c":
        for j, rot0 in enumerate((0.0, 90.0)):
            bl = parented(f"RB410 {take} blade {j}", BLADE, mover, chest); bl["spin"] = 4.0; bl["rot0"] = rot0
            so = bl.modifiers.new("thick", "SOLIDIFY"); so.thickness = 0.04; so.offset = 0.0
            ed = parented(f"RB410 {take} blade edge {j}", BLADE_EDGE, mover, chest); ed["spin"] = 4.0; ed["rot0"] = rot0
            wfm = ed.modifiers.new("edges", "WIREFRAME"); wfm.thickness = 0.03; wfm.use_replace = True
            ln = parented(f"RB410 {take} blade line {j}", BLADE_LINE, bl, (0, -2.75, 0))   # rides the blade's own plane
            primed += [bl, ed]
    pos = np.array([ox, 0.0, 9.0])
    for t in range(T_END + 1):
        f = t + 1
        phi = -R(course(t))
        fwd = Rz(phi) @ np.array([0.0, -1.0, 0.0])
        if t > 0:
            pos = pos + V * fwd
        p = pose_at(take, t)
        sol = solve(p)
        phi_b = -R(course(t - LEAD))
        set_pose_w(objs, sol, pos, f, phi_b, phi_b, 0.0)
        mover.location = tuple(pos); mover.rotation_euler = (0, 0, phi)
        mover.keyframe_insert("location", frame=f); mover.keyframe_insert("rotation_euler", frame=f)
        W = Rz(phi_b)
        hand = W @ (to_bl(hand_point(sol, "rarm")) - np.array(chest)) + np.array(chest) + pos
        is_primed = t >= T_PRIME
        ctr = pos + np.array(chest)
        if not is_primed:
            # fast flight: one thin ribbon off the ring fist, quiet
            spawn(f"RB410 {take} trail {t}", TRAIL_BITS, hand + 0.3 * fwd, phi, f, 8, 1.0, -0.02 * fwd)
        elif take == "P1a":
            # a braid of three ribbons that winds in and pulls tight behind the flyer
            for k_ in range(3):
                a = 0.4 * t + 2 * math.pi * k_ / 3
                off = Rz(phi) @ np.array([math.cos(a) * 0.55, 0.0, 0.0]) + np.array([0, 0, math.sin(a) * 0.55])
                spawn(f"RB410 {take} braid {k_} {t}", TRAIL_BITS, ctr + off - 0.8 * fwd, phi, f, 10, 1.1,
                      -off / 10.0 * 0.85 - 0.02 * fwd)
        elif take == "P1b":
            # flat diamond shards peel off the back and tumble outward
            for k_ in range(2):
                a = random.uniform(0, 2 * math.pi); rr = random.uniform(0.3, 0.8)
                off = Rz(phi) @ np.array([math.cos(a) * rr, 0.0, 0.0]) + np.array([0, 0, math.sin(a) * rr])
                spawn(f"RB410 {take} shard {t} {k_}", SHARD, ctr + off - random.uniform(0.6, 1.4) * fwd,
                      phi + random.uniform(-1.0, 1.0), f, 16, random.uniform(0.6, 1.1), off * 0.05 - 0.04 * fwd)
        elif take == "P1c":
            # four long thin streaks from the blade tails, following their spin
            th = R(4.0) * (t - T_PRIME)
            for k_ in range(4):
                a = -th + math.pi / 2 * k_
                off = Rz(phi) @ np.array([math.cos(a) * 0.5, 0.0, 0.0]) + np.array([0, 0, math.sin(a) * 0.5])
                spawn(f"RB410 {take} streak {k_} {t}", TRAIL_BITS, ctr + off - 1.2 * fwd, phi, f, 6, (1.0, 2.2, 1.0),
                      -0.06 * fwd)
    # the switch: fast cap folds away in 4 ticks, the primed look snaps on with a small overshoot and a flash
    for o in (cap, rim):
        key_scale(o, 1, 1.0)
        key_scale(o, T_PRIME + 1, 1.0); key_scale(o, T_PRIME + 5, 0.0)
    for o in primed:
        base = tuple(o.scale)
        key_scale(o, 1, (0.0, 0.0, 0.0)); key_scale(o, T_PRIME + 1, (0.0, 0.0, 0.0))
        key_scale(o, T_PRIME + 4, tuple(b * 1.15 for b in base)); key_scale(o, T_PRIME + 7, base)
        rate = o.get("spin")
        if rate is not None:                      # turns about the travel line, one way per piece
            for fr in range(T_PRIME + 1, T_END + 2, 10):
                o.rotation_euler = (0, R(rate) * (fr - T_PRIME) + R(o.get("rot0", 0.0)), 0); o.keyframe_insert("rotation_euler", frame=fr)
    scene.frame_set(T_PRIME + 1); bpy.context.view_layer.update()
    fl = link(bpy.data.objects.new(f"RB410 {take} prime flash", FLASH)); fl.parent = mover; fl.location = (0, -0.5, 1.0)
    key_scale(fl, 1, 0.0); key_scale(fl, T_PRIME, 0.0); key_scale(fl, T_PRIME + 1, 0.6); key_scale(fl, T_PRIME + 6, 4.0)
    key_scale(fl, T_PRIME + 7, 0.0)
    # speed markers: stone pillars either side of the lane
    for i in range(0, 130, 10):
        for sx in (-7, 7):
            h = 2 + (i * 7 + sx) % 5
            bpy_o = link(bpy.data.objects.new(f"RB410 {take} pillar {i} {sx}",
                                               box_mesh(f"RB410 pillar {take} {i} {sx}", (-8, -16 * h, -8), (8, 0, 8), STONE)))
            bpy_o.location = (ox + sx + (i % 3), -i * 1.0 + 4, 0)
    lb = bpy.data.curves.new(f"RB410 label {take}", "FONT"); lb.body = f"{take}  {NAMES[take]}"; lb.size = 1.4
    lb.align_x = "CENTER"
    tl = link(bpy.data.objects.new(f"RB410 label {take}", lb)); tl.location = (ox, 8.0, 0.05); tl.data.materials.append(LABEL)
    # cameras ride the mover: chase (behind, above, like the game's third person) and side
    scene.frame_set(1); bpy.context.view_layer.update()
    st = np.array([ox, 0.0, 9.0])
    c = cam(f"Cam {take}", tuple(st + np.array([1.2, 8.5, 2.6])), tuple(st + np.array([0.0, -5.0, 0.6])), 28)
    c.parent = mover; c.matrix_parent_inverse = mover.matrix_world.inverted()
    cc = cam(f"Cam {take} side", tuple(st + np.array([9.0, -1.5, 1.6])), tuple(st + np.array([0, -1.8, 0.9])), 30)
    cc.parent = mover; cc.matrix_parent_inverse = mover.matrix_world.inverted()
    fpc = link(bpy.data.objects.new(f"Cam {take} fp", bpy.data.cameras.new(f"Cam {take} fp")))
    fpc.data.sensor_fit = "HORIZONTAL"; fpc.data.angle_x = R(120); fpc.data.clip_start = 0.05
    fpc.parent = objs["head"]; fpc.matrix_parent_inverse.identity()
    fpc.location = (0.0, -0.32, 0.27); fpc.rotation_euler = (R(90), 0, R(180))
    print(take, "built", flush=True)


for o in scene.objects:
    ad = o.animation_data
    if ad and ad.action:
        try:
            for fc in ad.action.fcurves:
                for kp in fc.keyframe_points:
                    kp.interpolation = "LINEAR"
        except Exception:
            pass
        try:   # Blender 5 layered actions
            for lay in ad.action.layers:
                for strip in lay.strips:
                    for cb in strip.channelbags:
                        for fc in cb.fcurves:
                            for kp in fc.keyframe_points:
                                kp.interpolation = "LINEAR"
        except Exception:
            pass

scene.frame_start, scene.frame_end = 1, T_END
bpy.ops.mesh.primitive_plane_add(size=1, location=(LANE * 1.0, -60, 0))
g = bpy.context.active_object
for c in g.users_collection:
    c.objects.unlink(g)
link(g); g.name = "RB410 ground"; g.scale = (500, 500, 1)
gm = bpy.data.materials.new("RB410 ground"); gm.use_nodes = True
N_, Lk = gm.node_tree.nodes, gm.node_tree.links
ck = N_.new("ShaderNodeTexChecker"); ck.inputs["Scale"].default_value = 500
ck.inputs["Color1"].default_value = (0.2, 0.36, 0.13, 1); ck.inputs["Color2"].default_value = (0.24, 0.42, 0.16, 1)
Lk.new(ck.outputs["Color"], N_.get("Principled BSDF").inputs["Base Color"])
g.data.materials.append(gm)
world = bpy.data.worlds.new("RB410 world"); world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.35, 0.45, 0.6, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.6
scene.world = world
sun = link(bpy.data.objects.new("RB410 sun", bpy.data.lights.new("RB410 sun", "SUN")))
sun.data.energy = 3.0; sun.rotation_euler = (R(50), R(-10), R(-35))
try:
    scene.render.engine = "BLENDER_EEVEE"
except Exception:
    scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x, scene.render.resolution_y = 1600, 900
try:
    scene.view_settings.view_transform = "Standard"
except Exception:
    pass
scene.camera = bpy.data.objects["Cam P1a"]
try:
    bpy.ops.outliner.orphans_purge(do_recursive=True)
except Exception:
    pass
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("saved", OUT)
