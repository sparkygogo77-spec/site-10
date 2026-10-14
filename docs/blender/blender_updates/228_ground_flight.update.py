# Pass 228: ground flight with the running barrier (lead Blender chat, 2026-10-14). J: F2, but it launches the way you
# are moving, not the way you face. Running and double-tapping space starts a low forward flight; the ring keeps you
# riding on top of any 1-block step you run into. A 2-3 block wall is a barrier collision: an invisible dome around you
# (radius 3.5, a little smaller than the 4.5 flying dome) takes the hit. It shows only where it hits: the construct
# texture craters flat against the wall in a dome-shaped dent, particles burst out of the rim, the flattened patch is
# left behind on the wall as a construct imprint (fades over 5 s), and the dome re-forms straight away. J: "my flying
# should be brought to a halt in the same block where my barrier made the impact, as a quick animation."
#   H1 hard stop: 3 ticks, shallow crater, you stop just where the dome touched.
#   H2 cushion: 6 ticks, the dome squashes about 1.4 blocks and springs back.
#   H3 into the block: 8 ticks, the dome flattens right down and you halt in the impact block, one block off the wall.
# Every take: S1 sprint (ring forward), double tap, lift to a 1-block skim, ride up and over a 1-high step, hit a
# 3-high wall. Cameras "Cam H1".."Cam H3" (over the right shoulder, following), "Cam H1 side".., "Cam H1 wall"..,
# "Cam all". Writes LanternLive\ground_flight_poses.json, builds LanternLive\ground_flight.blend.
import json, math, os
import bpy
import numpy as np
from mathutils import Matrix

R = math.radians
OUT = os.path.join(FOLDER, "ground_flight.blend")
if bpy.data.filepath:
    try:
        bpy.ops.wm.save_mainfile()
    except Exception as e:
        print("save current:", e)
old = bpy.data.scenes.get("Ground Flight")
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new("Ground Flight")
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



FLY = dict(body=(1.42, 0, 0), head=(-1.25, 0, 0), ring=(-1.57, 0, 0.02), free=(1.35, 0, -0.12),
           ringleg=(1.38, 0, 0.03), ringknee=0.25, freeleg=(1.3, 0, -0.03), freeknee=0.4, grounded=False)
CROUCH = dict(body=(0.55, 0, 0), head=(-0.35, 0, 0), ring=(0.9, 0, 0.2), free=(0.7, 0, -0.15),
              ringleg=(-0.75, 0, 0.05), ringknee=1.4, freeleg=(-0.55, 0, -0.05), freeknee=1.2)
SPRING = dict(body=(0.6, 0, 0), head=(-0.5, 0, 0), ring=(-2.2, 0, 0.05), free=(1.0, 0, -0.15),
              ringleg=(0.5, 0, 0.04), ringknee=0.3, freeleg=(0.9, 0, -0.04), freeknee=0.9, grounded=False)
ROCKET_UP = dict(body=(0.0, 0, 0), head=(-0.3, 0, 0), ring=(-3.05, 0, 0.0), free=(0.15, 0, -0.1),
                 ringleg=(0.1, 0, 0.03), ringknee=0.15, freeleg=(0.25, 0, -0.03), freeknee=0.35, grounded=False)

# ------------------------------------------------------------------ course (blocks; forward is -y)
T_RUN, T_TAP, T_END = 16, 22, 170
RUN_V, FLY_V = 0.28, 0.55
STEP = (-11.0, -15.0, 1.0)            # a 1-high platform from y=-11 to y=-15
WALL_FACE, WALL_H, WALL_T, WALL_W = -26.0, 3.0, 1.0, 11.0
DOME_R, SKIM = 3.5, 0.5               # dome radius (flying dome is 4.5); origin rides 0.5 above the surface (~1 block clear)
HIT = WALL_FACE + DOME_R              # where the player's centre is when the dome front touches the wall
STOP = {"H1": (3, 0.5), "H2": (6, 1.4), "H3": (8, DOME_R - 1.0)}   # (ticks to stop, crater depth in blocks)
NAMES = {"H1": "hard stop", "H2": "cushion", "H3": "into the block"}
TAKES = ["H1", "H2", "H3"]
LANES = {k: i * 16.0 for i, k in enumerate(TAKES)}


