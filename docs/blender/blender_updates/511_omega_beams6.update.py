# Pass 511: omega beams round 6, long angular lines built out of the eyes (Chat C, 2026-10-14). J on 506: "for the
# omega beams i cant tell the difference too much but the two on the left are good i need the lines to look more like
# this though, they should leave the eyes and build from them every line" (references: long straight red lines with hard
# corners switching back and forth, two side by side from the eyes).
# KEEP: one parallel pair per use (0.26 blocks apart), the unpredictable route and random approach side, O1 slow walk,
# O2 hover brake, 0.5 s incinerate, O3 calm chaining barrage.
# NEW look: straight sides joined by sharp corners (no wiggle between corners), each side switching back across the
# line to the target with the switch-back plane turning a little every corner. The line is built out of the eyes:
# it stays joined to them while it grows corner by corner (the whole line shows, not a short tail); the corners shiver
# slightly; after the last hit it lets go of the eyes and burns away from the eye end at 2.5x the speed. In the
# barrage the line lets go of the eyes once it is 10 blocks long (6 ticks), and that is when you can move again.
#   P1 sides 1.6-2.6 blocks, 40-60 deg off the line (closest to the Z1/Z2 J liked)
#   P2 long sides 2.5-4 blocks, 45-65 deg (like the references)
#   P3 mixed 1.2-4 blocks, sharper 55-72 deg switchbacks. Each route is capped at ~2x the straight distance, and the
#   head is faster (1.8 blocks a tick) so long sides still hit quickly.
# Takes O1-P1..O3-P3. Cameras "Cam <take>" (over the right shoulder), "Cam <take> front".
# Builds LanternLive\combat\omega_beams6.blend.
import json, math, os
import bpy
import numpy as np
from mathutils import Matrix

R = math.radians
ASSETS = os.path.join(FOLDER, "kl_assets")
OUT = os.path.join(FOLDER, "omega_beams6.blend")
if bpy.data.filepath:
    try:
        bpy.ops.wm.save_mainfile()
    except Exception as e:
        print("save current:", e)
old = bpy.data.scenes.get("Omega Beams 6")
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new("Omega Beams 6")
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


SEED = 511
rng = np.random.default_rng(SEED)
END = 140
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



# ================================================================== pass 504
SEP = 0.26
SPEED = 1.8
STYLES = {"P1": "angular, sides 1.6-2.6, corners 40-60 deg", "P2": "angular, long sides 2.5-4, corners 45-65 deg",
          "P3": "angular, mixed 1.2-4, sharp 55-72 deg"}
POLY = {"P1": (1.6, 2.6, 40, 60), "P2": (2.5, 4.0, 45, 65), "P3": (1.2, 4.0, 55, 72)}   # side length, angle off the line
CUR = {"style": "P1"}


def perp_basis(u):
    a = np.array([0, 0, 1.0]) if abs(u[2]) < 0.9 else np.array([1.0, 0, 0])
    v = np.cross(u, a); v /= np.linalg.norm(v); w = np.cross(u, v)
    return v, w


def polyroute(points):
    """Long straight sides joined by sharp corners, switching back and forth across the line to each target, the
    switch-back plane turning a little every corner; every target approached from a random side."""
    l0, l1, a0, a1 = POLY[CUR["style"]]
    pts = [np.asarray(points[0], float)]
    marks = []
    for p_ in points[1:]:
        b = np.asarray(p_, float)
        app = rng.normal(0, 1, 3); app[2] = abs(app[2]) * 0.6; app /= np.linalg.norm(app)
        goal = b + app * float(rng.uniform(1.2, 2.2))
        sign = 1.0 if rng.random() < 0.5 else -1.0
        plane = float(rng.uniform(0, 2 * math.pi))
        leg0 = float(np.linalg.norm(goal - pts[-1])); run = 0.0
        for _ in range(40):
            c = pts[-1]; dvec = goal - c; dist = float(np.linalg.norm(dvec))
            if dist < l1 * 1.1 or run > 2.0 * leg0:          # never more than ~2x the straight distance
                break
            u = dvec / dist; v, w = perp_basis(u)
            plane += float(rng.uniform(-0.5, 0.5))
            side = math.cos(plane) * v + math.sin(plane) * w
            ang = math.radians(float(rng.uniform(a0, a1)))
            hd = math.cos(ang) * u + sign * math.sin(ang) * side
            ln = float(rng.uniform(l0, l1))
            nxt = c + hd * ln
            if nxt[2] < 0.3:
                nxt[2] = 0.3 + abs(nxt[2]) * 0.3
            pts.append(nxt); sign = -sign; run += ln
        pts.append(goal); pts.append(b)
        marks.append(len(pts) - 1)
    return [np.array(q) for q in pts], marks


