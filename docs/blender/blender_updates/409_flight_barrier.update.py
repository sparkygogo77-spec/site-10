# Pass 409: the flight barrier and trail, fast vs primed (coordinator, movement range, 2026-10-15). J, in game:
# "the barrier when im flying and primed as well as the trail should look better or different from the fast flying
# activation". In game both fast flight and primed flight draw the same placeholder cap (RamBarrierFx: a pale cracked
# shockwave-glass dome; its bbmodel hook ram_barrier.bbmodel was never filled).
#   F  = fast flight, not primed: a thin W1-weave cap the Dome's size (4.5 blocks) with a bright rim, one quiet ribbon.
#   P1 = primed: a six-sided hex lance point round the flyer (lit edges, turning slowly one way) + a twin helix trail.
#   P2 = primed: a domed shield of separate hex plates 1.8 blocks ahead (breathing) + hex afterimage rings every 4 ticks.
#   P3 = primed: a bullet nose of construct pixels round a dark core + a tail of pixels shrinking out over 0.9 s.
#        (rev 4, J: "need better constructs and textures": the nose is now a shell of staggered dark-jade bevelled
#        construct bricks over glowing mortar, a lit tip, and the tail is made of the same bricks and flecks.)
# Every P lane flies 2 s as F, primes at tick 40 (the cap folds away in 4 ticks, the primed look snaps on with a small
# overshoot and a flash ring), then flies 4 s primed. Fast flat glide at 1 block a tick, ring arm leading.
# Cameras: "Cam F|P1|P2|P3" (chase, like the game's third person), "Cam <take> side". First person: the head eye camera.
import json, math, os
import bpy
import numpy as np
from mathutils import Matrix

R = math.radians
OUT = os.path.join(FOLDER, "flight_barrier.blend")
if bpy.data.filepath:
    try:
        bpy.ops.wm.save_mainfile()
    except Exception as e:
        print("save current:", e)
old = bpy.data.scenes.get("Flight Barrier")
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new("Flight Barrier")
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




# ================================================================== pass 409: flight barriers and trails
import bmesh, random

T_END = 120
T_PRIME = 40                 # the tick the flyer primes (shift) in the P lanes
V = 1.0                      # blocks a tick: fast flight (the ram barrier only shows at speed)
LEAD = 1.6
KEYS = [(0, 0), (30, 0), (50, 12), (70, 12), (90, -10), (120, -10)]   # (tick, heading deg clockwise)
TAKES = ["F", "P1", "P2", "P3"]
NAMES = {"F": "fast flight barrier (not primed)", "P1": "primed: hex lance + twin helix trail",
         "P2": "primed: hex ram shield + afterimage rings", "P3": "primed: comet nose + pixel tail"}
GREEN = (0.10, 1.0, 0.30)
DEEP = (0.02, 0.35, 0.10)
LIME = (0.45, 1.0, 0.25)
random.seed(409)


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
    Primed (P lanes after T_PRIME): the free arm pulls in tight and the legs close up, a little more tucked."""
    p = dict(GLIDE)
    primed = take != "F" and t >= T_PRIME
    k = smooth(min(1.0, max(0.0, (t - T_PRIME) / 4.0))) if take != "F" else 0.0
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


M_CAP = cmat("RB409 cap weave", "weave", GREEN, 0.16, 1.0, 5.0)
M_RIM = cmat("RB409 rim", "solid", GREEN, 0.8, 2.5)
M_LANCE = cmat("RB409 lance hex", "hex", GREEN, 0.22, 1.6, 3.0)
M_EDGE = cmat("RB409 lance edge", "solid", GREEN, 0.9, 3.0)
M_SHIELD = cmat("RB409 shield hex", "hex", GREEN, 0.35, 1.8, 2.5)
M_RING = cmat("RB409 afterimage", "solid", GREEN, 0.6, 2.0)
M_CORE = cmat("RB409 dark core", "solid", DEEP, 0.75, 0.6)
M_PIX = [cmat(f"RB409 pixel {i}", "solid", c, 0.75, e) for i, (c, e) in
         enumerate((((0.10, 1.0, 0.30), 1.3), ((0.04, 0.70, 0.20), 1.0), ((0.30, 1.0, 0.35), 1.6), ((0.02, 0.45, 0.12), 0.6)),
                   start=1)]
M_TILE = [cmat(f"RB409 brick {i}", "solid", c, 0.82, e) for i, (c, e) in
          enumerate((((0.03, 0.42, 0.16), 0.35), ((0.02, 0.30, 0.12), 0.25), ((0.05, 0.55, 0.20), 0.5)), start=1)]
M_MORTAR = cmat("RB409 mortar", "solid", GREEN, 0.5, 1.9)
M_TRAIL = cmat("RB409 trail", "solid", GREEN, 0.7, 2.5)
M_FLASH = cmat("RB409 prime flash", "solid", LIME, 0.5, 3.5)
STONE = mat("RB409 stone", (0.32, 0.32, 0.34)); LABEL = mat("RB409 label", (0.85, 1.0, 0.9), emit=2.0)


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


def cube_mesh(name, s, m):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=s)
    return mesh_from_bm(name, bm, m)


def lance_meshes():
    """P1: a six-sided hard-light lance point round the flyer: apex 3 blocks ahead, wide end at the hips."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=False, segments=6, radius1=1.15, radius2=0.0, depth=2.8)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(R(90), 3, "X"))   # apex to -Y
    bmesh.ops.translate(bm, verts=bm.verts, vec=(0, -2.3, 0))
    edge_bm = bm.copy()
    body = mesh_from_bm("RB409 lance", bm, M_LANCE)
    ebm = edge_bm; me = bpy.data.meshes.new("RB409 lance edges"); ebm.to_mesh(me); ebm.free(); me.materials.append(M_EDGE)
    return body, me


