# Pass 517: omega beams round 10 - wild, hits on contact, strike endings (Chat C, 2026-10-14). J on 516: "wild is good
# fast flyer is also good, for underwater restless looks better maybe because its faster ... i want wild but at the
# speed of the restless, also when for some targets it zips to the mob at the last second when it thinks its close
# enough but the damage should accurately capable of being applied when the line makes another angle and when that
# angle which obeys the particle capabilities it should default to a certain type of strike animation".
# KEEP: E2 wild (PICKED; F2 fast flyer kept), darker beams, W2 boiling sleeve, x1.4 sides / 95% chase on fast targets.
# HIT ON CONTACT: every tick the beam head is tested against the target (0.75 blocks for a mob or horse): the instant
# any side touches it, on any angle, it is hit. No more straight last-second zip: the beam keeps making erratic sides
# (never longer than one normal side) until it touches the target or commits (then 55-63 deg corners, so it keeps
# gaining); when committed and within 1.5 sides it
# makes its final corner and ends in a strike:
#   K1 snap strike: a sharp kink 0.6 blocks off the line, then straight in, with a flash ring at the hit.
#   K2 coil strike: two short sides wrapping round the target (0.9 blocks out, 120 deg apart), then in.
#   K3 pierce strike: straight through, carrying on 1.2 blocks past the target before the line burns away.
# WILD AT RESTLESS SPEED (under water): the wildness is now counted by distance travelled, not time, so a faster head
# makes the same wild shape sooner. U3 E2 at 1.6x head speed, U4 E2 at 2x.
# Takes: K1/K2/K3 (galloping horse, E2), F2 (fast flyer, E2, K1), U3/U4 (under water, E2, K1, sleeve).
# Cameras "Cam <take>", "Cam <take> wide", "Cam <take> target". Builds LanternLive\combat\omega_strike.blend.
import json, math, os
import bpy
import numpy as np
from mathutils import Matrix

R = math.radians
ASSETS = os.path.join(FOLDER, "kl_assets")
OUT = os.path.join(FOLDER, "omega_strike.blend")
if bpy.data.filepath:
    try:
        bpy.ops.wm.save_mainfile()
    except Exception as e:
        print("save current:", e)
old = bpy.data.scenes.get("Omega Erratic")
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new("Omega Fire")
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


SEED = 517
rng = np.random.default_rng(SEED)
END = 130
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
SPEED = 2.2
STYLES = {"P1": "angular, sides 1.6-2.6, corners 40-60 deg", "P2": "angular, long sides 2.5-4, corners 45-65 deg",
          "P3": "angular, mixed 1.2-4, sharp 55-72 deg"}
POLY = {"P1": (1.6, 2.6, 40, 60), "P2": (2.5, 4.0, 45, 65), "P3": (0.8, 3.2, 55, 72)}   # side length, angle off the line
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

HORSE_M = mat("OB horse", (0.42, 0.27, 0.15)); MANE_M = mat("OB mane", (0.12, 0.08, 0.05))


def box_obj(name, x0, x1, y0, y1, z0, z1, m, parent):
    me = bpy.data.meshes.new(name)
    me.from_pydata([(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)], [],
                   [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)])
    me.materials.append(m)
    o = link(bpy.data.objects.new(name, me)); o.parent = parent
    return o


def make_horse(tag):
    """A blocky horse facing local -Y: body, neck, head, mane, tail, four legs hinged at the top."""
    root = link(bpy.data.objects.new(f"{tag} horse", None)); root.empty_display_size = 0.5
    box_obj(f"{tag} horse body", -0.35, 0.35, -0.75, 0.75, 0.75, 1.4, HORSE_M, root)
    neck = box_obj(f"{tag} horse neck", -0.2, 0.2, -1.15, -0.65, 1.15, 1.9, HORSE_M, root)
    box_obj(f"{tag} horse head", -0.18, 0.18, -1.6, -1.0, 1.65, 2.0, HORSE_M, root)
    box_obj(f"{tag} horse mane", -0.08, 0.08, -1.0, -0.7, 1.4, 2.0, MANE_M, root)
    tail = box_obj(f"{tag} horse tail", -0.07, 0.07, 0.75, 0.9, 0.7, 1.3, MANE_M, root); tail.rotation_euler = (R(-25), 0, 0)
    legs = []
    for lx, ly in ((-0.22, -0.55), (0.22, -0.55), (-0.22, 0.55), (0.22, 0.55)):
        piv = link(bpy.data.objects.new(f"{tag} horse leg pivot {lx} {ly}", None)); piv.parent = root
        piv.location = (lx, ly, 0.85)
        box_obj(f"{tag} horse leg {lx} {ly}", -0.1, 0.1, -0.1, 0.1, -0.85, 0.0, HORSE_M, piv)
        legs.append(piv)
    return root, legs



