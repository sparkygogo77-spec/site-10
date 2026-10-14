# Pass 401: directional take-off (Blender designer chat, 2026-10-14). J: "the flight take off is problematic not being
# able to control it ... I need the animations to look natural while leaving me feel control in the direction i want
# to go, generate animations for every direction faced and direction moved as animations for the way someone flies off".
# Picks: 16 directions (every 22.5 degrees of movement relative to the look), both body styles, bank into turns.
# Base: F2 rocket (pass 216, handed off): run, plant and crouch with the ring fist rising, shoot straight up, pitch
# over into flight about 12 blocks up, launching the way you MOVE.
#   A  hips lead, head looks: the body turns toward travel and the head keeps your look (yaw at most 75 degrees, pitch
#      within the 57 degree neck rule). Moving backwards (more than 90 degrees off the look) you backpedal on the
#      ground and fly back-first, leaning back, ring arm pointing the way you go, still facing your look.
#   B  whole body turns: the body runs and flies along the travel direction; the head goes with it.
# Every take steers once it is level: a 40 degree turn to the right with a bank into the turn (up to 35 degrees of
# roll, ring arm leading the new heading), then rolls level. The over-the-shoulder camera keeps the LOOK direction
# (-y) the whole time, the way the player's own camera would, so you see each take-off relative to your view.
# Cameras "Cam A000".."Cam A338" and "Cam B000".."Cam B338" (degrees clockwise from the look: 090 = right, 180 = back,
# 270 = left), "Cam A045 side"-style side cameras, "Cam A rose", "Cam B rose" (from above), "Cam all".
# Writes LanternLive\takeoff_dirs_poses.json and builds LanternLive\takeoff_dirs.blend.
import json, math, os
import bpy
import numpy as np
from mathutils import Matrix

R = math.radians
OUT = os.path.join(FOLDER, "takeoff_dirs.blend")
if bpy.data.filepath:
    try:
        bpy.ops.wm.save_mainfile()
    except Exception as e:
        print("save current:", e)
old = bpy.data.scenes.get("Takeoff Dirs")
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new("Takeoff Dirs")
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



# ================================================================== pass 401
T_RUN, T_CROUCH, T_UP, T_PITCH = 16, 5, 18, 12
T_LEV = T_RUN + T_CROUCH + T_UP + T_PITCH          # 51: level flight
T_TURN0, T_TURN1 = 58, 78                          # the steer
T_END = 100
TURN = R(40.0)
BANK = R(35.0)
RUN_V, FLY_V = 0.28, 0.55
HEAD_YAW = R(75.0)
DIRS = [i * 22.5 for i in range(16)]
MODES = ("A", "B")
SPACING = 44.0
ROSE = {"A": (0.0, 0.0), "B": (150.0, 0.0)}

FLY = dict(body=(1.42, 0, 0), head=(-1.25, 0, 0), ring=(-2.95, 0, 0.02), free=(0.35, 0, -0.12),
           ringleg=(1.38, 0, 0.03), ringknee=0.25, freeleg=(1.3, 0, -0.03), freeknee=0.4, grounded=False)
CROUCH = dict(body=(0.45, 0, 0), head=(-0.3, 0, 0), ring=(-3.05, 0, 0.1), free=(0.7, 0, -0.15),
              ringleg=(-0.75, 0, 0.05), ringknee=1.4, freeleg=(-0.55, 0, -0.05), freeknee=1.2)
ROCKET_UP = dict(body=(0.0, 0, 0), head=(-0.3, 0, 0), ring=(-3.05, 0, 0.0), free=(0.15, 0, -0.1),
                 ringleg=(0.1, 0, 0.03), ringknee=0.15, freeleg=(0.25, 0, -0.03), freeknee=0.35, grounded=False)
# flying back-first (A, rear half): leaning well back, ring arm reaching behind and down the way you go, legs ahead
BACKFLY = dict(body=(-0.55, 0, 0), head=(0.2, 0, 0), ring=(2.1, 0, 0.25), free=(0.4, 0, -0.5),
               ringleg=(-0.55, 0, 0.05), ringknee=0.55, freeleg=(-0.35, 0, -0.05), freeknee=0.8, grounded=False)


def legs(ph, amp=0.85, lean=0.0):
    thigh = 0.15 - amp * math.sin(ph) - lean * 0.5
    knee = 0.12 + 1.45 * ((1 + math.cos(ph + 0.35)) / 2) ** 2
    return thigh, knee


def wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def run_pose(t, legyaw=0.0, back=False):
    """S1 run (ring forward). legyaw turns the stride plane relative to the body (strafing); back runs it in reverse."""
    ph = 2 * math.pi * t / 12 * (-1 if back else 1)
    lean = -0.08 if back else 0.26
    tr, kr = legs(ph, 0.75 if back else 0.85, lean)
    tf, kf = legs(ph + math.pi, 0.75 if back else 0.85, lean)
    swing = math.sin(ph)
    return dict(body=(lean + 0.03 * math.sin(2 * ph), 0.07 * swing, 0.0), head=(-lean * 0.8, 0, 0.0),
                ringleg=(tr, -legyaw, 0.02), ringknee=kr, freeleg=(tf, legyaw, -0.02), freeknee=kf,
                ring=(-1.42 + 0.06 * math.sin(2 * ph), 0.06, 0.05), free=(0.15 - 0.95 * swing, 0, -0.08))


def body_yaw(mode, phi, rear):
    """Blender z-rotation of the body for travel phi (look = 0)."""
    if mode == "B":
        return phi
    if rear:
        return wrap(phi + math.pi) * 0.35                  # backpedal: mostly facing the look
    return max(-R(70), min(R(70), phi))


def simulate(mode, theta):
    """theta: degrees clockwise from the look. Returns per tick: pose, position, body yaw, travel yaw, roll, glow."""
    phi0 = -R(theta)                                       # Blender z-rotation of the travel direction
    rear = mode == "A" and math.cos(phi0) < -1e-6          # more than 90 degrees off the look
    pos = np.zeros(3); out = []
    phi = phi0
    for t in range(T_END + 1):
        roll = 0.0; heady = None
        # steering: the heading turns right 40 degrees, smoothly, once level
        if T_TURN0 <= t <= T_TURN1:
            w = (t - T_TURN0) / (T_TURN1 - T_TURN0)
            phi = phi0 - TURN * smooth(w)
            rate = 6 * w * (1 - w)                         # derivative of smoothstep, peaks at 1.5
            roll = -BANK * min(1.0, rate / 1.5)
        elif t > T_TURN1:
            phi = phi0 - TURN
        b_ground = body_yaw(mode, phi0, rear)
        if t < T_RUN:
            lrel = wrap(phi0 - b_ground + (math.pi if rear else 0.0))
            p = run_pose(t, legyaw=lrel, back=rear)
            speed, vz = RUN_V, 0.0; byaw = b_ground; glow = 2 + 6 * t / T_RUN
        elif t < T_RUN + T_CROUCH:
            w = smooth((t - T_RUN) / T_CROUCH)
            lrel = wrap(phi0 - b_ground + (math.pi if rear else 0.0))
            p = mixp(run_pose(t, lrel, rear), CROUCH, w)
            speed, vz = RUN_V * (1 - w) + 0.12 * w, 0.0; byaw = b_ground; glow = 8 + 8 * w
        elif t < T_RUN + T_CROUCH + T_UP:
            tt = t - (T_RUN + T_CROUCH)
            p = mixp(CROUCH, ROCKET_UP, smooth(min(1, tt / 4)))
            speed = 0.06; vz = None; glow = 18 if tt < 3 else 13
            # rising straight up, the body turns to where it will fly (A rear keeps facing the look)
            target = phi0 if (mode == "B" or not rear) else wrap(phi0 + math.pi)
            byaw = b_ground + wrap(target - b_ground) * smooth(min(1, tt / 12))
        else:
            ft = t - (T_RUN + T_CROUCH + T_UP)
            w = smooth(min(1, ft / T_PITCH))
            fly = BACKFLY if rear else FLY
            p = mixp(ROCKET_UP, fly, w)
            speed = 0.02 + (FLY_V - 0.02) * w; vz = None; glow = 10
            byaw = wrap(phi + math.pi) if rear else phi
            if roll:
                p = dict(p); glow = 12
                # the ring arm leads the new heading: reaches out toward the inside of the turn
                k = abs(roll) / BANK
                r0 = p["ring"]; p["ring"] = (r0[0], r0[1], r0[2] + 0.35 * k)
        p["grounded"] = t < T_RUN + T_CROUCH
        # head: A keeps the look (yaw at most 75 degrees off the body); B looks along the body
        if mode == "A":
            hy = max(-HEAD_YAW, min(HEAD_YAW, wrap(byaw)))
            h = p.get("head", (0, 0, 0)); p["head"] = (h[0], hy, h[2])
        # position: horizontal along travel, height from F2 (straight up to 10, level at 12)
        if t >= 1:
            pos = pos + speed * np.array([-math.sin(phi), -math.cos(phi), 0.0]) * (1 if t >= T_RUN + T_CROUCH else 1)
        tt = t - (T_RUN + T_CROUCH)
        if tt < 0:
            z = 0.0
        elif tt < T_UP:
            z = min(10.0, 0.02 * tt * tt + 0.25 * tt)
        else:
            hz = min(10.0, 0.02 * T_UP * T_UP + 0.25 * T_UP)
            z = hz + (12.0 - hz) * smooth(min(1, (tt - T_UP) / T_PITCH))
        pos[2] = z
        out.append((p, pos.copy(), byaw, phi, roll, glow, rear))
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