def shield_mesh():
    """P2: a slightly domed disc of separate hex plates, 1.8 blocks ahead, facing forward."""
    bm = bmesh.new(); size = 0.33; gap = 0.04
    for q in range(-3, 4):
        for r_ in range(-3, 4):
            s_ = -q - r_
            if max(abs(q), abs(r_), abs(s_)) > 3:
                continue
            x = size * 1.732 * (q + r_ / 2.0); z = size * 1.5 * r_
            d = math.hypot(x, z)
            y = -1.8 + 0.12 * d * d                     # domed: the middle leads
            ret = bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=size - gap, radius2=size - gap, depth=0.07)
            vs = ret["verts"]
            bmesh.ops.rotate(bm, verts=vs, cent=(0, 0, 0), matrix=Matrix.Rotation(R(90), 3, "X"))
            bmesh.ops.translate(bm, verts=vs, vec=(x, y, z))
    return mesh_from_bm("RB409 shield", bm, M_SHIELD)


def hex_ring_curve(name, r, m):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 0.035
    sp = cu.splines.new("POLY"); sp.points.add(5); sp.use_cyclic_u = True
    for i in range(6):
        a = 2 * math.pi * i / 6 + math.pi / 6
        sp.points[i].co = (r * math.cos(a), 0, r * math.sin(a), 1)
    cu.materials.append(m)
    return cu


NOSE_Y0, NOSE_LEN, NOSE_R = -1.9, 2.4, 1.05


def nose_r(u):
    """The bullet's profile: radius at u (0 = base, 1 = tip), a round ogive."""
    return NOSE_R * max(0.0, 1.0 - u ** 1.9) ** 0.62


def nose_pt(u, th):
    r = nose_r(u)
    return np.array([r * math.cos(th), NOSE_Y0 - u * NOSE_LEN, r * math.sin(th)])