def fire_pair(tag, style, points, t0, eye_fn, release=None, phase=0.0, end_sep=1.0, end_burn=None):
    """One pair of straight-sided lasers built out of the eyes: the line stays joined to the eyes while it grows corner
    by corner, the corners shiver slightly, and once the last target is hit it lets go of the eyes and burns away
    from the eye end. Returns the tick each target is reached and the tick the line leaves the eyes."""
    pts, marks = polyroute(points)
    seg = [float(np.linalg.norm(pts[i + 1] - pts[i])) for i in range(len(pts) - 1)]
    cum = np.concatenate([[0], np.cumsum(seg)])
    total = cum[-1]
    hits = [t0 + int(math.ceil(cum[m] / SPEED)) for m in marks]
    t_last = hits[-1]
    t_end = t_last + int(math.ceil(total / (SPEED * 2.5))) + 2
    overall = pts[-1] - pts[0]; overall[2] = 0
    side_g = np.cross(overall / (np.linalg.norm(overall) or 1), np.array([0, 0, 1.0]))
    side_g /= (np.linalg.norm(side_g) or 1)
    cubes = [[cube(f"{tag} b{k} side {i}", BEAM_M, 1.0) for i in range(len(seg))] for k in (0, 1)]
    lt = bpy.data.lights.new(tag + " light", "POINT"); lt.color = RED; lt.shadow_soft_size = 0.1
    lo = link(bpy.data.objects.new(tag + " light", lt))
    jit = [rng.uniform(0, 2 * math.pi, 3) for _ in pts]
    for t in range(1, END + 1):
        head = min(total, max(0.0, (t - t0) * SPEED))
        tail_s = 0.0 if t <= t_last else min(total, (t - t_last) * SPEED * 2.5)
        if release is not None:                      # barrage: the line lets go of the eyes once it is this long
            tail_s = max(tail_s, head - release)
        live = t0 <= t <= t_end
        le, re = eye_fn(min(t, END))
        eyes = [le, re]
        cur = []
        for i, q in enumerate(pts):
            if i == 0:
                cur.append((le + re) / 2); continue
            j = jit[i]
            cur.append(q + 0.05 * np.array([math.sin(0.4 * t + j[0]), math.sin(0.37 * t + j[1]), math.sin(0.43 * t + j[2])])
                       * (0 if i == len(pts) - 1 else 1))
        for k, cs in enumerate(cubes):
            off = (-1 if k == 0 else 1) * SEP / 2 * side_g
            for i, cb in enumerate(cs):
                a_s, b_s = cum[i], cum[i + 1]
                lo_s, hi_s = max(a_s, tail_s), min(b_s, head)
                if not live or hi_s <= lo_s + 1e-4:
                    keyo(cb, t, scale=(0, 0, 0)); continue
                A_ = cur[i] + (off if i > 0 else 0) ; B_ = cur[i + 1] + off
                if i == 0 and tail_s <= 0.0:
                    A_ = eyes[k]
                pa = A_ + (B_ - A_) * ((lo_s - a_s) / (b_s - a_s)); pb = A_ + (B_ - A_) * ((hi_s - a_s) / (b_s - a_s))
                mid = (pa + pb) / 2; v = pb - pa; ln = float(np.linalg.norm(v))
                yaw = math.atan2(v[1], v[0]); pitch = math.atan2(v[2], math.hypot(v[0], v[1]))
                keyo(cb, t, loc=mid, scale=(ln + 0.05, 0.05, 0.05), rot=(0, -pitch, yaw))
        hp = np.interp(head, cum, np.arange(len(pts)))
        i0 = min(int(hp), len(pts) - 2); fr = hp - i0
        lo.location = tuple(cur[i0] + (cur[i0 + 1] - cur[i0]) * fr); lo.keyframe_insert("location", frame=t)
        lt.energy = 110.0 if live else 0.0; lt.keyframe_insert("energy", frame=t)
    return hits, (t_last + 1 if release is None else t0 + int(math.ceil(release / SPEED)) + 1)