def tube_mesh(name, verts=10):
    me = bpy.data.meshes.new(name); vs, fs = [], []
    for k in range(verts):
        a = 2 * math.pi * k / verts
        vs += [(-0.5, math.cos(a), math.sin(a)), (0.5, math.cos(a), math.sin(a))]
    for k in range(verts):
        k2 = (k + 1) % verts
        fs.append((2 * k, 2 * k2, 2 * k2 + 1, 2 * k + 1))
    me.from_pydata(vs, [], fs); me.update()
    return me


TUBE = tube_mesh("OB tube")



from mathutils import Vector
CUR["style"] = "P3"
ERR = {"E1": (0.45, 30, 72, 3.2), "E2": (0.15, 45, 120, 3.2), "E3": (0.15, 45, 120, 4.5)}
CURE = {"e": "E2", "strike": "K1", "hmul": 1.0}
HIT_R = 0.75
LANE = 40.0
TIMEOUT = 100
dump = {"format": "per take: fire tick, hit tick (or timeout), target speed, side scale, head speed. 20 ticks a second.",
        "style": "P3", "side_blocks": POLY["P3"][:2], "corner_deg": POLY["P3"][2:],
        "side_scale_rule": "1 + 0.4 * min(1, target_speed / 1.5)",
        "head_speed_rule": "max(2.2, 0.95 * target_speed / 0.45) blocks a tick", "timeout_ticks": TIMEOUT,
        "erratic": {k: {"w0": v[0], "commit_ticks": v[1], "corner_max_deg": v[2], "side_max_blocks": v[3]} for k, v in ERR.items()},
        "erratic_rule": "w = w0 + (1-w0)*(age/T)^1.5; side dir = normalize(w*to_target + (1-w)*random); roll += pi +/- 1.2 rad",
        "look": {"core": {"rgb": [0.75, 0.1, 0.05], "radius": 0.02, "strength": 5}, "glow": {"rgb": [0.55, 0.012, 0.0], "radius": 0.07, "strength": 1.6}},
        "underwater": "W2 sleeve: 9 bubbles a tick along the beam, 4-tick life; after the beam: 0.4 s fizz, 9 -> 0",
        "takes": {}}
def tube_mesh(name, verts=10):
    me = bpy.data.meshes.new(name); vs, fs = [], []
    for k in range(verts):
        a = 2 * math.pi * k / verts
        vs += [(-0.5, math.cos(a), math.sin(a)), (0.5, math.cos(a), math.sin(a))]
    for k in range(verts):
        k2 = (k + 1) % verts
        fs.append((2 * k, 2 * k2, 2 * k2 + 1, 2 * k + 1))
    me.from_pydata(vs, [], fs); me.update()
    return me


TUBE = tube_mesh("OB tube")