def nose_meshes():
    """P3 (rev 4): the bullet nose as a shell of staggered, bevelled construct bricks (dark jade, three tones) standing
    0.03 off a glowing mortar surface, a lit tip cone, a hollow base. Returns (bricks, mortar, tip)."""
    bm = bmesh.new(); mm = bmesh.new()
    courses = 12; umax = 0.94
    for c in range(courses):
        u = umax * (c + 0.5) / courses
        r = nose_r(u)
        n = max(4, int(round(2 * math.pi * r / 0.25)))
        du = umax / courses
        ds = max(0.05, np.linalg.norm(nose_pt(u + du / 2, 0) - nose_pt(u - du / 2, 0)))
        for k in range(n):
            th = 2 * math.pi * (k + 0.5 * (c % 2)) / n
            ctr = nose_pt(u, th)
            ax = nose_pt(u + 0.01, th) - nose_pt(u - 0.01, th); ax /= np.linalg.norm(ax)
            tg = np.array([-math.sin(th), 0.0, math.cos(th)])
            nr = np.cross(tg, ax); nr /= np.linalg.norm(nr)
            if nr @ np.array([math.cos(th), 0.0, math.sin(th)]) < 0:
                nr = -nr
            tg = np.cross(ax, nr)
            wd = 2 * math.pi * r / n * 0.84; ht = ds * 0.86
            ret = bmesh.ops.create_cube(bm, size=1.0)
            tone = random.choice((0, 0, 1, 2))
            M = np.eye(4); M[:3, 0] = tg * wd; M[:3, 1] = ax * ht; M[:3, 2] = nr * 0.05; M[:3, 3] = ctr + nr * 0.045
            bmesh.ops.transform(bm, verts=ret["verts"], matrix=Matrix(M.tolist()))
            for f in {f for v in ret["verts"] for f in v.link_faces}:
                f.material_index = tone
    # mortar: the surface of revolution under the bricks
    rings = []
    for i in range(0, 25):
        u = umax * i / 24
        rings.append([mm.verts.new(tuple(nose_pt(u, 2 * math.pi * j / 32))) for j in range(32)])
    for i in range(24):
        for j in range(32):
            mm.faces.new((rings[i][j], rings[i][(j + 1) % 32], rings[i + 1][(j + 1) % 32], rings[i + 1][j]))
    tip = bmesh.new()
    bmesh.ops.create_cone(tip, cap_ends=False, segments=8, radius1=nose_r(umax) + 0.02, radius2=0.0,
                          depth=NOSE_LEN * (1 - umax) + 0.02)
    bmesh.ops.rotate(tip, verts=tip.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(R(90), 3, "X"))
    bmesh.ops.translate(tip, verts=tip.verts, vec=(0, NOSE_Y0 - NOSE_LEN * (1 + umax) / 2 - 0.005, 0))
    br = bpy.data.meshes.new("RB409 nose bricks"); bm.to_mesh(br); bm.free()
    for m_ in M_TILE:
        br.materials.append(m_)
    return br, mesh_from_bm("RB409 nose mortar", mm, M_MORTAR), mesh_from_bm("RB409 nose tip", tip, M_EDGE)


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


# ------------------------------------------------------------------ glow (compositor bloom), shared meshes
try:
    tree = bpy.data.node_groups.new("RB409 Glow", "CompositorNodeTree")
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

CAP = cap_mesh("RB409 cap", 4.5, 38, M_CAP)
RIM = ring_curve("RB409 cap rim", 4.5 * math.sin(R(38)), M_RIM, 0.06, y=-4.5 * math.cos(R(38)))
LANCE, LANCE_E = lance_meshes()
SHIELD = shield_mesh()
SH_RIM = hex_ring_curve("RB409 shield rim", 1.25, M_RING)
AFTER = hex_ring_curve("RB409 afterimage", 1.25, M_RING)
NOSE, NOSE_MORTAR, NOSE_TIP = nose_meshes()
CORE = bpy.data.meshes.new("RB409 core")
_bm = bmesh.new(); bmesh.ops.create_icosphere(_bm, subdivisions=2, radius=0.45); _bm.to_mesh(CORE); _bm.free()
CORE.materials.append(M_CORE)
_bm = bmesh.new(); bmesh.ops.create_cube(_bm, size=1.0)
bmesh.ops.scale(_bm, vec=(0.09, 1.05, 0.09), verts=_bm.verts)
TRAIL_BITS = mesh_from_bm("RB409 trail strip", _bm, M_TRAIL)
def brick_mesh(name, size, m):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=size, verts=bm.verts)
    return mesh_from_bm(name, bm, m)


# tail: three sizes of bevel-less construct bricks in the nose's jade tones, plus bright flecks
PIX = [brick_mesh("RB409 tail brick 1", (0.22, 0.13, 0.07), M_TILE[0]), brick_mesh("RB409 tail brick 2", (0.16, 0.10, 0.06), M_TILE[2]),
       brick_mesh("RB409 tail brick 3", (0.28, 0.12, 0.07), M_TILE[1]), cube_mesh("RB409 tail fleck", 0.08, M_PIX[2])]
FLASH = ring_curve("RB409 flash", 1.0, M_FLASH, 0.05)


def parented(name, data, mover, local=(0, 0, 0)):
    o = link(bpy.data.objects.new(name, data)); o.parent = mover; o.location = local; o.rotation_mode = "XYZ"
    return o