def incinerate(o, at, hit, size=1.0):
    """Faster than 223: embers the tick it is hit, gone in 10 ticks, ash straight after."""
    keyo(o, 1, scale=(1, 1, 1)); keyo(o, hit - 1, scale=(1, 1, 1)); keyo(o, hit, scale=(0, 0, 0))
    em = cube(o.name + " ember", EMBER_M, size); em.location = tuple(at)
    keyo(em, 1, scale=(0, 0, 0)); keyo(em, hit - 1, scale=(0, 0, 0)); keyo(em, hit, scale=(1.02, 1.02, 1.02))
    keyo(em, hit + 5, scale=(0.85, 0.85, 0.7)); keyo(em, hit + 10, scale=(0, 0, 0))
    lt = bpy.data.lights.new(o.name + " glow", "POINT"); lt.color = (1.0, 0.35, 0.08); lt.shadow_soft_size = 0.4
    lo = link(bpy.data.objects.new(o.name + " glow", lt)); lo.location = tuple(at)
    for f, e in ((1, 0), (hit - 1, 0), (hit, 350 * size), (hit + 8, 100 * size), (hit + 12, 0)):
        lt.energy = e; lt.keyframe_insert("energy", frame=f)
    for i in range(6):
        a = cube(o.name + f" ash {i}", ASH_M, 0.12 * size)
        p0 = np.asarray(at) + rng.uniform(-0.4, 0.4, 3) * size
        keyo(a, 1, loc=p0, scale=(0, 0, 0)); keyo(a, hit + 4, loc=p0, scale=(0, 0, 0))
        for j in range(1, 21):
            keyo(a, hit + 4 + j, loc=p0 + np.array([rng.normal(0, 0.01), rng.normal(0, 0.01), 0.035 * j]),
                 scale=(max(0, 1 - j / 20),) * 3)


WALK_A = 0.35


def walk(p, t, rate=0.16):
    q = dict(p); a = WALK_A * math.sin(t * rate * 2 * math.pi / 2)
    q["ringleg"] = (a, 0, 0.06); q["freeleg"] = (-a, 0, -0.06); q["ringknee"] = 0.2 + 0.2 * max(0, -a); q["freeknee"] = 0.2 + 0.2 * max(0, a)
    q["free"] = (0.4 * a, 0, -0.25)
    return q


AIM = dict(LOCK); AIM["head"] = (0.05, 0, 0)
SPARK_M, _ = emis("OB spark", RED, 8.0)
LANE = 14.0
dump = {"format": "per take: beam pair timings (ticks), targets, line style. 20 ticks a second.",
        "pair_separation_blocks": SEP, "head_speed_bpt": SPEED, "retract_speed_bpt": SPEED * 2.5,
        "styles": {k: {"side_blocks": [v[0], v[1]], "corner_deg": [v[2], v[3]]} for k, v in POLY.items()},
        "corner_shiver_blocks": 0.05, "approach_from_blocks": [1.2, 2.2],
        "incinerate": {"ember_ticks": 10, "ash_from_tick": 4, "ash_ticks": 20}, "takes": {}}