def fire_mats(tag, hot):
    """Core: thin white-hot red; glow: tight deep red fading to its edges. With `hot`, both flicker with hot spots: a
    noise along the line, moving."""
    out = []
    for kind, rgb, strength in (("core", (0.75, 0.1, 0.05), 5.0), ("glow", (0.55, 0.012, 0.0), 1.6)):
        m = bpy.data.materials.new(f"OB {tag} {kind}"); m.use_nodes = True
        N, L = m.node_tree.nodes, m.node_tree.links; N.clear()
        em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (*rgb, 1)
        st = N.new("ShaderNodeMath"); st.operation = "MULTIPLY"; st.inputs[1].default_value = strength
        if hot:
            geo = N.new("ShaderNodeNewGeometry")
            fr = N.new("ShaderNodeValue"); fcv = fr.outputs[0].driver_add("default_value"); fcv.driver.expression = "frame"
            sc = N.new("ShaderNodeMath"); sc.operation = "MULTIPLY"; sc.inputs[1].default_value = 0.4
            L.new(fr.outputs[0], sc.inputs[0])
            ad = N.new("ShaderNodeVectorMath"); ad.operation = "ADD"; L.new(geo.outputs["Position"], ad.inputs[0])
            cv = N.new("ShaderNodeCombineXYZ"); L.new(sc.outputs[0], cv.inputs[0]); L.new(sc.outputs[0], cv.inputs[1]); L.new(sc.outputs[0], cv.inputs[2])
            L.new(cv.outputs[0], ad.inputs[1])
            nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 2.0; nz.inputs["Detail"].default_value = 3.0
            L.new(ad.outputs[0], nz.inputs["Vector"])
            rp = N.new("ShaderNodeMapRange"); rp.inputs["From Min"].default_value = 0.35; rp.inputs["From Max"].default_value = 0.7
            rp.inputs["To Min"].default_value = 0.55; rp.inputs["To Max"].default_value = 1.8
            L.new(nz.outputs["Fac"], rp.inputs["Value"]); L.new(rp.outputs["Result"], st.inputs[0])
        else:
            st.inputs[0].default_value = 1.0
        L.new(st.outputs[0], em.inputs["Strength"])
        o_ = N.new("ShaderNodeOutputMaterial")
        if kind == "glow":
            lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.5
            inv = N.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 1.0
            L.new(lw.outputs["Facing"], inv.inputs[1])
            pw = N.new("ShaderNodeMath"); pw.operation = "POWER"; pw.inputs[1].default_value = 2.0; L.new(inv.outputs[0], pw.inputs[0])
            tr = N.new("ShaderNodeBsdfTransparent"); mix = N.new("ShaderNodeMixShader")
            L.new(pw.outputs[0], mix.inputs[0]); L.new(tr.outputs[0], mix.inputs[1]); L.new(em.outputs[0], mix.inputs[2])
            L.new(mix.outputs[0], o_.inputs["Surface"])
            try:
                m.surface_render_method = "BLENDED"
            except Exception:
                pass
        else:
            L.new(em.outputs[0], o_.inputs["Surface"])
        out.append(m)
    return out


