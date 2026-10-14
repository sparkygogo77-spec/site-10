# Pass 214: sprint run with the ring (lead Blender chat, 2026-10-14). J picked it as the next build ("2 and 3": the sprint
# run, then suit round 3) and wants every take to open on an over-the-shoulder camera.
# The player rig with knees (thigh 6 px + shin 6 px, as in pass 208), running forward at sprint speed (0.28 blocks a
# tick, 5.6 blocks a second) on a 12-tick stride (0.6 s), 48 ticks a loop. The hips drop until the lowest foot touches
# the ground every tick, so the body bobs on its own. Arms swing against the legs.
#   S1 ring forward: the ring fist held out in front the whole run, glowing, the free arm pumping.
#   S2 power pump: a classic sprint, both arms pumping, the ring flashing on each forward swing.
#   S3 launch dash: deep lean, long strides, ring arm trailing back and charging, as if about to take off.
#   S4 lantern carry: the free hand holds the lantern by the handle at the hip; it swings against the motion.
# Cameras "Cam S1".."Cam S4" (over the right shoulder, following), "Cam S1 side".."Cam S4 side", "Cam all".
# Pose format as before (per part rot rad, offset_px from the vanilla pivot; shins pivot at the knee). Writes
# LanternLive\sprint_run_poses.json, builds LanternLive\sprint_run.blend.
import json, math, os
import bpy
import numpy as np
from mathutils import Matrix

R = math.radians
OUT = os.path.join(FOLDER, "sprint_run.blend")
if bpy.data.filepath:
    try:
        bpy.ops.wm.save_mainfile()
    except Exception as e:
        print("save current:", e)
old = bpy.data.scenes.get("Sprint Run")
if old:
    bpy.data.scenes.remove(old)
scene = bpy.data.scenes.new("Sprint Run")
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


def ring_glow(take, t):
    ph = 2 * math.pi * t / STRIDE
    if take == "S1":
        return 6.0 + 2.0 * math.sin(2 * ph)
    if take == "S2":
        return 2.0 + 10.0 * max(0.0, -math.sin(ph)) ** 3      # flashes as the ring arm swings forward
    if take == "S3":
        return 2.0 + 14.0 * (t % LOOP) / LOOP                  # charging up for the launch
    return 2.5


def lantern_box(tag):
    root = link(bpy.data.objects.new(f"SR {tag} lantern", None)); root.empty_display_size = 0.04
    JADE = mat("SR jade", (0.02, 0.22, 0.08), rough=0.25); GOLD = mat("SR gold", (0.85, 0.62, 0.2), rough=0.3, metal=0.9)
    GLOWM = mat("SR lantern glow", (0.15, 1.0, 0.3), emit=3.0)
    for i, (a, b, m) in enumerate((((-3, 2.5, -3), (3, 11.5, 3), JADE), ((-3.6, 11.5, -3.6), (3.6, 12.5, 3.6), GOLD),
                                   ((-3.6, 1.5, -3.6), (3.6, 2.5, 3.6), GOLD), ((-0.5, 0, -0.5), (0.5, 1.5, 0.5), GOLD),
                                   ((-1.6, 5, 2.95), (1.6, 9, 3.3), GLOWM))):
        o = link(bpy.data.objects.new(f"SR {tag} lan {i}", box_mesh(f"SR {tag} lan {i}", a, b, m))); o.parent = root
    return root


def bl_from_rig(M_rig, origin):
    out = np.eye(4); out[:3, :3] = A @ M_rig[:3, :3] @ A.T; out[:3, 3] = to_bl(M_rig[:3, 3]) + np.asarray(origin)
    return Matrix(out.tolist())


TAKES = ["S1", "S2", "S3", "S4"]
NAMES = {"S1": "ring forward", "S2": "power pump", "S3": "launch dash", "S4": "lantern carry"}
LANE = {k: (i * 5.0, 0.0) for i, k in enumerate(TAKES)}
dump = {"format": "per take: 48 ticks, per tick part rot (xRot,yRot,zRot rad) and offset_px from the vanilla pivot "
                  "(shins pivot at the knee, 6 px below the hip); ring = right arm; moves 0.28 blocks a tick", "takes": {}}
