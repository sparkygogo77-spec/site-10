# Pass 221: combat poses (lead Blender chat, 2026-10-14). J picked them next. Knee rig, 20 ticks a second, each take a
# loop with its power shown as a simple stand-in (the game draws the real effects). Ring on the right hand.
#   P1 ring punch: guard, a straight ring jab with a flash on impact, back to guard (two jabs a loop).
#   P2 blast: wide stance, free hand braces the ring wrist, the ring charges, fires a bolt, recoil, reset.
#   P3 shield block: crouched behind the raised ring arm, a hard-light shield in front; a hit lands and he's shoved back.
#   P4 beam hold: braced, ring arm locked out, a steady beam with a slight shake, leaning into it.
#   P5 summon wall: both arms sweep up from low and a hard-light wall rises in front.
#   P6 ground slam: leaps a little, ring fist down into the ground, a ring of light spreads out (the Shockwave).
# Cameras "Cam P1".."Cam P6" (over the right shoulder), "Cam P1 front".., "Cam all". Builds LanternLive\combat_poses.blend.
import json, math, os
import bpy
import numpy as np
from mathutils import Matrix

R = math.radians
ASSETS = os.path.join(FOLDER, "kl_assets")
OUT = os.path.join(FOLDER, "combat_poses.blend")
if bpy.data.filepath:
    try:
        bpy.ops.wm.save_mainfile()
    except Exception as e:
        print("save current:", e)
old = bpy.data.scenes.get("Combat Poses")
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new("Combat Poses")
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



def P(**k):
    return k


GUARD = P(body=(0.15, -0.35, 0), head=(0.05, 0.3, 0), ring=(-1.15, 0.45, 0.25), free=(-1.25, -0.5, -0.2),
          ringleg=(0.35, 0, 0.12), ringknee=0.35, freeleg=(-0.35, 0, -0.1), freeknee=0.4)
JAB = P(body=(0.22, 0.25, 0), head=(0.0, -0.2, 0), ring=(-1.57, 0.0, 0.05), free=(-1.3, -0.55, -0.2),
        ringleg=(0.45, 0, 0.12), ringknee=0.2, freeleg=(-0.45, 0, -0.1), freeknee=0.45)
BLAST_SET = P(body=(0.1, -0.2, 0), head=(0.0, 0.15, 0), ring=(-1.5, 0.1, 0.05), free=(-1.45, -0.45, -0.1),
              ringleg=(0.45, 0, 0.25), ringknee=0.45, freeleg=(-0.45, 0, -0.25), freeknee=0.45)
BLAST_KICK = P(body=(-0.12, -0.2, 0), head=(-0.15, 0.15, 0), ring=(-1.85, 0.1, 0.05), free=(-1.7, -0.45, -0.1),
               ringleg=(0.5, 0, 0.25), ringknee=0.6, freeleg=(-0.4, 0, -0.25), freeknee=0.4)
SHIELD = P(body=(0.3, -0.15, 0), head=(0.25, 0.1, 0), ring=(-1.55, 0.6, 0.6), free=(-0.7, -0.3, -0.2),
           ringleg=(-0.55, 0, 0.18), ringknee=1.0, freeleg=(0.45, 0, -0.15), freeknee=0.6)
SHIELD_HIT = P(body=(0.05, -0.15, 0), head=(0.0, 0.1, 0), ring=(-1.45, 0.6, 0.6), free=(-0.5, -0.3, -0.25),
               ringleg=(-0.4, 0, 0.18), ringknee=0.75, freeleg=(0.55, 0, -0.15), freeknee=0.5)
BEAM = P(body=(-0.05, -0.25, 0), head=(0.0, 0.2, 0), ring=(-1.57, 0.2, 0.0), free=(-1.2, -0.6, -0.3),
         ringleg=(0.55, 0, 0.2), ringknee=0.5, freeleg=(-0.4, 0, -0.2), freeknee=0.35)