def lay_route2(eye_fn, tpath, t0):
    """Erratic route (E2) that hits on contact. Wildness by distance travelled. Committed and within one side: the final
    corner and a strike (K1 snap / K2 coil / K3 pierce). Sides never longer than one normal side x scale."""
    l0, l1, a0, a1 = POLY["P3"]
    le, re = eye_fn(t0)
    head = (le + re) / 2
    corners = [head.copy()]; queue = []
    w0, T_c, a_max, l_burst = ERR[CURE["e"]]; roll = float(rng.uniform(0, 2 * math.pi))
    frames = {}; t_hit = None; info = {"strike": CURE["strike"]}; travelled = 0.0; striking = False
    D_c = SPEED * T_c                                  # the commit distance (blocks of beam laid)

    def speed_at(t):
        return float(np.linalg.norm(tpath[min(t + 1, len(tpath) - 1)] - tpath[t]))

    for t in range(t0, END + 1):
        vt = speed_at(t)
        scale = 1.0 + 0.4 * min(1.0, vt / 1.5)
        hspeed = max(SPEED, 0.95 * vt / 0.45) * CURE["hmul"]
        info.setdefault("max_head_speed", 0); info["max_head_speed"] = max(info["max_head_speed"], round(hspeed, 2))
        if t_hit is None and t - t0 <= TIMEOUT:
            step = hspeed
            while step > 1e-6 and t_hit is None:
                tgt = tpath[t]
                if not queue:
                    d = tgt - head; dist = float(np.linalg.norm(d))
                    w_t = min(1.0, w0 + (1 - w0) * (travelled / D_c) ** 1.5)
                    lead = int(min(40, dist / (hspeed * 0.45)))
                    aim = tpath[min(len(tpath) - 1, t + lead)]
                    if w_t > 0.6 and dist < 1.5 * l1 * scale and not striking:
                        striking = True
                        aim = tpath[min(len(tpath) - 1, t + int(dist / hspeed) + 1)]
                        u = aim - head; u = u / np.linalg.norm(u)
                        v_, w_ = perp_basis(u)
                        if CURE["strike"] == "K1":
                            kink = head + u * 0.35 * dist + (math.cos(roll) * v_ + math.sin(roll) * w_) * 0.6
                            queue = [kink, aim]
                        elif CURE["strike"] == "K2":
                            r_ = 0.9; ph = roll
                            p1 = aim + r_ * (math.cos(ph) * v_ + math.sin(ph) * w_) - u * 0.3
                            p2 = aim + r_ * (math.cos(ph + 2.1) * v_ + math.sin(ph + 2.1) * w_) + u * 0.2
                            queue = [p1, p2, aim]
                        else:
                            queue = [aim + u * 1.2]
                    else:
                        u = aim - head; u = u / np.linalg.norm(u)
                        rnd = rng.normal(0, 1, 3); rnd[2] += 0.3; rnd /= np.linalg.norm(rnd)
                        if head[2] > 12.0:
                            rnd[2] = -abs(rnd[2])
                        dv = w_t * u + (1 - w_t) * rnd; dv /= np.linalg.norm(dv)
                        roll += math.pi + float(rng.uniform(-1.2, 1.2))
                        v_, w_ = perp_basis(dv)
                        sd = math.cos(roll) * v_ + math.sin(roll) * w_
                        hi_a = a1 + (a_max - a1) * (1 - w_t) if w_t < 0.95 else (a0 + a1) / 2    # committed: keeps gaining
                        ang = math.radians(float(rng.uniform(a0, hi_a)))
                        hd = math.cos(ang) * dv + math.sin(ang) * sd
                        e = head + hd * float(rng.uniform(l0, l1)) * scale
                        if e[2] < 0.4:
                            e[2] = 0.4 + (0.4 - e[2])
                        e[2] = min(e[2], 14.0)
                        queue = [e]
                nxt = queue[0]
                d = nxt - head; dist = float(np.linalg.norm(d))
                adv = min(step, dist)
                # contact test along this step, a few samples
                n_s = max(1, int(adv / 0.25))
                for k in range(1, n_s + 1):
                    p_ = head + d / max(dist, 1e-6) * adv * k / n_s
                    if np.linalg.norm(p_ - tgt) <= HIT_R:
                        if CURE["strike"] != "K3" or not striking:
                            head = p_.copy(); corners.append(head.copy()); t_hit = t; travelled += adv * k / n_s
                            info["hit_on_contact"] = not striking
                            break
                        if t_hit is None:
                            t_hit = t; info["hit_on_contact"] = False          # pierce: hit, but carry on through
                if t_hit is not None and not (CURE["strike"] == "K3" and striking):
                    break
                head = head + d / max(dist, 1e-6) * adv; travelled += adv; step -= adv
                if adv >= dist - 1e-9:
                    corners.append(head.copy()); queue.pop(0)
                    if striking and not queue:
                        if t_hit is None:
                            t_hit = t; info["hit_on_contact"] = False
                        break
        frames[t] = ([c.copy() for c in corners], head.copy())
    info["hit"] = t_hit
    return frames, t_hit, info


def horse_path(base):
    return [base + np.array([-17.0 + 0.65 * t, -18.0 + 3.0 * math.sin(0.09 * t), 1.1]) for t in range(END + 2)]


def flyer_path(base):
    """A fast flyer: straight across at 1.5 blocks a tick (30 b/s), then a hard banking turn, then away."""
    out, p, hd = [], base + np.array([-30.0, -16.0, 7.0]), 0.0
    for t in range(END + 2):
        out.append(p.copy())
        if 40 <= t < 62:
            hd += math.pi / 22 * 0.9
        v = 1.5 * np.array([math.cos(hd), math.sin(-hd) * 0.8 - 0.0, 0.06 * math.sin(0.2 * t)])
        p = p + v
    return out


def swimmer_path(base):
    return [base + np.array([-12.0 + 0.3 * t, -14.0 + 2.0 * math.sin(0.1 * t), 2.5 + 0.6 * math.sin(0.15 * t)])
            for t in range(END + 2)]


EMBER_S, _ = emis("OB ember spark", (1.0, 0.2, 0.05), 7.0)
FLARE_M, _ = emis("OB corner flare", (1.0, 0.3, 0.2), 14.0)
BUB_M = bpy.data.materials.new("OB bubble"); BUB_M.use_nodes = True
_p = BUB_M.node_tree.nodes["Principled BSDF"]; _p.inputs["Base Color"].default_value = (0.85, 0.95, 1.0, 1)
_p.inputs["Roughness"].default_value = 0.05; _p.inputs["Alpha"].default_value = 0.55
_p.inputs["Emission Color"].default_value = (1.0, 0.7, 0.6, 1); _p.inputs["Emission Strength"].default_value = 0.35
try:
    BUB_M.surface_render_method = "BLENDED"
