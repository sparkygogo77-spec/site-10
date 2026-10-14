# Pass 225: omega beams, round 3 (lead Blender chat, 2026-10-14). J picked "eye flash and lock-in variations", and for
# letting go mid-chase: "keep going straight". Two beams a use, one per eye, as J chose. Five takes, each a different
# start, side by side:
#   E1 snap: a hard white-red flash, the head snaps onto the target, the body freezes mid-step, beams out at once.
#   E2 smoulder: the eyes build up over a second, red smoke curling off them, then fire.
#   E3 air brake: flying in fast, he pitches back upright to brake, hangs in the air and fires down.
#   E4 crackle: little red lightning arcs jump round the eyes before the beams leave.
#   E5 let go: the beams chase a runner; the key is let go halfway and the beams fly on straight, burning the wall
#      past the runner instead (J's rule).
# Cameras "Cam E1".."Cam E5" (over the right shoulder), "Cam E1 face".. (close on the face). Builds LanternLive\omega_beams3.blend.
import heapq
import json, math, os
import bpy
import numpy as np
from mathutils import Matrix

R = math.radians
ASSETS = os.path.join(FOLDER, "kl_assets")
OUT = os.path.join(FOLDER, "omega_beams3.blend")
if bpy.data.filepath:
    try:
        bpy.ops.wm.save_mainfile()
    except Exception as e:
        print("save current:", e)
old = bpy.data.scenes.get("Omega Beams 3")
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new("Omega Beams 3")
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


def emis(name, rgb, strength, alpha=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    out = N.get("Material Output"); N.remove(N.get("Principled BSDF"))
    e = N.new("ShaderNodeEmission"); e.inputs["Color"].default_value = (*rgb, 1); e.inputs["Strength"].default_value = strength
    if alpha < 1:
        tr = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader"); mx.inputs["Fac"].default_value = alpha
        L.new(tr.outputs[0], mx.inputs[1]); L.new(e.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs["Surface"])
        try:
            m.surface_render_method = "BLENDED"
        except Exception:
            pass
    else:
        L.new(e.outputs[0], out.inputs["Surface"])
    return m, e


def cube(name, m, size):
    me = bpy.data.meshes.new(name); h = size / 2
    me.from_pydata([(x, y, z) for x in (-h, h) for y in (-h, h) for z in (-h, h)], [],
                   [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)])
    me.materials.append(m)
    return link(bpy.data.objects.new(name, me))


SEED = 225
rng = np.random.default_rng(SEED)
END = 110
RED = (1.0, 0.06, 0.03)


def emis(name, rgb, strength, alpha=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    out = N.get("Material Output"); N.remove(N.get("Principled BSDF"))
    e = N.new("ShaderNodeEmission"); e.inputs["Color"].default_value = (*rgb, 1); e.inputs["Strength"].default_value = strength
    if alpha < 1:
        tr = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader"); mx.inputs["Fac"].default_value = alpha
        L.new(tr.outputs[0], mx.inputs[1]); L.new(e.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs["Surface"])
        try:
            m.surface_render_method = "BLENDED"
        except Exception:
            pass
    else:
        L.new(e.outputs[0], out.inputs["Surface"])
    return m, e


def cube(name, m, size=1.0):
    me = bpy.data.meshes.new(name); h = size / 2
    me.from_pydata([(x, y, z) for x in (-h, h) for y in (-h, h) for z in (-h, h)], [],
                   [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)])
    me.materials.append(m)
    return link(bpy.data.objects.new(name, me))


def keyo(o, f, loc=None, scale=None, rot=None):
    if loc is not None:
        o.location = tuple(loc); o.keyframe_insert("location", frame=f)
    if scale is not None:
        o.scale = tuple(scale); o.keyframe_insert("scale", frame=f)
    if rot is not None:
        o.rotation_euler = tuple(rot); o.keyframe_insert("rotation_euler", frame=f)


def catmull(pts, n=120):
    pts = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = (np.asarray(pts[j], float) for j in (i - 1, i, i + 1, i + 2))
        for u in np.linspace(0, 1, n // (len(pts) - 3), endpoint=False):
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3))
    out.append(np.asarray(pts[-2], float))
    return np.array(out)