idx = 0
for scen in ("O1", "O2", "O3"):
    for st in ("P1", "P2", "P3"):
        CUR["style"] = st
        take = scen + "-" + st
        base = np.array([idx * LANE, 0.0, 0.0]); idx += 1
        objs = make_player(take); add_eyes(objs, take)
        poses = []
        info = {"style": STYLES[st]}
        if scen == "O1":
            # slow walk forward while firing, two volleys at a wall 9 blocks ahead
            for t in range(END + 1):
                fwd = 0.04 * max(0, t - 12)
                o_ = base + np.array([0, -fwd, 0])
                p_ = walk(AIM, t) if t >= 12 else dict(AIM)
                s_ = solve(p_); set_pose(objs, s_, o_, t + 1); poses.append((s_, o_))
            eye_flash(take, 10, 95)
            wall = {}
            for ix in range(-2, 3):
                for iz in range(0, 4):
                    at = base + np.array([ix * 1.0, -9.0, iz + 0.5])
                    wall[(ix, iz)] = (target_block(f"OB {take} wall {ix} {iz}", at), at)
            eyes = lambda tt, P=poses: (eye_world(*P[tt], which=0), eye_world(*P[tt], which=1))
            vol = []
            for n, (t0, (ix, iz)) in enumerate(((16, (-1, 1)), (52, (1, 2)))):
                at = wall[(ix, iz)][1]; at2 = wall[(ix + 1, iz)][1]
                mid = (at + at2) / 2 + np.array([0, 0.5, 0])
                le, re = eyes(t0)
                hits, clear = fire_pair(f"OB {take} pair{n}", st, [(le + re) / 2, mid], t0, eyes, phase=n * 1.3,
                                        end_sep=1.0)
                incinerate(wall[(ix, iz)][0], at, hits[-1] + 1); incinerate(wall[(ix + 1, iz)][0], at2, hits[-1] + 1)
                vol.append({"fire": t0, "hit": hits[-1]})
            info.update(walk_speed_bpt=0.04, volleys=vol)
            cam(f"Cam {take}", tuple(base + np.array([-1.0, 2.8, 2.3])), tuple(base + np.array([0.2, -6.0, 1.4])), 30)
            cam(f"Cam {take} front", tuple(base + np.array([8.0, -4.5, 2.6])), tuple(base + np.array([0, -4.5, 1.4])), 30)
        elif scen == "O2":
            mob_at = base + np.array([0.0, -6.5, 0.5])
            mob = target_block(f"OB {take} mob", mob_at, 1.0, MOB_M)
            mob_head = target_block(f"OB {take} mob head", mob_at + np.array([0, -0.45, 0.75]), 0.6, MOB_M)
            for t in range(END + 1):
                if t < 22:
                    y = 6.0 - 0.45 * t * (1 - t / 44.0); z = 4.0
                else:
                    y = 6.0 - 0.45 * 22 * 0.5; z = 4.0 + 0.08 * math.sin(t * 0.25)
                p_ = mixp(FLYING, HOVER, smooth(min(1, t / 22)))
                o_ = base + np.array([0.0, y, z]); s_ = solve(p_); set_pose(objs, s_, o_, t + 1); poses.append((s_, o_))
            eye_flash(take, 22, 80)
            eyes = lambda tt, P=poses: (eye_world(*P[tt], which=0), eye_world(*P[tt], which=1))
            le, re = eyes(28)
            hits, clear = fire_pair(f"OB {take} pair", st, [(le + re) / 2, mob_at + np.array([0, 0.3, 0.2])], 28, eyes,
                                    end_sep=0.4)
            incinerate(mob, mob_at, hits[-1] + 1); incinerate(mob_head, mob_at + np.array([0, -0.45, 0.75]), hits[-1] + 1, 0.6)
            info.update(fire=28, hit=hits[-1])
            cam(f"Cam {take}", tuple(base + np.array([-1.2, 5.5 + 3.2, 6.5])), tuple(base + np.array([0, -5.0, 1.0])), 30)
            cam(f"Cam {take} front", tuple(base + np.array([6.0, -4.0, 3.0])), tuple(base + np.array([0, 0.0, 2.5])), 28)
        else:
            # barrage: calm, short charge, one pair threads all six targets; you walk off once it has left the eyes
            tg = []
            angs = [-1.9, -1.1, -0.35, 0.4, 1.15, 2.0]
            for n, a in enumerate(angs):
                r = 5.0 + 2.5 * (n % 2)
                at = base + np.array([math.sin(a) * r, -math.cos(a) * r, 0.5 + (n % 3 == 1)])
                tg.append((target_block(f"OB {take} block {n}", at), at))
            T_CHARGE, T_FIRE = 6, 18
            clear_t = T_FIRE + int(math.ceil(10.0 / SPEED)) + 1   # the line lets go of the eyes at 10 blocks
            for t in range(END + 1):
                walking = t >= clear_t
                fwd = 0.13 * max(0, t - clear_t)            # normal walking pace once movement is back
                o_ = base + np.array([0, -fwd, 0])
                p_ = walk(LOCK, t, 0.3) if walking else dict(LOCK)
                if not walking:
                    p_["head"] = (0.08, 0, 0)               # calm: head level, no turning
                s_ = solve(p_); set_pose(objs, s_, o_, t + 1); poses.append((s_, o_))
            eye_flash(take, T_FIRE - 2, 100)
            s_ = EYE_M[take].inputs["Strength"]                # the charge: eyes build over 0.6 s
            for f, e in ((T_CHARGE, 0), (T_CHARGE + 6, 8), (T_FIRE - 2, 18)):
                s_.default_value = e; s_.keyframe_insert("default_value", frame=f)
            for i in range(10):                                 # red sparks gathering round the eyes
                sp = cube(f"OB {take} spark {i}", SPARK_M, 0.05)
                eye = eye_world(*poses[T_CHARGE], which=i % 2)
                src = eye + rng.normal(0, 0.35, 3)
                keyo(sp, 1, loc=src, scale=(0, 0, 0)); keyo(sp, T_CHARGE + i, loc=src, scale=(0, 0, 0))
                keyo(sp, T_CHARGE + i + 1, loc=src, scale=(1, 1, 1)); keyo(sp, T_FIRE - 1, loc=eye, scale=(0.4, 0.4, 0.4))
                keyo(sp, T_FIRE, loc=eye, scale=(0, 0, 0))
            eyes = lambda tt, P=poses: (eye_world(*P[tt], which=0), eye_world(*P[tt], which=1))
            le, re = eyes(T_FIRE)
            order = [2, 1, 0, 3, 4, 5]
            hits, clear = fire_pair(f"OB {take} pair", st, [(le + re) / 2] + [tg[k][1] for k in order], T_FIRE, eyes,
                                    end_sep=0.5, release=10.0)
            for k, h in zip(order, hits):
                incinerate(tg[k][0], tg[k][1], h + 1)
            info.update(charge_from=T_CHARGE, fire=T_FIRE, movement_back=clear_t, hits=hits)
            cam(f"Cam {take}", tuple(base + np.array([-1.0, 3.0, 2.8])), tuple(base + np.array([0, -4.0, 1.0])), 26)
            cam(f"Cam {take} front", tuple(base + np.array([7.0, -9.0, 7.0])), tuple(base + np.array([0, -1.5, 1.0])), 30)
        dump["takes"][take] = info
        cu = bpy.data.curves.new("OB label " + take, "FONT")
        cu.body = take + "  " + {"O1": "ground, slow walk", "O2": "hover brake", "O3": "barrage, one pair"}[scen] + " - " + STYLES[st]
        cu.size = 0.35; cu.align_x = "CENTER"
        tl = link(bpy.data.objects.new("OB label " + take, cu)); tl.location = tuple(base + np.array([0, 1.8, 0.01]))
        tl.data.materials.append(mat("OB label", (1.0, 0.8, 0.8), emit=2.0))
        print(take, "built", flush=True)

