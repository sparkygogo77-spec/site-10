# Pass 218: flight trail and speed effects (lead Blender chat, 2026-10-14). J picked "Flight trail + speed FX".
# One flyer per lane, in the cruise pose with the ring arm forward (J's arm style A), speeding up from 0.3 to 1.5
# blocks a tick over 4 s, so every effect is seen growing with speed. The cameras ride along (over the shoulder, side).
#   T1 ribbon: a light ribbon off the ring hand; it widens and stretches as he speeds up and fades along its length.
#   T2 sparks: construct pixels shed off the body; more of them the faster he goes, each drifting and shrinking away.
#   T3 wind: thin white streaks rushing past him; longer and more of them with speed.
#   T5 three thin trails: off both feet and the ring hand (J's pick for where the trail comes from).
# Wind only shows once he is flying fast (J): above 0.8 blocks a tick.
#   T4 all of it: a thin ribbon, the wind, and a ring of light that bursts out when he passes 1.1 blocks a tick.
# Builds LanternLive\flight_fx.blend.
import json, math, os
import bpy
import numpy as np
from mathutils import Matrix

R = math.radians
OUT = os.path.join(FOLDER, "flight_fx.blend")
if bpy.data.filepath:
    try:
        bpy.ops.wm.save_mainfile()
    except Exception as e:
        print("save current:", e)
old = bpy.data.scenes.get("Flight FX")
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new("Flight FX")
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


# ------------------------------------------------------------------ the run cycle
STRIDE, LOOP, SPEED = 12, 48, 0.28          # ticks a stride, ticks a loop, blocks a tick


def legs(ph, amp=0.85, lean=0.0):
    """Thigh and knee for one leg at phase ph: the thigh swings (forward is negative), the knee folds most while the
    leg comes through under the body and is nearly straight as the foot strikes out in front."""
    thigh = 0.15 - amp * math.sin(ph) - lean * 0.5
    knee = 0.12 + 1.45 * ((1 + math.cos(ph + 0.35)) / 2) ** 2
    return thigh, knee


def run_pose(take, t):
    ph = 2 * math.pi * t / STRIDE
    amp = {"S3": 1.0}.get(take, 0.85)
    lean = {"S1": 0.26, "S2": 0.3, "S3": 0.46, "S4": 0.24}[take]
    tr, kr = legs(ph, amp, lean)
    tf, kf = legs(ph + math.pi, amp, lean)
    swing = math.sin(ph)
    p = dict(body=(lean + 0.03 * math.sin(2 * ph), 0.07 * swing, 0.0), head=(-lean * 0.8, -0.05 * swing, 0.0),
             ringleg=(tr, 0, 0.02), ringknee=kr, freeleg=(tf, 0, -0.02), freeknee=kf)
    free_swing = 0.15 - 0.95 * swing
    if take == "S1":
        p["ring"] = (-1.42 + 0.06 * math.sin(2 * ph), 0.06, 0.05)
        p["free"] = (free_swing, 0, -0.08)
    elif take == "S2":
        p["ring"] = (0.15 + 0.95 * swing, 0, 0.08)
        p["free"] = (free_swing, 0, -0.08)
    elif take == "S3":
        p["ring"] = (1.05 + 0.08 * swing, 0, 0.22)
        p["free"] = (0.15 - 1.1 * swing, 0, -0.1)
    else:                                       # S4: the free hand carries the lantern low at the hip
        p["ring"] = (0.15 + 0.95 * swing, 0, 0.08)
        p["free"] = (-0.1 - 0.25 * swing, 0, -0.18)
    return p



FLYA = dict(body=(1.42, 0, 0), head=(-1.25, 0, 0), ring=(-1.57, 0, 0.02), free=(1.35, 0, -0.12),
            ringleg=(1.38, 0, 0.03), ringknee=0.25, freeleg=(1.3, 0, -0.03), freeknee=0.4, grounded=False)
END, H = 90, 3.0
rng = np.random.default_rng(218)


def speed(t):
    return 0.3 + 1.2 * smooth(min(1.0, t / 80))


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
    return m


def cube(name, m, size=1.0):
    me = bpy.data.meshes.new(name)
    h = size / 2
    v = [(x, y, z) for x in (-h, h) for y in (-h, h) for z in (-h, h)]
    me.from_pydata(v, [], [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)])
    me.materials.append(m)
    return link(bpy.data.objects.new(name, me))


