# Pass 219: charging at the lantern (lead Blender chat, 2026-10-14). J picked it next: the full charge ritual. The
# Dark Lantern (kl_assets), knee rig, 20 ticks a second; one charge is 8 s (160 ticks) like the game's, then a flare
# and 30 ticks to settle. Light streams out of the lantern's port into the ring the whole time, faster and brighter as
# the charge builds; the lantern's glow breathes, the ring builds to a flare, and a ring of light bursts at the end.
#   C1 oath kneel: down on the ring knee, head bowed, ring fist held to the port; halfway the head comes up.
#   C2 lantern raised: standing, the lantern held up by its handle in the free hand, ring fist to the port.
#   C3 both knees: on both knees, both hands round the lantern, the ring hand over the port, head bowed.
# Cameras "Cam C1".."Cam C3" (over the right shoulder), "Cam C1 front".., "Cam all". Builds LanternLive\lantern_charge.blend.
import json, math, os
import bpy
import numpy as np
from mathutils import Matrix

R = math.radians
ASSETS = os.path.join(FOLDER, "kl_assets")
OUT = os.path.join(FOLDER, "lantern_charge.blend")
if bpy.data.filepath:
    try:
        bpy.ops.wm.save_mainfile()
    except Exception as e:
        print("save current:", e)
old = bpy.data.scenes.get("Lantern Charge")
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new("Lantern Charge")
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