def surface(y):
    return STEP[2] if STEP[1] <= y <= STEP[0] else 0.0


BRACE = dict(body=(0.55, 0, 0), head=(0.0, 0, 0), ring=(-1.62, 0, 0.0), free=(-0.9, 0, -0.35),
             ringleg=(0.25, 0, 0.05), ringknee=0.7, freeleg=(-0.15, 0, -0.05), freeknee=0.9, grounded=False)
HOVER = dict(body=(0.12, 0, 0), head=(-0.05, 0, 0), ring=(-1.5, 0, 0.02), free=(0.1, 0, -0.12),
             ringleg=(0.1, 0, 0.04), ringknee=0.25, freeleg=(0.2, 0, -0.04), freeknee=0.45, grounded=False)


def simulate(take):
    """Per tick: (pose, y, z, glow, dome) where dome = (visible alpha, squash depth)."""
    n_stop, depth = STOP[take]
    out = []
    y, z, vz = 0.0, 0.0, 0.0
    v = 0.0
    t_hit = None
    for t in range(T_END + 1):
        if t < T_RUN:
            p = run_pose("S1", t); y = -RUN_V * t; z = 0.0; glow = 6.0
        elif t < T_TAP:                                            # double tap: a quick lift in the run direction
            w = smooth((t - T_RUN) / (T_TAP - T_RUN))
            p = mixp(run_pose("S1", t), FLY, w); p["grounded"] = w < 0.35
            v = RUN_V + (FLY_V - RUN_V) * w; y -= v
            z = SKIM * w; glow = 6 + 10 * (1 - abs(2 * w - 1))
        elif t_hit is None:
            v = FLY_V; y -= v
            ahead = max(surface(y - d) for d in np.linspace(-0.3, 1.6, 12))   # the ring looks ahead and lifts you on top
            target = ahead + SKIM
            vz += (target - z) * 0.35 - vz * 0.75; z += vz
            p = dict(FLY); glow = 7.0
            if y <= HIT:
                y = HIT; t_hit = t
        if t_hit is not None and t >= t_hit:
            k = t - t_hit
            if k <= n_stop:                                         # decelerate into the dome
                w = k / n_stop
                y = HIT - depth * (1 - (1 - w) ** 2)
                p = mixp(FLY, BRACE, smooth(min(1, k / max(2, n_stop * 0.6))))
                glow = 16.0
            else:                                                   # hold, settle into a hover where you stopped
                w = smooth(min(1, (k - n_stop) / 10))
                y = HIT - depth
                p = mixp(BRACE, HOVER, w); glow = 16 - 8 * w
            z += (SKIM - z) * 0.3
        sq = 0.0; alpha = 0.0
        if t_hit is not None and t >= t_hit:
            k = t - t_hit
            sq = (HIT - y)                                          # how far past first touch you are
            if k > n_stop:
                sq = depth * max(0.0, 1 - (k - n_stop) / 4)         # the dome springs back to round
                sq = depth * (1 - smooth(min(1, (k - n_stop) / 4)))
            alpha = 0.95 * (min(1, k / 1.5)) * (1 - smooth(min(1, max(0, k - n_stop - 2) / 10)))
        out.append((p, y, z, glow, (alpha, sq), t_hit))
    return out