def key(o, f, loc=None, scale=None):
    if loc is not None:
        o.location = tuple(loc); o.keyframe_insert("location", frame=f)
    if scale is not None:
        o.scale = tuple(scale); o.keyframe_insert("scale", frame=f)


LANES = {"T1": 0.0, "T2": 5.0, "T3": 10.0, "T4": 15.0, "T5": 20.0}
NAMES = {"T1": "ribbon", "T2": "sparks", "T3": "wind", "T4": "all + speed ring", "T5": "feet + ring trails"}
for take, ox in LANES.items():
    objs = make_player(take)
    rm = mat(f"FX ring {take}", (0.1, 1.0, 0.25), emit=6.0); objs["ring"].data.materials[0] = rm
    mover = link(bpy.data.objects.new(f"FX {take} mover", None))
    pos, hands, bodies, feet = [], [], [], {}
    y = 0.0
    for t in range(END + 1):
        y -= speed(t)
        origin = np.array([ox, y, H])
        sol = solve(FLYA)
        set_pose(objs, sol, origin, t + 1)
        key(mover, t + 1, loc=origin)
        hands.append(to_bl(hand_point(sol, "rarm")) + origin)
        for side_, shin in (("r", "rshin"), ("l", "lshin")):
            r_, pv_ = sol[shin]
            feet.setdefault(side_, []).append(to_bl(np.array([0.0, 6.0, 0.0]) @ rot(*r_).T + pv_) + origin)
        bodies.append(to_bl(sol["body"][1]) + origin + np.array([0, 0.35, 0]))
        pos.append(origin)
    # ---- ribbon: a chain of glowing segments laid along the ring hand's last positions
    trails = []
    if take in ("T1", "T4"):
        trails.append(("ring", hands, 1.0 if take == "T1" else 0.5))
    if take == "T5":
        trails += [("ring", hands, 0.7), ("rfoot", feet["r"], 0.45), ("lfoot", feet["l"], 0.45)]
    for tname, path, thin in trails:
        NSEG = 24
        segs = [cube(f"FX {take} {tname} {i}", emis(f"FX ribbon {take} {tname} {i}", (0.15, 1.0, 0.35), 2.2 * (1 - i / NSEG) + 0.4,
                                                    alpha=max(0.08, 0.9 * (1 - i / NSEG))), 1.0) for i in range(NSEG)]
        for t in range(END + 1):
            for i, sgo in enumerate(segs):
                a = path[max(0, t - i)]; b = path[max(0, t - i - 1)]
                mid = (a + b) / 2; ln = max(0.02, float(np.linalg.norm(a - b)))
                w = (0.03 + 0.05 * speed(t)) * thin * (1 - 0.6 * i / NSEG)
                key(sgo, t + 1, loc=mid, scale=(w, ln, w * 0.4))
    # ---- sparks: construct pixels shed off the body, more with speed
    if take == "T2":
        POOL, LIFE = 70, 16
        pm = emis("FX spark", (0.3, 1.0, 0.5), 8.0)
        sparks = [cube(f"FX spark {i}", pm, 0.07) for i in range(POOL)]
        for s_ in sparks:
            key(s_, 1, scale=(0, 0, 0))
        nxt, acc = 0, 0.0
        for t in range(END - LIFE):
            acc += 1.2 * speed(t) ** 1.5
            while acc >= 1.0:
                acc -= 1.0
                s_ = sparks[nxt % POOL]; nxt += 1
                p0 = bodies[t] + rng.normal(0, [0.18, 0.4, 0.12])
                drift = rng.normal(0, 0.012, 3) + np.array([0, 0.02, 0.004])
                key(s_, t, scale=(0, 0, 0))
                for k in range(LIFE + 1):
                    sz = 1.0 - k / LIFE
                    key(s_, t + 1 + k, loc=p0 + drift * k, scale=(sz, sz, sz))
    # ---- wind: thin streaks rushing past, longer with speed
    if take in ("T3", "T4"):
        WM = emis("FX wind", (0.9, 0.97, 1.0), 2.5, alpha=0.35)
        NW = 22
        streaks = [cube(f"FX {take} wind {i}", WM, 1.0) for i in range(NW)]
        offs = [np.array([rng.uniform(-1.4, 1.4), rng.uniform(-2.0, 6.0), rng.uniform(-0.9, 1.3)]) for _ in range(NW)]
        for t in range(END + 1):
            v = speed(t)
            for i, st in enumerate(streaks):
                o = offs[i]
                o[1] += 0.9 * v + 0.15                    # rushes back past the flyer
                if o[1] > 6.0:
                    o[:] = [rng.uniform(-1.4, 1.4), -3.0, rng.uniform(-0.9, 1.3)]
                    if abs(o[0]) < 0.45 and -0.6 < o[2] < 0.7:
                        o[0] += 0.9 * np.sign(o[0] or 1)
                ln = 0.2 + 1.4 * v
                vis = 1.0 if v > 0.8 and (i / NW) < (v - 0.8) / 0.7 else 0.0      # J: only when fast
                key(st, t + 1, loc=pos[t] + o, scale=(0.012 * vis, ln * vis, 0.012 * vis))
    # ---- speed ring: bursts out once he passes 1.1 blocks a tick
    if take == "T4":
        tb = next(t for t in range(END) if speed(t) >= 1.1)
        bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.04, major_segments=48, minor_segments=8)
        ring_o = bpy.context.active_object
        for c in list(ring_o.users_collection):
            c.objects.unlink(ring_o)
        link(ring_o); ring_o.name = "FX speed ring"; ring_o.rotation_euler = (R(90), 0, 0)
        ring_o.data.materials.append(emis("FX speed ring", (0.5, 1.0, 0.65), 10.0, alpha=0.6))
        key(ring_o, 1, loc=pos[tb], scale=(0, 0, 0)); key(ring_o, tb, loc=pos[tb], scale=(0, 0, 0))
        for k in range(1, 13):
            sc = 0.4 + 0.35 * k
            key(ring_o, tb + k, loc=pos[tb], scale=(sc, sc, sc * (1 - k / 13) + 0.01))
        key(ring_o, tb + 13, loc=pos[tb], scale=(0, 0, 0))
    cu = bpy.data.curves.new("FX label " + take, "FONT"); cu.body = f"{take}  {NAMES[take]}"; cu.size = 0.35; cu.align_x = "CENTER"
    tl = link(bpy.data.objects.new("FX label " + take, cu)); tl.location = (ox, 1.5, 0.01)
    tl.data.materials.append(mat("FX label", (0.8, 1.0, 0.85), emit=2.0))
    for nm_, loc, look, lens in ((f"Cam {take}", (-0.6, 2.4, 1.0), (0.1, -3.0, 0.0), 28),
                                 (f"Cam {take} side", (5.0, -0.6, 0.4), (0, -0.6, 0.1), 30)):
        c = cam(nm_, (ox + loc[0], loc[1], H + loc[2]), (ox + look[0], look[1], H + look[2]), lens)
        scene.frame_set(1); bpy.context.view_layer.update()      # parent while the mover is at its start
        mw = c.matrix_world.copy(); c.parent = mover; c.matrix_world = mw
    print(take, "built", flush=True)