except Exception:
    pass
STEAM_M, _ = emis("OB steam", (0.9, 0.75, 0.75), 0.6, alpha=0.25)
WATER_M = bpy.data.materials.new("OB water"); WATER_M.use_nodes = True
_N = WATER_M.node_tree.nodes; _N.clear()
_vs = _N.new("ShaderNodeVolumeScatter"); _vs.inputs["Color"].default_value = (0.3, 0.55, 0.65, 1); _vs.inputs["Density"].default_value = 0.035
_va = _N.new("ShaderNodeVolumeAbsorption"); _va.inputs["Color"].default_value = (0.35, 0.7, 0.8, 1); _va.inputs["Density"].default_value = 0.06
_ad = _N.new("ShaderNodeAddShader"); _o = _N.new("ShaderNodeOutputMaterial")
WATER_M.node_tree.links.new(_vs.outputs[0], _ad.inputs[0]); WATER_M.node_tree.links.new(_va.outputs[0], _ad.inputs[1])
WATER_M.node_tree.links.new(_ad.outputs[0], _o.inputs["Volume"])
SURF_M = mat("OB water surface", (0.25, 0.5, 0.6), alpha=0.35)
SWIM_M = mat("OB swimmer", (0.2, 0.45, 0.4))


_ICO = {}


def ico(name, m, r):
    """Shared sphere meshes (one per material and size), so hundreds of bubbles build quickly."""
    key = (m.name, round(r, 3))
    if key not in _ICO:
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=r)
        o = bpy.context.active_object; me = o.data; me.materials.append(m)
        bpy.data.objects.remove(o); _ICO[key] = me
    return link(bpy.data.objects.new(name, _ICO[key]))


def drift(o, p0, t, life, vel, wob=0.0, grow=1.0, top=None):
    keyo(o, 1, loc=p0, scale=(0, 0, 0)); keyo(o, max(1, t - 1), loc=p0, scale=(0, 0, 0))
    for j in range(life + 1):
        p = p0 + vel * j + np.array([wob * math.sin(0.8 * j + t), wob * math.cos(0.7 * j + t), 0])
        s = (1 + (grow - 1) * j / life) * (1 if j < life - 2 else max(0, (life - j) / 2))
        if top is not None and p[2] >= top:
            keyo(o, t + j, loc=p, scale=(0, 0, 0)); break
        keyo(o, t + j, loc=p, scale=(s, s, s))


def torus(name, m, minor=0.05):
    bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=minor, major_segments=32, minor_segments=6)
    o = bpy.context.active_object
    for cc in list(o.users_collection):
        cc.objects.unlink(o)
    link(o); o.name = name; o.data.materials.append(m)
    return o


TAKES = [("K1", "horse", "fire"), ("K2", "horse", "fire"), ("K3", "horse", "fire"), ("F2", "flyer", "fire"),
         ("U3", "swimmer", "water"), ("U4", "swimmer", "water")]
ERRK = {k: "E2" for k, _, _ in TAKES}
STRIKE = {"K1": "K1", "K2": "K2", "K3": "K3", "F2": "K1", "U3": "K1", "U4": "K1"}
HMUL = {"U3": 1.6, "U4": 2.0}
NAMES = {"K1": "wild, snap strike", "K2": "wild, coil strike", "K3": "wild, pierce strike", "F2": "fast flyer, wild, snap",
         "U3": "under water, wild at 1.6x speed", "U4": "under water, wild at 2x speed"}