def beam_path(start, end):
    """An irregular path: 2-4 waypoints thrown off the straight line, and a random final approach direction."""
    d = end - start; L_ = float(np.linalg.norm(d))
    n_w = int(rng.integers(2, 5))
    pts = [start]
    for i in range(1, n_w + 1):
        u = i / (n_w + 1)
        off = rng.normal(0, 0.28 * L_, 3); off[2] = abs(off[2]) * 0.6 + rng.normal(0, 0.1 * L_)
        pts.append(start + d * u + off)
    app = rng.normal(0, 1, 3); app /= np.linalg.norm(app)
    if np.dot(app, -d) < -0.2:
        app = -app
    pts.append(end + app * min(1.5, 0.25 * L_))            # comes in from any side
    pts.append(end)
    path = catmull(pts, 160)
    seg = np.linalg.norm(np.diff(path, axis=0), axis=1)
    cum = np.concatenate([[0], np.cumsum(seg)])
    return path, cum


def point_on(path, cum, s):
    s = min(max(s, 0.0), cum[-1])
    i = int(np.searchsorted(cum, s)) - 1; i = min(max(i, 0), len(path) - 2)
    u = (s - cum[i]) / max(1e-6, cum[i + 1] - cum[i])
    return path[i] + (path[i + 1] - path[i]) * u


BEAM_M, _ = emis("OB beam", RED, 7.0)      # strong enough to glow, low enough to stay red
EMBER_M, _ = emis("OB ember", (1.0, 0.35, 0.05), 12.0)
ASH_M = mat("OB ash", (0.12, 0.11, 0.1))
STONE_M = mat("OB stone", (0.42, 0.42, 0.44))
MOB_M = mat("OB mob", (0.25, 0.55, 0.25))


def target_block(name, at, size=1.0, m=STONE_M):
    o = cube(name, m, size); o.location = tuple(at)
    return o


def incinerate(o, at, hit, size=1.0):
    """At tick `hit` the thing turns to embers, glows, crumbles and drifts away as ash."""
    keyo(o, 1, scale=(1, 1, 1)); keyo(o, hit, scale=(1, 1, 1)); keyo(o, hit + 2, scale=(0, 0, 0))
    em = cube(o.name + " ember", EMBER_M, size); em.location = tuple(at)
    keyo(em, 1, scale=(0, 0, 0)); keyo(em, hit, scale=(0, 0, 0)); keyo(em, hit + 1, scale=(1.02, 1.02, 1.02))
    keyo(em, hit + 8, scale=(0.9, 0.9, 0.8)); keyo(em, hit + 18, scale=(0, 0, 0))
    lt = bpy.data.lights.new(o.name + " glow", "POINT"); lt.color = (1.0, 0.35, 0.08); lt.shadow_soft_size = 0.4
    lo = link(bpy.data.objects.new(o.name + " glow", lt)); lo.location = tuple(at)
    for f, e in ((1, 0), (hit, 0), (hit + 1, 350 * size), (hit + 12, 120 * size), (hit + 20, 0)):
        lt.energy = e; lt.keyframe_insert("energy", frame=f)
    for i in range(6):
        a = cube(o.name + f" ash {i}", ASH_M, 0.12 * size)
        p0 = np.asarray(at) + rng.uniform(-0.4, 0.4, 3) * size
        keyo(a, 1, loc=p0, scale=(0, 0, 0)); keyo(a, hit + 8, loc=p0, scale=(0, 0, 0))
        for j in range(1, 25):
            keyo(a, hit + 8 + j, loc=p0 + np.array([rng.normal(0, 0.01), rng.normal(0, 0.01), 0.03 * j]),
                 scale=(max(0, 1 - j / 24),) * 3)


def fire_beam(tag, start_fn, end, t0, speed=0.9, tail=1.4, nseg=14):
    """One laser from start_fn(t0) to end along its own path; head travels `speed` blocks a tick."""
    st = start_fn(t0)
    path, cum = beam_path(st, np.asarray(end, float))
    total = cum[-1]
    t_hit = t0 + int(math.ceil(total / speed))
    segs = [cube(f"{tag} seg {i}", BEAM_M, 1.0) for i in range(nseg)]
    lt = bpy.data.lights.new(tag + " light", "POINT"); lt.color = RED; lt.shadow_soft_size = 0.1
    lo = link(bpy.data.objects.new(tag + " light", lt))
    for t in range(1, END + 1):
        sh = (t - t0) * speed
        live = t0 <= t <= t_hit + int(tail / speed) + 1
        for i, sg in enumerate(segs):
            a = sh - tail * i / nseg; b = sh - tail * (i + 1) / nseg
            if not live or a < 0 or b > total:
                keyo(sg, t, scale=(0, 0, 0)); continue
            pa, pb = point_on(path, cum, a), point_on(path, cum, max(b, 0))
            mid = (pa + pb) / 2; v = pa - pb; ln = float(np.linalg.norm(v))
            if ln < 1e-4:
                keyo(sg, t, scale=(0, 0, 0)); continue
            yaw = math.atan2(v[1], v[0]); pitch = math.atan2(v[2], math.hypot(v[0], v[1]))
            w = 0.05 * (1 - 0.6 * i / nseg)
            keyo(sg, t, loc=mid, scale=(ln, w, w), rot=(0, -pitch, yaw))
        lo.location = tuple(point_on(path, cum, min(sh, total))); lo.keyframe_insert("location", frame=t)
        lt.energy = 60.0 if live else 0.0; lt.keyframe_insert("energy", frame=t)
    return t_hit