# --------------------------------------------------------------- scene
try:
    tree = bpy.data.node_groups.new("TD Glow", "CompositorNodeTree")
    tree.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    rl = tree.nodes.new("CompositorNodeRLayers"); go = tree.nodes.new("NodeGroupOutput")
    gl = tree.nodes.new("CompositorNodeGlare")
    if "Type" in gl.inputs:
        gl.inputs["Type"].default_value = "Bloom"
    for nm, val in (("Size", 0.6), ("Strength", 0.5), ("Threshold", 1.0)):
        if nm in gl.inputs:
            gl.inputs[nm].default_value = val
    tree.links.new(rl.outputs["Image"], gl.inputs["Image"]); tree.links.new(gl.outputs["Image"], go.inputs[0])
    scene.compositing_node_group = tree
except Exception as e:
    print("no glow:", e)

LOOKM = mat("TD look arrow", (0.9, 0.95, 1.0), emit=1.5)
TRAVM = mat("TD travel arrow", (0.15, 1.0, 0.35), emit=2.5)
PADM = mat("TD pad", (0.32, 0.32, 0.34), rough=0.9)
LABEL = mat("TD label", (0.85, 1.0, 0.9), emit=2.0)
TRAIL = mat("TD trail", (0.1, 1.0, 0.3), emit=4.0)


def arrow(name, origin, ang, length, m, width=0.25):
    """A flat arrow on the ground pointing at Blender z-rotation `ang` (0 = -y)."""
    d = np.array([-math.sin(ang), -math.cos(ang), 0.0]); s = np.array([-d[1], d[0], 0.0])
    o = np.asarray(origin, float) + np.array([0, 0, 0.02])
    tip = o + d * length; base = o + d * (length - 0.7)
    vs = [o + s * width / 2, o - s * width / 2, base - s * width / 2, base + s * width / 2,
          base + s * 0.45, tip, base - s * 0.45]
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(v) for v in vs], [], [(0, 1, 2, 3), (4, 3, 2, 6, 5)][:1] + [(4, 6, 5)])
    me.update(); me.materials.append(m)
    return link(bpy.data.objects.new(name, me))


dump = {"format": "per mode (A hips lead / head looks, B whole body turns), per direction (degrees clockwise from the "
                  "look; 90 = right, 180 = back): per tick part rot (xRot,yRot,zRot rad, model space before the body "
                  "yaw), offset_px from the vanilla pivot, body_yaw_deg (clockwise from the look), travel_deg, roll_deg "
                  "(bank, + = right side down), pos (right, forward, up blocks from the start), glow. 20 ticks a second.",
        "timing": {"run": [0, T_RUN], "crouch": [T_RUN, T_RUN + T_CROUCH],
                   "rise": [T_RUN + T_CROUCH, T_RUN + T_CROUCH + T_UP], "pitch_over": [T_RUN + T_CROUCH + T_UP, T_LEV],
                   "turn": [T_TURN0, T_TURN1]},
        "head_yaw_limit_deg": 75, "neck_pitch_limit_deg": 57, "bank_deg": 35, "turn_deg": 40,
        "rule_A": "body yaw = travel clamped to +-70 on the ground; > 90 off the look: backpedal (yaw 0.35 x the back "
                  "angle) and fly back-first (BACKFLY) facing the look; head yaw = -(body yaw) clamped to +-75",
        "rule_B": "body yaw = travel; head straight", "modes": {}}