# ------------------------------------------------------------------ materials and scenery
TEX = os.path.join(FOLDER, "dome_x3d1_f0.png")
def dome_mat(name, tint=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N, Lk = m.node_tree.nodes, m.node_tree.links
    p = N.get("Principled BSDF")
    try:
        img = bpy.data.images.load(TEX, check_existing=True)
        tx = N.new("ShaderNodeTexImage"); tx.image = img; tx.interpolation = "Closest"
        Lk.new(tx.outputs["Color"], p.inputs["Base Color"]); Lk.new(tx.outputs["Color"], p.inputs["Emission Color"])
    except Exception as e:
        print("dome tex:", e)
        p.inputs["Emission Color"].default_value = (0.2, 1.0, 0.35, 1)
    p.inputs["Emission Strength"].default_value = 3.0 * tint
    p.inputs["Alpha"].default_value = 0.0
    # alpha = keyed strength x the texture's own alpha (the dark gaps stay see-through); the dome is also masked so it
    # only shows where it meets the wall (1 within 0.4 of the face, gone by 1.6)
    val = N.new("ShaderNodeValue"); val.name = "Strength"; val.outputs[0].default_value = 0.0
    a_src = val.outputs[0]
    if "tx" in locals():
        m1 = N.new("ShaderNodeMath"); m1.operation = "MULTIPLY"
        Lk.new(tx.outputs["Alpha"], m1.inputs[0]); Lk.new(a_src, m1.inputs[1]); a_src = m1.outputs[0]
    if tint == 1.0:
        geo = N.new("ShaderNodeNewGeometry"); sep = N.new("ShaderNodeSeparateXYZ")
        mr = N.new("ShaderNodeMapRange"); mr.inputs[1].default_value = WALL_FACE + 0.4; mr.inputs[2].default_value = WALL_FACE + 1.6
        mr.inputs[3].default_value = 1.0; mr.inputs[4].default_value = 0.0
        mul = N.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
        Lk.new(geo.outputs["Position"], sep.inputs[0]); Lk.new(sep.outputs["Y"], mr.inputs[0])
        Lk.new(mr.outputs[0], mul.inputs[0]); Lk.new(a_src, mul.inputs[1]); a_src = mul.outputs[0]
    Lk.new(a_src, p.inputs["Alpha"])
    try:
        m.surface_render_method = "BLENDED"
    except Exception:
        pass
    return m


STONE = mat("GF stone", (0.42, 0.42, 0.44), rough=0.9)
STONE2 = mat("GF stone dark", (0.33, 0.33, 0.35), rough=0.9)
SPARK = mat("GF spark", (0.25, 1.0, 0.4), emit=9.0)


def block_row(tag, x0, y0, y1, h, z0=0.0, width=1, alt=True):
    """Unit cubes so it reads as Minecraft blocks."""
    me = bpy.data.meshes.new(tag)
    verts, faces = [], []
    for ix in range(width):
        for iy in range(int(round(abs(y1 - y0)))):
            for iz in range(int(h)):
                x = x0 - width / 2 + ix; y = max(y0, y1) - iy - 1; z = z0 + iz
                b = len(verts)
                verts += [(x + dx, y + dy, z + dz) for dx in (0, 1) for dy in (0, 1) for dz in (0, 1)]
                faces += [(b, b + 1, b + 3, b + 2), (b + 4, b + 6, b + 7, b + 5), (b, b + 4, b + 5, b + 1),
                          (b + 2, b + 3, b + 7, b + 6), (b, b + 2, b + 6, b + 4), (b + 1, b + 5, b + 7, b + 3)]
    me.from_pydata(verts, [], faces); me.update()
    me.materials.append(STONE); me.materials.append(STONE2)
    for i, poly in enumerate(me.polygons):
        poly.material_index = ((i // 6) % 2) if alt else 0
    return link(bpy.data.objects.new(tag, me))


dump = {"format": "per take: per tick part rot (xRot,yRot,zRot rad), offset_px from the vanilla pivot, forward and up "
                  "in blocks, ring glow, dome alpha and squash (blocks); dome radius 3.5", "dome_radius": DOME_R,
        "skim_blocks": SKIM, "takes": {}}
for take in TAKES:
    ox = LANES[take]
    block_row(f"GF {take} step", ox, STEP[0], STEP[1], 1, width=5)
    block_row(f"GF {take} wall", ox, WALL_FACE - WALL_T, WALL_FACE, WALL_H, width=int(WALL_W))
    objs = make_player(take)
    rm = mat(f"GF ring {take}", (0.1, 1.0, 0.25), emit=2.0); objs["ring"].data.materials[0] = rm
    mover = link(bpy.data.objects.new(f"GF {take} mover", None)); mover.empty_display_size = 0.1
    # the running dome: a sphere around the chest, invisible until it hits
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=DOME_R)
    dome = bpy.context.active_object
    for c in dome.users_collection:
        c.objects.unlink(dome)
    link(dome); dome.name = f"GF {take} dome"
    dm = dome_mat(f"GF {take} dome"); dome.data.materials.append(dm)
    da = dm.node_tree.nodes["Strength"].outputs[0]
    # the imprint left on the wall (a flat disc on the face) and its glowing rim
    bpy.ops.mesh.primitive_circle_add(vertices=48, radius=1.0, fill_type="NGON")
    imp = bpy.context.active_object
    for c in imp.users_collection:
        c.objects.unlink(imp)
    link(imp); imp.name = f"GF {take} imprint"; imp.rotation_euler = (R(90), 0, 0)
    im_m = dome_mat(f"GF {take} imprint", 1.6); imp.data.materials.append(im_m)
    ia = im_m.node_tree.nodes["Strength"].outputs[0]
    sim = simulate(take)
    t_hit = sim[-1][5]
    rng = np.random.default_rng(228 + TAKES.index(take))
    sparks = []
    for i in range(48):
        o = link(bpy.data.objects.new(f"GF {take} spark {i}", box_mesh(f"GF {take} sp {i}", (-0.7, -0.7, -0.7), (0.7, 0.7, 0.7), SPARK)))
        sparks.append((o, rng.uniform(0, 2 * math.pi), rng.uniform(0.12, 0.3), rng.uniform(0.02, 0.09), rng.integers(10, 18)))
    ticks = []
    for t, (p, y, z, glow, (alpha, sq), _) in enumerate(sim):
        origin = np.array([ox, y, z])
        sol = solve(p)
        set_pose(objs, sol, origin, t + 1)
        mover.location = (ox, y, z * 0.6); mover.keyframe_insert("location", frame=t + 1)
        s = rm.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
        s.default_value = glow; s.keyframe_insert("default_value", frame=t + 1)
        # dome: centred on the chest; squashed flat against the wall by `sq`, front face stays on the wall
        cz = z + 0.9
        flat = max(0.0, (y - DOME_R) - WALL_FACE) < 1e-6 and sq > 0
        if t_hit is not None and t >= t_hit and sq > 1e-4:
            # the back of the dome stays round behind you, the front is pressed flat on the wall face
            back = y + DOME_R
            front = y - DOME_R + sq                    # sq = how far the front is pushed in (on the wall while pressed)
            ry = (back - front) / (2 * DOME_R)
            dome.scale = (1.0 + 0.3 * (1 - ry), ry, 1.0 + 0.3 * (1 - ry))
            dome.location = (ox, (back + front) / 2, cz)
        else:
            dome.scale = (1, 1, 1); dome.location = (ox, y, cz)
        dome.keyframe_insert("location", frame=t + 1); dome.keyframe_insert("scale", frame=t + 1)
        da.default_value = alpha; da.keyframe_insert("default_value", frame=t + 1)
        # imprint: the flattened patch where the dome met the wall; stays and fades over 5 s (100 ticks)
        if t_hit is not None and t >= t_hit:
            k = t - t_hit
            n_stop, depth = STOP[take]
            d_in = min(depth, HIT - y) if k <= n_stop else depth
            rad = math.sqrt(max(0.01, DOME_R ** 2 - (DOME_R - max(d_in, 0.25)) ** 2))
            rad = min(rad * 1.0, 2.9)
            imp.location = (ox, WALL_FACE + 0.02, WALL_H / 2)          # kept on the wall face (no imprint in the air)
            imp.scale = (rad, min(rad, WALL_H / 2 - 0.05), 1)
            ia.default_value = min(0.85, 0.85 * min(1, k / 2)) * (1 - smooth(min(1, max(0, k - 20) / 100)))
        else:
            imp.location = (ox, WALL_FACE + 0.02, 1.5); imp.scale = (0.01, 0.01, 1); ia.default_value = 0.0
        imp.keyframe_insert("location", frame=t + 1); imp.keyframe_insert("scale", frame=t + 1)
        ia.keyframe_insert("default_value", frame=t + 1)
        # sparks: burst out of the crater rim along the wall and back toward you, under gravity, shrinking out
        for (o, ang, sp, up, life) in sparks:
            if t_hit is not None and 0 <= t - t_hit <= life:
                k = t - t_hit
                r0 = 0.6 + 1.6 * min(1, k / 3)
                o.location = (ox + math.cos(ang) * (r0 + sp * k), WALL_FACE + 0.1 + 0.06 * k,
                              max(0.05, max(cz, 1.0) + math.sin(ang) * (r0 + sp * k) + up * k - 0.012 * k * k))
                sc = 0.07 * (1 - k / life)
            else:
                o.location = (ox, WALL_FACE + 0.1, -3); sc = 0.0001
            o.scale = (sc, sc, sc)
            o.keyframe_insert("location", frame=t + 1); o.keyframe_insert("scale", frame=t + 1)
        ticks.append({"forward": round(-y, 3), "up": round(z, 3), "glow": round(float(glow), 2),
                      "dome_alpha": round(alpha, 3), "dome_squash": round(float(sq), 3),
                      "parts": {kk: {"rot": [round(float(v), 4) for v in sol[kk][0]],
                                     "offset_px": [round(float(v), 3) for v in sol[kk][1] - np.array(PIVOT[kk], float)]}
                                for kk in PARTS}})
    dump["takes"][take] = {"name": NAMES[take], "hit_tick": t_hit, "stop_ticks": STOP[take][0],
                           "crater_depth": STOP[take][1], "ticks": ticks}
    cu = bpy.data.curves.new("GF label " + take, "FONT"); cu.body = f"{take}  {NAMES[take]}"; cu.size = 0.45; cu.align_x = "CENTER"
    tl = link(bpy.data.objects.new("GF label " + take, cu)); tl.location = (ox, 1.5, 0.01)
    tl.data.materials.append(mat("GF label", (0.8, 1.0, 0.85), emit=2.0))
    for nm, loc, look, lens in ((f"Cam {take}", (-0.6, 2.3, 2.6), (0.15, -4.0, 1.3), 28),
                                (f"Cam {take} side", (9.0, -2.0, 2.2), (0, -2.0, 1.2), 30)):
        c = cam(nm, (ox + loc[0], loc[1], loc[2]), (ox + look[0], look[1], look[2]), lens)
        scene.frame_set(1); bpy.context.view_layer.update()
        mw = c.matrix_world.copy(); c.parent = mover; c.matrix_world = mw
    cam(f"Cam {take} wall", (ox + 7.5, WALL_FACE + 6.5, 3.2), (ox, WALL_FACE + 1.5, 1.4), 30)
    print(take, "built, hit at tick", t_hit, flush=True)

with open(os.path.join(FOLDER, "ground_flight_poses.json"), "w") as fh:
    json.dump(dump, fh, separators=(",", ":"))
scene.frame_start, scene.frame_end = 1, T_END
bpy.ops.mesh.primitive_plane_add(size=1, location=(16, -14, 0))
g = bpy.context.active_object
for c in g.users_collection:
    c.objects.unlink(g)
link(g); g.name = "GF ground"; g.scale = (60, 50, 1)
gm = bpy.data.materials.new("GF ground"); gm.use_nodes = True
N, Lk = gm.node_tree.nodes, gm.node_tree.links
ck = N.new("ShaderNodeTexChecker"); ck.inputs["Scale"].default_value = 50
ck.inputs["Color1"].default_value = (0.2, 0.36, 0.13, 1); ck.inputs["Color2"].default_value = (0.24, 0.42, 0.16, 1)
Lk.new(ck.outputs["Color"], N.get("Principled BSDF").inputs["Base Color"])
g.data.materials.append(gm)
world = bpy.data.worlds.new("GF world"); world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.35, 0.45, 0.6, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.8
scene.world = world
sun = link(bpy.data.objects.new("GF sun", bpy.data.lights.new("GF sun", "SUN")))
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
cam("Cam all", (16, 14, 12), (16, -16, 1), 26)
scene.camera = bpy.data.objects["Cam H2"]
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