LOCK = dict(body=(0.0, 0, 0), head=(0.0, 0, 0), ring=(0.15, 0, 0.25), free=(0.15, 0, -0.25),
            ringleg=(0.2, 0, 0.12), ringknee=0.15, freeleg=(-0.15, 0, -0.12), freeknee=0.15)
FLYING = dict(body=(1.42, 0, 0), head=(-1.25, 0, 0), ring=(-1.57, 0, 0.02), free=(1.35, 0, -0.12),
              ringleg=(1.38, 0, 0.03), ringknee=0.25, freeleg=(1.3, 0, -0.03), freeknee=0.4, grounded=False)
HOVER = dict(body=(0.15, 0, 0), head=(0.55, 0, 0), ring=(0.3, 0, 0.45), free=(0.3, 0, -0.45),
             ringleg=(0.15, 0, 0.06), ringknee=0.5, freeleg=(-0.1, 0, -0.06), freeknee=0.35, grounded=False)
EYE_M = {}


def add_eyes(objs, tag):
    em, node = emis(f"OB eyes {tag}", RED, 0.0)
    EYE_M[tag] = node
    for x0, x1 in ((-3.0, -1.0), (1.0, 3.0)):
        me = box_mesh(f"OB {tag} eye {x0}", (x0, -4.7, -4.2), (x1, -3.7, -4.1), em)
        o = link(bpy.data.objects.new(f"OB {tag} eye {x0}", me)); o.parent = objs["head"]
    return node


def eye_flash(tag, t_flash, t_end):
    s_ = EYE_M[tag].inputs["Strength"]
    for f, e in ((1, 0), (t_flash, 0), (t_flash + 2, 60), (t_flash + 5, 25), (t_end, 25), (t_end + 6, 0), (END, 0)):
        s_.default_value = e; s_.keyframe_insert("default_value", frame=f)


def eye_world(sol, origin, side=0.0, which=0):
    r, pv = sol["head"]
    local = np.array([-2.0 if which == 0 else 2.0, -4.2, -4.2])
    return to_bl(local @ rot(*r).T + pv) + origin



def fire_path(tag, path, t0, speed=0.85, tail=1.4, nseg=14, end_cb=None):
    """A laser along a given path (n,3)."""
    path = np.asarray(path, float)
    seg = np.linalg.norm(np.diff(path, axis=0), axis=1)
    cum = np.concatenate([[0], np.cumsum(seg)])
    total = cum[-1]
    t_hit = t0 + int(math.ceil(total / speed))
    segs = [cube(f"{tag} seg {i}", BEAM_M, 1.0) for i in range(nseg)]
    lt = bpy.data.lights.new(tag + " light", "POINT"); lt.color = RED; lt.shadow_soft_size = 0.1
    lo = link(bpy.data.objects.new(tag + " light", lt))
    for t in range(1, END + 1):
        sh = (t - t0) * speed
        live = t0 <= t <= t_hit + int(tail / speed) + 1
        for i, sg in enumerate(segs):
            a = sh - tail * i / nseg; b = sh - tail * (i + 1) / nseg
            if not live or a < 0 or b > total:
                keyo(sg, t, scale=(0, 0, 0)); continue
            pa, pb = point_on(path, cum, a), point_on(path, cum, max(b, 0))
            mid = (pa + pb) / 2; v = pa - pb; ln = float(np.linalg.norm(v))
            if ln < 1e-4:
                keyo(sg, t, scale=(0, 0, 0)); continue
            yaw = math.atan2(v[1], v[0]); pitch = math.atan2(v[2], math.hypot(v[0], v[1]))
            w = 0.05 * (1 - 0.6 * i / nseg)
            keyo(sg, t, loc=mid, scale=(ln, w, w), rot=(0, -pitch, yaw))
        lo.location = tuple(point_on(path, cum, min(sh, total))); lo.keyframe_insert("location", frame=t)
        lt.energy = 60.0 if live else 0.0; lt.keyframe_insert("energy", frame=t)
    return t_hit