for mi, mode in enumerate(MODES):
    dump["modes"][mode] = {}
    for di, theta in enumerate(DIRS):
        tag = f"{mode}{int(round(theta)) % 360:03d}"
        # a rose: each direction starts 14 blocks out from its mode's centre, along its own travel direction
        a0 = -R(theta)
        ox = ROSE[mode][0] - 14.0 * math.sin(a0)
        oy = ROSE[mode][1] - 14.0 * math.cos(a0)
        base = np.array([ox, oy, 0.0])
        objs = make_player(tag)
        rm = mat(f"TD ring {tag}", (0.1, 1.0, 0.25), emit=2.0); objs["ring"].data.materials[0] = rm
        mover = link(bpy.data.objects.new(f"TD {tag} mover", None)); mover.empty_display_size = 0.1
        sim = simulate(mode, theta)
        ticks = []
        trail_pts = []
        for t, (p, pos, byaw, phi, roll, glow, rear) in enumerate(sim):
            sol = solve(p)
            origin = base + pos
            set_pose_w(objs, sol, origin, t + 1, byaw, phi, roll)
            mover.location = tuple(base + pos * np.array([1, 1, 0.85])); mover.keyframe_insert("location", frame=t + 1)
            s = rm.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
            s.default_value = glow; s.keyframe_insert("default_value", frame=t + 1)
            if t % 2 == 0:
                trail_pts.append((origin[0], origin[1], 0.04))
            ticks.append({"pos": [round(float(-pos[0]), 3), round(float(-pos[1]), 3), round(float(pos[2]), 3)],
                          "body_yaw_deg": round(-math.degrees(byaw), 1), "travel_deg": round(-math.degrees(phi), 1),
                          "roll_deg": round(-math.degrees(roll), 1), "glow": round(float(glow), 1),
                          "parts": {kk: {"rot": [round(float(q), 3) for q in sol[kk][0]],
                                         "offset_px": [round(float(q), 2) for q in sol[kk][1] - np.array(PIVOT[kk], float)]}
                                    for kk in PARTS}})
        dump["modes"][mode][f"{int(round(theta)) % 360:03d}"] = {"rear": bool(sim[0][6]), "ticks": ticks}
        # the flight path as a thin green line (ring trail), the look arrow (white) and travel arrow (green)
        cu = bpy.data.curves.new(f"TD {tag} path", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 0.06
        sp = cu.splines.new("POLY"); sp.points.add(len(trail_pts) - 1)
        for i, q in enumerate(trail_pts):
            sp.points[i].co = (*q, 1)
        po = link(bpy.data.objects.new(f"TD {tag} path", cu)); po.data.materials.append(TRAIL)
        arrow(f"TD {tag} look", base + np.array([0, 1.2, 0]), 0.0, 3.0, LOOKM)
        arrow(f"TD {tag} travel", base, -R(theta), 4.0, TRAVM, 0.3)
        lb = bpy.data.curves.new(f"TD label {tag}", "FONT")
        lb.body = f"{tag}  {'hips lead, head looks' if mode == 'A' else 'whole body turns'}  moving {int(round(theta))}° from look"
        lb.size = 0.55; lb.align_x = "CENTER"
        tl = link(bpy.data.objects.new(f"TD label {tag}", lb)); tl.location = (ox, oy + 2.0, 0.02); tl.rotation_euler = (0, 0, 0)
        tl.data.materials.append(LABEL)
        # over the right shoulder, LOOKING the player's way (-y), following him
        y_s, z_s = oy + sim[0][1][1], sim[0][1][2]
        c = cam(f"Cam {tag}", (ox - 1.0, oy + 6.5, 3.6), (ox + 0.1, oy - 6.0, 1.6), 26)
        c.parent = mover; c.matrix_parent_inverse = Matrix.Translation((ox, oy, 0.0)).inverted()
        cam(f"Cam {tag} side", (ox + 18, oy - 4, 8), (ox, oy - 4, 5), 30)
    print(mode, "built", flush=True)

for mode, (cx, cy) in ROSE.items():
    cam(f"Cam {mode} rose", (cx, cy + 0.5, 125), (cx, cy, 0), 30)

with open(os.path.join(FOLDER, "takeoff_dirs_poses.json"), "w") as fh:
    json.dump(dump, fh, separators=(",", ":"))

scene.frame_start, scene.frame_end = 1, T_END
bpy.ops.mesh.primitive_plane_add(size=1, location=(75, 0, 0))
g = bpy.context.active_object
for c in g.users_collection:
    c.objects.unlink(g)
link(g); g.name = "TD ground"; g.scale = (900, 500, 1)
gm = bpy.data.materials.new("TD ground"); gm.use_nodes = True
N, Lk = gm.node_tree.nodes, gm.node_tree.links
ck = N.new("ShaderNodeTexChecker"); ck.inputs["Scale"].default_value = 900
ck.inputs["Color1"].default_value = (0.2, 0.36, 0.13, 1); ck.inputs["Color2"].default_value = (0.24, 0.42, 0.16, 1)
Lk.new(ck.outputs["Color"], N.get("Principled BSDF").inputs["Base Color"])
g.data.materials.append(gm)
world = bpy.data.worlds.new("TD world"); world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.35, 0.45, 0.6, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.8
scene.world = world
sun = link(bpy.data.objects.new("TD sun", bpy.data.lights.new("TD sun", "SUN")))
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
cam("Cam all", (75, 150, 110), (75, 0, 0), 32)
scene.camera = bpy.data.objects["Cam A090"]
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