LOW = P(body=(0.45, 0, 0), head=(0.1, 0, 0), ring=(0.35, 0, 0.35), free=(0.35, 0, -0.35),
        ringleg=(-0.6, 0, 0.2), ringknee=1.2, freeleg=(-0.6, 0, -0.2), freeknee=1.2)
SWEEP = P(body=(-0.1, 0, 0), head=(-0.2, 0, 0), ring=(-2.6, 0, 0.45), free=(-2.6, 0, -0.45),
          ringleg=(0.05, 0, 0.12), ringknee=0.1, freeleg=(0.05, 0, -0.12), freeknee=0.1)
CROUCH = P(body=(0.5, 0, 0), head=(-0.3, 0, 0), ring=(-2.7, 0, 0.1), free=(0.7, 0, -0.3),
           ringleg=(-0.8, 0, 0.1), ringknee=1.5, freeleg=(-0.6, 0, -0.1), freeknee=1.3)
SLAM = P(body=(0.9, 0, 0), head=(-0.6, 0, 0), ring=(-0.2, 0, 0.1), free=(0.9, 0, -0.5),
         ringleg=(0.2, 0, 0.06), ringknee=1.35, freeleg=(-1.2, 0, -0.08), freeknee=1.3)
STANDP = P(body=(0.0, 0, 0), head=(0.0, 0, 0), ring=(0.05, 0, 0.05), free=(0.05, 0, -0.05))

LOOP = 60
TAKES = {
    "P1": ("ring punch", [(GUARD, 0), (GUARD, 8), (JAB, 11), (JAB, 14), (GUARD, 22), (GUARD, 34), (JAB, 37), (JAB, 40), (GUARD, 48), (GUARD, 60)]),
    "P2": ("blast", [(STANDP, 0), (BLAST_SET, 8), (BLAST_SET, 34), (BLAST_KICK, 36), (BLAST_KICK, 40), (BLAST_SET, 50), (STANDP, 60)]),
    "P3": ("shield block", [(SHIELD, 0), (SHIELD, 24), (SHIELD_HIT, 27), (SHIELD, 36), (SHIELD, 60)]),
    "P4": ("beam hold", [(STANDP, 0), (BEAM, 8), (BEAM, 52), (STANDP, 60)]),
    "P5": ("summon wall", [(STANDP, 0), (LOW, 10), (LOW, 16), (SWEEP, 28), (SWEEP, 44), (STANDP, 60)]),
    "P6": ("ground slam", [(STANDP, 0), (CROUCH, 10), (CROUCH, 14), (SLAM, 20), (SLAM, 40), (STANDP, 60)]),
}


def keyed(keys, t):
    for (pa, ta), (pb, tb) in zip(keys, keys[1:]):
        if ta <= t <= tb:
            return mixp(pa, pb, 0 if tb == ta else smooth((t - ta) / (tb - ta)))
    return keys[-1][0]


def keyo(o, f, loc=None, scale=None, rot=None):
    if loc is not None:
        o.location = tuple(loc); o.keyframe_insert("location", frame=f)
    if scale is not None:
        o.scale = tuple(scale); o.keyframe_insert("scale", frame=f)
    if rot is not None:
        o.rotation_euler = tuple(rot); o.keyframe_insert("rotation_euler", frame=f)