WATER_TOP = 8.0
for idx, (take, kind, env) in enumerate(TAKES):
    base = np.array([idx * LANE, 0.0, 0.0])
    objs = make_player(take); add_eyes(objs, take)
    tpath = {"horse": horse_path, "flyer": flyer_path, "swimmer": swimmer_path}[kind](base)
    CURE["e"] = ERRK[take]; CURE["strike"] = STRIKE[take]; CURE["hmul"] = HMUL.get(take, 1.0)
    T0 = 18
    poses = []
    for t in range(END + 1):
        o_ = base + np.array([0, -0.04 * max(0, t - 12), 0])
        p_ = walk(AIM, t) if (t >= 12 and env == "fire") else dict(AIM)
        d_ = tpath[t] - (o_ + np.array([0, 0, 1.6]))
        yaw = math.atan2(-d_[0], -d_[1]); pt = math.atan2(d_[2], math.hypot(d_[0], d_[1]))
        p_["head"] = (max(-0.6, min(0.6, -pt)), max(-1.0, min(1.0, -yaw)), 0)
        p_["body"] = (0.0, max(-0.5, min(0.5, -0.35 * yaw)), 0)
        s_ = solve(p_); set_pose(objs, s_, o_, t + 1); poses.append((s_, o_))
    eye_flash(take, T0 - 2, 110)
    eyes = lambda tt, P=poses: (eye_world(*P[min(tt, END)], which=0), eye_world(*P[min(tt, END)], which=1))
    frames, t_hit, info = lay_route2(eyes, tpath, T0)
    t_last = t_hit if t_hit is not None else T0 + TIMEOUT
    # the target
    if kind == "horse":
        root, legs = make_horse(f"OB {take}")
        for t in range(1, END + 1):
            tt = min(t, t_last); v = tpath[tt + 1] - tpath[tt]
            keyo(root, t, loc=tpath[tt] + np.array([0, 0, -1.1 + 0.08 * abs(math.sin(0.9 * tt))]),
                 rot=(0.04 * math.sin(0.9 * tt), 0, math.atan2(v[0], -v[1])))
            for li, lg in enumerate(legs):
                keyo(lg, t, rot=(0.6 * math.sin(0.9 * tt + (0.0 if li < 2 else math.pi) + (0.35 if li % 2 else 0.0)), 0, 0))
        tgt_obj, tsize = root, 1.5
    else:
        tgt_obj = cube(f"OB {take} {kind}", SWIM_M if kind == "swimmer" else MOB_M, 0.9); tsize = 0.9
        for t in range(1, END + 1):
            tt = min(t, t_last) if t_hit is not None else t
            keyo(tgt_obj, t, loc=tpath[tt])
    if t_hit is not None:
        incinerate(tgt_obj, tpath[t_hit], t_hit + 1, tsize)
        # strike flash at the hit: a ring and a burst of embers
        fr_ = torus(f"OB {take} strike ring", FLARE_M, 0.05)
        hp_ = tpath[t_hit]
        if fr_ is not None:
            keyo(fr_, 1, loc=hp_, scale=(0, 0, 0)); keyo(fr_, t_hit, loc=hp_, scale=(0, 0, 0))
            for j in range(1, 8):
                r_ = 0.3 + 0.25 * j
                keyo(fr_, t_hit + j, loc=hp_, scale=(r_, r_, r_) if j < 7 else (0, 0, 0))
    follow = link(bpy.data.objects.new(f"OB {take} target follow", None))
    for t in range(1, END + 1):
        keyo(follow, t, loc=tpath[min(t, t_last)])
    core_m, glow_m = fire_mats(take, True)
    le0, re0 = eyes(T0)
    overall = tpath[T0] - le0; overall[2] = 0
    side_g = np.cross(overall / (np.linalg.norm(overall) or 1), np.array([0, 0, 1.0])); side_g /= (np.linalg.norm(side_g) or 1)
    NMAX = max(len(fr[0]) for fr in frames.values()) + 1
    tubes = []
    for k in (0, 1):
        row = []
        for i in range(NMAX):
            c_ = link(bpy.data.objects.new(f"OB {take} b{k} core {i}", TUBE.copy())); c_.data.materials.append(core_m)
            g_ = link(bpy.data.objects.new(f"OB {take} b{k} glow {i}", TUBE.copy())); g_.data.materials.append(glow_m)
            row.append((c_, g_))
        tubes.append(row)
    lt = bpy.data.lights.new(take + " light", "POINT"); lt.color = RED; lt.shadow_soft_size = 0.1
    lo = link(bpy.data.objects.new(take + " beam light", lt))
    fin = frames[min(t_last, END)]; final_pts = fin[0] + [fin[1]]
    fseg = [float(np.linalg.norm(final_pts[i + 1] - final_pts[i])) for i in range(len(final_pts) - 1)]
    fcum = np.concatenate([[0], np.cumsum(fseg)])
    t_end = t_last + int(math.ceil(fcum[-1] / (SPEED * 2.5))) + 2
    rng_fx = np.random.default_rng(1514 + idx)
    seen_corners = 0
    last_drawn = None; t_gone = None
    for t in range(1, END + 1):
        le, re = eyes(t)
        live = T0 <= t <= t_end
        if live and t <= t_last:
            cs, hp = frames[t]; pts = cs + [hp]; tail_s = 0.0
            sg = [float(np.linalg.norm(pts[i + 1] - pts[i])) for i in range(len(pts) - 1)]
            cm = np.concatenate([[0], np.cumsum(sg)])
        elif live:
            pts = final_pts; sg = fseg; cm = fcum; tail_s = (t - t_last) * SPEED * 2.5
        else:
            pts = None
        drawn = []
        for k, row in enumerate(tubes):
            off = (-1 if k == 0 else 1) * SEP / 2 * side_g
            for i, (c_, g_) in enumerate(row):
                if pts is None or i >= len(pts) - 1 or cm[i + 1] <= tail_s + 1e-4 or sg[i] < 1e-4:
                    keyo(c_, t, scale=(0, 0, 0)); keyo(g_, t, scale=(0, 0, 0)); continue
                A_ = pts[i] + off; B_ = pts[i + 1] + off
                if i == 0 and tail_s <= 0.0:
                    A_ = le if k == 0 else re
                if tail_s > cm[i]:
                    A_ = A_ + (B_ - A_) * ((tail_s - cm[i]) / sg[i])
                mid = (A_ + B_) / 2; v = B_ - A_; ln = float(np.linalg.norm(v))
                yaw = math.atan2(v[1], v[0]); pitch = math.atan2(v[2], math.hypot(v[0], v[1]))
                keyo(c_, t, loc=mid, scale=(ln + 0.02, 0.02, 0.02), rot=(0, -pitch, yaw))
                keyo(g_, t, loc=mid, scale=(ln + 0.1, 0.07, 0.07), rot=(0, -pitch, yaw))
                drawn.append((A_, B_, ln))
        if pts is not None:
            lo.location = tuple(pts[-1]); lo.keyframe_insert("location", frame=t)
        lt.energy = 110.0 if live else 0.0; lt.keyframe_insert("energy", frame=t)
        if drawn:
            last_drawn = drawn
        elif last_drawn is not None and env == "water":
            # the sleeve fizzes on for 0.4 s where the beam was, fading fast
            if t_gone is None:
                t_gone = t
            k_ = t - t_gone
            if k_ < 8:
                drawn = last_drawn; nfz = max(0, 9 - k_ - k_ // 2)
                lens = np.array([d[2] for d in drawn]); prob = lens / lens.sum()
                for n in range(nfz):
                    A_, B_, _ = drawn[int(rng_fx.choice(len(drawn), p=prob))]
                    p0 = A_ + (B_ - A_) * float(rng_fx.random())
                    drift(ico(f"OB {take} fizz {t} {n}", BUB_M, 0.05), p0, t, 4, np.array([0, 0, 0.05]), wob=0.02)
            continue
        if not drawn:
            continue
        lens = np.array([d[2] for d in drawn]); prob = lens / lens.sum()
        def pick():
            A_, B_, _ = drawn[int(rng_fx.choice(len(drawn), p=prob))]
            return A_ + (B_ - A_) * float(rng_fx.random())
        if env == "fire":
            for n in range(2):
                p0 = pick(); v = rng_fx.normal(0, 0.035, 3); v[2] = abs(v[2]) + 0.015
                drift(cube(f"OB {take} ember {t} {n}", EMBER_S, 0.045), p0, t, 8, v)
            if False:
                while seen_corners < len(pts) - 2:
                    seen_corners += 1
                    fl = ico(f"OB {take} flare {seen_corners}", FLARE_M, 0.12); cpt = pts[seen_corners]
                    keyo(fl, 1, loc=cpt, scale=(0, 0, 0)); keyo(fl, t - 1, loc=cpt, scale=(0, 0, 0))
                    for j in range(10):
                        keyo(fl, t + j, loc=cpt, scale=((1.6 - 0.15 * j) * (1 + 0.3 * math.sin(j * 1.7)),) * 3)
                    keyo(fl, t + 10, loc=cpt, scale=(0, 0, 0))
        else:
            for n in range(9):
                p0 = pick()
                if True:
                    drift(ico(f"OB {take} bub {t} {n}", BUB_M, 0.05), p0, t, 4, np.array([0, 0, 0.05]), wob=0.02)
                else:
                    r_ = float(rng_fx.uniform(0.05, 0.1))
                    drift(ico(f"OB {take} bub {t} {n}", BUB_M, r_), p0, t, 40, np.array([0, 0, 0.06]), wob=0.04,
                          grow=1.4, top=WATER_TOP)
            if False:
                while seen_corners < len(pts) - 2:
                    seen_corners += 1
                    stp = ico(f"OB {take} steam {seen_corners}", STEAM_M, 0.18)
                    drift(stp, pts[seen_corners], t, 22, np.array([0, 0, 0.05]), wob=0.03, grow=2.2, top=WATER_TOP)
    if env == "water":
        bpy.ops.mesh.primitive_cube_add(size=1, location=tuple(base + np.array([0, -8, WATER_TOP / 2])))
        wb = bpy.context.active_object
        for cc in list(wb.users_collection):
            cc.objects.unlink(wb)
        link(wb); wb.name = f"OB {take} water"; wb.scale = (36, 40, WATER_TOP); wb.data.materials.append(WATER_M)
        bpy.ops.mesh.primitive_plane_add(size=1, location=tuple(base + np.array([0, -8, WATER_TOP])))
        sf = bpy.context.active_object
        for cc in list(sf.users_collection):
            cc.objects.unlink(sf)
        link(sf); sf.name = f"OB {take} surface"; sf.scale = (36, 40, 1); sf.data.materials.append(SURF_M)
    vt0 = float(np.linalg.norm(tpath[T0 + 1] - tpath[T0]))
    dump["takes"][take] = {"name": NAMES[take], "fire": T0, "target_speed_bpt": round(vt0, 2), **info,
                           "gave_up": t_hit is None}
    cu = bpy.data.curves.new("OB label " + take, "FONT"); cu.body = f"{take}  {NAMES[take]}"
    cu.size = 0.5; cu.align_x = "CENTER"
    tl = link(bpy.data.objects.new("OB label " + take, cu)); tl.location = tuple(base + np.array([0, 2.0, 0.01]))
    tl.data.materials.append(mat("OB label", (1.0, 0.8, 0.8), emit=2.0))
    cam(f"Cam {take}", tuple(base + np.array([-1.2, 3.0, 2.5])), tuple(base + np.array([0.3, -12.0, 1.8 if kind != "flyer" else 4.0])), 24)
    cam(f"Cam {take} wide", tuple(base + np.array([22.0, 8.0, 20.0])), tuple(base + np.array([0, -14.0, 2.0])), 26)
    m0 = tpath[T0]
    ct = cam(f"Cam {take} target", tuple(m0 + np.array([6.0, -6.0, 3.0])), tuple(m0), 30)
    ct.parent = follow; ct.matrix_parent_inverse = Matrix.Translation(Vector(m0)).inverted()
    print(take, "built:", dump["takes"][take]["hit"], info, flush=True)

with open(os.path.join(FOLDER, "omega_strike_poses.json"), "w") as fh:
    json.dump(dump, fh, separators=(",", ":"))
scene.frame_start, scene.frame_end = 1, END
bpy.ops.mesh.primitive_plane_add(size=1, location=(LANE * 3, -8, 0))
g = bpy.context.active_object
for c in g.users_collection:
    c.objects.unlink(g)
link(g); g.name = "OB ground"; g.scale = (320, 90, 1); g.data.materials.append(mat("OB ground", (0.14, 0.2, 0.1)))
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
try:
    tree = bpy.data.node_groups.new("OB Glow", "CompositorNodeTree")
    tree.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    rl = tree.nodes.new("CompositorNodeRLayers"); go = tree.nodes.new("NodeGroupOutput")
    gl = tree.nodes.new("CompositorNodeGlare")
    if "Type" in gl.inputs:
        gl.inputs["Type"].default_value = "Bloom"
    for nm, val in (("Size", 0.7), ("Strength", 0.7), ("Threshold", 0.9)):
        if nm in gl.inputs:
            gl.inputs[nm].default_value = val
    tree.links.new(rl.outputs["Image"], gl.inputs["Image"]); tree.links.new(gl.outputs["Image"], go.inputs[0])
    scene.compositing_node_group = tree
except Exception as e:
    print("no glow:", e)
scene.camera = bpy.data.objects["Cam K1 wide"]
try:
    bpy.ops.outliner.orphans_purge(do_recursive=True)
except Exception:
    pass
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("saved", OUT)