def astar(start, goal, solid, lo, hi, step=0.5):
    """A* over a half-block grid inside [lo, hi], avoiding cells for which solid(p) is true."""
    def cell(p):
        return tuple(np.round((np.asarray(p) - lo) / step).astype(int))

    def pos(c):
        return lo + np.array(c) * step
    shape = tuple(np.round((hi - lo) / step).astype(int) + 1)
    s, g = cell(start), cell(goal)
    nbrs = [(dx, dy, dz) for dx in (-1, 0, 1) for dy in (-1, 0, 1) for dz in (-1, 0, 1) if (dx, dy, dz) != (0, 0, 0)]
    openh = [(0.0, s)]; came = {s: None}; gs = {s: 0.0}
    while openh:
        _, c = heapq.heappop(openh)
        if c == g:
            break
        for d in nbrs:
            n = (c[0] + d[0], c[1] + d[1], c[2] + d[2])
            if not all(0 <= n[i] < shape[i] for i in range(3)):
                continue
            if n != g and solid(pos(n)):
                continue
            ng = gs[c] + math.sqrt(d[0] ** 2 + d[1] ** 2 + d[2] ** 2) * (1 + 0.6 * rng.random())   # a little wander
            if ng < gs.get(n, 1e9):
                gs[n] = ng; came[n] = c
                heapq.heappush(openh, (ng + 0.95 * math.dist(n, g), n))
    path = []
    c = g if g in came else s
    while c is not None:
        path.append(pos(c)); c = came[c]
    return path[::-1]


def thin(path, keep=5):
    """Keep a handful of the A* cells as waypoints, jitter them a little, and smooth."""
    if len(path) <= 2:
        return np.array(path)
    idx = np.linspace(0, len(path) - 1, min(len(path), keep + 2)).astype(int)
    pts = [path[i] + (rng.normal(0, 0.15, 3) if 0 < k < len(idx) - 1 else 0) for k, i in enumerate(idx)]
    return catmull(pts, 160)


def boxes_solid(boxes):
    def f(p):
        return any(np.all(p >= a - 0.2) and np.all(p <= b + 0.2) for a, b in boxes)
    return f


def solid_box(name, a, b, m=STONE_M):
    a = np.asarray(a, float); b = np.asarray(b, float)
    o = cube(name, m, 1.0); o.location = tuple((a + b) / 2); o.scale = tuple(b - a)
    return a, b


def fire_path(tag, path, t0, speed=0.85, tail=1.4, nseg=14, end_cb=None):
    """A laser along a given path (n,3)."""
    path = np.asarray(path, float)
    seg = np.linalg.norm(np.diff(path, axis=0), axis=1)
    cum = np.concatenate([[0], np.cumsum(seg)])
    total = cum[-1]
    t_hit = t0 + int(math.ceil(total / speed))
    segs = [cube(f"{tag} seg {i}", BEAM_M, 1.0) for i in range(nseg)]
    lt = bpy.data.lights.new(tag + " light", "POINT"); lt.color = RED; lt.shadow_soft_size = 0.1
    lo = link(bpy.data.objects.new(tag + " light", lt))
    for t in range(1, END + 1):
        sh = (t - t0) * speed
        live = t0 <= t <= t_hit + int(tail / speed) + 1
        for i, sg in enumerate(segs):
            a = sh - tail * i / nseg; b = sh - tail * (i + 1) / nseg
            if not live or a < 0 or b > total:
                keyo(sg, t, scale=(0, 0, 0)); continue
            pa, pb = point_on(path, cum, a), point_on(path, cum, max(b, 0))
            mid = (pa + pb) / 2; v = pa - pb; ln = float(np.linalg.norm(v))
            if ln < 1e-4:
                keyo(sg, t, scale=(0, 0, 0)); continue
            yaw = math.atan2(v[1], v[0]); pitch = math.atan2(v[2], math.hypot(v[0], v[1]))
            w = 0.05 * (1 - 0.6 * i / nseg)
            keyo(sg, t, loc=mid, scale=(ln, w, w), rot=(0, -pitch, yaw))
        lo.location = tuple(point_on(path, cum, min(sh, total))); lo.keyframe_insert("location", frame=t)
        lt.energy = 60.0 if live else 0.0; lt.keyframe_insert("energy", frame=t)
    return t_hit