LANE = 70.0
for li, take in enumerate(TAKES):
    ox = li * LANE
    objs = make_player(take)
    rm = mat(f"RB409 ring {take}", (0.1, 1.0, 0.25), emit=6.0); objs["ring"].data.materials[0] = rm
    mover = link(bpy.data.objects.new(f"RB409 {take} mover", None)); mover.empty_display_size = 0.1
    mover.rotation_mode = "XYZ"
    chest = (0, 0, 1.0)
    # the fast-flight cap (all lanes) and this lane's primed look, both riding the mover
    cap = parented(f"RB409 {take} fast cap", CAP, mover, chest)
    rim = parented(f"RB409 {take} fast cap rim", RIM, mover, chest)
    primed = []
    if take == "P1":
        primed = [parented(f"RB409 {take} lance", LANCE, mover, chest)]
        e = parented(f"RB409 {take} lance edges", LANCE_E, mover, chest)
        wf = e.modifiers.new("edges", "WIREFRAME"); wf.thickness = 0.03; wf.use_replace = True
        primed.append(e)
    elif take == "P2":
        primed = [parented(f"RB409 {take} shield", SHIELD, mover, chest)]
        r2 = parented(f"RB409 {take} shield rim", SH_RIM, mover, (0, -1.85 + 0.0, 1.0)); r2.scale = (1.9, 1, 1.9)
        primed.append(r2)
    elif take == "P3":
        nb = parented(f"RB409 {take} nose", NOSE, mover, chest)
        bv = nb.modifiers.new("bevel", "BEVEL"); bv.width = 0.012; bv.segments = 2
        primed = [nb, parented(f"RB409 {take} nose mortar", NOSE_MORTAR, mover, chest),
                  parented(f"RB409 {take} nose tip", NOSE_TIP, mover, chest),
                  parented(f"RB409 {take} core", CORE, mover, (0, -3.1, 1.0))]
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
        foot = W @ (to_bl(hand_point(sol, "larm")) - np.array(chest)) + np.array(chest) + pos
        is_primed = take != "F" and t >= T_PRIME
        # trails
        if not is_primed:
            # fast flight: one thin ribbon off the ring fist (today's T4-style trail, quiet)
            spawn(f"RB409 {take} trail {t}", TRAIL_BITS, hand + 0.3 * fwd, phi, f, 8, 1.0, -0.02 * fwd)
        elif take == "P1":
            # twin helix: two ribbons winding round the travel line behind the flyer
            for k_ in (0, 1):
                a = 0.45 * t + math.pi * k_
                side = Rz(phi) @ np.array([math.cos(a) * 0.7, 0.0, 0.0]) + np.array([0, 0, math.sin(a) * 0.7])
                spawn(f"RB409 {take} helix {k_} {t}", TRAIL_BITS, pos + np.array(chest) + side - 0.8 * fwd, phi, f, 14, 1.2)
        elif take == "P2" and (t - T_PRIME) % 4 == 0:
            o = spawn(f"RB409 {take} afterimage {t}", AFTER, pos + np.array(chest) - 1.2 * fwd, phi, f, 10, 1.1)
        elif take == "P3":
            for k_ in range(2):
                j = np.array([random.uniform(-0.5, 0.5), 0, random.uniform(-0.5, 0.5)])
                spawn(f"RB409 {take} tail {t} {k_}", PIX[random.choice((0, 0, 1, 2, 3))], pos + np.array(chest) + Rz(phi) @ j
                      - random.uniform(0.6, 1.6) * fwd, phi + random.uniform(-0.6, 0.6), f, 18,
                      random.uniform(0.5, 0.9), -0.05 * fwd + Rz(phi) @ (j * 0.03))
    # the switch: fast cap folds away in 4 ticks, the primed look snaps on with a small overshoot and a flash
    for o in (cap, rim):
        key_scale(o, 1, 1.0)
        if take != "F":
            key_scale(o, T_PRIME + 1, 1.0); key_scale(o, T_PRIME + 5, 0.0)
    for o in primed:
        base = tuple(o.scale)
        key_scale(o, 1, (0.0, 0.0, 0.0)); key_scale(o, T_PRIME + 1, (0.0, 0.0, 0.0))
        key_scale(o, T_PRIME + 4, tuple(b * 1.15 for b in base)); key_scale(o, T_PRIME + 7, base)
        if "lance" in o.name:                     # the lance turns slowly about the travel line (one way)
            for fr in range(T_PRIME + 1, T_END + 2, 10):
                o.rotation_euler = (0, R(6.0) * (fr - T_PRIME), 0); o.keyframe_insert("rotation_euler", frame=fr)
        if "shield" in o.name and "rim" not in o.name:   # the plates breathe
            for fr in range(T_PRIME + 10, T_END + 2, 10):
                s = 1.04 if (fr // 10) % 2 else 1.0
                key_scale(o, fr, (s, s, s))
        if "nose" in o.name:                      # the pixels shimmer round
            for fr in range(T_PRIME + 1, T_END + 2, 10):
                o.rotation_euler = (0, R(4.0) * (fr - T_PRIME), 0); o.keyframe_insert("rotation_euler", frame=fr)
    if take != "F":
        scene.frame_set(T_PRIME + 1); bpy.context.view_layer.update()
        fl = link(bpy.data.objects.new(f"RB409 {take} prime flash", FLASH)); fl.parent = mover; fl.location = (0, -0.5, 1.0)
        key_scale(fl, 1, 0.0); key_scale(fl, T_PRIME, 0.0); key_scale(fl, T_PRIME + 1, 0.6); key_scale(fl, T_PRIME + 6, 4.0)
        key_scale(fl, T_PRIME + 7, 0.0)
    # speed markers: stone pillars either side of the lane
    for i in range(0, 130, 10):
        for sx in (-7, 7):
            h = 2 + (i * 7 + sx) % 5
            bpy_o = link(bpy.data.objects.new(f"RB409 {take} pillar {i} {sx}",
                                               box_mesh(f"RB409 pillar {take} {i} {sx}", (-8, -16 * h, -8), (8, 0, 8), STONE)))
            bpy_o.location = (ox + sx + (i % 3), -i * 1.0 + 4, 0)
    lb = bpy.data.curves.new(f"RB409 label {take}", "FONT"); lb.body = f"{take}  {NAMES[take]}"; lb.size = 1.4
    lb.align_x = "CENTER"
    tl = link(bpy.data.objects.new(f"RB409 label {take}", lb)); tl.location = (ox, 8.0, 0.05); tl.data.materials.append(LABEL)
    # cameras ride the mover: chase (behind, above, like the game's third person) and side
    scene.frame_set(1); bpy.context.view_layer.update()
    st = np.array([ox, 0.0, 9.0])
    c = cam(f"Cam {take}", tuple(st + np.array([1.2, 8.5, 2.6])), tuple(st + np.array([0.0, -5.0, 0.6])), 28)
    c.parent = mover; c.matrix_parent_inverse = mover.matrix_world.inverted()
    cc = cam(f"Cam {take} side", tuple(st + np.array([9.0, -1.5, 1.6])), tuple(st + np.array([0, -1.8, 0.9])), 30)
    cc.parent = mover; cc.matrix_parent_inverse = mover.matrix_world.inverted()
    # first person: an eye camera just in front of the face (the renderer's head camera sits where the flat glide's
    # arm isn't in view, so it skipped these clips); 120 degrees wide like the game
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
bpy.ops.mesh.primitive_plane_add(size=1, location=(LANE * 1.5, -60, 0))
g = bpy.context.active_object
for c in g.users_collection:
    c.objects.unlink(g)
link(g); g.name = "RB409 ground"; g.scale = (500, 500, 1)
gm = bpy.data.materials.new("RB409 ground"); gm.use_nodes = True
N_, Lk = gm.node_tree.nodes, gm.node_tree.links
ck = N_.new("ShaderNodeTexChecker"); ck.inputs["Scale"].default_value = 500
ck.inputs["Color1"].default_value = (0.2, 0.36, 0.13, 1); ck.inputs["Color2"].default_value = (0.24, 0.42, 0.16, 1)
Lk.new(ck.outputs["Color"], N_.get("Principled BSDF").inputs["Base Color"])
g.data.materials.append(gm)
world = bpy.data.worlds.new("RB409 world"); world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.35, 0.45, 0.6, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.6
scene.world = world
sun = link(bpy.data.objects.new("RB409 sun", bpy.data.lights.new("RB409 sun", "SUN")))
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
scene.camera = bpy.data.objects["Cam P1"]
try:
    bpy.ops.outliner.orphans_purge(do_recursive=True)
except Exception:
    pass
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("saved", OUT)