for take in TAKES:
    ox, oy = LANE[take]
    objs = make_player(take)
    rm = mat(f"SR ring {take}", (0.1, 1.0, 0.25), emit=2.0); objs["ring"].data.materials[0] = rm
    mover = link(bpy.data.objects.new(f"SR {take} mover", None)); mover.empty_display_size = 0.1
    lan = lantern_box(take) if take == "S4" else None
    ticks = []
    phi = om = 0.0; prev = []
    for t in range(LOOP + 1):
        origin = np.array([ox, oy - SPEED * t, 0.0])
        sol = solve(run_pose(take, t))
        set_pose(objs, sol, origin, t + 1)
        mover.location = tuple(origin); mover.keyframe_insert("location", frame=t + 1)
        s = rm.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
        s.default_value = ring_glow(take, t); s.keyframe_insert("default_value", frame=t + 1)
        if lan is not None:
            # the lantern hangs from the free hand and swings fore and aft against the hand's motion (damped pendulum)
            hp = hand_point(sol, "larm") + np.array([0, 0, -SPEED * 16 * t])
            prev.append(hp)
            if len(prev) >= 3:
                a = (prev[-1][2] - 2 * prev[-2][2] + prev[-3][2]) * 400.0     # px/s^2 along z
                Lc, g = 7.0, 9.81 * 16
                for _ in range(20):
                    al = -(g / Lc) * math.sin(phi) - (a / Lc) * math.cos(phi) - 2 * 0.15 * math.sqrt(g / Lc) * om
                    om += al / 400.0; phi += om / 400.0
            Rx = np.array([[1, 0, 0], [0, math.cos(phi), -math.sin(phi)], [0, math.sin(phi), math.cos(phi)]])
            M = np.eye(4); M[:3, :3] = Rx; M[:3, 3] = hand_point(sol, "larm")
            lan.matrix_world = bl_from_rig(M, origin)
            lan.keyframe_insert("location", frame=t + 1); lan.keyframe_insert("rotation_euler", frame=t + 1)
        ticks.append({k: {"rot": [round(float(v), 4) for v in sol[k][0]],
                          "offset_px": [round(float(v), 3) for v in sol[k][1] - np.array(PIVOT[k], float)]} for k in PARTS})
    for o in list(objs.values()) + ([lan] if lan else []) + [mover]:
        ad = o.animation_data
        if ad and ad.action:
            try:
                for fc in ad.action.fcurves:
                    for kp in fc.keyframe_points:
                        kp.interpolation = "LINEAR"
            except Exception:
                pass
    dump["takes"][take] = {"name": NAMES[take], "ticks": ticks, "blocks_per_tick": SPEED, "stride_ticks": STRIDE}
    cu = bpy.data.curves.new("SR label " + take, "FONT"); cu.body = f"{take}  {NAMES[take]}"; cu.size = 0.35; cu.align_x = "CENTER"
    tl = link(bpy.data.objects.new("SR label " + take, cu)); tl.location = (ox, oy + 1.2, 0.01)
    tl.data.materials.append(mat("SR label", (0.8, 1.0, 0.85), emit=2.0))
    # cameras ride with the runner: over the right shoulder, and from the side
    for nm, loc, look, lens in ((f"Cam {take}", (-0.55, 2.1, 2.35), (0.15, -4.0, 1.15), 30),
                                (f"Cam {take} side", (5.5, -0.4, 1.2), (0, -0.4, 0.95), 35)):
        c = cam(nm, (ox + loc[0], oy + loc[1], loc[2]), (ox + look[0], oy + look[1], look[2]), lens)
        scene.frame_set(1); bpy.context.view_layer.update()      # parent while the mover is at its start
        mw = c.matrix_world.copy(); c.parent = mover; c.matrix_world = mw
    print(take, "built", flush=True)

with open(os.path.join(FOLDER, "sprint_run_poses.json"), "w") as fh:
    json.dump(dump, fh, separators=(",", ":"))

scene.frame_start, scene.frame_end = 1, LOOP
# a long ground with a grid so the speed reads
bpy.ops.mesh.primitive_plane_add(size=1, location=(7.5, -8, 0))
g = bpy.context.active_object
for c in g.users_collection:
    c.objects.unlink(g)
link(g); g.name = "SR ground"; g.scale = (30, 40, 1)
gm = bpy.data.materials.new("SR ground"); gm.use_nodes = True
N, Lk = gm.node_tree.nodes, gm.node_tree.links
ck = N.new("ShaderNodeTexChecker"); ck.inputs["Scale"].default_value = 40
ck.inputs["Color1"].default_value = (0.2, 0.36, 0.13, 1); ck.inputs["Color2"].default_value = (0.24, 0.42, 0.16, 1)
Lk.new(ck.outputs["Color"], N.get("Principled BSDF").inputs["Base Color"])
g.data.materials.append(gm)
world = bpy.data.worlds.get("SR world") or bpy.data.worlds.new("SR world"); world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.35, 0.45, 0.6, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.8
scene.world = world
sun = link(bpy.data.objects.new("SR sun", bpy.data.lights.new("SR sun", "SUN")))
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
cams_all = cam("Cam all", (7.5, 9, 6), (7.5, -6, 0.8), 28)
scene.camera = bpy.data.objects["Cam S1"]
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