def face_cam(tag, ox, oz=0.0):
    cam(f"Cam {tag} face", (ox + 0.9, -1.6, 1.75 + oz), (ox, 0.0, 1.62 + oz), 50)


def eye_custom(tag, frames):
    s_ = EYE_M[tag].inputs["Strength"]
    for f, e in frames:
        s_.default_value = e; s_.keyframe_insert("default_value", frame=f)


SMOKE_M, _ = emis("OB smoke", (0.6, 0.05, 0.03), 1.5, alpha=0.35)
ARC_M, _ = emis("OB arc", (1.0, 0.3, 0.25), 20.0)
WHITE_M, _ = emis("OB flash", (1.0, 0.85, 0.8), 30.0)
STEP = dict(body=(0.1, 0, 0), head=(0.05, 0, 0), ring=(0.5, 0, 0.1), free=(-0.45, 0, -0.1),
            ringleg=(-0.45, 0, 0.04), ringknee=0.5, freeleg=(0.4, 0, -0.04), freeknee=0.2)
sols = {}

# E1 snap ----------------------------------------------------------------------------------------------
ox = 0.0; o = np.array([ox, 0, 0])
objs = make_player("E1"); add_eyes(objs, "E1")
tgt1 = o + np.array([2.5, -7.0, 0.5]); m1 = target_block("OB E1 target", tgt1, 1.0, MOB_M)
for t in range(END + 1):
    if t < 12:
        p_ = mixp(LOCK, STEP, 0.5 + 0.5 * math.sin(t * 0.5))
    else:
        p_ = mixp(LOCK, STEP, 0.5 + 0.5 * math.sin(12 * 0.5)); p_["head"] = (0.05, -0.33, 0)    # frozen, head snapped
    sl = solve(p_); set_pose(objs, sl, o, t + 1); sols[("E1", t)] = sl
eye_custom("E1", [(1, 0), (12, 0), (13, 120), (15, 40), (60, 40), (66, 0)])
flash = cube("OB E1 flash", WHITE_M, 0.5)
fp = eye_world(sols[("E1", 12)], o)
keyo(flash, 1, loc=fp, scale=(0, 0, 0)); keyo(flash, 12, loc=fp, scale=(0, 0, 0)); keyo(flash, 13, loc=fp, scale=(0.9, 0.9, 0.9)); keyo(flash, 17, loc=fp, scale=(0, 0, 0))
hs = [fire_beam(f"OB E1 beam {n}", lambda tt, n=n: eye_world(sols[("E1", min(tt, END))], o, which=n), tgt1, 14, speed=1.0) for n in range(2)]
incinerate(m1, tgt1, max(hs))

# E2 smoulder --------------------------------------------------------------------------------------------
ox = 8.0; o = np.array([ox, 0, 0])
objs = make_player("E2"); add_eyes(objs, "E2")
tgt2 = o + np.array([-1.5, -7.0, 0.5]); m2 = target_block("OB E2 target", tgt2, 1.0, MOB_M)
for t in range(END + 1):
    p_ = dict(LOCK); p_["head"] = (0.1 - 0.15 * smooth(min(1, t / 30)), 0.2, 0)
    sl = solve(p_); set_pose(objs, sl, o, t + 1); sols[("E2", t)] = sl
eye_custom("E2", [(1, 0), (8, 0)] + [(8 + k, 2 + 1.2 * k) for k in range(1, 26, 3)] + [(34, 70), (36, 35), (75, 35), (82, 0)])
for i in range(16):
    pf = cube(f"OB E2 smoke {i}", SMOKE_M, 0.06)
    t0 = 8 + i * 1.6
    start = eye_world(sols[("E2", int(t0))], o, which=i % 2)
    keyo(pf, 1, loc=start, scale=(0, 0, 0)); keyo(pf, int(t0), loc=start, scale=(0, 0, 0))
    for j in range(1, 18):
        keyo(pf, int(t0) + j, loc=start + np.array([0.02 * math.sin(j * 0.7 + i), -0.01 * j, 0.035 * j]),
             scale=((1 + j / 6) * (1 - j / 18),) * 3)