JADE_T, _ = emis("CP hard light", (0.2, 1.0, 0.4), 3.0, alpha=0.45)
BOLT, _ = emis("CP bolt", (0.4, 1.0, 0.55), 12.0)
for k, (take, (nm, keys)) in enumerate(TAKES.items()):
    origin = np.array([k * 4.0, 0.0, 0.0])
    objs = make_player(take)
    rm, _ = emis(f"CP ring {take}", (0.1, 1.0, 0.25), 2.0); objs["ring"].data.materials[0] = rm
    fx = None
    if take == "P2":
        fx = cube(f"CP {take} bolt", BOLT, 0.25)
    elif take in ("P3", "P5"):
        fx = cube(f"CP {take} hard light", JADE_T, 1.0)
    elif take == "P4":
        fx = cube(f"CP {take} beam", BOLT, 1.0)
    elif take == "P6":
        bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.05, major_segments=48, minor_segments=6)
        fx = bpy.context.active_object
        for cc in list(fx.users_collection):
            cc.objects.unlink(fx)
        link(fx); fx.name = f"CP {take} shockwave"; fx.data.materials.append(JADE_T)
    for t in range(LOOP + 1):
        sol = solve(keyed(keys, t))
        set_pose(objs, sol, origin, t + 1)
        hand = to_bl(hand_point(sol)) + origin
        e = 2.0
        if take == "P1":
            e = 25.0 if t in (11, 12, 37, 38) else 3.0
        elif take == "P2":
            e = 2.0 + 14.0 * min(1, max(0, (t - 8) / 26)) if t < 35 else (40.0 if t < 37 else 3.0)
            if 35 <= t < 50:
                keyo(fx, t + 1, loc=hand + np.array([0, -(t - 35) * 0.9, 0]), scale=(1, 1, 1))
            else:
                keyo(fx, t + 1, loc=hand, scale=(0, 0, 0))
        elif take == "P3":
            e = 6.0 if t not in (25, 26) else 30.0
            sh = to_bl(np.array([0.0, 4.0, -9.0])) + origin
            keyo(fx, t + 1, loc=sh + np.array([0, 0.05 if 25 <= t < 30 else 0, 0]), scale=(1.4, 0.06, 1.6))
        elif take == "P4":
            on = 8 <= t <= 52
            e = 10.0 + 2.0 * math.sin(t * 1.7) if on else 2.0
            ln = 6.0 if on else 0.0
            keyo(fx, t + 1, loc=hand + np.array([0, -ln / 2, 0]), scale=(0.12 * on, ln, 0.12 * on))
        elif take == "P5":
            w = smooth(min(1, max(0, (t - 16) / 12))) * (1.0 if t < 50 else max(0, 1 - (t - 50) / 8))
            e = 3.0 + 10.0 * w
            keyo(fx, t + 1, loc=origin + np.array([0, -2.2, 1.0 * w]), scale=(2.8, 0.15, 2.0 * w + 0.001))
        elif take == "P6":
            e = 30.0 if 20 <= t < 23 else 3.0
            r = 0.0 if t < 20 else 0.3 + (t - 20) * 0.35
            keyo(fx, t + 1, loc=origin + np.array([0, -0.6, 0.05]), scale=(r, r, r * 0.6 if t < 44 else 0.0))
        s_ = rm.node_tree.nodes["Emission"].inputs["Strength"]; s_.default_value = e; s_.keyframe_insert("default_value", frame=t + 1)
    cu = bpy.data.curves.new("CP label " + take, "FONT"); cu.body = f"{take}  {nm}"; cu.size = 0.3; cu.align_x = "CENTER"
    tl = link(bpy.data.objects.new("CP label " + take, cu)); tl.location = tuple(origin + np.array([0, 1.4, 0.01]))
    tl.data.materials.append(mat("CP label", (0.8, 1.0, 0.85), emit=2.0))
    cam(f"Cam {take}", tuple(origin + np.array([-1.1, 2.8, 2.4])), tuple(origin + np.array([0.1, -2.2, 0.9])), 30)
    cam(f"Cam {take} front", tuple(origin + np.array([1.8, -4.0, 1.4])), tuple(origin + np.array([0, -0.4, 0.9])), 35)
    print(take, "built", flush=True)

scene.frame_start, scene.frame_end = 1, LOOP
bpy.ops.mesh.primitive_plane_add(size=50, location=(10, -2, 0))
g = bpy.context.active_object
for c in g.users_collection:
    c.objects.unlink(g)
link(g); g.name = "CP ground"; g.data.materials.append(mat("CP ground", (0.18, 0.3, 0.12)))
world = bpy.data.worlds.new("CP world"); world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.25, 0.32, 0.45, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.6
scene.world = world
sun = link(bpy.data.objects.new("CP sun", bpy.data.lights.new("CP sun", "SUN")))
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
cam("Cam all", (10, -14, 5), (10, 0, 1.0), 30)
scene.camera = bpy.data.objects["Cam P1 front"]
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