scene.frame_start, scene.frame_end = 1, END
bpy.ops.mesh.primitive_plane_add(size=1, location=(7.5, -50, 0))
g = bpy.context.active_object
for c in g.users_collection:
    c.objects.unlink(g)
link(g); g.name = "FX ground"; g.scale = (60, 140, 1)
gm = bpy.data.materials.new("FX ground"); gm.use_nodes = True
N, Lk = gm.node_tree.nodes, gm.node_tree.links
ck = N.new("ShaderNodeTexChecker"); ck.inputs["Scale"].default_value = 140
ck.inputs["Color1"].default_value = (0.2, 0.36, 0.13, 1); ck.inputs["Color2"].default_value = (0.24, 0.42, 0.16, 1)
Lk.new(ck.outputs["Color"], N.get("Principled BSDF").inputs["Base Color"])
g.data.materials.append(gm)
world = bpy.data.worlds.new("FX world"); world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.25, 0.32, 0.45, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.6
scene.world = world
sun = link(bpy.data.objects.new("FX sun", bpy.data.lights.new("FX sun", "SUN")))
sun.data.energy = 2.5; sun.rotation_euler = (R(50), R(-10), R(-35))
try:
    scene.render.engine = "BLENDER_EEVEE"
except Exception:
    scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x, scene.render.resolution_y = 1600, 900
try:
    scene.view_settings.view_transform = "Standard"
except Exception:
    pass
scene.camera = bpy.data.objects["Cam T4"]
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