hs = [fire_beam(f"OB E2 beam {n}", lambda tt, n=n: eye_world(sols[("E2", min(tt, END))], o, which=n), tgt2, 36 + 3 * n, speed=0.85) for n in range(2)]
incinerate(m2, tgt2, max(hs))

# E3 air brake -------------------------------------------------------------------------------------------
ox = 16.0; o = np.array([ox, 0, 0])
objs = make_player("E3"); add_eyes(objs, "E3")
tgt3 = o + np.array([0.0, -8.0, 0.5]); m3 = target_block("OB E3 target", tgt3, 1.0, MOB_M)
BRAKE = dict(body=(-0.55, 0, 0), head=(0.5, 0, 0), ring=(-0.9, 0, 0.6), free=(-0.9, 0, -0.6),
             ringleg=(-0.9, 0, 0.08), ringknee=1.0, freeleg=(-0.6, 0, -0.08), freeknee=0.8, grounded=False)
pos3 = {}
for t in range(END + 1):
    if t < 14:
        y = 10.0 - 0.6 * t; p_ = FLYING
    elif t < 26:
        u = (t - 14) / 12; y = 10.0 - 0.6 * 14 - 0.6 * 12 * (u - u * u / 2); p_ = mixp(FLYING, BRAKE, smooth(min(1, u * 1.6)))
    else:
        y = 10.0 - 0.6 * 14 - 0.6 * 12 * 0.5; p_ = mixp(BRAKE, HOVER, smooth(min(1, (t - 26) / 10)))
    origin = o + np.array([0, y, 4.0 + 0.08 * math.sin(t * 0.3)])
    sl = solve(p_); set_pose(objs, sl, origin, t + 1); pos3[t] = (sl, origin)
eye_custom("E3", [(1, 0), (24, 0), (26, 70), (28, 35), (75, 35), (80, 0)])
hs = [fire_beam(f"OB E3 beam {n}", lambda tt, n=n: eye_world(*pos3[min(tt, END)], which=n), tgt3, 30 + 2 * n, speed=0.85) for n in range(2)]
incinerate(m3, tgt3, max(hs))

# E4 crackle --------------------------------------------------------------------------------------------
ox = 24.0; o = np.array([ox, 0, 0])
objs = make_player("E4"); add_eyes(objs, "E4")
tgt4 = o + np.array([1.0, -7.0, 0.5]); m4 = target_block("OB E4 target", tgt4, 1.0, MOB_M)
sl4 = solve(LOCK)
for t in range(END + 1):
    set_pose(objs, sl4, o, t + 1)
eye_custom("E4", [(1, 0), (8, 0), (10, 15), (30, 30), (32, 70), (34, 35), (75, 35), (80, 0)])
arcs = [cube(f"OB E4 arc {i}", ARC_M, 1.0) for i in range(10)]
for t in range(1, END + 1):
    for i, a in enumerate(arcs):
        if 10 <= t <= 32 and rng.random() < 0.6:
            c = eye_world(sl4, o, which=i % 2)
            p0 = c + rng.normal(0, 0.12, 3); p1 = p0 + rng.normal(0, 0.12, 3)
            v = p1 - p0; ln = float(np.linalg.norm(v))
            keyo(a, t, loc=(p0 + p1) / 2, scale=(ln, 0.012, 0.012),
                 rot=(0, -math.atan2(v[2], math.hypot(v[0], v[1])), math.atan2(v[1], v[0])))
        else:
            keyo(a, t, scale=(0, 0, 0))
hs = [fire_beam(f"OB E4 beam {n}", lambda tt, n=n: eye_world(sl4, o, which=n), tgt4, 33 + 2 * n, speed=0.85) for n in range(2)]
incinerate(m4, tgt4, max(hs))

# E5 let go: the beams fly on straight and burn the wall -------------------------------------------------
ox = 34.0; o = np.array([ox, 0, 0])
objs = make_player("E5"); add_eyes(objs, "E5")
cen = o + np.array([0, -6.0, 0.5])


def run5(t):
    a = 0.15 * t
    return cen + np.array([3.0 * math.cos(a), 3.0 * math.sin(a), 0.0])


runner = target_block("OB E5 runner", run5(0), 1.0, MOB_M)
for t in range(1, END + 1):
    keyo(runner, t, loc=run5(t))