def import_lantern(tag):
    root = link(bpy.data.objects.new(f"LC {tag} lantern", None))
    root.empty_display_size = 0.05
    glow_mats = []
    for name in ("dark_lantern", "dark_lantern_glow"):
        path = os.path.join(ASSETS, name + ".glb")
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=path)
        new = [o for o in bpy.data.objects if o not in before]
        for o in new:
            for c in list(o.users_collection):
                c.objects.unlink(o)
            col.objects.link(o)
            if o.type == "MESH":
                mats = []
                for i, m in enumerate(o.data.materials):
                    if m is None:
                        continue
                    m2 = m.copy(); m2.name = f"LC {tag} {m.name}"
                    o.data.materials[i] = m2
                    for n in m2.node_tree.nodes:
                        if n.type == "TEX_IMAGE":
                            n.interpolation = "Closest"
                    if "glow" in m.name.lower() or name.endswith("glow"):
                        bsdf = next((n for n in m2.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
                        tex = next((n for n in m2.node_tree.nodes if n.type == "TEX_IMAGE"), None)
                        if bsdf is not None:
                            if tex is not None:
                                m2.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Emission Color"])
                            else:
                                bsdf.inputs["Emission Color"].default_value = (0.15, 1.0, 0.3, 1)
                            glow_mats.append(bsdf)
        tops = [o for o in new if o.parent is None]
        for o in tops:
            o.parent = root
    # fit: base centre at the root, 16 px (1 block) tall
    bpy.context.view_layer.update()
    from mathutils import Vector
    pts = []
    for o in root.children_recursive:
        if o.type == "MESH":
            pts += [o.matrix_world @ Vector(c) for c in o.bound_box]
    if pts:
        P_ = np.array([tuple(p) for p in pts])
        lo, hi = P_.min(0), P_.max(0)
        s = (LH / 16.0) / max(hi[2] - lo[2], 1e-6)
        print("lantern mesh", tag, "w", round((hi[0] - lo[0]) * s * 16, 2), "d", round((hi[1] - lo[1]) * s * 16, 2), "h px", LH, "model hw*2", round(2 * HW, 2))
        for o in root.children:
            o.matrix_world = Matrix.Scale(s, 4) @ Matrix.Translation((-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2])) @ o.matrix_world
    return root, glow_mats



LH = 16.0; DL_H, DL_W, DL_BODY = 28.5, 11.0, 21.0
HW = DL_W * LH / DL_H / 2; BODY_H = DL_BODY * LH / DL_H
PORT_Y = BODY_H * 0.52
CHARGE, END = 160, 190
rng = np.random.default_rng(219)

POSES = {
    "C1": dict(body=(0.12, 0, 0), head=(0.55, 0, 0), ring=(-1.0, 0, 0.1), free=(-0.25, 0.2, -0.25),
               ringleg=(0.15, 0, 0.04), ringknee=1.25, freeleg=(-1.2, 0, -0.06), freeknee=1.3),
    "C2": dict(body=(0.05, 0, 0), head=(0.15, 0, 0), ring=(-1.4, 0.15, 0.1), free=(-1.35, -0.25, -0.1),
               ringleg=(0.15, 0, 0.04), ringknee=0.1, freeleg=(-0.15, 0, -0.04), freeknee=0.1),
    "C3": dict(body=(0.3, 0, 0), head=(0.7, 0, 0), ring=(-0.85, -0.3, 0.1), free=(-0.85, -0.3, -0.1),
               ringleg=(0.05, 0, 0.06), ringknee=1.55, freeleg=(0.05, 0, -0.06), freeknee=1.55),
}


def fist(sol, part="rarm"):
    return hand_point(sol, part)


def place(take):
    """The pose with the ring fist at the port, and where the lantern stands (rig space, base centre, yaw)."""
    p = dict(POSES[take])
    if take == "C2":
        # the free hand holds the handle in front of the chest; the lantern hangs from it, port facing him
        sol = solve(p)
        grip = fist(sol, "larm")
        base = grip + np.array([0.0, LH - 0.5, 0.0])
        port = base + np.array([0.0, -PORT_Y, HW])
        best = None
        for x in np.arange(-2.4, -0.4, 0.01):
            for y in np.arange(-0.6, 0.8, 0.02):
                q = dict(p, ring=(x, y, 0.1)); tip = fist(solve(q))
                e = float(np.linalg.norm(tip - (port + np.array([0, 0, 0.6]))))
                if best is None or e < best[0]:
                    best = (e, x, y)
        p["ring"] = (best[1], best[2], 0.1)
        return p, base, 0.0          # the port (the emblem) faces him
    # on the ground in front: tilt the ring arm until the fist is at port height, then stand the lantern there
    target_y = GROUND - PORT_Y
    best = None
    for x in np.arange(-2.2, 0.2, 0.005):
        q = dict(p, ring=(x, p["ring"][1], p["ring"][2])); tip = fist(solve(q))
        e = abs(tip[1] - target_y) - 0.02 * (-tip[2])
        if best is None or e < best[0]:
            best = (e, x)
    p["ring"] = (best[1], p["ring"][1], p["ring"][2])
    tip = fist(solve(p))
    base = np.array([tip[0], GROUND, tip[2] - HW - 0.6])            # port face just past the knuckles
    if take == "C3":                                                 # the free hand rests on the lantern's side
        p["free"] = (p["ring"][0], -p["ring"][1] * 0.6, -0.1)
    return p, base, 0.0


def bl_m(M_rig, origin):
    out = np.eye(4); out[:3, :3] = A @ M_rig[:3, :3] @ A.T; out[:3, 3] = to_bl(M_rig[:3, 3]) + np.asarray(origin)
    return Matrix(out.tolist())


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


def charge_curve(t):
    return smooth(min(1.0, t / CHARGE))


TAKES = {"C1": "oath kneel", "C2": "lantern raised", "C3": "both knees"}
for k, (take, nm) in enumerate(TAKES.items()):
    origin = np.array([k * 5.0, 0.0, 0.0])
    p, base, yaw = place(take)
    objs = make_player(take)
    rm, _ = emis(f"LC ring {take}", (0.1, 1.0, 0.25), 2.0); objs["ring"].data.materials[0] = rm
    root, glows = import_lantern(take)
    Ry = np.array([[math.cos(yaw), 0, math.sin(yaw)], [0, 1, 0], [-math.sin(yaw), 0, math.cos(yaw)]])
    M = np.eye(4); M[:3, :3] = Ry; M[:3, 3] = base
    root.matrix_world = bl_m(M, origin)
    port = base + Ry @ np.array([0.0, -PORT_Y, HW])
    # the light stream: motes leave the port and fly into the ring, more and faster as the charge builds
    sm, se = emis(f"LC stream {take}", (0.3, 1.0, 0.5), 9.0)
    POOL = 60
    motes = [cube(f"LC {take} mote {i}", sm, 0.05) for i in range(POOL)]
    for m_ in motes:
        m_.scale = (0, 0, 0); m_.keyframe_insert("scale", frame=1)
    nxt, acc = 0, 0.0
    head_up = take == "C1"
    for t in range(END + 1):
        c = charge_curve(t)
        q = dict(p)
        if head_up:
            hx = 0.55 - 0.75 * smooth(min(1, max(0, (t - 70) / 20)))
            q["head"] = (hx, 0, 0)
        sol = solve(q)
        set_pose(objs, sol, origin, t + 1)
        ringp = fist(sol)
        # ring: builds with the charge, flares at the end, settles
        e = 2.0 + 10.0 * c
        if CHARGE <= t < CHARGE + 6:
            e = 40.0
        elif t >= CHARGE + 6:
            e = 3.0 + 9.0 * math.exp(-(t - CHARGE - 6) / 8)
        s_ = rm.node_tree.nodes["Emission"].inputs["Strength"]; s_.default_value = e; s_.keyframe_insert("default_value", frame=t + 1)
        for bsdf in glows:
            g_ = bsdf.inputs["Emission Strength"]
            g_.default_value = (1.0 + 6.0 * c * (0.75 + 0.25 * math.sin(t * 0.35))) if t < CHARGE else 1.0 + 6.0 * math.exp(-(t - CHARGE) / 10)
            g_.keyframe_insert("default_value", frame=t + 1)
        if t < CHARGE:
            acc += 0.4 + 2.2 * c
            while acc >= 1.0:
                acc -= 1.0
                mo = motes[nxt % POOL]; nxt += 1
                life = max(5, int(14 - 8 * c))
                wob = rng.normal(0, 0.8, 3)
                mo.scale = (0, 0, 0); mo.keyframe_insert("scale", frame=t + 1)
                for j in range(life + 1):
                    u = j / life
                    pt = port + (ringp - port) * u + wob * math.sin(math.pi * u)
                    mo.location = tuple(to_bl(pt) + origin); mo.keyframe_insert("location", frame=t + 2 + j)
                    sz = 0.6 + 0.8 * c
                    mo.scale = (sz, sz, sz); mo.keyframe_insert("scale", frame=t + 2 + j)
                mo.scale = (0, 0, 0); mo.keyframe_insert("scale", frame=t + 3 + life)
    # the burst at full charge: a ring of light round him
    bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.03, major_segments=48, minor_segments=6)
    tor = bpy.context.active_object
    for cc in list(tor.users_collection):
        cc.objects.unlink(tor)
    link(tor); tor.name = f"LC {take} burst"
    tm, _ = emis(f"LC burst {take}", (0.5, 1.0, 0.65), 10.0, alpha=0.7); tor.data.materials.append(tm)
    tor.location = tuple(origin + np.array([0, 0, 0.5]))
    for f, sc in ((1, 0), (CHARGE, 0), (CHARGE + 1, 0.3), (CHARGE + 14, 3.5), (CHARGE + 15, 0)):
        tor.scale = (sc, sc, sc); tor.keyframe_insert("scale", frame=f)
    cu = bpy.data.curves.new("LC label " + take, "FONT"); cu.body = f"{take}  {nm}"; cu.size = 0.35; cu.align_x = "CENTER"
    tl = link(bpy.data.objects.new("LC label " + take, cu)); tl.location = tuple(origin + np.array([0, 1.4, 0.01]))
    tl.data.materials.append(mat("LC label", (0.8, 1.0, 0.85), emit=2.0))
    cam(f"Cam {take}", tuple(origin + np.array([-1.0, 3.0, 2.3])), tuple(origin + np.array([0.15, -1.4, 0.5])), 30)
    cam(f"Cam {take} front", tuple(origin + np.array([1.6, -3.4, 1.3])), tuple(origin + np.array([0, -0.4, 0.75])), 35)
    print(take, "built", flush=True)

scene.frame_start, scene.frame_end = 1, END
bpy.ops.mesh.primitive_plane_add(size=40, location=(5, 0, 0))
g = bpy.context.active_object
for c in g.users_collection:
    c.objects.unlink(g)
link(g); g.name = "LC ground"; g.data.materials.append(mat("LC ground", (0.06, 0.07, 0.065)))
world = bpy.data.worlds.new("LC world"); world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.02, 0.025, 0.035, 1)
scene.world = world
key = bpy.data.lights.new("LC key", "AREA"); key.energy = 400; key.size = 8
ko = link(bpy.data.objects.new("LC key", key)); ko.location = (5, -6, 6); ko.rotation_euler = (R(45), 0, 0)
try:
    scene.render.engine = "BLENDER_EEVEE"
except Exception:
    scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x, scene.render.resolution_y = 1600, 900
try:
    scene.view_settings.view_transform = "Standard"
except Exception:
    pass
cam("Cam all", (5, -12, 4), (5, 0, 0.8), 30)
scene.camera = bpy.data.objects["Cam C1"]
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