with open(os.path.join(FOLDER, "omega_beams6_poses.json"), "w") as fh:
    json.dump(dump, fh, separators=(",", ":"))
scene.frame_start, scene.frame_end = 1, END
bpy.ops.mesh.primitive_plane_add(size=1, location=(LANE * 4, -4, 0))
g = bpy.context.active_object
for c in g.users_collection:
    c.objects.unlink(g)
link(g); g.name = "OB ground"; g.scale = (160, 50, 1); g.data.materials.append(mat("OB ground", (0.14, 0.2, 0.1)))
world = bpy.data.worlds.new("OB world"); world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.03, 0.03, 0.05, 1)
scene.world = world
moon = link(bpy.data.objects.new("OB moon", bpy.data.lights.new("OB moon", "SUN")))
moon.data.energy = 0.4; moon.data.color = (0.6, 0.7, 1.0); moon.rotation_euler = (R(55), R(-10), R(-35))
try:
    scene.render.engine = "BLENDER_EEVEE"
except Exception:
    scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x, scene.render.resolution_y = 1600, 900
try:
    scene.view_settings.view_transform = "Standard"
except Exception:
    pass
scene.camera = bpy.data.objects["Cam O1-P2"]
try:
    bpy.ops.outliner.orphans_purge(do_recursive=True)
except Exception:
    pass
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("saved", OUT)