wall5 = []
for ix in range(-6, 7):
    for iz in range(0, 4):
        at = o + np.array([ix, -12.0, iz + 0.5])
        wall5.append((target_block(f"OB E5 wall {ix} {iz}", at), at))
sl5 = solve(LOCK)
for t in range(END + 1):
    set_pose(objs, sl5, o, t + 1)
eye_custom("E5", [(1, 0), (10, 0), (12, 70), (14, 35), (44, 35), (48, 0)])
RELEASE = 44
for n in range(2):
    t0 = 16 + 3 * n
    p_ = eye_world(sl5, o, which=n)
    v = np.array([(-1) ** n * 0.6, -0.5, 0.3]); v /= np.linalg.norm(v)
    pts = [p_.copy()]; t = t0
    while t < RELEASE:                                   # chasing while held
        to = run5(t + 1) - p_; d = float(np.linalg.norm(to))
        want = to / d + rng.normal(0, 0.25, 3); want /= np.linalg.norm(want)
        ang = math.acos(max(-1, min(1, float(np.dot(v, want)))))
        if ang > 0.22:
            axis = np.cross(v, want); axis /= (np.linalg.norm(axis) + 1e-9)
            c_, s_ = math.cos(0.22), math.sin(0.22)
            v = v * c_ + np.cross(axis, v) * s_ + axis * np.dot(axis, v) * (1 - c_)
        else:
            v = want
        p_ = p_ + v * 0.45; p_[2] = max(0.3, p_[2]); pts.append(p_.copy()); t += 1
    v[2] = max(v[2], -0.05); v /= np.linalg.norm(v)
    while p_[1] > o[1] - 12.0 + 0.55 and len(pts) < 400 and abs(p_[0] - ox) < 6.5:      # let go: straight on
        p_ = p_ + v * 0.45; pts.append(p_.copy())
    t_hit = fire_path(f"OB E5 beam {n}", np.array(pts), t0, speed=0.45)
    wi = min(range(len(wall5)), key=lambda i: float(np.linalg.norm(wall5[i][1] - p_)))
    incinerate(wall5[wi][0], wall5[wi][1], min(t_hit, END - 20))

for tag, ox_, lab, oz in (("E1", 0.0, "E1  snap", 0), ("E2", 8.0, "E2  smoulder", 0), ("E3", 16.0, "E3  air brake", 4.0),
                          ("E4", 24.0, "E4  crackle", 0), ("E5", 34.0, "E5  let go", 0)):
    cu = bpy.data.curves.new("OB label " + tag, "FONT"); cu.body = lab; cu.size = 0.35; cu.align_x = "CENTER"
    tl = link(bpy.data.objects.new("OB label " + tag, cu)); tl.location = (ox_, 1.6, 0.01)
    tl.data.materials.append(mat("OB label", (1.0, 0.8, 0.8), emit=2.0))
    if tag == "E3":
        cam("Cam E3", (ox_ - 1.2, 1.5, 7.5), (ox_, -8.0, 0.5), 28)
        cam("Cam E3 face", (ox_ + 1.5, -6.0, 5.6), (ox_, 4.6, 5.2), 40)
    else:
        cam(f"Cam {tag}", (ox_ - 1.0, 2.8, 2.4), (ox_ + 0.2, -6.0, 1.0), 30)
        face_cam(tag, ox_)
cam("Cam E5 top", (34.5, -5.5, 16), (34, -6.0, 0), 34)

scene.frame_start, scene.frame_end = 1, END
bpy.ops.mesh.primitive_plane_add(size=100, location=(17, -4, 0))
g = bpy.context.active_object
for c in g.users_collection:
    c.objects.unlink(g)
link(g); g.name = "OB ground"; g.data.materials.append(mat("OB ground", (0.14, 0.2, 0.1)))
world = bpy.data.worlds.new("OB world"); world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.03, 0.03, 0.05, 1)
scene.world = world
moon = link(bpy.data.objects.new("OB moon", bpy.data.lights.new("OB moon", "SUN")))
moon.data.energy = 0.5; moon.data.color = (0.6, 0.7, 1.0); moon.rotation_euler = (R(55), R(-10), R(-35))
try:
    scene.render.engine = "BLENDER_EEVEE"
except Exception:
    scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x, scene.render.resolution_y = 1600, 900
try:
    scene.view_settings.view_transform = "Standard"
except Exception:
    pass
scene.camera = bpy.data.objects["Cam E1 face"]
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
